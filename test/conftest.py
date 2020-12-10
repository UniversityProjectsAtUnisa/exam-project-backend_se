from flask.app import Flask
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
