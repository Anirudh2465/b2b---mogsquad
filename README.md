# AuraHealth - Smart Medication Adherence Platform

**Demo:** [https://vimeo.com/1152630189/e222ad2b94](https://vimeo.com/1152630189/e222ad2b94)

## Problem

Patients struggle with medication adherence, inventory tracking, and fragmented medical records across hospitals.

## Solution

- **OCR prescription scanning** - Digitize paper prescriptions automatically
- **Smart inventory tracking** - Auto-calculate medication supply and send refill alerts
- **AI Digital Twin** - Long-term health insights using Gemini AI
- **Hospital finder** - Locate nearby hospitals with Google Maps integration

## Tech Stack

Python, Flask, PostgreSQL, OpenCV, Tesseract, Gemini AI, Google Maps, Twilio

**Security:** AES-256 encryption, database sharding, rate limiting

---

## Setup

```bash
git clone https://github.com/Anirudh2465/b2b---mogsquad.git
cd b2b---mogsquad
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
PYTHONPATH=. python3 -m app.main
```

Server: `http://localhost:5000`

## API Keys Required

- **Gemini AI**: https://aistudio.google.com/app/apikey
- **Google Maps**: https://console.cloud.google.com/apis/credentials  
- **Twilio** : https://console.twilio.com

Add to `.env` file. Set `MOCK_MODE=true` to run without API keys.

## Key Endpoints

- `POST /api/prescriptions/upload` - Upload prescription image
- `GET /api/medications/<patient_id>` - Get medications
- `POST /api/medications/<id>/take` - Log dose taken
- `GET /api/digital_twin/<patient_id>/summary` - AI health summary
- `GET /api/hospitals/nearby?lat=X&lon=Y` - Find hospitals

## Testing

```bash
pytest tests/ -v
```

---

**MedTech Hackathon 2026** | MIT License
