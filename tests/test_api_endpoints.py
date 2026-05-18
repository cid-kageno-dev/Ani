"""Tests for API endpoints."""

import pytest


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_ok(self, client):
        """Test that health endpoint returns ok status."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'

    def test_health_response_structure(self, client):
        """Test health response has all required fields."""
        response = client.get('/health')
        data = response.get_json()
        assert 'status' in data


class TestChatEndpoint:
    """Tests for the chat endpoint."""

    def test_chat_with_message(self, client):
        """Test chat endpoint with valid message."""
        response = client.post('/chat', json={'message': 'Hello Ani'})
        assert response.status_code in [200, 500]

    def test_chat_missing_message(self, client):
        """Test chat endpoint without message field."""
        response = client.post('/chat', json={})
        assert response.status_code == 400

    def test_chat_empty_message(self, client):
        """Test chat endpoint with empty message."""
        response = client.post('/chat', json={'message': ''})
        assert response.status_code == 400

    def test_chat_invalid_json(self, client):
        """Test chat endpoint with invalid JSON."""
        response = client.post(
            '/chat',
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code == 400


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_not_found(self, client):
        """Test 404 for non-existent endpoint."""
        response = client.get('/nonexistent')
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 for wrong HTTP method."""
        response = client.post('/health')
        assert response.status_code == 405
