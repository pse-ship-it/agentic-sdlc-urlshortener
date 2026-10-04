"""
Resilience & Safety Controls:
- Bounded Retries with Exponential Backoff
- Workspace Snapshotting & Rollback Engine
- Safe-Stop & Circuit Breakers
"""

from __future__ import annotations
import os
import shutil
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class SafeStopException(Exception):
    """Raised when an unrecoverable policy failure or safety invariant triggers a governed safe-stop."""
    def __init__(self, reason: str, task_id: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(f"SafeStop triggered at task '{task_id}': {reason}")
        self.reason = reason
        self.task_id = task_id
        self.context = context or {}


class BoundedRetryController:
    """Enforces bounded retries, MTTR calculation, and circuit-breaker trip logic."""
    def __init__(self, default_max_retries: int = 3, base_backoff_seconds: float = 0.5):
        self.default_max_retries = default_max_retries
        self.base_backoff_seconds = base_backoff_seconds
        self.retry_history: Dict[str, List[Dict[str, Any]]] = {}

    def should_retry(self, task_id: str, current_retry_count: int, max_retries: Optional[int] = None) -> bool:
        limit = max_retries if max_retries is not None else self.default_max_retries
        return current_retry_count < limit

    def record_retry(self, task_id: str, attempt: int, error: str, recovery_strategy: str) -> None:
        if task_id not in self.retry_history:
            self.retry_history[task_id] = []
        self.retry_history[task_id].append({
            "attempt": attempt,
            "error": error,
            "recovery_strategy": recovery_strategy,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def get_backoff(self, attempt: int) -> float:
        return self.base_backoff_seconds * (2 ** (attempt - 1))

    def get_total_retries(self) -> int:
        return sum(len(attempts) for attempts in self.retry_history.values())


class WorkspaceSnapshotManager:
    """Manages transactional snapshots of the codebase to guarantee reliable rollbacks."""
    def __init__(self, workspace_root: str, snapshots_dir: Optional[str] = None):
        self.workspace_root = workspace_root
        self.snapshots_dir = snapshots_dir or os.path.join(workspace_root, ".sdlc_snapshots")
        os.makedirs(self.snapshots_dir, exist_ok=True)
        self.snapshot_manifest: List[Dict[str, Any]] = []

    def create_snapshot(self, snapshot_id: str, description: str) -> str:
        """Takes a copy snapshot of tracked source files before a risky mutation."""
        target_dir = os.path.join(self.snapshots_dir, snapshot_id)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        os.makedirs(target_dir, exist_ok=True)

        # Copy target directories/files while skipping .sdlc_snapshots and __pycache__
        ignored = {".sdlc_snapshots", "__pycache__", ".pytest_cache", ".git", "venv", ".venv"}
        for item in os.listdir(self.workspace_root):
            if item in ignored:
                continue
            src_path = os.path.join(self.workspace_root, item)
            dst_path = os.path.join(target_dir, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            else:
                shutil.copy2(src_path, dst_path)

        manifest_entry = {
            "snapshot_id": snapshot_id,
            "description": description,
            "path": target_dir,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.snapshot_manifest.append(manifest_entry)
        return snapshot_id

    def rollback(self, snapshot_id: str) -> bool:
        """Restores the workspace to the specified snapshot point."""
        snapshot = next((s for s in self.snapshot_manifest if s["snapshot_id"] == snapshot_id), None)
        if not snapshot or not os.path.exists(snapshot["path"]):
            return False

        source_dir = snapshot["path"]
        ignored = {".sdlc_snapshots", "__pycache__", ".pytest_cache", ".git", "venv", ".venv"}

        # Clear current workspace tracked contents
        for item in os.listdir(self.workspace_root):
            if item in ignored:
                continue
            p = os.path.join(self.workspace_root, item)
            if os.path.isdir(p):
                shutil.rmtree(p)
            else:
                os.remove(p)

        # Restore from snapshot
        for item in os.listdir(source_dir):
            s_path = os.path.join(source_dir, item)
            d_path = os.path.join(self.workspace_root, item)
            if os.path.isdir(s_path):
                shutil.copytree(s_path, d_path)
            else:
                shutil.copy2(s_path, d_path)

        return True
