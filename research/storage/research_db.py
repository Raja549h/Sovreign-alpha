"""
Research Database Schema and Operations
========================================
Extends the existing SQLite database with research-specific tables.
Does NOT touch existing tables.
"""

import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

BASE_DIR = Path(__file__).parent.parent.parent
BILLING_DIR = BASE_DIR / "billing"
RESEARCH_DB = BILLING_DIR / "research.db"

TABLES_SQL = """
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    company_name TEXT NOT NULL,
    exchange TEXT DEFAULT 'NSE',
    sector TEXT,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, exchange)
);

CREATE TABLE IF NOT EXISTS filings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    filing_type TEXT,
    period TEXT,
    source_url TEXT,
    local_path TEXT,
    extracted_text TEXT,
    extracted_tables TEXT,
    ingested_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS financial_series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    metric_name TEXT,
    period TEXT,
    value REAL,
    unit TEXT,
    source_filing_id INTEGER REFERENCES filings(id),
    extracted_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS forensic_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    flag_type TEXT,
    severity TEXT,
    description TEXT,
    supporting_data TEXT,
    period TEXT,
    detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
    analyst_note TEXT
);

CREATE TABLE IF NOT EXISTS research_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    note_reference TEXT UNIQUE,
    title TEXT,
    summary TEXT,
    full_content TEXT,
    risk_intensity_score REAL,
    confidence_score REAL,
    regime_sensitivity_score REAL,
    structural_quality_score REAL,
    forensic_flags_count INTEGER,
    generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    pdf_path TEXT,
    status TEXT DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS institutional_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    period TEXT,
    risk_intensity REAL,
    confidence REAL,
    regime_sensitivity REAL,
    structural_quality REAL,
    composite_score REAL,
    scoring_rationale TEXT,
    scored_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


FII_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS fii_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    flow_type TEXT NOT NULL,
    category TEXT NOT NULL,
    amount_cr REAL,
    source TEXT DEFAULT 'external',
    notes TEXT DEFAULT '',
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fii_flow_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    daily_net_cr REAL,
    weekly_net_cr REAL,
    monthly_net_cr REAL,
    regime TEXT,
    risk_level TEXT,
    portfolio_vulnerability REAL,
    details TEXT DEFAULT '{}',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def init_fii_tables():
    """Initialize FII flow tracking tables."""
    BILLING_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(RESEARCH_DB)) as conn:
        conn.executescript(FII_TABLES_SQL)


def init_db():
    """Initialize database tables."""
    BILLING_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(RESEARCH_DB)) as conn:
        conn.executescript(TABLES_SQL)
    return RESEARCH_DB


def get_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(str(RESEARCH_DB))
    conn.row_factory = sqlite3.Row
    return conn


def get_company(ticker: str, exchange: str = 'NSE') -> Optional[Dict]:
    """Get company by ticker and exchange."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM companies WHERE ticker = ? AND exchange = ?", (ticker, exchange))
        row = c.fetchone()
        return dict(row) if row else None


def add_company(ticker: str, name: str, exchange: str = 'NSE', sector: str = None) -> int:
    """Add company to database. Returns company id."""
    with get_connection() as conn:
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO companies (ticker, company_name, exchange, sector) VALUES (?, ?, ?, ?)",
                (ticker, name, exchange, sector)
            )
            conn.commit()
            return c.lastrowid
        except sqlite3.IntegrityError:
            c.execute("SELECT id FROM companies WHERE ticker = ? AND exchange = ?", (ticker, exchange))
            return c.fetchone()['id']


def save_filing(company_id: int, filing_type: str, period: str, url: str = None, path: str = None) -> int:
    """Save filing record. Returns filing id."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO filings (company_id, filing_type, period, source_url, local_path) VALUES (?, ?, ?, ?, ?)",
            (company_id, filing_type, period, url, path)
        )
        conn.commit()
        return c.lastrowid


def update_filing(filing_id: int, **kwargs):
    """Update filing record with extracted data."""
    with get_connection() as conn:
        c = conn.cursor()
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['extracted_text', 'extracted_tables', 'status']:
                fields.append(f"{key} = ?")
                values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
        if fields:
            values.append(filing_id)
            c.execute(f"UPDATE filings SET {', '.join(fields)} WHERE id = ?", values)
            conn.commit()


def save_metric(company_id: int, metric: str, period: str, value: float, unit: str, filing_id: int = None):
    """Save financial metric to series."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO financial_series (company_id, metric_name, period, value, unit, source_filing_id) VALUES (?, ?, ?, ?, ?, ?)",
            (company_id, metric, period, value, unit, filing_id)
        )
        conn.commit()


