"""API routes for the web application."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import uuid
import json

from ..config import settings
from ..services.runner import TestRunner, RunStatus


router = APIRouter()

test_runner = TestRunner()


class RunTestRequest(BaseModel):
    """Request model for running tests."""
    target_url: str
    timeout: int = 30
    delay: float = 0
    form_field: str = "file"
    generate_html: bool = True
    generate_json: bool = True


class RunTestResponse(BaseModel):
    """Response model for test run."""
    run_id: str
    status: str
    message: str


class RunSummary(BaseModel):
    """Summary of a test run."""
    run_id: str
    target_url: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    total_tests: int = 0
    accepted: int = 0
    rejected: int = 0
    anomalies: int = 0
    gaps: int = 0


@router.post("/run", response_model=RunTestResponse)
async def run_test(request: RunTestRequest, background_tasks: BackgroundTasks):
    """Trigger a new upload test run."""
    run_id = str(uuid.uuid4())[:8]
    
    background_tasks.add_task(
        test_runner.run_tests,
        run_id=run_id,
        target_url=request.target_url,
        timeout=request.timeout,
        delay=request.delay,
        form_field=request.form_field,
        generate_html=request.generate_html,
        generate_json=request.generate_json,
    )
    
    return RunTestResponse(
        run_id=run_id,
        status="pending",
        message=f"Test run {run_id} started"
    )


@router.get("/runs", response_model=List[RunSummary])
async def get_runs():
    """Get all test runs."""
    runs = test_runner.get_all_runs()
    return [
        RunSummary(
            run_id=run_id,
            target_url=data.get("target_url", ""),
            status=data.get("status", "unknown"),
            created_at=data.get("created_at", ""),
            completed_at=data.get("completed_at"),
            total_tests=data.get("total_tests", 0),
            accepted=data.get("accepted", 0),
            rejected=data.get("rejected", 0),
            anomalies=data.get("anomalies", 0),
            gaps=data.get("gaps", 0),
        )
        for run_id, data in runs.items()
    ]


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get a specific test run."""
    run = test_runner.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/runs/{run_id}/report")
async def get_run_report(run_id: str, format: str = "json"):
    """Get report for a specific run."""
    run = test_runner.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Run not completed")
    
    report_path = run.get(f"{format}_report")
    if not report_path or not Path(report_path).exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    if format == "json":
        with open(report_path, "r") as f:
            return json.load(f)
    
    with open(report_path, "r") as f:
        return f.read()


@router.delete("/runs/{run_id}")
async def delete_run(run_id: str):
    """Delete a test run."""
    success = test_runner.delete_run(run_id)
    if not success:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"message": "Run deleted"}


@router.get("/stats")
async def get_stats():
    """Get overall statistics."""
    runs = test_runner.get_all_runs()
    
    total_runs = len(runs)
    completed_runs = sum(1 for r in runs.values() if r.get("status") == "completed")
    total_tests = sum(r.get("total_tests", 0) for r in runs.values())
    total_anomalies = sum(r.get("anomalies", 0) for r in runs.values())
    
    return {
        "total_runs": total_runs,
        "completed_runs": completed_runs,
        "total_tests": total_tests,
        "total_anomalies": total_anomalies,
    }
