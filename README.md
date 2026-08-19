---
title: Sovereign Alpha
emoji: 📈
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

<div align="center">

# Sovereign Alpha: NLP Data-as-a-Service for Quantitative Finance

**Next-Generation Algorithmic Trading and Indian Equities NLP**

*Identify variant perception. Quantify hidden risk. Capture non-consensus alpha using Mistral Large.*

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Serverless-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![OpenBB](https://img.shields.io/badge/OpenBB-Integration-FFFFFF?style=for-the-badge)](https://openbb.co)

</div>

## Overview

Sovereign Alpha is a passive **Data-as-a-Service (DaaS)** distribution engine designed exclusively for **Quantitative Finance** and **Algorithmic Trading**. Utilizing advanced NLP pipelines, Sovereign Alpha extracts divergence metrics, high-conviction signals, and thesis tracking specifically tailored for **Indian Equities NLP**.

Our dual-engine pipeline guarantees robust data processing and seamless distribution:
1. **The Data Engine**: A fully automated GitHub Actions workflow (`daily_sync.yml`) queries our proprietary database and publishes raw JSON and CSV data daily.
2. **The Distribution Engine**: A serverless FastAPI backend serving real-time prediction data straight to OpenBB and institutional terminals.

## Data Endpoints

- **FastAPI Endpoint**: `https://svrn-alpha-sovereignalpha.hf.space/api/v1/divergence`
- **Raw CSV Data**: `https://raw.githubusercontent.com/Raja549h/Sovreign-alpha/main/data/daily_alpha.csv`
- **Raw JSON Data**: `https://raw.githubusercontent.com/Raja549h/Sovreign-alpha/main/data/daily_alpha.json`

## Jupyter Notebook / OpenBB Integration

Quants and data scientists can load our daily alpha signals natively into their research environments. Here is a Python snippet demonstrating how to ingest the raw CSV directly into pandas for algorithmic trading backtesting:

```python
import pandas as pd

# Direct URL to the raw CSV data published by Sovereign Alpha
csv_url = "https://raw.githubusercontent.com/Raja549h/Sovreign-alpha/main/data/daily_alpha.csv"

# Load data into DataFrame
df = pd.read_csv(csv_url)

# Display the highest conviction divergence signals
high_conviction = df[df['confidence'] >= 0.85]
print(high_conviction[['ticker', 'signal', 'confidence']])
```

## System Architecture

- **Backend Framework:** FastAPI / Uvicorn
- **Automation:** GitHub Actions (Daily Cron Sync)
- **Database Architecture:** Aiven PostgreSQL
- **LLM Engine:** Mistral AI (mistral-large-latest)
