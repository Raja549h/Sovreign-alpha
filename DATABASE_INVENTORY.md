# Database Inventory Report

## `billing.db`
- **File Size**: 52.00 KB
- **Total Tables**: 7

### Table: `prediction_ledger`
- **Row Count**: 5
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**:
  - `sqlite_autoindex_prediction_ledger_1` (Unique: True)

### Table: `veto_archive`
- **Row Count**: 5
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**:
  - `sqlite_autoindex_veto_archive_1` (Unique: True)

### Table: `performance_log`
- **Row Count**: 0
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**: None

### Table: `decisions`
- **Row Count**: 11
- **Primary Key(s)**: decision_id
- **Foreign Keys**: None
- **Indexes**:
  - `sqlite_autoindex_decisions_1` (Unique: True)

### Table: `inference_log`
- **Row Count**: 0
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**: None

### Table: `monthly_summary`
- **Row Count**: 0
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**: None

## `research.db`
- **File Size**: 332.00 KB
- **Total Tables**: 39

### Table: `observation_memory`
- **Row Count**: 6
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
- **Indexes**: None

### Table: `thesis_evolution`
- **Row Count**: 6
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
- **Indexes**: None

### Table: `thesis_scorecard`
- **Row Count**: 5
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
- **Indexes**: None

### Table: `observation_validations`
- **Row Count**: 15
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
  - `observation_id` references `observation_memory(id)`
- **Indexes**: None

### Table: `edge_scorecard`
- **Row Count**: 2
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
- **Indexes**: None

### Table: `companies`
- **Row Count**: 13
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**:
  - `sqlite_autoindex_companies_1` (Unique: True)

### Table: `filings`
- **Row Count**: 5
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
- **Indexes**: None

### Table: `financial_series`
- **Row Count**: 125
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `source_filing_id` references `filings(id)`
  - `company_id` references `companies(id)`
- **Indexes**: None

### Table: `forensic_flags`
- **Row Count**: 15
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
- **Indexes**: None

### Table: `research_notes`
- **Row Count**: 1
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
- **Indexes**:
  - `sqlite_autoindex_research_notes_1` (Unique: True)

### Table: `institutional_scores`
- **Row Count**: 5
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
- **Indexes**: None

### Table: `observation_autopsy`
- **Row Count**: 17
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
  - `observation_id` references `observation_memory(id)`
- **Indexes**: None

### Table: `reasoning_audit`
- **Row Count**: 17
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `validation_id` references `observation_validations(id)`
  - `company_id` references `companies(id)`
  - `observation_id` references `observation_memory(id)`
- **Indexes**: None

### Table: `failure_analysis`
- **Row Count**: 19
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
  - `observation_id` references `observation_memory(id)`
- **Indexes**: None

### Table: `edge_discovery_framework`
- **Row Count**: 13
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**: None

### Table: `confidence_calibration`
- **Row Count**: 20
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
  - `observation_id` references `observation_memory(id)`
- **Indexes**: None

### Table: `challenge_records`
- **Row Count**: 1
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
  - `observation_id` references `observation_memory(id)`
- **Indexes**: None

### Table: `memo_evolution`
- **Row Count**: 2
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
- **Indexes**: None

### Table: `shadow_portfolio`
- **Row Count**: 3
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**:
  - `sqlite_autoindex_shadow_portfolio_1` (Unique: True)

### Table: `shadow_trades`
- **Row Count**: 5
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `portfolio_id` references `shadow_portfolio(id)`
- **Indexes**: None

### Table: `credibility_evidence`
- **Row Count**: 1
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**: None

### Table: `evidence_timeline`
- **Row Count**: 25
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
  - `observation_id` references `observation_memory(id)`
- **Indexes**: None

### Table: `framework_performance`
- **Row Count**: 1
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**: None

### Table: `reproducibility_log`
- **Row Count**: 21
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
  - `observation_id` references `observation_memory(id)`
- **Indexes**: None

### Table: `portfolios`
- **Row Count**: 3
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**: None

### Table: `portfolio_positions`
- **Row Count**: 10
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
  - `portfolio_id` references `portfolios(id)`
- **Indexes**: None

### Table: `portfolio_stress_results`
- **Row Count**: 4
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `portfolio_id` references `portfolios(id)`
- **Indexes**: None

### Table: `portfolio_scores`
- **Row Count**: 3
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `portfolio_id` references `portfolios(id)`
- **Indexes**: None

### Table: `theses`
- **Row Count**: 5
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
- **Indexes**: None

### Table: `thesis_checks`
- **Row Count**: 15
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `thesis_id` references `theses(id)`
- **Indexes**: None

### Table: `watchlist`
- **Row Count**: 5
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
- **Indexes**:
  - `sqlite_autoindex_watchlist_1` (Unique: True)

### Table: `observations`
- **Row Count**: 6
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**: None

### Table: `calibration_history`
- **Row Count**: 0
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `observation_id` references `observation_memory(id)`
- **Indexes**: None

### Table: `nsdl_fpi_flows`
- **Row Count**: 0
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**:
  - `sqlite_autoindex_nsdl_fpi_flows_1` (Unique: True)

### Table: `fii_flows`
- **Row Count**: 0
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**: None

### Table: `fii_flow_snapshots`
- **Row Count**: 0
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**: None

### Table: `multi_source_evidence`
- **Row Count**: 0
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `observation_id` references `observation_memory(id)`
- **Indexes**: None

### Table: `research_quality_metrics`
- **Row Count**: 0
- **Primary Key(s)**: id
- **Foreign Keys**:
  - `company_id` references `companies(id)`
- **Indexes**: None

## `fund_data.db`
- **File Size**: 36.00 KB
- **Total Tables**: 3

### Table: `fund_params`
- **Row Count**: 5
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**:
  - `sqlite_autoindex_fund_params_1` (Unique: True)

### Table: `fund_uploads`
- **Row Count**: 0
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**: None

## `meter.db`
- **File Size**: 20.00 KB
- **Total Tables**: 4

### Table: `decisions`
- **Row Count**: 0
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**: None

### Table: `proofs`
- **Row Count**: 0
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**: None

### Table: `performance`
- **Row Count**: 0
- **Primary Key(s)**: id
- **Foreign Keys**: None
- **Indexes**: None

