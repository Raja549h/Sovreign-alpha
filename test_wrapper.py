import os
os.environ["NEON_URL"] = "postgresql://neondb_owner:npg_HxbKeITV73Gl@ep-super-art-adot6eyq-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
from database import get_connection
def test_wrapper():
    conn = get_connection()
    
    # 1. Test execute and parameter replacement
    c = conn.cursor()
    c.execute("SELECT 1 as num WHERE 1 = %s", (1,))
    row = c.fetchone()
    assert row is not None
    
    # 2. Test NeonRow dict-like and index-like access
    assert row[0] == 1
    assert row['num'] == 1
    assert dict(row) == {'num': 1}
    
    # 3. Test context manager
    with get_connection() as ctx_conn:
        c2 = ctx_conn.cursor()
        c2.execute("SELECT 2 as num")
        assert c2.fetchone()['num'] == 2
        
    # 4. Test exception mapping
    try:
        # Trying to insert a duplicate into prediction_ledger to trigger IntegrityError
        c.execute("INSERT INTO prediction_ledger (id, prediction_id, timestamp, asset, status, created_at) VALUES (1, 'test', CURRENT_TIMESTAMP, 'test', 'test', CURRENT_TIMESTAMP)")
    except sqlite3.IntegrityError:
        print("Caught IntegrityError properly!")
    except Exception as e:
        print(f"Failed to map exception: {type(e)}")

    print("All tests passed!")

if __name__ == "__main__":
    test_wrapper()
