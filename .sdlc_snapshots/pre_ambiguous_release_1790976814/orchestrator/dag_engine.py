"""
Stateful, Non-Linear DAG Workflow Orchestration Engine.
Coordinates parallel execution, entry/exit gates, lineage capture, bounded retries, and dynamic re-planning.
"""

from __future__ import annotations
import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor

from .models import (
    TaskNode,
    TaskStatus,
    DAG,
    SDLCState,
    GateStatus,
    AutonomyLevel,
    LifecycleStage
)
from .gates import EntryExitGateKeeper
from .lineage import LineageTracker
from .safety import WorkspaceSnapshotManager, BoundedRetryController, SafeStopException
from .metrics import MetricsCollector


class DAGEngine:
    def __init__(
        self,
        state: SDLCState,
        workspace_root: str,
        gatekeeper: Optional[EntryExitGateKeeper] = None,
        auto_approve_tier3: bool = False
    ):
        self.state = state
        self.workspace_root = workspace_root
        self.gatekeeper = gatekeeper or EntryExitGateKeeper()
        self.lineage = LineageTracker(state.run_id)
        self.safety = WorkspaceSnapshotManager(workspace_root)
        self.retries = BoundedRetryController(default_max_retries=3)
        self.metrics = MetricsCollector(state.run_id, state.scenario_name)
        self.auto_approve_tier3 = auto_approve_tier3

        # Agent execution dispatch registry
        self.agent_executors: Dict[str, Callable[[TaskNode, Dict[str, Any]], Dict[str, Any]]] = {}
        # Event callbacks for CLI and Web UI
        self.event_listeners: List[Callable[[str, Dict[str, Any]], None]] = []

    def register_agent(self, role_name: str, executor: Callable[[TaskNode, Dict[str, Any]], Dict[str, Any]]) -> None:
        self.agent_executors[role_name] = executor

    def add_event_listener(self, listener: Callable[[str, Dict[str, Any]], None]) -> None:
        self.event_listeners.append(listener)

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        for listener in self.event_listeners:
            try:
                listener(event_type, data)
            except Exception:
                pass

    def run_sync(self) -> SDLCState:
        """Executes the DAG to completion or until blocked by a human approval or safe-stop."""
        self._emit_event("pipeline_started", {"run_id": self.state.run_id, "scenario": self.state.scenario_name})
        initial_snap = self.safety.create_snapshot("initial_baseline", "Initial baseline before execution")
        self.state.shared_context["latest_snapshot_id"] = initial_snap

        while True:
            # Find all nodes that are ready to run (dependencies satisfied & status is PENDING)
            ready_nodes = [
                node for node in self.state.dag.nodes.values()
                if self.state.dag.is_ready_to_run(node.id)
            ]

            if not ready_nodes:
                # Check if all completed or if any blocked/waiting
                pending = [n for n in self.state.dag.nodes.values() if n.status == TaskStatus.PENDING]
                waiting = [n for n in self.state.dag.nodes.values() if n.status == TaskStatus.WAITING_APPROVAL]
                failed = [n for n in self.state.dag.nodes.values() if n.status in (TaskStatus.FAILED, TaskStatus.ROLLED_BACK)]

                if waiting:
                    self._emit_event("pipeline_paused_human_approval", {"waiting_nodes": [n.id for n in waiting]})
                    break
                if failed or not pending:
                    break

                # Pending nodes exist but none can run -> Unschedulable / deadlocked dependency
                self._emit_event("pipeline_deadlock_detected", {"unresolved_nodes": [n.id for n in pending]})
                for n in pending:
                    n.status = TaskStatus.BLOCKED
                    n.error_message = "Unresolved or missing prerequisite dependency in DAG."
                break

            # Group ready nodes by parallel group if present
            parallel_batches: Dict[str, List[TaskNode]] = {}
            sequential_nodes: List[TaskNode] = []

            for node in ready_nodes:
                if node.parallel_group:
                    parallel_batches.setdefault(node.parallel_group, []).append(node)
                else:
                    sequential_nodes.append(node)

            # Execute sequential nodes first
            for node in sequential_nodes:
                success = self._execute_node(node)
                if not success and node.status in (TaskStatus.FAILED, TaskStatus.ROLLED_BACK):
                    break

            # Execute parallel batch with synchronization barrier
            for group_name, p_nodes in parallel_batches.items():
                self._emit_event("parallel_group_started", {"group": group_name, "tasks": [n.id for n in p_nodes]})
                with ThreadPoolExecutor(max_workers=len(p_nodes)) as executor:
                    futures = [executor.submit(self._execute_node, n) for n in p_nodes]
                    for f in futures:
                        f.result()
                self._emit_event("parallel_group_synced", {"group": group_name})

        self.state.metrics = self.metrics.finalize()
        self.state.decisions = self.lineage.records
        self._emit_event("pipeline_completed", {"metrics": self.state.metrics.model_dump()})
        return self.state

    def _execute_node(self, node: TaskNode) -> bool:
        """Executes a single task node through its full governed lifecycle."""
        node.status = TaskStatus.RUNNING
        node.started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        start_time = time.time()
        self.metrics.start_stage(node.stage.value)
        self._emit_event("node_started", {"node_id": node.id, "name": node.name, "stage": node.stage.value})

        # 1. Evaluate Entry Gates
        self.state.shared_context["dag"] = self.state.dag
        entry_gate_res = self.gatekeeper.evaluate_entry_gates(node, self.state.shared_context)
        self.state.gate_results.append(entry_gate_res)

        if entry_gate_res.status != GateStatus.PASSED:
            node.status = TaskStatus.FAILED
            node.error_message = f"Entry gate failed: {entry_gate_res.message}"
            self.metrics.record_node_failed(node.id)
            self._emit_event("node_gate_failed", {"node_id": node.id, "gate": entry_gate_res.gate_name, "message": entry_gate_res.message})
            return False

        # 2. Check Autonomy Level & Human Approval Gate (Tier 3)
        if node.autonomy_level == AutonomyLevel.TIER_3_HIGH_IMPACT:
            self.metrics.record_approval_request()
            if self.auto_approve_tier3:
                if "human_approval_status" not in self.state.shared_context:
                    self.state.shared_context["human_approval_status"] = {}
                self.state.shared_context["human_approval_status"][node.id] = "APPROVED"
                self.metrics.record_approval_decision(True)
            else:
                approval_status = self.state.shared_context.get("human_approval_status", {}).get(node.id)
                if approval_status != "APPROVED":
                    node.status = TaskStatus.WAITING_APPROVAL
                    self._emit_event("human_approval_required", {
                        "node_id": node.id,
                        "name": node.name,
                        "description": f"Tier 3 High-Impact action requires human authorization: {node.name}"
                    })
                    return False
                self.metrics.record_approval_decision(True)

        # 3. Create pre-mutation snapshot if node modifies code/schemas
        if node.autonomy_level in (AutonomyLevel.TIER_2_CODE_CHANGE, AutonomyLevel.TIER_3_HIGH_IMPACT):
            snap_id = f"pre_{node.id}_{int(time.time())}"
            self.safety.create_snapshot(snap_id, f"Snapshot before {node.id}")
            self.state.shared_context["latest_snapshot_id"] = snap_id

        # 4. Agent Execution with Bounded Retry Loop
        attempt = 0
        while attempt <= node.max_retries:
            attempt += 1
            node.retry_count = attempt - 1
            try:
                executor = self.agent_executors.get(node.agent_role)
                if not executor:
                    raise ValueError(f"No agent registered for role: '{node.agent_role}'")

                output = executor(node, self.state.shared_context)
                node.output_payload = output
                self.state.shared_context[node.id] = output

                # Record decision lineage
                decision_summary = output.get("decision_summary", f"Completed {node.name}")
                rationale = output.get("rationale", "Standard architectural progression")
                alternatives = output.get("alternatives_rejected", [])
                self.lineage.record_decision(
                    stage=node.stage.value,
                    task_id=node.id,
                    decision=decision_summary,
                    rationale=rationale,
                    alternatives_rejected=alternatives,
                    input_data=node.input_payload,
                    output_data=output
                )

                # 5. Evaluate Exit Gates
                exit_gate_res = self.gatekeeper.evaluate_exit_gates(node, self.state.shared_context)
                self.state.gate_results.append(exit_gate_res)

                if exit_gate_res.status == GateStatus.PASSED:
                    # Success
                    node.status = TaskStatus.COMPLETED
                    node.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    node.duration_seconds = round(time.time() - start_time, 3)
                    self.metrics.record_node_completed(node.id)
                    self.metrics.end_stage(node.stage.value)
                    self._emit_event("node_completed", {"node_id": node.id, "duration": node.duration_seconds})
                    return True
                else:
                    # Exit gate failed
                    raise ValueError(f"Exit gate rejected: {exit_gate_res.message}")

            except Exception as e:
                err_msg = str(e)
                node.error_message = err_msg
                repair_start = time.time()

                if self.retries.should_retry(node.id, attempt - 1, node.max_retries):
                    backoff = self.retries.get_backoff(attempt)
                    self.retries.record_retry(node.id, attempt, err_msg, f"Self-correcting with backoff {backoff}s")
                    self._emit_event("node_retrying", {
                        "node_id": node.id,
                        "attempt": attempt,
                        "error": err_msg,
                        "backoff": backoff
                    })
                    time.sleep(min(backoff, 0.5))  # Sleep up to 0.5s for fast interactive testing
                    repair_duration = time.time() - repair_start
                    self.metrics.record_retry(node.id, attempt, repair_duration)
                    # Feed error back into node input for self-healing
                    node.input_payload["previous_error"] = err_msg
                    node.input_payload["attempt"] = attempt
                else:
                    # Retry limit exhausted -> Safe-Stop & Rollback
                    node.status = TaskStatus.ROLLED_BACK
                    last_snap = self.state.shared_context.get("latest_snapshot_id")
                    if last_snap:
                        self.safety.rollback(last_snap)
                        self.metrics.record_rollback(last_snap, f"Exhausted retries on {node.id}: {err_msg}")
                        self._emit_event("node_rolled_back", {"node_id": node.id, "snapshot": last_snap, "error": err_msg})
                    else:
                        node.status = TaskStatus.FAILED
                    self.metrics.record_node_failed(node.id)
                    return False

        return False

    def dynamic_replan(self, new_nodes: List[TaskNode], invalidate_node_ids: Optional[List[str]] = None) -> None:
        """
        Dynamically adjusts the DAG when upstream outputs or requirements change.
        Allows adding new tasks, updating dependencies, and resetting downstream stages.
        """
        self._emit_event("replan_triggered", {
            "new_nodes": [n.id for n in new_nodes],
            "invalidated": invalidate_node_ids or []
        })

        # Invalidate specific downstream nodes if requested
        if invalidate_node_ids:
            for n_id in invalidate_node_ids:
                if n_id in self.state.dag.nodes:
                    target = self.state.dag.nodes[n_id]
                    target.status = TaskStatus.PENDING
                    target.retry_count = 0
                    target.error_message = None

        # Insert new nodes
        for node in new_nodes:
            self.state.dag.add_node(node)

        self.lineage.record_decision(
            stage="DYNAMIC_REPLAN",
            task_id="dag_replan",
            decision=f"Inserted {len(new_nodes)} dynamic tasks into execution graph",
            rationale="Upstream requirement modification or test failure triggered dynamic branch restructuring."
        )

    def submit_human_approval(self, node_id: str, approved: bool, feedback: str = "") -> None:
        """Called by human reviewer via UI or CLI to approve or reject a Tier 3 action."""
        if "human_approval_status" not in self.state.shared_context:
            self.state.shared_context["human_approval_status"] = {}

        self.state.shared_context["human_approval_status"][node_id] = "APPROVED" if approved else "REJECTED"
        self.state.shared_context[f"{node_id}_human_feedback"] = feedback

        self.lineage.record_decision(
            stage=LifecycleStage.HUMAN_APPROVAL.value,
            task_id=node_id,
            decision="Approved by Human Reviewer" if approved else "Rejected by Human Reviewer",
            rationale=feedback or "Reviewer approved candidate for release."
        )
        self._emit_event("human_approval_submitted", {"node_id": node_id, "approved": approved, "feedback": feedback})
