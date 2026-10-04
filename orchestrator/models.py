"""
Data models and schemas for the Agentic SDLC Orchestration Engine.
"""

from __future__ import annotations
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    ROLLED_BACK = "ROLLED_BACK"


class GateStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    WAITING_HUMAN = "WAITING_HUMAN"
    BYPASS = "BYPASS"


class AutonomyLevel(str, Enum):
    TIER_0_READ_ONLY = "TIER_0_READ_ONLY"       # Analysis, intent classification (fully autonomous)
    TIER_1_LOW_RISK = "TIER_1_LOW_RISK"         # Documentation, test generation (autonomous with auto-gates)
    TIER_2_CODE_CHANGE = "TIER_2_CODE_CHANGE"   # Feature implementation, bugfixes (automated with test/lint gating)
    TIER_3_HIGH_IMPACT = "TIER_3_HIGH_IMPACT"   # Schema migration, production release (requires Human-in-the-Loop)


class LifecycleStage(str, Enum):
    REQUIREMENT_ANALYSIS = "REQUIREMENT_ANALYSIS"
    ARCHITECTURE_DESIGN = "ARCHITECTURE_DESIGN"
    CODEBASE_REASONING = "CODEBASE_REASONING"
    IMPLEMENTATION = "IMPLEMENTATION"
    TESTING_VERIFICATION = "TESTING_VERIFICATION"
    SECURITY_COMPLIANCE = "SECURITY_COMPLIANCE"
    DOCUMENTATION = "DOCUMENTATION"
    RELEASE_READINESS = "RELEASE_READINESS"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class GateResult(BaseModel):
    gate_name: str
    stage: str
    status: GateStatus
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DecisionRecord(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    stage: str
    task_id: str
    decision: str
    rationale: str
    alternatives_rejected: List[str] = Field(default_factory=list)
    risk_assessment: str = ""
    inputs_hash: str = ""
    outputs_hash: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TaskNode(BaseModel):
    id: str
    name: str
    stage: LifecycleStage
    agent_role: str
    dependencies: List[str] = Field(default_factory=list)
    parallel_group: Optional[str] = None
    autonomy_level: AutonomyLevel = AutonomyLevel.TIER_1_LOW_RISK
    entry_gates: List[str] = Field(default_factory=list)
    exit_gates: List[str] = Field(default_factory=list)
    max_retries: int = 3
    retry_count: int = 0
    status: TaskStatus = TaskStatus.PENDING
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    output_payload: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: float = 0.0


class DAG(BaseModel):
    nodes: Dict[str, TaskNode] = Field(default_factory=dict)
    execution_order: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_node(self, node: TaskNode) -> None:
        self.nodes[node.id] = node

    def get_dependencies_for(self, node_id: str) -> List[TaskNode]:
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[dep_id] for dep_id in node.dependencies if dep_id in self.nodes]

    def is_ready_to_run(self, node_id: str) -> bool:
        node = self.nodes.get(node_id)
        if not node or node.status != TaskStatus.PENDING:
            return False
        for dep_id in node.dependencies:
            dep = self.nodes.get(dep_id)
            if not dep or dep.status != TaskStatus.COMPLETED:
                return False
        return True


class ExecutionMetrics(BaseModel):
    run_id: str
    scenario_name: str
    total_nodes: int = 0
    completed_nodes: int = 0
    failed_nodes: int = 0
    retry_count: int = 0
    rollback_count: int = 0
    human_approvals_requested: int = 0
    human_approvals_granted: int = 0
    start_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = None
    total_duration_seconds: float = 0.0
    mttr_seconds: float = 0.0
    success_rate_percent: float = 0.0
    stage_latencies: Dict[str, float] = Field(default_factory=dict)


class SDLCState(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    scenario_name: str
    raw_requirement: str
    normalized_requirement: Optional[Dict[str, Any]] = None
    dag: DAG = Field(default_factory=DAG)
    shared_context: Dict[str, Any] = Field(default_factory=dict)
    decisions: List[DecisionRecord] = Field(default_factory=list)
    gate_results: List[GateResult] = Field(default_factory=list)
    snapshots: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Optional[ExecutionMetrics] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