def save_flag(company_id: int, flag_type: str, severity: str, description: str, data: Any = None, period: str = None, analyst_note: str = None):
    """Save forensic flag."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO forensic_flags (company_id, flag_type, severity, description, supporting_data, period, analyst_note) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (company_id, flag_type, severity, description, json.dumps(data) if data else None, period, analyst_note)
        )
        conn.commit()


def save_note(company_id: int, reference: str, title: str, content: str, scores: Dict, summary: str = None) -> int:
    """Save research note. Returns note id."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO research_notes 
               (company_id, note_reference, title, summary, full_content, 
                risk_intensity_score, confidence_score, regime_sensitivity_score, 
                structural_quality_score, forensic_flags_count) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (company_id, reference, title, summary, content,
             scores.get('risk_intensity'), scores.get('confidence'),
             scores.get('regime_sensitivity'), scores.get('structural_quality'),
             scores.get('forensic_flags_count', 0))
        )
        conn.commit()
        return c.lastrowid


def update_note_pdf(note_id: int, pdf_path: str):
    """Update note with PDF path."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE research_notes SET pdf_path = ? WHERE id = ?", (pdf_path, note_id))
        conn.commit()


def save_scores(company_id: int, period: str, scores: Dict, rationale: Dict = None):
    """Save institutional scores."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO institutional_scores 
               (company_id, period, risk_intensity, confidence, regime_sensitivity, 
                structural_quality, composite_score, scoring_rationale) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (company_id, period, scores.get('risk_intensity'), scores.get('confidence'),
             scores.get('regime_sensitivity'), scores.get('structural_quality'),
             scores.get('composite'), json.dumps(rationale) if rationale else None)
        )
        conn.commit()


def get_financial_series(company_id: int, metric: str = None) -> List[Dict]:
    """Get financial series for a company, optionally filtered by metric."""
    with get_connection() as conn:
        c = conn.cursor()
        if metric:
            c.execute("SELECT * FROM financial_series WHERE company_id = ? AND metric_name = ? ORDER BY period", (company_id, metric))
        else:
            c.execute("SELECT * FROM financial_series WHERE company_id = ? ORDER BY metric_name, period", (company_id,))
        return [dict(row) for row in c.fetchall()]


def get_flags(company_id: int) -> List[Dict]:
    """Get all forensic flags for a company."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM forensic_flags WHERE company_id = ? ORDER BY detected_at DESC", (company_id,))
        return [dict(row) for row in c.fetchall()]


def get_latest_scores(company_id: int) -> Optional[Dict]:
    """Get latest institutional scores for a company."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM institutional_scores WHERE company_id = ? ORDER BY scored_at DESC LIMIT 1", (company_id,))
        row = c.fetchone()
        return dict(row) if row else None


