from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ToolCallRequest(BaseModel):
    agent_id: str
    session_id: str
    tool: str
    parameters: Dict[str, Any]
    declared_scope: Optional[List[str]] = None

class RuleResult(BaseModel):
    rule_name: str
    rule_type: str
    allowed: bool
    shadow: bool
    reason: str

class InvokeResponse(BaseModel):
    disposition: str
    log_id: str
    tool: str
    rule_results: List[RuleResult]
    result: Optional[Any] = None
