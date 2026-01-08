"""
Medication Data Model
"""
from dataclasses import dataclass
from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime
import uuid


@dataclass
class MedicationData:
    """Medication record with inventory tracking"""
    
    medication_id: UUID
    patient_id: UUID
    prescription_id: UUID
    
    # Drug information
    drug_name: str
    strength: str  # e.g., "500mg"
    
    # Frequency
    frequency: str  # Raw text (e.g., "BID", "1-0-1")
    frequency_json: Dict  # Parsed schedule
    
    # Duration and inventory
    duration_days: int
    total_pills: int
    pills_remaining: int
    
    # Tracking
    last_taken_at: Optional[datetime]
    refill_threshold: int
    
    # Pharmacy
    pharmacy_name: Optional[str]
    pharmacy_phone: Optional[str]
    
    created_at: datetime
    
    @classmethod
    def create(cls,
               patient_id: UUID,
               prescription_id: UUID,
               drug_name: str,
               strength: str,
               frequency: str,
               frequency_json: Dict,
               duration_days: int,
               total_pills: int,
               pharmacy_name: Optional[str] = None,
               pharmacy_phone: Optional[str] = None):
        """Create new medication record"""
        return cls(
            medication_id=uuid.uuid4(),
            patient_id=patient_id,
            prescription_id=prescription_id,
            drug_name=drug_name,
            strength=strength,
            frequency=frequency,
            frequency_json=frequency_json,
            duration_days=duration_days,
            total_pills=total_pills,
            pills_remaining=total_pills,
            last_taken_at=None,
            refill_threshold=5,
            pharmacy_name=pharmacy_name,
            pharmacy_phone=pharmacy_phone,
            created_at=datetime.now()
        )
    
    def needs_refill(self) -> bool:
        """Check if medication needs refill"""
        return self.pills_remaining <= self.refill_threshold
    
    def is_active(self) -> bool:
        """Check if medication is still active"""
        return self.pills_remaining > 0
