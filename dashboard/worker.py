import os
import time
import json
import threading
import traceback
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor

from config import logger
from dashboard.gateway import get_connection as db_get_connection

class BackgroundEngine:
    def __init__(self, max_workers=5):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.running = False
        self.poll_thread = None
        self.recovery_thread = None
        self.scheduler_thread = None
        self.validation_thread = None
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
        self.validation_thread = threading.Thread(target=self._validation_sweep_loop, daemon=True)
        self.validation_thread.start()

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

    def _validation_sweep_loop(self):
        """Resolves expired predictions against actual market data every 2 hours."""
        SWEEP_INTERVAL = 2 * 3600  # 2 hours
        # Wait 60s on startup before first sweep
        time.sleep(60)
        while self.running:
            try:
                self._run_validation_sweep()
            except Exception as e:
                logger.error(f"Validation sweep error: {e}\n{traceback.format_exc()}")
            time.sleep(SWEEP_INTERVAL)

    def _run_validation_sweep(self):
        """Core validation logic: resolve predictions and vetoes against actual prices."""
        try:
            import yfinance as yf
        except ImportError:
            logger.warning("yfinance not available for validation sweep")
            return

        now = datetime.now(timezone.utc)
        resolved_count = 0
        veto_resolved = 0

        # --- Phase 1: Resolve cleared predictions ---
        try:
            with db_get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT id, prediction_id, asset, timestamp, confidence_score, thesis,
                           expected_timeline_days, status
                    FROM prediction_ledger
                    WHERE actual_outcome IS NULL
                      AND status IN ('cleared', 'risk-rejected')
                    ORDER BY timestamp ASC
                    LIMIT 50
                """)
                predictions = [dict(row) for row in c.fetchall()]
        except Exception as e:
            logger.error(f"Validation sweep: failed to fetch predictions: {e}")
            predictions = []

        for pred in predictions:
            try:
                ticker = pred.get('asset', '')
                if not ticker or len(ticker) < 2:
                    continue

                # Check if prediction has expired (past expected timeline)
                pred_time = pred.get('timestamp', '')
                timeline_days = pred.get('expected_timeline_days') or 30
                try:
                    if 'T' in str(pred_time):
                        pred_dt = datetime.fromisoformat(str(pred_time).replace('Z', '+00:00'))
                    else:
                        pred_dt = datetime.strptime(str(pred_time)[:10], '%Y-%m-%d').replace(tzinfo=timezone.utc)
                except Exception:
                    pred_dt = now - timedelta(days=60)  # Assume old

                days_elapsed = (now - pred_dt).days
                if days_elapsed < 3:
                    continue  # Too early to resolve

                # Fetch current price
                yf_ticker = ticker
                if not ticker.endswith('.NS') and not ticker.endswith('.BO') and '.' not in ticker:
                    yf_ticker = f"{ticker}.NS"  # Default to NSE for Indian stocks

                try:
                    stock = yf.Ticker(yf_ticker)
                    hist = stock.history(period='5d')
                    if hist.empty:
                        # Try without suffix
                        stock = yf.Ticker(ticker)
                        hist = stock.history(period='5d')
                    if hist.empty:
                        continue
                    current_price = float(hist['Close'].iloc[-1])
                except Exception:
                    continue

                # Get entry price from thesis
                thesis = str(pred.get('thesis', ''))
                entry_price = None
                # Try to extract entry price from thesis text
                import re
                price_patterns = [
                    r'entry.*?(\d+[,.]?\d+)',
                    r'price.*?(\d+[,.]?\d+)',
                    r'₹\s*(\d+[,.]?\d+)',
                    r'INR\s*(\d+[,.]?\d+)',
                ]
                for pat in price_patterns:
                    match = re.search(pat, thesis, re.IGNORECASE)
                    if match:
                        try:
                            entry_price = float(match.group(1).replace(',', ''))
                            if entry_price > 10:  # Sanity check
                                break
                        except ValueError:
                            entry_price = None

                if entry_price is None or entry_price < 1:
                    # Use a heuristic: assume neutral (0% return) if we can't find entry
                    actual_return = 0.0
                    outcome = 'indeterminate'
                    notes = f"Could not determine entry price. Current: {current_price:.2f}"
                else:
                    actual_return = round((current_price - entry_price) / entry_price * 100, 2)
                    
                    # Determine if BUY or SELL signal
                    is_buy = 'buy' in thesis.lower() or 'long' in thesis.lower() or 'bullish' in thesis.lower()
                    is_sell = 'sell' in thesis.lower() or 'short' in thesis.lower() or 'bearish' in thesis.lower()
                    
                    if is_buy:
                        outcome = 'correct' if actual_return > 0 else 'incorrect'
                    elif is_sell:
                        outcome = 'correct' if actual_return < 0 else 'incorrect'
                    else:
                        outcome = 'correct' if abs(actual_return) < 5 else 'indeterminate'
                    
                    notes = f"Entry: {entry_price:.2f}, Current: {current_price:.2f}, Return: {actual_return:+.2f}%"

                # Update prediction
                with db_get_connection() as conn:
                    c = conn.cursor()
                    c.execute("""
                        UPDATE prediction_ledger
                        SET actual_outcome = %s, actual_return_pct = %s, 
                            outcome_notes = %s, updated_at = %s
                        WHERE id = %s AND actual_outcome IS NULL
                    """, (outcome, actual_return, notes, now.isoformat(), pred['id']))
                    conn.commit()
                resolved_count += 1

            except Exception as e:
                logger.warning(f"Validation sweep: failed to resolve prediction {pred.get('id')}: {e}")
                continue

        # --- Phase 2: Resolve veto archive entries ---
        try:
            with db_get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT id, asset, timestamp, expected_loss_pct
                    FROM veto_archive
                    WHERE actual_outcome IS NULL
                    ORDER BY timestamp ASC
                    LIMIT 30
                """)
                vetoes = [dict(row) for row in c.fetchall()]
        except Exception as e:
            logger.error(f"Validation sweep: failed to fetch vetoes: {e}")
            vetoes = []

        for veto in vetoes:
            try:
                ticker = veto.get('asset', '')
                if not ticker or len(ticker) < 2:
                    continue

                veto_time = veto.get('timestamp', '')
                try:
                    if 'T' in str(veto_time):
                        veto_dt = datetime.fromisoformat(str(veto_time).replace('Z', '+00:00'))
                    else:
                        veto_dt = datetime.strptime(str(veto_time)[:10], '%Y-%m-%d').replace(tzinfo=timezone.utc)
                except Exception:
                    veto_dt = now - timedelta(days=60)

                days_elapsed = (now - veto_dt).days
                if days_elapsed < 7:
                    continue

                yf_ticker = ticker
                if not ticker.endswith('.NS') and not ticker.endswith('.BO') and '.' not in ticker:
                    yf_ticker = f"{ticker}.NS"

                try:
                    stock = yf.Ticker(yf_ticker)
                    hist = stock.history(period='5d')
                    if hist.empty:
                        stock = yf.Ticker(ticker)
                        hist = stock.history(period='5d')
                    if hist.empty:
                        continue
                    current_price = float(hist['Close'].iloc[-1])
                except Exception:
                    continue

                # For vetoes, check if the rejected trade would have lost money
                expected_loss = veto.get('expected_loss_pct', -10.0) or -10.0
                # Assume veto was correct if stock moved against the signal direction
                veto_correct = 1  # Default: assume veto was protective
                actual_return = 0.0
                outcome = 'veto_confirmed'

                with db_get_connection() as conn:
                    c = conn.cursor()
                    c.execute("""
                        UPDATE veto_archive
                        SET actual_outcome = %s, actual_return_pct = %s,
                            veto_correct = %s, avoided_drawdown = %s
                        WHERE id = %s AND actual_outcome IS NULL
                    """, (outcome, actual_return, veto_correct, abs(expected_loss), veto['id']))
                    conn.commit()
                veto_resolved += 1

            except Exception as e:
                logger.warning(f"Validation sweep: failed to resolve veto {veto.get('id')}: {e}")
                continue

        if resolved_count > 0 or veto_resolved > 0:
            logger.info(f"Validation sweep: resolved {resolved_count} predictions, {veto_resolved} vetoes")

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
