"""Scan selected directories (services, apps) with secret_scanner to reduce noise.
"""
from __future__ import annotations

import os
import sys
from services.api.integrations import secret_scanner

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PATHS = ['services', 'apps']
EXT_SKIP = {'.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz', '.pyc', '.exe', '.dll'}

matches = []
for p in PATHS:
    base = os.path.join(ROOT, p)
    if not os.path.exists(base):
        continue
    for dirpath, dirnames, filenames in os.walk(base):
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

print(f"Scanned paths: {PATHS}")
print(f"Found {len(matches)} candidate secret(s) in selected paths. Showing up to 200:")
for m in matches[:200]:
    print(f"- {m['file']} :: {m['type']} -> {m['snippet'][:200]!r}")

if not matches:
    print('No candidates in selected paths.')
else:
    print('Review candidates and add white-listing for known reference files.')
