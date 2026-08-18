"""Scan repository files with the project's secret_scanner and report candidates.
"""
from __future__ import annotations

import os
import sys
from services.api.integrations import secret_scanner

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
IGNORED = {'.git', '.venv', 'venv', 'dist', '__pycache__'}
# Allow scanner whitelist file at repo root to reduce noise
EXT_SKIP = {'.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz', '.pyc', '.exe', '.dll'}

# load optional whitelist to skip directories (simple basename matches)
_IMPORT_WHITELIST = []
try:
    import json
    wl_path = os.path.join(ROOT, 'scanner_whitelist.json')
    if os.path.exists(wl_path):
        with open(wl_path, 'r', encoding='utf-8') as wf:
            data = json.load(wf)
            _IMPORT_WHITELIST = data.get('paths', []) or []
            # normalize to set of basenames for simple checks
            _IMPORT_WHITELIST = [p.strip() for p in _IMPORT_WHITELIST if p.strip()]
except Exception:
    _IMPORT_WHITELIST = []
# if node_modules is not explicitly whitelisted, keep excluding it
if 'node_modules' not in _IMPORT_WHITELIST:
    IGNORED.add('node_modules')

matches = []

for dirpath, dirnames, filenames in os.walk(ROOT):
    # skip ignored dirs or whitelisted skip-paths
    parts = set(dirpath.split(os.sep))
    if parts & IGNORED:
        continue
    if any(w in parts for w in _IMPORT_WHITELIST):
        # skip paths explicitly configured in scanner_whitelist.json
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
