"""
Patient Data Model
Defines the schema for patient records with encrypted fields.
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
import uuid


@dataclass
class PatientRecord:
    """Patient record with encrypted sensitive data"""
    
    patient_id: UUID
    encrypted_name: bytes
    encrypted_history: bytes
    shard_id: int
    
    @classmethod
    def create(cls, patient_id: Optional[UUID] = None, shard_id: int = 0):
        """Create a new patient record with generated UUID if not provided"""
        if patient_id is None:
            patient_id = uuid.uuid4()
        
        return cls(
            patient_id=patient_id,
            encrypted_name=b'',
            encrypted_history=b'',
            shard_id=shard_id
        )


@dataclass
class PatientData:
    """Decrypted patient data for application use"""
    
    patient_id: UUID
    name: str
    medical_history: str
    shard_id: int
