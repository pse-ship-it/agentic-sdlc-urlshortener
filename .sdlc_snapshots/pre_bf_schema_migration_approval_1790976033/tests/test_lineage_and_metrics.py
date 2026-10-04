"""
Tests for Decision Lineage Cryptographic Provenance and Reliability Telemetry Metrics.
"""

import time
import pytest
from orchestrator.lineage import LineageTracker
from orchestrator.metrics import MetricsCollector


def test_lineage_tracker_tamper_evident_provenance():
    tracker = LineageTracker(run_id="run-test-01")

    # Record two sequential decisions
    d1 = tracker.record_decision(
        stage="REQUIREMENT_ANALYSIS",
        task_id="t1",
        decision="Normalized requirements with Base62",
        rationale="Base62 provides URL-safe encoding",
        alternatives_rejected=["UUIDv4"],
        input_data={"req": "shorten url"},
        output_data={"encoding": "base62"}
    )

    d2 = tracker.record_decision(
        stage="SECURITY_AUDIT",
        task_id="t2",
        decision="Enforced SSRF blocklist",
        rationale="Prevents internal subnet scanning",
        input_data={"ssrf_protection": True},
        output_data={"status": "enforced"}
    )

    assert d1.inputs_hash != ""
    assert d1.outputs_hash != ""
    assert len(tracker.records) == 2

    # Export and verify Merkle-like chain hash
    audit = tracker.export_audit_trail()
    assert audit["total_decisions"] == 2
    assert audit["final_audit_hash"] != ""
    assert len(audit["audit_log"]) == 2
    assert "chain_verification_hash" in audit["audit_log"][1]


def test_metrics_collector_mttr_and_reliability():
    collector = MetricsCollector(run_id="run-metrics-01", scenario_name="Test_Scenario")

    collector.start_stage("IMPLEMENTATION")
    time.sleep(0.05)
    collector.end_stage("IMPLEMENTATION")

    collector.record_node_completed("n1")
    collector.record_node_completed("n2")

    # Simulate a retry with 1.2s repair duration
    collector.record_retry(task_id="n3", attempt=1, duration_to_repair=1.2)
    collector.record_node_completed("n3")

    metrics = collector.finalize()
    assert metrics.completed_nodes == 3
    assert metrics.failed_nodes == 0
    assert metrics.success_rate_percent == 100.0
    assert metrics.retry_count == 1
    assert metrics.mttr_seconds == 1.2
    assert "IMPLEMENTATION" in metrics.stage_latencies
    assert metrics.stage_latencies["IMPLEMENTATION"] >= 0.04
