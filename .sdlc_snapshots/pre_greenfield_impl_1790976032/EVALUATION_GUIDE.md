# Charles Schwab Evaluation Criteria & Implementation Mapping Guide

This document provides a line-by-line mapping from each requirement in the Schwab interview specification to the exact implementation files, functions, and architecture decisions in this repository.

---

## 1. Core Requirements Mapping

### 1.1 Requirement Understanding & Ambiguity Normalization
> *"Interpret intent, identify ambiguity, normalize into a clear engineering problem."*
- **Implementation**: [`agents/requirement_agent.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/agents/requirement_agent.py)
  - Method `execute()`: Computes an `ambiguity_score` (0.0 to 1.0) based on specificity, extracts intent, and identifies missing specifications.
  - Normalization: Transforms raw user prompt into a structured engineering specification with 5 functional requirements, 4 non-functional requirements, and 5 RFC-style acceptance criteria.
  - Demonstrated in: [`scenarios/scenario_3_ambiguous.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/scenarios/scenario_3_ambiguous.py) where a score of 0.85 halts execution at the entry gate.

### 1.2 Task Decomposition & Explicit Dependencies
> *"Convert high-level requirements into actionable tasks with dependencies and sequencing."*
- **Implementation**: [`orchestrator/models.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/models.py) & [`orchestrator/dag_engine.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/dag_engine.py)
  - Class `TaskNode`: Encapsulates task ID, stage, agent role, `dependencies: List[str]`, `parallel_group: Optional[str]`, and autonomy tier.
  - Class `DAG`: Resolves topological dependencies via `is_ready_to_run(node_id)` and verifies DAG acyclicity.
  - Demonstrated in: All three scenarios (`scenarios/scenario_1_greenfield.py`, etc.).

### 1.3 Codebase Reasoning (Brownfield)
> *"Identify impacted modules/services/APIs/data flows and demonstrate architectural understanding."*
- **Implementation**: [`agents/codebase_reasoner.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/agents/codebase_reasoner.py)
  - Method `scan_codebase()`: Uses Python's native `ast` module to statically parse classes, functions, and import graphs across the repository without running untrusted code.
  - Impact Analysis: Mappings in `execute()` identify impacted files (e.g. `routes.py`, `database.py`, `ratelimit.py`, `analytics.py`), formulate data flow changes, and construct a zero-downtime migration strategy.
  - Demonstrated in: [`scenarios/scenario_2_brownfield.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/scenarios/scenario_2_brownfield.py).

### 1.4 Workflow Orchestration (Critical Differentiator)
> *"Design and implement an agentic orchestration layer that coordinates the full SDLC lifecycle... demonstrates non-linear, stateful execution with governance rather than simple linear task chaining."*

| Feature Required | Implementation Mechanism | Exact File & Function |
| :--- | :--- | :--- |
| **Explicit Dependency Graph** | Directed graph with dependency checking and ready-node scheduling | [`orchestrator/dag_engine.py:run_sync()`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/dag_engine.py) |
| **Entry & Exit Gates** | Explicit predicate evaluation before and after task execution | [`orchestrator/gates.py:EntryExitGateKeeper`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/gates.py) |
| **Parallel Paths & Sync Barriers** | `ThreadPoolExecutor` concurrent execution across `parallel_group` with join barrier | [`orchestrator/dag_engine.py:lines 110-120`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/dag_engine.py) |
| **Cross-Stage Context & Lineage** | Shared context dictionary and Merkle-chained decision tracker | [`orchestrator/lineage.py:LineageTracker`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/lineage.py) |
| **Human Approval Checkpoints** | Interception of Tier 3 tasks, halting execution for engineering sign-off | [`orchestrator/dag_engine.py:lines 144-165`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/dag_engine.py) |
| **Bounded Retries & Backoff** | $2^{(n-1)}$ exponential backoff with error diagnostic feedback loops | [`orchestrator/safety.py:BoundedRetryController`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/safety.py) |
| **Transactional Rollback & Safe-Stop** | Pre-mutation workspace snapshots and instant rollback on failure | [`orchestrator/safety.py:WorkspaceSnapshotManager`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/safety.py) |
| **Policy Guardrails & Security** | SSRF loopback defense, sliding-window rate limits, secret scanning | [`url_shortener/security.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/url_shortener/security.py) & [`agents/security_agent.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/agents/security_agent.py) |
| **Audit-Grade Traceability** | Merkle audit trail chaining previous decision hash with current artifacts | [`orchestrator/lineage.py:export_audit_trail()`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/lineage.py) |
| **Reliability Telemetry Tracking** | Tracks Success Rate, MTTR (Mean Time to Repair), and Latency per stage | [`orchestrator/metrics.py:MetricsCollector`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/metrics.py) |
| **Dynamic Re-planning** | Injects new tasks, modifies dependencies, and clears downstream errors | [`orchestrator/dag_engine.py:dynamic_replan()`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/orchestrator/dag_engine.py) |

### 1.5 Engineering Output Generation
> *"Produce production-quality code, API/schema definitions, unit/integration tests, and supporting documentation with clean design and maintainability."*
- **Code Quality**: Clean layered architecture adhering to PEP 8, typed with Pydantic v2 and SQLAlchemy 2.0.
- **API Contracts**: OpenAPI-compliant endpoints for shortening, redirecting, analytics, and metadata inspection.
- **Automated Tests**: 15 unit and integration tests passing with 100% pass rate in [`tests/`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/tests/).
- **Documentation**: Comprehensive [`README.md`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/README.md), [`ARCHITECTURE.md`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/ARCHITECTURE.md), and [`SCENARIOS.md`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/SCENARIOS.md).

### 1.6 Validation & Risk Control
> *"Identify risks/trade-offs/failure scenarios and define validation and safety guardrails."*
- **SSRF Protection**: Resolves target hostnames against DNS and blocks direct access to loopback (`127.0.0.1`), link-local (`169.254.0.0/16`), and private RFC 1918 subnets (`10.0.0.0/8`, `192.168.0.0/16`).
- **DoS / Scraping Defense**: Sliding-window token bucket algorithm in [`url_shortener/ratelimit.py`](file:///C:/Users/prasu/.gemini/antigravity/scratch/agentic-sdlc-urlshortener/url_shortener/ratelimit.py) enforcing default 60 req/min with HTTP 429 response.
- **Hash Collision Handling**: Base62 salted linear probing with maximum 5 attempts.
- **Data Privacy**: Salted SHA-256 IP anonymization for GDPR/enterprise compliance.

### 1.7 Controlled Autonomy Principle
> *"Agents execute multi-step work; humans provide oversight, approvals, and final quality control."*
- Tier 0 & Tier 1 execute autonomously under gate constraints.
- Tier 2 executes with automated pre-mutation snapshots and test verification.
- Tier 3 requires explicit human confirmation via CLI or the Web Dashboard modal.

---

## 2. Deliverables Checklist

- [x] **Working Prototype (runnable end-to-end)**: Accessible via `python run_all.py` and `python ui/dashboard.py`.
- [x] **Architecture Overview**: Complete design document in `ARCHITECTURE.md`.
- [x] **Three Scenarios**: Runnable scripts in `scenarios/` (Greenfield, Brownfield, Ambiguous).
- [x] **Setup Instructions**: Detailed in `README.md`.
- [x] **Testing Approach, Limitations, and Trade-offs**: Covered in `tests/`, `ARCHITECTURE.md`, and test reports.
