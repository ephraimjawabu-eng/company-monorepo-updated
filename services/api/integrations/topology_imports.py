"""Helpers to import topology data from common formats into GraphTopology.

This provides small, safe parsers inspired by network mapping tools (e.g., PyRIT, Caldera).
Do not copy upstream code; these are original helper wrappers that normalize JSON/adj lists
into the project's GraphTopology model.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from services.api.topology import GraphTopology


def import_from_adjlist(adj: Dict[str, Any]) -> GraphTopology:
    """Import adjacency list where adj[node] -> list of neighbor nodes or dicts.

    Example:
      {"a": ["b"], "b": ["c"]}
    """
    g = GraphTopology()
    for node, nbrs in adj.items():
        g.add_node(node)
    for node, nbrs in adj.items():
        for v in nbrs:
            if isinstance(v, str):
                g.add_edge(node, v)
            elif isinstance(v, dict) and 'id' in v:
                g.add_edge(node, v['id'])
    return g


def import_from_json_str(s: str) -> GraphTopology:
    """Load JSON string and convert to topology by looking for common keys.

    Heuristics: if top-level has 'nodes' and 'edges' use those; otherwise expect adj list.
    """
    obj = json.loads(s)
    g = GraphTopology()
    if isinstance(obj, dict):
        if 'nodes' in obj and 'edges' in obj:
            for n in obj['nodes']:
                nid = n.get('id') if isinstance(n, dict) else str(n)
                g.add_node(nid)
            for e in obj['edges']:
                u = e.get('source') or e.get('u') or (e[0] if isinstance(e, list) else None)
                v = e.get('target') or e.get('v') or (e[1] if isinstance(e, list) else None)
                if u is not None and v is not None:
                    g.add_edge(u, v)
            return g
        # fall back to adj list
        return import_from_adjlist(obj)
    raise ValueError('Unsupported JSON topology format')
