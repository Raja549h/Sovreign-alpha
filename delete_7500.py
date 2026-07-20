import sys
sys.path.insert(0, 'C:/Users/lokes/Downloads/project/sovereign-alpha')
from dotenv import load_dotenv
load_dotenv()
from dashboard.gateway import get_connection, init_pool

def delete_7500_days():
    init_pool()
    conn = get_connection()
    c = conn.cursor()
    # Check if there are any rows with expected_timeline_days >= 7000
    c.execute("SELECT expected_timeline_days FROM prediction_ledger WHERE expected_timeline_days >= 7000")
    print("Found >7000:", c.fetchall())
    
    # Or maybe it's in veto_archive?
    c.execute("SELECT expected_timeline_days FROM veto_archive WHERE expected_timeline_days >= 7000")
    print("Found >7000 in veto_archive:", c.fetchall())

    pass # conn.close()

if __name__ == '__main__':
    delete_7500_days()
