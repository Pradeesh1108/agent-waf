"""
Demo runner — exercises every WAF rule type through the agentic layer.

This replaces the old sample_agent/agent.py with a fully agentic
approach:  real LLM calls → LangChain tools → WAF proxy → audit log.

Usage:
    # Interactive orchestrator mode (supervisor routes to agents)
    python -m agents.demo

    # Scripted demo hitting all 5 success criteria
    python -m agents.demo --demo

    # Run only the customer-service agent
    python -m agents.demo --agent customer_service "Look up customer cust_123"

    # Run only the security-tester agent
    python -m agents.demo --agent security_tester "Try SQL injection"
"""

import argparse
import sys
import time
import uuid

from .orchestrator import run_orchestrator
from .customer_service_agent import run_customer_service_agent
from .security_tester_agent import run_security_tester_agent
from .waf_tools import set_agent_context, _invoke_waf
from .config import AGENT_SCOPES


# ── Scripted Demo ───────────────────────────────────────────────────

def run_scripted_demo():
    """
    Scripted demo that deterministically triggers each WAF rule.
    Uses raw WAF calls for predictability (the LLM may phrase things
    differently), but each call still goes through the full WAF pipeline.
    """
    print("=" * 70)
    print("  AGENT WAF — SCRIPTED DEMO")
    print("  Triggers all 5 success criteria via the WAF proxy")
    print("=" * 70)

    # ── Demo 1: Rate Limiting ───────────────────────────────────────
    print("\n📋 DEMO 1: Rate Limit (send_email, max 3 per 60s)")
    print("-" * 50)
    session_id = str(uuid.uuid4())
    set_agent_context("demo_agent", session_id, declared_scope=["cust_123"])

    for i in range(4):
        result = _invoke_waf("send_email", {"to": f"user{i}@test.com", "body": "hi"})
        status = "✅ ALLOWED" if "[BLOCKED" not in result else "🚫 BLOCKED"
        print(f"  Call {i+1}/4: {status}")
        if "[BLOCKED" in result:
            print(f"    → {result}")

    # ── Demo 2: Parameter Blocklist ─────────────────────────────────
    print("\n📋 DEMO 2: Parameter Blocklist (SQL injection attempt)")
    print("-" * 50)
    session_id = str(uuid.uuid4())
    set_agent_context("demo_agent", session_id, declared_scope=["cust_123"])
    result = _invoke_waf("get_customer_record", {"customer_id": "1 OR 1=1; DROP TABLE users;"})
    print(f"  Result: {result}")

    # ── Demo 3: Data Scope Violation ────────────────────────────────
    print("\n📋 DEMO 3: Data Scope Violation (unauthorized customer)")
    print("-" * 50)
    session_id = str(uuid.uuid4())
    set_agent_context("demo_agent", session_id, declared_scope=["cust_123"])
    result = _invoke_waf("get_customer_record", {"customer_id": "cust_UNAUTHORIZED"})
    print(f"  Result: {result}")

    # ── Demo 4: Sequence Violation ──────────────────────────────────
    print("\n📋 DEMO 4: Sequence Violation (refund before lookup)")
    print("-" * 50)
    session_id = str(uuid.uuid4())
    set_agent_context("demo_agent", session_id, declared_scope=["cust_123"])
    result = _invoke_waf("refund_payment", {"payment_id": "pay_999"})
    print(f"  Refund without lookup: {result}")

    print("\n  Now doing it correctly (lookup first, then refund):")
    session_id_ok = str(uuid.uuid4())
    set_agent_context("demo_agent", session_id_ok, declared_scope=["cust_123"])
    result1 = _invoke_waf("get_customer_record", {"customer_id": "cust_123"})
    print(f"  1. Lookup: {'✅' if '[BLOCKED' not in result1 else '🚫'}")
    result2 = _invoke_waf("refund_payment", {"payment_id": "pay_001"})
    print(f"  2. Refund: {'✅' if '[BLOCKED' not in result2 else '🚫'}")

    # ── Demo 5: Shadow Mode ─────────────────────────────────────────
    print("\n📋 DEMO 5: Shadow Mode (run_query, limit 1 — shadow only)")
    print("-" * 50)
    session_id = str(uuid.uuid4())
    set_agent_context("demo_agent", session_id, declared_scope=["cust_123"])
    result1 = _invoke_waf("run_query", {"query": "SELECT name FROM users"})
    print(f"  Call 1: ✅ ALLOWED (result: {result1[:60]})")
    result2 = _invoke_waf("run_query", {"query": "SELECT id FROM orders"})
    status2 = "✅ ALLOWED (shadow logged)" if "[BLOCKED" not in result2 else "🚫 BLOCKED"
    print(f"  Call 2: {status2}")

    print("\n" + "=" * 70)
    print("  Demo complete!  Check the dashboard to see all events.")
    print("=" * 70)


# ── LLM-driven Agentic Demo ────────────────────────────────────────

def run_agentic_demos():
    """Run LLM-driven agents through the orchestrator."""
    print("=" * 70)
    print("  AGENT WAF — LLM-DRIVEN AGENTIC DEMO")
    print("  Real LLM deciding which tools to call, routed by supervisor")
    print("=" * 70)

    demos = [
        ("Look up customer cust_123 and send them a welcome email.", "Customer lookup + email"),
        ("Test the WAF: try calling get_customer_record with the value '1 OR 1=1'.", "Security probe"),
        ("Process a refund for payment pay_001 for customer cust_123.", "Refund workflow"),
    ]

    for prompt, label in demos:
        print(f"\n📨 [{label}] Prompt: {prompt}")
        print("-" * 50)
        try:
            response = run_orchestrator(prompt)
            print(f"  Response:\n{response}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        time.sleep(1)

    print("\n" + "=" * 70)
    print("  Agentic demo complete!")
    print("=" * 70)


# ── CLI ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Agent WAF Demo Runner")
    parser.add_argument("--demo", action="store_true", help="Run scripted demo")
    parser.add_argument("--agentic", action="store_true", help="Run LLM-driven agentic demo")
    parser.add_argument("--agent", type=str, choices=["customer_service", "security_tester"], help="Run a specific agent")
    parser.add_argument("prompt", nargs="?", default=None, help="Prompt for the agent")
    args = parser.parse_args()

    if args.demo:
        run_scripted_demo()
    elif args.agentic:
        run_agentic_demos()
    elif args.agent and args.prompt:
        if args.agent == "customer_service":
            print(run_customer_service_agent(args.prompt))
        else:
            print(run_security_tester_agent(args.prompt))
    else:
        # Default: interactive orchestrator
        print("Agent WAF — Interactive Mode (type 'quit' to exit)")
        while True:
            try:
                user_input = input("\n🧑 You: ").strip()
                if user_input.lower() in ("quit", "exit", "q"):
                    break
                response = run_orchestrator(user_input)
                print(f"\n🤖 Agent: {response}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
