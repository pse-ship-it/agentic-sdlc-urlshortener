"""
Governance & Gate Control Layer.
Defines explicit entry and exit predicates for SDLC lifecycle stages.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from .models import GateResult, GateStatus, AutonomyLevel, TaskNode


class EntryExitGateKeeper:
    def __init__(self):
        self.entry_gates: Dict[str, Callable[[TaskNode, Dict[str, Any]], GateResult]] = {}
        self.exit_gates: Dict[str, Callable[[TaskNode, Dict[str, Any]], GateResult]] = {}
        self._register_default_gates()

    def _register_default_gates(self):
        # Entry Gates
        self.entry_gates["ambiguity_threshold"] = self._gate_ambiguity_threshold
        self.entry_gates["dependencies_completed"] = self._gate_dependencies_completed
        self.entry_gates["workspace_snapshot_ready"] = self._gate_snapshot_ready
        self.entry_gates["contract_defined"] = self._gate_contract_defined

        # Exit Gates
        self.exit_gates["test_coverage_and_pass"] = self._gate_test_coverage_and_pass
        self.exit_gates["security_compliance"] = self._gate_security_compliance
        self.exit_gates["human_signoff"] = self._gate_human_signoff
        self.exit_gates["release_readiness"] = self._gate_release_readiness
        self.exit_gates["syntax_and_types"] = self._gate_syntax_and_types

    # --- Entry Gate Implementations ---
    def _gate_ambiguity_threshold(self, node: TaskNode, context: Dict[str, Any]) -> GateResult:
        ambiguity_score = context.get("ambiguity_score", 0.0)
        max_allowed = 0.30
        if ambiguity_score > max_allowed:
            return GateResult(
                gate_name="ambiguity_threshold",
                stage=node.stage.value,
                status=GateStatus.FAILED,
                message=f"Ambiguity score {ambiguity_score:.2f} exceeds threshold {max_allowed}. Clarification required.",
                details={"ambiguity_score": ambiguity_score, "missing_specs": context.get("ambiguities", [])}
            )
        return GateResult(
            gate_name="ambiguity_threshold",
            stage=node.stage.value,
            status=GateStatus.PASSED,
            message=f"Ambiguity score {ambiguity_score:.2f} is within acceptable bounds."
        )

    def _gate_dependencies_completed(self, node: TaskNode, context: Dict[str, Any]) -> GateResult:
        dag = context.get("dag")
        if not dag:
            return GateResult(gate_name="dependencies_completed", stage=node.stage.value, status=GateStatus.PASSED, message="No DAG constraints.")

        for dep_id in node.dependencies:
            dep_node = dag.nodes.get(dep_id)
            if not dep_node or dep_node.status != "COMPLETED":
                return GateResult(
                    gate_name="dependencies_completed",
                    stage=node.stage.value,
                    status=GateStatus.FAILED,
                    message=f"Prerequisite dependency '{dep_id}' is not yet completed."
                )
        return GateResult(
            gate_name="dependencies_completed",
            stage=node.stage.value,
            status=GateStatus.PASSED,
            message="All prerequisite dependencies satisfied."
        )

    def _gate_snapshot_ready(self, node: TaskNode, context: Dict[str, Any]) -> GateResult:
        snapshot_id = context.get("latest_snapshot_id")
        if not snapshot_id and node.autonomy_level in (AutonomyLevel.TIER_2_CODE_CHANGE, AutonomyLevel.TIER_3_HIGH_IMPACT):
            return GateResult(
                gate_name="workspace_snapshot_ready",
                stage=node.stage.value,
                status=GateStatus.FAILED,
                message="Cannot execute mutating stage without active rollback snapshot."
            )
        return GateResult(
            gate_name="workspace_snapshot_ready",
            stage=node.stage.value,
            status=GateStatus.PASSED,
            message=f"Rollback snapshot '{snapshot_id}' verified."
        )

    def _gate_contract_defined(self, node: TaskNode, context: Dict[str, Any]) -> GateResult:
        api_spec = context.get("api_specification")
        if not api_spec and node.stage.value == "IMPLEMENTATION":
            return GateResult(
                gate_name="contract_defined",
                stage=node.stage.value,
                status=GateStatus.FAILED,
                message="Implementation cannot begin without prior Architecture/API Contract definition."
            )
        return GateResult(
            gate_name="contract_defined",
            stage=node.stage.value,
            status=GateStatus.PASSED,
            message="Architecture contract available."
        )

    # --- Exit Gate Implementations ---
    def _gate_test_coverage_and_pass(self, node: TaskNode, context: Dict[str, Any]) -> GateResult:
        test_results = node.output_payload.get("test_results") or context.get("test_results")
        if not test_results:
            return GateResult(
                gate_name="test_coverage_and_pass",
                stage=node.stage.value,
                status=GateStatus.FAILED,
                message="No test results recorded for verification."
            )

        failed_count = test_results.get("failed", 0)
        pass_rate = test_results.get("pass_rate", 0.0)

        if failed_count > 0 or pass_rate < 1.0:
            return GateResult(
                gate_name="test_coverage_and_pass",
                stage=node.stage.value,
                status=GateStatus.FAILED,
                message=f"Tests failed: {failed_count} failing tests. Pass rate: {pass_rate*100:.1f}%.",
                details=test_results
            )
        return GateResult(
            gate_name="test_coverage_and_pass",
            stage=node.stage.value,
            status=GateStatus.PASSED,
            message=f"All {test_results.get('total', 0)} tests passed with 100% pass rate."
        )

    def _gate_security_compliance(self, node: TaskNode, context: Dict[str, Any]) -> GateResult:
        security_findings = node.output_payload.get("security_findings") or context.get("security_findings", {})
        critical_vulns = security_findings.get("critical_vulnerabilities", 0)
        high_vulns = security_findings.get("high_vulnerabilities", 0)
        ssrf_guarded = security_findings.get("ssrf_protection_verified", True)

        if critical_vulns > 0 or high_vulns > 0 or not ssrf_guarded:
            return GateResult(
                gate_name="security_compliance",
                stage=node.stage.value,
                status=GateStatus.FAILED,
                message=f"Security policy rejection: {critical_vulns} critical, {high_vulns} high vulnerabilities found.",
                details=security_findings
            )
        return GateResult(
            gate_name="security_compliance",
            stage=node.stage.value,
            status=GateStatus.PASSED,
            message="Security & compliance gate satisfied: 0 high/critical issues, SSRF defenses active."
        )

    def _gate_human_signoff(self, node: TaskNode, context: Dict[str, Any]) -> GateResult:
        # If node requires Tier 3 autonomy or explicit human approval
        approval_status = context.get("human_approval_status", {}).get(node.id)
        if approval_status == "APPROVED":
            return GateResult(
                gate_name="human_signoff",
                stage=node.stage.value,
                status=GateStatus.PASSED,
                message="Human approval granted by engineering reviewer."
            )
        elif approval_status == "REJECTED":
            return GateResult(
                gate_name="human_signoff",
                stage=node.stage.value,
                status=GateStatus.FAILED,
                message="Human reviewer rejected release candidate."
            )
        else:
            return GateResult(
                gate_name="human_signoff",
                stage=node.stage.value,
                status=GateStatus.WAITING_HUMAN,
                message="Awaiting Human-in-the-Loop review & sign-off."
            )

    def _gate_release_readiness(self, node: TaskNode, context: Dict[str, Any]) -> GateResult:
        readiness_score = node.output_payload.get("readiness_score", 0.0)
        if readiness_score < 0.90:
            return GateResult(
                gate_name="release_readiness",
                stage=node.stage.value,
                status=GateStatus.FAILED,
                message=f"Readiness score {readiness_score*100:.1f}% below minimum 90.0% threshold."
            )
        return GateResult(
            gate_name="release_readiness",
            stage=node.stage.value,
            status=GateStatus.PASSED,
            message=f"Release readiness score {readiness_score*100:.1f}% meets enterprise standards."
        )

    def _gate_syntax_and_types(self, node: TaskNode, context: Dict[str, Any]) -> GateResult:
        syntax_errors = node.output_payload.get("syntax_errors", 0)
        if syntax_errors > 0:
            return GateResult(
                gate_name="syntax_and_types",
                stage=node.stage.value,
                status=GateStatus.FAILED,
                message=f"Syntax analysis found {syntax_errors} parser errors."
            )
        return GateResult(
            gate_name="syntax_and_types",
            stage=node.stage.value,
            status=GateStatus.PASSED,
            message="Syntax and AST validations passed."
        )

    # --- Verification Orchestrator ---
    def evaluate_entry_gates(self, node: TaskNode, context: Dict[str, Any]) -> GateResult:
        for gate_name in node.entry_gates:
            evaluator = self.entry_gates.get(gate_name)
            if evaluator:
                result = evaluator(node, context)
                if result.status != GateStatus.PASSED:
                    return result
        return GateResult(gate_name="all_entry_gates", stage=node.stage.value, status=GateStatus.PASSED, message="All entry gates satisfied.")

    def evaluate_exit_gates(self, node: TaskNode, context: Dict[str, Any]) -> GateResult:
        for gate_name in node.exit_gates:
            evaluator = self.exit_gates.get(gate_name)
            if evaluator:
                result = evaluator(node, context)
                if result.status != GateStatus.PASSED:
                    return result
        return GateResult(gate_name="all_exit_gates", stage=node.stage.value, status=GateStatus.PASSED, message="All exit gates satisfied.")
