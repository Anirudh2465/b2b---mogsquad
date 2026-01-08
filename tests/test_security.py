"""
Unit Tests for Security Infrastructure
Tests Vault, Encryption, Sharding, and Rate Limiting
"""
import unittest
from uuid import uuid4

from app.core.vault_client import VaultClient
from app.core.security import EncryptionManager
from app.database.router import ShardRouter


class TestVaultClient(unittest.TestCase):
    """Test Vault client wrapper"""
    
    def setUp(self):
        """Initialize mock Vault client"""
        self.vault = VaultClient(mock_mode=True)
    
    def test_get_master_key(self):
        """Test fetching master encryption key"""
        key = self.vault.get_master_encryption_key()
        self.assertIsNotNone(key)
        self.assertIsInstance(key, str)
    
    def test_get_database_credentials(self):
        """Test fetching database credentials"""
        creds = self.vault.get_database_credentials(0)
        self.assertIn('username', creds)
        self.assertIn('password', creds)
        self.assertIn('host', creds)
        self.assertEqual(creds['database'], 'aurahealth_shard0')
    
    def test_get_api_key(self):
        """Test fetching API keys"""
        twilio = self.vault.get_api_key('twilio')
        self.assertIn('account_sid', twilio)
        self.assertIn('auth_token', twilio)


class TestEncryption(unittest.TestCase):
    """Test AES-256-GCM encryption"""
    
    def setUp(self):
        """Initialize encryption manager"""
        self.encryption = EncryptionManager("test-master-key-32-bytes-long")
        self.user_id = str(uuid4())
    
    def test_encrypt_decrypt_cycle(self):
        """Test encryption and decryption returns original plaintext"""
        plaintext = "John Doe - Patient with diabetes"
        
        # Encrypt
        encrypted = self.encryption.encrypt(plaintext, self.user_id)
        self.assertIsInstance(encrypted, bytes)
        self.assertGreater(len(encrypted), len(plaintext))
        
        # Decrypt
        decrypted = self.encryption.decrypt(encrypted, self.user_id)
        self.assertEqual(decrypted, plaintext)
    
    def test_different_users_different_ciphertext(self):
        """Test same plaintext encrypts differently for different users"""
        plaintext = "Secret Medical Data"
        user1 = str(uuid4())
        user2 = str(uuid4())
        
        encrypted1 = self.encryption.encrypt(plaintext, user1)
        encrypted2 = self.encryption.encrypt(plaintext, user2)
        
        # Same plaintext should produce different ciphertext
        self.assertNotEqual(encrypted1, encrypted2)
        
        # But both decrypt correctly
        self.assertEqual(self.encryption.decrypt(encrypted1, user1), plaintext)
        self.assertEqual(self.encryption.decrypt(encrypted2, user2), plaintext)
    
    def test_empty_string(self):
        """Test handling of empty strings"""
        encrypted = self.encryption.encrypt("", self.user_id)
        self.assertEqual(encrypted, b'')
        
        decrypted = self.encryption.decrypt(b'', self.user_id)
        self.assertEqual(decrypted, '')
    
    def test_wrong_user_cannot_decrypt(self):
        """Test that wrong user ID cannot decrypt data"""
        plaintext = "Top Secret"
        user1 = str(uuid4())
        user2 = str(uuid4())
        
        encrypted = self.encryption.encrypt(plaintext, user1)
        
        # Attempting to decrypt with wrong user should fail
        with self.assertRaises(ValueError):
            self.encryption.decrypt(encrypted, user2)


class TestShardRouter(unittest.TestCase):
    """Test database sharding router"""
    
    def setUp(self):
        """Initialize shard router"""
        self.router = ShardRouter(num_shards=2)
    
    def test_shard_assignment_deterministic(self):
        """Test that same user_id always goes to same shard"""
        user_id = str(uuid4())
        
        shard1 = self.router.get_shard_id(user_id)
        shard2 = self.router.get_shard_id(user_id)
        shard3 = self.router.get_shard_id(user_id)
        
        self.assertEqual(shard1, shard2)
        self.assertEqual(shard2, shard3)
    
    def test_shard_distribution(self):
        """Test that users are distributed across shards"""
        shard_counts = {0: 0, 1: 0}
        
        # Generate 100 random user IDs
        for _ in range(100):
            user_id = str(uuid4())
            shard_id = self.router.get_shard_id(user_id)
            shard_counts[shard_id] += 1
        
        # Both shards should have some users (rough distribution)
        self.assertGreater(shard_counts[0], 0)
        self.assertGreater(shard_counts[1], 0)
    
    def test_validate_shard_consistency(self):
        """Test shard consistency validation"""
        user_id = str(uuid4())
        correct_shard = self.router.get_shard_id(user_id)
        
        # Correct shard should validate
        self.assertTrue(self.router.validate_shard_consistency(user_id, correct_shard))
        
        # Wrong shard should fail validation
        wrong_shard = 1 - correct_shard  # Flip 0->1 or 1->0
        self.assertFalse(self.router.validate_shard_consistency(user_id, wrong_shard))


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
