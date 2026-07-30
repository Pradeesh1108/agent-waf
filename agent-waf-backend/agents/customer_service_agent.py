"""
Customer Service Agent.

A specialised LangGraph agent for handling customer support tasks —
lookups, emails, refunds.  Every tool call is routed through the WAF
proxy automatically via the waf_tools layer.
"""

import uuid
from langchain_core.messages import HumanMessage

from .graph import create_agent_graph
from .prompts import CUSTOMER_SERVICE_PROMPT
from .waf_tools import set_agent_context
from .config import AGENT_SCOPES


def run_customer_service_agent(
    user_message: str,
    session_id: str | None = None,
) -> str:
    """
    Run the customer-service agent for a single user turn.

    Returns the agent's final text response.
    """
    session_id = session_id or str(uuid.uuid4())
    agent_id = "customer_service"

    # Set the WAF context so every tool call carries the right identity
    set_agent_context(
        agent_id=agent_id,
        session_id=session_id,
        declared_scope=AGENT_SCOPES.get(agent_id, []),
    )

    graph = create_agent_graph(system_prompt=CUSTOMER_SERVICE_PROMPT)

    result = graph.invoke(
        {"messages": [HumanMessage(content=user_message)]},
    )

    # Extract the last AI message as the response
    ai_messages = [
        m for m in result["messages"]
        if hasattr(m, "content") and m.content and not getattr(m, "tool_calls", None)
    ]
    return ai_messages[-1].content if ai_messages else "(no response)"
