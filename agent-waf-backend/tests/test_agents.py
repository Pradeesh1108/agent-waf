"""
Unit tests for the agent module structure.

These tests verify that:
1. WAF tools correctly format calls to the proxy.
2. The agent graph compiles without errors.
3. The orchestrator graph compiles without errors.
4. Context setting works correctly.
"""

import pytest
from unittest.mock import patch, MagicMock
import json


def test_set_agent_context():
    """set_agent_context updates the module-level context dict."""
    from agents.waf_tools import set_agent_context, _agent_context

    set_agent_context("test_agent", "test_session", ["scope_a"])
    assert _agent_context["agent_id"] == "test_agent"
    assert _agent_context["session_id"] == "test_session"
    assert _agent_context["declared_scope"] == ["scope_a"]


def test_waf_tools_are_langchain_tools():
    """All tools should be LangChain BaseTool instances."""
    from agents.waf_tools import ALL_TOOLS
    from langchain_core.tools import BaseTool

    assert len(ALL_TOOLS) == 4
    for t in ALL_TOOLS:
        assert isinstance(t, BaseTool), f"{t.name} is not a BaseTool"


def test_invoke_waf_formats_payload(monkeypatch):
    """_invoke_waf should POST the correct JSON structure to the proxy."""
    from agents.waf_tools import _invoke_waf, set_agent_context, _client

    set_agent_context("agent_x", "sess_y", ["cust_1"])

    captured = {}

    def mock_post(url, json=None, **kwargs):
        captured.update(json)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"result": {"ok": True}}
        return resp

    monkeypatch.setattr(_client, "post", mock_post)

    result = _invoke_waf("get_customer_record", {"customer_id": "cust_1"})

    assert captured["agent_id"] == "agent_x"
    assert captured["session_id"] == "sess_y"
    assert captured["tool"] == "get_customer_record"
    assert captured["declared_scope"] == ["cust_1"]
    assert "ok" in result


def test_invoke_waf_handles_403_block(monkeypatch):
    """A 403 from the WAF should return a readable BLOCKED message."""
    from agents.waf_tools import _invoke_waf, set_agent_context, _client

    set_agent_context("agent_x", "sess_y")

    def mock_post(url, json=None, **kwargs):
        resp = MagicMock()
        resp.status_code = 403
        resp.json.return_value = {
            "detail": {
                "rule_results": [
                    {"allowed": False, "reason": "Rate limit exceeded", "shadow": False}
                ]
            }
        }
        return resp

    monkeypatch.setattr(_client, "post", mock_post)

    result = _invoke_waf("send_email", {"to": "x@x.com", "body": "hi"})
    assert "[BLOCKED by WAF]" in result
    assert "Rate limit exceeded" in result


def test_invoke_waf_handles_connection_error(monkeypatch):
    """Connection errors should return a clean error string."""
    import httpx
    from agents.waf_tools import _invoke_waf, set_agent_context, _client

    set_agent_context("agent_x", "sess_y")

    def mock_post(url, json=None, **kwargs):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(_client, "post", mock_post)

    result = _invoke_waf("send_email", {"to": "x@x.com", "body": "hi"})
    assert "[WAF ERROR]" in result


def test_agent_graph_compiles(monkeypatch):
    """The ReAct agent graph should compile without errors."""
    monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-test")
    # Re-import to pick up the env var
    import agents.config
    monkeypatch.setattr(agents.config, "GROQ_API_KEY", "fake-key-for-test")

    from agents.graph import create_agent_graph
    graph = create_agent_graph(system_prompt="Test prompt")
    assert graph is not None


def test_orchestrator_compiles():
    """The multi-agent orchestrator graph should compile without errors."""
    from agents.orchestrator import create_orchestrator

    orch = create_orchestrator()
    assert orch is not None
