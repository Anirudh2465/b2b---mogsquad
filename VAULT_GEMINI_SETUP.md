# How to Store Gemini API Key in HashiCorp Vault

## 🔐 Vault Setup for Gemini API

### Option 1: Using Vault CLI

```bash
# Set your Vault address and token
export VAULT_ADDR=https://your-vault-cluster.vault.hashicorp.cloud:8200
export VAULT_TOKEN=hvs.your-admin-token

# Store Gemini API key in Vault
vault kv put secret/aurahealth/api/gemini \
  api_key="AIzaSyYOUR_GEMINI_API_KEY_HERE" \
  model_name="gemini-1.5-flash"
```

### Option 2: Using HCP Vault UI

1. Go to your HCP Vault dashboard
2. Navigate to **Secrets** → **secret/**
3. Create path: `aurahealth/api/gemini`
4. Add key-value pairs:
   - **Key**: `api_key` → **Value**: `AIzaSyYOUR_KEY`
   - **Key**: `model_name` → **Value**: `gemini-1.5-flash`

---

## 📋 Complete Vault Structure

Store all your API keys in Vault like this:

```
secret/
└── aurahealth/
    ├── encryption/
    │   └── master_key: "your-32-byte-encryption-key"
    └── api/
        ├── gemini/
        │   ├── api_key: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        │   └── model_name: "gemini-1.5-flash"
        ├── google_maps/
        │   └── api_key: "AIzaSyYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY"
        └── twilio/
            ├── account_sid: "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            ├── auth_token: "your-auth-token"
            └── phone_number: "+1234567890"
```

---

## 🔧 How It Works in Code

### 1. Production Mode (MOCK_MODE=false)

When you run with `MOCK_MODE=false`, the app:

```python
# app/main.py - Line 113
vault = get_vault()
gemini_config = vault.get_api_key('gemini')
gemini_api_key = gemini_config.get('api_key')
gemini_model = gemini_config.get('model_name', 'gemini-1.5-flash')
```

### 2. Fallback to Environment

If Vault is unreachable, it falls back to `.env`:

```python
# Fallback
gemini_api_key = os.getenv('GEMINI_API_KEY')
gemini_model = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
```

### 3. Mock Mode (MOCK_MODE=true)

Gemini API is not called; mock summaries are generated instead.

---

## 🚀 Deployment Workflow

### Step 1: Store Keys in Vault

```bash
# Gemini API
vault kv put secret/aurahealth/api/gemini \
  api_key="AIzaSy..." \
  model_name="gemini-1.5-flash"

# Google Maps API
vault kv put secret/aurahealth/api/google_maps \
  api_key="AIzaSy..."

# Twilio API
vault kv put secret/aurahealth/api/twilio \
  account_sid="AC..." \
  auth_token="..." \
  phone_number="+1234567890"
```

### Step 2: Update `.env`

```bash
# Enable production mode
MOCK_MODE=false

# Vault configuration
VAULT_URL=https://your-vault.vault.hashicorp.cloud:8200
VAULT_TOKEN=hvs.your-admin-token

# NO API KEYS IN .env - they come from Vault!
```

### Step 3: Run Application

```bash
python app/main.py
```

You'll see:
```
✅ Retrieved Gemini API key from Vault (model: gemini-1.5-flash)
✅ Retrieved Google Maps API key from Vault
✅ Google Gemini client initialized with model: gemini-1.5-flash
```

---

## 🧪 Testing Your Setup

### Test 1: Verify Vault Connection

```bash
# Check if you can read from Vault
vault kv get secret/aurahealth/api/gemini

# Expected output:
# ====== Data ======
# Key           Value
# ---           -----
# api_key       AIzaSy...
# model_name    gemini-1.5-flash
```

### Test 2: Start Application

```bash
python app/main.py
```

Look for these log messages:
```
✅ Vault client initialized (PRODUCTION mode)
✅ Retrieved Gemini API key from Vault (model: gemini-1.5-flash)
✅ Google Gemini client initialized with model: gemini-1.5-flash
```

### Test 3: Generate Clinical Summary

```bash
curl http://localhost:5000/api/twin/test-patient-123/summary
```

Should return a real AI-generated summary (not mock).

---

## 🎯 Configuration Priority

The app uses this priority order:

1. **Vault** (if `MOCK_MODE=false` and Vault is accessible)
2. **Environment Variables** (fallback if Vault fails)
3. **Mock Mode** (if `MOCK_MODE=true` or all else fails)

This ensures your app always works, even if Vault is temporarily down!

---

## 💡 Best Practices

### ✅ DO:
- Store all API keys in Vault
- Use `MOCK_MODE=true` for development
- Rotate API keys regularly via Vault
- Use different Vault paths for dev/staging/prod

### ❌ DON'T:
- Commit API keys to `.env` file
- Store API keys in code
- Share Vault tokens publicly
- Use production keys in development

---

## 🔒 Security Benefits

### Why Use Vault?

1. **Centralized Secrets**: All API keys in one place
2. **Audit Logging**: Track who accessed what key and when
3. **Dynamic Credentials**: Auto-rotate database passwords
4. **Access Control**: Fine-grained permissions per service
5. **Encryption**: All secrets encrypted at rest and in transit

### Example: Rotating Gemini API Key

```bash
# Get new API key from Google AI Studio
# Update in Vault (no code changes needed!)
vault kv put secret/aurahealth/api/gemini \
  api_key="NEW_KEY_HERE" \
  model_name="gemini-1.5-flash"

# Restart application
# New key is now in use!
```

---

## 📝 Quick Reference

### Vault Paths for AuraHealth:

| Service | Vault Path | Keys |
|---------|-----------|------|
| **Gemini AI** | `secret/aurahealth/api/gemini` | `api_key`, `model_name` |
| **Google Maps** | `secret/aurahealth/api/google_maps` | `api_key` |
| **Twilio** | `secret/aurahealth/api/twilio` | `account_sid`, `auth_token`, `phone_number` |
| **Encryption** | `secret/aurahealth/encryption` | `master_key` |

### Code Locations:

| Component | File | Line |
|-----------|------|------|
| Vault client | `app/core/vault_client.py` | 65 |
| Gemini init | `app/main.py` | 113 |
| API key fetch | `app/core/vault_client.py` | 65-74 |

---

## ✅ Final Checklist

- [ ] Get Gemini API key from https://makersuite.google.com/app/apikey
- [ ] Store in Vault: `vault kv put secret/aurahealth/api/gemini api_key="..."`
- [ ] Set `MOCK_MODE=false` in `.env`
- [ ] Configure `VAULT_URL` and `VAULT_TOKEN` in `.env`
- [ ] Remove any API keys from `.env` (use Vault only)
- [ ] Test: `python app/main.py`
- [ ] Verify log shows "Retrieved Gemini API key from Vault"

---

**Now your API keys are secure in Vault!** 🔐

No more hardcoded secrets in `.env` files or code!
