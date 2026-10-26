"""Small authorized tool-call and structured-response transport checks."""

import json

from gateway_budget import Gateway, ROOT, write_json


def main():
    gateway = Gateway()
    output = ROOT / "groundwork" / "access_probe.json"
    if output.exists():
        raise SystemExit("Access probe already recorded; refusing an automatic repeat")
    records = []
    tools = [{"type": "function", "function": {"name": "report_ready", "description": "Record transport readiness.",
              "parameters": {"type": "object", "properties": {"ready": {"type": "boolean"}}, "required": ["ready"], "additionalProperties": False}}}]
    for model in ["claude", "deepseek"]:
        message, record = gateway.complete(model, [{"role": "user", "content": "Call report_ready with ready=true."}],
                                            tools=tools, max_tokens=256, role="access_probe")
        calls = message.get("tool_calls", [])
        valid = len(calls) == 1 and calls[0]["function"]["name"] == "report_ready" and json.loads(calls[0]["function"]["arguments"]) == {"ready": True}
        records.append({"model": model, "passed": valid, "request_record": record["request_id"]})
        write_json(output, records)
        print(json.dumps(records[-1]), flush=True)
        if not valid:
            raise SystemExit("Tool-call transport check failed")
    schema = {"type": "json_schema", "json_schema": {"name": "readiness", "strict": True,
              "schema": {"type": "object", "properties": {"ready": {"type": "boolean"}}, "required": ["ready"], "additionalProperties": False}}}
    message, record = gateway.complete("gemini", [{"role": "user", "content": "Return ready=true."}],
                                        max_tokens=512, role="access_probe", response_format=schema)
    valid = json.loads(message["content"]) == {"ready": True}
    records.append({"model": "gemini", "passed": valid, "request_record": record["request_id"]})
    write_json(output, records)
    print(json.dumps(records[-1]), flush=True)
    if not valid:
        raise SystemExit("Structured output transport check failed")


if __name__ == "__main__":
    main()
