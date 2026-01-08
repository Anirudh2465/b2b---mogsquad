# AuraHealth - Intelligent Patient Continuity Engine

**Phase 1: Security Infrastructure** ✅

## 🎯 Project Vision
AuraHealth bridges the "Data Black Hole" between clinic visits by digitizing prescriptions, automating medication management, and creating a "Digital Twin" for seamless patient-pharmacy-hospital data flow.

## 🏗️ Architecture (Phase 1 Complete)

### 1. **Secrets Management** - HashiCorp Vault
- ✅ `hvac` Python wrapper implementation
- ✅ AppRole authentication
- ✅ Dynamic database credential rotation (24h expiry)
- ✅ Mock mode for development

### 2. **Row-Level Encryption** - AES-256-GCM
- ✅ User-specific key derivation with PBKDF2
- ✅ Master key stored in Vault
- ✅ Authenticated encryption (tamper detection)
- ✅ 96-bit IV + 128-bit auth tag

### 3. **Database Sharding** - PostgreSQL
- ✅ Hash-based routing: `hash(user_id) % 2`
- ✅ Connection pooling per shard
- ✅ Shard consistency validation

### 4. **DDoS Protection** - Flask-Limiter + Redis
- ✅ Rate limiting: 10 req/sec, 100 req/min
- ✅ IP-based tracking
- ✅ Memory fallback for development

## 📁 Project Structure
```
app/
├── core/
│   ├── vault_client.py      # Vault integration
│   ├── security.py           # AES-256-GCM encryption
│   └── __init__.py
├── database/
│   ├── connection.py         # Connection pooling
│   ├── router.py             # Sharding logic
│   └── __init__.py
├── models/
│   ├── patient.py            # Patient data models
│   └── __init__.py
├── services/
│   ├── patient_service.py    # Business logic
│   └── __init__.py
├── routers/
│   ├── patient_router.py     # REST API endpoints
│   └── __init__.py
└── main.py                   # Flask app entry point

tests/
└── test_security.py          # Unit tests

database_schema.sql           # PostgreSQL schema
requirements.txt              # Dependencies
.env.example                  # Configuration template
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and set MOCK_MODE=true for development
```

### 3. Run Application (Mock Mode)
```bash
python -m app.main
```

The API will start on `http://localhost:5000`

### 4. Run Tests
```bash
python -m pytest tests/test_security.py -v
```

## 🔒 Security Features

### ✅ Phase 1 Acceptance Criteria
- [x] No secret keys in `.env` or code (all from Vault)
- [x] Database queries routed to shards based on `hash(user_id)`
- [x] Patient data unreadable without Vault-stored master key
- [x] Rate limiting blocks excessive requests (10/sec, 100/min)

## 📡 API Endpoints

### Create Patient
```bash
POST /api/patients/
Content-Type: application/json

{
  "name": "John Doe",
  "medical_history": "No known allergies. Previous surgery in 2020."
}
```

### Get Patient
```bash
GET /api/patients/{patient_id}
```

### Update Patient
```bash
PUT /api/patients/{patient_id}
Content-Type: application/json

{
  "name": "Jane Doe",
  "medical_history": "Updated history"
}
```

### Health Check
```bash
GET /health
```

## 🧪 Testing Encryption

```python
from app.core.vault_client import init_vault
from app.core.security import init_encryption

# Initialize
vault = init_vault(mock_mode=True)
encryption = init_encryption(vault.get_master_encryption_key())

# Encrypt
user_id = "550e8400-e29b-41d4-a716-446655440000"
encrypted = encryption.encrypt("Sensitive Data", user_id)

# Decrypt
decrypted = encryption.decrypt(encrypted, user_id)
```

## 📊 Database Setup (Production)

```bash
# Shard 0
createdb aurahealth_shard0
psql aurahealth_shard0 < database_schema.sql

# Shard 1
createdb aurahealth_shard1
psql aurahealth_shard1 < database_schema.sql
```

## 🔐 Vault Setup (Production)

```bash
# Enable KV secrets engine
vault secrets enable -path=database kv-v2
vault secrets enable -path=api kv-v2

# Store master key
vault kv put database/master_key value="your-32-byte-key"

# Store database credentials
vault kv put database/shard0 \
  username=postgres \
  password=<password> \
  host=localhost \
  port=5432 \
  database=aurahealth_shard0
```

## 🎯 Next Steps (Phase 2)
- [ ] OCR Integration (Prescription scanning)
- [ ] Digital Twin Engine (Health trend tracking)
- [ ] Notification System (WhatsApp/SMS reminders)
- [ ] Geo-spatial Hospital Discovery

## 📝 License
Proprietary - Anokha 2026 Hackathon Project
