# System Dependency Graph

### Module: `agents/analyst.py`
- **Tables Touched**:
  - `filings`
  - `watchlist`

### Module: `agents/risk_manager.py`
- **Tables Touched**:
  - `veto_archive`

### Module: `audit_check.py`
- **Tables Touched**:
  - `companies`
  - `confidence_calibration`
  - `credibility_evidence`
  - `edge_discovery_framework`
  - `edge_scorecard`
  - `evidence_timeline`
  - `failure_analysis`
  - `filings`
  - `financial_series`
  - `forensic_flags`
  - `framework_performance`
  - `observation_memory`
  - `observation_validations`
  - `observations`
  - `prediction_ledger`
  - `proofs`
  - `reproducibility_log`
  - `research_notes`
  - `shadow_portfolio`
  - `shadow_trades`
  - `veto_archive`

### Module: `automation/email_digest.py`
- **Tables Touched**:
  - `prediction_ledger`
  - `veto_archive`

### Module: `automation/master_daily.py`
- **Tables Touched**:
  - `watchlist`

### Module: `backtesting/backtest_90day.py`
- **Tables Touched**:
  - `decisions`
  - `performance`
  - `portfolios`
  - `prediction_ledger`
  - `veto_archive`

### Module: `backtesting/backtest_engine.py`
- **Tables Touched**:
  - `decisions`
  - `performance`

### Module: `backtesting/reanalyze_buy_metrics.py`
- **Tables Touched**:
  - `performance`
  - `prediction_ledger`
  - `veto_archive`

### Module: `billing/init_meter_db.py`
- **Tables Touched**:
  - `decisions`
  - `performance`
  - `proofs`

### Module: `billing/meter.py`
- **Tables Touched**:
  - `inference_log`
  - `monthly_summary`
  - `performance`
  - `performance_log`

### Module: `blockchain/ledger.py`
- **Tables Touched**:
  - `decisions`

### Module: `build_track_record.py`
- **Tables Touched**:
  - `decisions`

### Module: `crew.py`
- **Tables Touched**:
  - `prediction_ledger`

### Module: `dashboard/app.py`
- **Tables Touched**:
  - `calibration_history`
  - `companies`
  - `confidence_calibration`
  - `credibility_evidence`
  - `decisions`
  - `edge_discovery_framework`
  - `edge_scorecard`
  - `evidence_timeline`
  - `failure_analysis`
  - `fii_flow_snapshots`
  - `fii_flows`
  - `filings`
  - `financial_series`
  - `forensic_flags`
  - `framework_performance`
  - `fund_params`
  - `fund_uploads`
  - `inference_log`
  - `institutional_scores`
  - `monthly_summary`
  - `multi_source_evidence`
  - `nsdl_fpi_flows`
  - `observation_autopsy`
  - `observation_memory`
  - `observation_validations`
  - `observations`
  - `performance`
  - `performance_log`
  - `portfolio_positions`
  - `portfolio_scores`
  - `portfolio_stress_results`
  - `portfolios`
  - `prediction_ledger`
  - `proofs`
  - `reasoning_audit`
  - `reproducibility_log`
  - `research_notes`
  - `research_quality_metrics`
  - `shadow_portfolio`
  - `shadow_trades`
  - `theses`
  - `thesis_checks`
  - `veto_archive`
  - `watchlist`

### Module: `dashboard/schemas.py`
- **Tables Touched**:
  - `calibration_history`
  - `companies`
  - `confidence_calibration`
  - `credibility_evidence`
  - `decisions`
  - `edge_discovery_framework`
  - `edge_scorecard`
  - `evidence_timeline`
  - `failure_analysis`
  - `fii_flow_snapshots`
  - `fii_flows`
  - `filings`
  - `financial_series`
  - `forensic_flags`
  - `framework_performance`
  - `fund_params`
  - `fund_uploads`
  - `inference_log`
  - `institutional_scores`
  - `monthly_summary`
  - `multi_source_evidence`
  - `nsdl_fpi_flows`
  - `observation_autopsy`
  - `observation_memory`
  - `observation_validations`
  - `performance_log`
  - `prediction_ledger`
  - `reasoning_audit`
  - `reproducibility_log`
  - `research_notes`
  - `research_quality_metrics`
  - `shadow_portfolio`
  - `veto_archive`
  - `watchlist`

### Module: `dashboard/seed_db.py`
- **Tables Touched**:
  - `companies`
  - `filings`
  - `financial_series`
  - `forensic_flags`
  - `fund_params`
  - `fund_uploads`
  - `institutional_scores`
  - `observation_memory`
  - `observations`
  - `research_notes`

### Module: `demo/demo_mode.py`
- **Tables Touched**:
  - `performance`
  - `proofs`

