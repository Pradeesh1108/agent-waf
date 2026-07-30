"""
Security Testing Agent.

A specialised LangGraph agent that deliberately probes the WAF to
verify that each rule type fires correctly.  Used for demo/audit
purposes.
"""

import uuid
from langchain_core.messages import HumanMessage

from .graph import create_agent_graph
from .prompts import SECURITY_TESTER_PROMPT
from .waf_tools import set_agent_context
from .config import AGENT_SCOPES


def run_security_tester_agent(
    test_instruction: str,
    session_id: str | None = None,
) -> str:
    """
    Run the security-testing agent with a specific instruction
    (e.g. "Try an SQL injection in a tool parameter").

    Returns the agent's test report.
    """
    session_id = session_id or str(uuid.uuid4())
    agent_id = "security_tester"

    set_agent_context(
        agent_id=agent_id,
        session_id=session_id,
        declared_scope=AGENT_SCOPES.get(agent_id, []),
    )

    graph = create_agent_graph(system_prompt=SECURITY_TESTER_PROMPT)

    result = graph.invoke(
        {"messages": [HumanMessage(content=test_instruction)]},
    )

    ai_messages = [
        m for m in result["messages"]
        if hasattr(m, "content") and m.content and not getattr(m, "tool_calls", None)
    ]
    return ai_messages[-1].content if ai_messages else "(no response)"
