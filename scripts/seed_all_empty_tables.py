"""Seed all 15 tables currently empty in research.db."""

import sqlite3, json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).parent.parent
DB = BASE / "billing" / "research.db"
conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT id, ticker, company_name, sector FROM companies")
companies = [dict(r) for r in c.fetchall()]
com = {r['ticker']: r for r in companies}

def ts():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

# ── 1. portfolios ──────────────────────────────────────────────
c.execute("SELECT COUNT(*) FROM portfolios")
if c.fetchone()[0] == 0:
    portfolios = [
        ('Core Equity', 'Long-only concentrated equity portfolio', 'Long-only'),
        ('Alpha Opportunities', 'High-conviction tactical positions', 'Opportunistic'),
        ('Defensive Income', 'Dividend and value-focused allocations', 'Defensive'),
    ]
    for name, desc, strategy in portfolios:
        c.execute("INSERT INTO portfolios (name, description, strategy) VALUES (?, ?, ?)", (name, desc, strategy))
    print(f"Seeded {len(portfolios)} portfolios")

# ── 2. portfolio_positions ──────────────────────────────────
c.execute("SELECT COUNT(*) FROM portfolio_positions")
if c.fetchone()[0] == 0:
    c.execute("SELECT id FROM portfolios")
    pids = [r['id'] for r in c.fetchall()]
    positions = [
        (pids[0], 1, 8.5, 4250.0, 'Core holding, strong momentum'),
        (pids[0], 3, 7.2, 2850.0, 'Energy & telecom conglomerate'),
        (pids[0], 4, 6.8, 3800.0, 'IT services leader'),
        (pids[0], 7, 5.5, 920.0, 'Banking sector anchor'),
        (pids[0], 10, 4.5, 750.0, 'Telecom subscriber growth story'),
        (pids[1], 5, 10.0, 1680.0, 'Alpha: banking recovery play'),
        (pids[1], 6, 9.0, 1450.0, 'Alpha: IT margin expansion'),
        (pids[1], 11, 7.5, 520.0, 'Alpha: consumer staple pivot'),
        (pids[2], 12, 6.0, 320.0, 'Defensive: IT value play'),
        (pids[2], 13, 5.0, 2600.0, 'Defensive: FMCG stable cash flows'),
    ]
    for pid, cid, weight, cost, notes in positions:
        c.execute(
            "INSERT INTO portfolio_positions (portfolio_id, company_id, weight_pct, cost_basis, notes) VALUES (?, ?, ?, ?, ?)",
            (pid, cid, weight, cost, notes))
    print(f"Seeded {len(positions)} portfolio positions")

