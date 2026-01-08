"""
Hospital Discovery API Router
Endpoints for geo-spatial hospital search and calling.
"""
from flask import Blueprint, request, jsonify
import logging

from app.services.maps_service import get_maps_service
from app.services.scraper_service import get_scraper_service
from app.services.voice_service import get_voice_service

logger = logging.getLogger(__name__)

hospital_bp = Blueprint('hospitals', __name__, url_prefix='/api/hospitals')


@hospital_bp.route('/search', methods=['GET'])
def search_hospitals():
    """
    Search for nearby hospitals
    
    Query Params:
        latitude: User's latitude (required)
        longitude: User's longitude (required)
        radius: Search radius in meters (default: 10000)
        patient_id: For smart ranking (optional)
    
    Response:
        {
            "hospitals": [...],
            "count": 3
        }
    """
    try:
        latitude = float(request.args.get('latitude'))
        longitude = float(request.args.get('longitude'))
        radius = int(request.args.get('radius', 10000))
        patient_id = request.args.get('patient_id')
        
        maps_service = get_maps_service()
        
        # Search nearby hospitals
        hospitals = maps_service.search_nearby_hospitals(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius
        )
        
        # Smart ranking if patient_id provided
        if patient_id:
            # TODO: Get visited place_ids from database
            visited_place_ids = []  # Mock for now
            hospitals = maps_service.rank_hospitals(hospitals, visited_place_ids)
        
        # Convert to JSON
        hospitals_json = []
        for h in hospitals:
            hospitals_json.append({
                "place_id": h.place_id,
                "name": h.name,
                "address": h.formatted_address,
                "location": {
                    "latitude": h.latitude,
                    "longitude": h.longitude
                },
                "distance_meters": h.distance_meters,
                "phone": h.phone_number,
                "website": h.website,
                "rating": h.rating,
                "user_ratings_total": h.user_ratings_total,
                "visited_before": h.visited_before,
                "rank_score": h.rank_score
            })
        
        return jsonify({
            "hospitals": hospitals_json,
            "count": len(hospitals_json),
            "search_radius_m": radius
        }), 200
        
    except ValueError:
        return jsonify({"error": "Invalid latitude/longitude"}), 400
    except Exception as e:
        logger.error(f"❌ Error searching hospitals: {e}")
        return jsonify({"error": "Internal server error"}), 500


@hospital_bp.route('/<place_id>/details', methods=['GET'])
def get_hospital_details(place_id: str):
    """
    Get detailed hospital information with scraped data
    
    Response:
        {
            "place_id": "...",
            "opd_timings": "...",
            "departments": [...],
            "emergency_number": "..."
        }
    """
    try:
        # Get basic info from Maps first (would need to fetch from DB or API)
        # For now, return scraped details
        
        website = request.args.get('website')
        
        if website:
            scraper_service = get_scraper_service()
            details = scraper_service.scrape_hospital_details(website, place_id)
            
            return jsonify({
                "place_id": place_id,
                "opd_timings": details.get("opd_timings"),
                "departments": details.get("departments", []),
                "emergency_number": details.get("emergency_number"),
                "bed_availability": details.get("bed_availability"),
                "last_scraped": details.get("last_scraped")
            }), 200
        else:
            return jsonify({"error": "Website URL required for scraping"}), 400
        
    except Exception as e:
        logger.error(f"❌ Error fetching hospital details: {e}")
        return jsonify({"error": "Internal server error"}), 500


@hospital_bp.route('/call', methods=['POST'])
def initiate_hospital_call():
    """
    Initiate click-to-call to hospital
    
    Request Body:
        {
            "patient_phone": "+919876543210",
            "hospital_phone": "+919123456789",
            "hospital_name": "City General Hospital"
        }
    
    Response:
        {
            "success": true,
            "call_sid": "...",
            "status": "initiated"
        }
    """
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ['patient_phone', 'hospital_phone', 'hospital_name']):
            return jsonify({"error": "Missing required fields"}), 400
        
        voice_service = get_voice_service()
        result = voice_service.initiate_call(
            patient_phone=data['patient_phone'],
            hospital_phone=data['hospital_phone'],
            hospital_name=data['hospital_name']
        )
        
        return jsonify(result), 200 if result.get('success') else 500
        
    except Exception as e:
        logger.error(f"❌ Error initiating call: {e}")
        return jsonify({"error": "Internal server error"}), 500


@hospital_bp.route('/appointment', methods=['POST'])
def book_appointment():
    """
    Book hospital appointment (webhook simulation)
    
    Request Body:
        {
            "patient_id": "...",
            "place_id": "...",
            "preferred_date": "2026-01-15",
            "preferred_time": "10:00 AM",
            "department": "Cardiology"
        }
    """
    try:
        data = request.get_json()
        
        # In real implementation, this would:
        # 1. Check if hospital has integration
        # 2. POST to hospital's booking API
        # 3. Or generate WhatsApp message with slot request
        
        # Mock response
        return jsonify({
            "success": True,
            "appointment_id": "mock_appt_123",
            "status": "pending_confirmation",
            "message": "Appointment request sent to hospital. You will receive confirmation shortly."
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error booking appointment: {e}")
        return jsonify({"error": "Internal server error"}), 500
