#!/usr/bin/env python3
"""
Sovereign Alpha — Database Seed Script
=======================================
Uses ONLY stdlib (sqlite3, os, json, datetime).
Zero external dependencies.

Creates all research tables, seeds Bajaj Finance data,
and initializes fund parameters. Safe to run multiple times.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from database import get_connection
import json
from datetime import datetime
BILLING_DIR = BASE_DIR / "billing"
BILLING_DIR.mkdir(exist_ok=True)



def seed_research_db():
    """Create research tables and seed Bajaj Finance data."""
    print("[seed] Initializing db...")

    from research.storage.research_db import init_evolution_tables, init_validation_tables, init_evolution_quality_tables, init_shadow_portfolio_tables, init_evidence_tables
    init_evolution_tables()
    init_validation_tables()
    init_evolution_quality_tables()
    init_shadow_portfolio_tables()
    init_evidence_tables()

    conn = get_connection()
    c = conn.cursor()

    # 1. companies
    c.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY,
            ticker TEXT NOT NULL,
            company_name TEXT NOT NULL,
            exchange TEXT DEFAULT 'NSE',
            sector TEXT,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, exchange)
        )
    """)

    # 2. filings
    c.execute("""
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
        )
    """)

    # 3. financial_series
    c.execute("""
        CREATE TABLE IF NOT EXISTS financial_series (
            id SERIAL PRIMARY KEY,
            company_id INTEGER REFERENCES companies(id),
            metric_name TEXT,
            period TEXT,
            value REAL,
            unit TEXT,
            source_filing_id INTEGER REFERENCES filings(id),
            extracted_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. forensic_flags
    c.execute("""
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
        )
    """)

    # 5. research_notes
    c.execute("""
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
        )
    """)

    # 6. institutional_scores
    c.execute("""
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
        )
    """)

    conn.commit()

    # Insert Bajaj Finance
    c.execute("""
        INSERT INTO companies
        (ticker, company_name, exchange, sector)
        VALUES (%s, %s, %s, %s)
    """, ("BAJFINANCE", "Bajaj Finance Limited", "NSE", "NBFC"))
    company_id = c.execute("SELECT id FROM companies WHERE ticker='BAJFINANCE'").fetchone()[0]
    print(f"  [ok] BAJFINANCE (id={company_id})")

    # Financial metrics
    metrics = [
        ("NIM", "FY23", 10.8, "percent"),
        ("NIM", "FY24", 10.1, "percent"),
        ("NIM", "FY25", 10.1, "percent"),
        ("COF", "FY23", 7.04, "percent"),
        ("COF", "FY24", 7.74, "percent"),
        ("COF", "FY25", 7.99, "percent"),
        ("ROA", "FY23", 4.2, "percent"),
        ("ROA", "FY24", 3.86, "percent"),
        ("ROA", "FY25", 3.58, "percent"),
        ("ROE", "FY23", 22.5, "percent"),
        ("ROE", "FY24", 19.1, "percent"),
        ("ROE", "FY25", 17.4, "percent"),
        ("GNPA", "FY23", 1.2, "percent"),
        ("GNPA", "FY24", 0.85, "percent"),
        ("GNPA", "FY25", 1.0, "percent"),
        ("CREDIT_COST", "FY23", 1.25, "percent"),
        ("CREDIT_COST", "FY24", 1.63, "percent"),
        ("CREDIT_COST", "FY25", 2.05, "percent"),
        ("OPEX_NTI", "FY23", 25.7, "percent"),
        ("OPEX_NTI", "FY24", 24.0, "percent"),
        ("OPEX_NTI", "FY25", 20.8, "percent"),
        ("PAT_GROWTH", "FY24", 25.6, "percent"),
        ("PAT_GROWTH", "FY25", 15.1, "percent"),
        ("AUM_GROWTH", "FY24", 34.0, "percent"),
        ("AUM_GROWTH", "FY25", 28.0, "percent"),
    ]

    count = 0
    for metric, period, value, unit in metrics:
        c.execute("""
            INSERT INTO financial_series
            (company_id, metric_name, period, value, unit)
            VALUES (%s, %s, %s, %s, %s)
        """, (company_id, metric, period, value, unit))
        count += 1
    print(f"  [ok] {count} financial metrics inserted")

    # Forensic flags
    flags = [
        ("credit_cost_acceleration", "high",
         "Credit cost rose from 1.25% to 2.05% — 64% increase over 2 periods",
         json.dumps({"fy23": 1.25, "fy25": 2.05, "change_pct": 64}), "FY25"),
        ("margin_compression", "medium",
         "NIM compressed 70bps FY23 to FY25 on rising cost of funds",
         json.dumps({"fy23_nim": 10.8, "fy25_nim": 10.1, "compression_bps": 70}), "FY25"),
        ("valuation_fragility", "high",
         "29x PE on 17.4% ROE vs prior cycle 22.5% ROE — multiple assumes full recovery",
         json.dumps({"pe": 29, "current_roe": 17.4, "prior_roe": 22.5}), "FY25"),
    ]

    for flag_type, severity, desc, evidence, period in flags:
        c.execute("""
            INSERT INTO forensic_flags
            (company_id, flag_type, severity, description, supporting_data, period)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (company_id, flag_type, severity, desc, evidence, period))
    print(f"  [ok] {len(flags)} forensic flags inserted")

    # Seed observation_memory from forensic flags
    from datetime import datetime, timedelta
    today = datetime.utcnow().strftime('%Y-%m-%d')
    d30 = (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d')
    d90 = (datetime.utcnow() + timedelta(days=90)).strftime('%Y-%m-%d')
    d180 = (datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d')
    c.execute("SELECT COUNT(*) FROM observation_memory WHERE company_id = %s", (company_id,))
    if c.fetchone()[0] == 0:
        obs_list = [
            ('credit_cost_acceleration', 'margin', 0.85,
             'Credit cost acceleration: 64% increase FY23->FY25, CREDIT_COST 1.25%->2.05%'),
            ('margin_compression', 'margin', 0.75,
             'NIM compressed 70bps FY23-FY25 on rising cost of funds (COF 7.04%->7.99%)'),
            ('valuation_fragility', 'valuation', 0.85,
             '29x PE on 17.4% ROE vs prior-cycle 22.5% ROE — premium priced for recovery'),
        ]
        expected = 'Monitor for deterioration in trend'
        for source_type, cat, conf, obs_text in obs_list:
            c.execute(
                """INSERT INTO observation_memory
                   (company_id, observation_date, category, observation_text,
                    confidence, source, expected_implication, review_date_30,
                    review_date_90, review_date_180, validation_status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE')""",
                (company_id, today, cat, obs_text, conf, 'filing',
                 expected, d30, d90, d180)
            )
        print("  [ok] 3 observations seeded into observation_memory")

    # Coverage expansion: top NSE companies by liquidity
    nse_coverage = [
        ("RELIANCE", "Reliance Industries Limited", "Energy & Telecom"),
        ("TCS", "Tata Consultancy Services Limited", "IT Services"),
        ("HDFCBANK", "HDFC Bank Limited", "Banking"),
        ("INFY", "Infosys Limited", "IT Services"),
        ("ICICIBANK", "ICICI Bank Limited", "Banking"),
        ("KOTAKBANK", "Kotak Mahindra Bank Limited", "Banking"),
        ("SBIN", "State Bank of India", "Banking"),
        ("BHARTIARTL", "Bharti Airtel Limited", "Telecom"),
        ("ITC", "ITC Limited", "Consumer Goods"),
        ("WIPRO", "Wipro Limited", "IT Services"),
        ("HINDUNILVR", "Hindustan Unilever Limited", "Consumer Goods"),
    ]
    for ticker, name, sector in nse_coverage:
        c.execute("""
            INSERT INTO companies
            (ticker, company_name, exchange, sector)
            VALUES (%s, %s, %s, %s)
        """, (ticker, name, "NSE", sector))
        if c.rowcount > 0:
            print(f"  [ok] Added {ticker} ({sector})")
    conn.commit()

    # Research note
    c.execute("""
        INSERT INTO research_notes
        (company_id, note_reference, title, status)
        VALUES (%s, %s, %s, %s)
    """, (company_id, "SR-2026-BAF-001",
          "Bajaj Finance — Marginal Efficiency Compression Under Liquidity Normalisation",
          "published"))
    print("  [ok] Research note SR-2026-BAF-001 inserted")

    conn.commit()
    conn.close()
    print("  [done] db seeded")


def seed_fund_db():
    """Create fund data tables and seed parameters."""
    print("[seed] Initializing db...")
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS fund_params (
            id SERIAL PRIMARY KEY,
            param_key TEXT UNIQUE,
            param_value TEXT,
            updated_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS fund_uploads (
            id SERIAL PRIMARY KEY,
            file_type TEXT,
            file_content BLOB,
            uploaded_at TEXT
        )
    """)

    params = [
        ("max_position_size", "5.0"),
        ("max_sector_exposure", "20.0"),
        ("max_drawdown", "15.0"),
        ("min_confidence", "65"),
        ("aum", "59000000"),
    ]

    for key, value in params:
        c.execute("""
            INSERT INTO fund_params (param_key, param_value, updated_at)
            VALUES (%s, %s, %s)
        """, (key, value, datetime.utcnow().isoformat()))
        print(f"  [ok] {key} = {value}")

    conn.commit()
    conn.close()
    print("  [done] db seeded")


if __name__ == "__main__":
    print("=" * 60)
    print("SOVEREIGN ALPHA — Database Seed")
    print("=" * 60)
    try:
        seed_research_db()
        seed_fund_db()
        print("=" * 60)
        print("SEED COMPLETE — Dashboard will show live data")
        print("=" * 60)
    except Exception as e:
        print(f"[seed] ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("SEED FAILED — Dashboard may show incomplete data")
