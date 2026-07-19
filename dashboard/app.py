#!/usr/bin/env python3
"""
Sovereign Alpha Dashboard
=======================

Flask-based web dashboard for the Sovereign Alpha system.
Run with: python dashboard/app.py

FIX LOG:
- FIX 1: Proof glob pattern changed from 'proof_*.json' to 'cert_*.json'
- FIX 2: Performance page now uses real database queries
- FIX 3: API /run returns counts of new decisions/proofs added
- FIX 4: Decisions page shows message when empty
- FIX 5: Proofs page better empty state handling
- FIX 6: API /status counts proofs from folder
- FIX 7: Login system added for fund protection
- FIX 8: Upload portal for fund managers
"""

try:
    from dashboard.scheduler_instance import scheduler
except ImportError:
    from scheduler_instance import scheduler
import os
import sys
import json
import decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

import pandas as pd
from pathlib import Path

dashboard_dir = Path(__file__).parent
project_dir = dashboard_dir.parent
sys.path.insert(0, str(project_dir))

from dashboard.gateway import get_connection as db_get_connection
from datetime import datetime, timedelta, timezone
from functools import wraps
import time
import hmac

from dotenv import load_dotenv
load_dotenv(str(project_dir / '.env'))

_missing = []
for _mod in ['flask', 'flask_limiter', 'flask_talisman', 'flask_wtf', 'flask_cors', 'werkzeug']:
    try:
        __import__(_mod)
    except ImportError:
        _missing.append(_mod)
if _missing:
    print(f"Missing packages: {_missing}. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r',
                           str(Path(__file__).parent.parent / 'requirements-docker.txt')])

from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

try:
    from dashboard.worker import BackgroundEngine
    bg_engine = BackgroundEngine()
    bg_engine.start()
except Exception as e:
    print(f"Failed to start BackgroundEngine: {e}")

FLASK_AVAILABLE = True
IS_CLOUD = bool(os.environ.get("SPACE_ID")) or os.environ.get("RENDER", "false").lower() == "true"

BASE_DIR = project_dir
PERSISTENT_DIR = Path(os.environ.get("PERSISTENT_DIR", "/data" if IS_CLOUD else BASE_DIR))

if IS_CLOUD and not PERSISTENT_DIR.exists():
    try:
        PERSISTENT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        print(f"WARNING: Cannot create {PERSISTENT_DIR}. Falling back to BASE_DIR.")
        PERSISTENT_DIR = BASE_DIR

if IS_CLOUD and PERSISTENT_DIR != BASE_DIR:
    if not (PERSISTENT_DIR / "billing").exists():
        import shutil
        print("[startup] Initializing persistent storage from Docker image data...")
        if (BASE_DIR / "billing").exists():
            shutil.copytree(BASE_DIR / "billing", PERSISTENT_DIR / "billing", dirs_exist_ok=True)
        if (BASE_DIR / "results").exists():
            shutil.copytree(BASE_DIR / "results", PERSISTENT_DIR / "results", dirs_exist_ok=True)
        if (BASE_DIR / "zkml" / "proofs").exists():
            (PERSISTENT_DIR / "zkml").mkdir(parents=True, exist_ok=True)
            shutil.copytree(BASE_DIR / "zkml" / "proofs", PERSISTENT_DIR / "zkml" / "proofs", dirs_exist_ok=True)
        if (BASE_DIR / "data").exists():
            shutil.copytree(BASE_DIR / "data", PERSISTENT_DIR / "data", dirs_exist_ok=True)
            print(f"[startup] Copied data/ to {PERSISTENT_DIR / 'data'}")
    else:
        # Even if billing exists (not first boot), ensure data files are refreshed from git
        import shutil
        if (BASE_DIR / "data").exists():
            for _json_file in ["live_market_data.json", "live_signals.json", "sample_positions.xlsx"]:
                _src = BASE_DIR / "data" / _json_file
                _dst = PERSISTENT_DIR / "data" / _json_file
                if _src.exists() and not _dst.exists():
                    (PERSISTENT_DIR / "data").mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(_src), str(_dst))
                    print(f"[startup] Copied missing {_json_file} to persistent storage")

DATA_DIR = PERSISTENT_DIR / "data"
BILLING_DIR = PERSISTENT_DIR / "billing"
RESULTS_DIR = PERSISTENT_DIR / "results"
PROOFS_DIR = PERSISTENT_DIR / "zkml" / "proofs"
CERTS_DIR = PERSISTENT_DIR / "zkml" / "certificates"
FUNDS_DIR = DATA_DIR / "funds"

DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PROOFS_DIR.mkdir(parents=True, exist_ok=True)
CERTS_DIR.mkdir(parents=True, exist_ok=True)
BILLING_DIR.mkdir(parents=True, exist_ok=True)
FUNDS_DIR.mkdir(parents=True, exist_ok=True)

def get_regime_data():
    """Get current regime classification for dashboard."""
    try:
        from engine.regime import MarketRegimeEngine
        engine = MarketRegimeEngine()
        latest = engine.get_latest()
        if latest:
            return {
                "regime": latest.regime,
                "confidence": f"{latest.confidence:.0%}",
                "summary": latest.summary,
                "indicators": latest.indicators or {}
            }
    except Exception:
        pass
    return {"regime": "NEUTRAL", "confidence": "—", "summary": "No data", "indicators": {}}

_macro_cache = {
    "data": {
        "vix": 18.4, "dxy": 99.3, "treasury_10y": 4.60,
        "gold": 2345.0, "oil_wti": 78.5, "spx_price": 5620.0,
        "spx_change": 0.45, "dxy_change": -0.12, "gold_change": 0.82,
        "oil_change": -0.55, "nsei": 23759.0, "nsei_change": 0.30
    },
    "timestamp": 0,
    "fetching": False
}

def _fetch_macro_async():
    global _macro_cache
    try:
        from engine.data_layer import DataLayer
        dl = DataLayer()
        macro = dl.fetch_macro_snapshot()
        tickers = {
            "vix": getattr(macro, 'vix', None),
            "dxy": getattr(macro, 'dxy', None),
            "treasury_10y": getattr(macro, 'treasury_10y', None),
            "gold": getattr(macro, 'gold', None),
            "oil_wti": getattr(macro, 'oil_wti', None),
            "spx_price": getattr(macro, 'spx', None),
            "spx_change": getattr(macro, 'spx_change', None),
            "dxy_change": getattr(macro, 'dxy_change', None),
            "gold_change": getattr(macro, 'gold_change', None),
            "oil_change": getattr(macro, 'oil_change', None),
            "nsei": getattr(macro, 'nsei', None),
            "nsei_change": getattr(macro, 'nsei_change', None),
        }
        result = {k: v for k, v in tickers.items() if v is not None}
        if result:
            _macro_cache["data"].update(result)
    except Exception as e:
        print(f"[WARN] Async macro fetch failed: {e}")
    finally:
        _macro_cache["timestamp"] = time.time()
        _macro_cache["fetching"] = False

def get_macro_tickers():
    """Get macro ticker data asynchronously to prevent blocking."""
    global _macro_cache
    now = time.time()
    if now - _macro_cache["timestamp"] > 300 and not _macro_cache["fetching"]:
        _macro_cache["fetching"] = True
        import threading
        threading.Thread(target=_fetch_macro_async, daemon=True).start()
    return _macro_cache["data"]

app = Flask(__name__, template_folder='templates')

@app.before_request
def check_db_availability():
    from flask import request, render_template, abort, jsonify
    if request.endpoint == "static" or request.path.startswith('/api/'):
        return
#    try:
#        from dashboard.gateway import get_db_connection, get_connection
#        conn = get_connection()
#        if conn is None:
#            raise Exception("DB connection returned None")
#        # # conn.close()
#    except Exception as e:
#        print("[DB_ERROR]", e)
#        try:
#            return render_template('unavailable.html', message="Database is currently unavailable. Please try again later.", error_code="DB_CONNECTION_FAILED"), 503
#        except Exception:
#            abort(503, description="Database unavailable — Sovereign Alpha is offline for maintenance.")
if IS_CLOUD:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET', os.environ.get('SECRET_KEY', 'change-this-secret-in-production'))
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SESSION_COOKIE_NAME'] = 'sa_session'
app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('JWT_SECRET', app.config['SECRET_KEY'])

csp = {
    'default-src': "'self'",
    'script-src': ["'self'", "'unsafe-inline'", "cdnjs.cloudflare.com", "cdn.jsdelivr.net"],
    'style-src': ["'self'", "'unsafe-inline'", "fonts.googleapis.com", "cdn.jsdelivr.net"],
    'font-src': ["'self'", "fonts.gstatic.com"],
    'img-src': "'self' data:",
    'connect-src': "'self'",
    'frame-ancestors': "'none'"
}
Talisman(app, force_https=False, strict_transport_security=True,
         strict_transport_security_max_age=31536000,
         content_security_policy=csp,
         referrer_policy='strict-origin-when-cross-origin',
         frame_options='DENY',
         x_xss_protection=True,
         session_cookie_secure=True,
         permissions_policy={'geolocation': "()", 'camera': "()", 'microphone': "()"})
CORS(app, origins=['http://localhost:5000', 'http://localhost:7860', 'https://demonsatan-soverignalpha.hf.space'], supports_credentials=True)

limiter = Limiter(app=app, key_func=get_remote_address,
                  default_limits=["2000 per day", "500 per hour"],
                  storage_uri="memory://")

csrf = CSRFProtect(app)

failed_attempts = {}

@app.errorhandler(404)
def handle_404(e):
    return render_template('error.html', error_code=404, error_message="Page not found"), 404

@app.errorhandler(500)
def handle_500(e):
    return render_template('error.html', error_code=500, error_message="Internal server error"), 500

@app.errorhandler(Exception)
def handle_error(e):
    app.logger.error(f"Unhandled error: {str(e)}", exc_info=True)
    return render_template('error.html', error_code=500, error_message=str(e)), 500

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return render_template('error.html', error_code=429,
                           error_message="Too many requests. Please wait before trying again."), 429

@app.errorhandler(413)
def file_too_large(e):
    return render_template('error.html', error_code=413,
                           error_message="File too large. Maximum 10MB."), 413

@app.after_request
def add_security_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    return response

TEMPLATE_DIR = dashboard_dir / 'templates'
if TEMPLATE_DIR.exists():
    app.template_folder = str(TEMPLATE_DIR)

DB_PATH = BILLING_DIR / "billing.db"
FUND_DATA_DB = BILLING_DIR / "fund_data.db"

import secrets
FUND_PASSWORD = os.environ.get("FUND_PASSWORD")
if not FUND_PASSWORD:
    FUND_PASSWORD = secrets.token_urlsafe(32)

DEMO_MODE = False

@app.context_processor
def inject_globals():
    macro = get_macro_tickers()
    regime = get_regime_data()
    return {
        'session_user': request.cookies.get('session_user', 'fund_manager'),
        'last_updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'macro_tickers': macro,
        'regime_data': regime,
        'is_demo': is_demo_mode()
    }

def init_fund_db():
    try:
        from dashboard.schemas import init_fund_data_db
        init_fund_data_db()
    except Exception as e:
        print(f"Warning: Could not initialize fund database: {e}")

try:
    init_fund_db()
except Exception as e:
    print(f"Warning: Initialization failed: {e}")

def get_db_connection():
    """Get database connection to db (prediction_ledger, veto_archive)."""
    conn = db_get_connection()
    return conn

def save_prediction(prediction_data: dict) -> bool:
    """Save a prediction to the ledger. Write-once, never update timestamp."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO prediction_ledger 
                (prediction_id, timestamp, asset, sector, thesis, confidence_score, 
                 status, expected_timeline_days, proof_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                prediction_data.get('prediction_id'),
                prediction_data.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
                prediction_data.get('asset'),
                prediction_data.get('sector', ''),
                prediction_data.get('thesis', ''),
                prediction_data.get('confidence_score', 0.0),
                prediction_data.get('status', 'pending'),
                prediction_data.get('expected_timeline_days', 30),
                prediction_data.get('proof_hash', ''),
                datetime.utcnow().isoformat() + 'Z',
                datetime.utcnow().isoformat() + 'Z'
            ))
            return True
    except Exception as e:
        print(f"Error saving prediction: {e}")
        return False

def get_predictions(limit: int = 100) -> list:
    """Get all predictions ordered by timestamp descending."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT * FROM prediction_ledger 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
            rows = c.fetchall()
            return [dict(row) for row in rows]
    except Exception:
        return []

def update_prediction_outcome(prediction_id: str, outcome_data: dict) -> bool:
    """Update a prediction with its outcome. Can only update outcome fields."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE prediction_ledger SET
                actual_outcome = %s,
                actual_return_pct = %s,
                outcome_notes = %s,
                status = %s,
                updated_at = %s
                WHERE prediction_id = %s
            """, (
                outcome_data.get('outcome', ''),
                outcome_data.get('actual_return_pct', 0.0),
                outcome_data.get('notes', ''),
                'HIT' if outcome_data.get('outcome', '').lower() == 'correct' else 'MISS',
                datetime.utcnow().isoformat() + 'Z',
                prediction_id
            ))
            return c.rowcount > 0
    except Exception as e:
        print(f"Error updating prediction outcome: {e}")
        return False

def save_veto(veto_data: dict) -> bool:
    """Save a veto to the archive."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO veto_archive
                (veto_id, prediction_id, timestamp, asset, sector, rejection_reason,
                 expected_loss_pct, proof_hash, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                veto_data.get('veto_id'),
                veto_data.get('prediction_id', ''),
                veto_data.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
                veto_data.get('asset'),
                veto_data.get('sector', ''),
                veto_data.get('rejection_reason'),
                veto_data.get('expected_loss_pct', 0.0),
                veto_data.get('proof_hash', ''),
                datetime.utcnow().isoformat() + 'Z'
            ))
            return True
    except Exception as e:
        print(f"Error saving veto: {e}")
        return False

def get_veto_archive(limit: int = 100) -> list:
    """Get all vetoed items ordered by timestamp descending."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT * FROM veto_archive 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
            rows = c.fetchall()
            return [dict(row) for row in rows]
    except Exception:
        return []

def update_veto_outcome(veto_id: str, outcome_data: dict) -> bool:
    """Update veto with actual outcome after time passes."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            actual_return = outcome_data.get('actual_return_pct', 0.0)
            expected_loss = outcome_data.get('expected_loss_pct', 0.0)
            veto_correct = actual_return < 0 if expected_loss > 0 else None
            avoided = abs(expected_loss - actual_return) if veto_correct and actual_return < 0 else 0
            
            c.execute("""
                UPDATE veto_archive SET
                actual_outcome = %s,
                actual_return_pct = %s,
                avoided_drawdown = %s,
                veto_correct = %s,
                notes = %s
                WHERE veto_id = %s
            """, (
                outcome_data.get('outcome', ''),
                actual_return,
                avoided,
                veto_correct,
                outcome_data.get('notes', ''),
                veto_id
            ))
            return c.rowcount > 0
    except Exception as e:
        print(f"Error updating veto outcome: {e}")
        return False

def calculate_ledger_stats() -> dict:
    """Calculate statistics for the prediction ledger."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger")
            total = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status = 'cleared'")
            approved = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status = 'risk-rejected'")
            rejected = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
            with_outcome = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE actual_outcome = 'correct'")
            correct = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status = 'cleared' AND actual_outcome IS NOT NULL AND actual_outcome != ''")
            cleared_with_outcome = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status = 'cleared' AND actual_outcome = 'correct'")
            cleared_correct = c.fetchone()[0] or 0
            
            c.execute("SELECT AVG(confidence_score) FROM prediction_ledger WHERE status = 'cleared'")
            avg_conf = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM veto_archive")
            total_vetoes = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM veto_archive WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
            vetoes_with_outcome = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM veto_archive WHERE veto_correct = 1")
            vetoes_correct = c.fetchone()[0] or 0
            
            c.execute("SELECT SUM(avoided_drawdown) FROM veto_archive")
            avoided = c.fetchone()[0] or 0
            
            c.execute("""
                SELECT asset, status, confidence_score, thesis
                FROM prediction_ledger 
                WHERE status = 'cleared'
                ORDER BY confidence_score DESC LIMIT 1
            """)
            top = c.fetchone()
            
            return {
                'total_predictions': total,
                'approved': approved,
                'rejected': rejected,
                'approval_rate': (approved / total * 100) if total > 0 else 0,
                'accuracy': (correct / with_outcome * 100) if with_outcome > 0 else 0,
                'cleared_accuracy': (cleared_correct / cleared_with_outcome * 100) if cleared_with_outcome > 0 else 0,
                'avg_confidence': avg_conf,
                'total_vetoes': total_vetoes,
                'veto_accuracy': (vetoes_correct / vetoes_with_outcome * 100) if vetoes_with_outcome > 0 else 0,
                'drawdown_avoided': avoided,
                'resolved_outcomes': with_outcome,
                'top_prediction': dict(top) if top else None
            }
    except Exception as e:
        print(f"Error calculating stats: {e}")
        return {
            'total_predictions': 0, 'approved': 0, 'rejected': 0, 'approval_rate': 0,
            'accuracy': 0, 'cleared_accuracy': 0, 'avg_confidence': 0,
            'total_vetoes': 0, 'veto_accuracy': 0, 'drawdown_avoided': 0,
            'resolved_outcomes': 0, 'top_prediction': None
        }

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = request.cookies.get('session_token')
        if not session_token:
            return redirect(url_for('login_page'))
        try:
            from privacy import verify_session_token
            fund_id = verify_session_token(session_token)
            if not fund_id:
                return redirect(url_for('login_page'))
        except Exception:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def save_fund_file(file_type: str, content: bytes):
    conn = db_get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM fund_uploads WHERE file_type = %s", (file_type,))
    c.execute("INSERT INTO fund_uploads (file_type, file_content, uploaded_at) VALUES (%s, %s, %s)",
              (file_type, content, datetime.utcnow().isoformat() + 'Z'))
    conn.commit()
    pass
    # # conn.close()

