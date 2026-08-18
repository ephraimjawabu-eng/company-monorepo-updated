from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app)


def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    js = r.json()
    # allow additional diagnostics in health response; ensure at least status ok
    assert isinstance(js, dict)
    assert js.get('status') == 'ok'


def test_plan_project():
    r = client.post('/plan', json={
        "name": "Secure SAAS",
        "domain": "fintech",
        "goals": "build a web platform",
        "constraints": "must be secure",
        "stack": "fullstack"
    })
    assert r.status_code == 200
    data = r.json()
    assert data['project'] == 'Secure SAAS'
    assert 'departments' in data
    assert len(data['departments']) >= 4


def test_create_product():
    r = client.post('/product', json={"id": 1, "name": "X"})
    assert r.status_code == 200
    d = r.json()
    assert d['created'] is True
    assert d['product']['name'] == 'X'
