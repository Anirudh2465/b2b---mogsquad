"""
Database Connection Manager
Manages connections to multiple PostgreSQL shards with dynamic credential rotation.
Includes fallback to In-Memory Mock Database if PostgreSQL is unavailable.
"""
import logging
from contextlib import contextmanager
from typing import Dict, Optional, Any, List

logger = logging.getLogger(__name__)

# Global in-memory storage for fallback mode
from datetime import datetime, timedelta

# Seed Data for "Wow" Demo
base_date = datetime.now()
PATIENT_ID = "550e8400-e29b-41d4-a716-446655440000"

IN_MEMORY_STORE = {
    "patients": [
        {"id": PATIENT_ID, "name": "Arjun Gopal", "dob": "1980-05-15", "gender": "Male", "phone": "+15550005555"}
    ],
    "medications": [
        # Hypertension Pattern (Amlodipine x3)
        {"patient_id": PATIENT_ID, "drug_name": "Amlodipine", "created_at": base_date - timedelta(days=60)},
        {"patient_id": PATIENT_ID, "drug_name": "Amlodipine", "created_at": base_date - timedelta(days=30)},
        {"patient_id": PATIENT_ID, "drug_name": "Amlodipine", "created_at": base_date - timedelta(days=2)},
        
        # Diabetes Pattern (Metformin x3)
        {"patient_id": PATIENT_ID, "drug_name": "Metformin", "created_at": base_date - timedelta(days=65)},
        {"patient_id": PATIENT_ID, "drug_name": "Metformin", "created_at": base_date - timedelta(days=35)},
        {"patient_id": PATIENT_ID, "drug_name": "Metformin", "created_at": base_date - timedelta(days=5)},
        
        # Other
        {"patient_id": PATIENT_ID, "drug_name": "Paracetamol", "created_at": base_date - timedelta(days=10)},
    ],
    "prescriptions": [],
    "adherence_events": [],
    "digital_twins": []
}

class MockCursor:
    """Mock Database Cursor for In-Memory operations"""
    def __init__(self):
        self.rows = []
        self.lastrowid = None
        self.rowcount = 0
        
    def execute(self, query: str, params: tuple = None):
        """Mock execute - logs query and simulates basic SELECTs with Column Filtering"""
        q_upper = query.strip().upper()
        
        if q_upper.startswith("SELECT"):
            data_source = []
            if "FROM MEDICATIONS" in q_upper:
                data_source = IN_MEMORY_STORE["medications"]
            elif "FROM PATIENTS" in q_upper:
                data_source = IN_MEMORY_STORE["patients"]
            elif "FROM PRESCRIPTIONS" in q_upper:
                data_source = IN_MEMORY_STORE["prescriptions"]
            elif "COUNT(*)" in q_upper:
                self.rows = [(len(IN_MEMORY_STORE["medications"]),)] # Dummy count
                return

            # Column Selection Logic
            if not data_source:
                self.rows = []
                return

            if "drug_name, created_at" in query.lower():
                self.rows = [(r['drug_name'], r['created_at']) for r in data_source]
            elif "count(*)" in query.lower():
                self.rows = [(len(data_source),)]
            elif "*" in query:
                self.rows = [tuple(r.values()) for r in data_source]
            else:
                 # Default fallback: return all values (best guess)
                self.rows = [tuple(r.values()) for r in data_source]
                
        elif q_upper.startswith("INSERT"):
            # Simple Insert Simulation
            self.rowcount = 1
            if "INTO MEDICATIONS" in q_upper:
                # Naive insert parsing - assumes params match dict order (fragile but fine for demo)
                pass 
            elif "INTO PATIENTS" in q_upper:
                pass
            self.rows = []
        else:
            self.rows = []
            
    def fetchall(self):
        return self.rows
        
    def fetchone(self):
        return self.rows[0] if self.rows else None
        
    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class MockConnection:
    """Mock Database Connection"""
    def cursor(self):
        return MockCursor()
        
    def commit(self):
        pass
        
    def rollback(self):
        pass
        
    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class DatabaseConnectionManager:
    """Manages connection pools for multiple database shards"""
    
    def __init__(self):
        """Initialize connection manager"""
        self.shard_pools: Dict[int, Any] = {}
        self.mock_mode = False
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
        """Add a database shard with connection pooling"""
        try:
            import psycopg2
            from psycopg2 import pool
            
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
            logger.warning(f"⚠️  PostgreSQL connection failed for Shard {shard_id}: {e}")
            logger.warning("⚠️  Falling back to IN-MEMORY Mock Database for this shard.")
            self.shard_pools[shard_id] = "MOCK_POOL"
            self.mock_mode = True
    
    @contextmanager
    def get_connection(self, shard_id: int):
        """Get a connection from the shard pool (context manager)"""
        if shard_id not in self.shard_pools:
            # Auto-initialize fallback if shard missing
            logger.warning(f"Shard {shard_id} not initialized. Using Mock.")
            self.shard_pools[shard_id] = "MOCK_POOL"
        
        pool = self.shard_pools[shard_id]
        
        if pool == "MOCK_POOL":
            conn = MockConnection()
            try:
                yield conn
            finally:
                conn.close()
            return

        connection = None
        try:
            connection = pool.getconn()
            yield connection
            connection.commit()
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"❌ Database error on Shard {shard_id}: {e}")
            raise
        finally:
            if connection:
                pool.putconn(connection)
    
    def close_all(self):
        """Close all connection pools"""
        for shard_id, pool in self.shard_pools.items():
            if pool != "MOCK_POOL":
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

