from app import create_app
import pytest


@pytest.fixture
def app():
    _app = create_app('config.TestConfig')
    from db import db
    db.init_app(_app)
    return _app


@pytest.fixture
def client(app):
    _client = app.test_client()
    return _client


@pytest.fixture
def user_seeds():
    """Gets the list of users that will be used to prepopulate the database before each test

    Returns:
        list of (dict of (str, str)): list of users
    """
    return [
        {'username': 'admin1', 'password': 'password', 'role': 'admin'},
        {'username': 'admin2', 'password': 'password', 'role': 'admin'},
        {'username': 'maintainer1', 'password': 'password', 'role': 'maintainer'},
        {'username': 'maintainer2', 'password': 'password', 'role': 'maintainer'},
        {'username': 'planner1', 'password': 'password', 'role': 'planner'},
        {'username': 'planner2', 'password': 'password', 'role': 'planner'},
    ]


@pytest.fixture
def unexisting_user():
    """Gets an user that is not included in user_seeds

    Returns:
        dict of (str, str): the unexisting_user
    """
    return {'username': 'username', 'password': 'password', 'role': 'admin'}


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
