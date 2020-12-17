from os import getenv
from dotenv import load_dotenv
from pathlib import Path
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# This file loads .env file in local memory and
# handles the initialization of Config and TestConfig classes
# used by Flask

# The main database url
DB_URL = getenv("DATABASE_URL", 'sqlite:///data.db')
# The test database url
TEST_DB_URL = getenv("TEST_DATABASE_URL", 'sqlite:///data.db')
TESTING = getenv("TESTING") == "TRUE"
ENVIRONMENT = "development" if getenv(
    "DEVELOPMENT") == "TRUE" else "production"
JWT_SECRET_KEY = getenv("JWT_SECRET_KEY")
JWT_TOKEN_EXPIRES = int(getenv("JWT_TOKEN_EXPIRES", "3600"))

# Configurable maintainer constants
MAINTAINER_WORK_START_HOUR = int(getenv("MAINTAINER_WORK_START_HOUR", "8"))
MAINTAINER_WORK_HOURS = int(getenv("MAINTAINER_WORK_HOURS", "9"))


class Config:
    """Flask Config class."""
    SQLALCHEMY_DATABASE_URI = DB_URL

    # silence the deprecation warning
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # jwt configs
    JWT_BLACKLIST_ENABLED = True  # enable blacklist feature
    # allow blacklisting for access and refresh tokens
    JWT_BLACKLIST_TOKEN_CHECKS = ["access"]
    # secret key to check jwt validity
    JWT_SECRET_KEY = JWT_SECRET_KEY
    # token expire time in seconds
    JWT_ACCESS_TOKEN_EXPIRES = JWT_TOKEN_EXPIRES

    # Enable testing mode. Exceptions are propagated rather than handled by the the app’s error handlers.
    TESTING = TESTING
    # Environment mode (development or production), defaults to production
    ENV = ENVIRONMENT


class TestConfig(Config):
    """Flask TestConfig class."""
    SQLALCHEMY_DATABASE_URI = TEST_DB_URL

    # silence the deprecation warning
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Enable testing mode. Exceptions are propagated rather than handled by the the app’s error handlers.
    TESTING = True
    ENV = 'development'