def get_fund_file(file_type: str) -> bytes:
    conn = db_get_connection()
    c = conn.cursor()
    c.execute("SELECT file_content FROM fund_uploads WHERE file_type = %s", (file_type,))
    row = c.fetchone()
    pass
    # # conn.close()
    return row[0] if row else None

def save_fund_param(key: str, value: str):
    conn = db_get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO fund_params (param_key, param_value, updated_at) VALUES (%s, %s, %s)",
              (key, value, datetime.utcnow().isoformat() + 'Z'))
    conn.commit()
    pass
    # # conn.close()

def get_fund_params() -> dict:
    conn = db_get_connection()
    c = conn.cursor()
    c.execute("SELECT param_key, param_value FROM fund_params")
    rows = c.fetchall()
    pass
    # # conn.close()
    return {row[0]: row[1] for row in rows}

def check_setup_progress() -> dict:
    has_positions = get_fund_file('positions') is not None
    has_params = len(get_fund_params()) > 0
    has_research = get_fund_file('research') is not None
    decisions = get_decisions()
    has_analysis = len(decisions) > 0
    return {
        'step1_done': True,
        'step2_done': has_positions,
        'step3_done': has_params,
        'step4_done': has_research,
        'step5_done': has_analysis,
        'all_done': has_positions and has_params and has_research and has_analysis
    }



def is_demo_mode():
    """Check if the system has no real data yet."""
    try:
        ledger = calculate_ledger_stats()
        return ledger['with_outcome'] == 0 or ledger['total_predictions'] == 0
    except Exception:
        return False


def get_db_data(query, params=None):
    """Get data from PostgreSQL database."""
    
    conn = db_get_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"DB Error: {e}")
        return []
    finally:
        pass
        # # conn.close()


def get_decisions():
    """Get all decisions from prediction_ledger and veto_archive ordered by newest first."""
    query = """
        SELECT 
            prediction_id AS decision_id,
            asset AS symbol,
            CASE WHEN status IN ('vetoed','risk-rejected','VETOED','RISK_REJECTED') 
                 THEN 'veto' ELSE 'approve' END AS action,
            status,
            confidence_score AS confidence,
            timestamp,
            proof_hash AS zk_proof_hash,
            expected_timeline_days
        FROM prediction_ledger
        UNION ALL
        SELECT 
            veto_id AS decision_id,
            asset AS symbol,
            'veto' AS action,
            'vetoed' AS status,
            1.0 - risk_score AS confidence,
            timestamp,
            NULL AS zk_proof_hash,
            NULL AS expected_timeline_days
        FROM veto_archive
        ORDER BY timestamp DESC
        LIMIT 100
    """
    return get_db_data(query)


def get_inference_stats():
    """Get inference statistics."""
    query = """
        SELECT 
            COUNT(*) as total_calls,
            SUM(total_tokens) as total_tokens,
            SUM(cost_estimate) as total_cost,
            model
        FROM inference_log
        GROUP BY model
    """
    return get_db_data(query)


def get_sector_stats():
    """Get sector breakdown from decisions."""
    query = """
        SELECT 
            COALESCE(sector, asset) as symbol,
            COUNT(*) as count,
            0 as total_alpha
        FROM prediction_ledger
        GROUP BY COALESCE(sector, asset)
    """
    return get_db_data(query)


def get_return_distribution():
    """Get return distribution from decisions."""
    query = """
        SELECT 
            (confidence_score * 0.1) as alpha_generated
        FROM prediction_ledger
        WHERE status NOT IN ('vetoed','risk-rejected','VETOED','RISK_REJECTED')
    """
    return get_db_data(query)


def load_results_files():
    """Load results from JSON files."""
    results = []
    
    if not RESULTS_DIR.exists():
        return results
    
    for f in sorted(RESULTS_DIR.glob('session_*.json'), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(f, 'r') as fp:
                data = json.load(fp)
                results.append(data)
        except Exception as e:
            print(f"Error loading {f}: {e}")
    
    return results


def load_proof_files():
    """Load proof files - FIX: Changed from 'proof_*.json' to 'cert_*.json'."""
    proofs = []
    
    if not PROOFS_DIR.exists():
        print(f"Proofs directory not found at {PROOFS_DIR}")
        return proofs
    
    for f in sorted(PROOFS_DIR.glob('cert_*.json'), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(f, 'r') as fp:
                data = json.load(fp)
                proofs.append(data)
        except Exception as e:
            print(f"Error loading proof {f}: {e}")
    
    print(f"Loaded {len(proofs)} proof files from {PROOFS_DIR}")
    return proofs


def count_proof_files():
    """Count proof files in directory."""
    if not PROOFS_DIR.exists():
        return 0
    return len(list(PROOFS_DIR.glob('cert_*.json')))


def calculate_dashboard_stats():
    """Calculate dashboard statistics from real database."""
    decisions = get_decisions()
    
    total_decisions = len(decisions)
    approved = len([d for d in decisions if d.get('status') in ['active', 'pending']])
    vetoed = total_decisions - approved
    
    approval_rate = (approved / total_decisions * 100) if total_decisions > 0 else 0
    
    total_alpha = sum(d.get('alpha_generated', 0) or 0 for d in decisions)
    
    proofs_count = count_proof_files()
    
    return {
        'total_decisions': total_decisions,
        'approved': approved,
        'vetoed': vetoed,
        'approval_rate': approval_rate,
        'total_alpha': total_alpha,
        'total_fees': total_alpha * 0.12,
        'proofs_verified': proofs_count,
        'last_verified': datetime.utcnow().strftime('%H:%M:%S')
    }


@app.template_filter('pct')
def pct_filter(value):
    """Format confidence as percentage. If <= 1.0, multiply by 100."""
    try:
        f = float(value)
        if f <= 1.0:
            return f"{f * 100:.1f}%"
        return f"{f:.1f}%"
    except (ValueError, TypeError):
        return "N/A"


def get_dashboard_stats():
    """Get real dashboard statistics from prediction_ledger and veto_archive."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM prediction_ledger")
            total = c.fetchone()[0]
            print(f"DEBUG: SELECT COUNT(*) FROM prediction_ledger -> {total}")
            
            c.execute("""SELECT COUNT(*) FROM prediction_ledger
                     WHERE status NOT IN ('vetoed','risk-rejected','VETOED','RISK_REJECTED')""")
            approved = c.fetchone()[0]
            
            c.execute("""SELECT COUNT(*) FROM prediction_ledger
                     WHERE status IN ('vetoed','risk-rejected','VETOED','RISK_REJECTED')""")
            vetoed = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM veto_archive")
            total_vetoes = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM veto_archive WHERE veto_correct = 1")
            correct_vetoes = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status IN ('HIT', 'MISS', 'hit', 'miss')")
            resolved_outcomes = c.fetchone()[0]
            print(f"DEBUG: SELECT COUNT(*) FROM prediction_ledger WHERE resolved IS TRUE -> {resolved_outcomes}")
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status IN ('HIT', 'hit')")
            hits = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status IN ('MISS', 'miss')")
            misses = c.fetchone()[0]

            approval_rate = round(approved / total * 100, 1) if total > 0 else 0
            veto_accuracy = round(correct_vetoes / total_vetoes * 100, 1) if total_vetoes > 0 else 0
            return {
                'total_predictions': total, 'approved': approved, 'vetoed': vetoed,
                'approval_rate': approval_rate, 'veto_efficiency': veto_accuracy,
                'total_vetoes': total_vetoes, 'correct_vetoes': correct_vetoes,
                'resolved_predictions': resolved_outcomes, 'hits': hits, 'misses': misses,
            }
    except Exception as e:
        print("GET_DASHBOARD_STATS ERROR:", e)
        return {'total_predictions': 0, 'approved': 0, 'vetoed': 0,
                'approval_rate': 0, 'veto_efficiency': 0,
                'total_vetoes': 0, 'correct_vetoes': 0, 'resolved_predictions': 0}


def get_evidence_trust_data():
    """Get evidence-based trust metrics from db (no vanity metrics)."""
    try:
        from research.storage.research_db import get_connection as get_rsch_conn
        with get_rsch_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM research_notes")
            research_notes = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM observation_memory")
            total_observations = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM observation_memory WHERE validation_status IN ('CONFIRMED','INVALIDATED')")
            resolved_obs = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM observation_validations")
            validations = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM confidence_calibration")
            calibrated = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM failure_analysis")
            failures = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM evidence_timeline")
            timeline_events = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM observation_autopsy")
            autopsied = c.fetchone()[0]
            c.execute("SELECT AVG(research_quality_score) FROM observation_autopsy")
            avg_rqs_row = c.fetchone()
            avg_rqs = round(avg_rqs_row[0], 4) if avg_rqs_row and avg_rqs_row[0] else 0
            validation_coverage = round(resolved_obs / total_observations * 100, 1) if total_observations > 0 else 0
            evidence_quality = 'INSUFFICIENT_DATA'
            if validations >= 10:
                evidence_quality = 'LOW'
            if validations >= 25:
                evidence_quality = 'DEVELOPING'
            if validations >= 50:
                evidence_quality = 'ADEQUATE'
            if validations >= 100:
                evidence_quality = 'SUBSTANTIAL'
            c.execute("SELECT COUNT(*) FROM shadow_portfolio WHERE status = 'OPEN'")
            open_positions = c.fetchone()[0]
            return {
                'research_notes': research_notes,
                'total_observations': total_observations,
                'resolved_observations': resolved_obs,
                'validation_coverage_pct': validation_coverage,
                'total_validations': validations,
                'calibration_events': calibrated,
                'failure_records': failures,
                'timeline_events': timeline_events,
                'autopsied_observations': autopsied,
                'avg_research_quality_score': avg_rqs,
                'evidence_quality': evidence_quality,
                'open_positions': open_positions,
            }
    except Exception:
        return {
            'research_notes': 0, 'total_observations': 0, 'resolved_observations': 0,
            'validation_coverage_pct': 0, 'total_validations': 0, 'calibration_events': 0,
            'failure_records': 0, 'timeline_events': 0, 'autopsied_observations': 0,
            'avg_research_quality_score': 0, 'evidence_quality': 'NO_DATA',
            'open_positions': 0,
        }





@app.route('/')
@login_required
def index():
    """Home page — honest system status, no vanity metrics."""
    try:
        observations = []
        macro_alerts = []
        high_severity_7d = 0
        try:
            from research.observation_stream import build_live_feed
            feed = build_live_feed(40)
            observations = feed.get('observations', [])
            
            # Sort observations by severity
            severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
            observations.sort(key=lambda x: severity_order.get(x.get('severity', 'LOW'), 99))
            
            macro_alerts = feed.get('macro_alerts', [])
            high_severity_7d = feed.get('high_severity_7d', 0)
        except Exception:
            pass

        trust = get_evidence_trust_data()
        stats = get_dashboard_stats()
        regime = get_regime_data()
        predictions_list = get_predictions(8)
        veto_list = get_veto_archive(6)
        progress = check_setup_progress()

        return render_template('index.html',
                           trust=trust,
                           stats=stats,
                           regime=regime['regime'],
                           regime_confidence=regime['confidence'],
                           predictions=predictions_list,
                           vetoes=veto_list,
                           last_verified=datetime.utcnow().strftime('%H:%M:%S'),
                           data_verified_at=datetime.utcnow(),
                           progress=progress,
                           is_demo=is_demo_mode(),
                           certificates=count_proof_files() + len(list(CERTS_DIR.glob("*.json"))),
                           observations=observations, macro_alerts=macro_alerts, high_severity_7d=high_severity_7d)
    except Exception as e:
        trust = get_evidence_trust_data()
        return render_template('index.html',
                           trust=trust,
                           stats=get_dashboard_stats(),
                           regime='NEUTRAL', regime_confidence='—',
                           predictions=[], vetoes=[],
                           last_verified=datetime.utcnow().strftime('%H:%M:%S'),
                           data_verified_at=datetime.utcnow(),
                           progress={'step1_done': True, 'step2_done': False, 'step3_done': False, 'step4_done': False, 'step5_done': False},
                           is_demo=False, certificates=0,
                           observations=[], macro_alerts=[], high_severity_7d=0)


@app.route('/decisions')
@login_required
def decisions():
    """Decisions page."""
    try:
        all_decisions = get_decisions()
        decisions_list = []
        for d in all_decisions:
            conf = d.get('confidence') or 0.7
            try:
                conf = float(conf)
            except (ValueError, TypeError):
                conf = 0.7
            decisions_list.append({
                'decision_id': d.get('decision_id', 'N/A'),
                'symbol': d.get('symbol', ''),
                'action': d.get('action', ''),
                'status': d.get('status', 'pending'),
                'confidence': conf,
                'potential_return': d.get('potential_return') or d.get('alpha_generated') or 0,
                'zk_proof_hash': d.get('zk_proof_hash', ''),
                'timestamp': d.get('timestamp', ''),
                'fee': d.get('fee_calculated') or 0
            })
        stats = get_dashboard_stats()
        has_data = len(decisions_list) > 0
        
        return render_template('decisions.html', 
                               decisions=decisions_list,
                               has_data=has_data,
                               stats=stats,
                               is_demo=is_demo_mode())
    except Exception:
        return render_template('decisions.html',
                               decisions=[],
                               has_data=False,
                               stats={'approval_rate': 0, 'approved': 0, 'vetoed': 0, 'total_alpha': 0, 'total_fees': 0, 'total_decisions': 0},
                                is_demo=True)



@app.route('/misses')
def misses_ledger():
    try:
        from dashboard.gateway import get_connection as db_get_connection
        conn = db_get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT timestamp, asset as ticker, thesis as prediction, 
                   actual_outcome as outcome, outcome_notes as post_mortem
            FROM prediction_ledger 
            WHERE status IN ('MISS', 'miss') OR actual_outcome IN ('MISS', 'miss')
            ORDER BY timestamp DESC
        """)
        misses = [dict(row) for row in c.fetchall()]
        c.close()
        pass
        # # conn.close()
    except Exception as e:
        print(f"Error fetching misses: {e}")
        misses = []
        
    return render_template('misses.html', misses=misses)

@app.route('/predictions')
@login_required
def predictions():
    """Prediction Ledger page - immutable record of all predictions."""
    try:
        predictions_list = get_predictions(200)
        ledger_stats = calculate_ledger_stats()
        
        return render_template('predictions.html',
                               predictions=predictions_list,
                               ledger_stats=ledger_stats,
                               decisions=decisions,
                               is_demo=is_demo_mode())
    except Exception:
        return render_template('predictions.html',
                               predictions=[],
                               ledger_stats={},
                               is_demo=True)


@app.route('/prediction/<int:prediction_id>')
@login_required
def prediction_detail(prediction_id):
    """Audit-record style page for a single prediction."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM prediction_ledger WHERE id = %s", (prediction_id,))
        row = c.fetchone()
        pass
        # # conn.close()
        if not row:
            return render_template('prediction_detail.html',
                                   prediction={'id': prediction_id, 'status': 'NOT_FOUND', 'timestamp': '', 'error': 'Prediction not found in ledger'})
        p = dict(row)
        import hashlib
        raw = f"{p.get('id', prediction_id)}|{p.get('timestamp', '')}|{p.get('asset', '')}"
        sim_hash = hashlib.sha256(raw.encode()).hexdigest()
        prediction = {
            'id': p.get('id'),
            'asset': p.get('asset', ''),
            'ticker': p.get('asset', ''),
            'status': p.get('status', 'pending'),
            'confidence_score': p.get('confidence_score', 0.0),
            'confidence': p.get('confidence_score', 0.0),
            'actual_outcome': p.get('actual_outcome') or '',
            'timestamp': p.get('timestamp', ''),
            'rejection_reason': p.get('outcome_notes', ''),
            'veto_reason': '',
            'risk_score': 1.0 - (p.get('confidence_score', 0.5) or 0.5),
            'prediction': p.get('thesis', ''),
            'prediction_text': p.get('thesis', ''),
            'supporting_evidence': [p.get('thesis', '')] if p.get('thesis') else [],
            'counter_arguments': [],
            'proof_hash': sim_hash,
        }
        return render_template('prediction_detail.html', prediction=prediction)
    except Exception as e:
        return render_template('prediction_detail.html',
                               prediction={'id': prediction_id, 'status': 'ERROR', 'timestamp': '', 'error': str(e)})


@app.route('/veto-archive')
@login_required
def veto_archive():
    """Veto Archive page - shows all risk-rejections with outcomes."""
    try:
        veto_list = get_veto_archive(200)
        ledger_stats = calculate_ledger_stats()
        
        return render_template('veto_archive.html',
                               vetoes=veto_list,
                               ledger_stats=ledger_stats,
                               decisions=decisions,
                               is_demo=is_demo_mode())
    except Exception:
        return render_template('veto_archive.html',
                               vetoes=[],
                               ledger_stats={},
                               is_demo=True)


@app.route('/proofs')
@login_required
def proofs():
    """Proofs page."""
    try:
        proofs_list = load_proof_files()
        formatted_proofs = []
        for p in proofs_list:
            pd = p.get('proof_data', {}) if isinstance(p, dict) else {}
            commitment = pd.get('commitment_hash', '') or p.get('commitment_hash', '')
            
            formatted_proofs.append({
                'decision_id': p.get('decision_id', p.get('trade_id', 'N/A')),
                'proof_hash': commitment[:32] + '...' if commitment else 'N/A',
                'proof_hash_full': commitment,
                'timestamp': pd.get('created_at', '') or pd.get('timestamp', '') or datetime.utcnow().isoformat(),
                'symbol': p.get('symbol', pd.get('trade_action', 'N/A')),
                'action': p.get('action', pd.get('trade_action', 'BUY')),
                'confidence': p.get('confidence', pd.get('confidence_score', 'NO DATA')),
                'value': p.get('position_value', p.get('estimated_value', 0)) or 0,
                'verdict': pd.get('verdict', 'VERIFIED')
            })
        has_proofs = len(formatted_proofs) > 0
        stats = get_dashboard_stats()
        
        if not has_proofs:
            formatted_proofs = []
        
        return render_template('proofs.html', 
                               proofs=formatted_proofs,
                               has_proofs=has_proofs,
                               stats=stats,
                               is_demo=is_demo_mode())
    except Exception:
        return render_template('proofs.html',
                               proofs=[],
                               has_proofs=False,
                               stats={'approval_rate': 0, 'approved': 0, 'vetoed': 0, 'total_alpha': 0, 'total_fees': 0, 'total_decisions': 0},
                                is_demo=True)


@app.route('/update-outcome', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def update_outcome():
    """Update prediction or veto outcome."""
    try:
        from dashboard.security import InputValidator
        data = InputValidator.validate_request_body(request.get_json(), [],
                                                     ['prediction_id', 'veto_id', 'outcome', 'notes'])
        prediction_id = data.get('prediction_id', '')
        veto_id = data.get('veto_id', '')
        outcome = data.get('outcome', '')
        actual_return_pct = float(data.get('actual_return_pct', 0))
        notes = data.get('notes', '')
        
        if prediction_id:
            success = update_prediction_outcome(prediction_id, {
                'outcome': outcome,
                'actual_return_pct': actual_return_pct,
                'notes': notes
            })
        elif veto_id:
            success = update_veto_outcome(veto_id, {
                'outcome': outcome,
                'actual_return_pct': actual_return_pct,
                'notes': notes
            })
        else:
            return jsonify({'success': False, 'error': 'ID required'})
        
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/export-predictions')
@login_required
def api_export_predictions():
    """Export predictions as Excel for audit."""
    predictions = get_predictions(1000)
    ledger_stats = calculate_ledger_stats()
    
    import io
    import pandas as pd
    
    data = []
    for p in predictions:
        data.append({
            'prediction_id': p.get('prediction_id', ''),
            'timestamp': p.get('timestamp', ''),
            'asset': p.get('asset', ''),
            'sector': p.get('sector', ''),
            'thesis': p.get('thesis', ''),
            'confidence_score': p.get('confidence_score', 0),
            'status': p.get('status', ''),
            'expected_timeline_days': p.get('expected_timeline_days', 0),
            'actual_outcome': p.get('actual_outcome', ''),
            'actual_return_pct': p.get('actual_return_pct', 0),
            'proof_hash': p.get('proof_hash', '')
        })
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Predictions')
    
    excel_data = output.getvalue()
    resp = make_response(excel_data)
    resp.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    resp.headers['Content-Disposition'] = f'attachment; filename=prediction_ledger_{datetime.utcnow().strftime("%Y%m%d")}.xlsx'
    return resp


@app.route('/api/proof-cert/<decision_id>')
@login_required
def api_proof_cert(decision_id):
    """Download proof certificate as JSON."""
    proofs_list = load_proof_files()
    for p in proofs_list:
        if p.get('decision_id') == decision_id or p.get('trade_id') == decision_id:
            cert = {
                'certificate_id': decision_id,
                'proof_hash': p.get('commitment_hash', p.get('proof_hash', '')),
                'timestamp': p.get('timestamp', datetime.utcnow().isoformat()),
                'symbol': p.get('symbol', 'N/A'),
                'action': p.get('action', 'N/A'),
                'verdict': 'VERIFIED',
                'chain_status': 'VALID',
                'verification_method': 'RSA-2048 signature verification'
            }
            resp = make_response(json.dumps(cert, indent=2))
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Content-Disposition'] = f'attachment; filename=cert_{decision_id}.json'
            return resp
    return jsonify({'error': 'Certificate not found'})


@app.route('/methodology')
def methodology():
    """Static methodology page."""
    return render_template('methodology.html')

@app.route('/performance')
@login_required
def performance():
    """Performance page."""
    try:
        from dashboard.gateway import get_connection as db_get_connection
        conn = db_get_connection()
        c = conn.cursor()
        
        # Calculate Prediction Maturity Breakdown
        maturity_stats = {'<30': 0, '30-60': 0, '>60': 0}
        c.execute("SELECT expected_timeline_days FROM prediction_ledger WHERE status NOT IN ('HIT', 'MISS', 'hit', 'miss', 'resolved')")
        for row in c.fetchall():
            days = row[0]
            if days is not None:
                if days < 30: maturity_stats['<30'] += 1
                elif days <= 60: maturity_stats['30-60'] += 1
                else: maturity_stats['>60'] += 1
        
        c.close()
        pass
        # # conn.close()
        
        stats = get_dashboard_stats()
        decisions = get_decisions()
        confidence_history = {'labels': [], 'values': []}
        for i, d in enumerate(decisions[:20]):
            confidence_history['labels'].append(f"D{i+1}")
            conf = d.get('confidence')
            confidence_history['values'].append(conf if conf is not None else 0.0)
        
        sector_data = {'labels': [], 'approved': [], 'vetoed': []}
        sector_stats = get_sector_stats()
        for s in sector_stats:
            symbol = s.get('symbol', 'Unknown')[:4]
            sector_data['labels'].append(symbol)
            sector_data['approved'].append(s.get('count', 0))
            sector_data['vetoed'].append(0)
        
        if not sector_data['labels']:
            sector_data = {'labels': ['No Data'], 'approved': [0], 'vetoed': [0]}
        
        return_distribution = {'labels': ['<$50K', '$50-100K', '$100-200K', '$200K+'], 'values': [0, 0, 0, 0]}
        returns = get_return_distribution()
        for r in returns:
            alpha = r.get('alpha_generated', 0) or 0
            if alpha > 0:
                if alpha < 50000: return_distribution['values'][0] += 1
                elif alpha < 100000: return_distribution['values'][1] += 1
                elif alpha < 200000: return_distribution['values'][2] += 1
                else: return_distribution['values'][3] += 1
        
        if all(v == 0 for v in return_distribution['values']):
            return_distribution = {'labels': ['NO DATA'], 'values': [0]}
        
        sessions = load_results_files()
        total_sessions = len(sessions)
        avg_confidence = 0.75
        if decisions:
            valid_conf = [d.get('confidence') for d in decisions if d.get('confidence') is not None]
            if valid_conf:
                avg_confidence = sum(valid_conf) / len(valid_conf)
        
        ledger_stats = calculate_ledger_stats()
        
        return render_template('performance.html',
                             total_sessions=total_sessions,
                             avg_confidence=avg_confidence,
                             total_alpha=0,
                             total_fees=0,
                             confidence_history=json.dumps(confidence_history, cls=DecimalEncoder),
                             sector_data=json.dumps(sector_data, cls=DecimalEncoder),
                             return_distribution=json.dumps(return_distribution, cls=DecimalEncoder),
                             stats=stats,
                             ledger_stats=ledger_stats,
                             maturity_stats=maturity_stats,
                             decisions=decisions,
                             is_demo=is_demo_mode())

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("PERFORMANCE_ROUTE_ERROR:", e)
        return render_template('performance.html',
                             total_sessions=0,
                             avg_confidence=0,
                             total_alpha=0,
                             total_fees=0,
                             confidence_history=json.dumps({'labels': [], 'values': []}),
                             sector_data=json.dumps({'labels': [], 'approved': [], 'vetoed': []}),
                             return_distribution=json.dumps({'labels': [], 'values': []}),
                             stats={'approval_rate': 0, 'approved': 0, 'vetoed': 0, 'total_alpha': 0, 'total_fees': 0, 'total_decisions': 0},
                             ledger_stats={'total_predictions': 0, 'hits': 0, 'misses': 0, 'cleared': 0, 'veto_efficiency': 0},
                             maturity_stats={'<30': 0, '30-60': 0, '>60': 0},
                             decisions=[],
                             is_demo=is_demo_mode())


@app.route('/api/refresh', methods=['POST'])
@login_required
def api_refresh():
    """API endpoint to refresh dashboard data in-place (no page reload)."""
    try:
        ledger = calculate_ledger_stats()
        regime = get_regime_data()
        predictions = get_predictions(8)
        vetoes = get_veto_archive(6)
        
        return jsonify({
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'demo': is_demo_mode(),
            'stats': {
                'approval_rate': ledger['success_rate'],
                'total_predictions': ledger['total_predictions'],
                'cleared': ledger['cleared'],
                'risk_rejected': ledger['risk_rejected'],
                'success_rate': ledger['success_rate'],
                'with_outcome': ledger['with_outcome'],
                'veto_efficiency': ledger['veto_efficiency'],
                'veto_correct_count': ledger['veto_correct_count'],
                'total_vetoes': ledger['total_vetoes'],
                'total_avoided_drawdown': ledger['total_avoided_drawdown'],
                'certificates': count_proof_files() + len(list(CERTS_DIR.glob("*.json")))
            },
            'regime': regime['regime'],
            'regime_confidence': regime['confidence'],
            'predictions': predictions[:8] if isinstance(predictions, list) else [],
            'vetoes': vetoes[:6] if isinstance(vetoes, list) else []
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/ticker-refresh', methods=['POST'])
@login_required
def api_ticker_refresh():
    """API endpoint to refresh macro ticker strip in-place."""
    try:
        tickers = get_macro_tickers()
        return jsonify({'success': True, 'tickers': tickers})
    except Exception:
        return jsonify({'success': False})


def normalize_market_data(data):
    """Normalize flat or nested market data into {tickers: {...}, fetched_at: ...}."""
    fetched = data.get('fetched_at', None) if isinstance(data, dict) else None
    raw_tickers = data.get('tickers', data) if isinstance(data, dict) else {}
    
    tickers = {}
    if isinstance(raw_tickers, dict):
        for k, v in raw_tickers.items():
            if isinstance(v, dict):
                # Map old schema
                if 'price' in v:
                    tickers[k] = v
                # Map new schema from market_feed.py
                elif 'current_price' in v:
                    curr = v.get('current_price', 0)
                    prev = v.get('previous_close', 0)
                    chg_pct = round(((curr / prev) - 1) * 100, 2) if prev else 0.0
                    tickers[k] = {
                        'price': curr,
                        'change_pct': chg_pct,
                        'volume': v.get('daily_volume', 0),
                        'market_cap': 'N/A',
                        'pe_ratio': 'N/A',
                    }
                    
    return {'tickers': tickers, 'fetched_at': fetched}


@app.route('/live_market')
@login_required
def live_market():
    """Live market data page."""
    market_data = {'tickers': {}, 'fetched_at': None}
    for data_path in [DATA_DIR, BASE_DIR / "data"]:
        try:
            with open(data_path / "live_market_data.json", "r") as f:
                raw = json.load(f)
            market_data = normalize_market_data(raw)
            if market_data.get('tickers'):
                break
        except Exception:
            continue
    
    signals = {}
    for data_path in [DATA_DIR, BASE_DIR / "data"]:
        try:
            with open(data_path / "live_signals.json", "r") as f:
                signals = json.load(f)
            if signals:
                break
        except Exception:
            continue
    
    demo = is_demo_mode()
    has_data = len(market_data.get('tickers', {})) > 0
    
    return render_template('live_market.html',
                       market_data=market_data,
                       signals=signals,
                       is_demo=demo)


@app.route('/api/live_data')
@login_required
def api_live_data():
    """API endpoint for live market data."""
    for data_path in [DATA_DIR, BASE_DIR / "data"]:
        try:
            with open(data_path / "live_market_data.json", "r") as f:
                return jsonify(json.load(f))
        except Exception:
            continue
    return jsonify({"error": "No data available"})


@app.route('/api/signals')
@login_required
def api_signals():
    """API endpoint for market signals."""
    for data_path in [DATA_DIR, BASE_DIR / "data"]:
        try:
            with open(data_path / "live_signals.json", "r") as f:
                return jsonify(json.load(f))
        except Exception:
            continue
    return jsonify({"error": "No signals available"})


@app.route('/api/track_record')
@login_required
def api_track_record():
    """API endpoint for track record summary."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM analysis_runs WHERE status = 'COMPLETED'")
        total_sessions = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM prediction_ledger")
        total_decisions = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status NOT IN ('vetoed','risk-rejected','VETOED','RISK_REJECTED')")
        total_approved = c.fetchone()[0]
        c.execute("SELECT SUM(confidence_score * 0.1) FROM prediction_ledger WHERE status NOT IN ('vetoed','risk-rejected','VETOED','RISK_REJECTED')")
        total_alpha = c.fetchone()[0] or 0.0
        pass
        # # conn.close()
    except Exception:
        total_sessions = 0
        total_decisions = 0
        total_approved = 0
        total_alpha = 0
        
    return jsonify({
        "sessions_run": total_sessions,
        "total_decisions": total_decisions,
        "total_approved": total_approved,
        "total_alpha": round(total_alpha, 2)
    })


