# 🏥 AuraHealth - Privacy-First Patient Continuity Engine

> **MedTech Hackathon 2026** | Smart Medication Adherence Platform

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 The Problem

There's a **"Data Black Hole"** between the clinic and home:
- Patients fail to adhere to prescriptions due to complex schedules
- Inventory blindness leads to running out of critical medications
- Medical history remains fragmented across hospitals

## 💡 The Solution

AuraHealth is a **Privacy-First Longitudinal Patient Continuity Engine** that:
- Digitizes paper prescriptions via OCR
- Automates medication tracking and refill alerts
- Synthesizes a "Health Digital Twin" for long-term insights

---

## ✨ Features Implemented

### Phase 1: Security & Infrastructure ✅
| Feature | Status | Description |
|---------|--------|-------------|
| AES-256-GCM Encryption | ✅ | Row-level encryption with per-user key derivation |
| Database Sharding | ✅ | Horizontal sharding by User_UUID using SHA-256 hash |
| Rate Limiting | ✅ | Flask-Limiter with configurable thresholds |
| Secrets Management | ✅ | Environment-based config (hackathon-friendly) |

### Phase 2: Vision-AI & Predictive Inventory ✅
| Feature | Status | Description |
|---------|--------|-------------|
| OCR Service | ✅ | OpenCV + Tesseract with deskewing & preprocessing |
| Medical NER | ✅ | Extracts drug name, strength, frequency, duration |
| Frequency Parsing | ✅ | Supports BID, TID, QD, 1-0-1, QHS formats |
| Inventory Calculation | ✅ | `Total Pills = Doses/Day × Duration` |
| Dynamic Tracking | ✅ | TAKEN (-1), MISSED (log only), LOST (manual) |
| Refill Alerts | ✅ | Auto-generate WhatsApp links when stock < 20% |

### Phase 3: Digital Twin & Geo-Intelligence ✅
| Feature | Status | Description |
|---------|--------|-------------|
| Health Digital Twin | ✅ | Chronic condition detection (≥3 prescriptions = chronic) |
| Clinical Summary | ✅ | Gemini AI-powered patient summaries |
| Risk Levels | ✅ | HIGH (<70%), MEDIUM (70-85%), LOW (>85%) adherence |
| Hospital Discovery | ✅ | Google Maps Places API integration |
| Web Scraper | ✅ | BeautifulSoup for OPD timings, departments |
| Voice Service | ✅ | Twilio Voice API integration |

### Phase 4: Interface (Backend Ready) ⏳
| Feature | Status | Description |
|---------|--------|-------------|
| REST API | ✅ | All endpoints implemented and tested |
| Frontend | ⏳ | Backend-only for security (Phase 4 pending) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.14+
- Tesseract OCR (for prescription scanning)
- PostgreSQL (optional, runs in mock mode)

### Installation

```bash
# Clone the repository
cd "/Users/gopal/Version 1"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run the application
PYTHONPATH=. python3 -m app.main
```

The API will be available at `http://localhost:5000`

> **Note:** If port 5000 is busy (macOS AirPlay), run on port 5001:
> ```bash
> PYTHONPATH=. python3 -c "from app.main import create_app; app = create_app(); app.run(port=5001)"
> ```

---

## 🔐 API Keys Configuration

### Required API Keys

