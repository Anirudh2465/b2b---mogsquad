"""
AES-256-GCM Encryption Module
Implements row-level encryption with authentication for patient data.
"""
import os
import hashlib
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Handles AES-256-GCM encryption/decryption with user-specific keys"""
    
    def __init__(self, master_key: str):
        """
        Initialize encryption manager
        
        Args:
            master_key: 32-byte master key from Vault
        """
        # Ensure master key is exactly 32 bytes
        self.master_key = master_key.encode('utf-8')[:32].ljust(32, b'\x00')
        logger.info("✅ Encryption manager initialized with master key")
    
    def _derive_user_key(self, user_id: str) -> bytes:
        """
        Derive a user-specific encryption key from master key + user_id
        
        Args:
            user_id: Patient UUID as string
            
        Returns:
            32-byte derived key
        """
        # Use PBKDF2 to derive a unique key per user
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=user_id.encode('utf-8'),
            iterations=100000,
        )
        return kdf.derive(self.master_key)
    
    def encrypt(self, plaintext: str, user_id: str) -> bytes:
        """
        Encrypt plaintext using AES-256-GCM
        
        Args:
            plaintext: Data to encrypt
            user_id: Patient UUID for key derivation
            
        Returns:
            Encrypted data (IV + ciphertext + auth_tag) as bytes
            
        Format: [96-bit IV][ciphertext][128-bit auth_tag]
        """
        if not plaintext:
            return b''
        
        # Derive user-specific key
        user_key = self._derive_user_key(user_id)
        
        # Generate 96-bit (12 bytes) random IV
        iv = os.urandom(12)
        
        # Initialize AES-GCM cipher
        aesgcm = AESGCM(user_key)
        
        # Encrypt (returns ciphertext + 128-bit auth tag appended)
        ciphertext = aesgcm.encrypt(iv, plaintext.encode('utf-8'), None)
        
        # Return: IV + ciphertext+tag
        return iv + ciphertext
    
    def decrypt(self, encrypted_data: bytes, user_id: str) -> str:
        """
        Decrypt AES-256-GCM encrypted data
        
        Args:
            encrypted_data: Encrypted bytes (IV + ciphertext + auth_tag)
            user_id: Patient UUID for key derivation
            
        Returns:
            Decrypted plaintext as string
            
        Raises:
            cryptography.exceptions.InvalidTag: If data was tampered with
        """
        if not encrypted_data:
            return ''
        
        # Derive user-specific key
        user_key = self._derive_user_key(user_id)
        
        # Extract IV (first 12 bytes)
        iv = encrypted_data[:12]
        
        # Extract ciphertext + auth_tag (remaining bytes)
        ciphertext = encrypted_data[12:]
        
        # Initialize AES-GCM cipher
        aesgcm = AESGCM(user_key)
        
        # Decrypt and verify authentication tag
        try:
            plaintext = aesgcm.decrypt(iv, ciphertext, None)
            return plaintext.decode('utf-8')
        except Exception as e:
            logger.error(f"❌ Decryption failed for user {user_id}: {e}")
            raise ValueError("Decryption failed - data may be corrupted or tampered")


# Global encryption manager instance
encryption_manager: EncryptionManager = None


def init_encryption(master_key: str) -> EncryptionManager:
    """
    Initialize the global encryption manager
    
    Args:
        master_key: 32-byte master key from Vault
    """
    global encryption_manager
    encryption_manager = EncryptionManager(master_key)
    return encryption_manager


def get_encryption_manager() -> EncryptionManager:
    """Get the global encryption manager instance"""
    if encryption_manager is None:
        raise RuntimeError("Encryption manager not initialized. Call init_encryption() first.")
    return encryption_manager
