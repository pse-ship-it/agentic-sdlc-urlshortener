"""
FastAPI Orchestration Dashboard Server.
Serves visual DAG graph, decision lineage viewer, metrics telemetry, and interactive URL shortener testing workbench.
"""

from __future__ import annotations
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Ensure project root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scenarios.scenario_1_greenfield import run_greenfield_scenario
from scenarios.scenario_2_brownfield import run_brownfield_scenario
from scenarios.scenario_3_ambiguous import run_ambiguous_scenario
from url_shortener.database import SessionLocal, init_db
from url_shortener.shortener import ShortenerService
from url_shortener.analytics import AnalyticsService
from url_shortener.routes import router as shortener_router

app = FastAPI(title="Agentic SDLC & PulseURL Visual Console")

# Mount Shortener API routes
app.include_router(shortener_router)

# Store latest run state in memory
latest_run_state: Dict[str, Any] = {}


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/", response_class=HTMLResponse)
def index():
    html_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Dashboard HTML not found.</h1>", status_code=404)


@app.post("/api/orchestrator/run/{scenario_name}")
def trigger_scenario(scenario_name: str):
    """Executes one of the 3 scenarios and returns state, DAG, lineage, and metrics."""
    global latest_run_state

    try:
        if scenario_name == "greenfield":
            state = run_greenfield_scenario(auto_approve_human_gate=True)
        elif scenario_name == "brownfield":
            state = run_brownfield_scenario(auto_approve_human_gate=True)
        elif scenario_name == "ambiguous":
            state = run_ambiguous_scenario(interactive=False, auto_approve_human_gate=True)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown scenario: {scenario_name}")

        result_payload = {
            "scenario": state.scenario_name,
            "raw_requirement": state.raw_requirement,
            "nodes": [node.model_dump() for node in state.dag.nodes.values()],
            "decisions": [d.model_dump() for d in state.decisions],
            "metrics": state.metrics.model_dump() if state.metrics else {},
            "gate_results": [g.model_dump() for g in state.gate_results]
        }
        latest_run_state = result_payload
        return JSONResponse(content=result_payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orchestrator/status")
def get_latest_status():
    return JSONResponse(content=latest_run_state)


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*80)
    print(">>> LAUNCHING AGENTIC SDLC & URL SHORTENER WEB CONSOLE <<<")
    print("Dashboard available at: http://127.0.0.1:8000")
    print("="*80 + "\n")
    uvicorn.run("ui.dashboard:app", host="127.0.0.1", port=8000, reload=False)
