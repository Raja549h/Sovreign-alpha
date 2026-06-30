import sys
sys.path.insert(0, 'C:/Users/lokes/Downloads/project/sovereign-alpha')
from dotenv import load_dotenv
load_dotenv()
from database import get_connection, init_pool

def check_observations():
    init_pool()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM observations LIMIT 0")
    print("Observations columns:", [desc[0] for desc in c.description])
    conn.close()

if __name__ == '__main__':
    check_observations()
