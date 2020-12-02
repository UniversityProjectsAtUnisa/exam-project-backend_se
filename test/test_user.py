def test_get_user_success(client, user_seeds):
    """ Test for searching an existing user by his username """
    test_user = user_seeds[0]
    res = client.get(f"/user/{test_user['username']}")
    assert res.status_code == 200
    assert res.get_json()['username'] == test_user['username']
    assert res.get_json()['role'] == test_user['role']
    assert 'password' not in res.get_json().keys()


def test_get_user_not_found(client, unexisting_user):
    """ Test for searching a non-existing user """
    test_user = unexisting_user
    res = client.get(f"/user/{test_user['username']}")
    assert res.status_code == 404
    assert 'message' in res.get_json().keys()


def test_get_users_success(client, user_seeds):
    """ Test for getting correctly the first page of users """
    test_current_page = 1
    test_page_size = len(user_seeds) - 1

    res = client.get(
        f"/users?current_page={test_current_page}&page_size={test_page_size}")

    assert res.status_code == 200
    assert len(res.get_json()['rows']) <= test_page_size
    assert res.get_json()['meta']['count'] == len(user_seeds)
    assert res.get_json()['meta']['current_page'] == test_current_page
    assert res.get_json()['meta']['page_size'] == test_page_size

    import math
    expected_page_count = math.ceil(len(user_seeds) / test_page_size)
    assert res.get_json()['meta']['page_count'] == expected_page_count


def test_get_users_page_not_found(client, user_seeds):
    """ Test for a non-existing page """
    test_page_size = 5
    import math
    test_page_count = math.ceil(len(user_seeds) / test_page_size)
    test_current_page = test_page_count + 1
    res = client.get(
        f"/users?current_page={test_current_page}&page_size={test_page_size}")

    assert res.status_code == 404
    assert "message" in res.get_json().keys()


def test_post_user_success(client, unexisting_user):
    """ Test for creating a new user with a non-existing username """
    test_user = unexisting_user
    res = client.post('/user', data=test_user)

    assert res.status_code == 201
    assert res.get_json()['username'] == test_user['username']
    assert res.get_json()['role'] == test_user['role']
    assert 'password' not in res.get_json().keys()


def test_post_user_already_exists(client, user_seeds):
    """ Test for creating a new user with an existing username """
    test_user = user_seeds[0]
    res = client.post('/user', data=test_user)

    assert res.status_code == 400
    assert 'message' in res.get_json().keys()


def test_post_user_missing_username(client):
    """ Test for creating a new user without username """
    test_user_without_username = {'password': 'password', 'role': 'admin'}
    res = client.post('/user', data=test_user_without_username)
    assert res.status_code == 400
    assert 'message' in res.get_json().keys()
    assert 'username' in res.get_json()['message'].keys()


def test_post_user_missing_password(client):
    """ Test for creating a new user without password """
    test_user_without_password = {'username': 'username', 'role': 'admin'}
    res = client.post('/user', data=test_user_without_password)
    assert res.status_code == 400
    assert 'message' in res.get_json().keys()
    assert 'password' in res.get_json()['message'].keys()


def test_post_user_missing_role(client):
    """ Test for creating a new user without role """
    test_user_without_role = {'username': 'username', 'password': 'password'}
    res = client.post('/user', data=test_user_without_role)
    assert res.status_code == 400
    assert 'message' in res.get_json().keys()
    assert 'role' in res.get_json()['message'].keys()


def test_put_user_success(client, unexisting_user, user_seeds):
    """ Test for modifying an user's username and role """
    test_user = unexisting_user
    test_user.pop('password')
    test_old_user = user_seeds[0]

    res = client.put(f"/user/{test_old_user['username']}", data=test_user)
    assert res.status_code == 200
    assert res.get_json()['username'] == test_user['username']
    assert res.get_json()['role'] == test_user['role']
    assert 'password' not in res.get_json().keys()


def test_put_user_username_success(client, unexisting_user, user_seeds):
    """ Test for modifying an user's username """
    test_user = {'username': unexisting_user['username']}
    test_old_user = user_seeds[0]

    res = client.put(f"/user/{test_old_user['username']}", data=test_user)
    assert res.status_code == 200
    assert res.get_json()['username'] == test_user['username']
    assert res.get_json()['role'] == test_old_user['role']
    assert 'password' not in res.get_json().keys()


def test_put_user_role_success(client, unexisting_user, user_seeds):
    """ Test for modifying an user's role """
    test_user = {'role': unexisting_user['role']}
    test_old_user = user_seeds[0]

    res = client.put(f"/user/{test_old_user['username']}", data=test_user)
    assert res.status_code == 200
    assert res.get_json()['username'] == test_old_user['username']
    assert res.get_json()['role'] == test_user['role']
    assert 'password' not in res.get_json().keys()


def test_put_user_not_found(client, unexisting_user):
    """ Test for modifying a non-existing user """
    test_user = unexisting_user
    res = client.put(f"/user/{test_user['username']}", data={})
    assert res.status_code == 404
    assert 'message' in res.get_json().keys()


def test_put_user_new_username_already_existing(client, user_seeds):
    """ Test for modifying an user with another username which is already used """
    test_user = user_seeds[0]
    user_with_username_already_existing = user_seeds[1]
    res = client.put(
        f"/user/{test_user['username']}", data=user_with_username_already_existing)
    assert res.status_code == 400
    assert 'message' in res.get_json().keys()


def test_delete_user_success(client, user_seeds):
    """ Test for deleting an existing user """
    test_user = user_seeds[0]
    res = client.delete(f"/user/{test_user['username']}")
    assert res.status_code == 200
    assert 'message' in res.get_json().keys()


def test_delete_user_not_found(client, unexisting_user):
    """ Test for deleting a non-existing user """
    test_user = unexisting_user
    res = client.delete(f"/user/{test_user['username']}")
    assert res.status_code == 404
    assert 'message' in res.get_json().keys()
