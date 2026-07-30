"""
Agent configuration — central place for LLM provider, model names,
WAF endpoint, and per-agent settings.

All agents import from here so switching providers is a one-line change.
"""

import os

# ── Load .env automatically if it exists ──────────────────────────────
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                try:
                    key, val = line.strip().split('=', 1)
                    os.environ.setdefault(key, val.strip('"\''))
                except ValueError:
                    pass

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
