"""
Digital Twin Service
Manages Health Digital Twin state, chronic condition detection, and adherence tracking.
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from uuid import UUID
import logging

from app.models.digital_twin import DigitalTwinState, ChronicCondition
from app.database.connection import get_db_manager
from app.database.router import get_shard_router

logger = logging.getLogger(__name__)

# Chronic drug pattern mappings
CHRONIC_DRUG_PATTERNS = {
    "DIABETES": ["metformin", "insulin", "glipizide", "sitagliptin", "gliclazide"],
    "HYPERTENSION": ["amlodipine", "telmisartan", "losartan", "atenolol", "ramipril"],
    "ASTHMA": ["salbutamol", "budesonide", "montelukast", "formoterol"],
    "THYROID": ["levothyroxine", "thyronorm", "eltroxin"],
    "CHOLESTEROL": ["atorvastatin", "rosuvastatin", "simvastatin"],
    "GERD": ["omeprazole", "pantoprazole", "esomeprazole", "rabeprazole"]
}


class DigitalTwinService:
    """Service for managing patient Digital Twins"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.shard_router = get_shard_router()
    
    def detect_chronic_conditions(self, patient_id: str, lookback_months: int = 3) -> List[ChronicCondition]:
        """
        Detect chronic conditions from medication history
        
        Rule: If a drug from chronic pattern appears in ≥3 prescriptions
              over the lookback period, tag as chronic condition
        
        Args:
            patient_id: Patient UUID
            lookback_months: Months to analyze (default: 3)
            
        Returns:
            List of detected chronic conditions
        """
        shard_id = self.shard_router.get_shard_id(patient_id)
        since_date = datetime.now() - timedelta(days=lookback_months * 30)
        
        with self.db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            
            # Get all medications in lookback period
            cursor.execute(
                """
                SELECT drug_name, created_at
                FROM medications
                WHERE patient_id = %s
                  AND created_at >= %s
                ORDER BY created_at ASC
                """,
                (patient_id, since_date)
            )
            
            medications = cursor.fetchall()
        
        # Count occurrences per condition
        condition_matches: Dict[str, List[tuple]] = {
            condition: [] for condition in CHRONIC_DRUG_PATTERNS.keys()
        }
        
        for drug_name, created_at in medications:
            drug_lower = drug_name.lower()
            
            # Check each chronic pattern
            for condition, drug_patterns in CHRONIC_DRUG_PATTERNS.items():
                if any(pattern in drug_lower for pattern in drug_patterns):
                    condition_matches[condition].append((drug_name, created_at))
        
        # Filter conditions with ≥3 occurrences
        chronic_conditions = []
        
        for condition, matches in condition_matches.items():
            if len(matches) >= 3:
                # Get unique drug names
                unique_drugs = list(set([drug for drug, _ in matches]))
                first_detected = min([date for _, date in matches])
                
                # Confidence based on number of occurrences
                confidence = min(len(matches) / 10.0, 1.0)
                
                chronic_conditions.append(ChronicCondition(
                    condition_name=condition,
                    first_detected=first_detected,
                    confidence_score=confidence,
                    supporting_medications=unique_drugs,
                    prescription_count=len(matches)
                ))
                
                logger.info(f"🔍 Detected chronic condition: {condition} (confidence: {confidence:.2f})")
        
        return chronic_conditions
    
    def calculate_consistency_index(self, patient_id: str, days: int = 30) -> float:
        """
        Calculate adherence consistency index
        
        Formula: (Total TAKEN / Total EXPECTED) * 100
        
        Args:
            patient_id: Patient UUID
            days: Period to analyze
            
        Returns:
            Consistency index (0-100%)
        """
        shard_id = self.shard_router.get_shard_id(patient_id)
        since_date = datetime.now() - timedelta(days=days)
        
        with self.db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            
            # Get all active medications
            cursor.execute(
                """
                SELECT medication_id, frequency_json
                FROM medications
                WHERE patient_id = %s
                  AND pills_remaining > 0
                  AND created_at <= %s
                """,
                (patient_id, datetime.now())
            )
            
            medications = cursor.fetchall()
            
            if not medications:
                return 100.0  # No medications = perfect adherence
            
            total_expected = 0
            total_taken = 0
            
            for med_id, freq_json in medications:
                # Calculate expected doses
                import json
                freq_data = json.loads(freq_json) if isinstance(freq_json, str) else freq_json
                count_per_day = freq_data.get('count_per_day', 1)
                total_expected += count_per_day * days
                
                # Count actual TAKEN events
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM adherence_events
                    WHERE medication_id = %s
                      AND event_type = 'TAKEN'
                      AND created_at >= %s
                    """,
                    (med_id, since_date)
                )
                
                taken_count = cursor.fetchone()[0]
                total_taken += taken_count
            
            consistency = (total_taken / total_expected * 100) if total_expected > 0 else 100.0
            
            logger.info(f"📊 Consistency Index: {consistency:.1f}% ({total_taken}/{total_expected})")
            return min(consistency, 100.0)
    
    def get_or_create_twin(self, patient_id: str) -> DigitalTwinState:
        """
        Get existing Digital Twin or create new one
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            DigitalTwinState
        """
        shard_id = self.shard_router.get_shard_id(patient_id)
        
        with self.db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            
            # Try to fetch existing twin (would be in a digital_twins table)
            # For now, create new one each time
            pass
        
        # Create new twin
        twin = DigitalTwinState.create(UUID(patient_id))
        
        # Detect chronic conditions
        twin.chronic_conditions = self.detect_chronic_conditions(patient_id)
        
        # Calculate consistency
        twin.consistency_index = self.calculate_consistency_index(patient_id)
        twin.risk_level = twin.calculate_risk_level()
        
        # Count active medications
        with self.db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) FROM medications WHERE patient_id = %s AND pills_remaining > 0",
                (patient_id,)
            )
            twin.active_medications_count = cursor.fetchone()[0]
            
            cursor.execute(
                "SELECT COUNT(*) FROM medications WHERE patient_id = %s",
                (patient_id,)
            )
            twin.total_prescriptions = cursor.fetchone()[0]
        
        logger.info(f"✅ Digital Twin created for patient {patient_id}")
        return twin


# Global service instance
digital_twin_service: Optional[DigitalTwinService] = None


def init_digital_twin_service() -> DigitalTwinService:
    """Initialize the global Digital Twin service"""
    global digital_twin_service
    digital_twin_service = DigitalTwinService()
    return digital_twin_service


def get_digital_twin_service() -> DigitalTwinService:
    """Get the global Digital Twin service instance"""
    if digital_twin_service is None:
        raise RuntimeError("Digital Twin service not initialized")
    return digital_twin_service
