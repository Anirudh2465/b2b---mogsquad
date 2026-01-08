# 🏥 AuraHealth - Privacy-First Patient Continuity Engine

> **MedTech Hackathon 2026** | Smart Medication Adherence Platform

## � Demo Video

**Watch the full demonstration:** [https://vimeo.com/1152630189/e222ad2b94](https://vimeo.com/1152630189/e222ad2b94)

---

## �🎯 Problem Statement

Patients face a **"Data Black Hole"** between clinic and home:
- Complex medication schedules lead to poor adherence
- No visibility into medication inventory before running out
- Fragmented medical history across multiple hospitals

## 💡 Solution

AuraHealth bridges this gap with:
- **OCR-based prescription digitization** (OpenCV + Tesseract)
- **Automated medication tracking** with refill alerts
- **AI-powered Digital Twin** for longitudinal health insights (Gemini AI)
- **Geo-intelligence** for nearby hospital discovery (Google Maps)

## ✨ Key Features

**Security & Infrastructure**
- AES-256-GCM encryption with per-user key derivation
- Horizontal database sharding (SHA-256 hash routing)
- Rate limiting and environment-based configuration

**Vision-AI & Inventory Management**
- OCR prescription scanning (OpenCV + Tesseract)
- Medical NER for extracting drug name, dosage, frequency
- Automatic inventory calculation and refill alerts (WhatsApp)

**Digital Twin & Intelligence**
- Chronic condition detection from prescription patterns
- AI-generated clinical summaries (Gemini 1.5)
- Nearby hospital discovery with web-scraped details
- Voice/SMS notifications (Twilio)

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

# CopyInstallation & Setup

### Prerequisites
- Python 3.12+
- Tesseract OCR (optional, for prescription scanning)

### Quick Start

```bash
# 1. Clone and navigate to the repository
git clone https://github.com/Anirudh2465/b2b---mogsquad.git
cd b2b---mogsquad

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and add your API keys (see below)

# 5. Run the application
PYTHONPATH=. python3 -m app.main
```

Server runs at `http://localhost:5000`

### API Keys Setup

Edit `.env` file with your credentials:

```env
# Google Gemini AI (free tier: https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_key_here

# Google Maps Places API (https://console.cloud.google.com/apis/credentials)
GOOGLE_MAPS_API_KEY=your_key_here

# Twilio (optional for SMS/Voice: https://console.twilio.com)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token

# Encryption key (generate with: python3 -c "import secrets; print(secrets.token_urlsafe(24))")
MASTER_ENCRYPTION_KEY=your_generated_key
```

**Mock Mode:** Set `MOCK_MODE=true` in `.env` to run without API keys
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
| Category | Endpoint | Description |
|----------|----------|-------------|
| **Core** | `GET /health` | Health check |
| **Patients** | `POST /api/patients/` | Create patient |
| | `GET /api/patients/<id>` | Get patient details |
| **Prescriptions** | `POST /api/prescriptions/upload` | Upload & OCR prescription |
| | `POST /api/prescriptions/<id>/confirm` | Create medications from OCR |
| **Medications** | `GET /api/medications/<patient_id>` | List medications |
| | `POST /api/medications/<id>/take` | Log dose taken |
| | `GET /api/medications/<id>/refill-link` | Get refill WhatsApp link |
| **Digital Twin** | `GET /api/digital_twin/<patient_id>` | Get health digital twin |
| | `GET /api/digital_twin/<patient_id>/summary` | AI clinical summary |
| **Hospitals** | `GET /api/hospitals/nearby?lat=X&lon=Y` | Find nearby hospitals |

### Testing

```bash
python3 -m pytest tests/ -v  # 46 tests
```
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
app/
├── main.py                  # Flask entry point
├── core/                    # Config, encryption, security
├── database/                # Connection manager, sharding router
├── models/                  # Data models (Patient, Medication, etc.)
├── routers/                 # API route handlers
└── services/                # Business logic (OCR, AI, Maps, etc.)
tests/                       # Unit & integration tests
requirements.txt             # Dependencies
.env.example                 # Environment template
```

## 🔒 Architecture

- **Security:** AES-256-GCM encryption, database sharding, rate limiting
- **Services:** OCR (Tesseract), Medical NER, AI Summaries (Gemini), Maps (Google), Notifications (Twilio)
- **Storage:** PostgreSQL with horizontal shardingMedTech Hackathon 2026

---

**Tech Stack:** Python 3.12+ | Flask | PostgreSQL | OpenCV | Tesseract | Gemini AI | Google Maps | Twilio