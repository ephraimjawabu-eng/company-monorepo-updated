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
    PATHS = ['services', 'apps']

    # reuse repository-level whitelist if present
    _IMPORT_WHITELIST = []
    try:
        import json, fnmatch
        wl_path = os.path.join(ROOT, 'scanner_whitelist.json')
        if os.path.exists(wl_path):
            with open(wl_path, 'r', encoding='utf-8') as wf:
                data = json.load(wf)
                _IMPORT_WHITELIST = [p.strip() for p in data.get('paths', []) or []]
    except Exception:
        _IMPORT_WHITELIST = []

    def _is_whitelisted(path_rel: str) -> bool:
        for pat in _IMPORT_WHITELIST:
            if fnmatch.fnmatch(path_rel, pat) or any(fnmatch.fnmatch(part, pat) for part in path_rel.split(os.sep)):
                return True
        return False

    for dirpath, dirnames, filenames in os.walk(base):
            rel = os.path.relpath(dirpath, ROOT)
            if _is_whitelisted(rel):
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

print(f"Scanned paths: {PATHS}")
print(f"Found {len(matches)} candidate secret(s) in selected paths. Showing up to 200:")
for m in matches[:200]:
    print(f"- {m['file']} :: {m['type']} -> {m['snippet'][:200]!r}")

if not matches:
    print('No candidates in selected paths.')
else:
    print('Review candidates and add white-listing for known reference files.')
