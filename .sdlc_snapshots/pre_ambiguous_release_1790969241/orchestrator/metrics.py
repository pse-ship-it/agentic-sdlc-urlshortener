"""
Reliability, Performance & Telemetry Metrics Collector.
Computes success rates, retry/rollback frequencies, MTTR, and phase latencies.
"""

from __future__ import annotations
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from .models import ExecutionMetrics


class MetricsCollector:
    def __init__(self, run_id: str, scenario_name: str):
        self.run_id = run_id
        self.scenario_name = scenario_name
        self.start_epoch = time.time()
        self.end_epoch: Optional[float] = None
        self.stage_starts: Dict[str, float] = {}
        self.stage_latencies: Dict[str, float] = {}
        self.retry_events: List[Dict[str, Any]] = []
        self.rollback_events: List[Dict[str, Any]] = []
        self.completed_nodes: set[str] = set()
        self.failed_nodes: set[str] = set()
        self.approvals_requested: int = 0
        self.approvals_granted: int = 0

    def start_stage(self, stage_name: str) -> None:
        self.stage_starts[stage_name] = time.time()

    def end_stage(self, stage_name: str) -> float:
        if stage_name in self.stage_starts:
            duration = round(time.time() - self.stage_starts[stage_name], 3)
            self.stage_latencies[stage_name] = duration
            return duration
        return 0.0

    def record_node_completed(self, node_id: str) -> None:
        self.completed_nodes.add(node_id)
        if node_id in self.failed_nodes:
            self.failed_nodes.remove(node_id)

    def record_node_failed(self, node_id: str) -> None:
        self.failed_nodes.add(node_id)

    def record_retry(self, task_id: str, attempt: int, duration_to_repair: float) -> None:
        self.retry_events.append({
            "task_id": task_id,
            "attempt": attempt,
            "repair_duration": duration_to_repair,
            "timestamp": datetime.utcnow().isoformat()
        })

    def record_rollback(self, snapshot_id: str, reason: str) -> None:
        self.rollback_events.append({
            "snapshot_id": snapshot_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })

    def record_approval_request(self) -> None:
        self.approvals_requested += 1

    def record_approval_decision(self, granted: bool) -> None:
        if granted:
            self.approvals_granted += 1

    def finalize(self) -> ExecutionMetrics:
        self.end_epoch = time.time()
        total_duration = round(self.end_epoch - self.start_epoch, 3)
        total_nodes = len(self.completed_nodes) + len(self.failed_nodes)

        # MTTR (Mean Time to Repair)
        mttr = 0.0
        if self.retry_events:
            total_repair_time = sum(e["repair_duration"] for e in self.retry_events)
            mttr = round(total_repair_time / len(self.retry_events), 3)

        # Success rate
        success_rate = (len(self.completed_nodes) / max(total_nodes, 1)) * 100.0

        return ExecutionMetrics(
            run_id=self.run_id,
            scenario_name=self.scenario_name,
            total_nodes=total_nodes,
            completed_nodes=len(self.completed_nodes),
            failed_nodes=len(self.failed_nodes),
            retry_count=len(self.retry_events),
            rollback_count=len(self.rollback_events),
            human_approvals_requested=self.approvals_requested,
            human_approvals_granted=self.approvals_granted,
            start_time=datetime.fromtimestamp(self.start_epoch).isoformat(),
            end_time=datetime.fromtimestamp(self.end_epoch).isoformat(),
            total_duration_seconds=total_duration,
            mttr_seconds=mttr,
            success_rate_percent=round(success_rate, 2),
            stage_latencies=self.stage_latencies
        )
