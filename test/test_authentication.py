import pytest


@pytest.fixture
def user_seeds():
    """Gets the list of users for every possible role

    Returns:
        list of (dict of (str, str)): list of users
    """
    return [
        {'username': 'admin', 'password': 'password', 'role': 'admin'},
        {'username': 'planner', 'password': 'password', 'role': 'planner'},
        {'username': 'maintainer', 'password': 'password', 'role': 'maintainer'},
    ]


@pytest.fixture
def unexisting_user():
    """Gets an user that is not included in user_seeds

    Returns:
        dict of (str, str): the unexisting user
    """
    return {'username': 'username', 'password': 'password'}


@pytest.fixture(autouse=True)
def setup(app, user_seeds):
    """Before each test it drops every table and recreates them.
    Then it creates an user for every dictionary present in user_seeds

    Returns:
        boolean: the return status
    """
    with app.app_context():
        from db import db
        db.drop_all()
        db.create_all()
        from models.user import UserModel
        for seed in user_seeds:
            user = UserModel(**seed)
            user.save_to_db()
    return True


@pytest.fixture
def admin_user(user_seeds):
    """ Finds the first admin user among the user seeds

    Returns:
        dict of (str, str): The admin user
    """
    return next(user for user in user_seeds if user["role"] == "admin")


@pytest.fixture
def admin_client(client, admin_user):
    """ Creates a test client with preset admin authorization headers taken from the login endpoint

    Returns:
        FlaskClient: The test client
    """
    res = client.post(
        "/login", data=admin_user)
    access_token = res.get_json()["access_token"]
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + access_token
    return client


def test_login_success(client, user_seeds):
    """ Tests a successful login """
    test_user = user_seeds[0]
    res = client.post(
        "/login", data=test_user)
    assert res.status_code == 200
    assert "access_token" in res.get_json()


def test_login_user_not_found(client, unexisting_user):
    """ Tests a failed login by using an unexisting username"""
    test_user = unexisting_user
    res = client.post(
        "/login", data=test_user)
    assert res.status_code == 404
    assert "message" in res.get_json()


def test_login_wrong_password(client, user_seeds):
    """ Tests a failed login by using an incorrect password """
    test_user = user_seeds[0]
    test_user["password"] = "wrongpassword"
    res = client.post(
        "/login", data=test_user)
    assert res.status_code == 400
    assert "message" in res.get_json()
    assert res.get_json()["message"] == "Incorrect password"


def test_logout_success(admin_client):
    """ Tests a successful logout """
    res = admin_client.post("/logout")
    assert res.status_code == 200
    assert "message" in res.get_json()


def test_logout_missing_authorization(client):
    """ Tests a failed logout by not using an access token """
    res = client.post("/logout")
    assert res.status_code == 401
    assert "message" in res.get_json()


def test_logout_already_logged_out(admin_client):
    """ Test a failed logout by using an access token that has already been dismissed """
    # Correctly logs out
    admin_client.post("/logout")
    # Fails to logout
    res = admin_client.post("/logout")
    assert res.status_code == 401
    assert "message" in res.get_json()


def test_change_password_success(admin_client, admin_user):
    """ Tests a successful password change """
    logged_user = admin_user
    data = {
        "old_password": logged_user["password"], "new_password": "new_password"}
    res = admin_client.post("/change_password", data=data)
    assert res.status_code == 200
    assert "message" in res.get_json()


def test_change_password_missing_authorization(client, admin_user):
    """ Tests a failed password change by not using an access token """
    logged_user = admin_user
    data = {
        "old_password": logged_user["password"], "new_password": "new_password"}
    res = client.post("/change_password", data=data)
    assert res.status_code == 401
    assert "message" in res.get_json()


def test_change_password_wrong_password(client):
    """ Tests a failed password change by using the wrong old password """
    data = {
        "old_password": "wrong_password", "new_password": "new_password"}
    res = client.post("/change_password", data=data)
    assert res.status_code == 401
    assert "message" in res.get_json()
