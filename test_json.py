import config, json
from database import get_connection
conn = get_connection()
if conn:
    c = conn.cursor()
    sql = """
        SELECT et.*, om.observation_text, c.ticker 
        FROM (SELECT * FROM evidence_timeline WHERE event_type NOT ILIKE ANY(ARRAY['%%test%%', '%%simulated%%', '%%stress%%', '%%verification%%', '%%e2e%%']) AND created_at >= '2026-01-01' ORDER BY created_at DESC LIMIT %s) et
        LEFT JOIN observation_memory om ON om.id = et.observation_id
        LEFT JOIN companies c ON c.id = et.company_id
        ORDER BY et.created_at DESC
    """
    try:
        c.execute(sql, [2])
        rows = [dict(r) for r in c.fetchall()]
        print('JSON:', json.dumps(rows)[:100])
    except Exception as e:
        import traceback
        traceback.print_exc()
