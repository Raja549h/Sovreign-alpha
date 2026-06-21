-- Ordered Neon PostgreSQL Schema

-- companies
CREATE TABLE companies (
            id SERIAL PRIMARY KEY,
            ticker TEXT NOT NULL,
            company_name TEXT NOT NULL,
            exchange TEXT DEFAULT 'NSE',
            sector TEXT,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, exchange)
        );

-- observation_memory
CREATE TABLE observation_memory (
    id SERIAL PRIMARY KEY,
    company_id INTEGER ,
    observation_date TEXT,
    category TEXT,
    observation_text TEXT,
    confidence REAL,
    source TEXT,
    metric_name TEXT,
    metric_value REAL,
    direction TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
, validation_status TEXT DEFAULT 'ACTIVE', expected_implication TEXT, review_date_30 TEXT, review_date_90 TEXT, review_date_180 TEXT, validation_evidence TEXT, validated_at TEXT, validated_by TEXT DEFAULT 'auto_engine', model_version TEXT DEFAULT '1.0', agent_version TEXT DEFAULT 'analyst-1.0', data_sources TEXT DEFAULT '[]', filings_used TEXT DEFAULT '[]', calculations_used TEXT DEFAULT '', expected_outcome TEXT DEFAULT '', actual_outcome TEXT DEFAULT '', is_immutable INTEGER DEFAULT 0);

-- filings
CREATE TABLE filings (
            id SERIAL PRIMARY KEY,
            company_id INTEGER ,
            filing_type TEXT,
            period TEXT,
            source_url TEXT,
            local_path TEXT,
            extracted_text TEXT,
            extracted_tables TEXT,
            ingested_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        );

