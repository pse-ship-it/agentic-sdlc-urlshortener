"""
Base SDLC Agent Abstract Class.
Enforces structured execution contracts, input/output validation, and lineage emission.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from orchestrator.models import TaskNode
from orchestrator.llm_provider import UnifiedLLMProvider


class BaseSDLCAgent(ABC):
    def __init__(self, role_name: str, llm_provider: Optional[UnifiedLLMProvider] = None):
        self.role_name = role_name
        self.llm = llm_provider or UnifiedLLMProvider()

    @abstractmethod
    def execute(self, task: TaskNode, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent's SDLC task.
        Must return a structured dictionary containing:
        - decision_summary: str
        - rationale: str
        - alternatives_rejected: list[str]
        - payload: dict with stage-specific outputs
        """
        pass