| Service | Where to Get | Environment Variable |
|---------|--------------|---------------------|
| **Gemini AI** | [Google AI Studio](https://aistudio.google.com/app/apikey) | `GEMINI_API_KEY` |
| **Google Maps** | [Google Cloud Console](https://console.cloud.google.com/apis/credentials) | `GOOGLE_MAPS_API_KEY` |
| **Twilio** | [Twilio Console](https://console.twilio.com) | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` |

### Setup Instructions

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your API keys:**
   ```bash
   nano .env   # or use any text editor
   ```

3. **Required fields:**
   ```env
   # Google Gemini (Free tier available)
   GEMINI_API_KEY=your_actual_api_key
   GEMINI_MODEL=gemini-1.5-flash
   
   # Google Maps (Enable Places API)
   GOOGLE_MAPS_API_KEY=your_actual_api_key
   
   # Twilio (For SMS/Voice/WhatsApp)
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=+1234567890
   
   # Encryption (CHANGE THIS!)
   MASTER_ENCRYPTION_KEY=generate_random_32_char_string
   ```

4. **Generate a secure encryption key:**
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(24))"
   ```

### ⚠️ Security Notes

- **NEVER commit `.env` to git** - it's in `.gitignore`
- **Mock Mode:** Set `MOCK_MODE=true` to run without real APIs
- The `.env.example` file contains **only placeholder values**

---

## 📡 API Endpoints

### Core Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API status |
| GET | `/health` | Health check |

### Patient Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/patients/` | Create new patient |
| GET | `/api/patients/<id>` | Get patient details |
| PUT | `/api/patients/<id>` | Update patient |

### Prescription OCR
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/prescriptions/upload` | Upload & OCR prescription image |
| GET | `/api/prescriptions/<id>` | Get prescription details |
| POST | `/api/prescriptions/<id>/confirm` | Confirm OCR & create medications |

### Medication Tracking
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/medications/<patient_id>` | List patient medications |
| POST | `/api/medications/<id>/take` | Log medication taken |
| POST | `/api/medications/<id>/miss` | Log missed dose |
| GET | `/api/medications/<id>/refill-link` | Get WhatsApp refill link |

### Digital Twin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/digital_twin/<patient_id>` | Get patient's Digital Twin |
| GET | `/api/digital_twin/<patient_id>/summary` | AI-generated clinical summary |

### Hospital Discovery
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hospitals/nearby` | Find nearby hospitals |
| GET | `/api/hospitals/<place_id>/details` | Get hospital details (scraped) |

---

## 🧪 Running Tests

```bash
source venv/bin/activate
python3 -m pytest tests/ -v
```

Expected output: **46 tests passed**

---

## 📁 Project Structure

```
Version 1/
├── app/
│   ├── main.py              # Flask app entry point
│   ├── core/
│   │   ├── config.py        # Environment configuration
│   │   └── security.py      # AES-256-GCM encryption
│   ├── database/
│   │   ├── connection.py    # PostgreSQL connection manager
│   │   └── router.py        # Sharding router
│   ├── models/              # Pydantic data models
│   ├── routers/             # Flask blueprints (API routes)
│   └── services/
│       ├── ocr_service.py           # Prescription OCR
│       ├── semantic_parser.py       # Medical NER
│       ├── notification_service.py  # WhatsApp/SMS alerts
│       ├── digital_twin_service.py  # Health Digital Twin
│       ├── clinical_summary_service.py  # Gemini AI summaries
│       ├── maps_service.py          # Google Maps integration
│       ├── scraper_service.py       # Hospital web scraper
│       └── voice_service.py         # Twilio Voice
├── tests/                   # Unit & integration tests
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## 🔒 Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Rate Limiter (100/min)                   │
├─────────────────────────────────────────────────────────────┤
│                      Flask REST API                          │
├───────────┬───────────┬───────────┬───────────┬─────────────┤
│  Patients │ Prescrip- │ Medica-   │  Digital  │  Hospitals  │
│   Router  │   tions   │   tions   │   Twin    │   Router    │
├───────────┴───────────┴───────────┴───────────┴─────────────┤
│                    Services Layer                            │
│  OCR │ NER │ Notifications │ Maps │ Scraper │ Voice │ AI    │
├─────────────────────────────────────────────────────────────┤
│  AES-256-GCM Encryption   │   SHA-256 Shard Router          │
│  (Per-user key derivation)│   (hash(user_id) % num_shards)  │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL Shard 0       │   PostgreSQL Shard 1            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Hackathon Checklist

- [x] **Phase 0:** Problem-solution fit confirmed
- [x] **Phase 1:** Sharded DB + encryption implemented
- [x] **Phase 2:** OCR + Medical NER + inventory tracking
- [x] **Phase 3:** Digital Twin + Gemini AI + Maps
- [ ] **Phase 4:** Frontend (backend complete, UI pending)

---

## 🛡️ Hackathon Security Tips

1. **Keep `.env` private** - Never share or commit
2. **Use mock mode** for demos: `MOCK_MODE=true`
3. **Rotate API keys** after the hackathon
4. **Rate limiting** is enabled to prevent abuse

---

## 📄 License

MIT License - Built for MedTech Hackathon 2026

---

**Built with ❤️ for better patient outcomes**
