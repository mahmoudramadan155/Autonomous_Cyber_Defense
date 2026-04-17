# 🛡️ Autonomous Cyber Defense & Threat Intelligence Platform

A full-stack, enterprise-grade cybersecurity platform built with **FastAPI**, **PostgreSQL**, **Redis Streams**, **scikit-learn**, and a true decoupled microservices architecture.

---

## 🧠 🔥 1. ENTERPRISE ARCHITECTURE (FINAL FORM)

```text
                ┌───────────────┐
                │  Data Sources │
                └──────┬────────┘
                       ↓
            ┌─────────────────────┐
            │  Vector / Beats     │
            └────────┬────────────┘
                     ↓
          ┌──────────────────────┐
          │ Redis Streams        │
          │ (Microservices Bus)  │
          └────────┬─────────────┘
                   ↓
    ┌──────────────────────────────────┐
    │ Detection + ML + Correlation     │
    │ (Worker Services)                │
    └────────┬─────────────────────────┘
             ↓
    ┌──────────────────────────────────┐
    │ Risk + SOAR Engine               │
    │ (Response Worker)                │
    └────────┬─────────────────────────┘
             ↓
 ┌────────────────────────────────────────────┐
 │ Storage Layer                              │
 │ PostgreSQL | Redis                         │
 └────────┬───────────────────────────────────┘
          ↓
 ┌────────────────────────────────────────────┐
 │ API Gateway + Auth + Multi-Tenant          │
 └────────┬───────────────────────────────────┘
          ↓
 ┌────────────────────────────────────────────┐
 │ Dashboard (Grafana + Custom React)         │
 └────────────────────────────────────────────┘
```

---

## 🏗️ What You're Building

```text
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃          AUTONOMOUS CYBER DEFENSE PLATFORM (SIEM + SOAR)                ┃
┃     Enterprise threat detection + automated response = mini-Splunk      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌─────────────────┐
│  LOG SOURCES    │
├─────────────────┤
│ Syslog          │
│ Nginx/Apache    │
│ Firewall        │
│ API Gateway     │
└────────┬────────┘
         │ (various formats)
         ▼
┌─────────────────────────────┐
│  INGESTION SERVICE          │
│  (Normalize → NormalizedLog)│
└────────┬────────────────────┘
         │ Redis: logs_raw
         ▼
     [PIPELINE]
     
┌─────────────────────────────┐
│  DETECTION WORKER           │
│  ┌─────────────────────┐    │
│  │ Rules (7 patterns)  │    │  Outputs:
│  │ ML (XGBoost/Iso)    │ ───┼→ • SQL Injection: 0.91 confidence
│  └─────────────────────┘    │  • Brute Force: 0.85 confidence
└────────┬────────────────────┘  • DDoS: 0.88 confidence
         │ Redis: alerts         • Port Scan: 0.70-0.98
         ▼
         
┌─────────────────────────────┐
│  CORRELATION WORKER         │
│  (Group alerts → incidents) │
├─────────────────────────────┤
│ Rule 1: 5 failed logins +   │  Outputs:
│         success = Account   │  • Account Compromise: risk 95
│         Compromise          │  • Web Application Attack: risk 82
│ Rule 2: SQLi + XSS = Web    │  • Sustained Brute Force: risk 75
│         Attack              │  • DDoS Incident: risk 90
└────────┬────────────────────┘
         │ Redis: incidents
         ▼
         
┌─────────────────────────────┐
│  RISK & RESPONSE WORKER     │
│  Formula:                   │
│  score = (severity ×        │  Risk Levels:
│           asset_value ×     │  • 80+:  Critical
│           incident_type ×   │  • 60-79: High
│           time_of_day) +    │  • 40-59: Medium
│          frequency_bonus    │  • 0-39:  Low
│                             │
│  If AUTO_MODE=True:         │  Actions:
│  • Score ≥80: Block IP      │  ├─ iptables rule
│  • Account: Disable user    │  ├─ DB user disable
└────────┬────────────────────┘
         │ API calls + DB updates
         ▼
         
┌─────────────────────────────┐
│  STORAGE (PostgreSQL)       │
│  ├─ alerts table            │
│  ├─ incidents table         │
│  └─ blocked_ips table       │
└────────┬────────────────────┘
         │
         ▼
         
┌─────────────────────────────┐
│  FASTAPI GATEWAY            │
│  • GET  /alerts             │
│  • GET  /incidents          │
│  • POST /response/execute   │
└─────────────────────────────┘
```

---

## 📚 10-Layer Stack

