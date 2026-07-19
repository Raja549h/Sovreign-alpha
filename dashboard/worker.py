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
        self.scheduler_thread = None
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
        self.scheduler_thread = threading.Thread(target=self._autonomous_scheduler_loop, daemon=True)
        self.scheduler_thread.start()

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

    def _autonomous_scheduler_loop(self):
        """Autonomous daemon: Enqueues jobs for active companies every 6 hours."""
        scheduler_id = "main_scheduler"
        while self.running:
            try:
                with db_get_connection() as conn:
                    c = conn.cursor()
                    
                    # 1. Update/Initialize health record
                    c.execute("""
                        INSERT INTO scheduler_health (scheduler_id, last_scheduler_tick)
                        VALUES (%s, CURRENT_TIMESTAMP)
                        ON CONFLICT (scheduler_id) DO UPDATE 
                        SET last_scheduler_tick = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    """, (scheduler_id,))
                    conn.commit()

                    # 2. Check if we need to schedule jobs (Every 6 hours)
                    c.execute("""
                        SELECT last_job_created 
                        FROM scheduler_health 
                        WHERE scheduler_id = %s
                    """, (scheduler_id,))
                    row = c.fetchone()
                    last_created = row['last_job_created'] if row and row['last_job_created'] else None
                    
                    # We schedule if last_created is NULL or > 6 hours ago
                    should_schedule = False
                    if not last_created:
                        should_schedule = True
                    else:
                        # calculate difference
                        diff = (datetime.now(timezone.utc).replace(tzinfo=None) - last_created).total_seconds()
                        if diff >= 6 * 3600:
                            should_schedule = True

                    if should_schedule:
                        logger.info("AutonomousSchedulerDaemon: Initiating 6-hour intelligence cycle.")
                        c.execute("SELECT ticker FROM companies")
                        companies = c.fetchall()
                        
                        jobs_created = 0
                        for comp in companies:
                            ticker = comp['ticker']
                            # Ensure no active runs for this ticker
                            c.execute("SELECT count(*) FROM analysis_runs WHERE ticker = %s AND status IN ('PENDING', 'RUNNING')", (ticker,))
                            active_count = c.fetchone()[0]
                            if active_count == 0:
                                c.execute("INSERT INTO analysis_runs (ticker, run_type) VALUES (%s, 'AUTONOMOUS_CYCLE') RETURNING run_id", (ticker,))
                                jobs_created += 1
                        
                        logger.info(f"AutonomousSchedulerDaemon: Enqueued {jobs_created} jobs.")
                        
                        # Update health record
                        c.execute("""
                            UPDATE scheduler_health 
                            SET last_job_created = CURRENT_TIMESTAMP, 
                                jobs_created_today = jobs_created_today + %s,
                                updated_at = CURRENT_TIMESTAMP 
                            WHERE scheduler_id = %s
                        """, (jobs_created, scheduler_id))
                        conn.commit()

            except Exception as e:
                logger.error(f"AutonomousSchedulerDaemon error: {e}")
            
            # Tick every 60 seconds to update health and check for 6 hour boundary
            time.sleep(60)

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
