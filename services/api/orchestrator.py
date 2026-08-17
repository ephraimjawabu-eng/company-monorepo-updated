"""Orchestrator: enqueue and manage project runs.

- Uses Redis/RQ when REDIS_URL provided; falls back to local file queue in ./runs/.
- Provides enqueue_run(), get_run_status(), get_run_logs() helpers.
"""
from __future__ import annotations

import os
import uuid
import json
import time
from typing import Any, Dict, Optional

try:
    import redis
    from rq import Queue
except Exception:
    redis = None  # type: ignore
    Queue = None  # type: ignore

from services.api.autopoietic_loop import AutopoieticLoop
from services.api.topology import GraphTopology

RUNS_DIR = os.path.join(os.path.dirname(__file__), '..', 'runs')
os.makedirs(RUNS_DIR, exist_ok=True)


def _local_run_path(run_id: str) -> str:
    return os.path.join(RUNS_DIR, f"{run_id}.json")


def _persist_local_run(run_id: str, data: Dict[str, Any]):
    path = _local_run_path(run_id)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _load_local_run(run_id: str) -> Optional[Dict[str, Any]]:
    path = _local_run_path(run_id)
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def enqueue_run(brief: Dict[str, Any], departments: Optional[list[str]] = None) -> str:
    """Create a run and enqueue it for execution. Returns run_id."""
    run_id = str(uuid.uuid4())
    run_meta = {
        'id': run_id,
        'brief': brief,
        'departments': departments or [],
        'status': 'queued',
        'created_at': time.time(),
        'logs': []
    }

    # try Redis/RQ
    redis_url = os.getenv('REDIS_URL')
    if redis_url and redis is not None and Queue is not None:
        try:
            r = redis.from_url(redis_url, decode_responses=True)
            q = Queue('orchestrator', connection=r)
            # enqueue job: we use a minimal job that will run run_job
            q.enqueue(run_job, run_id, run_meta)
            # persist metadata in redis
            r.set(f'run:{run_id}', json.dumps(run_meta))
            return run_id
        except Exception:
            # fall back to local file
            pass

    # local fallback: persist and run synchronously in background thread
    _persist_local_run(run_id, run_meta)
    # run synchronously (blocking) to simulate worker
    try:
        result = run_job(run_id, run_meta)
        return run_id
    except Exception:
        return run_id


def run_job(run_id: str, run_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Worker-executed job: runs the autopoietic loop and writes logs/status."""
    # update status
    run_meta['status'] = 'running'
    run_meta['started_at'] = time.time()
    _persist_local_run(run_id, run_meta)

    # prepare topology and run only relevant departments (simulate)
    topo = GraphTopology()
    # naive topology creation based on brief and departments
    topo.add_node('public')
    topo.add_node('frontend', sensitivity='low')
    topo.add_node('backend', sensitivity='low')
    topo.add_node('db', sensitivity='high')
    topo.add_edge('public', 'frontend')
    topo.add_edge('frontend', 'backend')
    topo.add_edge('backend', 'db')

    loop = AutopoieticLoop(topo, logger=lambda m: run_meta['logs'].append({'ts': time.time(), 'msg': m}))

    try:
        results = loop.run(iterations=2, delay=0.2)
        run_meta['status'] = 'completed'
        run_meta['results'] = results
    except Exception as e:
        run_meta['status'] = 'failed'
        run_meta.setdefault('errors', []).append(str(e))
    run_meta['finished_at'] = time.time()
    _persist_local_run(run_id, run_meta)
    return run_meta


def get_run_status(run_id: str) -> Optional[Dict[str, Any]]:
    """Return run metadata from Redis or local storage."""
    redis_url = os.getenv('REDIS_URL')
    if redis_url and redis is not None:
        try:
            r = redis.from_url(redis_url, decode_responses=True)
            data = r.get(f'run:{run_id}')
            if data:
                return json.loads(data)
        except Exception:
            pass
    return _load_local_run(run_id)


def get_run_logs(run_id: str, n: int = 200) -> list:
    meta = get_run_status(run_id)
    if not meta:
        return []
    return meta.get('logs', [])[-n:]
