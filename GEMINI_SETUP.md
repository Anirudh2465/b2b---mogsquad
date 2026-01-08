# Google Gemini API Setup Guide

## 🎯 Quick Setup (5 minutes)

### Step 1: Get Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click **"Create API Key"**
3. Copy your API key (starts with `AIza...`)

### Step 2: Add to Your `.env` File

Edit `d:/Anokha 2026/Hackathon/Version 1/.env`:

```bash
# Change this
MOCK_MODE=false

# Add your Gemini API key
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Choose your model (optional - defaults to gemini-1.5-flash)
GEMINI_MODEL=gemini-1.5-flash
```

### Step 3: Install Dependencies

```bash
pip install google-generativeai
```

### Step 4: Run the Application

```bash
python app/main.py
```

---

## 🤖 Available Gemini Models

### Recommended Models:

| Model | Best For | Speed | Cost | Max Tokens |
|-------|----------|-------|------|------------|
| **gemini-1.5-flash** ✅ | Fast responses, good quality | ⚡⚡⚡ | 💰 Free tier | 8,192 |
| **gemini-1.5-pro** | Best quality, complex tasks | ⚡⚡ | 💰💰 | 32,768 |
| **gemini-pro** | Legacy, still good | ⚡⚡ | 💰 Free tier | 8,192 |

**For hackathon:** Use `gemini-1.5-flash` (fastest + free)

---

## 🔧 Configuration Options

### Option 1: Environment Variables (Recommended)

Edit `.env`:
```bash
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-1.5-flash
```

### Option 2: HashiCorp Vault

Store in Vault:
```bash
vault kv put secret/aurahealth/api/gemini \
  api_key="your-key" \
  model_name="gemini-1.5-flash"
```

Then update `app/main.py` to fetch from Vault.

---

## 📊 Testing Your Setup

### Test 1: Health Check
```bash
curl http://localhost:5000/health
```

### Test 2: Generate Clinical Summary

```bash
curl http://localhost:5000/api/twin/550e8400-e29b-41d4-a716-446655440000/summary?max_words=150
```

**Expected Response:**
```json
{
  "patient_id": "550e8400-e29b-41d4-a716-446655440000",
  "summary": "Patient has...",
  "generated_at": "2026-01-08T19:30:00",
  "word_count": 142
}
```

---

## 🎯 Model Selection Guide

### When to use each model:

**gemini-1.5-flash** (Default - Recommended)
- ✅ Fast responses (< 2 seconds)
- ✅ Good for real-time summaries
- ✅ Free tier available
- ✅ Perfect for hackathon demos

**gemini-1.5-pro**
- ✅ Best quality outputs
- ✅ Better medical terminology understanding
- ✅ Use for production
- ⚠️ Slower (3-5 seconds)
- ⚠️ Costs more

**gemini-pro** (Legacy)
- ✅ Stable and reliable
- ✅ Free tier
- ⚠️ Being replaced by 1.5 models

---

## 💡 Advanced Configuration

### Custom Model Parameters

Edit `app/services/clinical_summary_service.py` line 70:

```python
generation_config={
    'temperature': 0.3,      # Lower = more focused (0.0-1.0)
    'max_output_tokens': 300, # Maximum summary length
    'top_p': 0.8,            # Nucleus sampling (0.0-1.0)
    'top_k': 40              # Top-k sampling
}
```

### For Medical Accuracy:
```python
temperature=0.2,  # More deterministic
top_p=0.7,        # More focused
top_k=30          # Narrower vocabulary
```

### For Creative Summaries:
```python
temperature=0.6,  # More creative
top_p=0.95,       # More diverse
top_k=60          # Wider vocabulary
```

---

## 🔒 Security Best Practices

### DO:
- ✅ Store API key in `.env` (not in code)
- ✅ Add `.env` to `.gitignore`
- ✅ Use Vault in production
- ✅ Rotate keys regularly

### DON'T:
- ❌ Commit API keys to GitHub
- ❌ Share keys publicly
- ❌ Use same key for dev/prod

---

## 🚨 Troubleshooting

### Error: "API key not valid"
**Solution:**
1. Check your API key is correct
2. Ensure no extra spaces in `.env`
3. Verify key at [Google AI Studio](https://makersuite.google.com/app/apikey)

### Error: "Module 'google.generativeai' not found"
**Solution:**
```bash
pip install google-generativeai
```

### Error: "Quota exceeded"
**Solution:**
1. Check your [quota usage](https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas)
2. Switch to paid tier or wait for quota reset
3. Use `MOCK_MODE=true` as fallback

### Mock Mode Not Working
**Solution:**
The service gracefully falls back to mock mode if:
- `MOCK_MODE=true` in `.env`
- API key is missing
- API call fails

---

## 📝 Code Changes Summary

### Files Modified:
1. ✅ `app/services/clinical_summary_service.py` - Gemini integration
2. ✅ `requirements.txt` - Added `google-generativeai`
3. ✅ `.env.example` - Added `GEMINI_API_KEY` and `GEMINI_MODEL`
4. ✅ `app/main.py` - Environment variable support

### What Changed:
- **Before:** OpenAI GPT-4 API
- **After:** Google Gemini API (configurable model)

---

## 🎉 You're Ready!

Your AuraHealth app now uses **Google Gemini** for AI-powered clinical summaries!

**Quick Start:**
```bash
# 1. Add your API key to .env
GEMINI_API_KEY=AIzaSy...

# 2. Run the app
python app/main.py

# 3. Test clinical summaries
curl http://localhost:5000/api/twin/{patient_id}/summary
```

**For hackathon demo:**
- Use `gemini-1.5-flash` (fastest)
- Keep `MOCK_MODE=true` as fallback
- The service automatically falls back to mock if API fails

---

## 📚 Resources

- [Google AI Studio](https://makersuite.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Python SDK Reference](https://ai.google.dev/tutorials/python_quickstart)
- [Pricing](https://ai.google.dev/pricing)
