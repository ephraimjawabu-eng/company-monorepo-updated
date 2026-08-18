"""RQ worker runner for orchestrator jobs.

Usage:
  set REDIS_URL and run: python -m services.api.run_worker

This script connects to Redis and starts an RQ worker processing the "orchestrator" queue.
If REDIS_URL is not set, it logs and exits. Placing it under services/api lets the orchestrator module imports be straightforward.
"""
from __future__ import annotations

import os
import logging
from typing import Optional

import redis
from rq import Worker, Queue, Connection

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("run_worker")

DEFAULT_QUEUE = "orchestrator"


def get_redis_conn() -> Optional[redis.Redis]:
    url = os.environ.get("REDIS_URL")
    if not url:
        log.error("REDIS_URL not set — worker requires Redis to run")
        return None
    return redis.from_url(url)


def main() -> None:
    conn = get_redis_conn()
    if conn is None:
        return

    with Connection(conn):
        q = Queue(DEFAULT_QUEUE)
        worker = Worker([q], name="orchestrator-worker")
        log.info("Starting RQ worker listening on queue: %s", DEFAULT_QUEUE)
        worker.work()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("Worker crashed: %s", e)
        raise