```text
LAYER 10  │ Dashboard (React)
          │ Monitoring (Grafana)
          │ Reports
──────────┼─────────────────────────────
LAYER 9   │ API Gateway (FastAPI)
          │ REST endpoints + WebSocket
──────────┼─────────────────────────────
LAYER 8   │ Storage (PostgreSQL + Redis)
──────────┼─────────────────────────────
LAYER 7   │ Response Engine (SOAR automation)
          │ Auto-block, rate-limit, disable user
──────────┼─────────────────────────────
LAYER 6   │ Risk Scoring Engine
          │ Severity × Assets × Type × Frequency
──────────┼─────────────────────────────
LAYER 5   │ Correlation Engine
          │ Alert grouping (sliding window rules)
──────────┼─────────────────────────────
LAYER 4   │ Detection Service
          │ Rules (7) + ML + Anomaly (IsoForest)
──────────┼─────────────────────────────
LAYER 3   │ Ingestion Service
          │ Log normalization → NormalizedLog schema
──────────┼─────────────────────────────
LAYER 2   │ Redis Streams (Event Queue)
          │ logs_raw → alerts → incidents
──────────┼─────────────────────────────
LAYER 1   │ Data Sources
          │ Vector, Syslog, Nginx, Firewall, API logs
```

---

## 📁 True Microservices Structure

This platform utilizes a modern streaming architecture. All workers boot from the same codebase but execute entirely decoupled asynchronous workloads communicating strictly via Redis Streams.

```text
app/
├── api/routes/         # FastAPI route handlers (Ingestion, Dashboards)
├── core/config.py      # Environment configuration
├── db/session.py       # Asyncpg PostgreSQL connection pool
├── models/             # SQLAlchemy ORM models
├── schemas/            # Pydantic schemas
├── services/           # Core business logic (Log Collector, Risk, etc)
├── main.py             # FastAPI API Gateway Entrypoint
├── worker_main.py      # Microservices Worker Entrypoint
└── workers.py          # Consumer Loops (Detection, Correlation, Response)
```

---

## 🚀 Quickstart (Production-Grade Local)

We use Docker Compose to spin up the entire microservices mesh. You can launch it in detached mode and view the logs individually.

```bash
# Start the full 8-container enterprise mesh in the background
docker compose -f docker/docker-compose.yml up -d --build

# View real-time logs for the API Gateway
docker compose -f docker/docker-compose.yml logs -f api

# View real-time logs for the Frontend Dashboard
docker compose -f docker/docker-compose.yml logs -f frontend

# Run all attacks from inside the API container:
docker exec -it cyber_defense_api python scripts/pentest_simulate.py --attack all

# Or individual attacks:
docker exec -it cyber_defense_api python scripts/pentest_simulate.py --attack ddos
docker exec -it cyber_defense_api python scripts/pentest_simulate.py --attack brute_force

```

This spins up **8 isolated containers**:
1. `cyber_defense_postgres`: Persistent SQL Storage
2. `cyber_defense_redis`: Stream Queue and Caching
3. `cyber_defense_api`: FastAPI Ingestion & Core API
4. `cyber_defense_detection`: AI & Rule Threat Detection Consumer
5. `cyber_defense_correlation`: Multi-Alert Correlation Consumer
6. `cyber_defense_response`: Dynamic Risk & SOAR Engine Consumer
7. `cyber_defense_vector`: 3rd Party Log Forwarding Engine
8. `cyber_defense_frontend`: React UI Dashboard served via Nginx

---

## 🖥️ Frontend Dashboard

The platform includes a real-time React dashboard that connects to the FastAPI backend. It allows security analysts to triage alerts, manage incidents, and view real-time system metrics.

**Access the Dashboard:** `http://localhost:3000/`
**Interactive API docs:** `http://localhost:8000/docs`

### How to Use the Dashboard
1. **Alert Triage:** Watch the live queue of raw threats detected by the Detection Worker (Rules/ML).
2. **Incident Investigation:** View incidents that have been successfully correlated from multiple weak alerts.
3. **SOAR Execution:** When an incident reaches a critical risk score (≥80), it is automatically blocked. For high-risk items (60-79), analysts can use the dashboard to **manually approve** response actions (e.g., blocking an IP address).
4. **Metrics:** View Grafana-style charts displaying Alerts/sec, Incidents/day, and Top Threats.

---

## 🔌 Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ingest/logs` | Async ingest one log event |
| `POST` | `/api/v1/ingest/logs/bulk` | Async ingest bulk log events |
| `GET`  | `/api/v1/alerts/` | List all detected alerts |
| `GET`  | `/api/v1/incidents/{id}/report` | Full incident report |
| `GET`  | `/api/v1/dashboard/` | Real-time stats |
| `POST` | `/api/v1/red-team/simulate/{type}` | Attack simulation |

**Attack simulation types:** `brute_force` · `sqli` · `xss` · `port_scan` · `ddos`
