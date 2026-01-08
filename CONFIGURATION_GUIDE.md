# AuraHealth Configuration Guide

## 🚀 Quick Start (Development with Mock Mode)

For **immediate testing without any external services**, just run:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy environment file
cp .env.example .env

# 3. Ensure MOCK_MODE=true (default in .env.example)
# No need to change anything!

# 4. Run the application
python app/main.py
```

The app will run on `http://localhost:5000` with all services in **mock mode**.

---

## 📋 Configuration Checklist

### Where to Add API Keys and Configurations

#### 1. **Environment Variables** (`.env` file)

Create a `.env` file in the root directory by copying `.env.example`:

```bash
cp .env.example .env
```

**Edit `.env` with your API keys:**

```bash
# ===== APPLICATION MODE =====
MOCK_MODE=false  # Change to false for production

# ===== VAULT CONFIGURATION =====
VAULT_URL=https://your-vault-server.com
VAULT_ROLE_ID=your-role-id-from-vault-admin
VAULT_SECRET_ID=your-secret-id-from-vault-admin

# ===== REDIS CONFIGURATION =====
REDIS_URL=redis://your-redis-host:6379

# ===== DATABASE CONFIGURATION =====
# Fallback credentials (if Vault is unavailable)
DB_SHARD0_HOST=your-postgres-host
DB_SHARD0_PORT=5432
DB_SHARD0_DATABASE=aurahealth_shard0
DB_SHARD0_USER=your-db-user
DB_SHARD0_PASSWORD=your-db-password

DB_SHARD1_HOST=your-postgres-host
DB_SHARD1_PORT=5433
DB_SHARD1_DATABASE=aurahealth_shard1
DB_SHARD1_USER=your-db-user
DB_SHARD1_PASSWORD=your-db-password
```

---

#### 2. **HashiCorp Vault Setup** (Secrets Management)

**What to store in Vault:**

##### A. Database Credentials (Dynamic)
```bash
# Vault path: database/creds/aurahealth
vault write database/config/postgres \
  plugin_name=postgresql-database-plugin \
  allowed_roles="aurahealth" \
  connection_url="postgresql://{{username}}:{{password}}@localhost:5432/aurahealth_shard0"

vault write database/roles/aurahealth \
  db_name=postgres \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';" \
  default_ttl="24h" \
  max_ttl="72h"
```

##### B. Master Encryption Key
```bash
# Vault path: secret/aurahealth/encryption
vault kv put secret/aurahealth/encryption \
  master_key="your-32-byte-base64-encoded-key"
```

##### C. API Keys
```bash
# Vault path: secret/aurahealth/api/google_maps
vault kv put secret/aurahealth/api/google_maps \
  api_key="YOUR_GOOGLE_MAPS_API_KEY"

# Vault path: secret/aurahealth/api/twilio
vault kv put secret/aurahealth/api/twilio \
  account_sid="YOUR_TWILIO_ACCOUNT_SID" \
  auth_token="YOUR_TWILIO_AUTH_TOKEN" \
  phone_number="+1234567890"

# Vault path: secret/aurahealth/api/openai (Optional)
vault kv put secret/aurahealth/api/openai \
  api_key="YOUR_OPENAI_API_KEY"
```

**Code location:** `app/core/vault_client.py` (already implemented)

---

#### 3. **Google Maps API** (Hospital Discovery)

**Where to get:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Places API (New)**
4. Create credentials → API Key
5. Restrict key to Places API

**Where to add:**
- **Option A (Recommended):** Store in Vault at `secret/aurahealth/api/google_maps`
- **Option B:** Add to `.env` file as `GOOGLE_MAPS_API_KEY=your-key`

**Code location:** `app/services/maps_service.py` line 28
```python
def __init__(self, mock_mode: bool = True, api_key: Optional[str] = None):
    # Pass your API key here
```

**How to initialize in `main.py`:**
```python
# Get from Vault
vault = get_vault()
maps_api_key = vault.get_api_key('google_maps').get('api_key')
maps_service = init_maps_service(mock_mode=False, api_key=maps_api_key)
```

---

#### 4. **OpenAI API** (Clinical Summaries)

