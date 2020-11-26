from app import create_app
import pytest


@pytest.fixture
def app():
    _app = create_app()
    from db import db
    db.init_app(_app)
    return _app


@pytest.fixture
def client(app):
    _client = app.test_client()
    return _client


def test_app_runs(client):
    res = client.get('/users')
    assert res.status_code == 200
