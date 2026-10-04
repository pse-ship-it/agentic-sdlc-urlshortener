"""
Scenario 1: Greenfield Implementation.
Builds the core URL Shortener system from scratch through all SDLC phases.
Demonstrates:
- Non-linear DAG with parallel branches (testing & security)
- Synchronization barrier before documentation
- Cryptographic decision lineage
- Governance entry/exit gates
- Human-in-the-Loop release signoff
"""

from __future__ import annotations
import os
import sys

# Ensure root directory is on sys.path
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
from agents.requirement_agent import RequirementAgent
from agents.architect_agent import ArchitectAgent
from agents.implementer_agent import ImplementerAgent
from agents.tester_agent import TesterAgent
from agents.security_agent import SecurityComplianceAgent
from agents.doc_agent import DocumentationAgent


def run_greenfield_scenario(auto_approve_human_gate: bool = True) -> SDLCState:
    print("\n" + "="*80)
    print(">>> RUNNING SCENARIO 1: GREENFIELD URL SHORTENER SYSTEM GENERATION <<<")
    print("="*80)

    raw_requirement = (
        "Build a production-grade URL shortener service with Base62 shortcode generation, "
        "collision resolution, SQLite persistence, URL validation, and redirect capability."
    )

    # 1. Construct explicit SDLC DAG
    dag = DAG()

    t1_req = TaskNode(
        id="greenfield_req",
        name="Requirement Analysis & Specification",
        stage=LifecycleStage.REQUIREMENT_ANALYSIS,
        agent_role="RequirementAnalyzer",
        autonomy_level=AutonomyLevel.TIER_0_READ_ONLY,
        entry_gates=["ambiguity_threshold"],
        exit_gates=[],
        input_payload={"raw_requirement": raw_requirement}
    )

    t2_arch = TaskNode(
        id="greenfield_arch",
        name="Architecture & API Schema Design",
        stage=LifecycleStage.ARCHITECTURE_DESIGN,
        agent_role="Architect",
        dependencies=["greenfield_req"],
        autonomy_level=AutonomyLevel.TIER_0_READ_ONLY,
        entry_gates=["dependencies_completed"],
        exit_gates=[]
    )

    t3_impl = TaskNode(
        id="greenfield_impl",
        name="Core Code Implementation",
        stage=LifecycleStage.IMPLEMENTATION,
        agent_role="Implementer",
        dependencies=["greenfield_arch"],
        autonomy_level=AutonomyLevel.TIER_2_CODE_CHANGE,
        entry_gates=["dependencies_completed", "contract_defined", "workspace_snapshot_ready"],
        exit_gates=["syntax_and_types"],
        input_payload={"target_module": "core_url_shortener"}
    )

    # Parallel branch 1: Testing
    t4a_test = TaskNode(
        id="greenfield_test",
        name="Unit & Integration Test Verification",
        stage=LifecycleStage.TESTING_VERIFICATION,
        agent_role="QualityEngineer",
        dependencies=["greenfield_impl"],
        parallel_group="verification_sync_group",
        autonomy_level=AutonomyLevel.TIER_1_LOW_RISK,
        entry_gates=["dependencies_completed"],
        exit_gates=["test_coverage_and_pass"],
        input_payload={"test_scope": "core_shortener_suite"}
    )

    # Parallel branch 2: Security & Compliance
    t4b_sec = TaskNode(
        id="greenfield_security",
        name="Security & SSRF Compliance Audit",
        stage=LifecycleStage.SECURITY_COMPLIANCE,
        agent_role="SecurityComplianceGuard",
        dependencies=["greenfield_impl"],
        parallel_group="verification_sync_group",
        autonomy_level=AutonomyLevel.TIER_1_LOW_RISK,
        entry_gates=["dependencies_completed"],
        exit_gates=["security_compliance"]
    )

    # Synchronization barrier node
    t5_doc = TaskNode(
        id="greenfield_doc",
        name="OpenAPI Documentation & Release Runbook",
        stage=LifecycleStage.DOCUMENTATION,
        agent_role="DocEngineer",
        dependencies=["greenfield_test", "greenfield_security"],
        autonomy_level=AutonomyLevel.TIER_1_LOW_RISK,
        entry_gates=["dependencies_completed"],
        exit_gates=["release_readiness"]
    )

    # Tier 3 Human-in-the-Loop Release Gate
    t6_release = TaskNode(
        id="greenfield_release",
        name="Production Release Readiness & Sign-off",
        stage=LifecycleStage.HUMAN_APPROVAL,
        agent_role="DocEngineer",
        dependencies=["t5_doc"],
        autonomy_level=AutonomyLevel.TIER_3_HIGH_IMPACT,
        entry_gates=["dependencies_completed"],
        exit_gates=["human_signoff"]
    )

    for node in [t1_req, t2_arch, t3_impl, t4a_test, t4b_sec, t5_doc, t6_release]:
        dag.add_node(node)

    # 2. Instantiate State & Engine
    state = SDLCState(
        scenario_name="Greenfield_URL_Shortener",
        raw_requirement=raw_requirement,
        dag=dag
    )

    engine = DAGEngine(state, workspace_root=BASE_DIR, auto_approve_tier3=auto_approve_human_gate)

    # Register specialized agents
    engine.register_agent("RequirementAnalyzer", RequirementAgent().execute)
    engine.register_agent("Architect", ArchitectAgent().execute)
    engine.register_agent("Implementer", ImplementerAgent(BASE_DIR).execute)
    engine.register_agent("QualityEngineer", TesterAgent(BASE_DIR).execute)
    engine.register_agent("SecurityComplianceGuard", SecurityComplianceAgent(BASE_DIR).execute)
    engine.register_agent("DocEngineer", DocumentationAgent(BASE_DIR).execute)

    # Event logger
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

    # Execute
    final_state = engine.run_sync()

    print("\n--- Greenfield Execution Summary ---")
    metrics = final_state.metrics
    print(f"  Total Nodes Executed: {metrics.completed_nodes}/{metrics.total_nodes}")
    print(f"  Success Rate: {metrics.success_rate_percent}%")
    print(f"  Total Duration: {metrics.total_duration_seconds}s")
    print(f"  Total Decisions Lineage Recorded: {len(final_state.decisions)}")
    print(f"  Cryptographic Merkle Audit Log Entries: {len(final_state.gate_results)}")
    print("="*80 + "\n")

    return final_state


if __name__ == "__main__":
    run_greenfield_scenario()
