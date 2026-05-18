"""Tests for configuration loading."""

import pytest


class TestConfigLoading:
    """Tests for config.py module."""

    def test_google_api_keys_loaded(self):
        """Test that Google API keys attribute exists."""
        try:
            from config import Config
            assert hasattr(Config, 'GOOGLE_API_KEYS')
            assert isinstance(Config.GOOGLE_API_KEYS, list)
        except ImportError:
            pytest.skip("Config module not available")

    def test_database_backend_is_firebase(self):
        """Test database backend is hardcoded to firebase."""
        try:
            from config import Config
            assert Config.DATABASE_BACKEND == 'firebase'
        except ImportError:
            pytest.skip("Config module not available")

    def test_firebase_project_id_configured(self):
        """Test Firebase project ID is set."""
        try:
            from config import Config
            assert Config.FIREBASE_PROJECT_ID == 'gen-lang-client-0109922552'
        except ImportError:
            pytest.skip("Config module not available")

    def test_firebase_collection_configured(self):
        """Test Firebase collection is set."""
        try:
            from config import Config
            assert Config.FIREBASE_COLLECTION == 'chat_interactions'
        except ImportError:
            pytest.skip("Config module not available")

    def test_github_username_configured(self):
        """Test GitHub username is configured."""
        try:
            from config import Config
            assert Config.GITHUB_USERNAME == 'cid-kageno-dev'
        except ImportError:
            pytest.skip("Config module not available")

    def test_firebase_service_account_json_present(self):
        """Test Firebase service account JSON is hardcoded."""
        try:
            import json
            from config import Config
            assert Config.FIREBASE_SERVICE_ACCOUNT_JSON
            data = json.loads(Config.FIREBASE_SERVICE_ACCOUNT_JSON)
            assert data.get('type') == 'service_account'
            assert data.get('project_id') == 'gen-lang-client-0109922552'
        except ImportError:
            pytest.skip("Config module not available")
