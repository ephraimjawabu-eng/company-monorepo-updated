"""Load detection rules from common repositories (Elastic detection-rules format).

This module provides a small loader that reads a directory of JSON/YAML rule files and
normalizes them into a simple Python dict format for use by the Blue Team detection engine.
"""
from __future__ import annotations

import os
import json
from typing import List, Dict, Any

import yaml


def load_rules_from_dir(path: str) -> List[Dict[str, Any]]:
    """Walk directory and load JSON/YAML rule files, returning normalized list.

    Only loads files with .json, .yml, .yaml extensions.
    """
    rules: List[Dict[str, Any]] = []
    for root, _, files in os.walk(path):
        for fname in files:
            if fname.lower().endswith(('.json', '.yml', '.yaml')):
                full = os.path.join(root, fname)
                try:
                    with open(full, 'r', encoding='utf-8') as f:
                        if fname.lower().endswith('.json'):
                            obj = json.load(f)
                        else:
                            obj = yaml.safe_load(f)
                    # normalization heuristics: many rules have 'name' or 'title'
                    rule = {
                        'id': obj.get('id') if isinstance(obj, dict) else None,
                        'title': obj.get('title') or obj.get('name') or fname,
                        'raw': obj
                    }
                    rules.append(rule)
                except Exception:
                    # ignore parse errors; higher-level code should log
                    continue
    return rules
