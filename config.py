from os import getenv
from dotenv import load_dotenv
from pathlib import Path
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
# Documenta tutte le flag

DB_URL = getenv("DATABASE_URL", 'sqlite:///data.db')
TEST_DB_URL = getenv("TEST_DATABASE_URL", 'sqlite:///data.db')
DEBUG = getenv("DEBUG") == "TRUE"
TESTING = getenv("TESTING") == "TRUE"
ENVIRONMENT = "development" if getenv(
    "DEVELOPMENT") == "TRUE" else "production"


class Config:
    """Flask config class."""
    SQLALCHEMY_DATABASE_URI = DB_URL

    # silence the deprecation warning
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PROPAGATE_EXCEPTIONS = True

    DEBUG = DEBUG
    TESTING = TESTING
    ENV = ENVIRONMENT


class TestConfig:
    """Flask test config class."""
    SQLALCHEMY_DATABASE_URI = TEST_DB_URL

    # silence the deprecation warning
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PROPAGATE_EXCEPTIONS = True

    DEBUG = True
    TESTING = True
    ENV = 'testing'
