"""
Database Sharding Router
Routes queries to appropriate PostgreSQL shard based on user_id hash.
"""
import hashlib
from typing import Literal
import logging

logger = logging.getLogger(__name__)

ShardId = Literal[0, 1]


class ShardRouter:
    """Routes database queries to the correct shard based on user_id"""
    
    def __init__(self, num_shards: int = 2):
        """
        Initialize shard router
        
        Args:
            num_shards: Total number of shards (default: 2)
        """
        self.num_shards = num_shards
        logger.info(f"✅ Shard router initialized with {num_shards} shards")
    
    def get_shard_id(self, user_id: str) -> ShardId:
        """
        Determine which shard a user belongs to
        
        Strategy: hash(user_id) % num_shards
        
        Args:
            user_id: Patient UUID as string
            
        Returns:
            Shard ID (0 or 1)
            
        Example:
            >>> router.get_shard_id("550e8400-e29b-41d4-a716-446655440000")
            0
        """
        # Hash the user_id using SHA-256
        hash_digest = hashlib.sha256(user_id.encode('utf-8')).hexdigest()
        
        # Convert first 8 chars of hex to integer
        hash_int = int(hash_digest[:8], 16)
        
        # Modulo to determine shard
        shard_id = hash_int % self.num_shards
        
        logger.debug(f"User {user_id[:8]}... → Shard {shard_id}")
        return shard_id
    
    def validate_shard_consistency(self, user_id: str, stored_shard_id: int) -> bool:
        """
        Verify that a record is in the correct shard
        
        Args:
            user_id: Patient UUID
            stored_shard_id: Shard ID stored in the database record
            
        Returns:
            True if consistent, False if data integrity issue
        """
        expected_shard = self.get_shard_id(user_id)
        
        if expected_shard != stored_shard_id:
            logger.error(
                f"⚠️  SHARD MISMATCH: User {user_id} expected in Shard {expected_shard}, "
                f"but found in Shard {stored_shard_id}!"
            )
            return False
        
        return True


# Global shard router instance
shard_router: ShardRouter = None


def init_shard_router(num_shards: int = 2) -> ShardRouter:
    """Initialize the global shard router"""
    global shard_router
    shard_router = ShardRouter(num_shards)
    return shard_router


def get_shard_router() -> ShardRouter:
    """Get the global shard router instance"""
    if shard_router is None:
        raise RuntimeError("Shard router not initialized. Call init_shard_router() first.")
    return shard_router
