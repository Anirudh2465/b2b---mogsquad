"""
Configuration Management
Handles loading secrets from environment variables (.env)
Replacing complex Vault integration with simple python-dotenv
"""
import os
from typing import Dict, Optional
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class ConfigManager:
    """Simple configuration manager using environment variables"""
    
    @staticmethod
    def get_database_credentials(shard_id: int) -> Dict[str, str]:
        """Get database credentials from env vars"""
        prefix = f"DB_SHARD{shard_id}"
        return {
            "host": os.getenv(f"{prefix}_HOST", "localhost"),
            "port": os.getenv(f"{prefix}_PORT", "5432"),
            "database": os.getenv(f"{prefix}_DATABASE", f"aurahealth_shard{shard_id}"),
            "username": os.getenv(f"{prefix}_USER", "postgres"),
            "password": os.getenv(f"{prefix}_PASSWORD", "postgres")
        }

    @staticmethod
    def get_master_encryption_key() -> str:
        """Get master encryption key"""
        # Default dev key if not set
        return os.getenv("MASTER_ENCRYPTION_KEY", "dev-master-key-32-bytes-long!!")

    @staticmethod
    def get_api_key(service: str) -> Dict[str, str]:
        """Get API keys for services"""
        if service == 'gemini':
            return {
                "api_key": os.getenv("GEMINI_API_KEY"),
                "model_name": os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            }
        elif service == 'google_maps':
            return {
                "api_key": os.getenv("GOOGLE_MAPS_API_KEY")
            }
        elif service == 'twilio':
            return {
                "account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
                "auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
                "phone_number": os.getenv("TWILIO_PHONE_NUMBER")
            }
        return {}

# Global instance for compatibility
config = ConfigManager()

def get_config() -> ConfigManager:
    return config
