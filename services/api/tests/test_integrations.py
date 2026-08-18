from __future__ import annotations

from services.api.integrations import secret_scanner, detection_loader, topology_imports
import os
import json

def test_secret_scanner_detects_aws():
    text = 'foo AKIAABCDEFGHIJKLMNOP key'
    res = secret_scanner.scan_text_for_secrets(text)
    assert any(r['type'] == 'aws_access_key_id' for r in res)


def test_detection_loader_reads_tmpfile(tmp_path):
    d = tmp_path / 'rules'
    d.mkdir()
    sample = {'id': 'rule-1', 'title': 'Test rule', 'query': 'process where name == "bad"'}
    f = d / 'test_rule.json'
    f.write_text(json.dumps(sample))
    rules = detection_loader.load_rules_from_dir(str(d))
    assert len(rules) == 1
    assert rules[0]['id'] == 'rule-1'


def test_topology_import_adjlist():
    adj = {'a': ['b'], 'b': ['c'], 'c': []}
    g = topology_imports.import_from_adjlist(adj)
    # GraphTopology exposes nodes() and reachable()
    assert 'a' in list(g.nodes())
    assert g.reachable('a', 'b')
