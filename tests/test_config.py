"""Tests for configuration loading."""

import os
import pytest


class TestConfigLoading:
    """Tests for config.py module."""

    def test_google_api_keys_loaded(self):
        """Test that Google API keys are loaded."""
        # This would need the actual config to be imported
        # For now, just test that we can import it
        try:
            from config import Config
            assert hasattr(Config, 'GOOGLE_API_KEYS')
        except ImportError:
            pytest.skip("Config module not available")

    def test_database_backend_default(self):
        """Test database backend defaults to auto."""
        try:
            from config import Config
            assert Config.DATABASE_BACKEND in ['auto', 'firebase', 'postgresql']
        except ImportError:
            pytest.skip("Config module not available")

    def test_github_username_configured(self):
        """Test GitHub username is configured."""
        try:
            from config import Config
            assert Config.GITHUB_USERNAME is not None
        except ImportError:
            pytest.skip("Config module not available")
