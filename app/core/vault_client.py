"""
HashiCorp Vault Client Wrapper
Provides secure secret retrieval from Vault with fallback to mock mode for development.
"""
import hvac
import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class VaultClient:
    """Wrapper for HashiCorp Vault operations"""
    
    def __init__(self, 
                 vault_url: str = "http://localhost:8200",
                 role_id: Optional[str] = None,
                 secret_id: Optional[str] = None,
                 mock_mode: bool = False):
        """
        Initialize Vault client
        
        Args:
            vault_url: Vault server URL
            role_id: AppRole Role ID for authentication
            secret_id: AppRole Secret ID for authentication
            mock_mode: If True, use mock secrets instead of real Vault
        """
        self.mock_mode = mock_mode
        self.vault_url = vault_url
        
        if mock_mode:
            logger.warning("⚠️  VAULT MOCK MODE ENABLED - Using hardcoded secrets for development only!")
            self.client = None
            self._mock_secrets = {
                "database/master_key": {"value": "dev-master-key-32-bytes-long!!"},
                "database/shard0": {
                    "username": "postgres",
                    "password": "postgres",
                    "host": "localhost",
                    "port": "5432",
                    "database": "aurahealth_shard0"
                },
                "database/shard1": {
                    "username": "postgres",
                    "password": "postgres",
                    "host": "localhost",
                    "port": "5433",
                    "database": "aurahealth_shard1"
                },
                "api/google_maps": {"key": "mock-google-maps-api-key"},
                "api/twilio": {
                    "account_sid": "mock-twilio-sid",
                    "auth_token": "mock-twilio-token"
                }
            }
        else:
            try:
                self.client = hvac.Client(url=vault_url)
                
                # Authenticate using AppRole
                if role_id and secret_id:
                    self.client.auth.approle.login(
                        role_id=role_id,
                        secret_id=secret_id
                    )
                    logger.info("✅ Vault authentication successful")
                else:
                    logger.error("❌ Vault credentials (role_id/secret_id) not provided")
                    raise ValueError("role_id and secret_id required for Vault authentication")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize Vault client: {e}")
                raise
    
    def get_secret(self, path: str, key: Optional[str] = None) -> Any:
        """
        Fetch a secret from Vault KV store
        
        Args:
            path: Secret path in Vault (e.g., 'database/master_key')
            key: Specific key within the secret (optional)
            
        Returns:
            Secret value or dict of all values if key not specified
            
        Example:
            >>> vault.get_secret("database/master_key", "value")
            "abcd1234..."
            >>> vault.get_secret("database/shard0")
            {"username": "...", "password": "..."}
        """
        if self.mock_mode:
            secret_data = self._mock_secrets.get(path, {})
            if key:
                return secret_data.get(key)
            return secret_data
        
        try:
            # Read from KV v2 secrets engine
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            secret_data = response['data']['data']
            
            if key:
                return secret_data.get(key)
            return secret_data
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch secret from Vault: path={path}, error={e}")
            raise
    
    def get_database_credentials(self, shard_id: int) -> Dict[str, str]:
        """
        Get dynamic database credentials for a specific shard
        
        Args:
            shard_id: Shard identifier (0 or 1)
            
        Returns:
            Dict with host, port, database, username, password
        """
        path = f"database/shard{shard_id}"
        return self.get_secret(path)
    
    def get_master_encryption_key(self) -> str:
        """
        Fetch the master encryption key for AES-256-GCM
        
        Returns:
            32-byte master key as string
        """
        return self.get_secret("database/master_key", "value")
    
    def get_api_key(self, service: str) -> Dict[str, str]:
        """
        Fetch API keys for external services
        
        Args:
            service: Service name ('google_maps', 'twilio')
            
        Returns:
            Dict with API credentials
        """
        path = f"api/{service}"
        return self.get_secret(path)


# Global Vault instance (initialized in app startup)
vault_instance: Optional[VaultClient] = None


def init_vault(mock_mode: bool = False) -> VaultClient:
    """
    Initialize the global Vault client
    
    Args:
        mock_mode: Enable mock mode for development
        
    Returns:
        VaultClient instance
    """
    global vault_instance
    
    if mock_mode:
        vault_instance = VaultClient(mock_mode=True)
    else:
        role_id = os.getenv("VAULT_ROLE_ID")
        secret_id = os.getenv("VAULT_SECRET_ID")
        vault_url = os.getenv("VAULT_URL", "http://localhost:8200")
        
        vault_instance = VaultClient(
            vault_url=vault_url,
            role_id=role_id,
            secret_id=secret_id,
            mock_mode=False
        )
    
    return vault_instance


def get_vault() -> VaultClient:
    """Get the global Vault instance"""
    if vault_instance is None:
        raise RuntimeError("Vault not initialized. Call init_vault() first.")
    return vault_instance
