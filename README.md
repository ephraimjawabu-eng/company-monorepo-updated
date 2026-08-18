Polyglot Company Monorepo

This repository is a security-first, multi-team operating system for building product companies and products at scale. It is designed so a client can describe a product and the system selects only the relevant departments, reducing confusion, semantic drift, and coordination overhead.

Included:
- `company/`: team registry and department selection logic that picks relevant departments from a project brief.
- `services/api`: FastAPI orchestrator with `/health`, `/departments`, `/plan`, and `/product` endpoints; includes a dedicated API Department and backend orchestration.
- `services/go`: lightweight Go service for additional backend capabilities.
- `apps/dashboard`: browser-based company control center for health checks, plan generation, and external endpoint monitoring.
- `apps/web`: generic web starter.
- `apps/native`: Electron native starter.
- `references/`: public GitHub references cloned for backend, fullstack, desktop app, and security patterns.
- `infra/`: Docker Compose for local orchestration.
- `.github/workflows/ci.yml`: CI that runs Python regression tests.
- `teams/`: department and manager definitions.
- `security/`: blue team, red team, encryption and secure dev guidance.
- `testing/`: regression and QA strategy.
- `deploy/`: environment and deployment guardrails.

Core operating principle:
- The system does not show irrelevant departments for a project. Departments are selected by project type, data sensitivity, compliance needs, ML needs, deployment requirements, and product complexity.
- Each department is structured with clear ownership boundaries and expected responsibilities.
- Security, testing, and operational reliability are built in from the beginning.

Run locally / Packaging:
- This repo can be run as a downloadable local application (backend + web/native UI). See PACKAGING.md for instructions to start the backend and optionally the Electron native UI.
- Quick start (Windows PowerShell): `scripts\start_local.ps1 -StartElectron`.
- Quick start (macOS/Linux): `./scripts/start_local.sh --electron`.

Validation:
1. Install Python 3.10+ and Go.
2. From repo root, run `scripts\run_tests.ps1`.
3. Start the API with `uvicorn services.api.main:app --reload`.
4. Open `apps\dashboard\index.html` or serve it locally to review the company dashboard.