import os
from database import get_connection

os.environ['NEON_URL'] = "postgresql://neondb_owner:npg_HxbKeITV73Gl@ep-super-art-adot6eyq-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
c = get_connection().cursor()

c.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'observations'")
print("observations:", [r[0] for r in c.fetchall()])

c.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'evidence_timeline'")
print("evidence_timeline:", [r[0] for r in c.fetchall()])

