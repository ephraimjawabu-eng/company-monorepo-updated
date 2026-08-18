"""Formal reachability checks using z3-solver.

This module provides an example verifier that proves (or disproves) the existence of a path
from src to dst by unrolling path lengths up to N (number of nodes). It is intentionally bounded
and deterministic for small topologies used in unit tests and CI.
"""
from __future__ import annotations

from typing import Dict, List
import logging

try:
    from z3 import Solver, Bool, Or, Not, And, unsat
except Exception:
    Solver = None  # type: ignore
    Bool = None  # type: ignore
    Or = None  # type: ignore
    Not = None  # type: ignore
    And = None  # type: ignore
    unsat = None  # type: ignore

log = logging.getLogger("blue_checks")


def verify_no_path_z3(adj: Dict[str, List[str]], src: str, dst: str) -> bool:
    """Return True if Z3 proves there is no path from src to dst (within unroll bound).

    adj: adjacency list mapping node -> list of neighbor node names
    src, dst: node names
    """
    if Solver is None:
        # z3 not available: fall back to conservative answer using adjacency simple reachability
        log.warning('z3 not available; falling back to networkx reachability (conservative)')
        try:
            import networkx as nx
            g = nx.DiGraph()
            for u, vs in adj.items():
                for v in vs:
                    g.add_edge(u, v)
            return not nx.has_path(g, src, dst)
        except Exception:
            # if networkx missing, return False (cannot prove)
            return False

    nodes = list(adj.keys())
    if src not in nodes or dst not in nodes:
        # if nodes missing, conservatively return False
        return False

    N = len(nodes)
    # create Bool variables for edge existence (fixed by adj)
    edges = {}
    for u in nodes:
        for v in nodes:
            edges[(u, v)] = Bool(f"e_{u}_{v}")
    s = Solver()
    # constrain edges according to adj (fixed true/false)
    for (u, v), var in edges.items():
        if v in adj.get(u, []):
            s.add(var)
        else:
            s.add(Not(var))

    # unrolled reachability: path_len_l[node]
    path_vars = []  # list of dicts per length
    for l in range(N + 1):
        d = {n: Bool(f"p_{l}_{n}") for n in nodes}
        path_vars.append(d)

    # base: length 0: only src is reachable
    for n in nodes:
        if n == src:
            s.add(path_vars[0][n])
        else:
            s.add(Not(path_vars[0][n]))

    # recurrence: p_{l+1}[v] = OR_over_u (p_l[u] AND e_{u,v})
    for l in range(N):
        for v in nodes:
            ors = []
            for u in nodes:
                # use z3 And for symbolic conjunction
                ors.append( And(path_vars[l][u], edges[(u, v)]) )
            s.add(path_vars[l+1][v] == Or(*ors))

    # assert that for all l in 0..N, p_l[dst] is False (no path up to length N)
    no_path_conditions = [ Not(path_vars[l][dst]) for l in range(N+1) ]
    # We want to check if there exists a model where any p_l[dst] is True.
    s.push()
    s.add( Or(*[ Not(c) for c in no_path_conditions ]) )
    res = s.check()
    s.pop()
    # If solver says unsat, then the negation is unsat -> no path in any model
    if unsat is None:
        # cannot evaluate, conservatively return False
        return False
    return res == unsat
