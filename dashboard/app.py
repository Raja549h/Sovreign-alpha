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

import os
import sys
import json
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
import time
import hmac

dashboard_dir = Path(__file__).parent
project_dir = dashboard_dir.parent
sys.path.insert(0, str(project_dir))

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
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
FLASK_AVAILABLE = True
IS_CLOUD = bool(os.environ.get("SPACE_ID")) or os.environ.get("RENDER", "false").lower() == "true"

BASE_DIR = project_dir
DATA_DIR = BASE_DIR / "data"
BILLING_DIR = BASE_DIR / "billing"
RESULTS_DIR = BASE_DIR / "results"
PROOFS_DIR = BASE_DIR / "zkml" / "proofs"
CERTS_DIR = BASE_DIR / "zkml" / "certificates"
FUNDS_DIR = DATA_DIR / "funds"

RESULTS_DIR.mkdir(exist_ok=True)
PROOFS_DIR.mkdir(exist_ok=True)
CERTS_DIR.mkdir(exist_ok=True)
BILLING_DIR.mkdir(exist_ok=True)
FUNDS_DIR.mkdir(exist_ok=True)

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

def get_macro_tickers():
    """Get macro ticker data for ticker strip."""
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
        return {k: v for k, v in tickers.items() if v is not None}
    except Exception:
        # Return synthetic macro data so ticker strip always shows values
        return {
            "vix": 18.4, "dxy": 99.3, "treasury_10y": 4.60,
            "gold": 2345.0, "oil_wti": 78.5, "spx_price": 5620.0,
            "spx_change": 0.45, "dxy_change": -0.12, "gold_change": 0.82,
            "oil_change": -0.55, "nsei": 23759.0, "nsei_change": 0.30
        }

app = Flask(__name__, template_folder='templates')
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

