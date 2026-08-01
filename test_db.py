from dotenv import load_dotenv; load_dotenv()
from dashboard.gateway import get_connection as db_get_connection
import traceback

try:
    conn = db_get_connection()
    c = conn.cursor()
    c.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'veto_archive' AND column_name = 'veto_correct'")
    row = c.fetchone()
    print("Type:", row)
except Exception as e:
    traceback.print_exc()
