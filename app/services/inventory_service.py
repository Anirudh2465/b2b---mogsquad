"""
Inventory Service
Manages medication inventory and adherence tracking.
"""
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime, timedelta
import logging

from app.models.medication import MedicationData
from app.models.adherence_event import AdherenceEvent
from app.database.connection import get_db_manager
from app.database.router import get_shard_router

logger = logging.getLogger(__name__)


class InventoryService:
    """Service for medication inventory management"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.shard_router = get_shard_router()
    
    def record_taken(self, 
                    medication_id: str,
                    patient_id: str,
                    scheduled_time: datetime,
                    pills_count: int = 1) -> bool:
        """
        Record that medication was taken
        
        Args:
            medication_id: Medication UUID
            patient_id: Patient UUID
            scheduled_time: When dose was scheduled
            pills_count: Number of pills taken
            
        Returns:
            True if successful
        """
        shard_id = self.shard_router.get_shard_id(patient_id)
        
        with self.db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            
            # Create adherence event
            event = AdherenceEvent.create_taken(
                medication_id=UUID(medication_id),
                scheduled_time=scheduled_time,
                pills_count=pills_count
            )
            
            # Insert event
            cursor.execute(
                """
                INSERT INTO adherence_events 
                (event_id, medication_id, event_type, pills_count, scheduled_time, actual_time, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (str(event.event_id), medication_id, event.event_type, 
                 event.pills_count, event.scheduled_time, event.actual_time, event.created_at)
            )
            
            # Update medication inventory
            cursor.execute(
                """
                UPDATE medications
                SET pills_remaining = pills_remaining - %s,
                    last_taken_at = %s
                WHERE medication_id = %s
                RETURNING pills_remaining
                """,
                (pills_count, datetime.now(), medication_id)
            )
            
            result = cursor.fetchone()
            remaining = result[0] if result else 0
            
            logger.info(f"✅ Recorded TAKEN event for {medication_id}. Remaining: {remaining} pills")
            return True
    
    def record_missed(self,
                     medication_id: str,
                     patient_id: str,
                     scheduled_time: datetime) -> bool:
        """
        Record that medication dose was missed
        
        Note: Does NOT decrement pills_remaining
        
        Args:
            medication_id: Medication UUID
            patient_id: Patient UUID
            scheduled_time: When dose was scheduled
            
        Returns:
            True if successful
        """
        shard_id = self.shard_router.get_shard_id(patient_id)
        
        with self.db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            
            event = AdherenceEvent.create_missed(
                medication_id=UUID(medication_id),
                scheduled_time=scheduled_time
            )
            
            cursor.execute(
                """
                INSERT INTO adherence_events 
                (event_id, medication_id, event_type, pills_count, scheduled_time, actual_time, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (str(event.event_id), medication_id, event.event_type,
                 event.pills_count, event.scheduled_time, event.actual_time, event.created_at)
            )
            
            logger.warning(f"⚠️  Recorded MISSED event for {medication_id}")
            return True
    
    def record_wastage(self,
                      medication_id: str,
                      patient_id: str,
                      pills_count: int) -> bool:
        """
        Record medication wastage (e.g., dropped pills)
        
        Args:
            medication_id: Medication UUID
            patient_id: Patient UUID
            pills_count: Number of pills wasted
            
        Returns:
            True if successful
        """
        shard_id = self.shard_router.get_shard_id(patient_id)
        
        with self.db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            
            event = AdherenceEvent.create_wastage(
                medication_id=UUID(medication_id),
                pills_count=pills_count
            )
            
            cursor.execute(
                """
                INSERT INTO adherence_events 
                (event_id, medication_id, event_type, pills_count, scheduled_time, actual_time, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (str(event.event_id), medication_id, event.event_type,
                 event.pills_count, event.scheduled_time, event.actual_time, event.created_at)
            )
            
            # Decrement inventory
            cursor.execute(
                """
                UPDATE medications
                SET pills_remaining = pills_remaining - %s
                WHERE medication_id = %s
                """,
                (pills_count, medication_id)
            )
            
            logger.warning(f"⚠️  Recorded WASTAGE of {pills_count} pills for {medication_id}")
            return True
    
    def record_refill(self,
                     medication_id: str,
                     patient_id: str,
                     pills_count: int) -> bool:
        """
        Record medication refill
        
        Args:
            medication_id: Medication UUID
            patient_id: Patient UUID
            pills_count: Number of pills added
            
        Returns:
            True if successful
        """
        shard_id = self.shard_router.get_shard_id(patient_id)
        
        with self.db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            
            event = AdherenceEvent.create_refill(
                medication_id=UUID(medication_id),
                pills_count=pills_count
            )
            
            cursor.execute(
                """
                INSERT INTO adherence_events 
                (event_id, medication_id, event_type, pills_count, scheduled_time, actual_time, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (str(event.event_id), medication_id, event.event_type,
                 event.pills_count, event.scheduled_time, event.actual_time, event.created_at)
            )
            
            # Increment inventory
            cursor.execute(
                """
                UPDATE medications
                SET pills_remaining = pills_remaining + %s
                WHERE medication_id = %s
                RETURNING pills_remaining
                """,
                (pills_count, medication_id)
            )
            
            result = cursor.fetchone()
            remaining = result[0] if result else 0
            
            logger.info(f"✅ Recorded REFILL of {pills_count} pills. New total: {remaining}")
            return True
    
    def get_medications_needing_refill(self, patient_id: str) -> List[Dict]:
        """
        Get all medications that need refill
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            List of medication dictionaries
        """
        shard_id = self.shard_router.get_shard_id(patient_id)
        
        with self.db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT medication_id, drug_name, strength, pills_remaining, 
                       refill_threshold, pharmacy_name, pharmacy_phone
                FROM medications
                WHERE patient_id = %s 
                  AND pills_remaining <= refill_threshold
                  AND pills_remaining > 0
                ORDER BY pills_remaining ASC
                """,
                (patient_id,)
            )
            
            results = cursor.fetchall()
            
            medications = []
            for row in results:
                medications.append({
                    "medication_id": str(row[0]),
                    "drug_name": row[1],
                    "strength": row[2],
                    "pills_remaining": row[3],
                    "refill_threshold": row[4],
                    "pharmacy_name": row[5],
                    "pharmacy_phone": row[6]
                })
            
            logger.info(f"🔔 Found {len(medications)} medications needing refill")
            return medications
    
    def get_adherence_rate(self, medication_id: str, patient_id: str, days: int = 7) -> float:
        """
        Calculate adherence rate for a medication
        
        Args:
            medication_id: Medication UUID
            patient_id: Patient UUID
            days: Number of days to calculate (default: 7)
            
        Returns:
            Adherence rate as percentage (0-100)
        """
        shard_id = self.shard_router.get_shard_id(patient_id)
        
        with self.db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            
            since_date = datetime.now() - timedelta(days=days)
            
            # Get expected doses per day
            cursor.execute(
                """
                SELECT frequency_json->>'count_per_day'
                FROM medications
                WHERE medication_id = %s
                """,
                (medication_id,)
            )
            result = cursor.fetchone()
            if not result:
                return 0.0
            
            expected_per_day = int(result[0])
            total_expected = expected_per_day * days
            
            # Count taken doses
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM adherence_events
                WHERE medication_id = %s
                  AND event_type = 'TAKEN'
                  AND created_at >= %s
                """,
                (medication_id, since_date)
            )
            
            taken_count = cursor.fetchone()[0]
            
            adherence_rate = (taken_count / total_expected * 100) if total_expected > 0 else 0
            
            logger.info(f"📊 Adherence rate: {adherence_rate:.1f}% ({taken_count}/{total_expected})")
            return adherence_rate
