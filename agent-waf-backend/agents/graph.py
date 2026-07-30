"""
LangGraph agent graph definitions.

This module contains the core ReAct-style agent graph that powers each
specialised agent.  The graph follows the standard pattern:

    agent (LLM decides) ──tool_call──▶ tools (execute via WAF) ──▶ agent
          │                                                           │
          └──no tool call──▶ END                                      │
                                                                      │
          ◀───────────────────────────────────────────────────────────┘

Each agent instance is created by `create_agent_graph()` which binds
the LLM, tools, and system prompt together into a compiled LangGraph.
"""

from typing import Annotated, Sequence
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from .config import GROQ_API_KEY, GROQ_MODEL
from .waf_tools import ALL_TOOLS


# ── Graph State ─────────────────────────────────────────────────────

class AgentState(TypedDict):
    """State that flows through every node in the agent graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]


# ── Graph Builder ───────────────────────────────────────────────────

def create_agent_graph(system_prompt: str, tools: list | None = None):
    """
    Build and compile a ReAct agent graph.

    Parameters
    ----------
    system_prompt : str
        Injected as a SystemMessage at the start of every conversation.
    tools : list, optional
        LangChain tools to bind.  Defaults to ALL_TOOLS.

    Returns
    -------
    compiled graph
        A LangGraph CompiledGraph ready to `.invoke()`.
    """
    if tools is None:
        tools = ALL_TOOLS

    # ── LLM with tool binding ───────────────────────────────────────
    llm = ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0,
    ).bind_tools(tools)

    # ── Node: agent ─────────────────────────────────────────────────
    def agent_node(state: AgentState):
        # Prepend the system prompt if the conversation is fresh
        messages = list(state["messages"])
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_prompt)] + messages
        response = llm.invoke(messages)
        return {"messages": [response]}

    # ── Node: tools ─────────────────────────────────────────────────
    tool_node = ToolNode(tools)

    # ── Routing ─────────────────────────────────────────────────────
    def should_continue(state: AgentState):
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    # ── Build graph ─────────────────────────────────────────────────
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
