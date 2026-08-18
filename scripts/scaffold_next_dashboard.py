"""Scaffold a minimal Next.js dashboard app in apps/dashboard-next when executed.

This generator creates a lightweight Next app with TypeScript, a basic index page, and a small API route that proxies to the existing FastAPI backend's /gateway endpoints. It is intentionally minimal so developers can run `node`/`pnpm` locally to build.

Usage:
  python scripts/scaffold_next_dashboard.py --out apps/dashboard-next
"""
from __future__ import annotations

import os
import argparse

TEMPLATE_FILES = {
    "package.json": '''{
  "name": "dashboard-next",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.5.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "swr": "2.1.0"
  }
}
''',
    "next.config.js": 'module.exports = { reactStrictMode: true };\n',
    "pages/index.js": '''import useSWR from 'swr'

const fetcher = (url) => fetch(url).then(r => r.json())

export default function Home() {
  const { data, error } = useSWR('/api/health', fetcher, { refreshInterval: 5000 })
  return (
    <main style={{ padding: 24, fontFamily: 'Segoe UI, Roboto, system-ui' }}>
      <h1>Company Dashboard (Next.js)</h1>
      <section>
        <h2>API Health</h2>
        <pre>{error ? String(error) : JSON.stringify(data, null, 2)}</pre>
      </section>
    </main>
  )
}
''',
    "pages/api/health.js": '''export default async function handler(req, res) {
  const backend = process.env.BACKEND_URL || 'http://localhost:8000'
  try {
    const r = await fetch(`${backend}/health`)
    const json = await r.json()
    res.status(200).json(json)
  } catch (err) {
    res.status(502).json({ error: String(err) })
  }
}
''',
    "README.md": '# Minimal Next.js dashboard scaffold\nRun `pnpm install` then `pnpm dev` to start.'
}


def write_files(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for path, content in TEMPLATE_FILES.items():
        full = os.path.join(out_dir, path)
        d = os.path.dirname(full)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        with open(full, 'w', encoding='utf-8') as f:
            f.write(content)
    print('Scaffolded Next.js dashboard at', out_dir)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', default='apps/dashboard-next', help='Output directory')
    args = p.parse_args()
    write_files(args.out)
