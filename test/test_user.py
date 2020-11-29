def test_get_user_success(client, user_seeds, reset_db):
    test_user = user_seeds[0]
    res = client.get(f"/user/{test_user['username']}")
    assert res.status_code == 200
    assert res.get_json()['username'] == test_user['username']
    assert res.get_json()['role'] == test_user['role']
    assert 'password' not in res.get_json().keys()


def test_get_user_not_found(client, unexisting_user, reset_db):
    test_user = unexisting_user
    res = client.get(f"/user/{test_user['username']}")
    assert res.status_code == 404
    assert 'message' in res.get_json().keys()


    assert res.status_code == 200
    data = res.get_json()
    assert len(data['rows']) == 3


def test_post_user_success(client, seed):
    res = client.post(
        '/user', data=test_user)
    assert res.status_code == 201
    assert isinstance(res.get_json(), dict)
    assert res.get_json()['username'] == test_user['username']
    assert res.get_json()['role'] == test_user['role']
    assert 'password' not in res.get_json().keys()


def test_get_users_after_post(client, seed):
    res = client.get('/users')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data['rows']) == 3
