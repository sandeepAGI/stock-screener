"""
Unit tests for API Key Manager
Tests secure storage, retrieval, and validation of API credentials
"""

import pytest
from src.utils.api_key_manager import APIKeyManager, APIKeyStatus


class TestAPIKeyManager:
    """Test suite for APIKeyManager"""

    @pytest.fixture
    def manager(self):
        """Create a fresh API Key Manager for each test"""
        mgr = APIKeyManager()
        # Clean up any existing test keys
        mgr.clear_all_keys()
        yield mgr
        # Clean up after test
        mgr.clear_all_keys()

    def test_save_and_retrieve_reddit_client_id(self, manager):
        """Test saving and retrieving Reddit client ID"""
        test_client_id = "test_client_id_12345"

        # Save
        assert manager.save_api_key(APIKeyManager.REDDIT_CLIENT_ID, test_client_id)

        # Retrieve
        retrieved = manager.get_api_key(APIKeyManager.REDDIT_CLIENT_ID)
        assert retrieved == test_client_id

    def test_save_and_retrieve_reddit_client_secret(self, manager):
        """Test saving and retrieving Reddit client secret"""
        test_secret = "test_secret_67890"

        # Save
        assert manager.save_api_key(APIKeyManager.REDDIT_CLIENT_SECRET, test_secret)

        # Retrieve
        retrieved = manager.get_api_key(APIKeyManager.REDDIT_CLIENT_SECRET)
        assert retrieved == test_secret

    def test_save_and_retrieve_claude_key(self, manager):
        """Test saving and retrieving Claude API key"""
        test_key = "sk-ant-api03-test-key-12345"

        # Save
        assert manager.save_api_key(APIKeyManager.CLAUDE_API_KEY, test_key)

        # Retrieve
        retrieved = manager.get_api_key(APIKeyManager.CLAUDE_API_KEY)
        assert retrieved == test_key

    def test_has_api_key(self, manager):
        """Test checking if API key exists"""
        # Initially should not have key
        assert not manager.has_api_key(APIKeyManager.REDDIT_CLIENT_ID)

        # After saving should have key
        manager.save_api_key(APIKeyManager.REDDIT_CLIENT_ID, "test_value")
        assert manager.has_api_key(APIKeyManager.REDDIT_CLIENT_ID)

    def test_delete_api_key(self, manager):
        """Test deleting an API key"""
        # Save a key
        manager.save_api_key(APIKeyManager.REDDIT_CLIENT_ID, "test_value")
        assert manager.has_api_key(APIKeyManager.REDDIT_CLIENT_ID)

        # Delete it
        assert manager.delete_api_key(APIKeyManager.REDDIT_CLIENT_ID)
        assert not manager.has_api_key(APIKeyManager.REDDIT_CLIENT_ID)

    def test_delete_nonexistent_key(self, manager):
        """Test deleting a key that doesn't exist"""
        # Should return False but not crash
        result = manager.delete_api_key(APIKeyManager.REDDIT_CLIENT_ID)
        assert result == False

    def test_save_reddit_credentials(self, manager):
        """Test saving all Reddit credentials at once"""
        client_id = "test_client"
        client_secret = "test_secret"
        user_agent = "TestApp:v1.0"

        # Save all at once
        assert manager.save_reddit_credentials(client_id, client_secret, user_agent)

        # Verify all saved
        assert manager.get_api_key(APIKeyManager.REDDIT_CLIENT_ID) == client_id
        assert manager.get_api_key(APIKeyManager.REDDIT_CLIENT_SECRET) == client_secret
        assert manager.get_api_key(APIKeyManager.REDDIT_USER_AGENT) == user_agent

    def test_delete_reddit_credentials(self, manager):
        """Test deleting all Reddit credentials at once"""
        # Save credentials
        manager.save_reddit_credentials("test_client", "test_secret", "TestApp:v1.0")

        # Delete all
        assert manager.delete_reddit_credentials()

        # Verify all deleted
        assert not manager.has_api_key(APIKeyManager.REDDIT_CLIENT_ID)
        assert not manager.has_api_key(APIKeyManager.REDDIT_CLIENT_SECRET)
        assert not manager.has_api_key(APIKeyManager.REDDIT_USER_AGENT)

    def test_has_reddit_credentials(self, manager):
        """Test checking if all Reddit credentials are configured"""
        # Initially should not have credentials
        assert not manager.has_reddit_credentials()

        # After saving all, should have credentials
        manager.save_reddit_credentials("client", "secret", "agent")
        assert manager.has_reddit_credentials()

        # After deleting one, should not have credentials
        manager.delete_api_key(APIKeyManager.REDDIT_CLIENT_ID)
        assert not manager.has_reddit_credentials()

    def test_has_claude_credentials(self, manager):
        """Test checking if Claude API key is configured"""
        # Initially should not have credentials
        assert not manager.has_claude_credentials()

        # After saving, should have credentials
        manager.save_api_key(APIKeyManager.CLAUDE_API_KEY, "sk-ant-test")
        assert manager.has_claude_credentials()

    def test_get_all_configured_keys(self, manager):
        """Test getting status of all API keys"""
        # Initially all should be False
        status = manager.get_all_configured_keys()
        assert all(not v for v in status.values())

        # After saving some keys
        manager.save_api_key(APIKeyManager.REDDIT_CLIENT_ID, "test")
        manager.save_api_key(APIKeyManager.CLAUDE_API_KEY, "test")

        status = manager.get_all_configured_keys()
        assert status[APIKeyManager.REDDIT_CLIENT_ID] == True
        assert status[APIKeyManager.CLAUDE_API_KEY] == True
        assert status[APIKeyManager.REDDIT_CLIENT_SECRET] == False

    def test_get_summary(self, manager):
        """Test getting configuration summary"""
        # Initially limited mode
        summary = manager.get_summary()
        assert summary["reddit_configured"] == False
        assert summary["claude_configured"] == False
        assert summary["limited_mode"] == True
        assert summary["full_functionality"] == False

        # After configuring Reddit
        manager.save_reddit_credentials("client", "secret", "agent")
        summary = manager.get_summary()
        assert summary["reddit_configured"] == True
        assert summary["reddit_enabled"] == True

        # After configuring Claude
        manager.save_api_key(APIKeyManager.CLAUDE_API_KEY, "sk-ant-test")
        summary = manager.get_summary()
        assert summary["claude_configured"] == True
        assert summary["sentiment_enabled"] == True
        assert summary["full_functionality"] == True
        assert summary["limited_mode"] == False

    def test_clear_all_keys(self, manager):
        """Test clearing all API keys"""
        # Save several keys
        manager.save_reddit_credentials("client", "secret", "agent")
        manager.save_api_key(APIKeyManager.CLAUDE_API_KEY, "sk-ant-test")

        # Clear all
        manager.clear_all_keys()

        # Verify all cleared
        status = manager.get_all_configured_keys()
        assert all(not v for v in status.values())

    def test_empty_string_not_considered_configured(self, manager):
        """Test that empty strings are not considered valid API keys"""
        # Save empty string
        manager.save_api_key(APIKeyManager.REDDIT_CLIENT_ID, "")

        # Should not be considered configured
        assert not manager.has_api_key(APIKeyManager.REDDIT_CLIENT_ID)

    def test_whitespace_only_not_considered_configured(self, manager):
        """Test that whitespace-only strings are not considered valid API keys"""
        # Save whitespace
        manager.save_api_key(APIKeyManager.REDDIT_CLIENT_ID, "   ")

        # Should not be considered configured
        assert not manager.has_api_key(APIKeyManager.REDDIT_CLIENT_ID)

    def test_test_reddit_connection_not_configured(self, manager):
        """Test Reddit connection validation when not configured"""
        status = manager.test_reddit_connection()

        assert status.is_configured == False
        assert status.is_valid == False
        assert "not configured" in status.error_message.lower()

    def test_test_claude_connection_not_configured(self, manager):
        """Test Claude connection validation when not configured"""
        status = manager.test_claude_connection()

        assert status.is_configured == False
        assert status.is_valid == False
        assert "not configured" in status.error_message.lower()

    def test_test_reddit_connection_invalid_credentials(self, manager):
        """Test Reddit connection validation with invalid credentials

        Note: Reddit API doesn't validate credentials until actual API calls are made.
        The connection test will pass even with invalid credentials, but actual
        data collection will fail. This is expected behavior.
        """
        # Save invalid credentials
        manager.save_reddit_credentials(
            "invalid_client",
            "invalid_secret",
            "TestApp:v1.0"
        )

        status = manager.test_reddit_connection()

        # Reddit allows connection with invalid creds (validation happens on API calls)
        assert status.is_configured == True
        # Note: is_valid may be True here, but will fail on actual API usage

    def test_test_claude_connection_invalid_key(self, manager):
        """Test Claude connection validation with invalid key"""
        # Save invalid key
        manager.save_api_key(APIKeyManager.CLAUDE_API_KEY, "invalid-key-12345")

        status = manager.test_claude_connection()

        assert status.is_configured == True
        assert status.is_valid == False
        assert status.error_message is not None

    def test_service_name_uniqueness(self, manager):
        """Test that service name is unique to avoid conflicts"""
        assert manager.service_name == "StockAnalyzer-Pro"
        assert manager.SERVICE_NAME == "StockAnalyzer-Pro"

    def test_multiple_managers_share_same_keys(self):
        """Test that multiple manager instances access the same keychain"""
        manager1 = APIKeyManager()
        manager2 = APIKeyManager()

        try:
            # Save with manager1
            manager1.save_api_key(APIKeyManager.REDDIT_CLIENT_ID, "shared_key")

            # Retrieve with manager2
            retrieved = manager2.get_api_key(APIKeyManager.REDDIT_CLIENT_ID)
            assert retrieved == "shared_key"

        finally:
            # Clean up
            manager1.clear_all_keys()


class TestAPIKeyStatus:
    """Test suite for APIKeyStatus dataclass"""

    def test_api_key_status_creation(self):
        """Test creating APIKeyStatus objects"""
        # Not configured
        status = APIKeyStatus(is_configured=False)
        assert status.is_configured == False
        assert status.is_valid is None
        assert status.error_message is None

        # Configured and valid
        status = APIKeyStatus(is_configured=True, is_valid=True)
        assert status.is_configured == True
        assert status.is_valid == True

        # Configured but invalid
        status = APIKeyStatus(
            is_configured=True,
            is_valid=False,
            error_message="Invalid credentials"
        )
        assert status.is_configured == True
        assert status.is_valid == False
        assert status.error_message == "Invalid credentials"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
