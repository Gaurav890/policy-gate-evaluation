"""Project-only credentials and durable conservative API cost admission."""

import fcntl
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODELS = {
    "claude": {"id": "anthropic/claude-sonnet-5", "route": "anthropic", "input": 2.0, "output": 10.0, "effort": "none"},
    "deepseek": {"id": "deepseek/deepseek-v4.1-flash", "route": "baseten", "input": 0.3, "output": 1.2, "effort": "none"},
    "gemini": {"id": "google/gemini-3.8-flash", "route": "google", "input": 0.75, "output": 3.75, "effort": "low"},
}


class BudgetExceeded(RuntimeError):
    """No further paid request may be admitted."""


class GatewayError(RuntimeError):
    """Sanitized API failure; do not retry silently."""


def load_study_key():
    """Read exactly one local key; no environment or parent-file fallback."""
    values = []
    for line in (ROOT / "groundwork" / ".env").read_text().splitlines():
        line = line.strip()
        if line.startswith("AI_GATEWAY_API_KEY="):
            values.append(line.split("=", 1)[1].strip().strip('"').strip("'"))
    if len(values) != 1 or len(values[0]) < 16:
        raise GatewayError("Study credential is absent or malformed")
    return values[0]


def write_json(path, value):
    """Save an artifact atomically in its destination directory."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temp.replace(path)


class Budget:
    """Never refund reservations, including failed or interrupted requests."""

    def __init__(self, ledger=None, ceiling=30.0):
        authorization = json.loads((ROOT / "groundwork" / "authorization.json").read_text())
        self.cap = min(float(ceiling), float(authorization["cumulative_usd_cap"]))
        self.ledger = Path(ledger or ROOT / "groundwork" / "spend_ledger.jsonl")

    def reserve(self, payload, rates, metadata):
        """Reserve a padded byte-based input bound and maximum output cost."""
        # Text-only API. Byte length overestimates ordinary tokenizer counts;
        # additional overhead and 25% rate padding cover serialization variance.
        input_bound = len(json.dumps(payload, ensure_ascii=True).encode()) + 4096
        amount = 1.25 * (input_bound * rates["input"] + payload["max_tokens"] * rates["output"]) / 1_000_000
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger.open("a+") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            handle.seek(0)
            entries = [json.loads(line) for line in handle if line.strip()]
            previous = sum(entry["reserved_usd"] for entry in entries)
            if previous + amount > self.cap:
                raise BudgetExceeded(f"Next reservation exceeds ${self.cap:.2f} stage ceiling")
            entry = {"request_id": uuid.uuid4().hex, "utc": datetime.now(timezone.utc).isoformat(),
                     "reserved_usd": amount, "cumulative_reserved_usd": previous + amount,
                     "input_token_bound": input_bound, "max_output_tokens": payload["max_tokens"],
                     "model": payload["model"], **metadata}
            handle.write(json.dumps(entry) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return entry

    def total_reserved(self):
        if not self.ledger.exists():
            return 0.0
        return sum(json.loads(line)["reserved_usd"] for line in self.ledger.read_text().splitlines() if line)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Gateway:
    """One attempt per request, fixed provider, complete private provenance."""

    def __init__(self, budget=None):
        self.budget = budget or Budget()
        self.key = load_study_key()
        self.records_dir = ROOT / "groundwork" / "api_records"

    def complete(self, model, messages, *, tools=None, max_tokens=2048, role="actor", episode="access", response_format=None):
        cfg = MODELS[model]
        payload = {"model": cfg["id"], "messages": messages, "max_tokens": max_tokens,
                   "reasoning": {"effort": cfg["effort"]},
                   "providerOptions": {"gateway": {"only": [cfg["route"]]}}}
        if tools:
            payload.update(tools=tools, tool_choice="auto")
        if response_format:
            payload["response_format"] = response_format
        reservation = self.budget.reserve(payload, cfg, {"role": role, "episode": episode})
        record = {**reservation, "status": "reserved", "request": payload}
        path = self.records_dir / (reservation["request_id"] + ".json")
        write_json(path, record)
        start = time.monotonic()
        request = urllib.request.Request(
            "https://ai-gateway.vercel.sh/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Authorization": "Bearer " + self.key, "Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.build_opener(NoRedirect).open(request, timeout=55) as response:
                data = json.load(response)
        except Exception as exc:
            record.update(status="request_failed", error_type=type(exc).__name__,
                          http_status=getattr(exc, "code", None), elapsed_s=time.monotonic()-start)
            write_json(path, record)
            raise GatewayError(f"API call failed: {record['error_type']}, HTTP {record['http_status']}; reservation retained") from None
        usage = data.get("usage", {})
        prompt = usage.get("prompt_tokens")
        completion = usage.get("completion_tokens")
        record.update(status="received", response=data, elapsed_s=time.monotonic()-start)
        if not isinstance(prompt, int) or not isinstance(completion, int):
            write_json(path, record)
            raise GatewayError("Missing usage; paid execution stopped")
        estimate = (prompt * cfg["input"] + completion * cfg["output"]) / 1_000_000
        record["uncached_cost_estimate_usd"] = estimate
        record["status"] = "ok"
        write_json(path, record)
        if estimate > reservation["reserved_usd"]:
            raise BudgetExceeded("Usage exceeded conservative reservation; stop and audit rates")
        try:
            choice = data["choices"][0]
            if choice.get("finish_reason") == "length":
                raise GatewayError("Output token limit reached; retain as infrastructure truncation")
            message = choice["message"]
            if not message.get("content") and not message.get("tool_calls"):
                raise GatewayError("Empty model response")
        except (KeyError, IndexError, TypeError):
            raise GatewayError("Malformed completion; usage preserved") from None
        return message, record