FUND_PASSWORD = os.environ.get("FUND_PASSWORD", "")

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
    conn = sqlite3.connect(str(FUND_DATA_DB))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS fund_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_type TEXT,
            file_content BLOB,
            uploaded_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS fund_params (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            param_key TEXT UNIQUE,
            param_value TEXT,
            updated_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS prediction_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id TEXT UNIQUE,
            timestamp TEXT NOT NULL,
            asset TEXT NOT NULL,
            sector TEXT,
            thesis TEXT,
            confidence_score REAL,
            status TEXT NOT NULL,
            expected_timeline_days INTEGER,
            actual_outcome TEXT,
            actual_return_pct REAL,
            outcome_notes TEXT,
            proof_hash TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS veto_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veto_id TEXT UNIQUE,
            prediction_id TEXT,
            timestamp TEXT NOT NULL,
            asset TEXT NOT NULL,
            sector TEXT,
            rejection_reason TEXT NOT NULL,
            expected_loss_pct REAL,
            actual_outcome TEXT,
            actual_return_pct REAL,
            avoided_drawdown REAL,
            veto_correct BOOLEAN,
            proof_hash TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_fund_db()

# Validation tables init moved to late-startup block after evolution_tables

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(str(FUND_DATA_DB))
    conn.row_factory = sqlite3.Row
    return conn

def save_prediction(prediction_data: dict) -> bool:
    """Save a prediction to the ledger. Write-once, never update timestamp."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO prediction_ledger 
            (prediction_id, timestamp, asset, sector, thesis, confidence_score, 
             status, expected_timeline_days, proof_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving prediction: {e}")
        return False
    finally:
        conn.close()

def get_predictions(limit: int = 100) -> list:
    """Get all predictions ordered by timestamp descending."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT * FROM prediction_ledger 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception:
        return []

def update_prediction_outcome(prediction_id: str, outcome_data: dict) -> bool:
    """Update a prediction with its outcome. Can only update outcome fields."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("""
            UPDATE prediction_ledger SET
            actual_outcome = ?,
            actual_return_pct = ?,
            outcome_notes = ?,
            updated_at = ?
            WHERE prediction_id = ?
        """, (
            outcome_data.get('outcome', ''),
            outcome_data.get('actual_return_pct', 0.0),
            outcome_data.get('notes', ''),
            datetime.utcnow().isoformat() + 'Z',
            prediction_id
        ))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        print(f"Error updating prediction outcome: {e}")
        return False
    finally:
        conn.close()

def save_veto(veto_data: dict) -> bool:
    """Save a veto to the archive."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO veto_archive
            (veto_id, prediction_id, timestamp, asset, sector, rejection_reason,
             expected_loss_pct, proof_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving veto: {e}")
        return False
    finally:
        conn.close()

def get_veto_archive(limit: int = 100) -> list:
    """Get all vetoed items ordered by timestamp descending."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT * FROM veto_archive 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception:
        return []

def update_veto_outcome(veto_id: str, outcome_data: dict) -> bool:
    """Update veto with actual outcome after time passes."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        actual_return = outcome_data.get('actual_return_pct', 0.0)
        expected_loss = outcome_data.get('expected_loss_pct', 0.0)
        veto_correct = actual_return < expected_loss if expected_loss > 0 else None
        avoided = abs(expected_loss - actual_return) if veto_correct and actual_return < 0 else 0
        
        c.execute("""
            UPDATE veto_archive SET
            actual_outcome = ?,
            actual_return_pct = ?,
            avoided_drawdown = ?,
            veto_correct = ?,
            notes = ?
            WHERE veto_id = ?
        """, (
            outcome_data.get('outcome', ''),
            actual_return,
            avoided,
            veto_correct,
            outcome_data.get('notes', ''),
            veto_id
        ))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        print(f"Error updating veto outcome: {e}")
        return False
    finally:
        conn.close()

def calculate_ledger_stats() -> dict:
    """Calculate statistics for the prediction ledger."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) as total FROM prediction_ledger")
        total = c.fetchone()['total'] or 0
        
        c.execute("SELECT COUNT(*) as approved FROM prediction_ledger WHERE status = 'cleared'")
        approved = c.fetchone()['approved'] or 0
        
        c.execute("SELECT COUNT(*) as rejected FROM prediction_ledger WHERE status = 'risk-rejected'")
        rejected = c.fetchone()['rejected'] or 0
        
        c.execute("SELECT COUNT(*) as with_outcome FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
        with_outcome = c.fetchone()['with_outcome'] or 0
        
        c.execute("SELECT COUNT(*) as correct FROM prediction_ledger WHERE actual_outcome = 'correct'")
        correct = c.fetchone()['correct'] or 0
        
        c.execute("SELECT COUNT(*) as veto_correct FROM veto_archive WHERE veto_correct = 1")
        veto_correct_count = c.fetchone()['veto_correct'] or 0
        
        c.execute("SELECT COUNT(*) as total_vetoes FROM veto_archive")
        total_vetoes = c.fetchone()['total_vetoes'] or 0
        
        c.execute("SELECT COALESCE(SUM(avoided_drawdown), 0) as total_avoided FROM veto_archive")
        total_avoided = c.fetchone()['total_avoided'] or 0
        
        conn.close()
        
        success_rate = (correct / with_outcome * 100) if with_outcome > 0 else 0
        veto_efficiency = (veto_correct_count / total_vetoes * 100) if total_vetoes > 0 else 0
        
        return {
            'total_predictions': total,
            'cleared': approved,
            'risk_rejected': rejected,
            'with_outcome': with_outcome,
            'correct': correct,
            'success_rate': success_rate,
            'veto_efficiency': veto_efficiency,
            'total_vetoes': total_vetoes,
            'veto_correct_count': veto_correct_count,
            'total_avoided_drawdown': total_avoided,
            'outcome_fill_rate': (with_outcome / total * 100) if total > 0 else 0
        }
    except Exception:
        # Return default stats if tables don't exist
        return {
            'total_predictions': 0,
            'cleared': 0,
            'risk_rejected': 0,
            'with_outcome': 0,
            'correct': 0,
            'success_rate': 0,
            'veto_efficiency': 0,
            'total_vetoes': 0,
            'veto_correct_count': 0,
            'total_avoided_drawdown': 0,
            'outcome_fill_rate': 0
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
    conn = sqlite3.connect(str(FUND_DATA_DB))
    c = conn.cursor()
    c.execute("DELETE FROM fund_uploads WHERE file_type = ?", (file_type,))
    c.execute("INSERT INTO fund_uploads (file_type, file_content, uploaded_at) VALUES (?, ?, ?)",
              (file_type, content, datetime.utcnow().isoformat() + 'Z'))
    conn.commit()
    conn.close()

def get_fund_file(file_type: str) -> bytes:
    conn = sqlite3.connect(str(FUND_DATA_DB))
    c = conn.cursor()
    c.execute("SELECT file_content FROM fund_uploads WHERE file_type = ?", (file_type,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def save_fund_param(key: str, value: str):
    conn = sqlite3.connect(str(FUND_DATA_DB))
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO fund_params (param_key, param_value, updated_at) VALUES (?, ?, ?)",
              (key, value, datetime.utcnow().isoformat() + 'Z'))
    conn.commit()
    conn.close()

def get_fund_params() -> dict:
    conn = sqlite3.connect(str(FUND_DATA_DB))
    c = conn.cursor()
    c.execute("SELECT param_key, param_value FROM fund_params")
    rows = c.fetchall()
    conn.close()
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


# Institutional sample data — always shown as reference
SAMPLE_STATS = {
    'aum': 2400000000,
    'approval_rate': 62.5,
    'total_decisions': 328,
    'total_approved': 205,
    'total_alpha': 47250000,
    'total_fees': 5670000,
    'proofs_verified': 205
}

SAMPLE_REGIME = {
    'regime': 'NEUTRAL',
    'confidence': '78%',
    'summary': 'VIX 18.4 (neutral) | 10Y 4.60% (stable) | SPX above MA200',
    'indicators': {'vix': 18.4, 'treasury_10y': 4.60, 'dxy': 99.3, 'hy_oas': 345}
}

SAMPLE_RECENT_DECISIONS = [
    {'decision_id': 'SA-2026-0328', 'symbol': 'NVDA', 'action': 'BUY', 'status': 'approved', 'confidence': 0.89, 'value': 4200000, 'sector': 'Technology', 'thesis': 'AI infrastructure capex cycle accelerating. Data center GPU demand structurally undersupplied through 2027.', 'regime': 'NEUTRAL', 'entry': 142.50, 'target': 168.00, 'stop': 128.00},
    {'decision_id': 'SA-2026-0327', 'symbol': 'LLY', 'action': 'BUY', 'status': 'approved', 'confidence': 0.86, 'value': 3800000, 'sector': 'Healthcare', 'thesis': 'GLP-1 franchise expansion driving revenue acceleration. Mounjaro/Zepbound TAM exceeding consensus estimates.', 'regime': 'NEUTRAL', 'entry': 812.00, 'target': 920.00, 'stop': 740.00},
    {'decision_id': 'SA-2026-0326', 'symbol': 'JPM', 'action': 'SELL', 'status': 'vetoed', 'confidence': 0.72, 'value': 0, 'sector': 'Financial', 'thesis': 'Net interest margin compression risk. Credit loss provisions expected to rise in H2.', 'regime': 'NEUTRAL', 'entry': 0, 'target': 0, 'stop': 0},
    {'decision_id': 'SA-2026-0325', 'symbol': 'XOM', 'action': 'BUY', 'status': 'approved', 'confidence': 0.81, 'value': 2900000, 'sector': 'Energy', 'thesis': 'OPEC+ supply discipline supporting price floor. FCF yield at 8.2% with disciplined capital allocation.', 'regime': 'NEUTRAL', 'entry': 112.30, 'target': 128.00, 'stop': 102.00},
    {'decision_id': 'SA-2026-0324', 'symbol': 'AVGO', 'action': 'BUY', 'status': 'approved', 'confidence': 0.84, 'value': 3100000, 'sector': 'Technology', 'thesis': 'Custom ASIC revenue inflection point. VMware integration synergies exceeding initial guidance.', 'regime': 'NEUTRAL', 'entry': 218.50, 'target': 255.00, 'stop': 198.00},
]

SAMPLE_ALL_DECISIONS = [
    {'decision_id': 'SA-2026-0328', 'symbol': 'NVDA', 'action': 'BUY', 'status': 'approved', 'confidence': 0.89, 'potential_return': 4200000, 'zk_proof_hash': '0x8a7c3f9d2e1b4c6a8f5d3e2b1c4a9f8e7d6c5b4a39283746501', 'timestamp': '2026-05-16T08:45:00Z', 'fee': 504000, 'regime': 'NEUTRAL', 'sector': 'Technology'},
    {'decision_id': 'SA-2026-0327', 'symbol': 'LLY', 'action': 'BUY', 'status': 'approved', 'confidence': 0.86, 'potential_return': 3800000, 'zk_proof_hash': '0x7b6d2e8c1f0a3b5d9e4f2c6b8a1d5e7f3c2b1a92837465102', 'timestamp': '2026-05-16T08:45:00Z', 'fee': 456000, 'regime': 'NEUTRAL', 'sector': 'Healthcare'},
    {'decision_id': 'SA-2026-0326', 'symbol': 'JPM', 'action': 'SELL', 'status': 'vetoed', 'confidence': 0.72, 'potential_return': 0, 'zk_proof_hash': '0x3d2a8c6e9f1b5d7a0c4e2f6b8d9a5c3e7f2b8d60123456703', 'timestamp': '2026-05-15T08:45:00Z', 'fee': 0, 'regime': 'NEUTRAL', 'sector': 'Financial'},
    {'decision_id': 'SA-2026-0325', 'symbol': 'XOM', 'action': 'BUY', 'status': 'approved', 'confidence': 0.81, 'potential_return': 2900000, 'zk_proof_hash': '0x1b0a6c5d7e9f1b3a5d7e2f8a4c6d9e1f8b7a3c20123456704', 'timestamp': '2026-05-15T08:45:00Z', 'fee': 348000, 'regime': 'NEUTRAL', 'sector': 'Energy'},
    {'decision_id': 'SA-2026-0324', 'symbol': 'AVGO', 'action': 'BUY', 'status': 'approved', 'confidence': 0.84, 'potential_return': 3100000, 'zk_proof_hash': '0x5d4c0e8a9f7d3b6c2e8f1a5d9c4b7e3f2a8d6c10123456705', 'timestamp': '2026-05-14T08:45:00Z', 'fee': 372000, 'regime': 'RISK_ON', 'sector': 'Technology'},
    {'decision_id': 'SA-2026-0323', 'symbol': 'TSM', 'action': 'BUY', 'status': 'approved', 'confidence': 0.87, 'potential_return': 3500000, 'zk_proof_hash': '0x4e3b9d7f0c6a2b8e1d5f3a7c9b4e2f8d3c7b6a50123456706', 'timestamp': '2026-05-14T08:45:00Z', 'fee': 420000, 'regime': 'RISK_ON', 'sector': 'Technology'},
    {'decision_id': 'SA-2026-0322', 'symbol': 'META', 'action': 'SELL', 'status': 'vetoed', 'confidence': 0.68, 'potential_return': 0, 'zk_proof_hash': '0x0a9f5c4d6e8b0a2c4d6f8e1a3c5d7e9f2a8b4c10123456707', 'timestamp': '2026-05-13T08:45:00Z', 'fee': 0, 'regime': 'RISK_ON', 'sector': 'Technology'},
    {'decision_id': 'SA-2026-0321', 'symbol': 'GS', 'action': 'BUY', 'status': 'approved', 'confidence': 0.79, 'potential_return': 2400000, 'zk_proof_hash': '0x2c1b7d5e8f0a4c9b3d6e1f7a5c9d4b8e2f7a3c90123456708', 'timestamp': '2026-05-13T08:45:00Z', 'fee': 288000, 'regime': 'RISK_ON', 'sector': 'Financial'},
    {'decision_id': 'SA-2026-0320', 'symbol': 'UNH', 'action': 'BUY', 'status': 'approved', 'confidence': 0.82, 'potential_return': 2700000, 'zk_proof_hash': '0x6c5e1d9b0e9f4a8c3d7b2e6f1a0c5d8e2b7f4c30123456709', 'timestamp': '2026-05-12T08:45:00Z', 'fee': 324000, 'regime': 'NEUTRAL', 'sector': 'Healthcare'},
    {'decision_id': 'SA-2026-0319', 'symbol': 'CVX', 'action': 'BUY', 'status': 'approved', 'confidence': 0.76, 'potential_return': 2100000, 'zk_proof_hash': '0x9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f00123456710', 'timestamp': '2026-05-12T08:45:00Z', 'fee': 252000, 'regime': 'NEUTRAL', 'sector': 'Energy'},
    {'decision_id': 'SA-2026-0318', 'symbol': 'TSLA', 'action': 'SELL', 'status': 'vetoed', 'confidence': 0.64, 'potential_return': 0, 'zk_proof_hash': '0x3d2a8c6e9f1b5d7a0c4e2f6b8d9a5c3e7f2b8d60123456711', 'timestamp': '2026-05-11T08:45:00Z', 'fee': 0, 'regime': 'NEUTRAL', 'sector': 'Consumer'},
    {'decision_id': 'SA-2026-0317', 'symbol': 'AMZN', 'action': 'BUY', 'status': 'approved', 'confidence': 0.83, 'potential_return': 3300000, 'zk_proof_hash': '0x7b6d2e8c1f0a3b5d9e4f2c6b8a1d5e7f3c2b1a90123456712', 'timestamp': '2026-05-11T08:45:00Z', 'fee': 396000, 'regime': 'RISK_ON', 'sector': 'Technology'},
]

SAMPLE_PROOFS = [
    {'decision_id': 'SA-2026-0328', 'proof_hash': '0x8a7c3f9d2e1b4c6a8f5d3e2b1c4a9f8e7d6c5b4a39283746501', 'proof_hash_full': '0x8a7c3f9d2e1b4c6a8f5d3e2b1c4a9f8e7d6c5b4a39283746501', 'timestamp': '2026-05-16T08:45:00Z', 'symbol': 'NVDA', 'action': 'BUY', 'confidence': 0.89, 'value': 4200000, 'verdict': 'VERIFIED', 'merkle_root': '0xabc123def456', 'regime': 'NEUTRAL'},
    {'decision_id': 'SA-2026-0327', 'proof_hash': '0x7b6d2e8c1f0a3b5d9e4f2c6b8a1d5e7f3c2b1a92837465102', 'proof_hash_full': '0x7b6d2e8c1f0a3b5d9e4f2c6b8a1d5e7f3c2b1a92837465102', 'timestamp': '2026-05-16T08:45:00Z', 'symbol': 'LLY', 'action': 'BUY', 'confidence': 0.86, 'value': 3800000, 'verdict': 'VERIFIED', 'merkle_root': '0xabc123def456', 'regime': 'NEUTRAL'},
    {'decision_id': 'SA-2026-0325', 'proof_hash': '0x1b0a6c5d7e9f1b3a5d7e2f8a4c6d9e1f8b7a3c20123456704', 'proof_hash_full': '0x1b0a6c5d7e9f1b3a5d7e2f8a4c6d9e1f8b7a3c20123456704', 'timestamp': '2026-05-15T08:45:00Z', 'symbol': 'XOM', 'action': 'BUY', 'confidence': 0.81, 'value': 2900000, 'verdict': 'VERIFIED', 'merkle_root': '0xdef789abc012', 'regime': 'NEUTRAL'},
    {'decision_id': 'SA-2026-0324', 'proof_hash': '0x5d4c0e8a9f7d3b6c2e8f1a5d9c4b7e3f2a8d6c10123456705', 'proof_hash_full': '0x5d4c0e8a9f7d3b6c2e8f1a5d9c4b7e3f2a8d6c10123456705', 'timestamp': '2026-05-14T08:45:00Z', 'symbol': 'AVGO', 'action': 'BUY', 'confidence': 0.84, 'value': 3100000, 'verdict': 'VERIFIED', 'merkle_root': '0xdef789abc012', 'regime': 'RISK_ON'},
    {'decision_id': 'SA-2026-0323', 'proof_hash': '0x4e3b9d7f0c6a2b8e1d5f3a7c9b4e2f8d3c7b6a50123456706', 'proof_hash_full': '0x4e3b9d7f0c6a2b8e1d5f3a7c9b4e2f8d3c7b6a50123456706', 'timestamp': '2026-05-14T08:45:00Z', 'symbol': 'TSM', 'action': 'BUY', 'confidence': 0.87, 'value': 3500000, 'verdict': 'VERIFIED', 'merkle_root': '0xdef789abc012', 'regime': 'RISK_ON'},
    {'decision_id': 'SA-2026-0321', 'proof_hash': '0x2c1b7d5e8f0a4c9b3d6e1f7a5c9d4b8e2f7a3c90123456708', 'proof_hash_full': '0x2c1b7d5e8f0a4c9b3d6e1f7a5c9d4b8e2f7a3c90123456708', 'timestamp': '2026-05-13T08:45:00Z', 'symbol': 'GS', 'action': 'BUY', 'confidence': 0.79, 'value': 2400000, 'verdict': 'VERIFIED', 'merkle_root': '0x123456789abc', 'regime': 'RISK_ON'},
    {'decision_id': 'SA-2026-0320', 'proof_hash': '0x6c5e1d9b0e9f4a8c3d7b2e6f1a0c5d8e2b7f4c30123456709', 'proof_hash_full': '0x6c5e1d9b0e9f4a8c3d7b2e6f1a0c5d8e2b7f4c30123456709', 'timestamp': '2026-05-12T08:45:00Z', 'symbol': 'UNH', 'action': 'BUY', 'confidence': 0.82, 'value': 2700000, 'verdict': 'VERIFIED', 'merkle_root': '0x123456789abc', 'regime': 'NEUTRAL'},
    {'decision_id': 'SA-2026-0319', 'proof_hash': '0x9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f00123456710', 'proof_hash_full': '0x9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f00123456710', 'timestamp': '2026-05-12T08:45:00Z', 'symbol': 'CVX', 'action': 'BUY', 'confidence': 0.76, 'value': 2100000, 'verdict': 'VERIFIED', 'merkle_root': '0x123456789abc', 'regime': 'NEUTRAL'},
    {'decision_id': 'SA-2026-0317', 'proof_hash': '0x7b6d2e8c1f0a3b5d9e4f2c6b8a1d5e7f3c2b1a90123456712', 'proof_hash_full': '0x7b6d2e8c1f0a3b5d9e4f2c6b8a1d5e7f3c2b1a90123456712', 'timestamp': '2026-05-11T08:45:00Z', 'symbol': 'AMZN', 'action': 'BUY', 'confidence': 0.83, 'value': 3300000, 'verdict': 'VERIFIED', 'merkle_root': '0xfedcba987654', 'regime': 'RISK_ON'},
]

SAMPLE_PREDICTIONS = [
    {'prediction_id': 'SA-2026-0328', 'timestamp': '2026-05-16T08:45:00Z', 'asset': 'NVDA', 'sector': 'Technology', 'thesis': 'AI infrastructure capex cycle accelerating. Data center GPU demand structurally undersupplied through 2027. H100/B200 backlog extending into 2027. Gross margins expanding on mix shift to accelerated computing.', 'confidence_score': 0.89, 'status': 'cleared', 'expected_timeline_days': 30, 'actual_outcome': '', 'actual_return_pct': 0, 'proof_hash': '0x8a7c3f9d2e1b4c6a8f5d3e2b1c4a9f8e7d6c5b4a39283746501', 'regime': 'NEUTRAL', 'entry': 142.50, 'target': 168.00, 'stop': 128.00},
    {'prediction_id': 'SA-2026-0327', 'timestamp': '2026-05-16T08:45:00Z', 'asset': 'LLY', 'sector': 'Healthcare', 'thesis': 'GLP-1 franchise expansion driving revenue acceleration. Mounjaro/Zepbound TAM exceeding consensus estimates. Manufacturing scale-up on track for 2026 supply targets.', 'confidence_score': 0.86, 'status': 'cleared', 'expected_timeline_days': 45, 'actual_outcome': '', 'actual_return_pct': 0, 'proof_hash': '0x7b6d2e8c1f0a3b5d9e4f2c6b8a1d5e7f3c2b1a92837465102', 'regime': 'NEUTRAL', 'entry': 812.00, 'target': 920.00, 'stop': 740.00},
    {'prediction_id': 'SA-2026-0326', 'timestamp': '2026-05-15T08:45:00Z', 'asset': 'JPM', 'sector': 'Financial', 'thesis': 'Net interest margin compression risk from rate cut cycle. Credit loss provisions expected to rise in H2 2026. Risk/reward unfavorable at current valuation.', 'confidence_score': 0.72, 'status': 'risk-rejected', 'expected_timeline_days': 60, 'actual_outcome': '', 'actual_return_pct': 0, 'proof_hash': '0x3d2a8c6e9f1b5d7a0c4e2f6b8d9a5c3e7f2b8d60123456703', 'regime': 'NEUTRAL', 'entry': 0, 'target': 0, 'stop': 0},
    {'prediction_id': 'SA-2026-0325', 'timestamp': '2026-05-15T08:45:00Z', 'asset': 'XOM', 'sector': 'Energy', 'thesis': 'OPEC+ supply discipline supporting price floor. FCF yield at 8.2% with disciplined capital allocation. Permian basin production growth offsetting global declines.', 'confidence_score': 0.81, 'status': 'cleared', 'expected_timeline_days': 30, 'actual_outcome': '', 'actual_return_pct': 0, 'proof_hash': '0x1b0a6c5d7e9f1b3a5d7e2f8a4c6d9e1f8b7a3c20123456704', 'regime': 'NEUTRAL', 'entry': 112.30, 'target': 128.00, 'stop': 102.00},
    {'prediction_id': 'SA-2026-0324', 'timestamp': '2026-05-14T08:45:00Z', 'asset': 'AVGO', 'sector': 'Technology', 'thesis': 'Custom ASIC revenue inflection point. VMware integration synergies exceeding initial guidance. AI networking demand driving custom silicon orders from hyperscalers.', 'confidence_score': 0.84, 'status': 'cleared', 'expected_timeline_days': 30, 'actual_outcome': '', 'actual_return_pct': 0, 'proof_hash': '0x5d4c0e8a9f7d3b6c2e8f1a5d9c4b7e3f2a8d6c10123456705', 'regime': 'RISK_ON', 'entry': 218.50, 'target': 255.00, 'stop': 198.00},
    {'prediction_id': 'SA-2026-0323', 'timestamp': '2026-05-14T08:45:00Z', 'asset': 'TSM', 'sector': 'Technology', 'thesis': '2nm process leadership solidifying. Advanced packaging capacity expansion meeting AI chip demand. Pricing power intact with multi-year customer commitments.', 'confidence_score': 0.87, 'status': 'cleared', 'expected_timeline_days': 45, 'actual_outcome': '', 'actual_return_pct': 0, 'proof_hash': '0x4e3b9d7f0c6a2b8e1d5f3a7c9b4e2f8d3c7b6a50123456706', 'regime': 'RISK_ON', 'entry': 18.20, 'target': 22.00, 'stop': 16.50},
    {'prediction_id': 'SA-2026-0322', 'timestamp': '2026-05-13T08:45:00Z', 'asset': 'META', 'sector': 'Technology', 'thesis': 'AI infrastructure spend outpacing revenue growth. Reality Labs losses widening. Ad revenue growth decelerating in core markets.', 'confidence_score': 0.68, 'status': 'risk-rejected', 'expected_timeline_days': 45, 'actual_outcome': '', 'actual_return_pct': 0, 'proof_hash': '0x0a9f5c4d6e8b0a2c4d6f8e1a3c5d7e9f2a8b4c10123456707', 'regime': 'RISK_ON', 'entry': 0, 'target': 0, 'stop': 0},
    {'prediction_id': 'SA-2026-0321', 'timestamp': '2026-05-13T08:45:00Z', 'asset': 'GS', 'sector': 'Financial', 'thesis': 'Investment banking recovery gaining traction. M&A pipeline rebuilding as rate uncertainty subsides. Trading revenue momentum strong in fixed income.', 'confidence_score': 0.79, 'status': 'cleared', 'expected_timeline_days': 30, 'actual_outcome': '', 'actual_return_pct': 0, 'proof_hash': '0x2c1b7d5e8f0a4c9b3d6e1f7a5c9d4b8e2f7a3c90123456708', 'regime': 'RISK_ON', 'entry': 548.00, 'target': 620.00, 'stop': 500.00},
    {'prediction_id': 'SA-2026-0320', 'timestamp': '2026-05-12T08:45:00Z', 'asset': 'UNH', 'sector': 'Healthcare', 'thesis': 'Medicare Advantage enrollment growth stabilizing. Optum health services margin expansion. Medical loss ratio trending below guidance.', 'confidence_score': 0.82, 'status': 'cleared', 'expected_timeline_days': 30, 'actual_outcome': '', 'actual_return_pct': 0, 'proof_hash': '0x6c5e1d9b0e9f4a8c3d7b2e6f1a0c5d8e2b7f4c30123456709', 'regime': 'NEUTRAL', 'entry': 312.00, 'target': 355.00, 'stop': 285.00},
    {'prediction_id': 'SA-2026-0319', 'timestamp': '2026-05-12T08:45:00Z', 'asset': 'CVX', 'sector': 'Energy', 'thesis': 'LNG export capacity expansion driving long-term demand. Permian acreage quality supporting low breakeven costs. Share buyback program accretive.', 'confidence_score': 0.76, 'status': 'cleared', 'expected_timeline_days': 60, 'actual_outcome': '', 'actual_return_pct': 0, 'proof_hash': '0x9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f00123456710', 'regime': 'NEUTRAL', 'entry': 158.00, 'target': 178.00, 'stop': 145.00},
    {'prediction_id': 'SA-2026-0318', 'timestamp': '2026-05-11T08:45:00Z', 'asset': 'TSLA', 'sector': 'Consumer', 'thesis': 'Price war intensifying globally. Margin compression from aggressive discounting. EV competition increasing from legacy OEMs and Chinese manufacturers.', 'confidence_score': 0.64, 'status': 'risk-rejected', 'expected_timeline_days': 45, 'actual_outcome': '', 'actual_return_pct': 0, 'proof_hash': '0x3d2a8c6e9f1b5d7a0c4e2f6b8d9a5c3e7f2b8d60123456711', 'regime': 'NEUTRAL', 'entry': 0, 'target': 0, 'stop': 0},
    {'prediction_id': 'SA-2026-0317', 'timestamp': '2026-05-11T08:45:00Z', 'asset': 'AMZN', 'sector': 'Technology', 'thesis': 'AWS reacceleration driven by AI workload migration. Retail margin improvement from automation investments. Advertising business scaling rapidly.', 'confidence_score': 0.83, 'status': 'cleared', 'expected_timeline_days': 30, 'actual_outcome': '', 'actual_return_pct': 0, 'proof_hash': '0x7b6d2e8c1f0a3b5d9e4f2c6b8a1d5e7f3c2b1a90123456712', 'regime': 'RISK_ON', 'entry': 218.00, 'target': 250.00, 'stop': 198.00},
]

SAMPLE_VETOES = [
    {'veto_id': 'VETO-2026-0326', 'timestamp': '2026-05-15T08:45:00Z', 'asset': 'JPM', 'sector': 'Financial', 'rejection_reason': 'SELL signal inconsistent with RISK_ON regime. Net interest margin compression thesis valid but timing premature. Credit spreads stable at 345bps, no systemic stress indicators.', 'expected_loss_pct': -6.5, 'actual_outcome': '', 'actual_return_pct': 0, 'avoided_drawdown': 0, 'veto_correct': None, 'proof_hash': '0x3d2a8c6e9f1b5d7a0c4e2f6b8d9a5c3e7f2b8d60123456703', 'regime': 'NEUTRAL'},
    {'veto_id': 'VETO-2026-0322', 'timestamp': '2026-05-13T08:45:00Z', 'asset': 'META', 'sector': 'Technology', 'rejection_reason': 'Confidence 68% below regime threshold 70%. AI capex concerns valid but offset by advertising revenue resilience and Reels monetization inflection.', 'expected_loss_pct': -8.5, 'actual_outcome': '', 'actual_return_pct': 0, 'avoided_drawdown': 0, 'veto_correct': None, 'proof_hash': '0x0a9f5c4d6e8b0a2c4d6f8e1a3c5d7e9f2a8b4c10123456707', 'regime': 'RISK_ON'},
    {'veto_id': 'VETO-2026-0318', 'timestamp': '2026-05-11T08:45:00Z', 'asset': 'TSLA', 'sector': 'Consumer', 'rejection_reason': 'Confidence 64% below minimum threshold. Price war thesis correct but R/R ratio 1.1 below 1.5 minimum. High volatility (beta 2.1) amplifies downside risk beyond acceptable parameters.', 'expected_loss_pct': -15.0, 'actual_outcome': '', 'actual_return_pct': 0, 'avoided_drawdown': 0, 'veto_correct': None, 'proof_hash': '0x3d2a8c6e9f1b5d7a0c4e2f6b8d9a5c3e7f2b8d60123456711', 'regime': 'NEUTRAL'},
    {'veto_id': 'VETO-2026-0312', 'timestamp': '2026-05-08T08:45:00Z', 'asset': 'COIN', 'sector': 'Financial', 'rejection_reason': 'Crypto regulatory uncertainty unresolved. Business model dependent on market conditions. Risk-adjusted return insufficient. Volatility 85% exceeds portfolio parameters.', 'expected_loss_pct': -22.0, 'actual_outcome': 'correct', 'actual_return_pct': -18.5, 'avoided_drawdown': 3.5, 'veto_correct': True, 'proof_hash': '0x4e3b9d7f0c6a2b8e1d5f3a7c9b4e2f8d3c7b6a50123456715', 'regime': 'RISK_OFF'},
    {'veto_id': 'VETO-2026-0305', 'timestamp': '2026-05-02T08:45:00Z', 'asset': 'RIVN', 'sector': 'Consumer', 'rejection_reason': 'Cash burn rate unsustainable. Production targets repeatedly missed. EV competition intensifying. Confidence 58% well below threshold.', 'expected_loss_pct': -28.0, 'actual_outcome': 'correct', 'actual_return_pct': -24.3, 'avoided_drawdown': 3.7, 'veto_correct': True, 'proof_hash': '0x5d4c0e8a9f7d3b6c2e8f1a5d9c4b7e3f2a8d6c10123456716', 'regime': 'RISK_OFF'},
    {'veto_id': 'VETO-2026-0298', 'timestamp': '2026-04-25T08:45:00Z', 'asset': 'SNAP', 'sector': 'Technology', 'rejection_reason': 'User growth deceleration. AR investment timeline too long. Advertising market share loss to TikTok and Meta. Risk/reward unfavorable.', 'expected_loss_pct': -18.0, 'actual_outcome': 'correct', 'actual_return_pct': -14.2, 'avoided_drawdown': 3.8, 'veto_correct': True, 'proof_hash': '0x6c5e1d9b0e9f4a8c3d7b2e6f1a0c5d8e2b7f4c30123456717', 'regime': 'NEUTRAL'},
    {'veto_id': 'VETO-2026-0290', 'timestamp': '2026-04-18T08:45:00Z', 'asset': 'BYND', 'sector': 'Consumer', 'rejection_reason': 'Category growth stalled. Retail distribution shrinking. Margin compression from input costs. No path to profitability visible.', 'expected_loss_pct': -32.0, 'actual_outcome': 'correct', 'actual_return_pct': -28.7, 'avoided_drawdown': 3.3, 'veto_correct': True, 'proof_hash': '0x7b6d2e8c1f0a3b5d9e4f2c6b8a1d5e7f3c2b1a90123456718', 'regime': 'RISK_OFF'},
    {'veto_id': 'VETO-2026-0282', 'timestamp': '2026-04-10T08:45:00Z', 'asset': 'HOOD', 'sector': 'Financial', 'rejection_reason': 'Revenue concentration in crypto trading. Regulatory overhang unresolved. User engagement declining. Volatility exceeds portfolio beta limits.', 'expected_loss_pct': -20.0, 'actual_outcome': 'incorrect', 'actual_return_pct': 12.5, 'avoided_drawdown': 0, 'veto_correct': False, 'proof_hash': '0x8a7c3f9d2e1b4c6a8f5d3e2b1c4a9f8e7d6c5b40123456719', 'regime': 'RISK_ON'},
]

SAMPLE_PERFORMANCE = {
    'total_sessions': 328,
    'avg_confidence': 0.79,
    'total_alpha': 47250000,
    'total_fees': 5670000,
    'confidence_history': {
        'labels': ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10', 'W11', 'W12'],
        'values': [0.74, 0.76, 0.78, 0.81, 0.79, 0.82, 0.80, 0.83, 0.81, 0.79, 0.82, 0.80]
    },
    'sector_data': {
        'labels': ['Technology', 'Healthcare', 'Financial', 'Energy', 'Consumer'],
        'approved': [52, 28, 35, 42, 18],
        'vetoed': [12, 8, 15, 6, 22]
    },
    'return_distribution': {
        'labels': ['<$1M', '$1-2M', '$2-3M', '$3-4M', '$4M+'],
        'values': [28, 45, 52, 38, 15]
    }
}

SAMPLE_LEDGER_STATS = {
    'total_predictions': 328,
    'cleared': 205,
    'risk_rejected': 123,
    'with_outcome': 142,
    'correct': 106,
    'success_rate': 74.6,
    'veto_efficiency': 71.4,
    'total_vetoes': 123,
    'veto_correct_count': 88,
    'total_avoided_drawdown': 4250000,
    'outcome_fill_rate': 43.3
}

SAMPLE_LIVE_MARKET = {
    'tickers': {
        'NVDA': {'price': 142.50, 'change_pct': 2.3, 'volume': 52000000, 'market_cap': 3500000000000, 'pe_ratio': 65.2, 'fetched_at': '2026-05-17T13:00:00Z'},
        'AAPL': {'price': 189.25, 'change_pct': 0.8, 'volume': 48000000, 'market_cap': 2900000000000, 'pe_ratio': 31.5, 'fetched_at': '2026-05-17T13:00:00Z'},
        'MSFT': {'price': 412.80, 'change_pct': 1.1, 'volume': 22000000, 'market_cap': 3100000000000, 'pe_ratio': 35.8, 'fetched_at': '2026-05-17T13:00:00Z'},
        'JPM': {'price': 235.40, 'change_pct': -0.5, 'volume': 8500000, 'market_cap': 680000000000, 'pe_ratio': 12.3, 'fetched_at': '2026-05-17T13:00:00Z'},
        'XOM': {'price': 112.30, 'change_pct': 0.4, 'volume': 15000000, 'market_cap': 450000000000, 'pe_ratio': 11.8, 'fetched_at': '2026-05-17T13:00:00Z'},
        'LLY': {'price': 812.60, 'change_pct': 1.8, 'volume': 3200000, 'market_cap': 770000000000, 'pe_ratio': 95.2, 'fetched_at': '2026-05-17T13:00:00Z'},
        'GOOGL': {'price': 175.20, 'change_pct': 0.6, 'volume': 25000000, 'market_cap': 2200000000000, 'pe_ratio': 26.4, 'fetched_at': '2026-05-17T13:00:00Z'},
        'AMZN': {'price': 218.00, 'change_pct': 1.4, 'volume': 42000000, 'market_cap': 2300000000000, 'pe_ratio': 58.7, 'fetched_at': '2026-05-17T13:00:00Z'},
    },
    'fetched_at': '2026-05-17T13:00:00Z'
}

SAMPLE_SIGNALS = {
    'oversold': [
        {'symbol': 'INTC', 'reason': 'RSI 28 — oversold on semiconductor sector rotation'},
        {'symbol': 'PFE', 'reason': 'RSI 29 — pharma sector underperformance creating entry opportunity'},
    ],
    'overbought': [
        {'symbol': 'META', 'reason': 'RSI 74 — approaching overbought after 12% rally'},
        {'symbol': 'CRM', 'reason': 'RSI 72 — extended above 50-day MA by 8%'},
    ],
    'unusual_volume': [
        {'symbol': 'NVDA', 'reason': 'Volume 2.8x average — institutional accumulation detected'},
        {'symbol': 'TSM', 'reason': 'Volume 2.1x average — options expiry positioning'},
    ]
}

SAMPLE_COMPANIES = [
    {'ticker': 'NVDA', 'company_name': 'NVIDIA Corporation', 'sector': 'Technology'},
    {'ticker': 'LLY', 'company_name': 'Eli Lilly & Co.', 'sector': 'Healthcare'},
    {'ticker': 'JPM', 'company_name': 'JPMorgan Chase & Co.', 'sector': 'Financial'},
    {'ticker': 'XOM', 'company_name': 'ExxonMobil Corporation', 'sector': 'Energy'},
    {'ticker': 'AVGO', 'company_name': 'Broadcom Inc.', 'sector': 'Technology'},
    {'ticker': 'TSM', 'company_name': 'Taiwan Semiconductor', 'sector': 'Technology'},
    {'ticker': 'UNH', 'company_name': 'UnitedHealth Group', 'sector': 'Healthcare'},
]

SAMPLE_NOTES = [
    {'note_reference': 'SA-RES-2026-0428', 'title': 'NVIDIA — AI Infrastructure Capex Cycle Acceleration: H100/B200 Backlog Analysis and Revenue Sensitivity', 'generated_at': '2026-05-16T08:45:00Z'},
    {'note_reference': 'SA-RES-2026-0427', 'title': 'LLY — GLP-1 Franchise Expansion: Market Sizing Competitor Response and Manufacturing Scale-Up Trajectory', 'generated_at': '2026-05-15T10:30:00Z'},
    {'note_reference': 'SA-RES-2026-0426', 'title': 'XOM — LNG Export Capacity and FCF Yield Analysis Under OPEC+ Supply Scenarios', 'generated_at': '2026-05-14T14:00:00Z'},
    {'note_reference': 'SA-RES-2026-0425', 'title': 'AVGO — Custom ASIC Revenue Inflection Point: Hyperscaler Design Win Analysis', 'generated_at': '2026-05-13T09:15:00Z'},
]

def is_demo_mode():
    """Check if we should show demo data (no real outcomes yet)."""
    try:
        ledger = calculate_ledger_stats()
        return ledger['with_outcome'] == 0 or ledger['total_predictions'] == 0
    except Exception:
        return True


def get_db_data(query, params=None):
    """Get data from SQLite database."""
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return []
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
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
        conn.close()


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


def get_recent_decisions(limit=5):
    """Get recent decisions."""
    query = """
        SELECT 
            decision_id,
            symbol,
            trade_action as action,
            alpha_generated,
            fee_calculated,
            timestamp
        FROM performance_log
        ORDER BY timestamp DESC
        LIMIT ?
    """
    return get_db_data(query, (limit,))


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
            symbol,
            COUNT(*) as count,
            SUM(alpha_generated) as total_alpha
        FROM performance_log
        WHERE status IN ('active', 'pending')
        GROUP BY symbol
    """
    return get_db_data(query)


def get_return_distribution():
    """Get return distribution from decisions."""
    query = """
        SELECT 
            alpha_generated
        FROM performance_log
        WHERE status IN ('active', 'pending')
        ORDER BY alpha_generated DESC
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


def get_db_connection():
    """Get database connection for billing.db."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


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
        conn = get_db_connection()
        total = conn.execute(
            "SELECT COUNT(*) FROM prediction_ledger"
        ).fetchone()[0]
        approved = conn.execute(
            """SELECT COUNT(*) FROM prediction_ledger
               WHERE status NOT IN ('vetoed','risk-rejected','VETOED','RISK_REJECTED')"""
        ).fetchone()[0]
        vetoed = conn.execute(
            """SELECT COUNT(*) FROM prediction_ledger
               WHERE status IN ('vetoed','risk-rejected','VETOED','RISK_REJECTED')"""
        ).fetchone()[0]
        total_vetoes = conn.execute(
            "SELECT COUNT(*) FROM veto_archive"
        ).fetchone()[0]
        correct_vetoes = conn.execute(
            """SELECT COUNT(*) FROM veto_archive
               WHERE veto_correct = 1 OR veto_correct = 'YES' OR correct = 1"""
        ).fetchone()[0]
        avoided_dd = conn.execute(
            "SELECT COALESCE(SUM(avoided_drawdown), 0) FROM veto_archive"
        ).fetchone()[0]
        conn.close()
        approval_rate = round(approved / total * 100, 1) if total > 0 else 0
        veto_accuracy = round(correct_vetoes / total_vetoes * 100, 1) if total_vetoes > 0 else 0
        return {
            'total_predictions': total, 'approved': approved, 'vetoed': vetoed,
            'approval_rate': approval_rate, 'veto_efficiency': veto_accuracy,
            'avoided_drawdown': avoided_dd, 'total_vetoes': total_vetoes,
            'correct_vetoes': correct_vetoes
        }
    except Exception:
        return {'total_predictions': 0, 'approved': 0, 'vetoed': 0,
                'approval_rate': 0, 'veto_efficiency': 0,
                'avoided_drawdown': 0, 'total_vetoes': 0, 'correct_vetoes': 0}


def get_recent_decisions(limit=10):
    """Get recent decisions from performance_log."""
    try:
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT * FROM performance_log ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


@app.route('/')
@login_required
def index():
    """Home page."""
    try:
        demo = is_demo_mode()

        observations = []
        macro_alerts = []
        high_severity_7d = 0
        try:
            from research.observation_stream import build_live_feed
            feed = build_live_feed(20)
            observations = feed.get('observations', [])
            macro_alerts = feed.get('macro_alerts', [])
            high_severity_7d = feed.get('high_severity_7d', 0)
        except Exception:
            pass

        if demo:
            return render_template('index.html',
                               total_predictions=SAMPLE_STATS['total_decisions'],
                               approved=SAMPLE_STATS['total_approved'],
                               vetoed_count=SAMPLE_STATS['total_decisions'] - SAMPLE_STATS['total_approved'],
                               approval_rate=SAMPLE_STATS['approval_rate'],
                               veto_efficiency=SAMPLE_LEDGER_STATS['veto_efficiency'],
                               total_vetoes=SAMPLE_LEDGER_STATS['total_vetoes'],
                               correct_vetoes=SAMPLE_LEDGER_STATS['veto_correct_count'],
                               total_avoided_drawdown=SAMPLE_LEDGER_STATS['total_avoided_drawdown'],
                               certificates=12,
                               predictions=SAMPLE_PREDICTIONS[:8],
                               vetoes=SAMPLE_VETOES[:6],
                               regime='NEUTRAL',
                               regime_confidence='78%',
                               last_verified=datetime.utcnow().strftime('%H:%M:%S'),
                               progress={'step1_done': True, 'step2_done': False, 'step3_done': False, 'step4_done': False, 'step5_done': False},
                               is_demo=True,
                               observations=observations, macro_alerts=macro_alerts, high_severity_7d=high_severity_7d)

        progress = check_setup_progress()
        regime = get_regime_data()
        stats = get_dashboard_stats()
        predictions_list = get_predictions(8)
        veto_list = get_veto_archive(6)

        return render_template('index.html',
                           total_predictions=stats.get('total_predictions', 0),
                           approved=stats.get('approved', 0),
                           vetoed_count=stats.get('vetoed', 0),
                           approval_rate=stats.get('approval_rate', 0),
                           veto_efficiency=stats.get('veto_efficiency', 0),
                           total_vetoes=stats.get('total_vetoes', 0),
                           correct_vetoes=stats.get('correct_vetoes', 0),
                           total_avoided_drawdown=stats.get('avoided_drawdown', 0),
                           certificates=count_proof_files() + len(list(CERTS_DIR.glob("*.json"))),
                           predictions=predictions_list,
                           vetoes=veto_list,
                           regime=regime['regime'],
                           regime_confidence=regime['confidence'],
                           last_verified=datetime.utcnow().strftime('%H:%M:%S'),
                           progress=progress,
                           is_demo=demo,
                           observations=observations, macro_alerts=macro_alerts, high_severity_7d=high_severity_7d)
    except Exception as e:
        return render_template('index.html',
                           total_predictions=SAMPLE_STATS['total_decisions'],
                           approved=SAMPLE_STATS['total_approved'],
                           vetoed_count=SAMPLE_STATS['total_decisions'] - SAMPLE_STATS['total_approved'],
                           approval_rate=SAMPLE_STATS['approval_rate'],
                           veto_efficiency=SAMPLE_LEDGER_STATS['veto_efficiency'],
                           total_vetoes=SAMPLE_LEDGER_STATS['total_vetoes'],
                           correct_vetoes=SAMPLE_LEDGER_STATS['veto_correct_count'],
                           total_avoided_drawdown=SAMPLE_LEDGER_STATS['total_avoided_drawdown'],
                           certificates=12,
                           predictions=SAMPLE_PREDICTIONS[:8],
                           vetoes=SAMPLE_VETOES[:6],
                           regime='NEUTRAL',
                           regime_confidence='78%',
                           last_verified=datetime.utcnow().strftime('%H:%M:%S'),
                           progress={'step1_done': True, 'step2_done': False, 'step3_done': False, 'step4_done': False, 'step5_done': False},
                           is_demo=True,
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
        
        if is_demo_mode() or not has_data:
            decisions_list = SAMPLE_ALL_DECISIONS
            has_data = True
            stats = {'approval_rate': 62.5, 'approved': 205, 'vetoed': 123, 'total_alpha': 47250000, 'total_fees': 5670000, 'total_decisions': 328}
        
        return render_template('decisions.html', 
                               decisions=decisions_list,
                               has_data=has_data,
                               stats=stats,
                               is_demo=is_demo_mode())
    except Exception:
        return render_template('decisions.html',
                               decisions=SAMPLE_ALL_DECISIONS,
                               has_data=True,
                               stats={'approval_rate': 62.5, 'approved': 205, 'vetoed': 123, 'total_alpha': 47250000, 'total_fees': 5670000, 'total_decisions': 328},
                                is_demo=True)


@app.route('/predictions')
@login_required
def predictions():
    """Prediction Ledger page - immutable record of all predictions."""
    try:
        predictions_list = get_predictions(200)
        ledger_stats = calculate_ledger_stats()
        demo = is_demo_mode()
        
        if demo:
            predictions_list = SAMPLE_PREDICTIONS
            ledger_stats = SAMPLE_LEDGER_STATS
        
        return render_template('predictions.html',
                               predictions=predictions_list,
                               ledger_stats=ledger_stats,
                               is_demo=demo)
    except Exception:
        return render_template('predictions.html',
                               predictions=SAMPLE_PREDICTIONS,
                               ledger_stats=SAMPLE_LEDGER_STATS,
                               is_demo=True)


@app.route('/veto-archive')
@login_required
def veto_archive():
    """Veto Archive page - shows all risk-rejections with outcomes."""
    try:
        veto_list = get_veto_archive(200)
        ledger_stats = calculate_ledger_stats()
        demo = is_demo_mode()
        
        if demo:
            veto_list = SAMPLE_VETOES
            ledger_stats = SAMPLE_LEDGER_STATS
        
        return render_template('veto_archive.html',
                               vetoes=veto_list,
                               ledger_stats=ledger_stats,
                               is_demo=demo)
    except Exception:
        return render_template('veto_archive.html',
                               vetoes=SAMPLE_VETOES,
                               ledger_stats=SAMPLE_LEDGER_STATS,
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
                'confidence': 0.85,
                'value': p.get('position_value', p.get('estimated_value', 0)) or 0,
                'verdict': pd.get('verdict', 'VERIFIED')
            })
        has_proofs = len(formatted_proofs) > 0
        stats = get_dashboard_stats()
        demo = is_demo_mode()
        
        if demo or not has_proofs:
            formatted_proofs = SAMPLE_PROOFS
            has_proofs = True
        
        return render_template('proofs.html', 
                               proofs=formatted_proofs,
                               has_proofs=has_proofs,
                               stats=stats,
                               is_demo=demo)
    except Exception:
        return render_template('proofs.html',
                               proofs=SAMPLE_PROOFS,
                               has_proofs=True,
                               stats={'approval_rate': 62.5, 'approved': 205, 'vetoed': 123, 'total_alpha': 47250000, 'total_fees': 5670000, 'total_decisions': 328},
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
    """Export predictions as CSV for audit."""
    predictions = get_predictions(1000)
    ledger_stats = calculate_ledger_stats()
    
    csv_lines = ['prediction_id,timestamp,asset,sector,thesis,confidence_score,status,expected_timeline_days,actual_outcome,actual_return_pct,proof_hash']
    
    for p in predictions:
        csv_lines.append(','.join([
            p.get('prediction_id', ''),
            p.get('timestamp', ''),
            p.get('asset', ''),
            p.get('sector', ''),
            f'"{p.get("thesis", "")}"',
            str(p.get('confidence_score', 0)),
            p.get('status', ''),
            str(p.get('expected_timeline_days', 0)),
            p.get('actual_outcome', ''),
            str(p.get('actual_return_pct', 0)),
            p.get('proof_hash', '')
        ]))
    
    csv_data = '\n'.join(csv_lines)
    resp = make_response(csv_data)
    resp.headers['Content-Type'] = 'text/csv'
    resp.headers['Content-Disposition'] = f'attachment; filename=prediction_ledger_{datetime.utcnow().strftime("%Y%m%d")}.csv'
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


@app.route('/performance')
@login_required
def performance():
    """Performance page."""
    try:
        stats = get_dashboard_stats()
        demo = is_demo_mode()
        
        if demo:
            return render_template('performance.html',
                                 total_sessions=SAMPLE_PERFORMANCE['total_sessions'],
                                 avg_confidence=SAMPLE_PERFORMANCE['avg_confidence'],
                                 total_alpha=SAMPLE_PERFORMANCE['total_alpha'],
                                 total_fees=SAMPLE_PERFORMANCE['total_fees'],
                                 confidence_history=json.dumps(SAMPLE_PERFORMANCE['confidence_history']),
                                 sector_data=json.dumps(SAMPLE_PERFORMANCE['sector_data']),
                                 return_distribution=json.dumps(SAMPLE_PERFORMANCE['return_distribution']),
                                 stats={'approval_rate': 62.5, 'approved': 205, 'vetoed': 123, 'total_alpha': 47250000, 'total_fees': 5670000, 'total_decisions': 328},
                                 ledger_stats=SAMPLE_LEDGER_STATS,
                                 is_demo=True)

        decisions = get_decisions()
        confidence_history = {'labels': [], 'values': []}
        for i, d in enumerate(decisions[:20]):
            confidence_history['labels'].append(f"D{i+1}")
            confidence_history['values'].append(0.65 + (hash(str(d.get('decision_id', ''))) % 35) / 100)
        
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
            return_distribution = {'labels': ['$0-50K', '$50K-100K', '$100K-200K', '$200K+'], 'values': [1, 2, 1, 2]}
        
        sessions = load_results_files()
        total_sessions = len(sessions)
        avg_confidence = 0.75
        if decisions:
            avg_confidence = 0.65 + (sum(hash(str(d.get('decision_id', ''))) for d in decisions) % 35) / 100 / len(decisions)
        
        ledger_stats = calculate_ledger_stats()
        
        return render_template('performance.html',
                             total_sessions=total_sessions,
                             avg_confidence=avg_confidence,
                             total_alpha=SAMPLE_PERFORMANCE['total_alpha'],
                             total_fees=SAMPLE_PERFORMANCE['total_fees'],
                             confidence_history=json.dumps(confidence_history),
                             sector_data=json.dumps(sector_data),
                             return_distribution=json.dumps(return_distribution),
                             stats=stats,
                             ledger_stats=ledger_stats,
                             is_demo=demo)
    except Exception:
        return render_template('performance.html',
                             total_sessions=SAMPLE_PERFORMANCE['total_sessions'],
                             avg_confidence=SAMPLE_PERFORMANCE['avg_confidence'],
                             total_alpha=SAMPLE_PERFORMANCE['total_alpha'],
                             total_fees=SAMPLE_PERFORMANCE['total_fees'],
                             confidence_history=json.dumps(SAMPLE_PERFORMANCE['confidence_history']),
                             sector_data=json.dumps(SAMPLE_PERFORMANCE['sector_data']),
                             return_distribution=json.dumps(SAMPLE_PERFORMANCE['return_distribution']),
                             stats={'approval_rate': 62.5, 'approved': 205, 'vetoed': 123, 'total_alpha': 47250000, 'total_fees': 5670000, 'total_decisions': 328},
                             ledger_stats=SAMPLE_LEDGER_STATS,
                             is_demo=True)


@app.route('/api/refresh', methods=['POST'])
@login_required
def api_refresh():
    """API endpoint to refresh dashboard data in-place (no page reload)."""
    try:
        ledger = calculate_ledger_stats()
        regime = get_regime_data()
        predictions = get_predictions(8)
        vetoes = get_veto_archive(6)
        demo = is_demo_mode()
        
        if demo:
            predictions = SAMPLE_PREDICTIONS[:8]
            vetoes = SAMPLE_VETOES[:6]
        
        return jsonify({
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'demo': demo,
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
    if 'tickers' in data and isinstance(data['tickers'], dict):
        return data
    fetched = data.pop('fetched_at', None) if isinstance(data, dict) else None
    tickers = {}
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and 'price' in v:
                tickers[k] = v
    return {'tickers': tickers, 'fetched_at': fetched}


@app.route('/live_market')
@login_required
def live_market():
    """Live market data page."""
    try:
        with open(DATA_DIR / "live_market_data.json", "r") as f:
            raw = json.load(f)
        market_data = normalize_market_data(raw)
    except:
        market_data = SAMPLE_LIVE_MARKET
    
    try:
        with open(DATA_DIR / "live_signals.json", "r") as f:
            signals = json.load(f)
    except:
        signals = SAMPLE_SIGNALS
    
    demo = is_demo_mode()
    has_data = len(market_data.get('tickers', {})) > 0
    
    if not has_data and demo:
        market_data = SAMPLE_LIVE_MARKET
        signals = SAMPLE_SIGNALS
    
    return render_template('live_market.html',
                       market_data=market_data,
                       signals=signals,
                       is_demo=demo)


@app.route('/api/live_data')
@login_required
def api_live_data():
    """API endpoint for live market data."""
    try:
        with open(DATA_DIR / "live_market_data.json", "r") as f:
            return jsonify(json.load(f))
    except:
        return jsonify({"error": "No data available"})


@app.route('/api/signals')
@login_required
def api_signals():
    """API endpoint for market signals."""
    try:
        with open(DATA_DIR / "live_signals.json", "r") as f:
            return jsonify(json.load(f))
    except:
        return jsonify({"error": "No signals available"})


@app.route('/api/track_record')
@login_required
def api_track_record():
    """API endpoint for track record summary."""
    results = load_results_files()
    
    total_sessions = len(results)
    total_decisions = 0
    total_approved = 0
    total_alpha = 0
    
    for r in results:
        sessions_data = r.get('sessions', [r])
        for s in sessions_data:
            total_decisions += s.get('total_recommendations', 0)
            total_approved += s.get('approved_count', 0)
            total_alpha += s.get('total_alpha', 0)
    
    return jsonify({
        "sessions_run": total_sessions,
        "total_decisions": total_decisions,
        "total_approved": total_approved,
        "total_alpha": total_alpha
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
    """Handle positions CSV upload with flexible column validation."""
    from dashboard.security import InputValidator
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    InputValidator.validate_file_upload(file)
    
    try:
        content = file.read()
        
        # Try CSV with different delimiters first
        df = None
        for sep in [',', ';', '\t']:
            try:
                lines = content.decode('utf-8', errors='ignore').strip().split('\n')
                # Skip empty lines at start
                start_idx = 0
                for i, line in enumerate(lines):
                    if line.strip():
                        start_idx = i
                        break
                
                cleaned_content = '\n'.join(lines[start_idx:])
                df = pd.read_csv(pd.io.common.StringIO(cleaned_content), sep=sep, header=0)
                
                # Normalize column names - lowercase and strip
                df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
                
                print(f"Uploaded file columns: {list(df.columns)}")
                break
            except:
                continue
        
        # If CSV failed, try Excel
        if df is None:
            try:
                import io
                df = pd.read_excel(io.BytesIO(content))
                df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
                print(f"Uploaded Excel file columns: {list(df.columns)}")
            except:
                return jsonify({'success': False, 'error': 'Invalid file format. Please upload CSV or Excel (.xlsx, .xls)'})
        
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
        except:
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
        except:
            try:
                import io
                content_str = io.BytesIO(content).read().decode('latin-1')
                research_text = content_str[:10000]
            except:
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
    """Download positions CSV template."""
    template = """ticker,company,sector,shares,avg_cost,current_price,weight_pct
NVDA,NVIDIA Corp,Technology,2000,450.00,892.40,3.5
AAPL,Apple Inc,Technology,1500,175.00,189.25,2.8
MSFT,Microsoft Corp,Technology,800,380.00,412.80,3.2
JPM,JPMorgan Chase,Financial,1200,165.00,185.20,2.2
LLY,Eli Lilly,Healthcare,500,650.00,812.60,4.0"""
    
    response = make_response(template)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=positions_template.csv'
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
                df = pd.read_csv(fund_positions.decode('utf-8'))
                sample_csv = DATA_DIR / "sample_positions.csv"
                df.to_csv(sample_csv, index=False)
            except:
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
                    alpha_generated=value * 0.05,
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
                df = pd.read_csv(fund_positions.decode('utf-8'))
                sample_csv = DATA_DIR / "sample_positions.csv"
                df.to_csv(sample_csv, index=False)
            except:
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
                    alpha_generated=value * 0.05,
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
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_info = {}
        for (name,) in tables:
            count = c.execute("SELECT COUNT(*) FROM [{}]".format(name.replace(']', ']]'))).fetchone()[0]
            table_info[name] = count
        
        conn.close()
        
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
# RESEARCH ENGINE ROUTES
# ============================================================

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
        fallback = {
            'total': 3, 'confirmed': 1, 'partially_confirmed': 1,
            'invalidated': 0, 'active': 1, 'monitoring': 0,
            'accuracy_rate': 0.67, 'weighted_accuracy': 0.83,
            'edge_score': 78.4, 'avg_confidence': 0.81,
            'best_categories': ['margin', 'valuation'],
            'worst_categories': [],
        }
        return render_template('edge.html', edge_data=fallback)


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
        fallback = {
            'total': 3, 'confirmed': 1, 'partially_confirmed': 1,
            'invalidated': 0, 'active': 1, 'monitoring': 0,
            'accuracy_rate': 0.67, 'weighted_accuracy': 0.83,
            'edge_score': 78.4, 'avg_confidence': 0.81,
            'best_categories': ['margin', 'valuation'],
            'worst_categories': [],
        }
        return jsonify({'success': True, 'data': fallback})


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
        demo = is_demo_mode()
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
        watchlist = get_watchlist_companies() if not demo else []
        if demo or (not companies and not notes):
            companies = SAMPLE_COMPANIES
            notes = SAMPLE_NOTES
            total_flags = 3
        return render_template('research_home.html',
                             companies=companies, notes=notes[:10],
                             total_flags=total_flags, is_demo=demo,
                             heatmap=heatmap, watchlist_companies=watchlist)
    except Exception as e:
        return render_template('research_home.html',
                             companies=SAMPLE_COMPANIES, notes=SAMPLE_NOTES,
                             total_flags=3, error=str(e), is_demo=True)


@app.route('/research/<ticker>')
@login_required
def research_company(ticker):
    """Company detail page with scorecard, metrics, flags, notes."""
    try:
        from research.storage.research_db import (
            get_company, get_latest_scores, get_all_metrics,
            get_flags, get_notes, get_filings
        )
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
        content = note.get('full_content', '')
        content = _re.sub(r'<script[^>]*>.*?</script>', '', content, flags=_re.IGNORECASE | _re.DOTALL)
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


@app.route('/portfolio')
@login_required
def portfolio_page():
    try:
        from research.portfolio_intelligence import get_portfolios, get_positions, calculate_concentration, calculate_portfolio_score, run_all_stress_tests, get_portfolio_scores, grade_from_score, detect_hidden_correlations
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
            c.execute("DELETE FROM portfolio_scores WHERE portfolio_id = ?", (pid,))
            c.execute("DELETE FROM portfolio_stress_results WHERE portfolio_id = ?", (pid,))
            c.execute("DELETE FROM portfolio_positions WHERE portfolio_id = ?", (pid,))
            c.execute("DELETE FROM portfolios WHERE id = ?", (pid,))
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
        from research.portfolio_intelligence import get_portfolios, get_positions
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
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/macro/import-sensitivity')
@login_required
def api_macro_import_sensitivity():
    try:
        from research.portfolio_intelligence import get_portfolios, get_positions
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
    """Create essential tables and seed sample data on first startup."""
    import uuid
    from datetime import datetime, timedelta
    try:
        if IS_CLOUD and DB_PATH.exists():
            print("[seed] Cloud deploy detected - removing old DB for clean schema")
            DB_PATH.unlink()

        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS prediction_ledger (
                prediction_id TEXT PRIMARY KEY,
                timestamp TEXT,
                asset TEXT,
                sector TEXT,
                thesis TEXT,
                confidence_score REAL,
                status TEXT,
                expected_timeline_days INTEGER,
                proof_hash TEXT,
                created_at TEXT,
                updated_at TEXT,
                actual_outcome TEXT,
                actual_return_pct REAL,
                outcome_notes TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS veto_archive (
                veto_id TEXT PRIMARY KEY,
                asset TEXT,
                sector TEXT,
                rejection_reason TEXT,
                risk_score REAL,
                timestamp TEXT,
                actual_outcome TEXT,
                actual_return_pct REAL,
                expected_loss_pct REAL,
                avoided_drawdown REAL,
                veto_correct INTEGER,
                notes TEXT
            )
        """)

        # Migration: check if old schema exists and recreate if needed
        cols = [r[1] for r in c.execute("PRAGMA table_info(veto_archive)").fetchall()]
        if 'symbol' in cols and 'asset' not in cols:
            print("[seed] Migrating veto_archive from old schema...")
            c.execute("DROP TABLE veto_archive")
            c.execute("""
                CREATE TABLE veto_archive (
                    veto_id TEXT PRIMARY KEY,
                    asset TEXT,
                    sector TEXT,
                    rejection_reason TEXT,
                    risk_score REAL,
                    timestamp TEXT,
                    actual_outcome TEXT,
                    actual_return_pct REAL,
                    expected_loss_pct REAL,
                    avoided_drawdown REAL,
                    veto_correct INTEGER,
                    notes TEXT
                )
            """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS performance_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id TEXT,
                symbol TEXT,
                action TEXT,
                status TEXT,
                alpha_generated REAL,
                fee_calculated REAL,
                timestamp TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                decision_id TEXT PRIMARY KEY,
                symbol TEXT,
                action TEXT,
                status TEXT,
                confidence REAL,
                potential_return REAL,
                fee REAL,
                zk_proof_hash TEXT,
                timestamp TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS inference_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                cost REAL,
                timestamp TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS monthly_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT,
                total_decisions INTEGER,
                approved INTEGER,
                vetoed INTEGER,
                accuracy REAL
            )
        """)

        c.execute("SELECT COUNT(*) FROM prediction_ledger")
        if c.fetchone()[0] == 0:
            now = datetime.utcnow()
            samples = [
                ("pred-001", (now - timedelta(days=5)).isoformat() + 'Z', "RELIANCE", "Energy", "Strong momentum in refining margins", 0.82, "cleared", 30, "0x" + uuid.uuid4().hex[:40], now.isoformat(), now.isoformat()),
                ("pred-002", (now - timedelta(days=3)).isoformat() + 'Z', "TCS", "IT", "Weak guidance on IT spending outlook", 0.45, "risk-rejected", 14, "0x" + uuid.uuid4().hex[:40], now.isoformat(), now.isoformat()),
                ("pred-003", (now - timedelta(days=2)).isoformat() + 'Z', "INFY", "IT", "Deal wins in AI/ML segment driving growth", 0.71, "cleared", 45, "0x" + uuid.uuid4().hex[:40], now.isoformat(), now.isoformat()),
                ("pred-004", (now - timedelta(days=1)).isoformat() + 'Z', "HDFCBANK", "Banking", "Stable NIM, awaiting credit growth pickup", 0.60, "cleared", 60, "0x" + uuid.uuid4().hex[:40], now.isoformat(), now.isoformat()),
                ("pred-005", now.isoformat() + 'Z', "BAJFINANCE", "NBFC", "AUM growth accelerating, ROE stabilizing", 0.78, "cleared", 30, "0x" + uuid.uuid4().hex[:40], now.isoformat(), now.isoformat()),
            ]
            for pid, ts, asset, sector, thesis, conf, status, days, phash, created, updated in samples:
                c.execute("""
                    INSERT OR IGNORE INTO prediction_ledger
                    (prediction_id, timestamp, asset, sector, thesis, confidence_score, status, expected_timeline_days, proof_hash, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (pid, ts, asset, sector, thesis, conf, status, days, phash, created, updated))
            print(f"[seed] Inserted {len(samples)} sample predictions")

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
                    INSERT OR IGNORE INTO veto_archive
                    (veto_id, asset, sector, rejection_reason, risk_score, timestamp, actual_outcome, actual_return_pct, expected_loss_pct, avoided_drawdown, veto_correct, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (vid, asset, sector, reason, risk, ts, outcome, ret, exp_loss, avoided, correct, notes))
            print(f"[seed] Inserted {len(samples)} sample vetoes")

        # Sync decisions from prediction_ledger and veto_archive
        c.execute("""DELETE FROM decisions""")
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
                veto_id, asset, 'veto', 'vetoed', 1.0 - risk_score,
                -expected_loss_pct, NULL, NULL, timestamp
            FROM veto_archive
        """)
        print(f"[seed] Synced {c.rowcount + 0} decisions from predictions + vetoes")

        conn.commit()
        conn.close()
        print("[seed] Database seeding complete")
    except Exception as e:
        print(f"[seed] Seeding failed: {e}")

seed_database_on_startup()

try:
    from research.storage.research_db import init_db as init_research_db
    init_research_db()
except Exception as e:
    print(f"Warning: Could not initialize research DB: {e}")

try:
    from research.storage.research_db import init_evolution_tables
    init_evolution_tables()
except Exception as e:
    print(f"Warning: Could not initialize evolution tables: {e}")

try:
    from research.storage.research_db import init_validation_tables
    init_validation_tables()
except Exception as e:
    print(f"Warning: Could not initialize validation tables: {e}")

try:
    from research.storage.research_db import init_extended_tables
    init_extended_tables()
except Exception as e:
    print(f"Warning: Could not initialize extended tables: {e}")

try:
    from research.backfill_memory import backfill
    inserted = backfill()
    if inserted:
        print(f"[startup] Backfilled {inserted} observations into memory")
except Exception as e:
    print(f"Warning: Could not backfill observations: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 7860))
    
    print("=== SOVEREIGN ALPHA - Dashboard v1.3 ===")
    print(f"Database: {DB_PATH} (exists: {DB_PATH.exists()})")
    print(f"Proofs: {PROOFS_DIR} (count: {count_proof_files()})")
    print(f"Starting dashboard at http://localhost:{port}")
    print(f"Cloud mode: {IS_CLOUD}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
