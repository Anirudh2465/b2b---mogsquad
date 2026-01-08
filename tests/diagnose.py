
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.getcwd())

def check_env():
    print("\n--- 1. Environment Variables ---")
    from dotenv import load_dotenv
    load_dotenv()
    
    keys = [
        "MOCK_MODE", "OPENROUTER_API_KEY", "MAPPLS_API_KEY", 
        "MAPPLS_CLIENT_ID", "MAPPLS_CLIENT_SECRET",
        "DB_SHARD0_HOST"
    ]
    
    for key in keys:
        val = os.getenv(key)
        status = "✅ Set" if val else "❌ Missing"
        masked = f"{val[:5]}..." if val and len(val) > 5 else "None"
        print(f"{key}: {status} ({masked})")

def check_openrouter():
    print("\n--- 2. OpenRouter (DeepSeek) Check ---")
    try:
        from app.services.clinical_summary_service import init_clinical_summary_service
        service = init_clinical_summary_service(mock_mode=False)
        
        # Test generation (dummy)
        # Note: we are not calling the full generation to save tokens/time, just checking init
        if hasattr(service, 'provider') and service.provider == 'openrouter':
            print(f"✅ Service initialized with provider: {service.provider}")
            print(f"Model: {service.model_name}")
            
            # Simple connection check
            import requests
            headers = {"Authorization": f"Bearer {service.api_key}"}
            res = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
            if res.status_code == 200:
                print("✅ OpenRouter API reachable and key valid")
            else:
                print(f"❌ OpenRouter API check failed: {res.status_code} {res.text}")
        else:
            print(f"⚠️ Service provider is: {getattr(service, 'provider', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ OpenRouter Check Failed: {e}")

def check_mappls():
    print("\n--- 3. Mappls (MapMyIndia) Check ---")
    try:
        from app.services.maps_service import init_maps_service
        service = init_maps_service(mock_mode=False)
        
        if hasattr(service, 'provider') and service.provider == 'mappls':
            print("✅ Service initialized with provider: mappls")
            
            # Test Token Generation
            try:
                token = service._get_mappls_token()
                print(f"✅ OAuth Token Generated: {token[:10]}...")
            except Exception as e:
                print(f"❌ OAuth Token Generation Failed: {e}")
        else:
            print(f"⚠️ Service provider is: {getattr(service, 'provider', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ Mappls Check Failed: {e}")

def check_database():
    print("\n--- 4. Database Connection Check ---")
    try:
        from app.database.connection import init_database_manager, get_db_manager
        # Attempt init
        try:
            init_database_manager()
            db = get_db_manager()
            # Test connection to shard 0
            with db.get_connection(0) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    print("✅ Database (Shard 0) Connected")
        except Exception as e:
            print(f"❌ Database Connection Failed: {e}")
            print("   (This is expected if PostgreSQL is not running locally)")
            
    except ImportError:
        print("❌ Could not import database modules")

if __name__ == "__main__":
    check_env()
    check_openrouter()
    check_mappls()
    check_database()
