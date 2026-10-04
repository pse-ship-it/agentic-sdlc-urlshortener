# Apex-SDLC: Agentic Software Engineering System (URL Shortener)

> **Enterprise Agentic SDLC Automation with Governed, Controlled Autonomy**  
> *Built for Charles Schwab Architectural & Agentic Engineering Assessment*

---

## 1. Executive Summary

**Apex-SDLC** is a production-grade Agentic Software Engineering platform designed to automate the entire Software Development Life Cycle (SDLC) with **governed, controlled autonomy**. Rather than relying on simple linear prompt chaining, Apex-SDLC implements a **non-linear, stateful Directed Acyclic Graph (DAG) orchestration engine** with entry/exit gates, cross-stage synchronization barriers, cryptographic decision lineage, bounded self-healing retries, and transactional workspace rollbacks.

The target system synthesized and evolved by the orchestrator is **PulseURL**, an enterprise-ready URL Shortener service built with FastAPI, SQLAlchemy, Base62 encoding, sliding-window rate limiting, Server-Side Request Forgery (SSRF) defense, and multi-dimensional click analytics.

---

## 2. Key Differentiators & Schwab Evaluation Alignment

| Evaluation Criteria | Apex-SDLC Implementation | Key Source Files |
| :--- | :--- | :--- |
| **Workflow Orchestration** | Non-linear DAG engine with parallel group execution, synchronization barriers, and dynamic re-planning. | [`orchestrator/dag_engine.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/dag_engine.py) |
| **Controlled Autonomy Tiers** | 4-tier autonomy governance model enforcing Human-in-the-Loop (HITL) checkpoints on high-impact actions (Tier 3). | [`orchestrator/models.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/models.py) |
| **Entry & Exit Governance Gates** | Explicit predicate evaluation before and after tasks (ambiguity score, test pass rate, 0 critical security flaws). | [`orchestrator/gates.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/gates.py) |
| **Resilience & Safe-Stop** | Bounded retries with exponential backoff, error feedback self-healing, and git-like snapshot rollback. | [`orchestrator/safety.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/safety.py) |
| **Decision Lineage & Audit Trail** | SHA-256 Merkle-like provenance linking decisions, rationales, rejected alternatives, inputs, and outputs. | [`orchestrator/lineage.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/lineage.py) |
| **Codebase Reasoning (Brownfield)** | Static AST analysis mapping module imports, impacted files, data flows, and breaking changes. | [`agents/codebase_reasoner.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/agents/codebase_reasoner.py) |
| **Ambiguity Gating & Re-planning** | Intent analysis detecting underspecified requests, halting premature execution, and dynamically re-wiring the DAG. | [`scenarios/scenario_3_ambiguous.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/scenarios/scenario_3_ambiguous.py) |
| **Reliability Telemetry** | Automated computation of Success Rate (%), MTTR (s), Phase Latencies (s), and Retry Frequencies. | [`orchestrator/metrics.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/metrics.py) |

---

## 3. Quickstart & How to Run

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Dependencies installed: `pip install fastapi uvicorn pydantic pytest httpx sqlalchemy`

### 1. Run Complete Verification & Scenario Suite
Execute all unit/integration tests and all 3 SDLC scenarios in a single command:
```bash
python run_all.py
```

### 2. Launch Interactive Web Console & Dashboard
Start the visual dashboard server:
```bash
python ui/dashboard.py
```
Open **`http://127.0.0.1:8000`** in your browser to:
- Visually trigger Greenfield, Brownfield, and Ambiguous scenarios with 1 click.
- Watch live DAG stage transitions (Pending &rarr; Running &rarr; Completed &rarr; Synced).
- Review cryptographic Decision Lineage entries in real time.
- Test the URL Shortener in the interactive sandbox (generate links, trigger redirects, and inspect live click analytics).

### 3. Run Standalone CLI Runner
```bash
# Run specific scenario
python cli.py --scenario greenfield
python cli.py --scenario brownfield
python cli.py --scenario ambiguous

# Run all scenarios
python cli.py --scenario all
```

### 4. Run Automated Pytest Suite
```bash
pytest tests/ -v
```

---

## 4. The Three Demonstration Scenarios

### Scenario 1: Greenfield Implementation
- **Objective**: Build the complete URL shortener system from a raw high-level requirement.
- **Workflow**:
  1. `RequirementAnalyzer`: Normalizes requirements into functional & acceptance criteria.
  2. `Architect`: Produces OpenAPI contracts, database schemas, and threat model.
  3. `Implementer`: Synthesizes modular codebase with Base62 encoding and SQLite persistence.
  4. Parallel Sync Group (`QualityEngineer` & `SecurityComplianceGuard`): Executes unit tests and SSRF security audits concurrently, synchronizing at a barrier.
  5. `DocEngineer`: Formulates developer runbook and OpenAPI specification.
  6. `HumanApprovalGate`: Tier 3 gatekeeper authorizing production release candidate.

