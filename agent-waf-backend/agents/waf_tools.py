"""
WAF-aware LangChain tools.

Every tool defined here is a thin wrapper that forwards the call to the
WAF proxy's POST /invoke endpoint.  The agent never touches the
downstream tool directly — the WAF intercepts, evaluates rules, logs
the call, and returns the result (or a 403 block).

This module is the single integration point between the agentic layer
and the WAF proxy layer.
"""

import json
import httpx
from typing import Optional, List
from langchain_core.tools import tool

from .config import WAF_URL
import os

WAF_API_KEY = os.environ.get("WAF_API_KEY", "super-secret-key")

# ── Internal HTTP helper ────────────────────────────────────────────

_client = httpx.Client(
    base_url=WAF_URL,
    timeout=15.0,
    headers={"X-WAF-API-Key": WAF_API_KEY}
)

# We store the current agent context in a module-level dict so tools
# can read it.  This is set by the graph before each agent turn.
_agent_context: dict = {
    "agent_id": "default",
    "session_id": "default",
    "declared_scope": None,
}


def set_agent_context(
    agent_id: str,
    session_id: str,
    declared_scope: Optional[List[str]] = None,
):
    """Called by the graph runner before invoking the agent."""
    _agent_context["agent_id"] = agent_id
    _agent_context["session_id"] = session_id
    _agent_context["declared_scope"] = declared_scope


def _invoke_waf(tool_name: str, parameters: dict) -> str:
    """
    Post a tool call to the WAF proxy and return a human-readable
    string result the LLM can reason about.
    """
    payload = {
        "agent_id": _agent_context["agent_id"],
        "session_id": _agent_context["session_id"],
        "tool": tool_name,
        "parameters": parameters,
    }
    if _agent_context["declared_scope"] is not None:
        payload["declared_scope"] = _agent_context["declared_scope"]

    try:
        resp = _client.post("/invoke", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            return json.dumps(data.get("result", {}), indent=2)
        elif resp.status_code == 403:
            detail = resp.json().get("detail", {})
            reasons = [
                r["reason"]
                for r in detail.get("rule_results", [])
                if not r["allowed"]
            ]
            return f"[BLOCKED by WAF] {'; '.join(reasons)}"
        else:
            return f"[WAF ERROR] HTTP {resp.status_code}: {resp.text}"
    except httpx.ConnectError:
        return "[WAF ERROR] Could not connect to the WAF proxy. Is it running?"
    except Exception as exc:
        return f"[WAF ERROR] {exc}"


# ── LangChain Tool Definitions ──────────────────────────────────────
# Each tool has a clear docstring the LLM uses to decide when to call it.

@tool
def get_customer_record(customer_id: str) -> str:
    """Fetch a customer record by their ID. Returns customer details like name and account info."""
    return _invoke_waf("get_customer_record", {"customer_id": customer_id})


@tool
def send_email(to: str, body: str) -> str:
    """Send an email to a recipient. Provide the recipient address and the email body."""
    return _invoke_waf("send_email", {"to": to, "body": body})


@tool
def run_query(query: str) -> str:
    """Run a database query and return results. Provide the SQL-like query string."""
    return _invoke_waf("run_query", {"query": query})


@tool
def refund_payment(payment_id: str) -> str:
    """Refund a payment transaction. You MUST look up the customer record first before issuing a refund."""
    return _invoke_waf("refund_payment", {"payment_id": payment_id})


# Convenience list for binding to the LLM
ALL_TOOLS = [get_customer_record, send_email, run_query, refund_payment]
