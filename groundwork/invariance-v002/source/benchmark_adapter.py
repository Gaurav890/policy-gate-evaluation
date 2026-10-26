"""Native benchmark execution with a bijective external tool-name wrapper."""

import copy
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ["PYTHON_DOTENV_DISABLED"] = "1"
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
os.environ["TAU2_DATA_DIR"] = str(ROOT / "groundwork/benchmark-source/data")

from loguru import logger
logger.remove()
from tau2.data_model.message import AssistantMessage, ToolCall, ToolMessage
from tau2.data_model.tasks import Task
from tau2.environment.environment import Environment
from tau2.domains.retail.environment import get_environment as retail_environment
from tau2.domains.airline.environment import get_environment as airline_environment
from tau2.evaluator.evaluator_env import EnvironmentEvaluator
from tau2.evaluator.evaluator_communicate import CommunicateEvaluator

CONSTRUCTORS = {"retail": retail_environment, "airline": airline_environment}


def load_task(domain, task_id):
    """Load only a development task; reject reserved/unallocated task access."""
    manifest = json.loads((ROOT / "pilot_manifest.json").read_text())
    if str(task_id) not in manifest["domains"][domain]["development_ids"]:
        raise ValueError("Task is not in the approved development allocation")
    path = ROOT / "groundwork/benchmark-source/data/tau2/domains" / domain / "tasks.json"
    for data in json.loads(path.read_text()):
        if str(data["id"]) == str(task_id):
            return Task.model_validate(data)
    raise ValueError("Task not found")


def replace_names(text, mapping):
    """Replace whole tool-name tokens, never substrings of other tool names."""
    if not mapping or not text:
        return text
    return re.sub(r"\b(?:" + "|".join(re.escape(k) for k in sorted(mapping, key=len, reverse=True)) + r")\b",
                  lambda match: mapping[match.group()], text)


class NameShiftEnvironment(Environment):
    """Expose renamed tools while using unmodified native tool implementations."""

    def __init__(self, native, shifted):
        self.name_map = {tool.name: "service_" + tool.name for tool in native.get_tools()} if shifted else {}
        self.inverse = {value: key for key, value in self.name_map.items()}
        super().__init__(domain_name=native.domain_name,
                         policy=replace_names(native.policy, self.name_map),
                         tools=native.tools, user_tools=native.user_tools)

    def get_tools(self):
        result = []
        for original in super().get_tools():
            tool = copy.copy(original)
            tool.name = self.name_map.get(original.name, original.name)
            tool.short_desc = replace_names(tool.short_desc, self.name_map)
            tool.long_desc = replace_names(tool.long_desc, self.name_map)
            tool.examples = [replace_names(example, self.name_map) for example in tool.examples]
            result.append(tool)
        return result

    def get_response(self, message):
        canonical = message.model_copy(deep=True)
        if self.name_map and message.requestor == "assistant":
            if message.name not in self.inverse:
                return ToolMessage(id=message.id, role="tool", requestor="assistant",
                                   content=json.dumps("Error: Unknown tool " + message.name), error=True)
            canonical.name = self.inverse[message.name]
        return super().get_response(canonical)

    def canonical_messages(self, messages):
        """Provide an evaluator-only canonical view; rejected legacy names stay invalid."""
        result = copy.deepcopy(messages)
        for message in result:
            for call in getattr(message, "tool_calls", None) or []:
                if self.name_map and call.requestor == "assistant":
                    call.name = self.inverse.get(call.name, "unavailable_" + call.name)
        return result


def make_environment(domain, shifted=False):
    return NameShiftEnvironment(CONSTRUCTORS[domain](), shifted)


def grade_deterministic(domain, task, messages, termination):
    """Score native deterministic components; never substitute them for NL checks."""
    env = EnvironmentEvaluator.calculate_reward(CONSTRUCTORS[domain], task, messages)
    comm = CommunicateEvaluator.calculate_reward(task, messages)
    basis = [item.value for item in task.evaluation_criteria.reward_basis]
    normal = termination in {"agent_stop", "user_stop"}
    components = {"DB": env.db_check.db_reward if env.db_check else env.reward,
                  "COMMUNICATE": comm.reward}
    known = [components[k] for k in basis if k in components]
    partial_pass = normal and all(value == 1.0 for value in known)
    pending = [k for k in basis if k not in components]
    native_success = partial_pass if not pending or not partial_pass else None
    return {"deterministic_pass": partial_pass, "native_success": native_success,
            "pending_components": pending, "reward_basis": basis,
            "environment": env.model_dump(mode="json"), "communication": comm.model_dump(mode="json"),
            "label_scope": "native deterministic components only; NL checks pending review"}


def bridge_generate(gateway, episode):
    """Adapt native agent/user model calls to the budgeted Gateway transport."""
    from tau2.utils.llm_utils import to_litellm_messages

    def generate(model, messages, tools=None, call_name=None, **kwargs):
        role = "customer" if call_name == "user_simulator_response" else "actor"
        converted = to_litellm_messages(messages)
        for item in converted:
            if item.get("tool_calls") is None:
                item.pop("tool_calls", None)
            for call in item.get("tool_calls", []):
                call.pop("name", None)
        message, record = gateway.complete(model, converted,
            tools=[tool.openai_schema for tool in tools] if tools else None,
            max_tokens=1024 if role == "customer" else 2048, role=role, episode=episode)
        calls = [ToolCall(id=call["id"], name=call["function"]["name"],
                          arguments=json.loads(call["function"]["arguments"]))
                 for call in message.get("tool_calls") or []]
        usage = record["response"]["usage"]
        return AssistantMessage(role="assistant", content=message.get("content"), tool_calls=calls or None,
                                cost=record["uncached_cost_estimate_usd"],
                                usage={"prompt_tokens": usage["prompt_tokens"], "completion_tokens": usage["completion_tokens"]},
                                raw_data={"request_record": record["request_id"], "model": record["response"].get("model")},
                                generation_time_seconds=record["elapsed_s"])
    return generate
