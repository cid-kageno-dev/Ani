"""Pytest configuration and fixtures."""

import os
import pytest
from app import create_app


@pytest.fixture
def app():
    """Create and configure a test app."""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'True'
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's CLI."""
    return app.test_cli_runner()
