"""
Digital Twin API Router
Endpoints for Health Digital Twin and clinical summaries.
"""
from flask import Blueprint, request, jsonify
import logging

from app.services.digital_twin_service import get_digital_twin_service
from app.services.clinical_summary_service import get_clinical_summary_service
from app.database.connection import get_db_manager
from app.database.router import get_shard_router

logger = logging.getLogger(__name__)

twin_bp = Blueprint('digital_twin', __name__, url_prefix='/api/twin')


@twin_bp.route('/<patient_id>', methods=['GET'])
def get_digital_twin(patient_id: str):
    """
    Get patient's Digital Twin state
    
    Response:
        {
            "twin_id": "...",
            "patient_id": "...",
            "chronic_conditions": [...],
            "consistency_index": 85.5,
            "risk_level": "LOW",
            "active_medications_count": 3
        }
    """
    try:
        twin_service = get_digital_twin_service()
        twin = twin_service.get_or_create_twin(patient_id)
        
        # Convert to dict
        conditions = [{
            "condition_name": c.condition_name,
            "first_detected": c.first_detected.isoformat(),
            "confidence_score": c.confidence_score,
            "supporting_medications": c.supporting_medications,
            "prescription_count": c.prescription_count
        } for c in twin.chronic_conditions]
        
        return jsonify({
            "twin_id": str(twin.twin_id),
            "patient_id": str(twin.patient_id),
            "chronic_conditions": conditions,
            "overall_adherence_rate": twin.overall_adherence_rate,
            "consistency_index": twin.consistency_index,
            "risk_level": twin.risk_level,
            "active_medications_count": twin.active_medications_count,
            "total_prescriptions": twin.total_prescriptions,
            "last_acute_episode": twin.last_acute_episode,
            "created_at": twin.created_at.isoformat(),
            "updated_at": twin.updated_at.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error fetching Digital Twin: {e}")
        return jsonify({"error": "Internal server error"}), 500


@twin_bp.route('/<patient_id>/summary', methods=['GET'])
def get_clinical_summary(patient_id: str):
    """
    Get LLM-generated clinical summary
    
    Query Params:
        max_words: Maximum summary length (default: 150)
    
    Response:
        {
            "patient_id": "...",
            "summary": "Patient has a 24-month history...",
            "generated_at": "2026-01-08T18:25:00"
        }
    """
    try:
        from datetime import datetime
        
        max_words = int(request.args.get('max_words', 150))
        
        # Get Digital Twin
        twin_service = get_digital_twin_service()
        twin = twin_service.get_or_create_twin(patient_id)
        
        # Get medication history
        shard_router = get_shard_router()
        db_manager = get_db_manager()
        shard_id = shard_router.get_shard_id(patient_id)
        
        with db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT drug_name, strength, frequency, created_at
                FROM medications
                WHERE patient_id = %s
                ORDER BY created_at DESC
                LIMIT 12
                """,
                (patient_id,)
            )
            
            med_history = []
            for row in cursor.fetchall():
                med_history.append({
                    "drug_name": row[0],
                    "strength": row[1],
                    "frequency": row[2],
                    "created_at": row[3].isoformat()
                })
        
        # Generate summary
        summary_service = get_clinical_summary_service()
        summary = summary_service.generate_summary(twin, med_history, max_words)
        
        return jsonify({
            "patient_id": patient_id,
            "summary": summary,
            "generated_at": datetime.now().isoformat(),
            "word_count": len(summary.split())
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error generating summary: {e}")
        return jsonify({"error": "Internal server error"}), 500


@twin_bp.route('/<patient_id>/chronic-conditions', methods=['GET'])
def get_chronic_conditions(patient_id: str):
    """
    Get detected chronic conditions
    
    Query Params:
        lookback_months: Months to analyze (default: 3)
    """
    try:
        lookback_months = int(request.args.get('lookback_months', 3))
        
        twin_service = get_digital_twin_service()
        conditions = twin_service.detect_chronic_conditions(patient_id, lookback_months)
        
        return jsonify({
            "patient_id": patient_id,
            "chronic_conditions": [{
                "condition_name": c.condition_name,
                "first_detected": c.first_detected.isoformat(),
                "confidence_score": c.confidence_score,
                "supporting_medications": c.supporting_medications,
                "prescription_count": c.prescription_count
            } for c in conditions],
            "count": len(conditions)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error detecting chronic conditions: {e}")
        return jsonify({"error": "Internal server error"}), 500
