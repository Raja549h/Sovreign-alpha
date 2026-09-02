import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv(override=True)

DB_URL = os.environ.get("DATABASE_URL") or os.environ.get("AIVEN_DATABASE_URL")
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
SHEET_NAME = os.environ.get("GOOGLE_SHEET_NAME", "Daily Feed")

def fetch_todays_predictions():
    conn = psycopg2.connect(DB_URL)
    c = conn.cursor(cursor_factory=RealDictCursor)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    c.execute("SELECT * FROM prediction_ledger WHERE timestamp >= %s ORDER BY timestamp DESC", (cutoff,))
    rows = c.fetchall()
    conn.close()
    return rows

def fetch_macro_regime():
    conn = psycopg2.connect(DB_URL)
    c = conn.cursor(cursor_factory=RealDictCursor)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    c.execute("SELECT * FROM observations WHERE type = 'regime_signal' AND timestamp >= %s ORDER BY timestamp DESC LIMIT 1", (cutoff,))
    row = c.fetchone()
    conn.close()
    return row

def fetch_todays_observations():
    conn = psycopg2.connect(DB_URL)
    c = conn.cursor(cursor_factory=RealDictCursor)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    c.execute("SELECT * FROM observations WHERE type != 'regime_signal' AND timestamp >= %s ORDER BY timestamp DESC LIMIT 20", (cutoff,))
    rows = c.fetchall()
    conn.close()
    return rows

def authenticate_sheets():
    import gspread
    from google.oauth2.service_account import Credentials
    creds_raw = os.environ.get("GOOGLE_CREDENTIALS", "")
    if not creds_raw:
        raise EnvironmentError("GOOGLE_CREDENTIALS environment variable is not set.")
    
    # Parse creds correctly with json.loads and replace newline
    creds_dict = json.loads(creds_raw.replace("\\\\n", "\\n").replace("\\n", "\n"))
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def get_or_create_worksheet(spreadsheet, name: str):
    import gspread
    try:
        return spreadsheet.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=name, rows=1000, cols=20)

def clear_and_write(worksheet, rows: list):
    worksheet.clear()
    if rows:
        worksheet.update(range_name="A1", values=rows)

def build_sheet_rows(predictions, regime, observations):
    now_ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    timestamp_str = now_ist.strftime("%Y-%m-%d %H:%M IST")
    rows = [["SOVEREIGN ALPHA - DAILY INTELLIGENCE FEED"], [f"Generated: {timestamp_str}"], [""]]
    rows.extend([["MACRO REGIME"], ["Regime", "Confidence", "Summary", "Timestamp"]])
    if regime:
        rows.append([regime.get("regime_relevance", "N/A"), "--", regime.get("headline", "N/A"), str(regime.get("timestamp", ""))[:16]])
    else:
        rows.append(["No regime data available for today", "", "", ""])
    rows.extend([[""], ["TODAY'S PREDICTIONS"], ["Timestamp", "Asset", "Sector", "Confidence %", "Status", "Thesis"]])
    if predictions:
        for p in predictions:
            conf = p.get("confidence_score")
            conf_str = f"{float(conf):.1f}%" if conf is not None else "N/A"
            rows.append([str(p.get("timestamp", ""))[:16], p.get("asset", ""), p.get("sector", ""), conf_str, p.get("status", ""), str(p.get("thesis", ""))[:200]])
    else:
        rows.append(["No predictions generated today", "", "", "", "", ""])
    rows.extend([[""], [f"Total Predictions: {len(predictions)}"], [""]])
    rows.extend([["TODAY'S OBSERVATIONS"], ["Timestamp", "Ticker", "Severity", "Headline"]])
    if observations:
        for o in observations:
            rows.append([str(o.get("timestamp", ""))[:16], o.get("ticker", ""), o.get("severity", ""), str(o.get("headline", ""))[:200]])
    else:
        rows.append(["No new observations detected today", "", "", ""])
    return rows

def main():
    if not DB_URL:
        print("[FATAL] DATABASE_URL or AIVEN_DATABASE_URL is not set.")
        sys.exit(1)
    predictions  = fetch_todays_predictions()
    regime       = fetch_macro_regime()
    observations = fetch_todays_observations()
    client      = authenticate_sheets()
    
    # Open by KEY instead of name
    spreadsheet = client.open_by_key(SHEET_ID)
    worksheet   = get_or_create_worksheet(spreadsheet, SHEET_NAME)
    
    rows = build_sheet_rows(predictions, regime, observations)
    clear_and_write(worksheet, rows)
    print(f"[SUCCESS] Wrote data to row {len(worksheet.get_all_values())} in tab 'Daily Intelligence' at {datetime.now()}")

if __name__ == '__main__':
    main()
