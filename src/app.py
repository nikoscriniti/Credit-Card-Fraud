# src/app.py
import os
import io
import json
from typing import List


import boto3
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---- Config (env) ----
S3_BUCKET = os.getenv("S3_BUCKET", "nikos-fraud-artifacts-2025")
ARTIFACT_PREFIX = os.getenv("ARTIFACT_PREFIX", "artifacts/")
API_KEY = os.getenv("API_KEY", "demo123")

EXPECTED_FEATURES = 30

# ---- Globals ----
_threshold: float = 0.5

# ---- AWS clients ----
s3 = boto3.client("s3")

# ---- App ----
app = FastAPI()

# CORS for your React app (lock down in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://api.nikosfraudapp.com"],  # replace later when you host the UI
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Startup: load threshold from S3 ----
def _load_threshold_from_s3() -> float:
    key = ARTIFACT_PREFIX.rstrip("/") + "/threshold.json"
    buf = io.BytesIO()
    s3.download_fileobj(S3_BUCKET, key, buf)
    buf.seek(0)
    raw = buf.read().decode("utf-8").strip()
    data = json.loads(raw)
    # Accept either a raw number, {"threshold": x}, or {"t": x}
    if isinstance(data, dict):
        if "threshold" in data:
            return float(data["threshold"])
        if "t" in data:
            return float(data["t"])
        raise RuntimeError(f"threshold.json missing key; got {data!r}")
    return float(data)

@app.on_event("startup")
def on_startup():
    global _threshold
    _threshold = _load_threshold_from_s3()

# ---- Schemas ----
class ScoreRequest(BaseModel):
    features: List[float]

# ---- Routes ----
@app.get("/health")
def health():
    return {
        "ok": True,
        "bucket": S3_BUCKET,
        "prefix": ARTIFACT_PREFIX,
        "threshold": _threshold,
        "expected_features": EXPECTED_FEATURES,
    }

@app.post("/score")
def score(req: ScoreRequest, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    if len(req.features) != EXPECTED_FEATURES:
        raise HTTPException(
            status_code=400,
            detail=f"Expected {EXPECTED_FEATURES} features, got {len(req.features)}",
        )
    # Simple placeholder scoring: average -> small probability
    prob = sum(req.features) / (EXPECTED_FEATURES * 100.0)
    is_fraud = 1 if prob >= _threshold else 0
    return {"probability": prob, "is_fraud": is_fraud, "threshold": _threshold}
