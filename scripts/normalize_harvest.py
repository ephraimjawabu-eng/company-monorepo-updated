"""Normalize harvested exploit artifacts into simple rule JSON files.

Reads services/api/integrations/exploits/*__harvest.json and writes normalized
rule files into services/api/integrations/exploits/curated/ with provenance.
"""
from __future__ import annotations
import json
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / 'services' / 'api' / 'integrations' / 'exploits'
OUT_DIR = IN_DIR / 'curated'
OUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_SNIPPET = 800


def make_id(source: str, path: str, snippet: str) -> str:
    h = hashlib.sha1((source + '::' + path + '::' + snippet).encode('utf-8')).hexdigest()[:12]
    return f"exploit-{h}"


def normalize_file(src: Path):
    try:
        obj = json.loads(src.read_text(encoding='utf-8'))
    except Exception:
        return 0
    repo = obj.get('repo')
    entries = obj.get('entries', [])
    cnt = 0
    for e in entries:
        path = e.get('path')
        snippet = (e.get('snippet') or '')[:MAX_SNIPPET]
        if not snippet.strip():
            continue
        rid = make_id(repo, path, snippet)
        rule = {
            'id': rid,
            'title': f"harvest:{repo}:{path}",
            'type': 'exploit_pattern',
            'source': repo,
            'path': path,
            'snippet': snippet,
            'provenance': str(src.name)
        }
        out = OUT_DIR / (rid + '.json')
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(rule, f, indent=2)
        cnt += 1
    return cnt


def main():
    total = 0
    for p in IN_DIR.glob('*__harvest.json'):
        print('normalizing', p)
        c = normalize_file(p)
        print('wrote', c, 'rules from', p.name)
        total += c
    print('total rules written:', total)

if __name__ == '__main__':
    main()
