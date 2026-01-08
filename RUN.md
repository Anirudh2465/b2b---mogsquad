# 🚀 AuraHealth Run Guide

## 1. Quick Start (Run the API)

Since you've already configured your `.env` file:

```bash
# Start the Flask Server
python app/main.py
```

SERVER RUNNING AT: `http://localhost:5000`

---

## 2. API Testing Commands

Open a new terminal to run these tests while the server is running.

### Health Check
```bash
curl http://localhost:5000/health
```

### Digital Twin Summary (Gemini AI)
```bash
curl "http://localhost:5000/api/twin/550e8400-e29b-41d4-a716-446655440000/summary"
```

### Hospital Search (Google Maps)
```bash
curl "http://localhost:5000/api/hospitals/search?lat=12.9716&lon=77.5946&radius=5000"
```

---

## 3. Background Services (Optional)

For full functionality (inventory tracking, rate limiting), you need these running:

1. **Redis** (for rate limits):
   ```bash
   redis-server
   ```

2. **Celery** (for inventory/notifications):
   ```bash
   celery -A app.tasks.celery_tasks worker --loglevel=info
   ```

---

## 4. Resetting Database (If needed)

If you need to wipe and recreate the database:

```bash
# Shard 0
psql -d aurahealth_shard0 -f database_schema.sql
psql -d aurahealth_shard0 -f database_schema_phase2.sql

# Shard 1
psql -d aurahealth_shard1 -f database_schema.sql
psql -d aurahealth_shard1 -f database_schema_phase2.sql
```
