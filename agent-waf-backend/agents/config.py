"""
Agent configuration — central place for LLM provider, model names,
WAF endpoint, and per-agent settings.

All agents import from here so switching providers is a one-line change.
"""

import os

# ── LLM Provider ────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

# ── WAF Proxy ───────────────────────────────────────────────────────
WAF_URL = os.environ.get("WAF_URL", "http://127.0.0.1:8000")

# ── Agent Defaults ──────────────────────────────────────────────────
DEFAULT_AGENT_ID = "langchain_agent"
DEFAULT_SESSION_TTL = 300  # seconds

# ── Scope Mapping ───────────────────────────────────────────────────
# Maps agent roles to the data scope they are authorised to access.
# In production this would come from an IAM / policy store.
AGENT_SCOPES = {
    "customer_service": ["cust_123", "cust_456", "cust_789"],
    "security_tester": ["cust_123"],
    "supervisor": ["cust_123", "cust_456", "cust_789"],
}
