from services.api.resilience import EnvironmentResilience


def test_resilience_audit_basic():
    r = EnvironmentResilience()
    findings = r.audit_environment(topology=None, recon={'config': {'DEBUG': 'True', 'DATABASE_URL': 'sqlite:///local.db'}})
    assert isinstance(findings, list)
    assert any(f.get('type') in ('config', 'runtime_hints', 'circuit_breaker') for f in findings)
