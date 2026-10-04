"""
Tests for Non-Linear DAG Workflow Orchestrator, Gates, Retries, and Rollback.
"""

import os
import shutil
import tempfile
import pytest

from orchestrator.models import (
    SDLCState,
    DAG,
    TaskNode,
    LifecycleStage,
    AutonomyLevel,
    TaskStatus,
    GateStatus
)
from orchestrator.dag_engine import DAGEngine
from orchestrator.gates import EntryExitGateKeeper
from orchestrator.safety import WorkspaceSnapshotManager, BoundedRetryController


def test_dag_dependency_resolution():
    dag = DAG()
    t1 = TaskNode(id="n1", name="Task 1", stage=LifecycleStage.REQUIREMENT_ANALYSIS, agent_role="Agent")
    t2 = TaskNode(id="n2", name="Task 2", stage=LifecycleStage.ARCHITECTURE_DESIGN, agent_role="Agent", dependencies=["n1"])

    dag.add_node(t1)
    dag.add_node(t2)

    # t1 has no dependencies, ready to run
    assert dag.is_ready_to_run("n1") is True
    # t2 depends on n1, which is PENDING, so not ready
    assert dag.is_ready_to_run("n2") is False

    t1.status = TaskStatus.COMPLETED
    # Now t2 should be ready
    assert dag.is_ready_to_run("n2") is True


def test_bounded_retry_controller():
    controller = BoundedRetryController(default_max_retries=3, base_backoff_seconds=0.1)

    assert controller.should_retry("task_a", 0) is True
    assert controller.should_retry("task_a", 2) is True
    assert controller.should_retry("task_a", 3) is False  # Reached limit

    controller.record_retry("task_a", 1, "Simulated Error", "Retry attempt 1")
    assert controller.get_total_retries() == 1
    assert controller.get_backoff(1) == 0.1
    assert controller.get_backoff(2) == 0.2


def test_workspace_snapshot_and_rollback():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create initial test file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Initial Version 1.0")

        manager = WorkspaceSnapshotManager(temp_dir)
        snap_id = manager.create_snapshot("snap1", "Snapshot before mutation")

        # Mutate the file
        with open(test_file, "w") as f:
            f.write("Corrupted Mutation 2.0")

        # Create a new unwanted file
        unwanted = os.path.join(temp_dir, "bad.txt")
        with open(unwanted, "w") as f:
            f.write("bad")

        # Execute rollback
        success = manager.rollback(snap_id)
        assert success is True

        # Verify restoration
        with open(test_file, "r") as f:
            content = f.read()
        assert content == "Initial Version 1.0"
        assert not os.path.exists(unwanted)


def test_gatekeeper_ambiguity_threshold():
    gatekeeper = EntryExitGateKeeper()
    node = TaskNode(
        id="check_ambig",
        name="Gate Check",
        stage=LifecycleStage.ARCHITECTURE_DESIGN,
        agent_role="Architect"
    )

    # Context with high ambiguity must fail
    res_fail = gatekeeper.evaluate_entry_gates(
        node=TaskNode(id="c1", name="N", stage=LifecycleStage.ARCHITECTURE_DESIGN, agent_role="A", entry_gates=["ambiguity_threshold"]),
        context={"ambiguity_score": 0.85}
    )
    assert res_fail.status == GateStatus.FAILED

    # Context with low ambiguity must pass
    res_pass = gatekeeper.evaluate_entry_gates(
        node=TaskNode(id="c2", name="N", stage=LifecycleStage.ARCHITECTURE_DESIGN, agent_role="A", entry_gates=["ambiguity_threshold"]),
        context={"ambiguity_score": 0.10}
    )
    assert res_pass.status == GateStatus.PASSED
