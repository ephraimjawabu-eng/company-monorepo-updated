from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from company.selection import build_company_plan
from services.api.gateway import router as gateway_router, attach_middleware as attach_gateway_middleware

# Prometheus metrics ASGI app
try:
    from prometheus_client import make_asgi_app, Counter, Histogram
except Exception:
    make_asgi_app = None
    Counter = None
    Histogram = None

# define gateway metrics if prometheus_client available
REQUESTS_TOTAL = Counter('requests_total', 'Total requests') if Counter is not None else None
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency') if Histogram is not None else None
RATE_LIMITED = Counter('rate_limited_total', 'Rate limited requests') if Counter is not None else None
AUTH_FAILURES = Counter('auth_failures_total', 'Auth failures') if Counter is not None else None

app = FastAPI(title="Company Orchestration API")

# register the gateway router (API key, rate limiting) under /gateway
app.include_router(gateway_router, prefix="/gateway")
# attach the middleware to the app so requests are validated and rate-limited
try:
    attach_gateway_middleware(app)
except Exception:
    # safe fallback for test environments where redis or other optional deps may be absent
    pass

# mount prometheus metrics if available
if make_asgi_app is not None:
    app.mount('/metrics', make_asgi_app())


class Product(BaseModel):
    id: int
    name: str
    description: str = ""


class ProjectBrief(BaseModel):
    name: str = Field(..., min_length=1)
    domain: str = "general product"
    goals: str = ""
    constraints: str = ""
    stack: str = "fullstack"


@app.get("/health")
def health() -> dict[str, Any]:
    """Health endpoint that reports optional subsystem statuses and degraded mode.

    Checks: Redis connectivity (if REDIS_URL set), Z3 availability for formal checks,
    and whether Prometheus client is available.
    """
    import os
    status = {"status": "ok", "degraded": False, "components": {}}
    # check Redis
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        try:
            import redis as _redis
            r = _redis.from_url(redis_url, socket_connect_timeout=1)
            r.ping()
            status['components']['redis'] = 'ok'
        except Exception as e:
            status['components']['redis'] = f'error: {str(e)}'
            status['degraded'] = True
    else:
        status['components']['redis'] = 'disabled'

    # check z3
    try:
        import z3  # type: ignore
        status['components']['z3'] = 'ok'
    except Exception:
        status['components']['z3'] = 'unavailable'
        # z3 absence is recoverable; mark degraded
        status['degraded'] = True

    # prometheus
    try:
        import prometheus_client as _pc
        status['components']['prometheus'] = 'ok'
    except Exception:
        status['components']['prometheus'] = 'unavailable'

    return status


@app.get("/departments")
def departments() -> dict[str, Any]:
    return {
        "departments": [
            "ceo",
            "cto",
            "product_management",
            "frontend_engineering",
            "backend_engineering",
            "api_department",
            "security_team",
            "devops",
            "qa",
        ]
    }


@app.get('/status')
def status() -> dict[str, Any]:
    """Return machine-readable project and department status overview."""
    import os
    projects = []
    root = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'projects')
    root = os.path.abspath(root)
    if not os.path.exists(root):
        return {"projects": []}
    for name in sorted(os.listdir(root)):
        pdir = os.path.join(root, name)
        if not os.path.isdir(pdir):
            continue
        # list contract files as produced by teams
        contracts = [f for f in os.listdir(pdir) if f.endswith('.contract.json')]
        projects.append({"name": name, "contracts": contracts})
    return {"projects": projects}


@app.get('/logs')
def logs(n: int = 50):
    from services.api.logger import recent
    return {"logs": recent(n)}


@app.post("/plan")
def plan_project(payload: ProjectBrief) -> dict[str, Any]:
    plan = build_company_plan({
        "name": payload.name,
        "domain": payload.domain,
        "goals": payload.goals,
        "constraints": payload.constraints,
        "stack": payload.stack,
    })
    return {
        "project": payload.name,
        "summary": plan["summary"],
        "departments": plan["departments"],
    }


@app.post("/product")
def create_product(p: Product):
    return {"created": True, "product": p.model_dump()}


# Orchestration endpoints using orchestrator helper
from services.api.orchestrator import enqueue_run, get_run_status, get_run_logs


class OrchestrateBody(BaseModel):
    brief: str
    domain: str = "general"
    name: str = "generated"


@app.post('/gateway/orchestrate')
def gateway_orchestrate(payload: OrchestrateBody):
    # build brief and choose relevant departments using selection
    plan = build_company_plan({
        'name': payload.name,
        'domain': payload.domain,
        'goals': payload.brief,
        'constraints': '',
        'stack': 'fullstack'
    })
    departments = [d['id'] if isinstance(d, dict) and 'id' in d else d for d in plan['departments']]
    run_id = enqueue_run({'name': payload.name, 'domain': payload.domain, 'goals': payload.brief}, departments=departments)
    return { 'run_id': run_id }


@app.get('/gateway/runs/{run_id}')
def gateway_run_status(run_id: str):
    s = get_run_status(run_id)
    if not s:
        return { 'error': 'not_found' }
    return s


@app.get('/gateway/runs/{run_id}/logs')
def gateway_run_logs(run_id: str, n: int = 200):
    return { 'logs': get_run_logs(run_id, n) }
