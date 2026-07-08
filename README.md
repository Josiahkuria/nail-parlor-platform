# Nail Parlor Digital Platform & Automation Engine

A containerized, multi-tiered digital platform featuring a modern customer frontend integrated with a headless WhatsApp booking automation gateway.

---

## System Architecture

The platform is split into two primary components: the client-facing frontend application and the backend automation infrastructure.

[ Customer Browser ] =(HTTPS)=> [ Frontend App ]
|
(Booking Webhooks)
|
v
[ WhatsApp Business ] <> [ Evolution API (Port 8080) ] <> [ n8n Workflow Engine (Port 5678) ]
||
[ PostgreSQL DB (Port 5432) ]

---

## Component Breakdown

### 1. Frontend Client
* **Location:** `/frontend`
* Contains the UI assets, booking forms, and schedules where clients interact with the salon.
* Connects seamlessly with the backend hooks to schedule appointments.

### 2. DevOps & Automation Stack
Managed via a unified `docker-compose` lifecycle, providing seamless persistence and network isolation.

* **n8n Orchestration Engine (Port 5678):** Handles the core scheduling logic, workflow branches, and timing events.
* **Evolution API Gateway (Port 8080):** Manages the headless browser instance interacting with the WhatsApp Web protocol.
* **PostgreSQL Database (Port 5432):** Delivers relational data persistence for system metadata and instant session-token recovery.

---

## Local Environment & Port Configuration

| Service | Local Mapping | Internal Port | Access URI |
| :--- | :--- | :--- | :--- |
| **Evolution API** | 8080:8080 | 8080 | http://localhost:8080 |
| **n8n Dashboard** | 5678:5678 | 5678 | http://localhost:5678 |
| **PostgreSQL** | Isolated | 5432 | whatsapp_db:5432 (Internal Net) |

### Core Security Access
* **Global Authentication Header:** `apikey`
* **Local Security Token:** `StudioAutomationKey2026`

---

## Deployment & Data Management

### Persistent Volumes
To ensure session tokens and database schemas survive container rebuilds, the following root paths are mapped directly to the host filesystem:
* `evolution_db_data/` -> PostgreSQL system tables.
* `evolution_storage/` -> Active WhatsApp login states and cache files.
* `n8n_storage/` -> Automation workflow states.

### Launching the Stack
To initialize the backend infrastructure, navigate to your orchestration root and execute:
```bash
docker compose up -d
Fetching a New QR Session Code
To request a new pairing token and pipe it straight into a local image rendering via the terminal:
Bash
curl -X GET "http://localhost:8080/instance/connect/nail-parlor-line" \
     -H "apikey: StudioAutomationKey2026" \
     | python3 -c "import sys, json, base64; data = json.load(sys.stdin)['base64'].split(',')[1]; open('office_qr.png', 'wb').write(base64.b64decode(data))"

---

### Step 3: Push it up to GitHub
Once you save the file in VS Code, run these commands in your terminal to update your repository:

```bash
git add README.md
git commit -m "Docs: Add architecture layout and port blueprint to README"
git push origin main
