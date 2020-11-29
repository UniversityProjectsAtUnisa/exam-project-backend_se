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
    return {'username': 'username', 'password': 'password', 'role': 'admin'}


@pytest.fixture
def reset_db(app, user_seeds):
    with app.app_context():
        from db import db
        db.drop_all()
        db.create_all()
        from models.user import UserModel
        for seed in user_seeds:
            user = UserModel(**seed)
            user.save_to_db()
    return True
