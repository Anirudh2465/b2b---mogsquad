"""
Database Connection Manager
Manages connections to multiple PostgreSQL shards with dynamic credential rotation.
"""
import psycopg2
from psycopg2 import pool
from typing import Dict, Optional
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Manages connection pools for multiple database shards"""
    
    def __init__(self):
        """Initialize connection manager"""
        self.shard_pools: Dict[int, pool.ThreadedConnectionPool] = {}
        logger.info("✅ Database connection manager initialized")
    
    def add_shard(self, 
                  shard_id: int,
                  host: str,
                  port: int,
                  database: str,
                  username: str,
                  password: str,
                  min_connections: int = 2,
                  max_connections: int = 10):
        """
        Add a database shard with connection pooling
        
        Args:
            shard_id: Shard identifier (0, 1, etc.)
            host: Database host
            port: Database port
            database: Database name
            username: DB username
            password: DB password
            min_connections: Minimum pool size
            max_connections: Maximum pool size
        """
        try:
            connection_pool = pool.ThreadedConnectionPool(
                min_connections,
                max_connections,
                host=host,
                port=port,
                database=database,
                user=username,
                password=password
            )
            
            self.shard_pools[shard_id] = connection_pool
            logger.info(f"✅ Shard {shard_id} connected: {database}@{host}:{port}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Shard {shard_id}: {e}")
            raise
    
    @contextmanager
    def get_connection(self, shard_id: int):
        """
        Get a connection from the shard pool (context manager)
        
        Args:
            shard_id: Shard to connect to
            
        Yields:
            psycopg2 connection object
            
        Example:
            >>> with db_manager.get_connection(0) as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT * FROM patients")
        """
        if shard_id not in self.shard_pools:
            raise ValueError(f"Shard {shard_id} not initialized")
        
        connection = None
        try:
            connection = self.shard_pools[shard_id].getconn()
            yield connection
            connection.commit()
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"❌ Database error on Shard {shard_id}: {e}")
            raise
        finally:
            if connection:
                self.shard_pools[shard_id].putconn(connection)
    
    def close_all(self):
        """Close all connection pools"""
        for shard_id, pool in self.shard_pools.items():
            pool.closeall()
            logger.info(f"✅ Closed connection pool for Shard {shard_id}")


# Global database manager instance
db_manager: Optional[DatabaseConnectionManager] = None


def init_database_manager() -> DatabaseConnectionManager:
    """Initialize the global database manager"""
    global db_manager
    db_manager = DatabaseConnectionManager()
    return db_manager


def get_db_manager() -> DatabaseConnectionManager:
    """Get the global database manager instance"""
    if db_manager is None:
        raise RuntimeError("Database manager not initialized. Call init_database_manager() first.")
    return db_manager
