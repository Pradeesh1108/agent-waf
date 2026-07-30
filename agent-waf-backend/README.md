# Agent WAF

A **policy-enforcing proxy** between AI agents and their tools that inspects, filters, and logs every tool invocation in real time. Built with a fully **agentic, modular** architecture using **LangChain + LangGraph**.

## Architecture

```
User Request
     │
     ▼
┌──────────────────────────────────────────────────┐
│  Multi-Agent Orchestrator (LangGraph)            │
│  ┌────────────────┐   ┌───────────────────────┐  │
│  │ Supervisor     │──▶│ Customer Service Agent │  │
│  │ (routes tasks) │   │ (lookups, emails,      │  │
│  │                │   │  refunds)              │  │
│  │                │──▶│ Security Tester Agent  │  │
│  │                │   │ (WAF rule probing)     │  │
│  └────────────────┘   └───────────┬───────────┘  │
│                                   │               │
│  Each agent uses LangChain tools  │               │
│  that route through the WAF ──────┘               │
└───────────────────────────┬──────────────────────┘
                            │  HTTP POST /invoke
                            ▼
┌──────────────────────────────────────────────────┐
│  WAF Proxy (FastAPI + Lambda/Mangum)             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Rule     │  │ Tool     │  │ State Manager│   │
│  │ Engine   │  │ Registry │  │ (DynamoDB /  │   │
│  │          │  │          │  │  In-Memory)  │   │
│  └──────────┘  └──────────┘  └──────────────┘   │
└──────────────────────────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────┐
            │  Live Dashboard (HTML/JS) │
            │  Polls /logs every 1s     │
            └───────────────────────────┘
```

## Project Structure

```
agent-waf-backend/
├── agents/                         # Agentic layer (LangChain + LangGraph)
│   ├── config.py                   # LLM provider, WAF URL, scope mappings
│   ├── waf_tools.py                # LangChain tools → WAF /invoke proxy
│   ├── prompts.py                  # System prompts per agent role
│   ├── graph.py                    # LangGraph ReAct agent graph builder
│   ├── customer_service_agent.py   # Customer support agent
│   ├── security_tester_agent.py    # WAF rule validation agent
│   ├── orchestrator.py             # Multi-agent supervisor (LangGraph)
│   └── demo.py                     # CLI demo runner
├── app/                            # WAF Proxy Service (FastAPI)
│   ├── main.py                     # POST /invoke, GET /health, /logs, /dashboard
│   ├── models.py                   # Pydantic request/response models
│   ├── rules.py                    # Rule engine (loads policies.yaml)
│   ├── state.py                    # DynamoDB + in-memory state manager
│   ├── tools.py                    # Mock downstream tools
│   ├── policies.yaml               # Declarative rule configuration
│   └── logging_config.py           # Structured JSON logging
├── dashboard/
│   └── index.html                  # Real-time polling dashboard
├── infra/
│   └── template.yaml               # AWS SAM deployment template
├── sample_agent/
│   └── agent.py                    # Backward-compat entry point → agents/
├── tests/
│   ├── test_rules.py               # WAF rule unit tests
│   └── test_agents.py              # Agent layer unit tests
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Setup
```bash
cd agent-waf-backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. Start the WAF Proxy (in-memory mode for local dev)
```bash
uvicorn app.main:app --reload
```

### 3. Open the Dashboard
[http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)

### 4. Run the Scripted Demo (no API key needed)
```bash
PYTHONPATH=. python -m agents.demo --demo
```
This triggers all 5 success criteria through the WAF.

### 5. Run the LLM-driven Agentic Demo
```bash
export GROQ_API_KEY="your-key-here"
PYTHONPATH=. python -m agents.demo --agentic
```
The supervisor routes tasks to specialised agents, each making real LLM-driven tool calls through the WAF.

### 6. Interactive Mode
```bash
export GROQ_API_KEY="your-key-here"
PYTHONPATH=. python -m agents.demo
```

### 7. Run Tests
```bash
PYTHONPATH=. pytest tests/ -v
```

## WAF Rule Types

| Rule | Description | Config Key |
|------|-------------|------------|
| **rate_limit** | Max N calls per M-second window (atomic DynamoDB counter) | `max_calls`, `window_seconds` |
| **param_blocklist** | Reject params matching regex patterns or exceeding length | `patterns`, `max_length` |
| **data_scope** | Reject access to data outside agent's declared scope | `tools`, `id_params` |
| **sequence** | Require Tool A before Tool B in a session | `tool`, `depends_on` |

**Bonus: Shadow Mode** — any rule can have `shadow: true` to log what it *would* block without actually blocking.

## AWS Deployment
```bash
sam build --template-file infra/template.yaml
sam deploy --guided
export WAF_URL="https://YOUR_API_ID.execute-api.REGION.amazonaws.com"
PYTHONPATH=. python -m agents.demo --demo
```
