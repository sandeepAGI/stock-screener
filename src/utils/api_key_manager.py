"""
API Key Manager - Secure storage for user-provided API keys
Uses macOS Keychain for secure credential storage
"""

import keyring
import logging
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class APIKeyStatus:
    """Status information for an API key"""
    is_configured: bool
    is_valid: Optional[bool] = None
    error_message: Optional[str] = None


class APIKeyManager:
    """
    Manages secure storage and retrieval of API keys using macOS Keychain.

    All API keys are stored in the system keychain and never bundled with the app.
    This ensures users provide their own credentials and control their API usage.
    """

    # Service name for keychain (unique identifier for this app)
    SERVICE_NAME = "StockAnalyzer-Pro"

    # Supported API key types
    REDDIT_CLIENT_ID = "reddit_client_id"
    REDDIT_CLIENT_SECRET = "reddit_client_secret"
    REDDIT_USER_AGENT = "reddit_user_agent"
    CLAUDE_API_KEY = "claude_api_key"
    NEWS_API_KEY = "news_api_key"  # Optional

    def __init__(self):
        """Initialize API Key Manager"""
        self.service_name = self.SERVICE_NAME
        logger.info("API Key Manager initialized")

    def save_api_key(self, key_type: str, key_value: str) -> bool:
        """
        Save an API key to the system keychain.

        Args:
            key_type: Type of API key (e.g., 'reddit_client_id')
            key_value: The actual API key value

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            keyring.set_password(self.service_name, key_type, key_value)
            logger.info(f"API key saved successfully: {key_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to save API key {key_type}: {e}")
            return False

    def get_api_key(self, key_type: str) -> Optional[str]:
        """
        Retrieve an API key from the system keychain.

        Args:
            key_type: Type of API key to retrieve

        Returns:
            The API key value, or None if not found
        """
        try:
            key_value = keyring.get_password(self.service_name, key_type)
            if key_value:
                logger.debug(f"API key retrieved: {key_type}")
            else:
                logger.debug(f"API key not found: {key_type}")
            return key_value
        except Exception as e:
            logger.error(f"Failed to retrieve API key {key_type}: {e}")
            return None

    def delete_api_key(self, key_type: str) -> bool:
        """
        Delete an API key from the system keychain.

        Args:
            key_type: Type of API key to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            keyring.delete_password(self.service_name, key_type)
            logger.info(f"API key deleted: {key_type}")
            return True
        except keyring.errors.PasswordDeleteError:
            logger.warning(f"API key not found for deletion: {key_type}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete API key {key_type}: {e}")
            return False

    def has_api_key(self, key_type: str) -> bool:
        """
        Check if an API key is configured.

        Args:
            key_type: Type of API key to check

        Returns:
            True if the key exists and is not empty
        """
        key_value = self.get_api_key(key_type)
        return key_value is not None and len(key_value.strip()) > 0

    def get_all_configured_keys(self) -> Dict[str, bool]:
        """
        Get status of all supported API keys.

        Returns:
            Dictionary mapping key types to configuration status
        """
        return {
            self.REDDIT_CLIENT_ID: self.has_api_key(self.REDDIT_CLIENT_ID),
            self.REDDIT_CLIENT_SECRET: self.has_api_key(self.REDDIT_CLIENT_SECRET),
            self.REDDIT_USER_AGENT: self.has_api_key(self.REDDIT_USER_AGENT),
            self.CLAUDE_API_KEY: self.has_api_key(self.CLAUDE_API_KEY),
            self.NEWS_API_KEY: self.has_api_key(self.NEWS_API_KEY),
        }

    def has_reddit_credentials(self) -> bool:
        """
        Check if all required Reddit API credentials are configured.

        Returns:
            True if client_id, client_secret, and user_agent are all set
        """
        return (
            self.has_api_key(self.REDDIT_CLIENT_ID) and
            self.has_api_key(self.REDDIT_CLIENT_SECRET) and
            self.has_api_key(self.REDDIT_USER_AGENT)
        )

    def has_claude_credentials(self) -> bool:
        """
        Check if Claude API key is configured.

        Returns:
            True if Claude API key is set
        """
        return self.has_api_key(self.CLAUDE_API_KEY)

    def test_reddit_connection(self) -> APIKeyStatus:
        """
        Test Reddit API credentials by attempting to authenticate.

        Returns:
            APIKeyStatus with validation results
        """
        if not self.has_reddit_credentials():
            return APIKeyStatus(
                is_configured=False,
                is_valid=False,
                error_message="Reddit credentials not configured"
            )

        try:
            import praw

            client_id = self.get_api_key(self.REDDIT_CLIENT_ID)
            client_secret = self.get_api_key(self.REDDIT_CLIENT_SECRET)
            user_agent = self.get_api_key(self.REDDIT_USER_AGENT)

            # Attempt to create Reddit instance
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )

            # Test by accessing read-only property
            # This will fail if credentials are invalid
            _ = reddit.read_only

            logger.info("Reddit API credentials validated successfully")
            return APIKeyStatus(
                is_configured=True,
                is_valid=True
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Reddit API validation failed: {error_msg}")
            return APIKeyStatus(
                is_configured=True,
                is_valid=False,
                error_message=f"Invalid credentials: {error_msg}"
            )

    def test_claude_connection(self) -> APIKeyStatus:
        """
        Test Claude API key by attempting to authenticate.

        Returns:
            APIKeyStatus with validation results
        """
        if not self.has_claude_credentials():
            return APIKeyStatus(
                is_configured=False,
                is_valid=False,
                error_message="Claude API key not configured"
            )

        try:
            from anthropic import Anthropic

            api_key = self.get_api_key(self.CLAUDE_API_KEY)

            # Attempt to create Anthropic client
            client = Anthropic(api_key=api_key)

            # Test with a minimal API call
            # Using count_tokens as it's lightweight
            response = client.messages.count_tokens(
                model="claude-3-5-sonnet-20241022",
                messages=[{"role": "user", "content": "test"}]
            )

            logger.info("Claude API key validated successfully")
            return APIKeyStatus(
                is_configured=True,
                is_valid=True
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Claude API validation failed: {error_msg}")
            return APIKeyStatus(
                is_configured=True,
                is_valid=False,
                error_message=f"Invalid API key: {error_msg}"
            )

    def save_reddit_credentials(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str
    ) -> bool:
        """
        Save all Reddit API credentials at once.

        Args:
            client_id: Reddit app client ID
            client_secret: Reddit app client secret
            user_agent: Reddit app user agent string

        Returns:
            True if all credentials saved successfully
        """
        success = True
        success &= self.save_api_key(self.REDDIT_CLIENT_ID, client_id)
        success &= self.save_api_key(self.REDDIT_CLIENT_SECRET, client_secret)
        success &= self.save_api_key(self.REDDIT_USER_AGENT, user_agent)

        if success:
            logger.info("All Reddit credentials saved successfully")
        else:
            logger.error("Failed to save some Reddit credentials")

        return success

    def delete_reddit_credentials(self) -> bool:
        """
        Delete all Reddit API credentials.

        Returns:
            True if all credentials deleted successfully
        """
        success = True
        success &= self.delete_api_key(self.REDDIT_CLIENT_ID)
        success &= self.delete_api_key(self.REDDIT_CLIENT_SECRET)
        success &= self.delete_api_key(self.REDDIT_USER_AGENT)

        if success:
            logger.info("All Reddit credentials deleted successfully")
        else:
            logger.warning("Some Reddit credentials may not have been deleted")

        return success

    def clear_all_keys(self) -> bool:
        """
        Clear all API keys from the system keychain.
        Use with caution - this will remove all configured credentials.

        Returns:
            True if all keys cleared successfully
        """
        success = True
        for key_type in [
            self.REDDIT_CLIENT_ID,
            self.REDDIT_CLIENT_SECRET,
            self.REDDIT_USER_AGENT,
            self.CLAUDE_API_KEY,
            self.NEWS_API_KEY
        ]:
            # Don't fail if key doesn't exist
            try:
                self.delete_api_key(key_type)
            except:
                pass

        logger.info("All API keys cleared")
        return success

    def get_summary(self) -> Dict[str, any]:
        """
        Get a summary of API key configuration status.

        Returns:
            Dictionary with configuration summary
        """
        has_reddit = self.has_reddit_credentials()
        has_claude = self.has_claude_credentials()

        return {
            "reddit_configured": has_reddit,
            "claude_configured": has_claude,
            "reddit_enabled": has_reddit,
            "sentiment_enabled": has_claude,
            "full_functionality": has_reddit and has_claude,
            "limited_mode": not (has_reddit and has_claude)
        }
