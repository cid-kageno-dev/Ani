"""Tests for GitHub context cache."""

import time
import pytest
from unittest.mock import patch, MagicMock


class TestGitHubCache:
    """Tests for the GitHub context in-memory cache."""

    def test_cache_is_used_on_second_call(self):
        """Second call within TTL should not trigger a new fetch."""
        import app.services.ai_service as ai_svc

        fake_context = "cached github data"
        ai_svc._github_cache["data"] = fake_context
        ai_svc._github_cache["fetched_at"] = time.time()

        with patch.object(ai_svc, "_safe_get") as mock_get:
            result = ai_svc.fetch_github_context()
            mock_get.assert_not_called()

        assert result == fake_context

    def test_cache_expires_after_ttl(self):
        """Cache should be refreshed when TTL has elapsed."""
        import app.services.ai_service as ai_svc
        from config import Config

        ai_svc._github_cache["data"] = "old data"
        ai_svc._github_cache["fetched_at"] = time.time() - Config.GITHUB_CACHE_TTL - 1

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.text = ""

        with patch.object(ai_svc, "_safe_get", return_value=mock_response):
            result = ai_svc.fetch_github_context()

        assert ai_svc._github_cache["data"] is not None
        assert ai_svc._github_cache["fetched_at"] > time.time() - 5

    def test_empty_cache_triggers_fetch(self):
        """Empty cache should always trigger a GitHub fetch."""
        import app.services.ai_service as ai_svc

        ai_svc._github_cache["data"] = None
        ai_svc._github_cache["fetched_at"] = 0

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.text = ""

        with patch.object(ai_svc, "_safe_get", return_value=mock_response):
            ai_svc.fetch_github_context()

        assert ai_svc._github_cache["data"] is not None