### Module: `demo/yc_demo.py`
- **Tables Touched**:
  - `proofs`

### Module: `documents/generate_one_pager.py`
- **Tables Touched**:
  - `decisions`
  - `prediction_ledger`
  - `veto_archive`

### Module: `documents/generate_whitepaper.py`
- **Tables Touched**:
  - `decisions`
  - `portfolios`
  - `prediction_ledger`
  - `veto_archive`

### Module: `engine/data_layer.py`
- **Tables Touched**:
  - `filings`
  - `watchlist`

### Module: `generate_dependency_graph.py`
- **Tables Touched**:
  - `calibration_history`
  - `companies`
  - `confidence_calibration`
  - `credibility_evidence`
  - `decisions`
  - `edge_discovery_framework`
  - `edge_scorecard`
  - `evidence_timeline`
  - `failure_analysis`
  - `fii_flow_snapshots`
  - `fii_flows`
  - `filings`
  - `financial_series`
  - `forensic_flags`
  - `framework_performance`
  - `fund_params`
  - `fund_uploads`
  - `inference_log`
  - `institutional_scores`
  - `monthly_summary`
  - `multi_source_evidence`
  - `nsdl_fpi_flows`
  - `observation_autopsy`
  - `observation_memory`
  - `observation_validations`
  - `observations`
  - `performance`
  - `performance_log`
  - `portfolio_positions`
  - `portfolio_scores`
  - `portfolio_stress_results`
  - `portfolios`
  - `prediction_ledger`
  - `proofs`
  - `reasoning_audit`
  - `reproducibility_log`
  - `research_notes`
  - `research_quality_metrics`
  - `shadow_portfolio`
  - `shadow_trades`
  - `theses`
  - `thesis_checks`
  - `thesis_evolution`
  - `thesis_scorecard`
  - `veto_archive`
  - `watchlist`

### Module: `generate_pitch_report.py`
- **Tables Touched**:
  - `decisions`
  - `performance`
  - `proofs`

### Module: `health_check.py`
- **Tables Touched**:
  - `proofs`

### Module: `health_check_full.py`
- **Tables Touched**:
  - `companies`
  - `filings`
  - `financial_series`
  - `forensic_flags`
  - `institutional_scores`
  - `research_notes`

### Module: `migrate_hf.py`
- **Tables Touched**:
  - `proofs`

### Module: `operations/daily_cycle.py`
- **Tables Touched**:
  - `prediction_ledger`
  - `proofs`
  - `veto_archive`

### Module: `rag/knowledge_base.py`
- **Tables Touched**:
  - `research_notes`

### Module: `research/auto_review_engine.py`
- **Tables Touched**:
  - `observation_memory`
  - `observation_validations`
  - `observations`

### Module: `research/backfill_memory.py`
- **Tables Touched**:
  - `companies`
  - `forensic_flags`
  - `observation_memory`
  - `observations`

### Module: `research/backfill_registry.py`
- **Tables Touched**:
  - `observation_memory`
  - `observations`

### Module: `research/cli.py`
- **Tables Touched**:
  - `filings`

### Module: `research/currency_sensitivity.py`
- **Tables Touched**:
  - `companies`

### Module: `research/deep_note_generator.py`
- **Tables Touched**:
  - `observations`

### Module: `research/deep_research_engine.py`
- **Tables Touched**:
  - `observations`

### Module: `research/engine.py`
- **Tables Touched**:
  - `filings`

### Module: `research/evolution_quality.py`
- **Tables Touched**:
  - `companies`
  - `confidence_calibration`
  - `edge_discovery_framework`
  - `edge_scorecard`
  - `evidence_timeline`
  - `failure_analysis`
  - `financial_series`
  - `framework_performance`
  - `observation_autopsy`
  - `observation_memory`
  - `observation_validations`
  - `observations`
  - `performance`
  - `reasoning_audit`
  - `reproducibility_log`
  - `shadow_trades`
  - `watchlist`

### Module: `research/fii_intelligence.py`
- **Tables Touched**:
  - `companies`
  - `nsdl_fpi_flows`

### Module: `research/ingestion/filing_fetcher.py`
- **Tables Touched**:
  - `filings`

### Module: `research/ingestion/pdf_parser.py`
- **Tables Touched**:
  - `filings`

### Module: `research/ingestion/table_extractor.py`
- **Tables Touched**:
  - `filings`

### Module: `research/intelligence/cross_verifier.py`
- **Tables Touched**:
  - `observations`

### Module: `research/intelligence/forensic_detector.py`
- **Tables Touched**:
  - `observations`

### Module: `research/intelligence/regime_connector.py`
- **Tables Touched**:
  - `fii_flows`

### Module: `research/macro/fii_flow.py`
- **Tables Touched**:
  - `fii_flow_snapshots`
  - `fii_flows`
  - `portfolios`

