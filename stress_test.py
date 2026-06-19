import os
import threading
import time
from database import get_connection, IntegrityError, OperationalError

errors = []
successes = 0
lock = threading.Lock()

def stress_worker(worker_id):
    global successes, errors
    try:
        conn = get_connection()
        c = conn.cursor()
        
        # 1. Observation Creation
        c.execute("INSERT INTO observations (ticker, company, type, headline, severity, timestamp) VALUES (%s, %s, %s, %s, %s, NOW()) RETURNING id", 
                  ("TSLA", "Tesla", "STRESS", f"Stress test observation {worker_id}", "MEDIUM"))
        
        obs_id = c.fetchone()['id']
        
        # 2. Pipeline Evidence Creation
        c.execute("INSERT INTO evidence_timeline (observation_id, company_id, event_type, event_label, event_detail, created_at) VALUES (%s, %s, %s, %s, %s, NOW())",
                  (obs_id, 1, "STRESS_TEST", "Worker Execution", f"Worker {worker_id} executed successfully"))
                  
        conn.commit()
        conn.close()
        
        with lock:
            successes += 1
    except Exception as e:
        with lock:
            errors.append(str(e))

threads = []
print("Starting Neon-native Stress Test (20 concurrent threads)...")
for i in range(20):
    t = threading.Thread(target=stress_worker, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print(f"Stress Test Complete.")
print(f"Successes: {successes}")
print(f"Errors: {len(errors)}")
if errors:
    print(errors[0])
