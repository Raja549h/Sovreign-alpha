import psycopg2, os
from dotenv import load_dotenv
from datetime import datetime, timezone
load_dotenv()
conn = psycopg2.connect(os.environ['NEON_URL'])
c = conn.cursor()

timestamp = datetime.now(timezone.utc).isoformat()

# Insert observations (already inserted partially? Wait, let's check if the first transaction committed. No, conn.commit() was at the end, so nothing inserted.)
obs = [
    ('HDFCBANK', 'HDFC Bank Limited', 'forensic_flag', 'LCR Dropped Below Guidance', 'MEDIUM', 'Q4 FY26 reported LCR (Liquidity Coverage Ratio) dropped to 110% from 115% QoQ, despite management guidance of maintaining >115%. Deposit mobilization cost increased by 15bps.', 'High Rates', timestamp),
    ('BAJFINANCE', 'Bajaj Finance Limited', 'macro_divergence', 'B2B Acquisition Slowdown', 'HIGH', 'New customer acquisition velocity in B2B segment slowed by 12% YoY in April 2026, contradicting the 20% growth guidance given in the Q4 call. Stage 2 assets ticked up by 25bps.', 'Consumption Slowdown', timestamp)
]

c.executemany("INSERT INTO observations (ticker, company, type, headline, severity, supporting_data, regime_relevance, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", obs)

# Insert predictions
preds = [
    ('PRED-HDFC-202606', timestamp, 'HDFCBANK', 'Financials', 'NIM to compress by at least 10bps in Q1 FY27 due to higher cost of funds required to support CD ratio.', 0.85, 'cleared', '0x123abc', 90, timestamp, timestamp),
    ('PRED-BAJ-202606', timestamp, 'BAJFINANCE', 'Financials', 'Credit costs to exceed management guidance of 1.7% by at least 20bps (hitting >1.9%) in H1 FY27 due to unsecured loan stress.', 0.75, 'cleared', '0x456def', 180, timestamp, timestamp)
]

c.executemany("INSERT INTO prediction_ledger (prediction_id, timestamp, asset, sector, thesis, confidence_score, status, proof_hash, expected_timeline_days, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", preds)

conn.commit()
print("Cycle 1 DB Injection Complete")
