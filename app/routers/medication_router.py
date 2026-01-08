"""
Medication API Router
Endpoints for medication management and adherence tracking.
"""
from flask import Blueprint, request, jsonify
import logging
from datetime import datetime

from app.services.inventory_service import InventoryService
from app.services.notification_service import get_notification_service
from app.database.connection import get_db_manager
from app.database.router import get_shard_router

logger = logging.getLogger(__name__)

medication_bp = Blueprint('medications', __name__, url_prefix='/api/medications')

# Initialize service
inventory_service = None


def init_medication_router(service: InventoryService):
    """Initialize with inventory service"""
    global inventory_service
    inventory_service = service


@medication_bp.route('/', methods=['GET'])
def list_medications():
    """
    List all active medications for a patient
    
    Query Params:
        patient_id: Required
    """
    try:
        patient_id = request.args.get('patient_id')
        if not patient_id:
            return jsonify({"error": "patient_id required"}), 400
        
        shard_router = get_shard_router()
        db_manager = get_db_manager()
        
        shard_id = shard_router.get_shard_id(patient_id)
        
        with db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT medication_id, drug_name, strength, frequency, 
                       pills_remaining, total_pills, frequency_json
                FROM medications
                WHERE patient_id = %s AND pills_remaining > 0
                ORDER BY created_at DESC
                """,
                (patient_id,)
            )
            
            medications = []
            for row in cursor.fetchall():
                medications.append({
                    "medication_id": str(row[0]),
                    "drug_name": row[1],
                    "strength": row[2],
                    "frequency": row[3],
                    "pills_remaining": row[4],
                    "total_pills": row[5],
                    "schedule": row[6]
                })
            
            return jsonify({"medications": medications}), 200
            
    except Exception as e:
        logger.error(f"❌ Error listing medications: {e}")
        return jsonify({"error": "Internal server error"}), 500


@medication_bp.route('/<medication_id>/taken', methods=['POST'])
def mark_taken(medication_id: str):
    """
    Mark medication as taken
    
    Request Body:
        {
            "patient_id": "...",
            "scheduled_time": "2026-01-08T09:00:00",
            "pills_count": 1
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'patient_id' not in data:
            return jsonify({"error": "patient_id required"}), 400
        
        patient_id = data['patient_id']
        scheduled_time_str = data.get('scheduled_time')
        pills_count = data.get('pills_count', 1)
        
        # Parse datetime
        if scheduled_time_str:
            scheduled_time = datetime.fromisoformat(scheduled_time_str)
        else:
            scheduled_time = datetime.now()
        
        # Record event
        success = inventory_service.record_taken(
            medication_id=medication_id,
            patient_id=patient_id,
            scheduled_time=scheduled_time,
            pills_count=pills_count
        )
        
        if success:
            return jsonify({"message": "Marked as taken"}), 200
        else:
            return jsonify({"error": "Failed to record"}), 500
            
    except Exception as e:
        logger.error(f"❌ Error marking taken: {e}")
        return jsonify({"error": "Internal server error"}), 500


@medication_bp.route('/<medication_id>/missed', methods=['POST'])
def mark_missed(medication_id: str):
    """
    Mark medication dose as missed
    
    Request Body:
        {
            "patient_id": "...",
            "scheduled_time": "2026-01-08T09:00:00"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'patient_id' not in data:
            return jsonify({"error": "patient_id required"}), 400
        
        patient_id = data['patient_id']
        scheduled_time_str = data.get('scheduled_time')
        
        if scheduled_time_str:
            scheduled_time = datetime.fromisoformat(scheduled_time_str)
        else:
            scheduled_time = datetime.now()
        
        success = inventory_service.record_missed(
            medication_id=medication_id,
            patient_id=patient_id,
            scheduled_time=scheduled_time
        )
        
        if success:
            return jsonify({"message": "Marked as missed"}), 200
        else:
            return jsonify({"error": "Failed to record"}), 500
            
    except Exception as e:
        logger.error(f"❌ Error marking missed: {e}")
        return jsonify({"error": "Internal server error"}), 500


@medication_bp.route('/<medication_id>/wastage', methods=['POST'])
def record_wastage_endpoint(medication_id: str):
    """
    Record medication wastage
    
    Request Body:
        {
            "patient_id": "...",
            "pills_count": 2
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'patient_id' not in data or 'pills_count' not in data:
            return jsonify({"error": "patient_id and pills_count required"}), 400
        
        success = inventory_service.record_wastage(
            medication_id=medication_id,
            patient_id=data['patient_id'],
            pills_count=data['pills_count']
        )
        
        if success:
            return jsonify({"message": "Wastage recorded"}), 200
        else:
            return jsonify({"error": "Failed to record"}), 500
            
    except Exception as e:
        logger.error(f"❌ Error recording wastage: {e}")
        return jsonify({"error": "Internal server error"}), 500


@medication_bp.route('/<medication_id>/refill', methods=['POST'])
def refill_medication(medication_id: str):
    """
    Record medication refill
    
    Request Body:
        {
            "patient_id": "...",
            "pills_count": 30
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'patient_id' not in data or 'pills_count' not in data:
            return jsonify({"error": "patient_id and pills_count required"}), 400
        
        success = inventory_service.record_refill(
            medication_id=medication_id,
            patient_id=data['patient_id'],
            pills_count=data['pills_count']
        )
        
        if success:
            return jsonify({"message": "Refill recorded"}), 200
        else:
            return jsonify({"error": "Failed to record"}), 500
            
    except Exception as e:
        logger.error(f"❌ Error recording refill: {e}")
        return jsonify({"error": "Internal server error"}), 500


@medication_bp.route('/refill-alerts', methods=['GET'])
def get_refill_alerts():
    """
    Get medications needing refill
    
    Query Params:
        patient_id: Required
    """
    try:
        patient_id = request.args.get('patient_id')
        if not patient_id:
            return jsonify({"error": "patient_id required"}), 400
        
        medications = inventory_service.get_medications_needing_refill(patient_id)
        
        # Generate WhatsApp links
        notification_service = get_notification_service()
        
        for med in medications:
            refill_data = notification_service.generate_refill_notification(med)
            med['whatsapp_url'] = refill_data.get('whatsapp_url')
            med['pills_needed'] = refill_data.get('pills_needed')
        
        return jsonify({
            "count": len(medications),
            "medications": medications
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting refill alerts: {e}")
        return jsonify({"error": "Internal server error"}), 500


@medication_bp.route('/<medication_id>/adherence', methods=['GET'])
def get_adherence_rate_endpoint(medication_id: str):
    """
    Get adherence rate for medication
    
    Query Params:
        patient_id: Required
        days: Optional (default: 7)
    """
    try:
        patient_id = request.args.get('patient_id')
        if not patient_id:
            return jsonify({"error": "patient_id required"}), 400
        
        days = int(request.args.get('days', 7))
        
        adherence_rate = inventory_service.get_adherence_rate(
            medication_id=medication_id,
            patient_id=patient_id,
            days=days
        )
        
        return jsonify({
            "medication_id": medication_id,
            "adherence_rate": adherence_rate,
            "days": days
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting adherence rate: {e}")
        return jsonify({"error": "Internal server error"}), 500
