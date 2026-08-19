from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI(title="Sovereign Alpha API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAW_DATA_URL = "https://raw.githubusercontent.com/Raja549h/Sovreign-alpha/main/data/daily_alpha.json"

@app.get("/api/v1/divergence")
def get_divergence_data():
    try:
        response = requests.get(RAW_DATA_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch data from source.")

@app.get("/health")
def health_check():
    return {"status": "healthy"}
