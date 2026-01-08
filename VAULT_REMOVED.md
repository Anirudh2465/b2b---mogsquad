# Secrets Management Removed (Vault -> Dotenv)

## 🔄 Migration Complete

I have removed the complex HashiCorp Vault integration and replaced it with **python-dotenv**. This is much simpler and better suited for a hackathon.

## 🚀 How to Configure Now

1. **Edit `.env` file** directly:

```bash
# Set mode
MOCK_MODE=false

# Add API Keys
GEMINI_API_KEY=AIzaSy...
GOOGLE_MAPS_API_KEY=AIzaSy...
TWILIO_AUTH_TOKEN=...

# Database Config
DB_SHARD0_PASSWORD=postgres
```

2. **Run Application**:
```bash
python app/main.py
```

That's it! No extra servers, no tokens, no Vault commands.

## 📂 File Changes
- **Deleted**: `app/core/vault_client.py`
- **Created**: `app/core/config.py`
- **Updated**: `app/main.py` (Now uses ConfigManager)
- **Updated**: `app/services/voice_service.py`
