"""Lightweight secret scanner inspired by gitleaks patterns.

This module provides simple regex-based heuristics to find probable secrets in files.
It's intentionally conservative and returns candidates for manual review. It does not
attempt to exfiltrate or store secrets beyond returning matches to the caller.
"""
from __future__ import annotations

import re
from typing import List, Dict

# a small set of heuristic regexes (don't copy gitleaks patterns verbatim)
_PATTERNS = {
    'aws_access_key_id': re.compile(r'AKIA[0-9A-Z]{16}'),
    'aws_secret_access_key_like': re.compile(r"(?i)aws(.{0,20})?(secret|secret_key).{0,40}[\"']?([A-Za-z0-9/+=]{40})[\"']?"),
    'generic_base64_key': re.compile(r'(?<![A-Za-z0-9/+=])[A-Za-z0-9+/]{40,}={0,2}(?![A-Za-z0-9/+=])'),
    'rsa_private_key_header': re.compile(r'-----BEGIN RSA PRIVATE KEY-----'),
    'pem_private_key_header': re.compile(r'-----BEGIN (?:OPENSSH|PRIVATE) KEY-----'),
    # additional conservative heuristics
    'github_pat': re.compile(r'gh[pousr]_[A-Za-z0-9_]{36}'),
    'gh_token_old': re.compile(r'gh[rt]_[A-Za-z0-9_]{36}'),
    'slack_token': re.compile(r'xox[bprsa]-[A-Za-z0-9-]{10,}'),
    'jwt_like': re.compile(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_.-]{10,}\.[A-Za-z0-9_.-]{10,}'),
    'generic_api_key_like': re.compile(r"(?i)(api[_-]?key|secret|token|passwd).{0,30}[\"']?([A-Za-z0-9_\-=/+]{16,64})[\"']?"),
}


def scan_text_for_secrets(text: str) -> List[Dict[str, str]]:
    """Return list of matches: {type, snippet}

    Caller should handle masking and secure display of candidate snippets.
    """
    matches = []
    for name, rx in _PATTERNS.items():
        for m in rx.finditer(text):
            snippet = text[max(0, m.start()-40):m.end()+40]
            matches.append({'type': name, 'snippet': snippet})
    return matches
