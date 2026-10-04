"""
Decision Lineage & Audit Trail Tracker.
Provides tamper-evident cryptographic provenance, rationales, and input-output mapping.
"""

from __future__ import annotations
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from .models import DecisionRecord


class LineageTracker:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.records: List[DecisionRecord] = []
        self._audit_log: List[Dict[str, Any]] = []

    @staticmethod
    def compute_sha256(data: Any) -> str:
        """Computes a deterministic SHA-256 hash for arbitrary data."""
        if isinstance(data, str):
            payload = data.encode("utf-8")
        elif isinstance(data, (dict, list)):
            payload = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        elif isinstance(data, bytes):
            payload = data
        else:
            payload = str(data).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def record_decision(
        self,
        stage: str,
        task_id: str,
        decision: str,
        rationale: str,
        alternatives_rejected: Optional[List[str]] = None,
        risk_assessment: str = "",
        input_data: Any = None,
        output_data: Any = None
    ) -> DecisionRecord:
        """Records an architectural, design, or implementation decision with cryptographic lineage."""
        inputs_hash = self.compute_sha256(input_data) if input_data is not None else ""
        outputs_hash = self.compute_sha256(output_data) if output_data is not None else ""

        record = DecisionRecord(
            stage=stage,
            task_id=task_id,
            decision=decision,
            rationale=rationale,
            alternatives_rejected=alternatives_rejected or [],
            risk_assessment=risk_assessment,
            inputs_hash=inputs_hash,
            outputs_hash=outputs_hash,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.records.append(record)

        audit_entry = {
            "run_id": self.run_id,
            "decision_id": record.decision_id,
            "stage": stage,
            "task_id": task_id,
            "decision": decision,
            "rationale": rationale,
            "inputs_hash": inputs_hash,
            "outputs_hash": outputs_hash,
            "timestamp": record.timestamp
        }
        self._audit_log.append(audit_entry)
        return record

    def get_lineage_for_stage(self, stage: str) -> List[DecisionRecord]:
        return [r for r in self.records if r.stage == stage]

    def export_audit_trail(self) -> Dict[str, Any]:
        """Exports the full audit trail with Merkle-like chain verification."""
        chain_hash = ""
        for entry in self._audit_log:
            combined = f"{chain_hash}:{entry['decision_id']}:{entry['inputs_hash']}:{entry['outputs_hash']}"
            chain_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
            entry["chain_verification_hash"] = chain_hash

        return {
            "run_id": self.run_id,
            "total_decisions": len(self.records),
            "final_audit_hash": chain_hash,
            "records": [r.model_dump() for r in self.records],
            "audit_log": self._audit_log
        }
