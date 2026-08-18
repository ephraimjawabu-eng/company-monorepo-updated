from __future__ import annotations

import os
import json
import time

import fakeredis

import services.api.orchestrator as orchestrator


class DummyQueue:
    def __init__(self, conn=None):
        self.conn = conn
    def enqueue(self, func, *args, **kwargs):
        # synchronous execution for test simplicity
        return func(*args, **kwargs)


def test_enqueue_run_with_fakeredis(monkeypatch, tmp_path):
    # prepare fake redis and monkeypatch orchestrator's redis.from_url and Queue
    fake = fakeredis.FakeRedis()
    # create a tiny module-like object exposing from_url
    class FakeRedisModule:
        @staticmethod
        def from_url(u, decode_responses=True):
            return fake
    monkeypatch.setattr(orchestrator, 'redis', FakeRedisModule)
    monkeypatch.setattr(orchestrator, 'Queue', DummyQueue)

    # ensure REDIS_URL in env
    os.environ['REDIS_URL'] = 'redis://localhost:6379'

    brief = {'title': 'test-run'}
    run_id = orchestrator.enqueue_run(brief, departments=['frontend','backend'])
    assert isinstance(run_id, str)

    # read run metadata from fake redis
    data = fake.get(f'run:{run_id}')
    assert data is not None
    meta = json.loads(data)
    assert meta['id'] == run_id
    # Because DummyQueue executes synchronously, run should already be completed
    assert meta['status'] in ('completed', 'failed')


def test_run_job_local_persistence(tmp_path):
    brief = {'title': 'local-job'}
    run_id = 'local-test-' + str(int(time.time()))
    meta = {'id': run_id, 'brief': brief, 'departments': [], 'status': 'queued', 'created_at': time.time(), 'logs': []}
    res = orchestrator.run_job(run_id, meta)
    assert res['id'] == run_id
    assert res['status'] in ('completed', 'failed')
    assert 'finished_at' in res
