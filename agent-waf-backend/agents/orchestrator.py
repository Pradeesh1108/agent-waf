"""
Multi-agent orchestrator — Supervisor pattern via LangGraph.

The Supervisor is an LLM-powered router that reads the user's request
and decides which specialised agent should handle it:

    User ──▶ Supervisor ──▶ customer_service | security_tester
                  ▲                │
                  └────────────────┘  (loop until FINISH)

This gives us a proper multi-agent system where:
- Each agent has its own identity, scope, and system prompt.
- The WAF enforces different policies per agent_id.
- The supervisor never calls tools directly — it only routes.
"""

import uuid
from typing import Annotated, Literal, Sequence
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from .config import GROQ_API_KEY, GROQ_MODEL
from .prompts import SUPERVISOR_PROMPT
from .customer_service_agent import run_customer_service_agent
from .security_tester_agent import run_security_tester_agent


# ── Orchestrator State ──────────────────────────────────────────────

class OrchestratorState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_agent: str
    session_id: str


# ── Nodes ───────────────────────────────────────────────────────────

def supervisor_node(state: OrchestratorState):
    """The supervisor reads the conversation and picks the next agent."""
    llm = ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0,
    )
    messages = [SystemMessage(content=SUPERVISOR_PROMPT)] + list(state["messages"])
    response = llm.invoke(messages)

    # Parse the routing decision from the LLM's text response
    decision = response.content.strip().lower()
    if "customer_service" in decision:
        next_agent = "customer_service"
    elif "security_tester" in decision:
        next_agent = "security_tester"
    else:
        next_agent = "FINISH"

    return {
        "messages": [AIMessage(content=f"[Supervisor] Routing to: {next_agent}")],
        "next_agent": next_agent,
    }


def customer_service_node(state: OrchestratorState):
    """Delegate to the customer-service agent sub-graph."""
    # Get the original user request (last HumanMessage)
    user_msg = ""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            user_msg = m.content
            break

    response = run_customer_service_agent(
        user_message=user_msg,
        session_id=state["session_id"],
    )
    return {"messages": [AIMessage(content=f"[Customer Service Agent]\n{response}")]}


def security_tester_node(state: OrchestratorState):
    """Delegate to the security-testing agent sub-graph."""
    user_msg = ""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            user_msg = m.content
            break

    response = run_security_tester_agent(
        test_instruction=user_msg,
        session_id=state["session_id"],
    )
    return {"messages": [AIMessage(content=f"[Security Tester Agent]\n{response}")]}


# ── Routing ─────────────────────────────────────────────────────────

def route_from_supervisor(state: OrchestratorState):
    next_agent = state.get("next_agent", "FINISH")
    if next_agent == "customer_service":
        return "customer_service"
    elif next_agent == "security_tester":
        return "security_tester"
    return END


# ── Build the orchestrator graph ────────────────────────────────────

def create_orchestrator():
    graph = StateGraph(OrchestratorState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("customer_service", customer_service_node)
    graph.add_node("security_tester", security_tester_node)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "customer_service": "customer_service",
            "security_tester": "security_tester",
            END: END,
        },
    )

    # After a worker finishes, end (single-turn routing).
    # For multi-turn, route back to supervisor instead.
    graph.add_edge("customer_service", END)
    graph.add_edge("security_tester", END)

    return graph.compile()


def run_orchestrator(user_message: str, session_id: str | None = None) -> str:
    """
    Top-level entry point.  Send a natural-language request and the
    supervisor decides which agent handles it.
    """
    session_id = session_id or str(uuid.uuid4())
    orchestrator = create_orchestrator()

    result = orchestrator.invoke({
        "messages": [HumanMessage(content=user_message)],
        "next_agent": "",
        "session_id": session_id,
    })

    # Return the last AI message
    ai_msgs = [m for m in result["messages"] if isinstance(m, AIMessage)]
    return ai_msgs[-1].content if ai_msgs else "(no response)"
