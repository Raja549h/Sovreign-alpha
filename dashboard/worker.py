import os
import time
import json
import threading
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

from config import logger
from database import get_connection as db_get_connection

class BackgroundEngine:
    def __init__(self, max_workers=5):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.running = False
        self.poll_thread = None
        self.recovery_thread = None
        self.heartbeat_threads = {} # run_id -> threading.Event

    def start(self):
        if self.running:
            return
        self.running = True
        logger.info("Starting Continuous Operation Background Engine...")
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()
        self.recovery_thread = threading.Thread(target=self._recovery_loop, daemon=True)
        self.recovery_thread.start()

    def stop(self):
        self.running = False
        self.executor.shutdown(wait=False)

    def _log_event(self, run_id, event_type, message):
        try:
            with db_get_connection() as conn:
                c = conn.cursor()
                c.execute(
                    "INSERT INTO analysis_run_events (run_id, event_type, event_message) VALUES (%s, %s, %s)",
                    (run_id, event_type, message)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log event for run {run_id}: {e}")

    def _recovery_loop(self):
        """Sweeps stuck jobs every 60 seconds."""
        while self.running:
            try:
                with db_get_connection() as conn:
                    c = conn.cursor()
                    # Recover jobs running for > 5 minutes
                    c.execute("""
                        UPDATE analysis_runs 
                        SET status = CASE WHEN retry_count >= 3 THEN 'FAILED' ELSE 'PENDING' END,
                            retry_count = CASE WHEN retry_count >= 3 THEN retry_count ELSE retry_count + 1 END,
                            error_log = CASE WHEN retry_count >= 3 THEN 'Max retries exceeded after crash.' ELSE error_log END
                        WHERE status = 'RUNNING' AND heartbeat_at < NOW() - INTERVAL '5 minutes'
                        RETURNING run_id, status
                    """)
                    recovered = c.fetchall()
                    conn.commit()
                for row in recovered:
                    if row['status'] == 'FAILED':
                        self._log_event(row['run_id'], 'RUN_FAILED', 'Run crashed and exceeded max retries.')
                    else:
                        self._log_event(row['run_id'], 'RUN_RETRIED', 'Run recovered from crash and reset to PENDING.')
            except Exception as e:
                logger.error(f"Recovery loop error: {e}")
            
            time.sleep(60)

    def _heartbeat_loop(self, run_id, stop_event):
        """Updates heartbeat_at every 30 seconds."""
        while not stop_event.is_set():
            try:
                with db_get_connection() as conn:
                    c = conn.cursor()
                    c.execute("UPDATE analysis_runs SET heartbeat_at = CURRENT_TIMESTAMP WHERE run_id = %s", (run_id,))
                    conn.commit()
            except Exception as e:
                logger.error(f"Heartbeat error for run {run_id}: {e}")
            stop_event.wait(30)

    def _poll_loop(self):
        while self.running:
            job = self._acquire_job()
            if job:
                self.executor.submit(self._execute_job, job)
            else:
                time.sleep(2)

    def _acquire_job(self):
        try:
            with db_get_connection() as conn:
                c = conn.cursor()
                # Atomic lock acquisition
                c.execute("""
                    UPDATE analysis_runs 
                    SET status = 'RUNNING', heartbeat_at = CURRENT_TIMESTAMP, started_at = COALESCE(started_at, CURRENT_TIMESTAMP), updated_at = CURRENT_TIMESTAMP 
                    WHERE run_id = (
                        SELECT run_id 
                        FROM analysis_runs 
                        WHERE status = 'PENDING' 
                        ORDER BY created_at ASC 
                        FOR UPDATE SKIP LOCKED 
                        LIMIT 1
                    )
                    RETURNING run_id, ticker, retry_count
                """)
                job = c.fetchone()
                conn.commit()
            if job:
                return dict(job)
        except Exception as e:
            logger.error(f"Job acquisition error: {e}")
        return None

    def _execute_job(self, job):
        run_id = job['run_id']
        ticker = job['ticker']
        
        stop_event = threading.Event()
        hb_thread = threading.Thread(target=self._heartbeat_loop, args=(run_id, stop_event), daemon=True)
        hb_thread.start()
        
        self._log_event(run_id, 'RUN_STARTED', f"Starting analysis run for {ticker}")
        
        from research.engine import SovereignAlphaResearch
        engine = SovereignAlphaResearch()
        
        def progress_cb(pct, step_name):
            try:
                with db_get_connection() as conn:
                    c = conn.cursor()
                    c.execute(
                        "UPDATE analysis_runs SET progress_pct = %s, current_step = %s, updated_at = CURRENT_TIMESTAMP WHERE run_id = %s",
                        (pct, step_name, run_id)
                    )
                    conn.commit()
                # Assuming events are logged directly in engine for major milestones
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

        try:
            result = engine.full_pipeline(ticker=ticker, filings_list=[], run_id=run_id, progress_callback=progress_cb)
            
            with db_get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    UPDATE analysis_runs 
                    SET status = 'COMPLETED', progress_pct = 100, current_step = 'Completed', 
                        completed_at = CURRENT_TIMESTAMP, result_data = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE run_id = %s
                """, (json.dumps(result), run_id))
                conn.commit()
            
            self._log_event(run_id, 'RUN_COMPLETED', f"Successfully completed run for {ticker}")
            
        except Exception as e:
            import traceback
            err_msg = str(e) + "\n" + traceback.format_exc()
            with db_get_connection() as conn:
                c = conn.cursor()
                
                # Check retries
                new_status = 'FAILED'
                if job['retry_count'] < 3:
                    new_status = 'PENDING'
                    c.execute("UPDATE analysis_runs SET status = %s, retry_count = retry_count + 1, error_log = %s, updated_at = CURRENT_TIMESTAMP WHERE run_id = %s", (new_status, err_msg, run_id))
                    self._log_event(run_id, 'RUN_RETRIED', f"Run failed, retrying... Error: {e}")
                else:
                    c.execute("UPDATE analysis_runs SET status = %s, error_log = %s, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE run_id = %s", (new_status, err_msg, run_id))
                    self._log_event(run_id, 'RUN_FAILED', f"Run failed permanently. Error: {e}")
                
                conn.commit()
            
        finally:
            stop_event.set()
