"""
AuraHealth Flask Application
Main entry point with security infrastructure initialization.
"""
from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os

# Import core modules
from app.core.vault_client import init_vault, get_vault
from app.core.security import init_encryption
from app.database.router import init_shard_router
from app.database.connection import init_database_manager, get_db_manager

# Import services
from app.services.patient_service import PatientService

# Import routers
from app.routers.patient_router import patient_bp, init_patient_router

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
    
    # ===== SECURITY INITIALIZATION =====
    logger.info("🚀 Initializing AuraHealth Security Infrastructure...")
    
    # 1. Initialize Vault
    vault = init_vault(mock_mode=mock_mode)
    logger.info("✅ Vault initialized")
    
    # 2. Initialize Encryption with master key from Vault
    master_key = vault.get_master_encryption_key()
    init_encryption(master_key)
    logger.info("✅ AES-256-GCM encryption initialized")
    
    # 3. Initialize Shard Router
    init_shard_router(num_shards=2)
    logger.info("✅ Database shard router initialized")
    
    # 4. Initialize Database Connections
    db_manager = init_database_manager()
    
    if not mock_mode:
        # Connect to real shards using Vault credentials
        for shard_id in [0, 1]:
            creds = vault.get_database_credentials(shard_id)
            db_manager.add_shard(
                shard_id=shard_id,
                host=creds['host'],
                port=int(creds['port']),
                database=creds['database'],
                username=creds['username'],
                password=creds['password']
            )
    else:
        logger.info("⚠️  MOCK MODE: Skipping real database connections")
    
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
    
    # ===== REGISTER BLUEPRINTS =====
    app.register_blueprint(patient_bp)
    
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
    # Check if we should run in mock mode
    mock_mode = os.getenv("MOCK_MODE", "true").lower() == "true"
    
    app = create_app(mock_mode=mock_mode)
    
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