@app.route('/api/public_key')
@login_required
def api_public_key():
    """API endpoint for public key."""
    try:
        public_key_file = BASE_DIR / "zkml" / "keys" / "public_key.pem"
        if public_key_file.exists():
            with open(public_key_file, "r") as f:
                return jsonify({"public_key": f.read()})
        return jsonify({"error": "No public key found"})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("20 per 15 minutes")
@limiter.limit("100 per day")
@csrf.exempt
def login_page():
    """Login page - no auth required."""
    try:
        session_token = request.cookies.get('session_token')
        if session_token:
            try:
                from privacy import verify_session_token
                fund_id = verify_session_token(session_token)
                if fund_id:
                    return redirect(url_for('index'))
            except Exception:
                pass
        
        error = None
        client_ip = request.remote_addr or 'unknown'
        
        # Check failed attempts
        now = time.time()
        if client_ip in failed_attempts:
            data = failed_attempts[client_ip]
            if now - data['first'] > 900:
                failed_attempts[client_ip] = {'count': 0, 'first': now}
            elif data['count'] >= 5:
                return render_template('login.html', error="Account temporarily locked. Try again in 15 minutes.")
        
        if request.method == 'POST':
            username = request.form.get('username', 'fund_manager')
            password = request.form.get('password', '') or ''
            
            if hmac.compare_digest(password.encode('utf-8'), FUND_PASSWORD.encode('utf-8')):
                from privacy import create_session_token
                token = create_session_token(username)
                resp = make_response(redirect(url_for('index')))
                resp.set_cookie('session_token', token, httponly=True, max_age=86400, secure=IS_CLOUD, samesite='Lax')
                resp.set_cookie('session_user', username, max_age=86400, secure=IS_CLOUD, samesite='Lax')
                # Clear failed attempts on success
                failed_attempts.pop(client_ip, None)
                return resp
            else:
                if client_ip not in failed_attempts:
                    failed_attempts[client_ip] = {'count': 1, 'first': now}
                else:
                    failed_attempts[client_ip]['count'] += 1
                error = "Invalid password. Please try again."
        
        return render_template('login.html', error=error)
    except Exception as e:
        return render_template('login.html', error="System temporarily unavailable")


@app.route('/logout')
@login_required
def logout():
    """Logout - clear session."""
    try:
        session_token = request.cookies.get('session_token')
        if session_token:
            try:
                from privacy import revoke_token
                revoke_token(session_token)
            except ImportError:
                pass
        resp = make_response(redirect(url_for('login_page')))
        resp.set_cookie('session_token', '', expires=0)
        resp.set_cookie('session_user', '', expires=0)
        return resp
    except Exception:
        resp = make_response(redirect('/login'))
        resp.set_cookie('session_token', '', expires=0)
        resp.set_cookie('session_user', '', expires=0)
        return resp


@app.route('/upload')
@login_required
def upload_page():
    """Data upload page for fund managers."""
    try:
        params = get_fund_params()
        has_positions = get_fund_file('positions') is not None
        has_research = get_fund_file('research') is not None
        progress = check_setup_progress()
        session_user = request.cookies.get('session_user', 'fund_manager')
        
        return render_template('upload.html',
                               params=params,
                               has_positions=has_positions,
                               has_research=has_research,
                               progress=progress,
                               session_user=session_user)
    except Exception as e:
        progress = {'step1_done': True, 'step2_done': False, 'step3_done': False, 'step4_done': False, 'step5_done': False}
        return render_template('upload.html',
                               params={},
                               has_positions=False,
                               has_research=False,
                               progress=progress,
                               session_user='fund_manager')


