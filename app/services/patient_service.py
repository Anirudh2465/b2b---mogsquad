"""
Patient Service Layer
Business logic for patient record CRUD operations with encryption and sharding.
"""
from typing import Optional, List
from uuid import UUID
import logging

from app.models.patient import PatientRecord, PatientData
from app.core.security import get_encryption_manager
from app.database.router import get_shard_router
from app.database.connection import get_db_manager

logger = logging.getLogger(__name__)


class PatientService:
    """Service layer for patient operations"""
    
    def __init__(self):
        self.encryption = get_encryption_manager()
        self.shard_router = get_shard_router()
        self.db_manager = get_db_manager()
    
    def create_patient(self, name: str, medical_history: str) -> PatientData:
        """
        Create a new patient record with encrypted data
        
        Args:
            name: Patient's name (will be encrypted)
            medical_history: Medical history (will be encrypted)
            
        Returns:
            PatientData with decrypted information
        """
        # Generate new patient ID
        patient_id = UUID(int=0).hex  # Temporary, will use uuid4
        import uuid
        patient_id = str(uuid.uuid4())
        
        # Determine shard
        shard_id = self.shard_router.get_shard_id(patient_id)
        
        # Encrypt sensitive data
        encrypted_name = self.encryption.encrypt(name, patient_id)
        encrypted_history = self.encryption.encrypt(medical_history, patient_id)
        
        # Insert into appropriate shard
        with self.db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO patient_records (patient_id, encrypted_name, encrypted_history, shard_id)
                VALUES (%s, %s, %s, %s)
                """,
                (patient_id, encrypted_name, encrypted_history, shard_id)
            )
        
        logger.info(f"✅ Created patient {patient_id} in Shard {shard_id}")
        
        return PatientData(
            patient_id=UUID(patient_id),
            name=name,
            medical_history=medical_history,
            shard_id=shard_id
        )
    
    def get_patient(self, patient_id: str) -> Optional[PatientData]:
        """
        Retrieve and decrypt patient data
        
        Args:
            patient_id: Patient UUID as string
            
        Returns:
            PatientData if found, None otherwise
        """
        # Determine which shard to query
        shard_id = self.shard_router.get_shard_id(patient_id)
        
        # Query the shard
        with self.db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT patient_id, encrypted_name, encrypted_history, shard_id
                FROM patient_records
                WHERE patient_id = %s
                """,
                (patient_id,)
            )
            
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"⚠️  Patient {patient_id} not found in Shard {shard_id}")
                return None
            
            # Verify shard consistency
            stored_shard_id = row[3]
            if not self.shard_router.validate_shard_consistency(patient_id, stored_shard_id):
                raise ValueError(f"Data integrity error: patient in wrong shard")
            
            # Decrypt sensitive data
            decrypted_name = self.encryption.decrypt(row[1], patient_id)
            decrypted_history = self.encryption.decrypt(row[2], patient_id)
            
            return PatientData(
                patient_id=UUID(row[0]),
                name=decrypted_name,
                medical_history=decrypted_history,
                shard_id=stored_shard_id
            )
    
    def update_patient(self, patient_id: str, name: Optional[str] = None, 
                      medical_history: Optional[str] = None) -> bool:
        """
        Update patient information
        
        Args:
            patient_id: Patient UUID
            name: New name (optional)
            medical_history: New medical history (optional)
            
        Returns:
            True if updated successfully
        """
        shard_id = self.shard_router.get_shard_id(patient_id)
        
        updates = []
        params = []
        
        if name is not None:
            encrypted_name = self.encryption.encrypt(name, patient_id)
            updates.append("encrypted_name = %s")
            params.append(encrypted_name)
        
        if medical_history is not None:
            encrypted_history = self.encryption.encrypt(medical_history, patient_id)
            updates.append("encrypted_history = %s")
            params.append(encrypted_history)
        
        if not updates:
            return False
        
        params.append(patient_id)
        
        with self.db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            query = f"UPDATE patient_records SET {', '.join(updates)} WHERE patient_id = %s"
            cursor.execute(query, params)
            
            logger.info(f"✅ Updated patient {patient_id} in Shard {shard_id}")
            return cursor.rowcount > 0
