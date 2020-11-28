from os import getenv
from common.utils import get_env_variable

from dotenv import load_dotenv
from pathlib import Path  # python3 only
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Dynamic (Environmental) configurations

# Crashes if not present in environment
SECRET_KEY = get_env_variable('SECRET_KEY')

# TODO: Change default database url
# DB_URL is postgres one if launched from Heroku or sqlite one for local testing
DB_URL = getenv("DATABASE_URL", 'sqlite:///data.db')
TEST_DB_URL = getenv("TEST_DATABASE_URL", 'sqlite:///data.db')

# Debug and testing only if explicitly stated in environment
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
    """Flask config class."""
    SQLALCHEMY_DATABASE_URI = TEST_DB_URL

    # silence the deprecation warning
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PROPAGATE_EXCEPTIONS = True

    DEBUG = True
    TESTING = True
    ENV = 'testing'
