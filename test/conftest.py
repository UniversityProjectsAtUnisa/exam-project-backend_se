from flask.app import Flask
from app import create_app
import pytest


@pytest.fixture
def app():
    """Creates the app

    Returns:
        Flask: The Flask app
    """
    _app = create_app('config.TestConfig')
    return _app


@pytest.fixture
def client(app):
    """Creates a test client that can be used to test the endpoints without the server being active

    Returns:
        FlaskClient: The test client
    """
    _client = app.test_client()
    return _client
