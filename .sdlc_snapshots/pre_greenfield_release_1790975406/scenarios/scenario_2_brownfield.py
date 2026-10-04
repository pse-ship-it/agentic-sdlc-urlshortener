"""
Scenario 2: Brownfield Feature Evolution & AST Codebase Reasoning.
Enhances existing URL Shortener with Analytics and Sliding-Window Rate Limiting.
Demonstrates:
- Static AST parsing and codebase dependency mapping
- Impact analysis and breaking-change hazard detection
- Zero-downtime database migration strategy
- Regression testing verifying existing API contracts
- Governance gates and human sign-off on schema migrations
"""

from __future__ import annotations
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from orchestrator.models import (
    SDLCState,
    DAG,
    TaskNode,
    LifecycleStage,
    AutonomyLevel
)
from orchestrator.dag_engine import DAGEngine
from agents.codebase_reasoner import CodebaseReasonerAgent
from agents.architect_agent import ArchitectAgent
from agents.implementer_agent import ImplementerAgent
from agents.tester_agent import TesterAgent
from agents.security_agent import SecurityComplianceAgent
from agents.doc_agent import DocumentationAgent


def run_brownfield_scenario(auto_approve_human_gate: bool = True) -> SDLCState:
    print("\n" + "="*80)
    print(">>> RUNNING SCENARIO 2: BROWNFIELD CODEBASE EVOLUTION & IMPACT ANALYSIS <<<")
    print("="*80)

    feature_requirement = (
        "Enhance the existing URL shortener service with click analytics (tracking referrers, "
        "user agents, device types, timestamps) and sliding-window rate limiting without breaking "
        "existing redirect performance or database records."
    )

    dag = DAG()

    # 1. AST Codebase Reasoning Node
    t1_reasoning = TaskNode(
        id="bf_ast_reasoning",
        name="AST Codebase Reasoning & Impact Mapping",
        stage=LifecycleStage.CODEBASE_REASONING,
        agent_role="CodebaseReasoner",
        autonomy_level=AutonomyLevel.TIER_0_READ_ONLY,
        entry_gates=[],
        exit_gates=[],
        input_payload={"enhancement_description": feature_requirement}
    )

    # 2. Additive Migration Architecture
    t2_arch = TaskNode(
        id="bf_migration_arch",
        name="Zero-Downtime Migration & Non-Breaking API Design",
        stage=LifecycleStage.ARCHITECTURE_DESIGN,
        agent_role="Architect",
        dependencies=["bf_ast_reasoning"],
        autonomy_level=AutonomyLevel.TIER_0_READ_ONLY,
        entry_gates=["dependencies_completed"],
        exit_gates=[]
    )

    # 3. Targeted Implementation
    t3_impl = TaskNode(
        id="bf_impl",
        name="Targeted Analytics & Rate Limiter Implementation",
        stage=LifecycleStage.IMPLEMENTATION,
        agent_role="Implementer",
        dependencies=["bf_migration_arch"],
        autonomy_level=AutonomyLevel.TIER_2_CODE_CHANGE,
        entry_gates=["dependencies_completed", "contract_defined", "workspace_snapshot_ready"],
        exit_gates=["syntax_and_types"],
        input_payload={"target_module": "analytics_and_ratelimit"}
    )

    # Parallel branch A: Regression Testing
    t4a_regression = TaskNode(
        id="bf_regression_tests",
        name="Backward Compatibility & Regression Suite",
        stage=LifecycleStage.TESTING_VERIFICATION,
        agent_role="QualityEngineer",
        dependencies=["bf_impl"],
        parallel_group="bf_validation_sync",
        autonomy_level=AutonomyLevel.TIER_1_LOW_RISK,
        entry_gates=["dependencies_completed"],
        exit_gates=["test_coverage_and_pass"],
        input_payload={"test_scope": "backward_compatibility_regression"}
    )

    # Parallel branch B: Security & Latency Profiling
    t4b_security = TaskNode(
        id="bf_security_audit",
        name="Security Policy & DoS Protection Audit",
        stage=LifecycleStage.SECURITY_COMPLIANCE,
        agent_role="SecurityComplianceGuard",
        dependencies=["bf_impl"],
        parallel_group="bf_validation_sync",
        autonomy_level=AutonomyLevel.TIER_1_LOW_RISK,
        entry_gates=["dependencies_completed"],
        exit_gates=["security_compliance"]
    )

    # Synchronization Barrier
    t5_doc = TaskNode(
        id="bf_doc_update",
        name="API Documentation & Migration Runbook Update",
        stage=LifecycleStage.DOCUMENTATION,
        agent_role="DocEngineer",
        dependencies=["bf_regression_tests", "bf_security_audit"],
        autonomy_level=AutonomyLevel.TIER_1_LOW_RISK,
        entry_gates=["dependencies_completed"],
        exit_gates=["release_readiness"]
    )

    # Tier 3 Human Sign-off for Database Schema Migration
    t6_human_gate = TaskNode(
        id="bf_schema_migration_approval",
        name="Database Schema Migration & Zero-Downtime Sign-off",
        stage=LifecycleStage.HUMAN_APPROVAL,
        agent_role="DocEngineer",
        dependencies=["bf_doc_update"],
        autonomy_level=AutonomyLevel.TIER_3_HIGH_IMPACT,
        entry_gates=["dependencies_completed"],
        exit_gates=["human_signoff"]
    )

    for node in [t1_reasoning, t2_arch, t3_impl, t4a_regression, t4b_security, t5_doc, t6_human_gate]:
        dag.add_node(node)

    state = SDLCState(
        scenario_name="Brownfield_Analytics_and_RateLimiting",
        raw_requirement=feature_requirement,
        dag=dag
    )

    engine = DAGEngine(state, workspace_root=BASE_DIR, auto_approve_tier3=auto_approve_human_gate)

    engine.register_agent("CodebaseReasoner", CodebaseReasonerAgent(BASE_DIR).execute)
    engine.register_agent("Architect", ArchitectAgent().execute)
    engine.register_agent("Implementer", ImplementerAgent(BASE_DIR).execute)
    engine.register_agent("QualityEngineer", TesterAgent(BASE_DIR).execute)
    engine.register_agent("SecurityComplianceGuard", SecurityComplianceAgent(BASE_DIR).execute)
    engine.register_agent("DocEngineer", DocumentationAgent(BASE_DIR).execute)

    def on_event(event_type: str, data: dict):
        if event_type == "node_started":
            print(f"  [RUNNING] Node: {data['name']} (Stage: {data['stage']})")
        elif event_type == "node_completed":
            print(f"  [COMPLETED] Node: {data['node_id']} in {data['duration']}s")
        elif event_type == "parallel_group_started":
            print(f"  [PARALLEL] Executing group '{data['group']}' across tasks: {data['tasks']}")
        elif event_type == "parallel_group_synced":
            print(f"  [SYNC-BARRIER] Parallel group '{data['group']}' synchronized successfully.")
        elif event_type == "human_approval_required":
            print(f"  [HITL GATE] High-Impact checkpoint reached: {data['description']}")

    engine.add_event_listener(on_event)

    final_state = engine.run_sync()

    print("\n--- Brownfield Execution Summary ---")
    metrics = final_state.metrics
    print(f"  Total Nodes Executed: {metrics.completed_nodes}/{metrics.total_nodes}")
    print(f"  Success Rate: {metrics.success_rate_percent}%")
    print(f"  Total Duration: {metrics.total_duration_seconds}s")
    print(f"  Total Decisions Lineage Recorded: {len(final_state.decisions)}")
    print(f"  Impacted Files Discovered via AST: {len(final_state.shared_context.get('brownfield_impact_analysis', {}).get('impacted_files', []))}")
    for f in final_state.shared_context.get('brownfield_impact_analysis', {}).get('impacted_files', []):
        print(f"    - {f}")
    print("="*80 + "\n")

    return final_state


if __name__ == "__main__":
    run_brownfield_scenario()
