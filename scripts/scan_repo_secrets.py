"""Scan repository files with the project's secret_scanner and report candidates.
"""
from __future__ import annotations

import os
import sys
from services.api.integrations import secret_scanner

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
IGNORED = {'.git', '.venv', 'venv', 'node_modules', 'dist', '__pycache__'}
EXT_SKIP = {'.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz', '.pyc', '.exe', '.dll'}

matches = []

for dirpath, dirnames, filenames in os.walk(ROOT):
    # skip ignored dirs
    parts = set(dirpath.split(os.sep))
    if parts & IGNORED:
        continue
    for fname in filenames:
        if any(fname.lower().endswith(ext) for ext in EXT_SKIP):
            continue
        full = os.path.join(dirpath, fname)
        try:
            with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                txt = f.read()
        except Exception:
            continue
        res = secret_scanner.scan_text_for_secrets(txt)
        for r in res:
            matches.append({'file': os.path.relpath(full, ROOT), 'type': r['type'], 'snippet': r['snippet']})

# print summary
print(f"Scanned repository root: {ROOT}")
print(f"Found {len(matches)} candidate secret(s). Showing up to 50:")
for m in matches[:50]:
    print(f"- {m['file']} :: {m['type']} -> {m['snippet'][:200]!r}")

if len(matches) == 0:
    print('No candidates found (good).')
else:
    print('Candidates are only heuristics — review and remove/rotate any real secrets.')