EVOLUTION_QUALITY_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS observation_autopsy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER REFERENCES observation_memory(id),
    company_id INTEGER REFERENCES companies(id),
    signal_strength REAL,
    novelty_score REAL,
    actionability_score REAL,
    falsifiability_score REAL,
    relevance_score REAL,
    research_quality_score REAL,
    autopsy_notes TEXT,
    performed_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reasoning_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER REFERENCES observation_memory(id),
    company_id INTEGER REFERENCES companies(id),
    validation_id INTEGER REFERENCES observation_validations(id),
    contributing_factors TEXT,
    primary_factor TEXT,
    factor_weight REAL,
    confidence_at_time REAL,
    auditor_notes TEXT,
    audited_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS failure_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER REFERENCES observation_memory(id),
    company_id INTEGER REFERENCES companies(id),
    invalidated_at TEXT,
    failure_category TEXT,
    root_cause TEXT,
    missed_signals TEXT,
    incorrect_assumption TEXT,
    lessons_learned TEXT,
    confidence_prior REAL,
    confidence_posterior REAL,
    severity TEXT,
    analyzed_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS edge_discovery_framework (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    framework_name TEXT,
    metric_name TEXT,
    category TEXT,
    total_observations INTEGER DEFAULT 0,
    confirmed_count INTEGER DEFAULT 0,
    invalidated_count INTEGER DEFAULT 0,
    accuracy_rate REAL,
    avg_confidence REAL,
    predictive_value REAL,
    rank_score REAL,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS confidence_calibration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER REFERENCES observation_memory(id),
    company_id INTEGER REFERENCES companies(id),
    predicted_confidence REAL,
    actual_outcome REAL,
    confidence_error REAL,
    calibration_bucket TEXT,
    adjusted_confidence REAL,
    calibration_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS challenge_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER REFERENCES observation_memory(id),
    company_id INTEGER REFERENCES companies(id),
    challenger_type TEXT,
    bull_case TEXT,
    bear_case TEXT,
    counterargument TEXT,
    challenge_outcome TEXT,
    passed_challenge INTEGER DEFAULT 0,
    observation_survived INTEGER DEFAULT 1,
    challenged_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memo_evolution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    memo_reference TEXT,
    memo_type TEXT,
    prior_memo_reference TEXT,
    quality_delta REAL,
    new_insights_count INTEGER,
    lessons_applied_count INTEGER,
    lessons_ignored_count INTEGER,
    overall_quality_score REAL,
    generated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def init_evolution_quality_tables():
    """Initialize evolution quality tracking tables."""
    with sqlite3.connect(str(RESEARCH_DB)) as conn:
        conn.executescript(EVOLUTION_QUALITY_TABLES_SQL)


def get_notes(company_id: int = None) -> List[Dict]:
    """Get research notes, optionally filtered by company."""
    with get_connection() as conn:
        c = conn.cursor()
        if company_id:
            c.execute("SELECT * FROM research_notes WHERE company_id = ? ORDER BY generated_at DESC", (company_id,))
        else:
            c.execute("SELECT * FROM research_notes ORDER BY generated_at DESC")
        return [dict(row) for row in c.fetchall()]


def get_all_companies() -> List[Dict]:
    """Get all companies in database."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM companies ORDER BY added_at DESC")
        return [dict(row) for row in c.fetchall()]


def get_filings(company_id: int) -> List[Dict]:
    """Get all filings for a company."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM filings WHERE company_id = ? ORDER BY ingested_at DESC", (company_id,))
        return [dict(row) for row in c.fetchall()]


def get_filings_count(company_id: int) -> int:
    """Get count of filings for a company."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM filings WHERE company_id = ?", (company_id,))
        return c.fetchone()['cnt']


def get_metrics_count(company_id: int) -> int:
    """Get count of metrics for a company."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM financial_series WHERE company_id = ?", (company_id,))
        return c.fetchone()['cnt']


def get_flags_count(company_id: int) -> int:
    """Get count of flags for a company."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM forensic_flags WHERE company_id = ?", (company_id,))
        return c.fetchone()['cnt']


def get_flags_by_severity(company_id: int) -> Dict[str, int]:
    """Get flag counts by severity."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT severity, COUNT(*) as cnt FROM forensic_flags WHERE company_id = ? GROUP BY severity", (company_id,))
        return {row['severity']: row['cnt'] for row in c.fetchall()}


def get_note_by_reference(reference: str) -> Optional[Dict]:
    """Get note by reference number."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM research_notes WHERE note_reference = ?", (reference,))
        row = c.fetchone()
        return dict(row) if row else None


def get_company_by_id(company_id: int) -> Optional[Dict]:
    """Get company by ID."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
        row = c.fetchone()
        return dict(row) if row else None


def get_metric_series(company_id: int, metric: str) -> List[Dict]:
    """Get time series for a specific metric."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT period, value, unit FROM financial_series WHERE company_id = ? AND metric_name = ? ORDER BY period",
            (company_id, metric)
        )
        return [dict(row) for row in c.fetchall()]


def get_all_metrics(company_id: int) -> Dict[str, List[Dict]]:
    """Get all metrics grouped by name."""
    series = get_financial_series(company_id)
    grouped = {}
    for s in series:
        name = s['metric_name']
        if name not in grouped:
            grouped[name] = []
        grouped[name].append({'period': s['period'], 'value': s['value'], 'unit': s['unit']})
    return grouped


def delete_company(company_id: int):
    """Delete company and all related data (cascade)."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM institutional_scores WHERE company_id = ?", (company_id,))
        c.execute("DELETE FROM research_notes WHERE company_id = ?", (company_id,))
        c.execute("DELETE FROM forensic_flags WHERE company_id = ?", (company_id,))
        c.execute("DELETE FROM financial_series WHERE company_id = ?", (company_id,))
        c.execute("DELETE FROM filings WHERE company_id = ?", (company_id,))
        c.execute("DELETE FROM companies WHERE id = ?", (company_id,))
        conn.commit()


