from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import ValidationError

from .models import ToolCallRequest, InvokeResponse, RuleResult
from .rules import evaluate_rules, get_policies
from .state import state_manager
from .tools import TOOL_REGISTRY
from .logging_config import logger
import os
from fastapi import Security
from fastapi.security import APIKeyHeader

WAF_API_KEY = os.environ.get("WAF_API_KEY", "super-secret-key")
api_key_header = APIKeyHeader(name="X-WAF-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != WAF_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-WAF-API-Key header")
    return api_key

app = FastAPI(title="Agent WAF")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/invoke", response_model=InvokeResponse)
def invoke_tool(request: ToolCallRequest, api_key: str = Security(verify_api_key)):
    try:
        rule_results, should_block = evaluate_rules(request)
        disposition = "block" if should_block else "allow"
        
        result = None
        if not should_block:
            if request.tool not in TOOL_REGISTRY:
                disposition = "block"
                rule_results.append(RuleResult(
                    rule_name="tool_exists",
                    rule_type="system",
                    allowed=False,
                    shadow=False,
                    reason=f"Tool {request.tool} not found."
                ))
            else:
                try:
                    tool_func = TOOL_REGISTRY[request.tool]
                    result = tool_func(**request.parameters)
                    
                    state_manager.append_session_sequence(request.agent_id, request.session_id, request.tool)
                    
                    # Increment any rate limits defined for this tool
                    for rule_def in get_policies().get("rules", []):
                        if rule_def.get("type") == "rate_limit" and rule_def.get("tool") == request.tool:
                            window = rule_def.get("window_seconds", 60)
                            state_manager.increment_rate_count(request.agent_id, request.tool, window)
                except Exception as e:
                    logger.error("Tool execution failed", extra={"extra_info": {"error": str(e)}})
                    raise HTTPException(status_code=500, detail="Tool execution failed")
        
        log_id = state_manager.log_invocation(request, rule_results, disposition, result)
        
        logger.info(f"Invocation {disposition}", extra={"extra_info": {
            "log_id": log_id,
            "agent_id": request.agent_id,
            "tool": request.tool,
            "disposition": disposition
        }})
        
        if disposition == "block":
            raise HTTPException(status_code=403, detail={
                "disposition": disposition,
                "log_id": log_id,
                "tool": request.tool,
                "rule_results": [r.model_dump() for r in rule_results]
            })
            
        return InvokeResponse(
            disposition=disposition,
            log_id=log_id,
            tool=request.tool,
            rule_results=rule_results,
            result=result
        )
        
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Internal Server Error", extra={"extra_info": {"error": str(e)}})
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
def health_check():
    status = {"status": "ok"}
    try:
        if not state_manager._in_memory_logs and hasattr(state_manager, 'dynamodb'):
            # It's using dynamodb
            state_manager.table.table_status
            status["dynamodb"] = "connected"
        else:
            status["dynamodb"] = "in-memory"
    except Exception as e:
        status["dynamodb"] = "error"
        status["error"] = str(e)
    return status

@app.get("/logs")
def get_logs(since: int = 0, limit: int = 100, api_key: str = Security(verify_api_key)):
    try:
        logs = state_manager.get_recent_logs(since, limit)
        return {"logs": logs}
    except Exception as e:
        logger.error("Error fetching logs", extra={"extra_info": {"error": str(e)}})
        raise HTTPException(status_code=500, detail="Error fetching logs")


handler = Mangum(app)
