from services.api.blue_checks import verify_no_path


def test_verify_no_path_simple():
    adj = {
        'public': ['web'],
        'web': ['backend'],
        'backend': ['db'],
        'db': []
    }
    # verify that without modification, there IS a path, so verify_no_path should return False
    assert verify_no_path(adj, 'public', 'db') is False

    # modify graph to remove backend->db edge
    adj2 = {
        'public': ['web'],
        'web': ['backend'],
        'backend': [],
        'db': []
    }
    assert verify_no_path(adj2, 'public', 'db') is True
