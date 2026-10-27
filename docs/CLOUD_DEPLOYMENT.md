# Cloud Deployment Guide

The app is a stateless-config, containerised service. Pick ONE option below for your lab.

## Option A – Render (persistent SQLite)
1. Push this project to a GitHub repository.
2. In the Render Dashboard, choose **New → Blueprint**, connect the repository, and select `render.yaml`.
3. Review the paid Starter web service and persistent disk, then apply the Blueprint.
4. Open the Render URL shown for the service. Render checks `/health` after deploy.

The Blueprint generates `SECRET_KEY` and mounts a 1 GiB persistent disk at `/data`, where the SQLite database is stored. Keep one app instance when using SQLite; use PostgreSQL before scaling to multiple instances.

## 0. Build & test locally
```bash
docker build -t hms:1.0 .
docker run -p 8080:8080 -v hms-data:/data hms:1.0
# open http://localhost:8080   | health: http://localhost:8080/health
```

## Option B – AWS EC2 (IaaS) – simplest for labs
1. Launch an EC2 instance (Amazon Linux 2023, t2.micro free tier). Security group: allow TCP 22 and 8080.
2. SSH in and install Docker:
   ```bash
   sudo dnf install -y docker git && sudo systemctl enable --now docker
   sudo usermod -aG docker ec2-user && newgrp docker
   ```
3. Copy project (git clone / scp), then:
   ```bash
   docker build -t hms:1.0 .
   docker run -d --restart=always -p 8080:8080 -v hms-data:/data -e SECRET_KEY=$(openssl rand -hex 16) hms:1.0
   ```
4. Visit `http://<EC2-PUBLIC-IP>:8080`.

## Option C – Google Cloud Run (serverless containers / PaaS)
```bash
gcloud auth login && gcloud config set project YOUR_PROJECT
gcloud run deploy hms --source . --region asia-south1 --allow-unauthenticated --port 8080
```
Note: Cloud Run's disk is ephemeral. Use Cloud SQL (PostgreSQL) for permanent data (see "Scaling" below).

## Option D – Azure Container Apps / App Service
```bash
az group create -n hms-rg -l centralindia
az acr create -g hms-rg -n <uniqueacr> --sku Basic
az acr build -r <uniqueacr> -t hms:1.0 .
az containerapp up -n hms -g hms-rg --image <uniqueacr>.azurecr.io/hms:1.0 --target-port 8080 --ingress external
```

## Option E – Kubernetes (Minikube / EKS / GKE / AKS)
```bash
minikube start
eval $(minikube docker-env) && docker build -t hms:1.0 .
sed -i 's#YOUR_REGISTRY/hms:1.0#hms:1.0#' k8s/deployment.yaml
# add imagePullPolicy: Never under the container when using Minikube local image
kubectl create secret generic hms-secret --from-literal=SECRET_KEY=$(openssl rand -hex 16)
kubectl apply -f k8s/deployment.yaml
minikube service hms        # opens the app
kubectl get pods,svc
```

## Scaling & production notes (good for viva)
| Concern | Lab setup | Production approach |
|---|---|---|
| Database | SQLite file on a volume | Amazon RDS / Cloud SQL / Azure DB for PostgreSQL |
| Scaling | 1 replica | Multiple replicas behind a Load Balancer + Auto Scaling |
| Secrets | env var | AWS Secrets Manager / Key Vault / K8s Secrets |
| Monitoring | `/health` endpoint | CloudWatch / Cloud Monitoring / Prometheus |
| Security | HTTP, no login | HTTPS (ACM/Let's Encrypt), authentication (JWT/OAuth), IAM roles |
| Backups | manual | Automated DB snapshots |
| CI/CD | GitHub Actions test + build | Push image to ECR/GCR/ACR and auto-deploy |

## Cloud concepts demonstrated
IaaS (EC2) · PaaS/serverless containers (Cloud Run, Container Apps) · Containerisation (Docker) · Orchestration (Kubernetes) · Elasticity & load balancing · Health checks · 12-factor config · CI/CD.
