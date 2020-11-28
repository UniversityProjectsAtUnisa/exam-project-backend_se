test_user = {'username': 'marco741', 'password': 'password', 'role': 'admin'}


def test_get_users(client, seed):
    res = client.get('/users')
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
