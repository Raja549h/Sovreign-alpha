"""
Observation Stream
Cross-company forensic intelligence feed with macro-triggered alerts.
"""
import json
from database import get_connection as db_get_connection
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).parent.parent
BILLING_DIR = BASE_DIR / "billing"

def get_connection():
    conn = db_get_connection()
    return conn

def add_observation(ticker: str, company: str, obs_type: str, headline: str, severity: str, supporting_data: str = "", regime_relevance: str = "") -> int:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO observations (ticker, company, type, headline, severity, supporting_data, regime_relevance) VALUES (%s, %s, %s, %s, %s, %s, %s)", (ticker, company, obs_type, headline, severity, supporting_data, regime_relevance))
        conn.commit()
        return c.lastrowid

def get_recent_observations(limit: int = 50, severity: str = None, obs_type: str = None) -> List[Dict]:
    with get_connection() as conn:
        c = conn.cursor()
        query = "SELECT * FROM observations"
        params = []
        where = []
        if severity:
            where.append("severity = %s")
            params.append(severity)
        if obs_type:
            where.append("type = %s")
            params.append(obs_type)
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
        c.execute(query, params)
        return [dict(r) for r in c.fetchall()]

def get_observations_by_ticker(ticker: str, limit: int = 20) -> List[Dict]:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM observations WHERE ticker = %s ORDER BY timestamp DESC LIMIT %s", (ticker, limit))
        return [dict(r) for r in c.fetchall()]

def get_high_severity_count(days: int = 7) -> int:
    with get_connection() as conn:
        c = conn.cursor()
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        c.execute("SELECT COUNT(*) as cnt FROM observations WHERE severity IN ('HIGH','CRITICAL') AND timestamp >= %s", (cutoff,))
        return c.fetchone()["cnt"]

def generate_macro_alerts() -> List[Dict]:
    alerts = []
    try:
        from engine.regime import MarketRegimeEngine
        engine = MarketRegimeEngine()
        latest = engine.get_latest()
        regime = latest.regime if latest else "NEUTRAL"
        if regime == "RISK_OFF":
            alerts.append({"type": "macro", "severity": "HIGH", "headline": "Risk-Off regime detected — tightening conditions across portfolio", "regime": regime})
        if regime == "RISK_ON":
            alerts.append({"type": "macro", "severity": "LOW", "headline": "Risk-On regime — elevated exposure tolerance warranted", "regime": regime})
        try:
            from engine.data_layer import DataLayer
            dl = DataLayer()
            macro = dl.fetch_macro_snapshot()
            vix = getattr(macro, 'vix', 0) or 0
            if vix > 30:
                alerts.append({"type": "volatility", "severity": "HIGH", "headline": f"VIX at {vix:.1f} — volatility stress threshold breached", "regime": regime})
            elif vix > 25:
                alerts.append({"type": "volatility", "severity": "MEDIUM", "headline": f"VIX at {vix:.1f} — elevated volatility warning", "regime": regime})
        except Exception:
            pass
    except Exception:
        pass
    return alerts

def generate_forensic_alerts() -> List[Dict]:
    alerts = []
    try:
        high_flags = get_high_severity_count(7)
        if high_flags >= 3:
            alerts.append({"type": "forensic", "severity": "HIGH", "headline": f"{high_flags} high-severity forensic flags across companies in 7 days"})
        elif high_flags >= 1:
            alerts.append({"type": "forensic", "severity": "MEDIUM", "headline": f"{high_flags} high-severity forensic flags detected"})
    except Exception:
        pass
    return alerts

def build_live_feed(limit: int = 30) -> Dict:
    observations = get_recent_observations(limit)
    macro_alerts = generate_macro_alerts()
    forensic_alerts = generate_forensic_alerts()
    high_count = get_high_severity_count(7)
    return {"observations": observations, "macro_alerts": macro_alerts, "forensic_alerts": forensic_alerts, "high_severity_7d": high_count, "total": len(observations)}

def ingest_flags_as_observations() -> int:
    count = 0
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO observations (ticker, company, type, headline, severity, supporting_data, regime_relevance)
                SELECT c.ticker, c.company_name, 'forensic_flag', f.description, f.severity, f.supporting_data, 'TBD'
                FROM forensic_flags f
                JOIN companies c ON c.id = f.company_id
                WHERE f.detected_at >= datetime('now', '-7 days')
                AND NOT EXISTS (SELECT 1 FROM observations o WHERE o.supporting_data = f.supporting_data AND o.headline = f.description AND o.ticker = c.ticker)
            """)
            conn.commit()
            count = c.rowcount
    except Exception:
        pass
    return count
