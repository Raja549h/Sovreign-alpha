import os
from dashboard.gateway import get_db_connection

def purge_test():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM prediction_ledger WHERE thesis ILIKE '%test%' OR asset ILIKE '%test%' OR thesis ILIKE '%stress%' OR asset ILIKE '%stress%' OR thesis ILIKE '%demo%' OR asset ILIKE '%demo%'")
            print("Purged prediction_ledger:", c.rowcount)
            c.execute("DELETE FROM observations WHERE observation_text ILIKE '%test%' OR observation_text ILIKE '%stress%' OR observation_text ILIKE '%demo%'")
            print("Purged observations:", c.rowcount)
            c.execute("DELETE FROM veto_archive WHERE asset ILIKE '%test%' OR asset ILIKE '%demo%'")
            print("Purged veto_archive:", c.rowcount)
            conn.commit()
    except Exception as e:
        print(f"Error purging: {e}")

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    purge_test()
