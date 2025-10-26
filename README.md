# Credit Card Fraud Scorer (XGBoost + FastAPI + React + AWS)

# Production-ready demo that scores credit-card transactions for fraud.
# CSV file on Github (to test)
# Samples at button to show 

**Live endpoints:**
- API: https://api.nikosfraudapp.com
- Frontend: https://nikosfraudapp.com

---

## Overview

This project demonstrates an end-to-end machine learning deployment:
- Model: XGBoost trained offline, artifacts stored in S3.
- Backend: FastAPI container on ECS Fargate, image stored in ECR.
- Networking: Application Load Balancer with ACM TLS certificate and Route 53 DNS.
- Frontend: React (Vite) app hosted on S3 + CloudFront.
- Security: API key header, IAM least-privilege roles, security groups.
- Ops: CloudWatch logs and AWS Budgets alerts.

---

## Architecture

```mermaid
flowchart LR
    subgraph CloudFront
      CF[CloudFront (ACM cert)] --> S3Site[(S3 Static Website Bucket)]
    end

    subgraph VPC
      ALB[Application Load Balancer (HTTPS)] --> TG[(Target Group)]
      TG --> ECS[Amazon ECS Fargate Task (FastAPI)]
    end

    S3Artifacts[(S3 Artifacts Bucket: model.pkl, threshold.json)] --> ECS

    Browser -->|GET| CF
    Browser -->|POST /score + X-API-Key| ALB
```

---

## Repository Structure

```
.
├── src/
│   ├── app.py                 # FastAPI service (GET /health, POST /score)
│   └── artifacts/             # local copies for dev
├── scripts/train.py           # trains XGBoost and saves model/threshold
├── docker/
│   └── Dockerfile             # API container
├── frontend/                  # Vite/React app
│   └── ...
└── README.md
```

---

## API

### Health

```
GET https://api.nikosfraudapp.com/health
```

Response:
```json
{
  "ok": true,
  "bucket": "nikos-fraud-artifacts-2025",
  "prefix": "artifacts/",
  "threshold": 0.4574,
  "expected_features": 30
}
```

### Score

```
POST https://api.nikosfraudapp.com/score
```

Headers:
```
Content-Type: application/json
X-API-Key: demo123
```

Request body:
```json
{ "features": [30 numeric values matching (Time, V1..V28, Amount)] }
```

Response:
```json
{ "probability": 0.12345, "is_fraud": 0, "threshold": 0.4574 }
```

Quick test:
```bash
curl -s -X POST "https://api.nikosfraudapp.com/score"   -H "Content-Type: application/json" -H "X-API-Key: demo123"   -d '{"features":[0.0,-1.2,0.3,0.1,-0.7,1.1,-0.2,0.05,-0.3,0.8,-0.4,0.6,-0.9,0.2,0.0,0.15,-0.25,0.35,-0.12,0.44,-0.05,0.27,-0.63,0.09,-0.18,0.22,-0.31,0.13,0.77,12.50]}'
```

---

## Security Notes

- ECS task role: read-only access to S3 artifacts bucket.
- ECS task security group: inbound 8000 only from ALB SG.
- ALB: HTTP port 80 redirects to HTTPS (443) with ACM cert.
- Frontend uses API key header. Real deployments should use secrets or auth.

---

## Deployment Flow

### Train model
```bash
python scripts/train.py
```
Uploads model.pkl and threshold.json to S3.

### Build backend container
```bash
docker build -t fraud-api .
docker push <ECR_URI>:latest
```

### ECS Fargate service
- Uses ECR image.
- Env vars: S3_BUCKET, ARTIFACT_PREFIX, API_KEY.
- Logs to CloudWatch.

### ALB
- Listeners: 80 (HTTP) redirect, 443 (HTTPS).
- Target group pointing to ECS.

### Frontend
```bash
npm run build
aws s3 sync dist/ s3://<your-site-bucket>/
aws cloudfront create-invalidation --distribution-id <CF_DIST_ID> --paths "/*"
```

---

## Operations

- Logs: CloudWatch (`aws logs tail /ecs/fraud-api --since 5m --follow`)
- ALB target health: must show "healthy"
- Budgets: $5 monthly guardrail alert email
- Costs: S3 pennies, ECS/ALB a few dollars/month if left running

---

## Resume Highlights

- Built **end-to-end ML system**: XGBoost + FastAPI + React + AWS.
- Production-grade infra: ECS Fargate, ALB, ACM certs, Route 53 DNS, CloudFront.
- Secure deployment: API key auth, IAM least privilege, SG lockdown.
- CI-style workflow: Dockerized backend, artifacts in S3, static frontend in S3+CF.




# Sample  1  (copy 30)
0,-1.3598071336738,-0.0727811733098497,2.53634673796914,1.37815522427443,-0.338320769942518,0.462387777762292,0.239598554061257,0.0986979012610507,0.363786969611213,0.0907941719789316,-0.551599533260813,-0.617800855762348,-0.991389847235408,-0.311169353699879,1.46817697209427,-0.470400525259478,0.207971241929242,0.0257905801985591,0.403992960255733,0.251412098239705,-0.018306777944153,0.277837575558899,-0.110473910188767,0.0669280749146731,0.128539358273528,-0.189114843888824,0.133558376740387,-0.0210530534538215,149.62


# Sample 2 
0,1.19185711131486,0.26615071205963,0.16648011335321,0.448154078460911,0.0600176492822243,-0.0823608088155687,-0.0788029833323113,0.0851016549148104,-0.255425128109186,-0.166974414004614,1.61272666105479,1.06523531137287,0.48909501589608,-0.143772296441519,0.635558093258208,0.463917041022171,-0.114804663102346,-0.183361270123994,-0.145783041325259,-0.0690831352230203,-0.225775248033138,-0.638671952771851,0.101288021253234,-0.339846475529127,0.167170404418143,0.125894532368176,-0.00898309914322813,0.0147241691924927,2.69

# sample 3
36,-1.00492933857661,-0.985977681437715,-0.0380388289597724,3.71006135915003,-6.63195083213121,5.12210258142297,4.37169125592055,-2.00686750606648,-0.278736460739287,-0.230872923441907,0.145155263239837,-0.0631560504596301,-0.79958507056403,-0.341956368039262,-0.930529781903999,0.510510185482595,0.0924281060557055,0.823984132238812,1.19039780013038,-0.00197997769185823,1.39340600409007,-0.381671395166542,0.969719175646086,0.0194447958389348,0.57092281345927,0.333277781691674,0.857373192365587,-0.0755382461617961,1402.95

