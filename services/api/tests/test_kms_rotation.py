from services.api.kms import KMSRotationManager, build_key_hierarchy


def test_kms_rotation_changes_fingerprint_and_version():
    manager = KMSRotationManager(key_id='demo-root')
    root = b'root-key-1234567890'
    result = manager.rotate_kek(root, context=b'prod')
    assert result['key_id'] == 'demo-root'
    assert 'new_kek' in result
    assert result['previous_kek_fingerprint'] != result['new_kek_fingerprint']
    assert result['version']


def test_key_hierarchy_is_deterministic_by_context():
    root = b'root-key-9876543210'
    first = build_key_hierarchy(root, ['api', 'db', 'worker'])
    second = build_key_hierarchy(root, ['api', 'db', 'worker'])
    assert first == second
    assert first['api'] != first['db']
    assert first['db'] != first['worker']