**Where to get:**
1. Go to [platform.openai.com](https://platform.openai.com/)
2. Create account and get API key
3. Ensure GPT-4 access is enabled

**Where to add:**
- **Option A (Recommended):** Store in Vault at `secret/aurahealth/api/openai`
- **Option B:** Add to `.env` file as `OPENAI_API_KEY=your-key`

**Code location:** `app/services/clinical_summary_service.py` line 21
```python
def __init__(self, mock_mode: bool = True, api_key: Optional[str] = None):
    # Pass your API key here
```

**How to initialize in `main.py`:**
```python
# Get from Vault
openai_api_key = vault.get_api_key('openai').get('api_key')
clinical_summary_service = init_clinical_summary_service(mock_mode=False, api_key=openai_api_key)
```

---

#### 5. **Twilio API** (Voice Calls & SMS)

**Where to get:**
1. Go to [twilio.com](https://www.twilio.com/)
2. Sign up and verify phone number
3. Get Account SID, Auth Token, and Twilio Phone Number from Dashboard

**Where to add:**
- **Recommended:** Store in Vault at `secret/aurahealth/api/twilio`
  ```json
  {
    "account_sid": "ACxxxxxxxxxxxxx",
    "auth_token": "your-auth-token",
    "phone_number": "+1234567890"
  }
  ```

**Code location:** 
- `app/services/notification_service.py` (SMS) - line 19
- `app/services/voice_service.py` (Voice) - line 21

**Already integrated with Vault** - credentials are fetched automatically from Vault in production mode.

---

#### 6. **PostgreSQL Database** (Sharded Data Storage)

**Setup:**

1. **Create two database shards:**
```bash
# Shard 0
createdb aurahealth_shard0
psql -d aurahealth_shard0 -f database_schema.sql
psql -d aurahealth_shard0 -f database_schema_phase2.sql

# Shard 1
createdb aurahealth_shard1
psql -d aurahealth_shard1 -f database_schema.sql
psql -d aurahealth_shard1 -f database_schema_phase2.sql
```

2. **Configure connection in `.env`** (fallback) or **Vault** (recommended)

**Code location:** `app/database/connection.py` - handles connection pooling

**How connections are initialized in `main.py` line 73:**
```python
if not mock_mode:
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
```

---

#### 7. **Redis** (Rate Limiting & Caching)

**Setup:**
```bash
# Install Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                  # macOS

# Start Redis
redis-server
```

**Where to add:**
- Add to `.env`: `REDIS_URL=redis://localhost:6379`

**Code location:** `app/main.py` line 107
```python
limiter = Limiter(
    storage_uri="redis://localhost:6379" if not mock_mode else "memory://"
)
```

---

#### 8. **Celery** (Background Jobs)

**Setup:**
```bash
# Start Celery worker
celery -A app.tasks.celery_tasks worker --loglevel=info

# Start Celery beat (scheduler)
celery -A app.tasks.celery_tasks beat --loglevel=info
```

**Configuration in code:** `app/tasks/celery_tasks.py` line 11
```python
celery_app = Celery(
    'aurahealth_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)
```

**Scheduled tasks:**
- Inventory monitor: Every hour
- Reminder scheduler: Daily
- Adherence scores: Weekly

---

## 🔧 Production Deployment Checklist

### Step 1: Environment Setup
```bash
# 1. Clone repository
git clone <your-repo>
cd <repo-directory>

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure .env
cp .env.example .env
# Edit .env with production values
```

### Step 2: Infrastructure Setup
```bash
# 1. Setup HashiCorp Vault
# 2. Create PostgreSQL shards (2 instances)
# 3. Setup Redis
# 4. Configure Cloudflare WAF (optional but recommended)
```

### Step 3: Database Migration
```bash
# Run schemas on both shards
psql -d aurahealth_shard0 -f database_schema.sql
psql -d aurahealth_shard0 -f database_schema_phase2.sql
psql -d aurahealth_shard1 -f database_schema.sql
psql -d aurahealth_shard1 -f database_schema_phase2.sql
```

### Step 4: Configure Vault
```bash
# Store all secrets in Vault (see section 2 above)
```

### Step 5: Update `main.py`
Change `MOCK_MODE=false` in `.env`

### Step 6: Run Application
```bash
# Production server (use gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 app.main:app

# Or with supervisor for auto-restart
supervisord -c supervisord.conf
```

---

## 🎯 Service-by-Service Configuration

### Summary Table

| Service | Configuration Location | Required API Key | Mock Mode Available |
|---------|----------------------|------------------|-------------------|
| **Vault** | `.env`: `VAULT_URL`, `VAULT_ROLE_ID`, `VAULT_SECRET_ID` | ✅ Yes | ✅ Yes |
| **PostgreSQL** | Vault or `.env`: `DB_SHARD*` vars | ❌ No (user/pass) | ⚠️ Partial |
| **Redis** | `.env`: `REDIS_URL` | ❌ No | ✅ Yes (in-memory) |
| **Google Maps** | Vault: `api/google_maps` | ✅ Yes | ✅ Yes |
| **OpenAI** | Vault: `api/openai` | ✅ Yes | ✅ Yes |
| **Twilio** | Vault: `api/twilio` (3 keys) | ✅ Yes | ✅ Yes |
| **Tesseract** | System install | ❌ No | ⚠️ N/A (OCR engine) |

---

## 🧪 Testing Your Configuration

### Test 1: Health Check
```bash
curl http://localhost:5000/health
# Expected: {"status": "healthy"}
```

### Test 2: Root Endpoint
```bash
curl http://localhost:5000/
# Expected: {"name": "AuraHealth API", "status": "operational", "mode": "mock"}
```

### Test 3: Create Patient (Phase 1)
```bash
curl -X POST http://localhost:5000/api/patients \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe",
    "medical_history": "Test patient"
  }'
```

### Test 4: Upload Prescription (Phase 2)
```bash
# Base64 encode an image first
base64 prescription.jpg > prescription_b64.txt

curl -X POST http://localhost:5000/api/prescriptions/upload \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "550e8400-e29b-41d4-a716-446655440000",
    "image": "'$(cat prescription_b64.txt)'"
  }'
```

### Test 5: Get Digital Twin (Phase 3)
```bash
curl http://localhost:5000/api/twin/550e8400-e29b-41d4-a716-446655440000
```

---

## ⚠️ Common Issues

### Issue 1: "Vault not initialized"
**Solution:** Set `MOCK_MODE=true` in `.env` for development

### Issue 2: "Database connection failed"
**Solution:** 
- Check PostgreSQL is running: `pg_isready`
- Verify credentials in `.env`
- Ensure schemas are loaded

### Issue 3: "Rate limiter error"
**Solution:** 
- Check Redis is running: `redis-cli ping`
- Or use MOCK_MODE for in-memory rate limiting

### Issue 4: "Import error: No module named 'cv2'"
**Solution:** `pip install opencv-python`

### Issue 5: "Tesseract not found"
**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

---

## 📚 Additional Resources

- **Vault Setup Guide:** https://www.vaultproject.io/docs/install
- **Google Places API:** https://developers.google.com/maps/documentation/places/web-service/overview
- **OpenAI API:** https://platform.openai.com/docs/api-reference
- **Twilio Docs:** https://www.twilio.com/docs/voice
- **PostgreSQL Sharding:** https://www.postgresql.org/docs/current/ddl-partitioning.html

---

## 🎯 Quick Reference: File Locations

```
Configuration Files:
├── .env                          # Main configuration (CREATE THIS)
├── .env.example                  # Template
├── requirements.txt              # Dependencies
├── database_schema.sql           # Phase 1 DB schema
├── database_schema_phase2.sql    # Phase 2 DB schema

Service Initialization:
├── app/main.py                   # Lines 43-173 (create_app function)
│   ├── Line 56: Vault init
│   ├── Line 69: Database connection
│   ├── Line 107: Maps service init
│   ├── Line 108: OpenAI service init
│   └── Line 110: Twilio service init

API Key Storage:
├── app/core/vault_client.py      # Vault integration
│   ├── Line 38: get_database_credentials()
│   ├── Line 56: get_master_encryption_key()
│   └── Line 65: get_api_key()

Service Files (where APIs are used):
├── app/services/maps_service.py          # Google Maps API
├── app/services/clinical_summary_service.py  # OpenAI API
├── app/services/notification_service.py  # Twilio SMS
└── app/services/voice_service.py         # Twilio Voice
```

---

## ✅ Final Checklist

Before going to production:

- [ ] Copy `.env.example` to `.env`
- [ ] Set `MOCK_MODE=false`
- [ ] Configure Vault with all secrets
- [ ] Setup PostgreSQL (2 shards)
- [ ] Install and start Redis
- [ ] Get Google Maps API key
- [ ] Get OpenAI API key (optional)
- [ ] Get Twilio credentials
- [ ] Install Tesseract OCR
- [ ] Run database migrations
- [ ] Test all endpoints
- [ ] Setup Celery workers
- [ ] Configure reverse proxy (nginx)
- [ ] Enable HTTPS
- [ ] Setup monitoring (optional)

**For hackathon demo:** Just keep `MOCK_MODE=true` and everything works without external services! 🎉
