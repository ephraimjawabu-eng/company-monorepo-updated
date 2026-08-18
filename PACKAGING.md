Packaging & Desktop Distribution

Goal: allow end users to download a self-contained application that runs the company engine locally (backend + UI) on Windows/macOS/Linux.

Quick start (user-friendly):
- Windows (powershell):
  1. Install Python 3.10+. Install Node.js (for Electron) if you want native UI.
  2. Clone the repo and open PowerShell in repo root.
  3. Run: .\scripts\start_local.ps1 -StartElectron

- macOS/Linux (bash):
  1. Install Python 3.10+ and Node.js (optional for Electron).
  2. Clone the repo and run: ./scripts/start_local.sh --electron

What these scripts do:
- Start a local backend (FastAPI uvicorn) bound to 127.0.0.1:8000 (localhost-only).
- Optionally start the Electron native UI which loads the packaged web UI and talks to the backend via localhost.
- The web UI can be opened directly in Chrome by loading apps/web/index.html and will interact with the backend at http://127.0.0.1:8000.

Security & packaging notes:
- By default all services bind to localhost only and require no public exposure to run locally.
- Electron scaffold enforces contextIsolation, disables nodeIntegration and sets a CSP header for loaded pages.
- For production-grade installers, use electron-builder/electron-forge in apps/native and run a CI job to sign installers.
- For secure local secrets, integrate OS keychains (Windows Credential Manager / macOS Keychain / libsecret) via services/api/kms.py.

Developer packaging steps (scaffolded):
1. Build the web UI (if using Next.js): cd apps/dashboard-next; npm install; npm run build; npm run export to create a static export.
2. Copy static export into apps/native/www (or update Electron load path to the exported folder).
3. Configure electron-builder in apps/native/package.json and run npx electron-builder --win --mac --linux.

Limitations & next steps:
- This repository provides scaffolding and secure defaults. Building signed installers, creating platform-specific services, and prepackaging Python runtimes require CI secrets and OS-specific signing — these are next steps.
- Can add automatic self-signed cert generation and TLS pinning for local HTTPS if desired.
