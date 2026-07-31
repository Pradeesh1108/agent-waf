import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.state import state_manager

client = TestClient(app, headers={"X-WAF-API-Key": "super-secret-key"})

@pytest.fixture(autouse=True)
def clear_state():
    state_manager._in_memory_logs = []
    state_manager._in_memory_rate_counters = {}
    state_manager._in_memory_session_sequence = {}
    yield

def test_rate_limit_blocks_after_max():
    for i in range(3):
        resp = client.post("/invoke", json={
            "agent_id": "agent1",
            "session_id": "sess1",
            "tool": "send_email",
            "parameters": {"to": "test@test.com", "body": "hello"}
        })
        assert resp.status_code == 200
        
    resp = client.post("/invoke", json={
        "agent_id": "agent1",
        "session_id": "sess1",
        "tool": "send_email",
        "parameters": {"to": "test@test.com", "body": "hello"}
    })
    assert resp.status_code == 403
    assert resp.json()["detail"]["disposition"] == "block"
    assert any(r["rule_name"] == "rate_limit_send_email" and not r["allowed"] for r in resp.json()["detail"]["rule_results"])

def test_param_blocklist_blocks_sql_injection():
    resp = client.post("/invoke", json={
        "agent_id": "agent1",
        "session_id": "sess2",
        "tool": "get_customer_record",
        "parameters": {"customer_id": "123 OR 1=1"}
    })
    assert resp.status_code == 403
    assert any(r["rule_name"] == "blocklist_sql_injection" and not r["allowed"] for r in resp.json()["detail"]["rule_results"])

def test_data_scope_blocks_unauthorized_id():
    resp = client.post("/invoke", json={
        "agent_id": "agent1",
        "session_id": "sess3",
        "tool": "get_customer_record",
        "parameters": {"customer_id": "cust_999"},
        "declared_scope": ["cust_123", "cust_456"]
    })
    assert resp.status_code == 403
    assert any(r["rule_name"] == "scope_data_access" and not r["allowed"] for r in resp.json()["detail"]["rule_results"])

def test_sequence_blocks_out_of_order():
    resp = client.post("/invoke", json={
        "agent_id": "agent1",
        "session_id": "sess4",
        "tool": "refund_payment",
        "parameters": {"payment_id": "pay_123"}
    })
    assert resp.status_code == 403
    assert any(r["rule_name"] == "enforce_sequence" and not r["allowed"] for r in resp.json()["detail"]["rule_results"])
    
def test_shadow_mode_logs_but_allows():
    resp = client.post("/invoke", json={
        "agent_id": "agent1",
        "session_id": "sess5",
        "tool": "run_query",
        "parameters": {"query": "valid_query"}
    })
    assert resp.status_code == 200
    
    resp = client.post("/invoke", json={
        "agent_id": "agent1",
        "session_id": "sess5",
        "tool": "run_query",
        "parameters": {"query": "valid_query"}
    })
    assert resp.status_code == 200
    
    logs = client.get("/logs").json()["logs"]
    assert len(logs) >= 2
    
    # The two requests might have the same timestamp, so check both
    shadow_blocked = False
    for log in logs[:2]:
        shadow_result = next((r for r in log["rule_results"] if r["rule_name"] == "shadow_rate_limit_query"), None)
        if shadow_result and shadow_result["allowed"] is False:
            shadow_blocked = True
            assert shadow_result["shadow"] is True
            break
            
    assert shadow_blocked, "Shadow rule did not trigger as blocked"
