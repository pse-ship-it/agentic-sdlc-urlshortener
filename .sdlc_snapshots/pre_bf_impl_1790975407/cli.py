"""
Interactive CLI for Agentic SDLC Orchestrator.
Allows running scenarios, observing DAG transitions, reviewing gate checks, and authorizing Tier 3 actions.
"""

from __future__ import annotations
import argparse
import sys
import os

from scenarios.scenario_1_greenfield import run_greenfield_scenario
from scenarios.scenario_2_brownfield import run_brownfield_scenario
from scenarios.scenario_3_ambiguous import run_ambiguous_scenario


def main():
    parser = argparse.ArgumentParser(description="Apex-SDLC Agentic Workflow Orchestrator CLI")
    parser.add_argument(
        "--scenario",
        choices=["greenfield", "brownfield", "ambiguous", "all"],
        default="all",
        help="SDLC scenario to execute"
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        default=True,
        help="Automatically grant Tier 3 human approval checkpoints"
    )
    args = parser.parse_args()

    print("\n" + "="*80)
    print("        APEX-SDLC: AGENTIC SOFTWARE ENGINEERING SYSTEM (SCHWAB URL SHORTENER)        ")
    print("="*80)

    if args.scenario in ("greenfield", "all"):
        run_greenfield_scenario(auto_approve_human_gate=args.auto_approve)

    if args.scenario in ("brownfield", "all"):
        run_brownfield_scenario(auto_approve_human_gate=args.auto_approve)

    if args.scenario in ("ambiguous", "all"):
        run_ambiguous_scenario(interactive=False, auto_approve_human_gate=args.auto_approve)

    print("\n[SUCCESS] All requested scenarios executed under governed autonomous orchestration.")
    print("To launch the visual interactive dashboard, run: python -m ui.dashboard\n")


if __name__ == "__main__":
    main()
