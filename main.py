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

import json
from fastapi.responses import FileResponse

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Sovereign Alpha DaaS API",
        "status": "Online",
        "endpoints": {
            "divergence_json": "/api/v1/divergence",
            "divergence_csv": "/api/v1/divergence/csv",
            "health": "/health"
        }
    }

@app.get("/api/v1/divergence")
def get_divergence_data():
    try:
        with open("data/daily_alpha.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Data file not found. Ensure pipeline has run.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to read data from source.")

@app.get("/api/v1/divergence/csv")
def get_divergence_csv():
    try:
        return FileResponse("data/daily_alpha.csv", media_type="text/csv", filename="daily_alpha.csv")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to read CSV data from source.")

@app.get("/health")
def health_check():
    return {"status": "healthy"}
