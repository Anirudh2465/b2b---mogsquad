"""
Digital Twin Data Model
Represents a patient's longitudinal health state.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime
import uuid


@dataclass
class ChronicCondition:
    """Chronic health condition detected from medication patterns"""
    
    condition_name: str  # e.g., "DIABETES", "HYPERTENSION"
    first_detected: datetime
    confidence_score: float  # 0.0 to 1.0
    supporting_medications: List[str]
    prescription_count: int


@dataclass
class DigitalTwinState:
    """Patient's Health Digital Twin state"""
    
    twin_id: UUID
    patient_id: UUID
    
    # Chronic conditions
    chronic_conditions: List[ChronicCondition]
    
    # Adherence metrics
    overall_adherence_rate: float  # 0-100%
    consistency_index: float  # 0-100%
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    
    # Medication summary
    active_medications_count: int
    total_prescriptions: int
    
    # Last acute episode
    last_acute_episode: Optional[str]
    last_acute_date: Optional[datetime]
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def create(cls, patient_id: UUID):
        """Create new Digital Twin"""
        return cls(
            twin_id=uuid.uuid4(),
            patient_id=patient_id,
            chronic_conditions=[],
            overall_adherence_rate=0.0,
            consistency_index=0.0,
            risk_level="LOW",
            active_medications_count=0,
            total_prescriptions=0,
            last_acute_episode=None,
            last_acute_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def add_chronic_condition(self, condition: ChronicCondition):
        """Add or update chronic condition"""
        # Check if condition already exists
        for i, existing in enumerate(self.chronic_conditions):
            if existing.condition_name == condition.condition_name:
                self.chronic_conditions[i] = condition
                return
        
        self.chronic_conditions.append(condition)
        self.updated_at = datetime.now()
    
    def calculate_risk_level(self) -> str:
        """Determine risk level based on adherence"""
        if self.consistency_index < 70:
            return "HIGH"
        elif self.consistency_index < 85:
            return "MEDIUM"
        else:
            return "LOW"
