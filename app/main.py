"""
AuraHealth Flask Application
Main entry point with security infrastructure initialization.
"""
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
from dotenv import load_dotenv

# Load env vars before anything else
load_dotenv()

# Import core modules
from app.core.security import init_encryption
from app.database.router import init_shard_router
from app.database.connection import init_database_manager, get_db_manager

# Import services
from app.services.patient_service import PatientService
from app.services.inventory_service import InventoryService
from app.services.ocr_service import init_ocr_service
from app.services.notification_service import init_notification_service
from app.services.digital_twin_service import init_digital_twin_service
from app.services.clinical_summary_service import init_clinical_summary_service
from app.services.maps_service import init_maps_service
from app.services.scraper_service import init_scraper_service
from app.services.voice_service import init_voice_service

# Import routers
from app.routers.patient_router import patient_bp, init_patient_router
from app.routers.prescription_router import prescription_bp
from app.routers.medication_router import medication_bp, init_medication_router
from app.routers.digital_twin_router import twin_bp
from app.routers.hospital_router import hospital_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(mock_mode: bool = True) -> Flask:
    """
    Create and configure the Flask application
    
    Args:
        mock_mode: If True, use mock Vault and skip real DB connections
        
    Returns:
        Configured Flask app
    """
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    
    # ===== SECURITY INITIALIZATION =====
    logger.info("🚀 Initializing AuraHealth Security Infrastructure...")
    
    # Initialize simple config manager
    from app.core.config import get_config
    config = get_config()

    # Initialize encryption
    # Using simple env var key instead of Vault
    master_key = config.get_master_encryption_key()
    init_encryption(master_key)
    logger.info("✅ Encryption initialized")

    # Initialize shard router
    init_shard_router(num_shards=2)
    logger.info("✅ Database shard router initialized")

    # Initialize database connection manager
    db_manager = init_database_manager()
    
    # Configure database shards
    if not mock_mode:
        for shard_id in [0, 1]:
            creds = config.get_database_credentials(shard_id)
            db_manager.add_shard(
                shard_id=shard_id,
                host=creds['host'],
                port=int(creds['port']),
                database=creds['database'],
                username=creds['username'],
                password=creds['password']
            )
        logger.info("✅ Database shards configured (PRODUCTION mode)")
    else:
        logger.info("⚠️  Database in MOCK mode (No connection)")
    
    # 5. Initialize Rate Limiter with Redis
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["100 per minute", "10 per second"],
        storage_uri="memory://" if mock_mode else "redis://localhost:6379",
        strategy="fixed-window"
    )
    logger.info("✅ Rate limiter initialized")
    
    # ===== SERVICE INITIALIZATION =====
    patient_service = PatientService()
    init_patient_router(patient_service)
    
    # Phase 2 services
    ocr_service = init_ocr_service()
    notification_service = init_notification_service(mock_mode=mock_mode)
    inventory_service = InventoryService()
    init_medication_router(inventory_service)
    
    # Phase 3 services
    digital_twin_service = init_digital_twin_service()
    
    # Clinical summary with Gemini
    gemini_config = config.get_api_key('gemini')
    clinical_summary_service = init_clinical_summary_service(
        mock_mode=mock_mode,
        api_key=gemini_config.get('api_key') if not mock_mode else None,
        model_name=gemini_config.get('model_name', 'gemini-1.5-flash')
    )
    
    # Maps and other services
    maps_config = config.get_api_key('google_maps')
    maps_service = init_maps_service(
        mock_mode=mock_mode, 
        api_key=maps_config.get('api_key') if not mock_mode else None
    )
    
    scraper_service = init_scraper_service(mock_mode=mock_mode)
    voice_service = init_voice_service(mock_mode=mock_mode)
    
    logger.info("✅ Phase 2 & 3 services initialized")
    
    # ===== REGISTER BLUEPRINTS =====
    app.register_blueprint(patient_bp)
    app.register_blueprint(prescription_bp)
    app.register_blueprint(medication_bp)
    app.register_blueprint(twin_bp)
    app.register_blueprint(hospital_bp)
    
    # ===== GLOBAL ERROR HANDLERS =====
    @app.errorhandler(429)
    def ratelimit_handler(e):
        """Handle rate limit exceeded"""
        logger.warning(f"⚠️  Rate limit exceeded: {request.remote_addr}")
        return jsonify({
            "error": "Rate limit exceeded",
            "message": str(e.description)
        }), 429
    
    @app.errorhandler(500)
    def internal_error_handler(e):
        """Handle internal server errors"""
        logger.error(f"❌ Internal server error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
    # ===== ROOT ENDPOINT =====
    @app.route('/')
    def root():
        """Root endpoint"""
        return jsonify({
            "name": "AuraHealth API",
            "version": "1.0.0",
            "status": "operational",
            "mode": "mock" if mock_mode else "production"
        }), 200
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({"status": "healthy"}), 200
    
    logger.info("✅ AuraHealth application initialized successfully")
    return app


if __name__ == '__main__':
    # Check if we should run in mock mode (Default to FALSE for production feel)
    mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"
    
    app = create_app(mock_mode=mock_mode)
    
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5002,
        debug=True
    )
