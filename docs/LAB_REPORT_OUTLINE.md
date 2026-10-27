# Lab Report Outline – Hospital Management System on the Cloud

1. **Aim** – Design, containerise and deploy a Hospital Management System on a cloud platform.
2. **Problem statement** – Hospitals need accessible, scalable, always-available systems for patients, doctors, appointments and billing.
3. **Why cloud?** – On-demand resources, pay-as-you-go, high availability, easy scaling, global access, managed backups.
4. **System modules** – Dashboard, Patient mgmt, Doctor mgmt, Appointment scheduling (with clash detection), Billing, REST API, Health check.
5. **Architecture** – Browser → Load Balancer → Container (Flask + Gunicorn) → Persistent volume / managed DB.
6. **Technology stack** – Python 3.12, Flask, SQLite, Gunicorn, Docker, Kubernetes, GitHub Actions, AWS/GCP/Azure.
7. **Database schema** – patients, doctors, appointments(FK→patients, doctors), bills(FK→patients).
8. **REST endpoints** – `GET /health`, `GET /api/stats`, `GET|POST /api/patients`, `GET /api/doctors`, `GET /api/appointments`.
9. **Deployment steps** – paste screenshots: docker build, docker run, cloud console (instance/service), running app URL.
10. **Testing** – `pytest` results (4 tests), manual test cases.
11. **Cloud service model mapping** – IaaS (EC2), PaaS (Cloud Run/App Service), Containers/Orchestration (K8s).
12. **Security & scalability discussion** – see docs/CLOUD_DEPLOYMENT.md table.
13. **Limitations & future work** – add login/roles, PostgreSQL, HTTPS, auto-scaling, SMS/email reminders, S3 storage for medical reports.
14. **Conclusion**.
