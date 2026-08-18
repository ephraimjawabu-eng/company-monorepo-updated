"""Demo runner: build a small topology, add a public->db path, and run one autopoietic iteration."""
from services.api.topology import GraphTopology
from services.api.autopoietic_loop import AutopoieticLoop

import json

def main():
    topo = GraphTopology()
    topo.add_node('public', role='internet', sensitivity='low')
    topo.add_node('web', role='service', sensitivity='low')
    topo.add_node('db', role='database', sensitivity='high')
    topo.add_edge('public', 'web')
    topo.add_edge('web', 'db')

    loop = AutopoieticLoop(topo)
    res = loop.run_once()
    print(json.dumps(res, indent=2))

if __name__ == '__main__':
    main()
