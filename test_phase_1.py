import psycopg2

NEON_URL = "postgresql://neondb_owner:npg_HxbKeITV73Gl@ep-super-art-adot6eyq-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def verify_connection():
    try:
        conn = psycopg2.connect(NEON_URL)
        cur = conn.cursor()
        
        # Verify Neon URL reachable & SSL active
        cur.execute("SELECT current_database(), current_schemas(true), ssl_is_used();")
        db, schemas, ssl = cur.fetchone()
        
        report = "# Neon Connection Verification Report\n\n"
        report += "- **Neon URL Reachable**: PASSED\n"
        report += f"- **SSL Connection Active**: {'PASSED' if ssl else 'FAILED'}\n"
        report += "- **Credentials Valid**: PASSED\n"
        report += f"- **Database**: `{db}`\n"
        report += f"- **Active Schemas**: `{schemas}`\n"
        
        with open('NEON_CONNECTION_REPORT.md', 'w') as f:
            f.write(report)
            
        print("Phase 1 Complete.")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == '__main__':
    verify_connection()
