def smoke():
    try:
        from services.api.topology import GraphTopology
        from services.api.autopoietic_loop import AutopoieticLoop
        t = GraphTopology()
        t.add_node('public')
        t.add_node('svc1', sensitivity='low')
        t.add_node('db', sensitivity='high')
        t.add_edge('public', 'svc1')
        t.add_edge('svc1', 'db')
        loop = AutopoieticLoop(t)
        res = loop.run_once()
        print('agents smoke:', res)
        return True
    except Exception as e:
        print('agents smoke failed:', e)
        return False

if __name__ == '__main__':
    smoke()
