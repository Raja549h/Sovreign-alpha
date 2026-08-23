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

load_dotenv()

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
def authenticate_sheets():
    """Authenticate using service account credentials from environment."""
    import gspread
    from google.oauth2.service_account import Credentials

    if not CREDS_JSON:
        raise EnvironmentError("GOOGLE_CREDENTIALS environment variable is not set.")
    if not SHEET_ID:
        raise EnvironmentError("GOOGLE_SHEET_ID environment variable is not set.")

    creds_dict = json.loads(CREDS_JSON)
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
