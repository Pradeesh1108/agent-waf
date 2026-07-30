"""
Agent WAF — Agentic Layer

This package contains LangChain/LangGraph-powered agents that interact
with the WAF proxy. Every tool call an agent makes is routed through
the WAF's /invoke endpoint for inspection, filtering, and logging.
"""
