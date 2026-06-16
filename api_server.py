"""
api_server.py
─────────────
FastAPI wrapper that lets n8n call your job agent via HTTP.
Deploy this on Railway so n8n Cloud can trigger your Python agent.

Run locally:   uvicorn api_server:app --host 0.0.0.0 --port 8000
Railway runs:  uvicorn api_server:app --host 0.0.0.0 --port $PORT
"""

from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import json
import os
from datetime import datetime
from pathlib import Path

app = FastAPI(title="Job Agent API", version="1.0")


class RunRequest(BaseModel):
    platform: str = "all"       # "all", "linkedin", "indeed"
    limit: int = 20              # max applications this run
    dry_run: bool = False        # True = test only, don't submit


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status": "running",
        "message": "Job Agent API is live ✓",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Run the job agent ──────────────────────────────────────────────────────────

@app.post("/run-agent")
def run_agent(req: RunRequest):
    """
    Triggered by n8n Schedule node every day.
    Runs job_agent.py with the given settings.
    """
    cmd = [
        "python", "job_agent.py",
        "--platform", req.platform,
        "--limit",    str(req.limit),
    ]
    if req.dry_run:
        cmd.append("--dry-run")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,           # 10 min max per run
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        # Count successful applications from log output
        applied_count = result.stdout.count("✓ Applied")
        failed_count  = result.stdout.count("✗ Failed")

        return {
            "status":        "success" if result.returncode == 0 else "error",
            "applied_count": applied_count,
            "failed_count":  failed_count,
            "dry_run":       req.dry_run,
            "platform":      req.platform,
            "log_tail":      result.stdout[-3000:],   # last 3000 chars of log
            "errors":        result.stderr[-500:] if result.stderr else "",
            "run_time":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except subprocess.TimeoutExpired:
        return {
            "status":  "timeout",
            "message": "Agent ran for 10 minutes — session ended automatically",
        }
    except Exception as e:
        return {
            "status":  "error",
            "message": str(e),
        }


# ── Application stats ──────────────────────────────────────────────────────────

@app.get("/status")
def get_status():
    """Returns total applications tracked so far."""
    csv_path = Path("applications.csv")
    if not csv_path.exists():
        return {
            "total_applications": 0,
            "message": "No applications yet — run the agent first"
        }
    with open(csv_path, "r") as f:
        lines = f.readlines()
    total = max(0, len(lines) - 1)   # subtract header row

    # Count by status
    applied  = sum(1 for l in lines[1:] if "Applied"  in l)
    failed   = sum(1 for l in lines[1:] if "Failed"   in l)
    dry_runs = sum(1 for l in lines[1:] if "DRY_RUN"  in l)

    return {
        "total_applications": total,
        "applied":            applied,
        "failed":             failed,
        "dry_runs":           dry_runs,
        "csv_exists":         True,
    }


# ── Test endpoint (no agent needed) ───────────────────────────────────────────

@app.get("/test")
def test():
    """Quick test to confirm the API is reachable from n8n."""
    return {
        "status":  "reachable",
        "message": "n8n can talk to your job agent ✓",
        "time":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
