import os
import sys

sys.path.insert(0, os.path.abspath('.'))
from dotenv import load_dotenv
load_dotenv()
from database import get_connection

def clean_test_data():
    conn = get_connection()
    c = conn.cursor()
    
    # Identify test records
    c.execute("SELECT id, ticker FROM companies WHERE ticker LIKE '%TEST%' OR ticker LIKE '%DEMO%' OR ticker LIKE '%PLACEHOLDER%'")
    companies = c.fetchall()
    print("Test Companies:", companies)
    
    c.execute("SELECT id, asset FROM prediction_ledger WHERE asset LIKE '%TEST%' OR asset LIKE '%DEMO%'")
    predictions = c.fetchall()
    print("Test Predictions:", predictions)

    c.execute("SELECT id, ticker FROM observations WHERE ticker LIKE '%TEST%' OR ticker LIKE '%DEMO%'")
    observations = c.fetchall()
    print("Test Observations:", observations)
    
    # Delete test records
    c.execute("DELETE FROM companies WHERE ticker LIKE '%TEST%' OR ticker LIKE '%DEMO%' OR ticker LIKE '%PLACEHOLDER%'")
    c.execute("DELETE FROM prediction_ledger WHERE asset LIKE '%TEST%' OR asset LIKE '%DEMO%' OR asset LIKE '%PLACEHOLDER%'")
    c.execute("DELETE FROM observations WHERE ticker LIKE '%TEST%' OR ticker LIKE '%DEMO%' OR ticker LIKE '%PLACEHOLDER%'")
    pass
    
    conn.commit()
    print("Test records cleaned.")
    
def get_data_density():
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT count(*) FROM research_notes")
    notes = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM observations")
    obs = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM prediction_ledger")
    preds = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM analysis_run_events")
    events = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM observations WHERE is_validated = TRUE")
    validations = c.fetchone()[0]
    
    print(f"\n--- DATA DENSITY ---")
    print(f"Research Notes: {notes} (Target: 50+)")
    print(f"Observations: {obs} (Target: 100+)")
    print(f"Predictions: {preds}")
    print(f"Events: {events} (Target: 200+)")
    print(f"Validations: {validations} (Target: 100+)")

if __name__ == '__main__':
    clean_test_data()
    get_data_density()