# ── 3. portfolio_scores ──────────────────────────────────────
c.execute("SELECT COUNT(*) FROM portfolio_scores")
if c.fetchone()[0] == 0:
    c.execute("SELECT id FROM portfolios")
    pids = [r['id'] for r in c.fetchall()]
    scores = [
        (pids[0], 78.5, 5.2, 3.8, 2.1, -4.5, 72.3),
        (pids[1], 65.0, 8.5, 6.2, 4.8, -8.2, 56.8),
        (pids[2], 85.0, 2.5, 1.8, 1.2, -2.8, 82.2),
    ]
    for pid, div, conc, sector_conc, corr, stress, comp in scores:
        c.execute(
            "INSERT INTO portfolio_scores (portfolio_id, diversification_score, concentration_penalty, sector_concentration_penalty, correlation_penalty, stress_impact_score, composite_score) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (pid, div, conc, sector_conc, corr, stress, comp))
    print(f"Seeded {len(scores)} portfolio scores")

# ── 4. portfolio_stress_results ──────────────────────────────
c.execute("SELECT COUNT(*) FROM portfolio_stress_results")
if c.fetchone()[0] == 0:
    c.execute("SELECT id FROM portfolios LIMIT 1")
    pid = c.fetchone()['id']
    scenarios = [
        (pid, 'Market crash -20%', -14.2, -8500000, 'RELIANCE:-18.5%', 8, 10),
        (pid, 'Rate hike +100bps', -6.8, -4100000, 'HDFCBANK:-9.2%', 5, 10),
        (pid, 'Oil price shock +30%', -3.5, -2100000, 'RELIANCE:-7.5%', 4, 10),
        (pid, 'Currency depreciation -5%', -4.2, -2500000, 'INFY:-8.1%', 6, 10),
    ]
    for pid, scenario, impact_pct, impact_val, max_pos, num_aff, total in scenarios:
        c.execute(
            "INSERT INTO portfolio_stress_results (portfolio_id, scenario, impact_pct, impact_value, max_position_impact, num_positions_affected, total_positions) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (pid, scenario, impact_pct, impact_val, max_pos, num_aff, total))
    print(f"Seeded {len(scenarios)} stress scenarios")

# ── 5. shadow_portfolio ──────────────────────────────────────
c.execute("SELECT COUNT(*) FROM shadow_portfolio")
if c.fetchone()[0] == 0:
    trades = [
        ('SP-20260601-RELIANCE', 'RELIANCE', 'Reliance Industries', 'Energy & Telecom', ts(), 2850.0, 1, 'Jio subscriber growth + retail expansion', 'Stock to outperform on digital pivot', 0.82, 'CLOSED', ts(), 3120.0, 9.47, 8.0, 1.47, 'correct', 'Digital pivot exceeding expectations'),
        ('SP-20260602-TCS', 'TCS', 'TCS Ltd', 'IT Services', ts(), 3800.0, 1, 'AI services tailwind', 'AI consulting revenue to drive 15% growth', 0.78, 'OPEN', None, None, None, None, None, None, None),
        ('SP-20260603-HDFCBANK', 'HDFCBANK', 'HDFC Bank', 'Banking', ts(), 1680.0, 1, 'NIM recovery post-merger', 'Bank to regain margin trajectory', 0.75, 'CLOSED', ts(), 1750.0, 4.17, 4.5, -0.33, 'incorrect', 'Margin recovery slower than expected'),
    ]
    for pos_id, ticker, name, sector, entry_date, entry_price, size, thesis, expected, conf, status, exit_date, exit_price, ret_pct, bench_pct, alpha, outcome, lessons in trades:
        c.execute("""INSERT INTO shadow_portfolio
            (position_id, ticker, company_name, sector, entry_date, entry_price, position_size, thesis, expected_outcome, confidence, status, exit_date, exit_price, return_pct, benchmark_return_pct, alpha_pct, outcome, lessons)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pos_id, ticker, name, sector, entry_date, entry_price, size, thesis, expected, conf, status, exit_date, exit_price, ret_pct, bench_pct, alpha, outcome, lessons))
    print(f"Seeded {len(trades)} shadow portfolio trades")

# ── 6. shadow_trades ─────────────────────────────────────────
c.execute("SELECT COUNT(*) FROM shadow_trades")
if c.fetchone()[0] == 0:
    c.execute("SELECT id FROM shadow_portfolio LIMIT 2")
    sp_ids = [r['id'] for r in c.fetchall()]
    st_trades = [
        (sp_ids[0], ts(), 'BUY', 'RELIANCE', 2850.0, 100, 'Fundamental entry on digital pivot thesis'),
        (sp_ids[0], ts(), 'SELL', 'RELIANCE', 3120.0, 100, 'Target achieved on digital monetization'),
        (sp_ids[1] if len(sp_ids) > 1 else sp_ids[0], ts(), 'BUY', 'TCS', 3800.0, 100, 'AI services growth thesis entry'),
        (sp_ids[0] if len(sp_ids) == 1 else sp_ids[1], ts(), 'BUY', 'HDFCBANK', 1680.0, 150, 'NIM recovery thesis entry'),
        (sp_ids[0] if len(sp_ids) == 1 else sp_ids[1], ts(), 'SELL', 'HDFCBANK', 1750.0, 150, 'Exited on slower-than-expected recovery'),
    ]
    for spid, trade_date, trade_type, ticker, price, qty, reason in st_trades:
        c.execute("INSERT INTO shadow_trades (portfolio_id, trade_date, trade_type, ticker, price, quantity, reason) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (spid, trade_date, trade_type, ticker, price, qty, reason))
    print(f"Seeded {len(st_trades)} shadow trades")

# ── 7. theses ────────────────────────────────────────────────
c.execute("SELECT COUNT(*) FROM theses")
if c.fetchone()[0] == 0:
    thesis_data = [
        (1, 'Bajaj Finance — NBFC market share expansion', 'Bajaj Finance continues to gain market share in consumer lending. AUM growth trajectory 25%+ CAGR supported by branch expansion and product diversification.', 'AUM growth rate, NIM %, credit cost', 180, 0.85, 'INTACT', 'Credit quality stable, AUM growth on track'),
        (3, 'Reliance — Digital & Retail monetization', 'Jio 5G subscriber monetization and retail margin expansion drive value unlock. O2C business provides stable cash flows.', 'Jio ARPU, retail revenue growth, GRM', 180, 0.82, 'INTACT', 'Digital services showing strong adoption'),
        (4, 'TCS — AI services leadership', 'TCS well-positioned to capture AI/ML consulting and implementation spend. Strong deal pipeline in cloud and AI.', 'Deal TCV, headcount growth, margin %', 120, 0.78, 'MONITORING', 'AI deal wins materializing but margin pressure'),
        (7, 'ICICI Bank — Digital banking moat', 'ICICI leads in digital banking adoption with superior cost-to-income ratio. Retail franchise strengthening.', 'CASA ratio, NIM, cost-to-income', 180, 0.80, 'INTACT', 'Digital platform metrics improving'),
        (10, 'Bharti Airtel — ARPU expansion cycle', 'Tariff hike cycle and 5G monetization drive ARPU expansion. Enterprise segment showing strong growth.', 'ARPU, 5G subscriber mix, enterprise revenue', 120, 0.76, 'INTACT', 'Recent tariff hike positive for ARPU'),
    ]
    for cid, title, thesis_text, key_vars, timeframe, conviction, status, notes in thesis_data:
        c.execute("INSERT INTO theses (company_id, title, thesis_text, key_variables, timeframe_days, conviction, status, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (cid, title, thesis_text, key_vars, timeframe, conviction, status, notes))
    print(f"Seeded {len(thesis_data)} theses")

# ── 8. thesis_checks ─────────────────────────────────────────
c.execute("SELECT COUNT(*) FROM thesis_checks")
if c.fetchone()[0] == 0:
    c.execute("SELECT id, company_id FROM theses")
    all_theses = [dict(r) for r in c.fetchall()]
    checks = []
    for t in all_theses[:5]:
        checks.extend([
            (t['id'], 'AUM Growth', '22-28%', '25.3%', 'GREEN', 'On track'),
            (t['id'], 'NIM', '4.5-5.0%', '4.8%', 'GREEN', 'Stable'),
            (t['id'], 'Credit Cost', '<1.5%', '1.2%', 'GREEN', 'Better than expected'),
        ])
    for thesis_id, var, expected, actual, severity, notes in checks:
        c.execute("INSERT INTO thesis_checks (thesis_id, variable, expected_range, actual_value, flag_severity, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (thesis_id, var, expected, actual, severity, notes))
    print(f"Seeded {len(checks)} thesis checks")

# ── 9. thesis_evolution ──────────────────────────────────────
c.execute("SELECT COUNT(*) FROM thesis_evolution")
if c.fetchone()[0] == 0:
    evolutions = [
        (3, ts(), '2026-03-01', 'Digital Strategy', 'Jio subscriber base at 460M, retail revenue growing 15%', 'Jio 5G subscriber base 520M, retail EBITDA margin expansion 200bps', 'POSITIVE_EVOLUTION', 'SIGNIFICANT', 'Jio ARPU rising on 5G mix shift'),
        (3, ts(), '2026-03-01', 'O2C Margins', 'GRM at $8.2/bbl, chemical margins stable', 'GRM at $9.5/bbl, chemical margins improving on demand recovery', 'POSITIVE_EVOLUTION', 'MODERATE', 'Global refining margins supportive'),
        (1, ts(), '2026-03-15', 'AUM Growth', 'AUM at Rs.3.2L Cr, growing 24% YoY', 'AUM at Rs.3.6L Cr, growth accelerating to 26% YoY', 'POSITIVE_EVOLUTION', 'MODERATE', 'Branch expansion driving growth'),
        (4, ts(), '2026-02-15', 'AI Pipeline', 'AI deal pipeline at $500M, early stage', 'AI deal pipeline crossed $1.2B, 15 wins in Q1', 'POSITIVE_EVOLUTION', 'SIGNIFICANT', 'Enterprise AI adoption accelerating'),
        (7, ts(), '2026-02-20', 'Digital Banking', 'Digital transactions up 35%, CASA at 42%', 'Digital transactions up 48%, CASA at 45%', 'POSITIVE_EVOLUTION', 'MODERATE', 'Digital first strategy paying off'),
    ]
    for cid, analysis_date, prior_date, category, prior_obs, current_obs, status, magnitude, evidence in evolutions:
        c.execute("""INSERT INTO thesis_evolution
            (company_id, analysis_date, prior_analysis_date, category, prior_observation, current_observation, evolution_status, magnitude, evidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (cid, analysis_date, prior_date, category, prior_obs, current_obs, status, magnitude, evidence))
    print(f"Seeded {len(evolutions)} thesis evolutions")

# ── 10. thesis_scorecard ─────────────────────────────────────
c.execute("SELECT COUNT(*) FROM thesis_scorecard")
if c.fetchone()[0] == 0:
    scorecards = [
        (1, ts(), 'Strong', 'Efficient', 'Good', 'Adequate', 'Stable', 'Moderate', 'Fair', 'Positive', 'Well-managed NBFC with strong growth trajectory and controlled credit costs'),
        (3, ts(), 'Strong', 'Disciplined', 'Good', 'Strong', 'Stable', 'Moderate', 'Attractive', 'Positive', 'Conglomerate with multiple growth engines across digital, retail, and energy'),
        (4, ts(), 'Strong', 'Excellent', 'Very Good', 'Strong', 'Stable', 'Low', 'Fair', 'Stable', 'IT services leader well-positioned for AI-led transformation cycle'),
        (7, ts(), 'Strong', 'Good', 'Very Good', 'Strong', 'Stable', 'Low', 'Attractive', 'Positive', 'Best-in-class banking franchise with digital advantage'),
        (10, ts(), 'Good', 'Disciplined', 'Good', 'Adequate', 'Moderate', 'Low', 'Attractive', 'Positive', 'Telecom sector consolidation beneficiary with ARPU expansion'),
    ]
    for cid, scored_at, bq, ca, gov, liq, fs, me, val, direction, summary in scorecards:
        c.execute("""INSERT INTO thesis_scorecard
            (company_id, scored_at, business_quality, capital_allocation, governance, liquidity, funding_structure, macro_exposure, valuation, overall_direction, scorecard_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (cid, scored_at, bq, ca, gov, liq, fs, me, val, direction, summary))
    print(f"Seeded {len(scorecards)} thesis scorecards")

# ── 11. observations ──────────────────────────────────────────
c.execute("SELECT COUNT(*) FROM observations")
if c.fetchone()[0] == 0:
    obs_data = [
        ('RELIANCE', 'Reliance Industries', 'earnings', 'Q4 EBITDA beat on Jio + Retail strength', 'LOW', '{"ebitda_margin": 18.5}', 'NEUTRAL'),
        ('TCS', 'TCS Ltd', 'deal_win', 'Signed $200M AI transformation deal with global bank', 'HIGH', '{"deal_tcv": 200000000}', 'BULLISH'),
        ('HDFCBANK', 'HDFC Bank', 'regulatory', 'RBI approves board reappointment, clarity on merger roadmap', 'MEDIUM', '{}', 'BULLISH'),
        ('INFY', 'Infosys', 'guidance', 'Revised FY26 revenue guidance to 4.5-6.5% from 3-5%', 'HIGH', '{"guidance_revision": 1.5}', 'BULLISH'),
        ('ICICIBANK', 'ICICI Bank', 'digital', 'Digital transactions cross 1B quarterly for first time', 'MEDIUM', '{"digital_txn_growth": 48}', 'BULLISH'),
        ('BHARTIARTL', 'Bharti Airtel', 'tariff', 'Implemented 15% tariff hike on prepaid plans', 'HIGH', '{"tariff_hike_pct": 15}', 'BULLISH'),
    ]
    for ticker, company, otype, headline, severity, supporting_data, regime_relevance in obs_data:
        c.execute("INSERT INTO observations (ticker, company, type, headline, severity, supporting_data, regime_relevance) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ticker, company, otype, headline, severity, supporting_data, regime_relevance))
    print(f"Seeded {len(obs_data)} observations")

# ── 12. filings ──────────────────────────────────────────────
c.execute("SELECT COUNT(*) FROM filings")
if c.fetchone()[0] == 0:
    filings = [
        (1, 'annual_report', 'FY2025-26', 'https://www.bajajfinance.com/investors', '/data/filings/bajaj_finance_fy25_26.pdf', 'pending'),
        (3, 'quarterly', 'Q4 FY2025-26', 'https://www.ril.com/investors', '/data/filings/reliance_q4_fy25_26.pdf', 'pending'),
        (4, 'annual_report', 'FY2025-26', 'https://www.tcs.com/investors', '/data/filings/tcs_annual_fy25_26.pdf', 'pending'),
        (7, 'quarterly', 'Q4 FY2025-26', 'https://www.icicibank.com/investors', '/data/filings/icici_q4_fy25_26.pdf', 'pending'),
        (10, 'annual_report', 'FY2025-26', 'https://www.airtel.com/investors', '/data/filings/bharti_airtel_annual_fy25_26.pdf', 'pending'),
    ]
    for cid, filing_type, period, source_url, local_path, status in filings:
        c.execute("INSERT INTO filings (company_id, filing_type, period, source_url, local_path, status) VALUES (?, ?, ?, ?, ?, ?)",
            (cid, filing_type, period, source_url, local_path, status))
    print(f"Seeded {len(filings)} filings")

# ── 13. institutional_scores ─────────────────────────────────
c.execute("SELECT COUNT(*) FROM institutional_scores")
if c.fetchone()[0] == 0:
    inst_scores = [
        (1, 'Q1-2026', 3.2, 8.5, 2.8, 7.8, 78.5, 'Strong AUM growth, stable credit costs, well-diversified product mix'),
        (3, 'Q1-2026', 4.5, 8.2, 5.5, 7.0, 72.0, 'Conglomerate discount narrowing on digital monetization, O2C cyclical'),
        (4, 'Q1-2026', 2.8, 7.8, 3.2, 8.5, 80.2, 'IT services leader with strong AI tailwinds, excellent capital allocation'),
        (7, 'Q1-2026', 3.0, 8.0, 3.5, 8.0, 76.5, 'Best-in-class banking franchise, digital leadership, stable margins'),
        (10, 'Q1-2026', 3.5, 7.5, 4.0, 7.2, 70.8, 'Telecom recovery play with tariff hike catalyst, enterprise growth'),
    ]
    for cid, period, risk, conf, regime_sens, struct_qual, comp, rationale in inst_scores:
        c.execute("INSERT INTO institutional_scores (company_id, period, risk_intensity, confidence, regime_sensitivity, structural_quality, composite_score, scoring_rationale) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (cid, period, risk, conf, regime_sens, struct_qual, comp, rationale))
    print(f"Seeded {len(inst_scores)} institutional scores")

# ── 14. edge_discovery_framework ─────────────────────────────
c.execute("SELECT COUNT(*) FROM edge_discovery_framework")
if c.fetchone()[0] == 0:
    frameworks = [
        ('Momentum Edge', 'price_momentum', 'Technical', 15, 10, 2, 0.8333, 0.82, 0.78, 85.0),
        ('Value Composite', 'valuation_metrics', 'Fundamental', 12, 8, 1, 0.8889, 0.79, 0.82, 88.0),
        ('Quality Screener', 'quality_factors', 'Fundamental', 18, 14, 1, 0.9333, 0.85, 0.91, 92.0),
        ('Growth at Reasonable', 'growth_metrics', 'Fundamental', 10, 7, 1, 0.8750, 0.80, 0.76, 82.0),
        ('Sentiment Signal', 'sentiment_analysis', 'Alternative', 8, 5, 2, 0.7143, 0.72, 0.65, 68.0),
    ]
    for name, metric, category, total_obs, confirmed, invalidated, acc_rate, avg_conf, pred_val, rank in frameworks:
        c.execute("""INSERT INTO edge_discovery_framework
            (framework_name, metric_name, category, total_observations, confirmed_count, invalidated_count, accuracy_rate, avg_confidence, predictive_value, rank_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, metric, category, total_obs, confirmed, invalidated, acc_rate, avg_conf, pred_val, rank))
    print(f"Seeded {len(frameworks)} edge discovery frameworks")

# ── 15. watchlist ────────────────────────────────────────────
c.execute("SELECT COUNT(*) FROM watchlist")
if c.fetchone()[0] == 0:
    watchlist_items = [
        (5, 'HIGH', 'HDFC Bank merger integration progress monitoring'),
        (6, 'MEDIUM', 'Infosys guidance revision impact on valuation'),
        (11, 'LOW', 'ITC dematerialization timeline'),
        (12, 'MEDIUM', 'Wipro margin recovery trajectory'),
        (13, 'LOW', 'HUL demand recovery in rural markets'),
    ]
    for cid, threshold, notes in watchlist_items:
        c.execute("INSERT OR IGNORE INTO watchlist (company_id, alert_threshold, notes) VALUES (?, ?, ?)",
            (cid, threshold, notes))
    print(f"Seeded {len(watchlist_items)} watchlist items")

conn.commit()
conn.close()
print("\nAll 15 tables seeded successfully.")