### Scenario 2: Brownfield AST Codebase Evolution
- **Objective**: Add real-time click analytics and sliding-window rate limiting to the existing service without breaking redirect performance.
- **Workflow**:
  1. `CodebaseReasoner`: Scans Python AST across the repository to map dependencies, identifying impacted files (`routes.py`, `database.py`, `ratelimit.py`, `analytics.py`).
  2. `Architect`: Designs zero-downtime schema evolution (additive `ClickEvent` table).
  3. `Implementer`: Implements sliding-window token bucket and async click telemetry.
  4. Parallel Regression Group: Verifies backward compatibility of existing endpoints while testing new features.
  5. `HumanApprovalGate`: Reviews migration impact analysis and authorizes database update.

### Scenario 3: Ambiguous Intent & Dynamic Re-planning
- **Objective**: Process a vague prompt: *"Make the URL shortener enterprise-ready, safe, and robust."*
- **Workflow**:
  1. `RequirementAnalyzer`: Computes an ambiguity score of **0.85** (exceeds the 0.30 threshold).
  2. Entry Gate Block: Halts downstream architecture execution to prevent speculative coding.
  3. Human Clarification Dialogue: Clarifies rate limits (60 req/min), SSRF loopback protections, and approval policies.
  4. Re-normalization: Ambiguity score drops to **0.05**.
  5. Dynamic Re-Planning (`engine.dynamic_replan()`): Dynamically restructures the DAG, inserting hardening tasks and unblocking execution.

---

## 5. Target Application: PulseURL API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/urls` | Shorten URL with optional custom alias and TTL expiration in seconds. |
| `GET` | `/{short_code}` | High-performance HTTP 307 redirect with asynchronous click telemetry capture. |
| `GET` | `/api/v1/urls/{short_code}` | Inspect link metadata (creation timestamp, expiration, total clicks). |
| `GET` | `/api/v1/urls/{short_code}/analytics` | Retrieve analytics summary (referrers, device breakdown, recent event log). |
| `DELETE` | `/api/v1/urls/{short_code}` | Deactivate/expire short link. |
| `GET` | `/api/v1/health` | Health check probe. |

### Sample cURL Usage

```bash
# 1. Shorten URL
curl -X POST http://127.0.0.1:8000/api/v1/urls \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.schwab.com/trading", "custom_alias": "schwab-trade", "ttl_seconds": 3600}'

# 2. Access Redirection
curl -i http://127.0.0.1:8000/schwab-trade

# 3. View Analytics Breakdown
curl http://127.0.0.1:8000/api/v1/urls/schwab-trade/analytics
```

---

## 6. Project Layout

```
agentic-sdlc-urlshortener/
├── orchestrator/               # Core Agentic SDLC Engine
│   ├── dag_engine.py           # Stateful non-linear DAG executor & scheduler
│   ├── gates.py                # Entry and exit policy gatekeeper
│   ├── lineage.py              # Cryptographic decision provenance & Merkle audit trail
│   ├── safety.py               # Bounded retries, safe-stop, and workspace snapshot rollback
│   ├── metrics.py              # Telemetry collector (MTTR, Success Rate, Latencies)
│   ├── models.py               # Pydantic data schemas & state models
│   └── llm_provider.py         # Deterministic simulator + live Gemini model adapter
├── agents/                     # Specialized SDLC Agents
│   ├── base_agent.py           # Structured execution contracts & base class
│   ├── requirement_agent.py    # Intent normalization & ambiguity scoring
│   ├── architect_agent.py      # Architecture blueprints, OpenAPI specs & threat model
│   ├── codebase_reasoner.py    # Static AST codebase reasoning & impact mapping
│   ├── implementer_agent.py    # Multi-file implementation & AST syntax validation
│   ├── tester_agent.py         # Automated test suite generation & pass rate gating
│   ├── security_agent.py       # SSRF prevention, secret scanning & policy guardrails
│   └── doc_agent.py            # OpenAPI docs & release runbook generation
├── url_shortener/              # Target Production URL Shortener (PulseURL)
│   ├── main.py                 # FastAPI application & lifespan management
│   ├── routes.py               # Route handlers (shorten, redirect, analytics, metadata)
│   ├── shortener.py            # Base62 encoding engine & collision resolution
│   ├── database.py             # SQLAlchemy models (URLRecord, ClickEvent) & SQLite engine
│   ├── security.py             # SSRF guardrail, domain blocklist & IP anonymization
│   ├── ratelimit.py            # Sliding-window token bucket rate limiter
│   └── config.py               # Application configuration settings
├── scenarios/                  # Three Executable Scenarios
│   ├── scenario_1_greenfield.py
│   ├── scenario_2_brownfield.py
│   └── scenario_3_ambiguous.py
├── tests/                      # Automated Verification Test Suites
│   ├── test_shortener_service.py
│   ├── test_analytics_and_security.py
│   ├── test_dag_orchestrator.py
│   └── test_lineage_and_metrics.py
├── ui/                         # Visual Web Console
│   ├── dashboard.py            # FastAPI dashboard server & API
│   └── static/index.html       # Responsive real-time console UI
├── cli.py                      # Interactive terminal CLI runner
├── run_all.py                  # Single-command test and scenario verification script
├── ARCHITECTURE.md             # In-depth architectural treatise & state machine design
├── SCENARIOS.md                # Detailed walkthrough logs of the 3 scenarios
└── EVALUATION_GUIDE.md         # Schwab evaluation criteria cross-reference guide
```
