# Agent WAF

## Tech Stack
- **Backend:** FastAPI, Python (managed via `uv`), LangChain, LangGraph
- **Frontend:** React, Vite, TailwindCSS
- **State Management:** In-Memory (with DynamoDB support built-in for AWS)
- **LLM Provider:** Groq API (Llama3-8b-8192)

---

## Problem Statement

### Context
AI Agents are rapidly gaining autonomy, capable of invoking tools, accessing databases, and performing actions on behalf of users. However, current Web Application Firewalls (WAFs) are built exclusively for traditional HTTP REST APIs. They rely on network-level heuristics (like IP rate-limiting or payload matching) and are completely blind to the intent and context of an AI agent's tool invocations. This leaves organizations without a robust, intent-aware security layer to verify if an agent is allowed to access specific data scopes, call tools in a specific sequence, or if they are executing dangerous, hallucinated parameters. 

### The Challenge
Build a policy-enforcing proxy between AI agents and their tools that transparently inspects, filters, and logs every tool invocation in real time based on declarative security rules.

### What to Build
- A transparent proxy layer that intercepts all tool calls from a sample agent.
- A rule engine with at least these rule types: 
  - **Rate limit:** Agent may call Tool X no more than N times per minute.
  - **Parameter validation:** Reject calls where parameter values match a blocklist or exceed size limits.
  - **Data scope:** Reject calls that reference data outside the agent's declared scope.
  - **Sequence rules:** Reject calls to Tool B unless Tool A was called first in this session.
- Each intercepted call is logged with timestamp, agent ID, tool, parameters sanitised, rule evaluation outcome, and final disposition.
- A real-time dashboard showing tool call traffic and block events.

### Success Criteria
- [x] Rate limit fires correctly after N calls within the window.
- [x] Parameter blocklist catches a simulated injection attempt in a tool parameter.
- [x] Out-of-scope data access is blocked.
- [x] Sequence rule enforcement correctly blocks a tool called out of expected order.
- [x] Dashboard updates in real time as calls flow through.

---

## What We Have Done (Case Study)

For this hackathon, we built a fully functional, production-ready **Agent WAF Microservice Architecture**, strictly decoupling the frontend dashboard from the backend rule engine to demonstrate scalability. 

### 1. The Proxy Architecture
We developed a transparent proxy layer in FastAPI that sits exactly between the LangChain/LangGraph agent execution environment and the downstream Tool Registry. The agent uses `@tool` wrappers that do not execute code locally, but instead serialize the LLM's intent into an HTTP POST request to the WAF. The WAF evaluates the request against `policies.yaml` and only forwards it to the execution registry if all rules pass.

### 2. The Rule Engine
The core of the WAF is the dynamic rule engine supporting:
*   **Rate Limiting**: Sliding window counters per tool.
*   **Parameter Blocklists**: Regex evaluations to instantly block SQL injections (e.g. `1 OR 1=1; DROP TABLE`).
*   **Data Scoping**: Validates if the agent is authorized to access the specific `customer_id` it requested.
*   **Sequence Enforcement**: Maintains session state to ensure prerequisites (e.g. `get_customer_record` MUST be called before `refund_payment`).
*   **Shadow Mode**: A critical enterprise feature where a rule can be toggled to `shadow: true`. This allows the WAF to silently log rule violations without actually blocking the live agent, enabling safe testing of new policies in production!

### 3. Real-Time Dashboard
We built a beautiful, dark-mode React/Vite dashboard to visualize the WAF's activity. The dashboard actively polls the backend and renders high-precision (millisecond) absolute timestamps to perfectly trace rapid, sequential LLM tool calls. The UI explicitly visualizes the rule configurations (Enforce vs Shadow mode) and graphs real-time blocked vs allowed traffic.

### 4. Agent Simulation
To prove the WAF works in an actual AI environment, we utilized **LangGraph** to build a multi-agent orchestrator. A Supervisor agent routes user prompts to specialized workers (e.g., a Customer Service Agent and a Security Tester Agent). These agents use the Groq API to reason about the user's prompt and invoke tools, which are seamlessly intercepted by our WAF.

### Architecture Diagram

```mermaid
graph TD
    subgraph "Agentic Layer (LangGraph + Groq)"
        Supervisor[Supervisor Agent]
        CSAgent[Customer Service Agent]
        STAgent[Security Tester Agent]
        
        Supervisor --> CSAgent
        Supervisor --> STAgent
    end

    subgraph "WAF Proxy (FastAPI)"
        Proxy[POST /invoke]
        RuleEngine[Rule Engine / policies.yaml]
        State[State Manager / Audit Logs]
        
        Proxy --> RuleEngine
        RuleEngine --> State
    end

    subgraph "Execution Layer"
        Tools[Tool Registry (Actual execution)]
    end
    
    subgraph "Frontend (React/Vite)"
        Dashboard[Real-time Dashboard]
        LogsAPI[GET /logs]
        
        Dashboard -- "Polls every 1.4s" --> LogsAPI
    end

    CSAgent -- "Tool Calls" --> Proxy
    STAgent -- "Malicious Calls" --> Proxy
    
    RuleEngine -- "Allowed" --> Tools
    RuleEngine -- "Blocked (403)" --> Proxy
    
    State --> LogsAPI
```

---

## Quick Start

### 1. Setup Environment
```bash
uv venv
source .venv/bin/activate
uv pip install -r agent-waf-backend/requirements.txt
```

### 2. Add API Keys
Copy `.env.example` to `.env` and add your Groq API key:
```bash
cp .env.example .env
# Edit .env and add GROQ_API_KEY
```

### 3. Run the Full Stack
We have provided a unified script to run both the FastAPI backend and the React frontend simultaneously:
```bash
cd agent-waf-backend
./run_all.sh
```

### 4. View the Dashboard
Open your browser to: [http://localhost:5173](http://localhost:5173)

### 5. Trigger the AI Agents
While the dashboard is running, open a new terminal and run the agentic demo to see the WAF block the LLM in real-time:
```bash
cd agent-waf-backend
source .venv/bin/activate
PYTHONPATH=. python -m agents.demo --agentic
```
