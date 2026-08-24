"""
push_to_sheets.py — Sovereign Alpha DaaS Google Sheets Push
=============================================================
Authenticates via Google Service Account (GOOGLE_CREDENTIALS env var),
fetches today's predictions and macro regime from Aiven, and writes
them directly into the configured Google Sheet.

Required environment variables:
  DATABASE_URL          — Aiven PostgreSQL connection string
  GOOGLE_CREDENTIALS    — Full JSON content of the service account key
  GOOGLE_SHEET_ID       — The target spreadsheet ID (from its URL)

Optional:
  GOOGLE_SHEET_NAME     — Worksheet tab name (default: "Daily Intelligence")
"""

import os
import json
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# override=False ensures env vars already set (e.g. by GitHub Actions)
# are NOT overwritten by .env file values — critical for GOOGLE_CREDENTIALS
# which is multi-line JSON that gets corrupted in flat .env files.
load_dotenv(override=False)

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
SHEET_ID   = os.environ.get("GOOGLE_SHEET_ID", "")
SHEET_NAME = os.environ.get("GOOGLE_SHEET_NAME", "Daily Intelligence")
DB_URL     = os.environ.get("DATABASE_URL") or os.environ.get("AIVEN_DATABASE_URL")
CREDS_JSON = os.environ.get("GOOGLE_CREDENTIALS", "")

# ─────────────────────────────────────────────
# Database helper
# ─────────────────────────────────────────────
@contextmanager
def get_conn():
    conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


def fetch_todays_predictions():
    """Return today's approved predictions from the prediction ledger."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat().replace("+00:00", "Z")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT
                timestamp,
                asset,
                sector,
                thesis,
                confidence_score,
                status
            FROM prediction_ledger
            WHERE timestamp >= %s
            ORDER BY confidence_score DESC
            """,
            (cutoff,),
        )
        return c.fetchall()


def fetch_macro_regime():
    """Return the latest market regime observation from the observations table."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat().replace("+00:00", "Z")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT ticker, headline, severity, regime_relevance, timestamp
            FROM observations
            WHERE type = 'regime_signal'
              AND timestamp >= %s
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (cutoff,),
        )
        return c.fetchone()


def fetch_todays_observations():
    """Return fresh observations from the last 24 hours."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat().replace("+00:00", "Z")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT ticker, headline, severity, timestamp
            FROM observations
            WHERE timestamp >= %s
            ORDER BY timestamp DESC
            LIMIT 20
            """,
            (cutoff,),
        )
        return c.fetchall()


# ─────────────────────────────────────────────
# Google Sheets helpers
# ─────────────────────────────────────────────
def parse_creds(raw: str) -> dict:
    """Robustly parse Google service account credentials from various string formats."""
    if not raw or not raw.strip():
        raise EnvironmentError("GOOGLE_CREDENTIALS environment variable is empty or not set.")

    raw = raw.strip()

    # If wrapped in single or double quotes, strip them
    if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
        raw = raw[1:-1].strip()

    # 1. Direct JSON parse
    try:
        data = json.loads(raw, strict=False)
        if isinstance(data, dict):
            return data
        if isinstance(data, str):
            return json.loads(data, strict=False)
    except Exception:
        pass

    # 2. Extract substring between first { and last }
    start = raw.find('{')
    end = raw.rfind('}')
    if start != -1 and end != -1 and end > start:
        candidate = raw[start:end+1]
        try:
            return json.loads(candidate, strict=False)
        except Exception:
            pass

    # 3. Base64 decode
    try:
        import base64
        decoded = base64.b64decode(raw).decode('utf-8')
        return json.loads(decoded, strict=False)
    except Exception:
        pass

    # 4. Precision regex extractor for Google Service Account fields
    import re
    extracted = {
        "type": "service_account",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
    }

    # Extract client_email
    m_email = re.search(r'client_email["\']?\s*:\s*["\']?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.iam\.gserviceaccount\.com)', raw)
    if m_email:
        extracted["client_email"] = m_email.group(1)
        extracted["client_x509_cert_url"] = f"https://www.googleapis.com/robot/v1/metadata/x509/{extracted['client_email'].replace('@', '%40')}"

    # Extract project_id
    m_proj = re.search(r'project_id["\']?\s*:\s*["\']?([a-zA-Z0-9-_]+)', raw)
    if m_proj:
        extracted["project_id"] = m_proj.group(1)

    # Extract private_key_id
    m_pkid = re.search(r'private_key_id["\']?\s*:\s*["\']?([a-f0-9]+)', raw)
    if m_pkid:
        extracted["private_key_id"] = m_pkid.group(1)

    # Extract client_id
    m_cid = re.search(r'client_id["\']?\s*:\s*["\']?([0-9]+)', raw)
    if m_cid:
        extracted["client_id"] = m_cid.group(1)

    # Extract private_key
    m_key = re.search(r'["\']?private_key["\']?\s*:\s*["\']?(-----BEGIN PRIVATE KEY-----.*?-----END PRIVATE KEY-----\\?n?)["\']?', raw, re.DOTALL)
    if m_key:
        pk = m_key.group(1).replace("\\n", "\n").strip()
        if not pk.endswith("\n"):
            pk += "\n"
        extracted["private_key"] = pk

    if "client_email" in extracted and "private_key" in extracted:
        return extracted

    preview = raw[:30] + "..." if len(raw) > 30 else raw
    raise ValueError(f"Could not parse GOOGLE_CREDENTIALS into a valid JSON dictionary (len={len(raw)}, preview={repr(preview)}).")


def authenticate_sheets():
    """Authenticate using service account credentials from environment."""
    import gspread
    from google.oauth2.service_account import Credentials

    creds_raw = os.environ.get("GOOGLE_CREDENTIALS", "")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "")

    if not creds_raw:
        raise EnvironmentError("GOOGLE_CREDENTIALS environment variable is not set.")
    if not sheet_id:
        raise EnvironmentError("GOOGLE_SHEET_ID environment variable is not set.")

    creds_dict = parse_creds(creds_raw)
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client


def get_or_create_worksheet(spreadsheet, name: str):
    """Get a worksheet by name, or create it if it doesn't exist."""
    try:
        return spreadsheet.worksheet(name)
    except Exception:
        return spreadsheet.add_worksheet(title=name, rows=1000, cols=20)


