from services.api.topology import GraphTopology
from services.api.autopoietic_loop import AutopoieticLoop


def test_autopoietic_one_iteration():
    t = GraphTopology()
    t.add_node('public')
    t.add_node('svc1', sensitivity='low')
    t.add_node('db', sensitivity='high')
    t.add_edge('public', 'svc1')
    t.add_edge('svc1', 'db')
    loop = AutopoieticLoop(t)
    r = loop.run_once()
    assert 'recon' in r and 'crypto' in r and 'patch' in r and 'verified' in r
