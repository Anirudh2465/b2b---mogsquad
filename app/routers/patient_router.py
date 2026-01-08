"""
Patient API Router
REST endpoints for patient management with rate limiting.
"""
from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

from app.services.patient_service import PatientService

logger = logging.getLogger(__name__)

# Create blueprint
patient_bp = Blueprint('patients', __name__, url_prefix='/api/patients')

# Initialize service
patient_service = None


def init_patient_router(service: PatientService):
    """Initialize the patient router with service dependency"""
    global patient_service
    patient_service = service


@patient_bp.route('/', methods=['POST'])
def create_patient():
    """
    Create a new patient
    
    Request Body:
        {
            "name": "John Doe",
            "medical_history": "No known allergies. Previous surgery in 2020."
        }
    
    Response:
        {
            "patient_id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "John Doe",
            "medical_history": "...",
            "shard_id": 0
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'medical_history' not in data:
            return jsonify({"error": "Missing required fields: name, medical_history"}), 400
        
        patient = patient_service.create_patient(
            name=data['name'],
            medical_history=data['medical_history']
        )
        
        return jsonify({
            "patient_id": str(patient.patient_id),
            "name": patient.name,
            "medical_history": patient.medical_history,
            "shard_id": patient.shard_id
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error creating patient: {e}")
        return jsonify({"error": "Internal server error"}), 500


@patient_bp.route('/<patient_id>', methods=['GET'])
def get_patient(patient_id: str):
    """
    Retrieve patient information
    
    Response:
        {
            "patient_id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "John Doe",
            "medical_history": "...",
            "shard_id": 0
        }
    """
    try:
        patient = patient_service.get_patient(patient_id)
        
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        
        return jsonify({
            "patient_id": str(patient.patient_id),
            "name": patient.name,
            "medical_history": patient.medical_history,
            "shard_id": patient.shard_id
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error retrieving patient: {e}")
        return jsonify({"error": "Internal server error"}), 500


@patient_bp.route('/<patient_id>', methods=['PUT'])
def update_patient(patient_id: str):
    """
    Update patient information
    
    Request Body:
        {
            "name": "Jane Doe",  // optional
            "medical_history": "Updated history"  // optional
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        success = patient_service.update_patient(
            patient_id=patient_id,
            name=data.get('name'),
            medical_history=data.get('medical_history')
        )
        
        if not success:
            return jsonify({"error": "Patient not found or no updates made"}), 404
        
        return jsonify({"message": "Patient updated successfully"}), 200
        
    except Exception as e:
        logger.error(f"❌ Error updating patient: {e}")
        return jsonify({"error": "Internal server error"}), 500


@patient_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint (not rate limited)"""
    return jsonify({"status": "ok"}), 200