-- portfolios
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    strategy TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- theses
CREATE TABLE theses (
    id SERIAL PRIMARY KEY,
    company_id INTEGER ,
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

-- shadow_portfolio
CREATE TABLE shadow_portfolio (
    id SERIAL PRIMARY KEY,
    position_id TEXT UNIQUE,
    ticker TEXT NOT NULL,
    company_name TEXT,
    sector TEXT,
    entry_date TEXT NOT NULL,
    entry_price REAL,
    position_size INTEGER DEFAULT 1,
    thesis TEXT,
    expected_outcome TEXT,
    confidence REAL,
    benchmark_ticker TEXT DEFAULT 'NIFTY50',
    exit_date TEXT,
    exit_price REAL,
    return_pct REAL,
    benchmark_return_pct REAL,
    alpha_pct REAL,
    status TEXT DEFAULT 'OPEN',
    outcome TEXT,
    lessons TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- observation_validations
CREATE TABLE observation_validations (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER ,
    company_id INTEGER ,
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

-- prediction_ledger
CREATE TABLE prediction_ledger (
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

-- veto_archive
CREATE TABLE "veto_archive" (
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
                veto_correct INTEGER,
                proof_hash TEXT,
                notes TEXT,
                created_at TEXT NOT NULL
            );

-- performance_log
CREATE TABLE performance_log (
                id SERIAL PRIMARY KEY,
                decision_id TEXT,
                symbol TEXT,
                action TEXT,
                status TEXT,
                alpha_generated REAL,
                fee_calculated REAL,
                timestamp TEXT
            );

-- decisions
CREATE TABLE decisions (
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

-- inference_log
CREATE TABLE inference_log (
                id SERIAL PRIMARY KEY,
                model TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                cost REAL,
                timestamp TEXT
            );

-- monthly_summary
CREATE TABLE monthly_summary (
                id SERIAL PRIMARY KEY,
                month TEXT,
                total_decisions INTEGER,
                approved INTEGER,
                vetoed INTEGER,
                accuracy REAL
            );

-- thesis_evolution
CREATE TABLE thesis_evolution (
    id SERIAL PRIMARY KEY,
    company_id INTEGER ,
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

-- thesis_scorecard
CREATE TABLE thesis_scorecard (
    id SERIAL PRIMARY KEY,
    company_id INTEGER ,
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

-- edge_scorecard
CREATE TABLE edge_scorecard (
    id SERIAL PRIMARY KEY,
    company_id INTEGER ,
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

-- financial_series
CREATE TABLE financial_series (
            id SERIAL PRIMARY KEY,
            company_id INTEGER ,
            metric_name TEXT,
            period TEXT,
            value REAL,
            unit TEXT,
            source_filing_id INTEGER ,
            extracted_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

-- forensic_flags
CREATE TABLE forensic_flags (
            id SERIAL PRIMARY KEY,
            company_id INTEGER ,
            flag_type TEXT,
            severity TEXT,
            description TEXT,
            supporting_data TEXT,
            period TEXT,
            detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
            analyst_note TEXT
        );

-- research_notes
CREATE TABLE research_notes (
            id SERIAL PRIMARY KEY,
            company_id INTEGER ,
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

-- institutional_scores
CREATE TABLE institutional_scores (
            id SERIAL PRIMARY KEY,
            company_id INTEGER ,
            period TEXT,
            risk_intensity REAL,
            confidence REAL,
            regime_sensitivity REAL,
            structural_quality REAL,
            composite_score REAL,
            scoring_rationale TEXT,
            scored_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

-- observation_autopsy
CREATE TABLE observation_autopsy (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER ,
    company_id INTEGER ,
    signal_strength REAL,
    novelty_score REAL,
    actionability_score REAL,
    falsifiability_score REAL,
    relevance_score REAL,
    research_quality_score REAL,
    autopsy_notes TEXT,
    performed_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- reasoning_audit
CREATE TABLE reasoning_audit (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER ,
    company_id INTEGER ,
    validation_id INTEGER ,
    contributing_factors TEXT,
    primary_factor TEXT,
    factor_weight REAL,
    confidence_at_time REAL,
    auditor_notes TEXT,
    audited_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- failure_analysis
CREATE TABLE failure_analysis (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER ,
    company_id INTEGER ,
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

-- edge_discovery_framework
CREATE TABLE edge_discovery_framework (
    id SERIAL PRIMARY KEY,
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

-- confidence_calibration
CREATE TABLE confidence_calibration (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER ,
    company_id INTEGER ,
    predicted_confidence REAL,
    actual_outcome REAL,
    confidence_error REAL,
    calibration_bucket TEXT,
    adjusted_confidence REAL,
    calibration_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- challenge_records
CREATE TABLE challenge_records (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER ,
    company_id INTEGER ,
    challenger_type TEXT,
    bull_case TEXT,
    bear_case TEXT,
    counterargument TEXT,
    challenge_outcome TEXT,
    passed_challenge INTEGER DEFAULT 0,
    observation_survived INTEGER DEFAULT 1,
    challenged_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- memo_evolution
CREATE TABLE memo_evolution (
    id SERIAL PRIMARY KEY,
    company_id INTEGER ,
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

-- shadow_trades
CREATE TABLE shadow_trades (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER ,
    trade_date TEXT NOT NULL,
    trade_type TEXT CHECK(trade_type IN ('BUY','SELL')),
    ticker TEXT NOT NULL,
    price REAL,
    quantity INTEGER,
    reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- credibility_evidence
CREATE TABLE credibility_evidence (
    id SERIAL PRIMARY KEY,
    evidence_type TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    source_url TEXT,
    completed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- evidence_timeline
CREATE TABLE evidence_timeline (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER ,
    company_id INTEGER ,
    event_type TEXT NOT NULL,
    event_label TEXT,
    event_detail TEXT,
    old_status TEXT,
    new_status TEXT,
    source TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- framework_performance
CREATE TABLE framework_performance (
    id SERIAL PRIMARY KEY,
    framework_name TEXT NOT NULL,
    category TEXT,
    observation_count INTEGER DEFAULT 0,
    confirmed_count INTEGER DEFAULT 0,
    invalidated_count INTEGER DEFAULT 0,
    confirmation_rate REAL,
    avg_confidence REAL,
    total_alpha_pct REAL,
    last_observation_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- reproducibility_log
CREATE TABLE reproducibility_log (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER ,
    company_id INTEGER ,
    filing_sources TEXT,
    earnings_call_sources TEXT,
    financial_inputs TEXT,
    calculations_used TEXT,
    model_version TEXT,
    agent_version TEXT,
    data_signature TEXT,
    logged_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- portfolio_positions
CREATE TABLE portfolio_positions (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER  ,
    company_id INTEGER ,
    weight_pct REAL,
    cost_basis REAL,
    notes TEXT DEFAULT '',
    added_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- portfolio_stress_results
CREATE TABLE portfolio_stress_results (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER  ,
    scenario TEXT NOT NULL,
    impact_pct REAL,
    impact_value REAL,
    max_position_impact TEXT,
    num_positions_affected INTEGER,
    total_positions INTEGER,
    tested_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- portfolio_scores
CREATE TABLE portfolio_scores (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER  ,
    diversification_score REAL,
    concentration_penalty REAL,
    sector_concentration_penalty REAL,
    correlation_penalty REAL,
    stress_impact_score REAL,
    composite_score REAL,
    scored_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- thesis_checks
CREATE TABLE thesis_checks (
    id SERIAL PRIMARY KEY,
    thesis_id INTEGER  ,
    variable TEXT,
    expected_range TEXT,
    actual_value TEXT,
    flag_severity TEXT,
    notes TEXT DEFAULT '',
    checked_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- watchlist
CREATE TABLE watchlist (
    id SERIAL PRIMARY KEY,
    company_id INTEGER  UNIQUE,
    alert_threshold TEXT DEFAULT 'MEDIUM',
    notes TEXT DEFAULT '',
    added_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- observations
CREATE TABLE observations (
    id SERIAL PRIMARY KEY,
    ticker TEXT,
    company TEXT,
    type TEXT,
    headline TEXT,
    severity TEXT,
    supporting_data TEXT DEFAULT '',
    regime_relevance TEXT DEFAULT '',
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

-- calibration_history
CREATE TABLE calibration_history (
            id SERIAL PRIMARY KEY,
            observation_id INTEGER ,
            predicted_confidence REAL,
            actual_outcome REAL,
            calibration_error REAL,
            calibrated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

-- nsdl_fpi_flows
CREATE TABLE nsdl_fpi_flows (
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

-- fii_flows
CREATE TABLE fii_flows (
    id SERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    flow_type TEXT NOT NULL,
    category TEXT NOT NULL,
    amount_cr REAL,
    source TEXT DEFAULT 'external',
    notes TEXT DEFAULT '',
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- fii_flow_snapshots
CREATE TABLE fii_flow_snapshots (
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

-- multi_source_evidence
CREATE TABLE multi_source_evidence (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER ,
    source_name TEXT,
    source_type TEXT,
    evidence_text TEXT,
    source_url TEXT,
    collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
    relevance_score REAL,
    conflict_status TEXT
);

-- research_quality_metrics
CREATE TABLE research_quality_metrics (
    id SERIAL PRIMARY KEY,
    company_id INTEGER ,
    period TEXT,
    completeness REAL,
    consistency REAL,
    timeliness REAL,
    source_quality REAL,
    composite_quality REAL,
    notes TEXT,
    calculated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- fund_params
CREATE TABLE fund_params (
            id SERIAL PRIMARY KEY,
            param_key TEXT UNIQUE,
            param_value TEXT,
            updated_at TEXT
        );

-- fund_uploads
CREATE TABLE fund_uploads (
            id SERIAL PRIMARY KEY,
            file_type TEXT,
            file_content BYTEA,
            uploaded_at TEXT
        );

-- proofs
CREATE TABLE proofs (
            id SERIAL PRIMARY KEY,
            decision_id TEXT,
            proof_hash TEXT,
            verified INTEGER,
            created_at TEXT
        );

-- performance
CREATE TABLE performance (
            id SERIAL PRIMARY KEY,
            date TEXT,
            portfolio_value REAL,
            benchmark_value REAL,
            alpha REAL
        );

-- analysis_runs
CREATE TABLE IF NOT EXISTS analysis_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker TEXT NOT NULL,
    run_type TEXT DEFAULT 'MANUAL',
    status TEXT NOT NULL DEFAULT 'PENDING',
    progress_pct INTEGER DEFAULT 0,
    current_step TEXT DEFAULT 'Initialized',
    retry_count INTEGER DEFAULT 0,
    heartbeat_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result_data JSONB,
    error_log TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- analysis_run_events
CREATE TABLE IF NOT EXISTS analysis_run_events (
    event_id SERIAL PRIMARY KEY,
    run_id UUID REFERENCES analysis_runs(run_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE observation_memory ADD COLUMN IF NOT EXISTS run_id UUID;
ALTER TABLE research_notes ADD COLUMN IF NOT EXISTS run_id UUID;
ALTER TABLE institutional_scores ADD COLUMN IF NOT EXISTS run_id UUID;
ALTER TABLE observation_autopsy ADD COLUMN IF NOT EXISTS run_id UUID;
ALTER TABLE evidence_timeline ADD COLUMN IF NOT EXISTS run_id UUID;

