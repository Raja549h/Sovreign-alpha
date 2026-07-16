import config
from database import get_connection
conn = get_connection()
if conn:
    c = conn.cursor()
    sql = """
        SELECT * FROM evidence_timeline 
        WHERE event_type NOT ILIKE ANY(ARRAY['%%test%%', '%%simulated%%', '%%stress%%', '%%verification%%', '%%e2e%%'])
        LIMIT %s
    """
    try:
        c.execute(sql, [2])
        print('SUCCESS:', len(c.fetchall()))
    except Exception as e:
        print('ERROR:', e)
