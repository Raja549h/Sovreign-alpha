"""
Sovereign Alpha — Single Source of Truth for All Table DDLs
============================================================
Every table across all databases is defined here and only here.
No other file creates tables; they import from here.

Databases:
  db:   prediction_ledger, veto_archive, decisions, performance_log,
                inference_log, monthly_summary
  db:  companies, filings, financial_series, forensic_flags,
                research_notes, institutional_scores, nsdl_fpi_flows,
                fii_flows, fii_flow_snapshots, edge_scorecard,
                observation_memory, observation_validations
                (+ evolution, validation, quality, shadow_portfolio, evidence)
  db: fund_params, fund_uploads
"""

from pathlib import Path
from typing import Optional
from database import IntegrityError, OperationalError, DatabaseError, get_connection

# ---------------------------------------------------------------------------
# db
# ---------------------------------------------------------------------------

BILLING_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS prediction_ledger (
    id SERIAL PRIMARY KEY,
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
);

CREATE TABLE IF NOT EXISTS veto_archive (
    id SERIAL PRIMARY KEY,
    veto_id TEXT UNIQUE,
    prediction_id TEXT,
    timestamp TEXT NOT NULL,
    asset TEXT NOT NULL,
    sector TEXT,
    rejection_reason TEXT NOT NULL,
    risk_score REAL,
    expected_loss_pct REAL,
    actual_outcome TEXT,
    actual_return_pct REAL,
    avoided_drawdown REAL,
    veto_correct BOOLEAN,
    proof_hash TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);

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
);

