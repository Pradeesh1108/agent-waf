"""
Sample Agent — backward-compatible entry point.

This file now delegates to the new LangChain/LangGraph-based agentic
layer in the `agents/` package.

Usage:
    python sample_agent/agent.py           # Interactive orchestrator
    python sample_agent/agent.py --demo    # Scripted WAF demo
    python sample_agent/agent.py --agentic # LLM-driven multi-agent demo
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.demo import main

if __name__ == "__main__":
    sys.exit(main())
