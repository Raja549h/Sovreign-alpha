import psycopg2, os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()
conn = psycopg2.connect(os.environ['NEON_URL'])
c = conn.cursor()

# C1: Add TRENT
try:
    c.execute("INSERT INTO companies (ticker, company_name, sector) VALUES ('TRENT', 'Trent Ltd', 'Retail') ON CONFLICT DO NOTHING")
    print("Inserted TRENT into companies.")
except Exception as e:
    print("Error inserting TRENT:", e)

# C2: Add short-term prediction for TRENT
try:
    now = datetime.now(timezone.utc)
    ts = now.isoformat()
    # If the schema doesn't have review_date, we just use expected_timeline_days = 30
    c.execute("""
        INSERT INTO prediction_ledger 
        (prediction_id, timestamp, asset, sector, thesis, confidence_score, status, proof_hash, expected_timeline_days, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, ('PRED-TRENT-ST-001', ts, 'TRENT', 'Retail', 'Apparel segment margin expansion to offset Zudio growth normalization. Short-term verifiable within 30 days.', 0.8, 'cleared', '0xtrent123', 30, ts, ts))
    print("Inserted TRENT prediction.")
except Exception as e:
    print("Error inserting TRENT prediction:", e)

# C4: Create data_gaps table
try:
    c.execute("""
        CREATE TABLE IF NOT EXISTS data_gaps (
            id SERIAL PRIMARY KEY,
            gap_description TEXT,
            impact TEXT,
            recommended_source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created data_gaps table.")
    
    # Insert the gap
    c.execute("""
        INSERT INTO data_gaps (gap_description, impact, recommended_source)
        VALUES ('Branch-level deposit rates for HDFC Bank', 'Medium', 'RBI OSMOS or bank investor presentations')
    """)
    print("Inserted data gap.")
except Exception as e:
    print("Error creating data_gaps:", e)

conn.commit()
c.close()
conn.close()