### Module: `research/macro/import_sensitivity.py`
- **Tables Touched**:
  - `portfolios`

### Module: `research/macro/macro_engine.py`
- **Tables Touched**:
  - `observations`

### Module: `research/observation_registry.py`
- **Tables Touched**:
  - `companies`
  - `edge_scorecard`
  - `observation_memory`
  - `observation_validations`
  - `observations`

### Module: `research/observation_stream.py`
- **Tables Touched**:
  - `companies`
  - `forensic_flags`
  - `observations`

### Module: `research/output/note_generator.py`
- **Tables Touched**:
  - `observations`

### Module: `research/portfolio_intelligence.py`
- **Tables Touched**:
  - `companies`
  - `forensic_flags`
  - `portfolio_positions`
  - `portfolio_scores`
  - `portfolio_stress_results`
  - `portfolios`

### Module: `research/seed_muthoot.py`
- **Tables Touched**:
  - `companies`
  - `filings`
  - `financial_series`
  - `forensic_flags`
  - `research_notes`

### Module: `research/seed_pageind.py`
- **Tables Touched**:
  - `companies`
  - `filings`
  - `financial_series`
  - `forensic_flags`

### Module: `research/storage/research_db.py`
- **Tables Touched**:
  - `calibration_history`
  - `companies`
  - `confidence_calibration`
  - `credibility_evidence`
  - `edge_discovery_framework`
  - `edge_scorecard`
  - `evidence_timeline`
  - `failure_analysis`
  - `fii_flow_snapshots`
  - `fii_flows`
  - `filings`
  - `financial_series`
  - `forensic_flags`
  - `framework_performance`
  - `institutional_scores`
  - `observation_autopsy`
  - `observation_memory`
  - `observation_validations`
  - `observations`
  - `performance`
  - `portfolio_positions`
  - `portfolio_scores`
  - `portfolio_stress_results`
  - `portfolios`
  - `reasoning_audit`
  - `reproducibility_log`
  - `research_notes`
  - `research_quality_metrics`
  - `shadow_portfolio`
  - `shadow_trades`
  - `theses`
  - `thesis_checks`
  - `thesis_evolution`
  - `thesis_scorecard`
  - `watchlist`

### Module: `research/thesis_evolution_engine.py`
- **Tables Touched**:
  - `companies`
  - `observation_memory`
  - `observations`
  - `thesis_evolution`
  - `thesis_scorecard`

### Module: `research/thesis_tracker.py`
- **Tables Touched**:
  - `companies`
  - `forensic_flags`
  - `theses`
  - `thesis_checks`
  - `watchlist`

### Module: `research/web_researcher.py`
- **Tables Touched**:
  - `performance`

### Module: `run_sessions.py`
- **Tables Touched**:
  - `decisions`
  - `performance`

### Module: `scripts/red_team_attack.py`
- **Tables Touched**:
  - `prediction_ledger`
  - `veto_archive`

### Module: `scripts/seed_all_empty_tables.py`
- **Tables Touched**:
  - `companies`
  - `edge_discovery_framework`
  - `filings`
  - `institutional_scores`
  - `observations`
  - `portfolio_positions`
  - `portfolio_scores`
  - `portfolio_stress_results`
  - `portfolios`
  - `research_notes`
  - `shadow_portfolio`
  - `shadow_trades`
  - `theses`
  - `thesis_checks`
  - `thesis_evolution`
  - `thesis_scorecard`
  - `watchlist`

### Module: `scripts/seed_evidence_engine.py`
- **Tables Touched**:
  - `companies`
  - `confidence_calibration`
  - `credibility_evidence`
  - `evidence_timeline`
  - `failure_analysis`
  - `framework_performance`
  - `observation_autopsy`
  - `observation_memory`
  - `observation_validations`
  - `observations`
  - `performance`
  - `reproducibility_log`

### Module: `scripts/verify_db.py`
- **Tables Touched**:
  - `observation_autopsy`
  - `observations`
  - `performance`
  - `performance_log`
  - `prediction_ledger`
  - `veto_archive`

### Module: `security/generate_security_report.py`
- **Tables Touched**:
  - `proofs`

### Module: `test_persistence.py`
- **Tables Touched**:
  - `prediction_ledger`

### Module: `zkml/merkle_chain.py`
- **Tables Touched**:
  - `decisions`
  - `proofs`

### Module: `zkml/proof_generator.py`
- **Tables Touched**:
  - `decisions`
  - `proofs`

### Module: `zkml/trust_engine.py`
- **Tables Touched**:
  - `proofs`

### Module: `zkml/verify_proof.py`
- **Tables Touched**:
  - `proofs`

### Module: `zkml/verify_proof_v2.py`
- **Tables Touched**:
  - `proofs`

