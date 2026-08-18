"""Simple AEAD linter heuristics to detect non-AEAD or unsafe cipher usage.

This is an advisory tool: it scans source code strings for suspicious patterns such as
AES.new(..., mode=AES.MODE_CBC) or use of raw OpenSSL calls without GCM/AEAD.
"""
from __future__ import annotations

import re
from typing import List, Dict

_PATTERNS = [
    (re.compile(r"AES\.new\([^\)]*MODE_CBC"), 'AES-CBC usage detected; prefer AES-GCM/AEAD'),
    (re.compile(r"AES\.new\([^\)]*MODE_ECB"), 'AES-ECB usage detected; insecure'),
    (re.compile(r"ChaCha20Poly1305"), 'ChaCha20-Poly1305 detected (AEAD) — good'),
    (re.compile(r"ChaCha20\([^\)]*\)"), 'ChaCha20 stream cipher usage detected; ensure AEAD or proper MAC'),
]


def lint_code_for_aead_issues(code: str) -> List[Dict[str, str]]:
    issues = []
    for rx, msg in _PATTERNS:
        for m in rx.finditer(code):
            snippet = code[max(0, m.start()-40):m.end()+40]
            issues.append({'msg': msg, 'snippet': snippet})
    return issues
