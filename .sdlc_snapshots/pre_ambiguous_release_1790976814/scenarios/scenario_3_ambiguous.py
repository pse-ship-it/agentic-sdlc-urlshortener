"""
Scenario 3: Ambiguity Interpretation, Gating, Interactive Clarification, and Dynamic Re-planning.
Handles vague, underspecified requests:
- Detects high ambiguity score (0.85 > 0.30 threshold)
- Fails entry gate, halting premature implementation
- Executes Human Clarification dialogue to resolve missing specifications
- Normalizes requirement into RFC-grade acceptance criteria
- Dynamically re-plans DAG by inserting security hardening and rate-limiting tasks
- Executes complete governed pipeline to release
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
    AutonomyLevel,
    TaskStatus
)
from orchestrator.dag_engine import DAGEngine
from agents.requirement_agent import RequirementAgent
from agents.architect_agent import ArchitectAgent
from agents.implementer_agent import ImplementerAgent
from agents.tester_agent import TesterAgent
from agents.security_agent import SecurityComplianceAgent
from agents.doc_agent import DocumentationAgent


def run_ambiguous_scenario(interactive: bool = False, auto_approve_human_gate: bool = True) -> SDLCState:
    print("\n" + "="*80)
    print(">>> RUNNING SCENARIO 3: AMBIGUITY DETECTION, CLARIFICATION & DYNAMIC RE-PLANNING <<<")
    print("="*80)

    vague_requirement = "Make the URL shortener enterprise-ready, safe, and robust."
    print(f"Initial Raw Requirement: \"{vague_requirement}\"\n")

    # 1. Build initial DAG
    dag = DAG()

    t1_ambiguity = TaskNode(
        id="ambiguity_eval",
        name="Ambiguity & Intent Scoring",
        stage=LifecycleStage.REQUIREMENT_ANALYSIS,
        agent_role="RequirementAnalyzer",
        autonomy_level=AutonomyLevel.TIER_0_READ_ONLY,
        entry_gates=[],
        exit_gates=[],
        input_payload={"raw_requirement": vague_requirement}
    )

    t2_arch = TaskNode(
        id="ambiguous_arch",
        name="Architecture & Threat Model Formulation",
        stage=LifecycleStage.ARCHITECTURE_DESIGN,
        agent_role="Architect",
        dependencies=["ambiguity_eval"],
        autonomy_level=AutonomyLevel.TIER_0_READ_ONLY,
        entry_gates=["dependencies_completed", "ambiguity_threshold"],  # Will fail if ambiguity > 0.30!
        exit_gates=[]
    )

    dag.add_node(t1_ambiguity)
    dag.add_node(t2_arch)

    state = SDLCState(
        scenario_name="Ambiguous_Requirement_Normalization",
        raw_requirement=vague_requirement,
        dag=dag
    )

    engine = DAGEngine(state, workspace_root=BASE_DIR, auto_approve_tier3=auto_approve_human_gate)
    req_agent = RequirementAgent()

    engine.register_agent("RequirementAnalyzer", req_agent.execute)
    engine.register_agent("Architect", ArchitectAgent().execute)
    engine.register_agent("Implementer", ImplementerAgent(BASE_DIR).execute)
    engine.register_agent("QualityEngineer", TesterAgent(BASE_DIR).execute)
    engine.register_agent("SecurityComplianceGuard", SecurityComplianceAgent(BASE_DIR).execute)
    engine.register_agent("DocEngineer", DocumentationAgent(BASE_DIR).execute)

    # Execute Phase 1: Ambiguity Evaluation & Gate Check
    print("[PHASE 1] Executing Ambiguity Evaluation...")
    engine.run_sync()

    ambiguity_node = state.dag.nodes["ambiguity_eval"]
    arch_node = state.dag.nodes["ambiguous_arch"]

    print(f"  Ambiguity Score Detected: {state.shared_context.get('ambiguity_score', 0.0):.2f}")
    print(f"  Architecture Node Status: {arch_node.status.value}")
    if arch_node.error_message:
        print(f"  Entry Gate Block Triggered: {arch_node.error_message}")

    # Phase 2: Human Clarification Checkpoint
    print("\n[PHASE 2] Human Clarification Checkpoint Activated")
    clarification_answers = {
        "rate_limiting": "Enforce sliding-window token bucket with 60 requests per minute per IP.",
        "ssrf_protection": "Prohibit private IPv4/IPv6 ranges (127.0.0.1, 10.0.0.0/8, 192.168.0.0/16).",
        "governance": "Require Tier 3 engineering sign-off before releasing database schema changes."
    }
    for q, a in clarification_answers.items():
        print(f"  Clarification [{q}]: {a}")

    # Phase 3: Requirement Normalization with Clarifications
    print("\n[PHASE 3] Normalizing Intent & Resolving Ambiguity...")
    state.shared_context["ambiguity_score"] = 0.05  # Ambiguity resolved
    state.shared_context["ambiguities"] = []
    normalized_spec = {
        "title": "Enterprise URL Shortener Hardened Specification",
        "clarified_scope": clarification_answers,
        "acceptance_criteria": [
            "HTTP 429 returned after 60 req/min sliding window",
            "SSRF rejection for private subnets",
            "Tier 3 Human sign-off required for release"
        ]
    }
    state.shared_context["normalized_specification"] = normalized_spec
    engine.lineage.record_decision(
        stage="REQUIREMENT_CLARIFICATION",
        task_id="ambiguity_eval",
        decision="Normalized ambiguous requirement through human feedback dialogue",
        rationale="Clarifications resolved rate limits, SSRF controls, and governance policies. Ambiguity score reduced to 0.05."
    )

    # Phase 4: Dynamic Re-Planning of the DAG
    print("\n[PHASE 4] Dynamic Re-Planning: Restructuring SDLC Dependency Graph...")
    arch_node.status = TaskStatus.PENDING
    arch_node.error_message = None

    t3_impl = TaskNode(
        id="ambiguous_impl",
        name="Enterprise Security & Hardening Implementation",
        stage=LifecycleStage.IMPLEMENTATION,
        agent_role="Implementer",
        dependencies=["ambiguous_arch"],
        autonomy_level=AutonomyLevel.TIER_2_CODE_CHANGE,
        entry_gates=["dependencies_completed", "contract_defined", "workspace_snapshot_ready"],
        exit_gates=["syntax_and_types"],
        input_payload={"target_module": "enterprise_hardened"}
    )

    t4_verify = TaskNode(
        id="ambiguous_verify",
        name="Security Policy & Hardening Test Suite",
        stage=LifecycleStage.TESTING_VERIFICATION,
        agent_role="QualityEngineer",
        dependencies=["ambiguous_impl"],
        autonomy_level=AutonomyLevel.TIER_1_LOW_RISK,
        entry_gates=["dependencies_completed"],
        exit_gates=["test_coverage_and_pass"]
    )

    t5_release = TaskNode(
        id="ambiguous_release",
        name="Enterprise Release Readiness & Sign-off",
        stage=LifecycleStage.HUMAN_APPROVAL,
        agent_role="DocEngineer",
        dependencies=["ambiguous_verify"],
        autonomy_level=AutonomyLevel.TIER_3_HIGH_IMPACT,
        entry_gates=["dependencies_completed"],
        exit_gates=["human_signoff"]
    )

    engine.dynamic_replan(new_nodes=[t3_impl, t4_verify, t5_release])

    # Phase 5: Resuming Governed Execution
    print("\n[PHASE 5] Resuming Governed Execution with Dynamic DAG...")
    final_state = engine.run_sync()

    print("\n--- Ambiguous Scenario Execution Summary ---")
    metrics = final_state.metrics
    print(f"  Total Nodes in Re-planned Graph: {len(final_state.dag.nodes)}")
    print(f"  Total Nodes Completed: {metrics.completed_nodes}")
    print(f"  Final Success Rate: {metrics.success_rate_percent}%")
    print(f"  Total Decisions Lineage Recorded: {len(final_state.decisions)}")
    print("="*80 + "\n")

    return final_state


if __name__ == "__main__":
    run_ambiguous_scenario()
