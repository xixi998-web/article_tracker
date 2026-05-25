from __future__ import annotations

import uuid
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, Query
from pydantic import BaseModel

from article_tracker.config.config import Config

app = FastAPI(title="Article Tracker API", version="0.1.0")

_tasks: dict[str, dict] = {}


class TrackRequest(BaseModel):
    config_path: str = "config.yaml"
    source: str = "all"
    since_days: Optional[int] = None
    dry_run: bool = False


class TaskResponse(BaseModel):
    task_id: str
    status: str


class ArticlesResponse(BaseModel):
    articles: list[dict]
    total: int


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