EXTENDED_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    strategy TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolio_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER REFERENCES portfolios(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id),
    weight_pct REAL,
    cost_basis REAL,
    notes TEXT DEFAULT '',
    added_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolio_stress_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER REFERENCES portfolios(id) ON DELETE CASCADE,
    scenario TEXT NOT NULL,
    impact_pct REAL,
    impact_value REAL,
    max_position_impact TEXT,
    num_positions_affected INTEGER,
    total_positions INTEGER,
    tested_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolio_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER REFERENCES portfolios(id) ON DELETE CASCADE,
    diversification_score REAL,
    concentration_penalty REAL,
    sector_concentration_penalty REAL,
    correlation_penalty REAL,
    stress_impact_score REAL,
    composite_score REAL,
    scored_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS theses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    title TEXT NOT NULL,
    thesis_text TEXT,
    key_variables TEXT,
    timeframe_days INTEGER DEFAULT 90,
    conviction REAL DEFAULT 0.0,
    status TEXT DEFAULT 'INTACT',
    notes TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS thesis_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thesis_id INTEGER REFERENCES theses(id) ON DELETE CASCADE,
    variable TEXT,
    expected_range TEXT,
    actual_value TEXT,
    flag_severity TEXT,
    notes TEXT DEFAULT '',
    checked_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id) UNIQUE,
    alert_threshold TEXT DEFAULT 'MEDIUM',
    notes TEXT DEFAULT '',
    added_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT,
    company TEXT,
    type TEXT,
    headline TEXT,
    severity TEXT,
    supporting_data TEXT DEFAULT '',
    regime_relevance TEXT DEFAULT '',
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def init_extended_tables():
    """Initialize new extended tables."""
    with sqlite3.connect(str(RESEARCH_DB)) as conn:
        conn.executescript(EXTENDED_TABLES_SQL)


EVOLUTION_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS observation_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    observation_date TEXT,
    category TEXT,
    observation_text TEXT,
    confidence REAL,
    source TEXT,
    metric_name TEXT,
    metric_value REAL,
    direction TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS thesis_evolution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    analysis_date TEXT,
    prior_analysis_date TEXT,
    category TEXT,
    prior_observation TEXT,
    current_observation TEXT,
    evolution_status TEXT,
    magnitude TEXT,
    evidence TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS thesis_scorecard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    scored_at TEXT,
    business_quality TEXT,
    capital_allocation TEXT,
    governance TEXT,
    liquidity TEXT,
    funding_structure TEXT,
    macro_exposure TEXT,
    valuation TEXT,
    overall_direction TEXT,
    scorecard_summary TEXT
);
"""


def init_evolution_tables():
    """Initialize thesis evolution tracking tables."""
    with sqlite3.connect(str(RESEARCH_DB)) as conn:
        conn.executescript(EVOLUTION_TABLES_SQL)


VALIDATION_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS observation_validations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER REFERENCES observation_memory(id),
    company_id INTEGER REFERENCES companies(id),
    validation_date TEXT,
    review_type TEXT,
    prior_status TEXT,
    new_status TEXT,
    validation_method TEXT,
    supporting_data TEXT,
    groq_reasoning TEXT,
    accuracy_contribution REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS edge_scorecard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    calculated_at TEXT,
    total_observations INTEGER,
    confirmed INTEGER,
    partially_confirmed INTEGER,
    invalidated INTEGER,
    active INTEGER,
    monitoring INTEGER,
    accuracy_rate REAL,
    weighted_accuracy REAL,
    avg_confidence REAL,
    top_categories TEXT,
    worst_categories TEXT,
    edge_score REAL
);
"""

VALIDATION_MIGRATIONS = [
    "ALTER TABLE observation_memory ADD COLUMN validation_status TEXT DEFAULT 'ACTIVE'",
    "ALTER TABLE observation_memory ADD COLUMN expected_implication TEXT",
    "ALTER TABLE observation_memory ADD COLUMN review_date_30 TEXT",
    "ALTER TABLE observation_memory ADD COLUMN review_date_90 TEXT",
    "ALTER TABLE observation_memory ADD COLUMN review_date_180 TEXT",
    "ALTER TABLE observation_memory ADD COLUMN validation_evidence TEXT",
    "ALTER TABLE observation_memory ADD COLUMN validated_at TEXT",
    "ALTER TABLE observation_memory ADD COLUMN validated_by TEXT DEFAULT 'auto_engine'",
]


def init_validation_tables():
    """Initialize validation tracking tables and migrate observation_memory."""
    with sqlite3.connect(str(RESEARCH_DB)) as conn:
        conn.executescript(VALIDATION_TABLES_SQL)
        for migration in VALIDATION_MIGRATIONS:
            try:
                conn.execute(migration)
            except sqlite3.OperationalError:
                pass
        conn.commit()
