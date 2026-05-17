"""Integration tests for complete workflows."""

import pytest


class TestIntegration:
    """Integration tests."""

    def test_app_creation(self, app):
        """Test that app can be created."""
        assert app is not None
        assert app.config['TESTING'] is True

    def test_client_initialization(self, client):
        """Test that test client is initialized."""
        assert client is not None

    @pytest.mark.integration
    def test_health_check_integration(self, client):
        """Test health check in integration."""
        response = client.get('/health')
        assert response.status_code == 200
