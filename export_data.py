import os
import pandas as pd
import psycopg2

def export_latest_data():
    db_url = os.environ.get('AIVEN_DATABASE_URL') or os.environ.get('DATABASE_URL')
    if not db_url:
        print("Error: Database URL not found.")
        return

    print("Connecting to database...")
    try:
        conn = psycopg2.connect(db_url)
        query = """
        SELECT asset as ticker, status as signal, confidence_score as confidence, thesis, timestamp
        FROM prediction_ledger
        ORDER BY timestamp DESC
        LIMIT 100
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        os.makedirs('data', exist_ok=True)
        
        csv_path = 'data/daily_alpha.csv'
        json_path = 'data/daily_alpha.json'
        
        df.to_csv(csv_path, index=False)
        df.to_json(json_path, orient='records', indent=4)
        
        print(f"Successfully exported {len(df)} records to {csv_path} and {json_path}")
    except Exception as e:
        print(f"Failed to export data: {e}")

if __name__ == "__main__":
    export_latest_data()
