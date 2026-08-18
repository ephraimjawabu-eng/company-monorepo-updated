"""Topology engine: models assets and trust boundaries as a graph and performs reachability analytics.
"""
from __future__ import annotations
from typing import Any, Dict, Iterable, List

try:
    import networkx as nx
except Exception:
    nx = None  # type: ignore


class GraphTopology:
    def __init__(self):
        if nx is None:
            raise RuntimeError("networkx is required for topology operations")
        self.graph = nx.DiGraph()

    def add_node(self, node_id: str, **meta: Any) -> None:
        """Add node with optional metadata (e.g. role='service', sensitivity='high')."""
        self.graph.add_node(node_id, **meta)

    def add_edge(self, src: str, dst: str, **meta: Any) -> None:
        """Add directed edge representing allowed communication or trust link."""
        self.graph.add_edge(src, dst, **meta)

    def reachable(self, source: str, target: str) -> bool:
        """Return True if target is reachable from source."""
        try:
            return nx.has_path(self.graph, source, target)
        except Exception:
            return False

    def shortest_path(self, source: str, target: str) -> List[str]:
        """Return a shortest path (list of node ids) or empty list if none."""
        try:
            return nx.shortest_path(self.graph, source, target)
        except Exception:
            return []

    def has_node(self, node_id: str) -> bool:
        """Return True if node exists in topology."""
        return node_id in self.graph.nodes()

    def sensitive_assets(self) -> List[str]:
        """Return nodes marked sensitive in metadata."""
        return [n for n, d in self.graph.nodes(data=True) if d.get('sensitivity') == 'high']

    def nodes(self) -> Iterable[str]:
        return self.graph.nodes()

    def edges(self) -> Iterable:
        return self.graph.edges(data=True)

    def centrality_ranking(self, k: int = 10) -> List[str]:
        """Return a list of nodes ranked by betweenness centrality (descending)."""
        try:
            c = nx.betweenness_centrality(self.graph)
            return sorted(c.keys(), key=lambda n: c[n], reverse=True)[:k]
        except Exception:
            return list(self.graph.nodes())[:k]
