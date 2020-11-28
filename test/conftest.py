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
def seed(app):
    with app.app_context():
        from db import db
        db.drop_all()
        db.create_all()
        from models.user import UserModel
        for i in range(3):
            user = UserModel(str(i), "password", 'admin')
            user.save_to_db()
    return True
