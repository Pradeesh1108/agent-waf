import yaml
import re
import os
from typing import List, Tuple
from .models import ToolCallRequest, RuleResult
from .state import state_manager

_policies_cache = {}
_policies_mtime = 0

def get_policies() -> dict:
    global _policies_cache, _policies_mtime
    path = os.path.join(os.path.dirname(__file__), "policies.yaml")
    try:
        mtime = os.path.getmtime(path)
        if mtime > _policies_mtime:
            with open(path, "r") as f:
                _policies_cache = yaml.safe_load(f)
            _policies_mtime = mtime
    except Exception:
        pass
    return _policies_cache or {}

def evaluate_rules(request: ToolCallRequest) -> Tuple[List[RuleResult], bool]:
    results = []
    should_block = False

    policies = get_policies()
    for rule_def in policies.get("rules", []):
        rule_type = rule_def.get("type")
        rule_name = rule_def.get("name")
        shadow = rule_def.get("shadow", False)
        
        allowed = True
        reason = ""

        if rule_type == "rate_limit":
            if request.tool == rule_def.get("tool"):
                window = rule_def.get("window_seconds", 60)
                max_calls = rule_def.get("max_calls", 1)
                count = state_manager.get_rate_count(request.agent_id, request.tool, window)
                if count >= max_calls:
                    allowed = False
                    reason = f"Rate limit exceeded for tool {request.tool}. Max {max_calls} per {window}s."
                else:
                    reason = f"Rate limit ok. Current count: {count}."
            else:
                continue

        elif rule_type == "param_blocklist":
            patterns = rule_def.get("patterns", [])
            max_length = rule_def.get("max_length", 1000)
            
            for param_name, param_val in request.parameters.items():
                if isinstance(param_val, str):
                    if len(param_val) > max_length:
                        allowed = False
                        reason = f"Parameter {param_name} exceeds max length of {max_length}."
                        break
                    
                    for pat in patterns:
                        if re.search(pat, param_val):
                            allowed = False
                            reason = f"Parameter {param_name} matched blocklist pattern."
                            break
                if not allowed:
                    break
            
            if allowed:
                reason = "Parameters passed blocklist validation."

        elif rule_type == "data_scope":
            tools = rule_def.get("tools", [])
            if request.tool in tools:
                id_params = rule_def.get("id_params", [])
                
                if request.declared_scope is None:
                    allowed = False
                    reason = "No declared_scope provided, failing closed."
                else:
                    for param_name in id_params:
                        if param_name in request.parameters:
                            val = str(request.parameters[param_name])
                            if val not in request.declared_scope:
                                allowed = False
                                reason = f"Data scope violation. {val} not in {request.declared_scope}."
                                break
                
                if allowed:
                    reason = "Data scope validated successfully."
            else:
                continue

        elif rule_type == "sequence":
            if request.tool == rule_def.get("tool"):
                depends_on = rule_def.get("depends_on")
                history = state_manager.get_session_sequence(request.agent_id, request.session_id)
                if depends_on not in history:
                    allowed = False
                    reason = f"Sequence violation: {depends_on} must be called before {request.tool}."
                else:
                    reason = f"Sequence validated successfully. {depends_on} was called."
            else:
                continue

        results.append(RuleResult(
            rule_name=rule_name,
            rule_type=rule_type,
            allowed=allowed,
            shadow=shadow,
            reason=reason
        ))
        
        if not allowed and not shadow:
            should_block = True

    return results, should_block