def clear_and_write(worksheet, rows: list[list]):
    """Clear the sheet and write a fresh batch of rows."""
    worksheet.clear()
    if rows:
        worksheet.update(range_name="A1", values=rows)


# ─────────────────────────────────────────────
# Build sheet payload
# ─────────────────────────────────────────────
def build_sheet_rows(predictions, regime, observations):
    """Assemble all data into a list of rows for Google Sheets."""
    now_ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    timestamp_str = now_ist.strftime("%Y-%m-%d %H:%M IST")

    rows = []

    # ── Header block ────────────────────────────────────────────────────
    rows.append(["SOVEREIGN ALPHA — DAILY INTELLIGENCE FEED"])
    rows.append([f"Generated: {timestamp_str}"])
    rows.append([""])

    # ── Macro Regime ────────────────────────────────────────────────────
    rows.append(["MACRO REGIME"])
    rows.append(["Regime", "Confidence", "Summary", "Timestamp"])
    if regime:
        rows.append([
            regime.get("regime_relevance", "N/A"),
            "--",
            regime.get("headline", "N/A"),
            str(regime.get("timestamp", ""))[:16],
        ])
    else:
        rows.append(["No regime data available for today", "", "", ""])

    rows.append([""])

    # ── Predictions ─────────────────────────────────────────────────────
    rows.append(["TODAY'S PREDICTIONS"])
    rows.append(["Timestamp", "Asset", "Sector", "Confidence %", "Status", "Thesis"])
    if predictions:
        for p in predictions:
            conf = p.get("confidence_score")
            conf_str = f"{float(conf):.1f}%" if conf is not None else "N/A"
            rows.append([
                str(p.get("timestamp", ""))[:16],
                p.get("asset", ""),
                p.get("sector", ""),
                conf_str,
                p.get("status", ""),
                str(p.get("thesis", ""))[:200],
            ])
    else:
        rows.append(["No predictions generated today", "", "", "", "", ""])

    rows.append([""])
    rows.append([f"Total Predictions: {len(predictions)}"])
    rows.append([""])

    # ── Observations ─────────────────────────────────────────────────────
    rows.append(["TODAY'S OBSERVATIONS"])
    rows.append(["Timestamp", "Ticker", "Severity", "Headline"])
    if observations:
        for o in observations:
            rows.append([
                str(o.get("timestamp", ""))[:16],
                o.get("ticker", ""),
                o.get("severity", ""),
                str(o.get("headline", ""))[:200],
            ])
    else:
        rows.append(["No new observations detected today", "", "", ""])

    return rows


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    if not DB_URL:
        print("[FATAL] DATABASE_URL or AIVEN_DATABASE_URL is not set.")
        sys.exit(1)

    print("[1/4] Fetching data from Aiven database...")
    predictions  = fetch_todays_predictions()
    regime       = fetch_macro_regime()
    observations = fetch_todays_observations()

    print(f"      Predictions: {len(predictions)}")
    print(f"      Regime: {regime.get('regime_relevance', 'N/A') if regime else 'None'}")
    print(f"      Observations: {len(observations)}")

    print("[2/4] Authenticating with Google Sheets...")
    client      = authenticate_sheets()
    spreadsheet = client.open_by_key(SHEET_ID)
    worksheet   = get_or_create_worksheet(spreadsheet, SHEET_NAME)
    print(f"      Connected to spreadsheet: {spreadsheet.title} → tab: {SHEET_NAME}")

    print("[3/4] Building and writing data to sheet...")
    rows = build_sheet_rows(predictions, regime, observations)
    clear_and_write(worksheet, rows)
    print(f"      Written {len(rows)} rows successfully.")

    print("[4/4] Push complete.")
    print(f"      Sheet URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}")


if __name__ == "__main__":
    main()
