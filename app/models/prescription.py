"""
Prescription Data Model
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from uuid import UUID
import uuid


@dataclass
class PrescriptionData:
    """Prescription with OCR extracted data"""
    
    prescription_id: UUID
    patient_id: UUID
    prescription_image: bytes  # Encrypted
    extracted_data: Dict[str, Any]  # Structured OCR output
    
    @classmethod
    def create(cls, patient_id: UUID, image: bytes):
        """Create new prescription"""
        return cls(
            prescription_id=uuid.uuid4(),
            patient_id=patient_id,
            prescription_image=image,
            extracted_data={}
        )


@dataclass
class ExtractedPrescriptionData:
    """Structured data extracted from prescription OCR"""
    
    # Pharmacy information
    pharmacy_name: Optional[str] = None
    pharmacy_phone: Optional[str] = None
    pharmacy_address: Optional[str] = None
    
    # Doctor information
    doctor_name: Optional[str] = None
    doctor_registration: Optional[str] = None
    
    # Prescription details
    prescription_date: Optional[str] = None
    
    # Medications (list of dicts)
    medications: list = None
    
    def __post_init__(self):
        if self.medications is None:
            self.medications = []