CREATE TABLE IF NOT EXISTS performance_log (
    id SERIAL PRIMARY KEY,
    decision_id TEXT,
    symbol TEXT,
    action TEXT,
    trade_action TEXT,
    status TEXT,
    position_value REAL,
    alpha_generated REAL,
    fee_calculated REAL,
    fee_paid REAL,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS inference_log (
    id SERIAL PRIMARY KEY,
    model TEXT,
    agent_id TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    cost REAL,
    cost_estimate REAL,
    latency_ms REAL,
    decision_id TEXT,
    status TEXT,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS monthly_summary (
    id SERIAL PRIMARY KEY,
    month TEXT,
    total_decisions INTEGER,
    approved INTEGER,
    vetoed INTEGER,
    accuracy REAL,
    total_inferences INTEGER,
    total_tokens INTEGER,
    total_cost REAL,
    alpha_generated REAL,
    performance_fee REAL,
    report_generated_at TEXT
);
"""

# ---------------------------------------------------------------------------
# db — core tables
# ---------------------------------------------------------------------------

RESEARCH_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    company_name TEXT NOT NULL,
    exchange TEXT DEFAULT 'NSE',
    sector TEXT,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, exchange)
);

CREATE TABLE IF NOT EXISTS filings (
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    metric_name TEXT,
    period TEXT,
    value REAL,
    unit TEXT,
    source_filing_id INTEGER REFERENCES filings(id),
    extracted_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS forensic_flags (
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
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

CREATE TABLE IF NOT EXISTS nsdl_fpi_flows (
    id SERIAL PRIMARY KEY,
    flow_date TEXT UNIQUE,
    equity_net REAL,
    debt_net REAL,
    total_net REAL,
    equity_buy REAL,
    equity_sell REAL,
    source TEXT,
    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fii_flows (
    id SERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    flow_type TEXT NOT NULL,
    category TEXT NOT NULL,
    amount_cr REAL,
    source TEXT DEFAULT 'external',
    notes TEXT DEFAULT '',
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fii_flow_snapshots (
    id SERIAL PRIMARY KEY,
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

CREATE TABLE IF NOT EXISTS edge_scorecard (
    id SERIAL PRIMARY KEY,
    company_id INTEGER,
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

CREATE TABLE IF NOT EXISTS watchlist (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) UNIQUE,
    alert_threshold TEXT DEFAULT 'MEDIUM',
    notes TEXT DEFAULT '',
    added_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

# ---------------------------------------------------------------------------
# db — observation / validation tables
# ---------------------------------------------------------------------------

OBSERVATION_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS observation_memory (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    observation_date TEXT,
    category TEXT,
    observation_text TEXT,
    confidence REAL,
    source TEXT,
    metric_name TEXT,
    metric_value REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    validation_status TEXT DEFAULT 'ACTIVE',
    expected_implication TEXT,
    review_date_30 TEXT,
    review_date_90 TEXT,
    review_date_180 TEXT,
    validation_evidence TEXT,
    validated_at TEXT,
    validated_by TEXT DEFAULT 'auto_engine',
    model_version TEXT DEFAULT '1.0',
    agent_version TEXT DEFAULT 'analyst-1.0',
    data_sources TEXT DEFAULT '[]',
    filings_used TEXT DEFAULT '[]',
    calculations_used TEXT DEFAULT '',
    expected_outcome TEXT DEFAULT '',
    actual_outcome TEXT DEFAULT '',
    is_immutable INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS observation_validations (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER REFERENCES observation_memory(id),
    company_id INTEGER,
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

CREATE TABLE IF NOT EXISTS evidence_timeline (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER REFERENCES observation_memory(id),
    event_type TEXT,
    event_date TEXT,
    description TEXT,
    source TEXT,
    link TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS multi_source_evidence (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER REFERENCES observation_memory(id),
    source_name TEXT,
    source_type TEXT,
    evidence_text TEXT,
    source_url TEXT,
    collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
    relevance_score REAL,
    conflict_status TEXT
);

CREATE TABLE IF NOT EXISTS framework_performance (
    id SERIAL PRIMARY KEY,
    framework_name TEXT,
    category TEXT,
    accuracy REAL,
    total_predictions INTEGER,
    calibration_data TEXT,
    calculated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reproducibility_log (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER REFERENCES observation_memory(id),
    original_prediction TEXT,
    reproduced_by TEXT,
    reproduced_at TEXT,
    status TEXT,
    result_data TEXT,
    notes TEXT
);
"""

# ---------------------------------------------------------------------------
# db — evolution / quality tables (from evolution_quality.py)
# ---------------------------------------------------------------------------

EVOLUTION_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS observation_autopsy (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER REFERENCES observation_memory(id),
    company_id INTEGER REFERENCES companies(id),
    signal_strength REAL,
    novelty_score REAL,
    actionability_score REAL,
    falsifiability_score REAL,
    relevance_score REAL,
    research_quality_score REAL,
    autopsy_notes TEXT,
    scored_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reasoning_audit (
    id SERIAL PRIMARY KEY,
    validation_id INTEGER,
    validation_method TEXT,
    primary_factor TEXT,
    factor_weight REAL,
    factors_considered TEXT,
    reasoning_quality REAL,
    audit_date TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS failure_analysis (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER REFERENCES observation_memory(id),
    failure_type TEXT,
    severity TEXT,
    root_cause TEXT,
    missed_signals TEXT,
    lessons TEXT,
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS calibration_history (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER REFERENCES observation_memory(id),
    predicted_confidence REAL,
    actual_outcome REAL,
    calibration_error REAL,
    calibrated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS edge_discovery_framework (
    id SERIAL PRIMARY KEY,
    edge_type TEXT,
    category TEXT,
    sub_category TEXT,
    confirmed_count INTEGER DEFAULT 0,
    invalidated_count INTEGER DEFAULT 0,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shadow_portfolio (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    entry_date TEXT,
    entry_price REAL,
    current_price REAL,
    position_type TEXT,
    rationale TEXT,
    confidence_at_entry REAL,
    category TEXT,
    expected_return TEXT,
    actual_return REAL,
    risk_score REAL,
    status TEXT DEFAULT 'open',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    closed_at TEXT
);

CREATE TABLE IF NOT EXISTS credibility_evidence (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER REFERENCES observation_memory(id),
    evidence_type TEXT,
    evidence_text TEXT,
    source TEXT,
    collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
    weight REAL,
    relevance TEXT
);

CREATE TABLE IF NOT EXISTS research_quality_metrics (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    period TEXT,
    completeness REAL,
    consistency REAL,
    timeliness REAL,
    source_quality REAL,
    composite_quality REAL,
    notes TEXT,
    calculated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS confidence_calibration (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER REFERENCES observation_memory(id),
    confidence_bucket TEXT,
    expected_accuracy REAL,
    actual_accuracy REAL,
    bucket_size INTEGER,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

# ---------------------------------------------------------------------------
# db
# ---------------------------------------------------------------------------

FUND_DATA_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS fund_params (
    id SERIAL PRIMARY KEY,
    param_key TEXT UNIQUE,
    param_value TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS fund_uploads (
    id SERIAL PRIMARY KEY,
    file_type TEXT,
    file_content BLOB,
    uploaded_at TEXT
);
"""

# --------------------------------------------------------------------------
# Migration guards — run these after CREATE TABLE IF NOT EXISTS
# They silently skip columns that already exist.
# --------------------------------------------------------------------------

OBSERVATION_MIGRATIONS = [
    "ALTER TABLE observation_memory ADD COLUMN validation_status TEXT DEFAULT 'ACTIVE'",
    "ALTER TABLE observation_memory ADD COLUMN expected_implication TEXT",
    "ALTER TABLE observation_memory ADD COLUMN review_date_30 TEXT",
    "ALTER TABLE observation_memory ADD COLUMN review_date_90 TEXT",
    "ALTER TABLE observation_memory ADD COLUMN review_date_180 TEXT",
    "ALTER TABLE observation_memory ADD COLUMN validation_evidence TEXT",
    "ALTER TABLE observation_memory ADD COLUMN validated_at TEXT",
    "ALTER TABLE observation_memory ADD COLUMN validated_by TEXT DEFAULT 'auto_engine'",
    "ALTER TABLE observation_memory ADD COLUMN model_version TEXT DEFAULT '1.0'",
    "ALTER TABLE observation_memory ADD COLUMN agent_version TEXT DEFAULT 'analyst-1.0'",
    "ALTER TABLE observation_memory ADD COLUMN data_sources TEXT DEFAULT '[]'",
    "ALTER TABLE observation_memory ADD COLUMN filings_used TEXT DEFAULT '[]'",
    "ALTER TABLE observation_memory ADD COLUMN calculations_used TEXT DEFAULT ''",
    "ALTER TABLE observation_memory ADD COLUMN expected_outcome TEXT DEFAULT ''",
    "ALTER TABLE observation_memory ADD COLUMN actual_outcome TEXT DEFAULT ''",
    "ALTER TABLE observation_memory ADD COLUMN is_immutable INTEGER DEFAULT 0",
]


def safe_migrate(conn: any, migrations: list) -> None:
    """Run ALTER TABLE migrations, silently skipping those that fail."""
    for migration in migrations:
        try:
            conn.execute(migration)
        except OperationalError:
            pass


def init_billing_db() -> any:
    """Create/verify db tables."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    conn.executescript(BILLING_TABLES_SQL)
    conn.commit()
    return conn


def init_research_db() -> any:
    """Create/verify db tables + run migrations."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    conn.executescript(RESEARCH_TABLES_SQL)
    conn.executescript(OBSERVATION_TABLES_SQL)
    conn.executescript(EVOLUTION_TABLES_SQL)
    safe_migrate(conn, OBSERVATION_MIGRATIONS)
    conn.commit()
    return conn


def init_fund_data_db() -> any:
    """Create/verify db tables."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    conn.executescript(FUND_DATA_TABLES_SQL)
    conn.commit()
    return conn
