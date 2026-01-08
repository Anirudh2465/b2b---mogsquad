"""
Adherence Event Data Model
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from datetime import datetime
import uuid


@dataclass
class AdherenceEvent:
    """Event tracking medication adherence"""
    
    event_id: UUID
    medication_id: UUID
    event_type: str  # 'TAKEN', 'MISSED', 'WASTAGE', 'REFILL'
    pills_count: int
    scheduled_time: Optional[datetime]
    actual_time: datetime
    created_at: datetime
    
    @classmethod
    def create_taken(cls,
                    medication_id: UUID,
                    scheduled_time: datetime,
                    pills_count: int = 1):
        """Create a 'taken' event"""
        return cls(
            event_id=uuid.uuid4(),
            medication_id=medication_id,
            event_type='TAKEN',
            pills_count=pills_count,
            scheduled_time=scheduled_time,
            actual_time=datetime.now(),
            created_at=datetime.now()
        )
    
    @classmethod
    def create_missed(cls,
                     medication_id: UUID,
                     scheduled_time: datetime):
        """Create a 'missed' event"""
        return cls(
            event_id=uuid.uuid4(),
            medication_id=medication_id,
            event_type='MISSED',
            pills_count=0,
            scheduled_time=scheduled_time,
            actual_time=datetime.now(),
            created_at=datetime.now()
        )
    
    @classmethod
    def create_wastage(cls,
                      medication_id: UUID,
                      pills_count: int):
        """Create a 'wastage' event"""
        return cls(
            event_id=uuid.uuid4(),
            medication_id=medication_id,
            event_type='WASTAGE',
            pills_count=pills_count,
            scheduled_time=None,
            actual_time=datetime.now(),
            created_at=datetime.now()
        )
    
    @classmethod
    def create_refill(cls,
                     medication_id: UUID,
                     pills_count: int):
        """Create a 'refill' event"""
        return cls(
            event_id=uuid.uuid4(),
            medication_id=medication_id,
            event_type='REFILL',
            pills_count=pills_count,
            scheduled_time=None,
            actual_time=datetime.now(),
            created_at=datetime.now()
        )