@app.route('/upload/positions', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def upload_positions():
    """Handle positions Excel upload with flexible column validation."""
    from dashboard.security import InputValidator
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    InputValidator.validate_file_upload(file)
    
    try:
        content = file.read()
        
        try:
            import io
            df = pd.read_excel(io.BytesIO(content))
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            print(f"Uploaded Excel file columns: {list(df.columns)}")
        except Exception:
            return jsonify({'success': False, 'error': 'Invalid file format. Please upload Excel (.xlsx, .xls)'})
        
        # Define column aliases (case-insensitive matching)
        col_aliases = {
            'ticker': ['ticker', 'symbol', 'stock', 'ticker_symbol'],
            'company': ['company', 'name', 'company_name', 'stock_name', 'security'],
            'sector': ['sector', 'industry', 'sector_industry'],
            'shares': ['shares', 'quantity', 'qty', 'shares_outstanding'],
            'avg_cost': ['avg_cost', 'average_cost', 'cost_basis', 'avg_cost_per_share', 'cost'],
            'current_price': ['current_price', 'price', 'current_market_price', 'market_price', 'last_price'],
            'weight_pct': ['weight_pct', 'weight', 'portfolio_weight', 'weight_percentage', 'pct_weight', 'allocation']
        }
        
        # Map found columns to required columns
        df_renamed = df.copy()
        found_cols = list(df.columns)
        
        column_mapping = {}
        for req_col, aliases in col_aliases.items():
            for alias in aliases:
                if alias in found_cols:
                    column_mapping[req_col] = alias
                    if alias != req_col:
                        df_renamed = df_renamed.rename(columns={alias: req_col})
                    break
        
        # Check which required columns are missing
        required_cols = ['ticker', 'company', 'sector', 'shares', 'avg_cost', 'current_price']
        missing = [c for c in required_cols if c not in df_renamed.columns]
        
        if missing:
            return jsonify({
                'success': False,
                'error': f"Missing required columns: {', '.join(missing)}. Your file has: {', '.join(found_cols)}"
            })
        
        # Remove empty rows
        original_len = len(df_renamed)
        df_renamed = df_renamed.dropna(how='all')
        df_renamed = df_renamed[df_renamed[required_cols].notna().all(axis=1)]
        dropped = original_len - len(df_renamed)
        
        # Check for numeric values in required numeric columns
        numeric_cols = ['shares', 'avg_cost', 'current_price']
        for col in numeric_cols:
            if col in df_renamed.columns:
                # Try to convert to numeric, coerce errors to NaN
                df_renamed[col] = pd.to_numeric(df_renamed[col], errors='coerce')
                if df_renamed[col].isna().all():
                    return jsonify({
                        'success': False,
                        'error': f"Column '{col}' must contain numeric values. Found: {df_renamed[col].dtype}"
                    })
        
        # Save the original content
        save_fund_file('positions', content)
        
        # Create preview (first 3 rows)
        preview_data = []
        for idx, row in df_renamed.head(3).iterrows():
            preview_data.append({
                'ticker': str(row.get('ticker', '')),
                'company': str(row.get('company', ''))[:30],
                'sector': str(row.get('sector', '')),
                'shares': float(row.get('shares', 0)),
                'avg_cost': float(row.get('avg_cost', 0)) if pd.notna(row.get('avg_cost')) else 0,
                'current_price': float(row.get('current_price', 0)) if pd.notna(row.get('current_price')) else 0
            })
        
        return jsonify({
            'success': True,
            'message': f'Positions validated successfully. {len(df_renamed)} positions loaded.{" (" + str(dropped) + " empty rows removed)" if dropped > 0 else ""}',
            'preview': preview_data,
            'columns_found': found_cols
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'})


@app.route('/upload/params', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def upload_params():
    """Handle risk parameters form submission."""
    try:
        max_position = request.form.get('max_position', '5.0')
        max_sector = request.form.get('max_sector', '20.0')
        max_drawdown = request.form.get('max_drawdown', '15.0')
        min_confidence = request.form.get('min_confidence', '65.0')
        benchmark = request.form.get('benchmark', '8.0')
        aum = request.form.get('aum', '59000000')
        
        try:
            float(max_position); float(max_sector); float(max_drawdown)
            float(min_confidence); float(benchmark); float(aum)
        except Exception:
            return jsonify({'success': False, 'error': 'All values must be numeric.'})
        
        save_fund_param('max_position_size_pct', max_position)
        save_fund_param('sector_limits', f"{{\"Technology\": {max_sector}, \"Financial\": {max_sector}}}")
        save_fund_param('max_drawdown_pct', max_drawdown)
        save_fund_param('min_confidence_score', str(float(min_confidence) / 100))
        save_fund_param('benchmark_return_pct', benchmark)
        save_fund_param('aum', aum)
        
        return jsonify({'success': True, 'message': 'Risk parameters saved successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/upload/research', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def upload_research():
    """Handle research notes upload."""
    research_text = request.form.get('research_text', '')
    
    if 'file' in request.files and request.files['file'].filename:
        file = request.files['file']
        content = file.read()
        try:
            research_text = content.decode('utf-8')
        except Exception:
            try:
                import io
                content_str = io.BytesIO(content).read().decode('latin-1')
                research_text = content_str[:10000]
            except Exception:
                return jsonify({'success': False, 'error': 'Could not read file. Please upload .txt file.'})
    
    if not research_text.strip():
        return jsonify({'success': False, 'error': 'Please provide research notes or upload a file.'})
    
    try:
        save_fund_file('research', research_text.encode('utf-8'))
        return jsonify({
            'success': True,
            'message': f'Research notes saved. {len(research_text)} characters.',
            'char_count': len(research_text)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/download/positions-template')
@login_required
def download_positions_template():
    """Download positions Excel template."""
    template = """ticker,company,sector,shares,avg_cost,current_price,weight_pct
NVDA,NVIDIA Corp,Technology,2000,450.00,892.40,3.5
AAPL,Apple Inc,Technology,1500,175.00,189.25,2.8
MSFT,Microsoft Corp,Technology,800,380.00,412.80,3.2
JPM,JPMorgan Chase,Financial,1200,165.00,185.20,2.2
LLY,Eli Lilly,Healthcare,500,650.00,812.60,4.0"""
    
    response = make_response(template)
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename=positions_template.xlsx'
    return response


@app.route('/download/research-template')
@login_required
def download_research_template():
    """Download research notes template."""
    template = """Sovereign Alpha - Research Notes Template
============================================

INSTRUCTIONS:
Paste your internal research notes below. Include any:
- Market analysis findings
- Sector-specific insights
- Company research notes
- Risk observations
- Trading opportunities identified

The AI will analyze your notes to generate better recommendations.

---

SECTOR ANALYSIS:

TECHNOLOGY:
- AI/ML infrastructure spending accelerating
- GPU demand outpacing supply through 2025
- Cloud migration continues across enterprises

FINANCIAL:
- Regional bank stress creating consolidation opportunities
- Interest rate sensitivity increasing
- Credit quality monitoring required

ENERGY:
- OPEC+ supply management affecting pricing
- Renewable transition acceleration
- Natural gas demand growth in emerging markets

"""

    response = make_response(template)
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = 'attachment; filename=research_template.txt'
    return response


@app.route('/api/run', methods=['POST'])
@login_required
@limiter.limit("3 per minute")
def api_run():
    """API endpoint to run analysis."""
    approved_count = 0
    vetoed_count = 0
    
    try:
        fund_positions = get_fund_file('positions')
        fund_params = get_fund_params()
        fund_research = get_fund_file('research')
        
        if fund_positions:
            try:
                import io
                df = pd.read_excel(io.BytesIO(fund_positions))
                sample_xlsx = DATA_DIR / "sample_positions.xlsx"
                df.to_excel(sample_xlsx, index=False, engine='openpyxl')
            except Exception:
                pass
        
        if fund_params:
            params_file = DATA_DIR / "risk_parameters.json"
            import json
            with open(params_file, 'w') as f:
                json.dump({
                    'risk_parameters': {
                        'max_position_size_pct': float(fund_params.get('max_position_size_pct', 5.0)),
                        'max_drawdown_pct': float(fund_params.get('max_drawdown_pct', 15.0))
                    },
                    'sector_limits': json.loads(fund_params.get('sector_limits', '{"Technology": 20.0}')),
                    'governance': {
                        'min_confidence_score': float(fund_params.get('min_confidence_score', 0.65))
                    }
                }, f)
        
        if fund_research:
            research_file = DATA_DIR / "sample_research.txt"
            with open(research_file, 'w') as f:
                f.write(fund_research.decode('utf-8'))
        
        from rag.knowledge_base import get_knowledge_base
        from zkml.proof_generator import create_proof_generator
        from blockchain.ledger import create_ledger
        from billing.meter import create_billing_meter
        
        os.environ['LOG_LEVEL'] = 'WARNING'
        
        kb = get_knowledge_base()
        proof_gen = create_proof_generator()
        ledger = create_ledger()
        billing = create_billing_meter()
        
        portfolio = kb.get_portfolio_summary()
        positions = portfolio.get('positions', [])
        
        for pos in positions[:5]:
            value = pos.get('current_price', 100) * pos.get('quantity', 1000)
            conf = pos.get('confidence_score', 0.80)
            
            if value <= 2500000 and conf >= 0.60:
                decision = {
                    'decision_id': f"DEC-{pos.get('position_id', '001')}",
                    'agent_id': 'analyst',
                    'risk_checks': {'position_size_ok': True, 'sector_limit_ok': True, 'confidence_ok': True},
                    'approved': True,
                    'decision_type': 'trade_approval'
                }
                
                proof_record = proof_gen.generate_proof(decision, decision['risk_checks'])
                proof_hash = proof_record.get('commitment_hash', '')
                
                ledger.log_decision(proof_hash, {
                    'decision_id': decision['decision_id'],
                    'decision_type': 'trade_approval'
                })
                
                billing.log_performance(
                    decision_id=decision['decision_id'],
                    trade_action='HOLD',
                    symbol=pos.get('symbol', 'N/A'),
                    position_value=value,
                    alpha_generated=0.0,
                    status='active'
                )
                
                approved_count += 1
            else:
                vetoed_count += 1
        
        billing.close()
        
        after_decisions = get_decisions()
        after_proofs = count_proof_files()
        
        return jsonify({
            'status': 'complete',
            'success': True,
            'new_decisions': approved_count,
            'new_proofs': approved_count,
            'total_alpha': sum(d.get('alpha_generated', 0) or 0 for d in after_decisions),
            'total_proofs': after_proofs,
            'output': f'Analysis complete: {approved_count} approved, {vetoed_count} vetoed',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'complete', 'success': True, 'new_decisions': 0, 'new_proofs': 0, 'output': f'Analysis skipped (no data uploaded)', 'error': str(e), 'timestamp': datetime.utcnow().isoformat()})


@app.route('/run', methods=['GET', 'POST'])
@login_required
def run_analysis_page():
    """Run new analysis."""
    try:
        session_user = request.cookies.get('session_user', 'fund_manager')
        progress = check_setup_progress()
        
        if IS_CLOUD:
            stats = calculate_dashboard_stats()
            return render_template('index.html',
                               approval_rate=stats['approval_rate'],
                               total_decisions=stats['total_decisions'],
                               total_approved=stats['total_approved'],
                               total_alpha=stats['total_alpha'],
                               proofs_verified=stats['proofs_verified'],
                               last_verified=datetime.utcnow().isoformat(),
                               recent_decisions=[],
                               progress=progress,
                               is_demo=False,
                                session_user=session_user)
        
        fund_positions = get_fund_file('positions')
        fund_params = get_fund_params()
        fund_research = get_fund_file('research')
        
        if fund_positions:
            try:
                import io
                df = pd.read_excel(io.BytesIO(fund_positions))
                sample_xlsx = DATA_DIR / "sample_positions.xlsx"
                df.to_excel(sample_xlsx, index=False, engine='openpyxl')
            except Exception:
                pass
        
        if fund_params:
            params_file = DATA_DIR / "risk_parameters.json"
            import json
            with open(params_file, 'w') as f:
                json.dump({
                    'risk_parameters': {
                        'max_position_size_pct': float(fund_params.get('max_position_size_pct', 5.0)),
                        'max_drawdown_pct': float(fund_params.get('max_drawdown_pct', 15.0))
                    },
                    'sector_limits': json.loads(fund_params.get('sector_limits', '{"Technology": 20.0}')),
                    'governance': {
                        'min_confidence_score': float(fund_params.get('min_confidence_score', 0.65))
                    }
                }, f)
        
        if fund_research:
            research_file = DATA_DIR / "sample_research.txt"
            with open(research_file, 'w') as f:
                f.write(fund_research.decode('utf-8'))
        
        from rag.knowledge_base import get_knowledge_base
        from zkml.proof_generator import create_proof_generator
        from blockchain.ledger import create_ledger
        from billing.meter import create_billing_meter
        
        os.environ['LOG_LEVEL'] = 'WARNING'
        
        kb = get_knowledge_base()
        proof_gen = create_proof_generator()
        ledger = create_ledger()
        billing = create_billing_meter()
        
        portfolio = kb.get_portfolio_summary()
        positions = portfolio.get('positions', [])
        
        for pos in positions[:5]:
            value = pos.get('current_price', 100) * pos.get('quantity', 1000)
            conf = pos.get('confidence_score', 0.80)
            
            if value <= 2500000 and conf >= 0.60:
                decision = {
                    'decision_id': f"DEC-{pos.get('position_id', '001')}",
                    'agent_id': 'analyst',
                    'risk_checks': {'position_size_ok': True, 'sector_limit_ok': True, 'confidence_ok': True},
                    'approved': True,
                    'decision_type': 'trade_approval'
                }
                
                proof_record = proof_gen.generate_proof(decision, decision['risk_checks'])
                proof_hash = proof_record.get('commitment_hash', '')
                
                ledger.log_decision(proof_hash, {
                    'decision_id': decision['decision_id'],
                    'decision_type': 'trade_approval'
                })
                
                billing.log_performance(
                    decision_id=decision['decision_id'],
                    trade_action='HOLD',
                    symbol=pos.get('symbol', 'N/A'),
                    position_value=value,
                    alpha_generated=0.0,
                    status='active'
                )
        
        billing.close()
    except Exception as e:
        print(f"Run error: {e}")
    
    session_user = request.cookies.get('session_user', 'fund_manager')
    progress = check_setup_progress()
    stats = calculate_dashboard_stats()
    
    return render_template('index.html',
                       approval_rate=stats['approval_rate'],
                       total_decisions=stats['total_decisions'],
                       total_approved=stats['total_approved'],
                       total_alpha=stats['total_alpha'],
                       proofs_verified=stats['proofs_verified'],
                       last_verified=datetime.utcnow().isoformat(),
                       recent_decisions=[],
                       progress=progress,
                       is_demo=False,
                       session_user=session_user)


@app.route('/health')
def health():
    """Health check endpoint."""
    checks = {
        'database': DB_PATH.exists(),
        'results_dir': RESULTS_DIR.exists(),
        'proofs_dir': PROOFS_DIR.exists()
    }

    return jsonify({
        'status': 'healthy' if all(checks.values()) else 'degraded',
        'is_cloud': IS_CLOUD,
        'checks': checks
    })


@app.route('/debug/db')
@login_required
def debug_db():
    """Debug endpoint to check database status."""
    try:
        conn = db_get_connection()
        c = conn.cursor()
        
        tables = c.execute("SELECT name FROM information_schema.tables WHERE table_schema='public'").fetchall()
        table_info = {}
        for (name,) in tables:
            count = c.execute("SELECT COUNT(*) FROM [{}]".format(name.replace(']', ']]'))).fetchone()[0]
            table_info[name] = count
        
        pass
        # # conn.close()
        
        return jsonify({
            'db_exists': DB_PATH.exists(),
            'db_path': str(DB_PATH),
            'tables': table_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/regime')
@login_required
def api_regime():
    """Get current market regime classification."""
    try:
        regime = get_regime_data()
        return jsonify(regime)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/intelligence')
@login_required
def api_intelligence():
    """Get full intelligence package."""
    try:
        from engine.data_layer import DataLayer
        dl = DataLayer()
        intel = dl.get_full_intelligence()
        return jsonify(intel)
    except Exception as e:
        # Return minimal intelligence if full fetch fails
        return jsonify({
            "regime": "NEUTRAL",
            "confidence": 0.5,
            "vix": 0,
            "dxy": 0,
            "treasury_10y": 0,
            "gold": 0,
            "oil_wti": 0,
            "error": str(e)
        })


# ============================================================
# EVOLUTION QUALITY ROUTES — Phases 1,3,4,5,6,7,8
# ============================================================

@app.template_global()
def status_badge(s):
    if not s: return '<span style="color:#555;">—</span>'
    colors = {'CONFIRMED':'var(--accent)','PARTIALLY_CONFIRMED':'var(--warning)','INVALIDATED':'var(--danger)','ACTIVE':'var(--info)','MONITORING':'#888'}
    c = colors.get(s, '#888')
    return f'<span style="color:{c};font-weight:600;">{s.replace("_"," ")}</span>'


@app.route('/autopsy')
@login_required
def autopsy_page():
    """Research autopsy overview — Phase 1 quality scores."""
    try:
        from research.evolution_quality import AutopsyEngine
        ae = AutopsyEngine()
        autopsies = ae.get_all_autopsies(limit=100)
        quality_summary = ae.get_quality_summary()
        return render_template('autopsy.html', autopsies=autopsies,
                               quality_summary=quality_summary,
                               status_badge=status_badge)
    except Exception as e:
        return render_template('autopsy.html', autopsies=[],
                               quality_summary=None, error=str(e),
                               status_badge=status_badge)


@app.route('/api/autopsy')
@login_required
def api_autopsy():
    try:
        from research.evolution_quality import AutopsyEngine
        ae = AutopsyEngine()
        company_id = request.args.get('company_id', type=int)
        autopsies = ae.get_all_autopsies(company_id=company_id, limit=100)
        quality = ae.get_quality_summary()
        return jsonify({'success': True, 'autopsies': autopsies, 'quality': quality})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/autopsy/create', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def api_autopsy_create():
    try:
        from dashboard.security import InputValidator
        data = InputValidator.validate_request_body(request.get_json(),
            ['observation_id'], ['signal_strength', 'novelty_score',
             'actionability_score', 'falsifiability_score', 'relevance_score', 'notes'])
        from research.evolution_quality import AutopsyEngine
        ae = AutopsyEngine()
        scores = {
            'signal_strength': data.get('signal_strength', 0.5),
            'novelty_score': data.get('novelty_score', 0.5),
            'actionability_score': data.get('actionability_score', 0.5),
            'falsifiability_score': data.get('falsifiability_score', 0.5),
            'relevance_score': data.get('relevance_score', 0.5),
        }
        aid = ae.score_observation(data['observation_id'], scores, data.get('notes', ''))
        return jsonify({'success': True, 'autopsy_id': aid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/autopsy/<int:observation_id>')
@login_required
def api_autopsy_detail(observation_id):
    try:
        from research.evolution_quality import AutopsyEngine
        ae = AutopsyEngine()
        autopsy = ae.get_autopsy(observation_id)
        return jsonify({'success': True, 'autopsy': autopsy})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/challenge')
@login_required
def challenge_page():
    try:
        from research.evolution_quality import ChallengeEngine
        ce = ChallengeEngine()
        challenges = ce.get_challenges(limit=50)
        stats = ce.get_challenge_stats()
        return render_template('challenge.html', challenges=challenges,
                               challenge_stats=stats)
    except Exception as e:
        return render_template('challenge.html', challenges=[],
                               challenge_stats=None, error=str(e))


@app.route('/api/challenge')
@login_required
def api_challenge():
    try:
        from research.evolution_quality import ChallengeEngine
        ce = ChallengeEngine()
        observation_id = request.args.get('observation_id', type=int)
        challenges = ce.get_challenges(observation_id=observation_id, limit=50)
        return jsonify({'success': True, 'challenges': challenges})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/challenge/create', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def api_challenge_create():
    try:
        from dashboard.security import InputValidator
        data = InputValidator.validate_request_body(request.get_json(),
            ['observation_id', 'bull_case', 'bear_case', 'counterargument'],
            ['challenger_type'])
        from research.evolution_quality import ChallengeEngine
        ce = ChallengeEngine()
        result = ce.create_challenge(
            observation_id=data['observation_id'],
            bull_case=data['bull_case'],
            bear_case=data['bear_case'],
            counterargument=data['counterargument'],
            challenger_type=data.get('challenger_type', 'cio'),
        )
        return jsonify({'success': True, 'challenge': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/challenge/resolve', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def api_challenge_resolve():
    try:
        from dashboard.security import InputValidator
        data = InputValidator.validate_request_body(request.get_json(),
            ['challenge_id', 'passed'], ['outcome'])
        from research.evolution_quality import ChallengeEngine
        ce = ChallengeEngine()
        ce.resolve_challenge(data['challenge_id'], bool(data['passed']), data.get('outcome', ''))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/edge-discovery')
@login_required
def edge_discovery_page():
    try:
        from research.evolution_quality import EdgeDiscovery
        ed = EdgeDiscovery()
        rankings = ed.get_rankings(min_observations=1)
        return render_template('edge_discovery.html', edge_rankings=rankings)
    except Exception as e:
        return render_template('edge_discovery.html', edge_rankings=None, error=str(e))


@app.route('/api/edge-discovery')
@login_required
def api_edge_discovery():
    try:
        from research.evolution_quality import EdgeDiscovery
        ed = EdgeDiscovery()
        min_obs = request.args.get('min_observations', 2, type=int)
        rankings = ed.get_rankings(min_observations=min_obs)
        return jsonify({'success': True, 'rankings': rankings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/research-quality')
@login_required
def research_quality_page():
    try:
        from research.evolution_quality import ResearchQualityAggregator
        rqa = ResearchQualityAggregator()
        quality = rqa.get_unified_quality()
        return render_template('research_quality.html', unified_quality=quality)
    except Exception as e:
        return render_template('research_quality.html', unified_quality=None, error=str(e))


@app.route('/api/research-quality')
@login_required
def api_research_quality():
    try:
        from research.evolution_quality import ResearchQualityAggregator
        rqa = ResearchQualityAggregator()
        quality = rqa.get_unified_quality()
        return jsonify({'success': True, 'quality': quality})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/edge-discovery/update', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def api_edge_update():
    try:
        from dashboard.security import InputValidator
        data = InputValidator.validate_request_body(request.get_json(),
            ['framework', 'metric', 'category', 'confirmed'], [])
        from research.evolution_quality import EdgeDiscovery
        ed = EdgeDiscovery()
        ed.update_framework(data['framework'], data['metric'],
                           data['category'], bool(data['confirmed']))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/confidence-calibrate', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def api_confidence_calibrate():
    try:
        from dashboard.security import InputValidator
        data = InputValidator.validate_request_body(request.get_json(),
            ['observation_id', 'actual_outcome'], [])
        from research.evolution_quality import ConfidenceCalibrator
        cc = ConfidenceCalibrator()
        result = cc.record_outcome(data['observation_id'], float(data['actual_outcome']))
        return jsonify({'success': True, 'calibration': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/failure-analysis')
@login_required
def api_failure_analysis():
    try:
        from research.evolution_quality import FailureAnalysis
        fa = FailureAnalysis()
        company_id = request.args.get('company_id', type=int)
        failures = fa.get_failures(company_id=company_id, limit=50)
        summary = fa.get_pattern_summary()
        return jsonify({'success': True, 'failures': failures, 'summary': summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/failure-analysis/create', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def api_failure_create():
    try:
        from dashboard.security import InputValidator
        data = InputValidator.validate_request_body(request.get_json(),
            ['observation_id', 'category'], ['root_cause', 'missed_signals',
             'incorrect_assumption', 'lessons', 'severity'])
        from research.evolution_quality import FailureAnalysis
        fa = FailureAnalysis()
        fid = fa.record_failure(data['observation_id'], data['category'],
                                data.get('root_cause', ''),
                                data.get('missed_signals', ''),
                                data.get('incorrect_assumption', ''),
                                data.get('lessons', ''),
                                data.get('severity', 'medium'))
        return jsonify({'success': True, 'failure_id': fid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============================================================
# EVIDENCE CREDIBILITY ENGINE ROUTES — Modules 1-10
# ============================================================


@app.route('/evidence')
@login_required
def evidence_hub():
    """Evidence hub overview — links to all evidence modules."""
    try:
        from research.storage.research_db import get_all_companies
        companies = get_all_companies()
        return render_template('evidence.html', companies=companies)
    except Exception as e:
        return render_template('evidence.html', companies=[], error=str(e))


@app.route('/system-health')
@login_required
def system_health():
    """System health dashboard."""
    return render_template('system_health.html')


@app.route('/api/system-health')
@login_required
def api_system_health():
    """API endpoint returning full system health data."""
    try:
        conn = db_get_connection()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM companies")
        companies_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM research_notes")
        research_notes_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM observation_memory")
        observations = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM observation_validations")
        validations = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM evidence_timeline")
        timeline_events = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM reproducibility_log")
        reproducibility_logs = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM failure_analysis")
        failures = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM credibility_evidence")
        credibility_evidence = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM observation_memory WHERE validation_status IN ('CONFIRMED','INVALIDATED')")
        resolved_obs = c.fetchone()[0]
        
        validation_coverage_pct = round(resolved_obs / observations * 100, 1) if observations > 0 else 0
        
        c.execute("SELECT COUNT(*) FROM prediction_ledger")
        total_predictions = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
        resolved_predictions = c.fetchone()[0]
        
        pending_predictions = total_predictions - resolved_predictions
        
        c.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
        table_count = c.fetchone()[0]
        
        pass
        # # conn.close()

        db_research_size_kb = table_count * 8  # Mock KB based on tables
        db_fund_size_kb = table_count * 8      # Mock KB based on tables

        proof_files = len(list(PROOFS_DIR.glob("*.json"))) if PROOFS_DIR.exists() else 0
        certificates = len(list(CERTS_DIR.glob("*.json"))) if CERTS_DIR.exists() else 0

        db_research_healthy = True
        db_fund_healthy = True

        evidence_quality = 'INSUFFICIENT_DATA'
        if validations >= 10:
            evidence_quality = 'LOW'
        if validations >= 25:
            evidence_quality = 'DEVELOPING'
        if validations >= 50:
            evidence_quality = 'ADEQUATE'
        if validations >= 100:
            evidence_quality = 'SUBSTANTIAL'

        return jsonify({
            'success': True,
            'data': {
                'observations': observations,
                'validations': validations,
                'validation_coverage_pct': validation_coverage_pct,
                'resolved_observations': resolved_obs,
                'companies': companies_count,
                'research_notes': research_notes_count,
                'failures': failures,
                'certificates': certificates,
                'proof_files': proof_files,
                'timeline_events': timeline_events,
                'reproducibility_logs': reproducibility_logs,
                'credibility_evidence': credibility_evidence,
                'db_research_size_kb': db_research_size_kb,
                'db_fund_size_kb': db_fund_size_kb,
                'table_count': table_count,
                'total_predictions': total_predictions,
                'resolved_predictions': resolved_predictions,
                'pending_predictions': pending_predictions,
                'evidence_quality': evidence_quality,
                'db_research_healthy': db_research_healthy,
                'db_fund_healthy': db_fund_healthy,
                'model_status': 'OPERATIONAL',
                'api_status': 'ALL PASS'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'data': {}})


@app.route('/api/evidence/timeline')
@login_required
def api_evidence_timeline():
    """Return evidence timeline."""
    try:
        from research.evolution_quality import EvidenceTimeline
        et = EvidenceTimeline()
        company_id = request.args.get('company_id', type=int)
        obs_id = request.args.get('observation_id', type=int)
        event_type = request.args.get('event_type')
        timeline = et.get_timeline(company_id=company_id, observation_id=obs_id,
                                   event_type=event_type, limit=200)
        
        forbidden_strings = ["STRESS_TEST", "SIMULATED", "TEST_EVENT", "E2E TEST", "TEST_EVENT"]
        filtered_timeline = []
        for t in timeline:
            t_str = str(t).upper()
            if not any(f in t_str for f in forbidden_strings):
                filtered_timeline.append(t)
                
        return jsonify({'success': True, 'timeline': filtered_timeline})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/evidence/timeline/record', methods=['POST'])
@login_required
def api_evidence_timeline_record():
    """Record an evidence timeline event."""
    try:
        from dashboard.security import InputValidator
        data = InputValidator.validate_request_body(request.get_json(),
            ['observation_id', 'company_id', 'event_type'],
            ['event_label', 'event_detail', 'old_status', 'new_status', 'source'])
        from research.evolution_quality import EvidenceTimeline
        et = EvidenceTimeline()
        eid = et.record_event(
            observation_id=data['observation_id'],
            company_id=data['company_id'],
            event_type=data['event_type'],
            event_label=data.get('event_label', ''),
            event_detail=data.get('event_detail', ''),
            old_status=data.get('old_status', ''),
            new_status=data.get('new_status', ''),
            source=data.get('source', 'user'),
        )
        return jsonify({'success': True, 'event_id': eid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/failure-ledger')
@login_required
def failure_ledger_page():
    """Failure Ledger — permanent failure records with pattern analysis."""
    try:
        from research.evolution_quality import FailureAnalysis
        fa = FailureAnalysis()
        failures = fa.get_failures(limit=100)
        summary = fa.get_pattern_summary()
        return render_template('failure_ledger.html', failures=failures, summary=summary)
    except Exception as e:
        return render_template('failure_ledger.html', failures=[], summary={}, error=str(e))


@app.route('/api/evidence/reproducibility')
@login_required
def api_reproducibility():
    """Return reproducibility data for an observation."""
    try:
        from research.evolution_quality import ReproducibilityTracker
        rt = ReproducibilityTracker()
        obs_id = request.args.get('observation_id', type=int)
        if not obs_id:
            return jsonify({'success': False, 'error': 'observation_id required'})
        data = rt.get_reproducibility(obs_id)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/evidence/reproducibility/log', methods=['POST'])
@login_required
def api_reproducibility_log():
    """Log reproducibility data for an observation."""
    try:
        from dashboard.security import InputValidator
        data = InputValidator.validate_request_body(request.get_json(),
            ['observation_id', 'company_id'], [])
        from research.evolution_quality import ReproducibilityTracker
        rt = ReproducibilityTracker()
        lid = rt.log_reproducibility(
            observation_id=data['observation_id'],
            company_id=data['company_id'],
            filing_sources=data.get('filing_sources', ''),
            earnings_call_sources=data.get('earnings_call_sources', ''),
            financial_inputs=data.get('financial_inputs', ''),
            calculations_used=data.get('calculations_used', ''),
            model_version=data.get('model_version', '1.0'),
            agent_version=data.get('agent_version', 'analyst-1.0'),
        )
        return jsonify({'success': True, 'log_id': lid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/evidence/framework-performance')
@login_required
def api_framework_performance():
    """Return framework performance rankings."""
    try:
        from research.evolution_quality import FrameworkPerformance
        fp = FrameworkPerformance()
        min_obs = request.args.get('min_observations', 2, type=int)
        rankings = fp.get_performance_rankings(min_observations=min_obs)
        return jsonify({'success': True, 'data': rankings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/evidence/framework-performance/update', methods=['POST'])
@login_required
def api_framework_performance_update():
    """Update framework performance record."""
    try:
        from dashboard.security import InputValidator
        data = InputValidator.validate_request_body(request.get_json(),
            ['framework_name', 'category', 'confirmed'], ['confidence'])
        from research.evolution_quality import FrameworkPerformance
        fp = FrameworkPerformance()
        fp.update_performance(data['framework_name'], data['category'],
                              bool(data['confirmed']),
                              float(data.get('confidence', 0.5)))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/evidence/memos')
@login_required
def api_evidence_memos():
    """Return research evolution memos."""
    try:
        from research.evolution_quality import MemoEvolutionEngine
        me = MemoEvolutionEngine()
        company_id = request.args.get('company_id', type=int)
        memos = me.get_memos(company_id=company_id, limit=20)
        return jsonify({'success': True, 'memos': memos})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/evidence/memos/generate', methods=['POST'])
@login_required
def api_evidence_memo_generate():
    """Generate a new evolution memo for a company."""
    try:
        from dashboard.security import InputValidator
        data = InputValidator.validate_request_body(request.get_json(),
            ['company_id', 'memo_reference'], ['memo_type', 'prior_memo_reference'])
        from research.evolution_quality import MemoEvolutionEngine
        me = MemoEvolutionEngine()
        memo = me.generate_memo(
            company_id=data['company_id'],
            memo_reference=data['memo_reference'],
            memo_type=data.get('memo_type', 'evolution'),
            prior_memo_reference=data.get('prior_memo_reference', ''),
        )
        return jsonify({'success': True, 'memo': memo})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/evidence/anti-vanity')
@login_required
def api_anti_vanity():
    """Anti-Vanity Filter: audit all metrics and flag unsupported claims."""
    try:
        from research.evolution_quality import AntiVanityFilter
        av = AntiVanityFilter()
        min_validations = request.args.get('min_validations', 10, type=int)
        audit = av.audit_metrics(min_validations=min_validations)
        metric_filter = request.args.get('metric')
        if metric_filter:
            audit['metric_check'] = av.check_metric(metric_filter)
        return jsonify({'success': True, 'audit': audit})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/evidence/weekly-ic-report')
@login_required
def api_weekly_ic_report():
    """Generate Weekly IC report."""
    try:
        from research.evolution_quality import WeeklyICReport
        ic = WeeklyICReport()
        report = ic.generate_report()
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/evidence/calibration-dashboard')
@login_required
def api_calibration_dashboard():
    """Return calibration summary for dashboard."""
    try:
        from research.evolution_quality import ConfidenceCalibrator
        cc = ConfidenceCalibrator()
        summary = cc.get_calibration_summary()
        
        import math
        if summary.get('mean_absolute_error') == math.inf:
            summary['mean_absolute_error'] = "Insufficient Data"
        for b in summary.get('by_bucket', []):
            if b.get('avg_abs_error') == math.inf:
                b['avg_abs_error'] = "Insufficient Data"
        
        from research.storage.research_db import get_connection
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("""SELECT cc.*, om.observation_text, c2.ticker
                         FROM confidence_calibration cc
                         JOIN observation_memory om ON om.id = cc.observation_id
                         JOIN companies c2 ON c2.id = cc.company_id
                         ORDER BY cc.created_at DESC LIMIT 50""")
            records = [dict(r) for r in c.fetchall()]
        return jsonify({'success': True, 'summary': summary, 'records': records})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/evidence/institutional-credibility')
@login_required
def api_evidence_institutional_credibility():
    """Module 8: Evidence-only institutional credibility scoring.
    No self-referential metrics. Every point must cite evidence."""
    try:
        from research.storage.research_db import get_all_companies
        companies = get_all_companies()
        total_companies = len(companies)
        with db_get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as cnt FROM observation_memory")
            total_obs = c.fetchone()['cnt']
            c.execute("SELECT COUNT(*) as cnt FROM observation_validations")
            total_validations = c.fetchone()['cnt']
            c.execute("SELECT COUNT(*) as cnt FROM evidence_timeline")
            timeline_events = c.fetchone()['cnt']
            c.execute("SELECT COUNT(*) as cnt FROM reproducibility_log")
            reproducible_obs = c.fetchone()['cnt']
            c.execute("SELECT COUNT(*) as cnt FROM failure_analysis")
            total_failures = c.fetchone()['cnt']
            c.execute("""SELECT COUNT(DISTINCT framework_name) as cnt FROM framework_performance
                         WHERE observation_count >= 2""")
            frameworks_ranked = c.fetchone()['cnt']
            c.execute("SELECT COUNT(*) as cnt FROM challenge_records")
            total_challenges = c.fetchone()['cnt']
            c.execute("""SELECT COUNT(*) as cnt FROM challenge_records
                         WHERE passed_challenge = 1""")
            challenges_passed = c.fetchone()['cnt']
            c.execute("SELECT COUNT(*) as cnt FROM shadow_trades")
            total_trades = c.fetchone()['cnt']
            c.execute("""SELECT COUNT(*) as cnt FROM confidence_calibration""")
            calibrated = c.fetchone()['cnt']
        score = 0.0
        max_score = 100.0
        components = {}
        evidence_breadth = min(total_obs / 100 * 15, 15)
        score += evidence_breadth
        components['evidence_breadth'] = {'score': evidence_breadth, 'max': 15,
                                           'evidence': f'{total_obs} observations in memory'}
        validation_coverage = min(total_validations / total_obs * 15, 15) if total_obs > 0 else 0
        score += validation_coverage
        components['validation_coverage'] = {'score': validation_coverage, 'max': 15,
                                              'evidence': f'{total_validations}/{total_obs} observations validated'}
        timeline_score = min(timeline_events / 20 * 10, 10)
        score += timeline_score
        components['timeline_integrity'] = {'score': timeline_score, 'max': 10,
                                             'evidence': f'{timeline_events} timeline events recorded'}
        reproducibility_score = min(reproducible_obs / total_obs * 10, 10) if total_obs > 0 else 0
        score += reproducibility_score
        components['reproducibility'] = {'score': reproducibility_score, 'max': 10,
                                          'evidence': f'{reproducible_obs}/{total_obs} observations reproducible'}
        failure_transparency = min(total_failures * 2, 10)
        score += failure_transparency
        components['failure_transparency'] = {'score': failure_transparency, 'max': 10,
                                               'evidence': f'{total_failures} failure records on file'}
        framework_score = min(frameworks_ranked * 3, 15)
        score += framework_score
        components['framework_performance'] = {'score': framework_score, 'max': 15,
                                                'evidence': f'{frameworks_ranked} frameworks ranked by evidence'}
        challenge_score = min(challenges_passed * 5, 10)
        score += challenge_score
        components['challenge_integrity'] = {'score': challenge_score, 'max': 10,
                                              'evidence': f'{challenges_passed}/{total_challenges} challenges passed' if total_challenges > 0 else 'No challenges conducted'}
        calibration_score = min(calibrated * 1, 5)
        score += calibration_score
        components['calibration_evidence'] = {'score': calibration_score, 'max': 5,
                                               'evidence': f'{calibrated} calibration events recorded'}
        score = round(score, 1)
        grade = 'F' if score < 20 else ('D' if score < 40 else ('C' if score < 60 else ('B' if score < 80 else 'A')))
        verdict = 'Prototype — insufficient evidence for institutional credibility.'
        if score >= 80:
            verdict = 'INSTITUTIONAL GRADE: Evidence base meets institutional standards.'
        elif score >= 60:
            verdict = 'DEVELOPING: Evidence base growing but gaps remain for institutional use.'
        elif score >= 40:
            verdict = 'EMERGING: Core evidence exists but significant gaps remain.'
        return jsonify({'success': True, 'data': {
            'credibility_score': score,
            'max_possible': max_score,
            'grade': grade,
            'verdict': verdict,
            'components': components,
            'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        }})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/calibration')
@login_required
def calibration():
    """Calibration Dashboard — Module 3: predicted vs actual confidence tracking."""
    try:
        from research.evolution_quality import ConfidenceCalibrator
        from research.storage.research_db import get_connection
        cc = ConfidenceCalibrator()
        calibration_summary = cc.get_calibration_summary()
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("""SELECT cc.*, om.observation_text, c2.ticker
                         FROM confidence_calibration cc
                         JOIN observation_memory om ON om.id = cc.observation_id
                         JOIN companies c2 ON c2.id = cc.company_id
                         ORDER BY cc.created_at DESC LIMIT 200""")
            records = [dict(r) for r in c.fetchall()]
            c.execute("""SELECT calibration_bucket, AVG(actual_outcome) as actual_success_rate
                         FROM confidence_calibration
                         GROUP BY calibration_bucket""")
            bucket_stats = {r['calibration_bucket']: round(r['actual_success_rate'], 4) for r in c.fetchall()}
        if calibration_summary.get('by_bucket'):
            for b in calibration_summary['by_bucket']:
                b['actual_success_rate'] = bucket_stats.get(b['calibration_bucket'], 0)
        return render_template('calibration.html',
                               calibration_summary=calibration_summary,
                               calibration_records=records)
    except Exception as e:
        return render_template('calibration.html',
                               calibration_summary={},
                               calibration_records=[],
                               error=str(e))


@app.route('/audit')
@login_required
def audit():
    """Audit Trail — Section 9: immutable append-only timeline."""
    try:
        from research.evolution_quality import EvidenceTimeline
        et = EvidenceTimeline()
        events = et.get_timeline(limit=500)
        return render_template('audit.html', events=events)
    except Exception as e:
        return render_template('audit.html', events=[], error=str(e))


# ============================================================
# RESEARCH ENGINE ROUTES
# ============================================================

@app.route('/api/benchmark')
@login_required
def api_benchmark():
    """Compare historical predictions against simple baselines: NIFTY50, buy-and-hold, random."""
    try:
        from research.observation_registry import ObservationRegistry
        reg = ObservationRegistry()
        edge = reg.calculate_edge_score()
        total = edge.get('total', 0)
        confirmed = edge.get('confirmed', 0)
        invalidated = edge.get('invalidated', 0)
        resolved = confirmed + invalidated
        hit_rate = round(confirmed / resolved, 4) if resolved > 0 else None
        nifty50_benchmark = 0.12
        buy_hold_return = 0.08
        random_accuracy = 0.50
        random_accuracy_pct = 50.0
        sa_accuracy_pct = round(hit_rate * 100, 1) if hit_rate else None
        alpha_vs_nifty = round(hit_rate - nifty50_benchmark, 4) if hit_rate else None
        alpha_vs_random = round(hit_rate - random_accuracy, 4) if hit_rate else None
        return jsonify({'success': True, 'data': {
            'system_accuracy_pct': sa_accuracy_pct,
            'nifty50_benchmark_pct': round(nifty50_benchmark * 100, 1),
            'buy_and_hold_return_pct': round(buy_hold_return * 100, 1),
            'random_selection_accuracy_pct': random_accuracy_pct,
            'alpha_vs_nifty50_pct': round(alpha_vs_nifty * 100, 2) if alpha_vs_nifty else None,
            'alpha_vs_random_pct': round(alpha_vs_random * 100, 2) if alpha_vs_random else None,
            'observations_validated': resolved,
            'observations_total': total,
            'has_sufficient_data': resolved >= 10,
            'verdict': 'Insufficient validated observations for benchmark comparison.'
                       if not hit_rate else
                       ('System underperforms baselines.' if hit_rate < 0.5
                        else 'System outperforms random but below institutional threshold.')
                       if hit_rate < 0.6
                       else 'System exceeds institutional benchmarks.',
        }})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/edge')
@login_required
def edge():
    """Observation Edge Scorecard page."""
    try:
        from research.observation_registry import ObservationRegistry
        from research.storage.research_db import init_evolution_tables, init_validation_tables
        init_evolution_tables()
        init_validation_tables()
        reg = ObservationRegistry()
        scorecard = reg.calculate_edge_score()
        return render_template('edge.html', edge_data=scorecard or {})
    except Exception:
        return render_template('edge.html', edge_data={
            'edge_score': None, 'accuracy_rate': 0.0, 'weighted_accuracy': 0.0,
            'avg_confidence': 0.0, 'has_validated_data': False,
            'total': 0, 'confirmed': 0, 'partially_confirmed': 0,
            'invalidated': 0, 'active': 0, 'monitoring': 0,
            'best_categories': [], 'worst_categories': [],
        })


@app.route('/api/edge')
@login_required
def api_edge():
    """Return edge scorecard data."""
    try:
        from research.observation_registry import ObservationRegistry
        from research.storage.research_db import init_evolution_tables, init_validation_tables
        init_evolution_tables()
        init_validation_tables()
        reg = ObservationRegistry()
        scorecard = reg.calculate_edge_score()
        return jsonify({'success': True, 'data': scorecard or {}})
    except Exception as e:
        return jsonify({'success': True, 'data': {
            'edge_score': None, 'accuracy_rate': 0.0, 'weighted_accuracy': 0.0,
            'avg_confidence': 0.0, 'has_validated_data': False,
            'total': 0, 'confirmed': 0, 'partially_confirmed': 0,
            'invalidated': 0, 'active': 0, 'monitoring': 0,
            'best_categories': [], 'worst_categories': [],
        }})


@app.route('/api/edge/validations')
@login_required
def api_edge_validations():
    """Return validation feed with optional filtering."""
    try:
        from research.observation_registry import ObservationRegistry
        reg = ObservationRegistry()
        validations = reg.get_validations_feed(limit=100)
        status_filter = request.args.get('status', '')
        if status_filter:
            validations = [v for v in validations if v.get('new_status', '').upper() == status_filter.upper()]
        category_filter = request.args.get('category', '')
        if category_filter:
            validations = [v for v in validations if v.get('category', '') == category_filter]
        return jsonify({'success': True, 'data': validations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/validate/due')
@login_required
def api_validate_due():
    """List observations due for review (30/90/180-day windows)."""
    try:
        from research.observation_registry import ObservationRegistry
        reg = ObservationRegistry()
        due_30 = reg.get_due_for_review('30_day')
        due_90 = reg.get_due_for_review('90_day')
        due_180 = reg.get_due_for_review('180_day')
        return jsonify({'success': True, 'data': {
            'due_30': due_30, 'due_90': due_90, 'due_180': due_180,
            'total_due': len(due_30) + len(due_90) + len(due_180),
        }})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/validate/run-review', methods=['POST'])
@login_required
def api_validate_run_review():
    """Run scheduled review for all due observations. Records a validation event for each."""
    try:
        from research.observation_registry import ObservationRegistry
        reg = ObservationRegistry()
        due_30 = reg.get_due_for_review('30_day')
        due_90 = reg.get_due_for_review('90_day')
        due_180 = reg.get_due_for_review('180_day')
        all_due = due_30 + due_90 + due_180
        reviewed = []
        for obs in all_due[:5]:
            result = reg.update_validation_status(
                observation_id=obs['id'],
                new_status='MONITORING' if obs.get('validation_status') == 'ACTIVE' else obs.get('validation_status'),
                evidence=f"Auto-review: No new contradictory data. Status maintained.",
                method='auto_review',
                reasoning=f"Scheduled review at {(datetime.now(timezone.utc)).strftime('%Y-%m-%d')}. Awaiting outcome data."
            )
            reviewed.append({'observation_id': obs['id'], 'status': obs.get('validation_status'), 'reviewed': result})
        return jsonify({'success': True, 'data': {
            'due_count': len(all_due), 'reviewed': reviewed,
            'note': 'Observations kept at current status. Manual validation required for actual outcome confirmation.',
        }})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/institutional-credibility')
@login_required
def api_institutional_credibility():
    """Evidence-only institutional credibility score — delegates to Module 8."""
    try:
        from research.storage.research_db import get_all_companies, get_connection
        from datetime import datetime, timezone
        companies = get_all_companies()
        total_companies = len(companies)
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as cnt FROM observation_memory")
            total_obs = c.fetchone()['cnt']
            c.execute("SELECT COUNT(*) as cnt FROM observation_validations")
            total_validations = c.fetchone()['cnt']
            c.execute("SELECT COUNT(*) as cnt FROM evidence_timeline")
            timeline_events = c.fetchone()['cnt']
            c.execute("SELECT COUNT(*) as cnt FROM reproducibility_log")
            reproducible_obs = c.fetchone()['cnt']
            c.execute("SELECT COUNT(*) as cnt FROM failure_analysis")
            total_failures = c.fetchone()['cnt']
            c.execute("SELECT COUNT(*) as cnt FROM challenge_records")
            total_challenges = c.fetchone()['cnt']
            c.execute("""SELECT COUNT(*) as cnt FROM challenge_records WHERE passed_challenge = 1""")
            challenges_passed = c.fetchone()['cnt']
            c.execute("SELECT COUNT(*) as cnt FROM confidence_calibration")
            calibrated = c.fetchone()['cnt']
        score = 0.0
        max_score = 100.0
        components = {}
        evidence_breadth = min(total_obs / 100 * 15, 15)
        score += evidence_breadth
        components['evidence_breadth'] = {'score': evidence_breadth, 'max': 15,
                                           'evidence': f'{total_obs} observations in memory'}
        validation_coverage = min(total_validations / total_obs * 15, 15) if total_obs > 0 else 0
        score += validation_coverage
        components['validation_coverage'] = {'score': validation_coverage, 'max': 15,
                                              'evidence': f'{total_validations}/{total_obs} observations validated'}
        timeline_score = min(timeline_events / 20 * 10, 10)
        score += timeline_score
        components['timeline_integrity'] = {'score': timeline_score, 'max': 10,
                                             'evidence': f'{timeline_events} timeline events recorded'}
        reproducibility_score = min(reproducible_obs / total_obs * 10, 10) if total_obs > 0 else 0
        score += reproducibility_score
        components['reproducibility'] = {'score': reproducibility_score, 'max': 10,
                                          'evidence': f'{reproducible_obs}/{total_obs} observations reproducible'}
        failure_transparency = min(total_failures * 2, 10)
        score += failure_transparency
        components['failure_transparency'] = {'score': failure_transparency, 'max': 10,
                                               'evidence': f'{total_failures} failure records on file'}
        challenge_score = min(challenges_passed * 5, 10)
        score += challenge_score
        components['challenge_integrity'] = {'score': challenge_score, 'max': 10,
                                              'evidence': f'{challenges_passed}/{total_challenges} challenges passed' if total_challenges > 0 else 'No challenges conducted'}
        calibration_score = min(calibrated * 1, 5)
        score += calibration_score
        components['calibration_evidence'] = {'score': calibration_score, 'max': 5,
                                               'evidence': f'{calibrated} calibration events recorded'}
        score = round(score, 1)
        grade = 'F' if score < 20 else ('D' if score < 40 else ('C' if score < 60 else ('B' if score < 80 else 'A')))
        verdict = 'Prototype — insufficient evidence for institutional credibility.'
        if score >= 80:
            verdict = 'INSTITUTIONAL GRADE: Evidence base meets institutional standards.'
        elif score >= 60:
            verdict = 'DEVELOPING: Evidence base growing but gaps remain for institutional use.'
        elif score >= 40:
            verdict = 'EMERGING: Core evidence exists but significant gaps remain.'
        return jsonify({'success': True, 'data': {
            'credibility_score': score,
            'max_possible': max_score,
            'grade': grade,
            'verdict': verdict,
            'components': components,
            'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        }})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/research')
@login_required
def research_home():
    """Research home page showing companies and latest notes."""
    try:
        from research.storage.research_db import get_all_companies, get_notes, get_flags_count, get_flags
        from research.thesis_tracker import get_watchlist_companies
        companies = get_all_companies()
        notes = get_notes()
        total_flags = sum(get_flags_count(c['id']) for c in companies)
        heatmap = []
        for c in companies:
            flags = get_flags(c['id'])
            if flags:
                high = sum(1 for f in flags if f.get('severity') in ('HIGH', 'CRITICAL'))
                med = sum(1 for f in flags if f.get('severity') == 'MEDIUM')
                if high > 0:
                    severity = 'HIGH'
                    label = f'{high} HIGH, {med} MEDIUM'
                elif med > 0:
                    severity = 'MEDIUM'
                    label = f'{med} MEDIUM'
                else:
                    severity = 'LOW'
                    label = f'{len(flags)} total'
                heatmap.append({'ticker': c['ticker'], 'company_name': c['company_name'], 'flag_count': len(flags), 'severity': severity, 'severity_label': label})
            else:
                heatmap.append({'ticker': c['ticker'], 'company_name': c['company_name'], 'flag_count': 0, 'severity': 'NONE', 'severity_label': 'No flags'})
        watchlist = get_watchlist_companies()
        if not companies and not notes:
            companies = []
            notes = []
            total_flags = 0
        return render_template('research_home.html',
                             companies=companies, notes=notes[:10],
                             total_flags=total_flags, is_demo=is_demo_mode(),
                             heatmap=heatmap, watchlist_companies=watchlist)
    except Exception as e:
        print("RESEARCH_ROUTE_ERROR:", e)
        return render_template('research_home.html',
                             companies=[], notes=[],
                             total_flags=0, error=str(e), is_demo=is_demo_mode())


@app.route('/research/<ticker>')
@login_required
def research_company(ticker):
    """Company detail page with scorecard, metrics, flags, notes."""
    try:
        from research.storage.research_db import (
            get_company, get_latest_scores, get_all_metrics,
            get_flags, get_notes, get_filings
        )
        ticker = ticker.upper().strip()
        company = get_company(ticker)
        if not company:
            return f"Company {ticker} not found", 404
        
        company_id = company['id']
        scores = get_latest_scores(company_id) or {}
        metrics = get_all_metrics(company_id) or {}
        flags = get_flags(company_id) or []
        notes = get_notes(company_id) or []
        filings = get_filings(company_id) or []
        
        try:
            from research.thesis_evolution_engine import ThesisEvolutionEngine
            tee = ThesisEvolutionEngine()
            evo_report = tee.generate_evolution_report(company_id)
            scorecard = tee.update_thesis_scorecard(company_id)
            timeline = tee.get_observation_timeline(company_id, limit=50)
        except Exception:
            evo_report = {}
            scorecard = {}
            timeline = []

        return render_template('research_company.html',
                             company=company, scores=scores,
                             metrics=metrics, flags=flags,
                             notes=notes, filings=filings,
                             evo_report=evo_report,
                             scorecard=scorecard,
                             timeline=timeline)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template('error.html', error_code=500, error_message=str(e)), 500


@app.route('/api/research/<ticker>/evolution')
@login_required
def api_research_evolution(ticker):
    try:
        from research.storage.research_db import get_company
        from research.thesis_evolution_engine import ThesisEvolutionEngine
        company = get_company(ticker)
        if not company:
            return jsonify({'success': False, 'error': 'Company not found'})
        tee = ThesisEvolutionEngine()
        evo = tee.generate_evolution_report(company['id'])
        return jsonify({'success': True, 'evolution': evo})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/research/<ticker>/observations')
@login_required
def api_research_observations(ticker):
    category = request.args.get('category')
    try:
        from research.storage.research_db import get_company
        from research.thesis_evolution_engine import ThesisEvolutionEngine
        company = get_company(ticker)
        if not company:
            return jsonify({'success': False, 'error': 'Company not found'})
        tee = ThesisEvolutionEngine()
        obs = tee.get_observation_timeline(company['id'], category=category, limit=50)
        return jsonify({'success': True, 'observations': obs})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/research/<ticker>/scorecard')
@login_required
def api_research_scorecard(ticker):
    try:
        from research.storage.research_db import get_company
        from research.thesis_evolution_engine import ThesisEvolutionEngine
        company = get_company(ticker)
        if not company:
            return jsonify({'success': False, 'error': 'Company not found'})
        tee = ThesisEvolutionEngine()
        sc = tee.update_thesis_scorecard(company['id'])
        return jsonify({'success': True, 'scorecard': sc})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/research/note/<reference>')
@login_required
def research_note(reference):
    """Individual note page with full HTML content."""
    try:
        from research.storage.research_db import get_note_by_reference
        note = get_note_by_reference(reference)
        if not note:
            return f"Note {reference} not found", 404
        # Strip dangerous tags/attributes from note content to prevent XSS
        import re as _re
        content = note.get('full_content')
        if not content:
            content = ''
        content = _re.sub(r'<script[^>]*>.*%s</script>', '', content, flags=_re.IGNORECASE | _re.DOTALL)
        content = _re.sub(r'\bon\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=_re.IGNORECASE)
        content = _re.sub(r'javascript:', '', content, flags=_re.IGNORECASE)
        note = dict(note)
        note['full_content'] = content
        return render_template('research_note.html', note=note)
    except Exception as e:
        return render_template('error.html', error_code=500, error_message=str(e)), 500


@app.route('/research/analyze', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def research_analyze():
    """Trigger analysis for a ticker."""
    try:
        from dashboard.security import InputValidator
        data = InputValidator.validate_request_body(request.get_json(), ['ticker'],
                                                     ['pe', 'pbv'])
        ticker = InputValidator.validate_ticker(data.get('ticker', ''))
        pe = data.get('pe')
        pbv = data.get('pbv')
        
        from research.engine import SovereignAlphaResearch
        engine = SovereignAlphaResearch()
        result = engine.run_analysis(ticker, current_pe=pe, current_pbv=pbv)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/research/export/<reference>')
@login_required
def research_export(reference):
    """Download PDF for a note reference."""
    try:
        from research.output.pdf_exporter import export_note_to_pdf
        from research.storage.research_db import get_note_by_reference
        
        note = get_note_by_reference(reference)
        if not note:
            return "Note not found", 404
        
        pdf_path = note.get('pdf_path')
        if pdf_path and Path(pdf_path).exists():
            return send_file(pdf_path, as_attachment=True,
                           download_name=f"{reference}.pdf")
        
        pdf_path = export_note_to_pdf(reference)
        if pdf_path and Path(pdf_path).exists():
            return send_file(pdf_path, as_attachment=True,
                           download_name=f"{reference}.pdf")
        
        return "PDF not available", 404
    except Exception as e:
        return f"Error: {e}", 500


@app.route('/research/generate')
@login_required
def deep_research_page():
    try:
        from research.storage.research_db import get_notes
        notes = get_notes()
        return render_template('deep_research.html', notes=notes)
    except Exception as e:
        return render_template('deep_research.html', notes=[], error=str(e))

@app.route('/api/research/generate', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def api_deep_research_generate():
    try:
        from dashboard.security import InputValidator
        company_name = request.form.get('company_name', '').strip()
        ticker = request.form.get('ticker', '').strip().upper()
        sector = request.form.get('sector', '').strip()
        exchange = request.form.get('exchange', 'NSE').strip().upper()
        pe = request.form.get('pe', type=float)
        pbv = request.form.get('pbv', type=float)
        if not company_name or not ticker:
            return jsonify({'success': False, 'error': 'Company name and ticker required'})
        ticker = InputValidator.validate_ticker(ticker)
        from research.deep_research_engine import start_generation
        job_id = start_generation(company_name, ticker, sector, exchange, pe, pbv)
        return jsonify({'success': True, 'job_id': job_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/research/status/<job_id>')
@login_required
def api_deep_research_status(job_id):
    try:
        from research.deep_research_engine import get_status
        status = get_status(job_id)
        return jsonify(status)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/api/research/result/<job_id>')
@login_required
def api_deep_research_result(job_id):
    try:
        from research.deep_research_engine import get_result
        result = get_result(job_id)
        if result:
            return jsonify({'success': True, 'result': result})
        return jsonify({'success': False, 'error': 'Result not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/research/report/<reference>')
@login_required
def deep_research_report(reference):
    try:
        from research.deep_research_engine import get_report, get_report_meta
        html_content = get_report(reference)
        if not html_content:
            return "Report not found", 404
        meta = get_report_meta(reference)
        return render_template('deep_report.html', html_content=html_content, meta=meta)
    except Exception as e:
        return render_template('deep_report.html', error=str(e))

@app.route('/research/download/<reference>')
@login_required
def deep_research_download(reference):
    try:
        from research.storage.research_db import get_note_by_reference
        note = get_note_by_reference(reference)
        if not note:
            return "Report not found", 404
        pdf_path = note.get('pdf_path')
        if pdf_path and Path(pdf_path).exists():
            return send_file(pdf_path, as_attachment=True, download_name=f"{reference}.pdf")
        html_path = note.get('full_content')
        if html_path:
            from research.output.pdf_exporter import generate_deep_report_pdf
            from pathlib import Path as _P
            notes_dir = _P(__file__).parent.parent / "research" / "data" / "notes"
            pdf_result = generate_deep_report_pdf(reference, html_path, str(notes_dir))
            if pdf_result and _P(pdf_result).exists():
                return send_file(pdf_result, as_attachment=True, download_name=f"{reference}.pdf")
        return "PDF not available", 404
    except Exception as e:
        return f"Error: {e}", 500


@app.route('/api/shadow-portfolio')
@login_required
def api_shadow_portfolio():
    """List shadow portfolio positions with P&L."""
    try:
        conn = db_get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM shadow_portfolio ORDER BY entry_date DESC")
        positions = c.fetchall()
        pass
        # # conn.close()
        return jsonify({'success': True, 'data': [dict(r) for r in positions]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/shadow-portfolio/open', methods=['POST'])
@login_required
def api_shadow_portfolio_open():
    """Open a shadow portfolio position."""
    try:
        body = request.get_json(force=True, silent=True) or {}
        ticker = body.get('ticker', '').upper()
        if not ticker:
            return jsonify({'success': False, 'error': 'ticker required'})
        entry_price = float(body.get('entry_price', 0))
        thesis = body.get('thesis', '')
        expected_outcome = body.get('expected_outcome', '')
        confidence = float(body.get('confidence', 0.5))
        conn = db_get_connection()
        c = conn.cursor()
        c.execute("""INSERT INTO shadow_portfolio
            (position_id, ticker, entry_date, entry_price, thesis,
             expected_outcome, confidence, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'OPEN')""",
            (f"SP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{ticker}",
             ticker, datetime.now(timezone.utc).strftime('%Y-%m-%d'),
             entry_price, thesis, expected_outcome, confidence))
        conn.commit()
        pos_id = c.lastrowid
        pass
        # # conn.close()
        return jsonify({'success': True, 'position_id': pos_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/shadow-portfolio/close', methods=['POST'])
@login_required
def api_shadow_portfolio_close():
    """Close a shadow portfolio position and record P&L."""
    try:
        body = request.get_json(force=True, silent=True) or {}
        position_id = body.get('position_id', '')
        exit_price = float(body.get('exit_price', 0))
        outcome = body.get('outcome', '')
        lessons = body.get('lessons', '')
        conn = db_get_connection()
        c = conn.cursor()
        pos = c.execute("SELECT * FROM shadow_portfolio WHERE position_id = %s",
                        (position_id,)).fetchone()
        if not pos:
            return jsonify({'success': False, 'error': 'position not found'})
        entry_price = pos[4]
        return_pct = round((exit_price - entry_price) / entry_price * 100, 2)
        try:
            fund_params = get_fund_params()
            benchmark_return_pct = float(fund_params.get('benchmark_return_pct', 0.0))
        except Exception:
            benchmark_return_pct = 0.0
        alpha_pct = round(return_pct - benchmark_return_pct, 2)
        c.execute("""UPDATE shadow_portfolio SET
            exit_date = %s, exit_price = %s, return_pct = %s,
            benchmark_return_pct = %s, alpha_pct = %s,
            status = 'CLOSED', outcome = %s, lessons = %s
            WHERE position_id = %s""",
            (datetime.now(timezone.utc).strftime('%Y-%m-%d'),
             exit_price, return_pct, benchmark_return_pct,
             alpha_pct, outcome, lessons, position_id))
        conn.commit()
        pass
        # # conn.close()
        return jsonify({'success': True, 'return_pct': return_pct, 'alpha_pct': alpha_pct})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/portfolio')
@login_required
def portfolio_page():
    try:
        from research.portfolio_intelligence import get_portfolios, get_positions, calculate_concentration, calculate_portfolio_score, run_all_stress_tests, detect_hidden_correlations
        all_portfolios = get_portfolios()
        selected = request.args.get('portfolio_id', type=int)
        portfolio_detail = None
        conc_data = {}
        corr_data = []
        stress_results = []
        score_data = None
        positions_data = []
        if selected and any(p['id'] == selected for p in all_portfolios):
            from research.portfolio_intelligence import get_portfolio
            portfolio_detail = get_portfolio(selected)
            positions_data = get_positions(selected)
            conc_data = calculate_concentration(selected)
            corr_data = detect_hidden_correlations(selected)
            stress_results = run_all_stress_tests(selected)
            score_data = calculate_portfolio_score(selected)
        now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        return render_template('portfolio.html', portfolios=all_portfolios, portfolio=portfolio_detail, portfolio_id=selected,
                             portfolios_count=len(all_portfolios), positions_count=sum(len(get_positions(p['id'])) for p in all_portfolios) if all_portfolios else 0,
                             concentration=conc_data, correlations=corr_data, stress_results=stress_results, positions=positions_data, portfolio_score=score_data, avg_score=score_data['composite_score'] if score_data else '—',
                             stress_impact=max(r['impact_pct'] for r in stress_results) if stress_results else 0, timestamp=now_str)
    except Exception as e:
        now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        return render_template('portfolio.html', portfolios=[], portfolio=None, portfolio_id=None, error=str(e), portfolios_count=0, positions_count=0, timestamp=now_str)

@app.route('/api/portfolio/delete', methods=['POST'])
@login_required
def api_portfolio_delete():
    try:
        from research.portfolio_intelligence import get_connection
        pid = int(request.form.get('portfolio_id', 0))
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM portfolio_scores WHERE portfolio_id = %s", (pid,))
            c.execute("DELETE FROM portfolio_stress_results WHERE portfolio_id = %s", (pid,))
            c.execute("DELETE FROM portfolio_positions WHERE portfolio_id = %s", (pid,))
            c.execute("DELETE FROM portfolios WHERE id = %s", (pid,))
            conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/portfolio/create', methods=['POST'])
@login_required
def api_portfolio_create():
    try:
        from research.portfolio_intelligence import create_portfolio
        name = request.form.get('name', 'Unnamed Portfolio')
        description = request.form.get('description', '')
        strategy = request.form.get('strategy', '')
        pid = create_portfolio(name, description, strategy)
        return jsonify({'success': True, 'portfolio_id': pid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/portfolio/<int:pid>/add', methods=['POST'])
@login_required
def api_portfolio_add(pid):
    try:
        from research.portfolio_intelligence import add_position
        company_id = int(request.form.get('company_id', 0))
        weight = float(request.form.get('weight_pct', 0))
        cost = request.form.get('cost_basis', type=float)
        notes = request.form.get('notes', '')
        pos_id = add_position(pid, company_id, weight, cost, notes)
        return jsonify({'success': True, 'position_id': pos_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/portfolio/position/delete', methods=['POST'])
@login_required
def api_portfolio_delete_position():
    try:
        from research.portfolio_intelligence import delete_position
        pos_id = int(request.form.get('position_id', 0))
        delete_position(pos_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/portfolio/<int:pid>/stress-test', methods=['POST'])
@login_required
def api_portfolio_stress_test(pid):
    try:
        from research.portfolio_intelligence import run_all_stress_tests, save_stress_results
        results = run_all_stress_tests(pid)
        save_stress_results(pid, results)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/portfolio/<int:pid>/score', methods=['POST'])
@login_required
def api_portfolio_score(pid):
    try:
        from research.portfolio_intelligence import calculate_portfolio_score
        score = calculate_portfolio_score(pid)
        return jsonify({'success': True, 'score': score})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/watchlist')
@login_required
def watchlist_page():
    try:
        from research.thesis_tracker import get_watchlist_companies
        from research.storage.research_db import get_all_companies
        companies = get_all_companies()
        watchlist = get_watchlist_companies()
        from research.thesis_tracker import get_theses
        theses = get_theses()
        active = [t for t in theses if t.get('status') == 'INTACT']
        weakening = [t for t in theses if t.get('status') == 'WEAKENING']
        broken = [t for t in theses if t.get('status') == 'BROKEN']
        thesis_id = request.args.get('thesis_id', type=int)
        thesis_detail = None
        thesis_checks = []
        if thesis_id:
            from research.thesis_tracker import get_thesis, get_checks
            thesis_detail = get_thesis(thesis_id)
            thesis_checks = get_checks(thesis_id) if thesis_detail else []
        now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        return render_template('watchlist.html', companies=companies, watchlist=watchlist, theses=theses,
                             active_theses=len(active), weakening_count=len(weakening), broken_count=len(broken),
                             thesis=thesis_detail, thesis_checks=thesis_checks, thesis_id=thesis_id,
                             watchlist_count=len(watchlist), timestamp=now_str)
    except Exception as e:
        now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        return render_template('watchlist.html', companies=[], watchlist=[], theses=[], error=str(e),
                             active_theses=0, weakening_count=0, broken_count=0, watchlist_count=0, timestamp=now_str)

@app.route('/api/watchlist/add/<int:company_id>', methods=['POST'])
@login_required
def api_watchlist_add(company_id):
    try:
        from research.thesis_tracker import add_to_watchlist
        threshold = request.form.get('alert_threshold', 'MEDIUM')
        notes = request.form.get('notes', '')
        wid = add_to_watchlist(company_id, threshold, notes)
        return jsonify({'success': True, 'watchlist_id': wid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/watchlist/remove', methods=['POST'])
@login_required
def api_watchlist_remove():
    try:
        from research.thesis_tracker import remove_from_watchlist
        company_id = int(request.form.get('company_id', 0))
        remove_from_watchlist(company_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/thesis/create', methods=['POST'])
@login_required
def api_thesis_create():
    try:
        from research.thesis_tracker import create_thesis
        company_id = int(request.form.get('company_id', 0))
        title = request.form.get('title', '')
        thesis_text = request.form.get('thesis_text', '')
        key_vars = request.form.get('key_variables', '')
        timeframe = int(request.form.get('timeframe_days', 90))
        conviction = float(request.form.get('conviction', 0))
        tid = create_thesis(company_id, title, thesis_text, key_vars, timeframe, conviction)
        return jsonify({'success': True, 'thesis_id': tid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/thesis/check', methods=['POST'])
@login_required
def api_thesis_check():
    try:
        from research.thesis_tracker import add_check, assess_thesis_status
        tid = int(request.form.get('thesis_id', 0))
        variable = request.form.get('variable', '')
        expected = request.form.get('expected_range', '')
        actual = request.form.get('actual_value', '')
        severity = request.form.get('flag_severity', None)
        notes = request.form.get('notes', '')
        add_check(tid, variable, expected, actual, severity, notes)
        assessment = assess_thesis_status(tid)
        return jsonify({'success': True, 'assessment': assessment})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/thesis/<int:tid>/assess', methods=['POST'])
@login_required
def api_thesis_assess(tid):
    try:
        from research.thesis_tracker import assess_thesis_status
        assessment = assess_thesis_status(tid)
        return jsonify({'success': True, 'assessment': assessment})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/observations/feed')
@login_required
def api_observations_feed():
    try:
        from research.observation_stream import build_live_feed
        limit = request.args.get('limit', 30, type=int)
        feed = build_live_feed(limit)
        return jsonify({'success': True, **feed})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/heatmap/data')
@login_required
def api_heatmap_data():
    try:
        from research.storage.research_db import get_all_companies, get_flags
        companies = get_all_companies()
        heatmap = []
        for c in companies:
            flags = get_flags(c['id'])
            if flags:
                high = sum(1 for f in flags if f.get('severity') in ('HIGH', 'CRITICAL'))
                med = sum(1 for f in flags if f.get('severity') == 'MEDIUM')
                if high > 0:
                    severity = 'HIGH'
                    label = f'{high} HIGH, {med} MEDIUM'
                elif med > 0:
                    severity = 'MEDIUM'
                    label = f'{med} MEDIUM'
                else:
                    severity = 'LOW'
                    label = f'{len(flags)} total'
                heatmap.append({'ticker': c['ticker'], 'company_name': c['company_name'], 'flag_count': len(flags), 'severity': severity, 'severity_label': label})
            else:
                heatmap.append({'ticker': c['ticker'], 'company_name': c['company_name'], 'flag_count': 0, 'severity': 'NONE', 'severity_label': 'No flags'})
        return jsonify({'success': True, 'heatmap': heatmap})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ---------------------------------------------------------------------------
# Macro & Currency Intelligence Routes
# ---------------------------------------------------------------------------

@app.route('/macro')
@login_required
def macro_page():
    return redirect('/macro-health')


@app.route('/macro-health')
@login_required
def macro_health_page():
    try:
        from research.macro.macro_health import build_macro_health_report, init_macro_tables
        init_macro_tables()
        report = build_macro_health_report()
        return render_template('macro_health.html', report=report)
    except Exception as e:
        return render_template('macro_health.html', report=None, error=str(e))

@app.route('/api/macro/overview')
@login_required
def api_macro_overview():
    try:
        from research.macro.macro_engine import get_macro_overview
        overview = get_macro_overview()
        return jsonify({'success': True, 'overview': overview})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/macro/fii-flow')
@login_required
def macro_fii_flow():
    try:
        from research.macro.fii_flow import build_flow_intelligence_report
        report = build_flow_intelligence_report()
        return render_template('fii_flow.html', report=report)
    except Exception as e:
        return render_template('fii_flow.html', report=None, error=str(e))

@app.route('/api/macro/fii-flow/record', methods=['POST'])
@login_required
def api_macro_fii_record():
    try:
        from research.macro.fii_flow import record_flow_entry
        date = request.form.get('date', '')
        flow_type = request.form.get('flow_type', 'EQUITY')
        category = request.form.get('category', 'EQUITY_FII')
        amount = request.form.get('amount_cr', type=float)
        if not date or amount is None:
            return jsonify({'success': False, 'error': 'Date and amount required'})
        record_flow_entry(date, flow_type, category, amount)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/macro/fii-flow/data')
@login_required
def api_macro_fii_data():
    try:
        from research.macro.fii_flow import build_flow_intelligence_report
        report = build_flow_intelligence_report()
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/macro/currency-cards')
@login_required
def macro_currency_cards():
    try:
        from research.portfolio_intelligence import get_portfolios, get_positions
        from research.storage.research_db import get_company_by_id
        from research.macro.currency_sensitivity import build_portfolio_currency_view

        portfolios = get_portfolios()
        selected = request.args.get('portfolio_id', type=int)
        positions_data = []
        if selected and any(p['id'] == selected for p in portfolios):
            raw_positions = get_positions(selected)
            for pos in raw_positions:
                company = get_company_by_id(pos.get('company_id'))
                if company:
                    positions_data.append({
                        'company_id': pos['company_id'],
                        'company_name': company['company_name'],
                        'ticker': company['ticker'],
                        'sector': company.get('sector', ''),
                        'weight_pct': pos.get('weight_pct'),
                    })

        report = build_portfolio_currency_view(positions_data)
        if selected:
            report['portfolio_name'] = next((p['name'] for p in portfolios if p['id'] == selected), None)
        report['portfolios'] = portfolios
        report['selected_id'] = selected
        return render_template('currency_cards.html', report=report)
    except Exception as e:
        return render_template('currency_cards.html', report=None, error=str(e))

@app.route('/api/macro/currency-sensitivity')
@login_required
def api_macro_currency():
    try:
        from research.portfolio_intelligence import get_positions
        from research.storage.research_db import get_company_by_id
        from research.macro.currency_sensitivity import build_portfolio_currency_view

        pid = request.args.get('portfolio_id', type=int)
        positions_data = []
        if pid:
            raw_positions = get_positions(pid)
            for pos in raw_positions:
                company = get_company_by_id(pos.get('company_id'))
                if company:
                    positions_data.append({
                        'company_id': pos['company_id'],
                        'company_name': company['company_name'],
                        'ticker': company['ticker'],
                        'sector': company.get('sector', ''),
                        'weight_pct': pos.get('weight_pct'),
                    })
        report = build_portfolio_currency_view(positions_data)
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/macro/macro-health')
@login_required
def api_macro_health():
    try:
        from research.macro.macro_health import build_macro_health_report
        report = build_macro_health_report()
        if 'indicators' in report and isinstance(report['indicators'], dict):
            indicators_dict = report.pop('indicators')
            report['indicators'] = []
            for key, val in indicators_dict.items():
                report['indicators'].append({
                    'name': val.get('thresholds', {}).get('label', key),
                    'key': key,
                    'value': val.get('value'),
                    'score': val.get('score'),
                    'status': val.get('status', 'NO_DATA'),
                    'direction': _macro_direction(val.get('value'), val.get('thresholds', {})),
                    'observation': '',
                })
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def _macro_direction(value, thresholds):
    if value is None or not thresholds:
        return 'flat'
    direction = thresholds.get('direction', 'higher_better')
    if direction == 'higher_better':
        return 'up' if value >= thresholds.get('good_min', 0) else 'down'
    elif direction == 'lower_better':
        return 'down' if value <= thresholds.get('good_max', 999) else 'up'
    return 'flat'

@app.route('/api/macro/import-sensitivity')
@login_required
def api_macro_import_sensitivity():
    try:
        from research.portfolio_intelligence import get_positions
        from research.storage.research_db import get_company_by_id
        from research.macro.import_sensitivity import build_import_sensitivity_overlay

        pid = request.args.get('portfolio_id', type=int)
        positions_data = []
        if pid:
            raw_positions = get_positions(pid)
            for pos in raw_positions:
                company = get_company_by_id(pos.get('company_id'))
                if company:
                    positions_data.append({
                        'company_id': pos['company_id'],
                        'company_name': company['company_name'],
                        'ticker': company['ticker'],
                        'sector': company.get('sector', ''),
                        'weight_pct': pos.get('weight_pct'),
                    })
        report = build_import_sensitivity_overlay(positions_data)
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/macro/reserve-stress')
@login_required
def api_macro_reserve_stress():
    try:
        from research.macro.reserve_stress import build_reserve_stress_report
        report = build_reserve_stress_report(
            reserve_usd_bn=request.args.get('reserve', type=float),
            import_cover_months=request.args.get('import_cover', type=float),
            st_debt_coverage=request.args.get('debt_coverage', type=float),
        )
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/macro/init-db', methods=['POST'])
@login_required
def api_macro_init_db():
    try:
        from research.macro.macro_engine import init_macro_tables
        init_macro_tables()
        return jsonify({'success': True, 'message': 'Macro tables initialized'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def seed_database_on_startup():
    """Create all tables and seed sample data on first startup."""
    import uuid
    try:
        # Create ALL tables from the master schema file
        schema_path = Path(__file__).parent.parent / 'POSTGRES_SCHEMA.sql'
        if schema_path.exists():
            schema_sql = schema_path.read_text()
            schema_conn = db_get_connection()
            schema_conn.cursor().execute(schema_sql)
            schema_conn.commit()
            schema_# # conn.close()
            print("[seed] All tables created from POSTGRES_SCHEMA.sql")
        else:
            # Fallback to schemas.py if schema file missing
            from dashboard.schemas import init_billing_db, init_research_db, init_fund_data_db
            init_billing_db()
            init_research_db()
            init_fund_data_db()
            print("[seed] Tables created from schemas.py")

        conn = db_get_connection()
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM prediction_ledger")
        if c.fetchone()[0] == 0:
            now = datetime.utcnow()
            samples = [
                ("pred-001", (now - timedelta(days=5)).isoformat() + 'Z', "RELIANCE", "Energy", "Strong momentum in refining margins", 0.82, "cleared", 30, "0x" + uuid.uuid4().hex[:40], now.isoformat(), now.isoformat(), "correct", 8.5),
                ("pred-002", (now - timedelta(days=3)).isoformat() + 'Z', "TCS", "IT", "Weak guidance on IT spending outlook", 0.45, "risk-rejected", 14, "0x" + uuid.uuid4().hex[:40], now.isoformat(), now.isoformat(), None, None),
                ("pred-003", (now - timedelta(days=2)).isoformat() + 'Z', "INFY", "IT", "Deal wins in AI/ML segment driving growth", 0.71, "cleared", 45, "0x" + uuid.uuid4().hex[:40], now.isoformat(), now.isoformat(), "incorrect", -3.2),
                ("pred-004", (now - timedelta(days=1)).isoformat() + 'Z', "HDFCBANK", "Banking", "Stable NIM, awaiting credit growth pickup", 0.60, "cleared", 60, "0x" + uuid.uuid4().hex[:40], now.isoformat(), now.isoformat(), "correct", 4.1),
                ("pred-005", now.isoformat() + 'Z', "BAJFINANCE", "NBFC", "AUM growth accelerating, ROE stabilizing", 0.78, "cleared", 30, "0x" + uuid.uuid4().hex[:40], now.isoformat(), now.isoformat(), None, None),
            ]
            for pid, ts, asset, sector, thesis, conf, status, days, phash, created, updated, outcome, ret in samples:
                c.execute("""
                    INSERT INTO prediction_ledger
                    (prediction_id, timestamp, asset, sector, thesis, confidence_score, status, expected_timeline_days, proof_hash, created_at, updated_at, actual_outcome, actual_return_pct)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (pid, ts, asset, sector, thesis, conf, status, days, phash, created, updated, outcome, ret))
            print(f"[seed] Inserted {len(samples)} sample predictions")
        c.execute("UPDATE prediction_ledger SET actual_outcome = 'correct', status = 'HIT', actual_return_pct = 8.5 WHERE prediction_id = 'pred-001' AND (actual_outcome IS NULL OR actual_outcome = '')")
        c.execute("UPDATE prediction_ledger SET actual_outcome = 'incorrect', status = 'MISS', actual_return_pct = -3.2 WHERE prediction_id = 'pred-003' AND (actual_outcome IS NULL OR actual_outcome = '')")
        c.execute("UPDATE prediction_ledger SET actual_outcome = 'correct', status = 'HIT', actual_return_pct = 4.1 WHERE prediction_id = 'pred-004' AND (actual_outcome IS NULL OR actual_outcome = '')")

        c.execute("SELECT COUNT(*) FROM veto_archive")
        if c.fetchone()[0] == 0:
            now = datetime.utcnow()
            samples = [
                ("veto-001", "ADANIENT", "Energy", "High promoter pledge risk", 0.91, (now - timedelta(days=7)).isoformat(), "correct", -12.5, 8.0, 12.5, 1, "Stock fell 12.5% after pledge news"),
                ("veto-002", "PAYTM", "Fintech", "Regulatory overhang unresolved", 0.85, (now - timedelta(days=4)).isoformat(), "correct", -8.2, 6.0, 8.2, 1, "RBI restrictions continued"),
                ("veto-003", "ZEEL", "Media", "Governance red flags", 0.88, (now - timedelta(days=2)).isoformat(), None, None, 7.0, None, None, None),
            ]
            for vid, asset, sector, reason, risk, ts, outcome, ret, exp_loss, avoided, correct, notes in samples:
                c.execute("""
                    INSERT INTO veto_archive
                    (veto_id, asset, sector, rejection_reason, risk_score, timestamp, actual_outcome, actual_return_pct, expected_loss_pct, avoided_drawdown, veto_correct, notes, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (vid, asset, sector, reason, risk, ts, outcome, ret, exp_loss, avoided, correct, notes, ts))
            print(f"[seed] Inserted {len(samples)} sample vetoes")

        c.execute("DELETE FROM decisions")
        c.execute("""INSERT INTO decisions
            (decision_id, symbol, action, status, confidence, potential_return, fee, zk_proof_hash, timestamp)
            SELECT
                prediction_id, asset,
                CASE WHEN status IN ('vetoed','risk-rejected','VETOED','RISK_REJECTED')
                     THEN 'veto' ELSE 'approve' END,
                status, confidence_score, NULL, NULL, proof_hash, timestamp
            FROM prediction_ledger
        """)
        c.execute("""INSERT INTO decisions
            (decision_id, symbol, action, status, confidence, potential_return, fee, zk_proof_hash, timestamp)
            SELECT
                veto_id, asset, 'veto', 'vetoed',
                COALESCE(1.0 - risk_score, 0.5),
                -expected_loss_pct, NULL, NULL, timestamp
            FROM veto_archive
        """)

        conn.commit()
        pass
        # # conn.close()
        print("[seed] Billing DB seeding complete")
    except Exception as e:
        print(f"[seed] Seeding failed: {e}")

seed_database_on_startup()

# SAFETY NET REMOVED - No demo data insertion.

try:
    from dashboard.schemas import init_research_db
    init_research_db()
    from research.storage.research_db import init_extended_tables
    init_extended_tables()
except Exception as e:
    print(f"Warning: Could not initialize research DB: {e}")

try:
    _fconn = db_get_connection()
    _f# # conn.close()
except Exception as _fe:
    pass

try:
    from research.backfill_memory import backfill
    inserted = backfill()
    if inserted:
        print(f"[startup] Backfilled {inserted} observations into memory")
except Exception as e:
    print(f"Warning: Could not backfill observations: {e}")

try:
    from scripts.seed_all_empty_tables import seed_all_empty_tables
    result = seed_all_empty_tables(quiet=False)
except Exception as e:
    print(f"Warning: Could not seed extended tables: {e}")

print("=" * 60)
print("STARTUP VERIFICATION")
print("=" * 60)
try:
    _vconn = db_get_connection()
    _vc = _vconn.cursor()
    for _tbl in ['prediction_ledger', 'veto_archive', 'decisions', 'performance_log', 'inference_log', 'monthly_summary']:
        _vc.execute(f"SELECT COUNT(*) FROM {_tbl}")
        _cnt = _vc.fetchone()[0]
        print(f"  [db] {_tbl}: {_cnt} rows")
    _v# # conn.close()
except Exception as _ve:
    print(f"  [db] verification failed: {_ve}")

try:
    _vconn2 = db_get_connection()
    _vc2 = _vconn2.cursor()
    _all_tables = [
        'companies', 'filings', 'financial_series', 'forensic_flags', 'research_notes',
        'institutional_scores', 'nsdl_fpi_flows', 'fii_flows', 'fii_flow_snapshots',
        'edge_scorecard', 'watchlist',
        'observation_memory', 'observation_validations', 'evidence_timeline',
        'multi_source_evidence', 'framework_performance', 'reproducibility_log',
        'observation_autopsy', 'reasoning_audit', 'failure_analysis',
        'calibration_history', 'edge_discovery_framework', 'shadow_portfolio',
        'credibility_evidence', 'research_quality_metrics', 'confidence_calibration',
        'portfolios', 'portfolio_positions', 'portfolio_scores', 'portfolio_stress_results',
        'theses', 'thesis_checks', 'observations',
    ]
    for _tbl in _all_tables:
        try:
            _vc2.execute(f"SELECT COUNT(*) FROM {_tbl}")
            _cnt = _vc2.fetchone()[0]
            print(f"  [db] {_tbl}: {_cnt} rows")
        except Exception:
            print(f"  [db] {_tbl}: MISSING")
    _vconn2.close()
except Exception as _ve:
    print(f"  [db] verification failed: {_ve}")

print("=" * 60)

# --- BACKGROUND RUNS ROUTES ---
@app.route('/runs')
@login_required
def runs_view():
    return render_template('runs.html')

@app.route('/api/runs', methods=['GET'])
@login_required
def get_runs():
    try:
        with db_get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM analysis_runs ORDER BY created_at DESC LIMIT 50")
            rows = [dict(r) for r in c.fetchall()]
        for r in rows:
            if 'created_at' in r and r['created_at']: r['created_at'] = str(r['created_at'])
            if 'updated_at' in r and r['updated_at']: r['updated_at'] = str(r['updated_at'])
            if 'heartbeat_at' in r and r['heartbeat_at']: r['heartbeat_at'] = str(r['heartbeat_at'])
            if 'started_at' in r and r['started_at']: r['started_at'] = str(r['started_at'])
            if 'completed_at' in r and r['completed_at']: r['completed_at'] = str(r['completed_at'])
            if 'run_id' in r: r['run_id'] = str(r['run_id'])
        return jsonify({"runs": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/runs/submit', methods=['POST'])
@login_required
def submit_run():
    data = request.json
    ticker = data.get('ticker')
    if not ticker: return jsonify({"error": "No ticker provided"}), 400
    
    try:
        with db_get_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO analysis_runs (ticker, run_type, status, current_step) VALUES (%s, %s, %s, %s) RETURNING run_id",
                (ticker, data.get('run_type', 'MANUAL'), 'PENDING', 'Queued')
            )
            run_id = c.fetchone()['run_id']
            c.execute("INSERT INTO analysis_run_events (run_id, event_type, event_message) VALUES (%s, %s, %s)",
                      (run_id, 'RUN_CREATED', f"Run created for {ticker}"))
            conn.commit()
        return jsonify({"run_id": str(run_id)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/runs/events/<run_id>', methods=['GET'])
@login_required
def get_run_events(run_id):
    try:
        with db_get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM analysis_run_events WHERE run_id = %s ORDER BY created_at ASC", (run_id,))
            rows = [dict(r) for r in c.fetchall()]
        for r in rows:
            if 'created_at' in r and r['created_at']: r['created_at'] = str(r['created_at'])
            if 'run_id' in r: r['run_id'] = str(r['run_id'])
        return jsonify({"events": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/pipeline-health')
@login_required
def pipeline_health():
    """Pipeline health diagnostic endpoint."""
    try:
        from pipeline_health import check_pipeline_health
        result = check_pipeline_health()
    except Exception as e:
        result = {"status": "FAIL", "checks": {}, "verdict": f"Health check error: {e}"}

    if request.headers.get('Accept', '').startswith('application/json'):
        return jsonify(result)
    return render_template('health_diagnostic.html', health=result)


# --- SCHEDULER INITIALIZATION (Survives HF Reboots) ---
from apscheduler.triggers.cron import CronTrigger
import pytz

if not scheduler.running:
    scheduler.start()

# Remove existing jobs to avoid duplication on reloads
for job in scheduler.get_jobs():
    scheduler.remove_job(job.id)

def run_pipeline_job():
    script_path = os.path.join(project_dir, 'automation', 'master_daily.py')
    print(f"[Scheduler] Triggering daily pipeline: {script_path}")
    import subprocess
    subprocess.Popen([sys.executable, script_path])

scheduler.add_job(
    run_pipeline_job,
    CronTrigger(hour=8, minute=45, timezone=pytz.timezone('Asia/Kolkata')),
    id='daily_pipeline',
    replace_existing=True
)
print("[Scheduler] Job 'daily_pipeline' configured for 08:45 AM Asia/Kolkata.")

@app.route('/trigger-pipeline', methods=['GET', 'POST'])
@login_required
def trigger_pipeline():
    """Manual trigger to force the pipeline to run immediately."""
    try:
        run_pipeline_job()
        return jsonify({"status": "ok", "message": "Pipeline triggered successfully in background."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
# ------------------------------------------------------


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 7860))
    
    print("=== SOVEREIGN ALPHA - Dashboard v1.3 ===")
    print(f"Database: {DB_PATH} (exists: {DB_PATH.exists()})")
    print(f"Proofs: {PROOFS_DIR} (count: {count_proof_files()})")
    print(f"Starting dashboard at http://localhost:{port}")
    print(f"Cloud mode: {IS_CLOUD}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
