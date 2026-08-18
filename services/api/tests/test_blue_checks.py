from __future__ import annotations

from services.api import blue_checks


def test_verify_no_path_simple():
    adj = {
        'a': ['b'],
        'b': ['c'],
        'c': []
    }
    # there is a path a->c, so verify_no_path_z3 should return False
    assert blue_checks.verify_no_path_z3(adj, 'a', 'c') is False
    # no path c->a
    assert blue_checks.verify_no_path_z3(adj, 'c', 'a') is True
