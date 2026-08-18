from services.api.topology import GraphTopology
from services.api.autopoietic_loop import AutopoieticLoop


def test_autopoietic_detects_public_to_db():
    topo = GraphTopology()
    topo.add_node('public', role='internet', sensitivity='low')
    topo.add_node('web', role='service', sensitivity='low')
    topo.add_node('db', role='database', sensitivity='high')
    topo.add_edge('public', 'web')
    topo.add_edge('web', 'db')

    loop = AutopoieticLoop(topo)
    out = loop.run_once()
    # expect at least one topology detection matching our curated rule
    assert any(d.get('type') == 'topology' and ('Public to DB' in d.get('desc') or 'Public to DB' in (d.get('rule') or '')) for d in out.get('detections', []))
