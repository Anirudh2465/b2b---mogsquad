"""
Prescription API Router
Endpoints for uploading prescriptions and running OCR.
"""
from flask import Blueprint, request, jsonify
import logging
from uuid import UUID
import base64

from app.services.ocr_service import get_ocr_service
from app.services.semantic_parser import get_semantic_parser
from app.core.security import get_encryption_manager
from app.database.connection import get_db_manager
from app.database.router import get_shard_router

logger = logging.getLogger(__name__)

prescription_bp = Blueprint('prescriptions', __name__, url_prefix='/api/prescriptions')


@prescription_bp.route('/upload', methods=['POST'])
def upload_prescription():
    """
    Upload prescription image and run OCR
    
    Request Body:
        {
            "patient_id": "550e8400-e29b-41d4-a716-446655440000",
            "image": "<base64-encoded-image>"
        }
    
    Response:
        {
            "prescription_id": "...",
            "extracted_data": {
                "pharmacy_name": "...",
                "medications": [...]
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'patient_id' not in data or 'image' not in data:
            return jsonify({"error": "Missing patient_id or image"}), 400
        
        patient_id = data['patient_id']
        image_base64 = data['image']
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            return jsonify({"error": "Invalid base64 image"}), 400
        
        # Run OCR
        ocr_service = get_ocr_service()
        text = ocr_service.extract_text(image_bytes)
        extracted_data = ocr_service.extract_structured_data(text)
        
        # Encrypt and store prescription
        encryption = get_encryption_manager()
        shard_router = get_shard_router()
        db_manager = get_db_manager()
        
        shard_id = shard_router.get_shard_id(patient_id)
        
        # Encrypt image
        encrypted_image = encryption.encrypt(image_base64, patient_id)
        
        # Store prescription
        import uuid
        prescription_id = str(uuid.uuid4())
        
        with db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO prescriptions (prescription_id, patient_id, prescription_image, extracted_data)
                VALUES (%s, %s, %s, %s)
                """,
                (prescription_id, patient_id, encrypted_image, str(extracted_data))
            )
        
        logger.info(f"✅ Uploaded prescription {prescription_id}")
        
        return jsonify({
            "prescription_id": prescription_id,
            "extracted_data": extracted_data,
            "raw_text": text[:500]  # First 500 chars
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error uploading prescription: {e}")
        return jsonify({"error": "Internal server error"}), 500


@prescription_bp.route('/<prescription_id>', methods=['GET'])
def get_prescription(prescription_id: str):
    """
    Retrieve prescription by ID
    
    Query Params:
        patient_id: Required for shard routing
    """
    try:
        patient_id = request.args.get('patient_id')
        if not patient_id:
            return jsonify({"error": "patient_id query param required"}), 400
        
        shard_router = get_shard_router()
        db_manager = get_db_manager()
        
        shard_id = shard_router.get_shard_id(patient_id)
        
        with db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT prescription_id, extracted_data, created_at
                FROM prescriptions
                WHERE prescription_id = %s AND patient_id = %s
                """,
                (prescription_id, patient_id)
            )
            
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Prescription not found"}), 404
            
            return jsonify({
                "prescription_id": str(row[0]),
                "extracted_data": row[1],
                "created_at": row[2].isoformat()
            }), 200
            
    except Exception as e:
        logger.error(f"❌ Error retrieving prescription: {e}")
        return jsonify({"error": "Internal server error"}), 500


@prescription_bp.route('/<prescription_id>/confirm', methods=['POST'])
def confirm_prescription(prescription_id: str):
    """
    Confirm OCR results and create medication records
    
    Request Body:
        {
            "patient_id": "...",
            "medications": [
                {
                    "drug_name": "Paracetamol",
                    "strength": "500mg",
                    "frequency": "BID",
                    "duration_days": 10,
                    "dosage_per_intake": 1
                }
            ],
            "pharmacy_name": "ABC Pharmacy",
            "pharmacy_phone": "9876543210"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'patient_id' not in data or 'medications' not in data:
            return jsonify({"error": "Missing required fields"}), 400
        
        patient_id = data['patient_id']
        medications = data['medications']
        pharmacy_name = data.get('pharmacy_name')
        pharmacy_phone = data.get('pharmacy_phone')
        
        semantic_parser = get_semantic_parser()
        shard_router = get_shard_router()
        db_manager = get_db_manager()
        
        shard_id = shard_router.get_shard_id(patient_id)
        created_medications = []
        
        with db_manager.get_connection(shard_id) as conn:
            cursor = conn.cursor()
            
            for med in medications:
                # Parse frequency
                frequency_schedule = semantic_parser.parse_frequency(med['frequency'])
                if not frequency_schedule:
                    continue
                
                # Calculate total pills
                total_pills = semantic_parser.calculate_total_inventory(
                    dosage_per_intake=med.get('dosage_per_intake', 1),
                    frequency=frequency_schedule,
                    duration_days=med['duration_days']
                )
                
                # Create medication record
                import uuid as uuid_lib
                medication_id = str(uuid_lib.uuid4())
                
                frequency_json = {
                    "count_per_day": frequency_schedule.count_per_day,
                    "times": frequency_schedule.times,
                    "abbreviation": frequency_schedule.abbreviation
                }
                
                cursor.execute(
                    """
                    INSERT INTO medications 
                    (medication_id, patient_id, prescription_id, drug_name, strength, 
                     frequency, frequency_json, duration_days, total_pills, pills_remaining,
                     pharmacy_name, pharmacy_phone)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (medication_id, patient_id, prescription_id, med['drug_name'], med['strength'],
                     med['frequency'], str(frequency_json), med['duration_days'], 
                     total_pills, total_pills, pharmacy_name, pharmacy_phone)
                )
                
                created_medications.append({
                    "medication_id": medication_id,
                    "drug_name": med['drug_name'],
                    "total_pills": total_pills
                })
        
        logger.info(f"✅ Created {len(created_medications)} medication records")
        
        return jsonify({
            "message": "Medications created successfully",
            "medications": created_medications
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error confirming prescription: {e}")
        return jsonify({"error": "Internal server error"}), 500
