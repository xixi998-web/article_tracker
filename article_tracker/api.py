from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

import yaml
from fastapi import BackgroundTasks, FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from article_tracker.config.config import Config

app = FastAPI(title="Article Tracker API", version="0.1.0")

_tasks: dict[str, dict] = {}
CONFIG_PATH = "config.yaml"


class TrackRequest(BaseModel):
    config_path: str = "config.yaml"
    source: str = "all"
    since_days: Optional[int] = None
    dry_run: bool = False


class TaskResponse(BaseModel):
    task_id: str
    status: str


def _run_track_task(task_id: str, req: TrackRequest):
    from article_tracker.cli import _run_track
    _tasks[task_id]["status"] = "running"
    try:
        cfg = Config.load(req.config_path)
        run_log = _run_track(cfg, req.source, req.since_days, req.dry_run)
        _tasks[task_id]["status"] = "completed"
        _tasks[task_id]["result"] = run_log.to_dict()
    except Exception as e:
        _tasks[task_id]["status"] = "failed"
        _tasks[task_id]["error"] = str(e)


# ---------- 配置 API ----------

@app.get("/api/v1/config")
def get_config():
    try:
        p = Path(CONFIG_PATH)
        if not p.exists():
            return JSONResponse({"error": "config.yaml not found"}, status_code=404)
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/v1/config")
def save_config(data: dict):
    try:
        cfg = Config.from_raw(data)
        p = Path(CONFIG_PATH)
        with open(p, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return {"status": "saved"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


# ---------- 追踪 API ----------

@app.post("/api/v1/track", response_model=TaskResponse)
def trigger_track(req: TrackRequest, background_tasks: BackgroundTasks):
    task_id = uuid.uuid4().hex[:12]
    _tasks[task_id] = {"status": "pending"}
    background_tasks.add_task(_run_track_task, task_id, req)
    return TaskResponse(task_id=task_id, status="running")


@app.get("/api/v1/track/{task_id}")
def get_track_status(task_id: str):
    return _tasks.get(task_id, {"status": "not_found"})


@app.post("/api/v1/weekly-report", response_model=TaskResponse)
def trigger_weekly_report(background_tasks: BackgroundTasks):
    task_id = uuid.uuid4().hex[:12]
    _tasks[task_id] = {"status": "pending"}
    return TaskResponse(task_id=task_id, status="running")


@app.get("/api/v1/articles")
def list_articles(tier: Optional[str] = None, source: Optional[str] = None, limit: int = Query(default=20, le=100)):
    return {"articles": [], "total": 0}


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


# ---------- 前端页面 ----------

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    from article_tracker.web import get_html
    return HTMLResponse(content=get_html())
