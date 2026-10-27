# 🏥 Hospital Management System – Cloud Computing Lab Project

A cloud-ready Hospital Management System (Flask + SQLite) packaged with Docker, Kubernetes manifests,
CI pipeline and deployment guides for AWS / GCP / Azure.

## Features
- Dashboard with live statistics (patients, doctors, appointments, revenue, unpaid bills)
- Patient management (add, search, delete)
- Doctor management (specialization, fees)
- Appointment booking with **double-booking prevention**, status updates (Scheduled/Completed/Cancelled)
- Billing: generate bills, mark as paid
- JSON REST API and `/health` endpoint for load balancers / Kubernetes probes

## Project structure
```
app.py                  Flask application + REST API
templates/ static/      UI
tests/test_app.py       pytest tests
Dockerfile              container image
docker-compose.yml      one-command local run
k8s/deployment.yaml     Kubernetes Deployment + PVC + Service
render.yaml             Render Blueprint with persistent SQLite disk
.github/workflows/      CI (tests + docker build)
docs/CLOUD_DEPLOYMENT.md   AWS / GCP / Azure / K8s steps
docs/LAB_REPORT_OUTLINE.md report/viva structure
```

## Run locally (no Docker)
```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                                        # http://localhost:5000
```

## Run with Docker
```bash
docker compose up --build                            # http://localhost:8080
```

## Run tests
```bash
python -m pytest -q tests
```

## Deploy to the cloud
See **docs/CLOUD_DEPLOYMENT.md**.

## Configuration (environment variables)
| Variable | Default | Purpose |
|---|---|---|
| `PORT` | 5000 (8080 in Docker) | listen port |
| `DB_PATH` | hms.db (/data/hms.db in Docker) | database file location |
| `SECRET_KEY` | dev value | Flask session/flash secret – **change in production** |
