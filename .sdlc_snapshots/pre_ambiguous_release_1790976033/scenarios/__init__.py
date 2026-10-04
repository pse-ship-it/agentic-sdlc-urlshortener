"""
Demonstrable SDLC Execution Scenarios.
1. Greenfield: System creation from raw requirements through parallel testing to release.
2. Brownfield: AST codebase reasoning, impact analysis, and zero-regression feature enhancement.
3. Ambiguous: Intent interpretation, ambiguity gating, interactive clarification, and dynamic re-planning.
"""

from .scenario_1_greenfield import run_greenfield_scenario
from .scenario_2_brownfield import run_brownfield_scenario
from .scenario_3_ambiguous import run_ambiguous_scenario

__all__ = [
    "run_greenfield_scenario",
    "run_brownfield_scenario",
    "run_ambiguous_scenario",
]
