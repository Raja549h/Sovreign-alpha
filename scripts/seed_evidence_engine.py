"""
Seed the Evidence & Credibility Engine with sample data.
Populates: observation_validations, confidence_calibration, evidence_timeline,
           failure_analysis, observation_autopsy, reproducibility_log,
           framework_performance, memo_evolution, challenge_records
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dashboard.gateway import get_connection

from research.storage.research_db import get_connection
from research.evolution_quality import (
    AutopsyEngine, FailureAnalysis, EvidenceTimeline, ConfidenceCalibrator,
    ReproducibilityTracker, FrameworkPerformance, MemoEvolutionEngine,
    EdgeDiscovery, ChallengeEngine, AntiVanityFilter, ReasoningAudit
)

conn = get_connection()
conn.row_factory = None  # default

# Get existing observations
c = conn.cursor()
c.execute("""SELECT o.id, o.company_id, o.confidence, o.validation_status,
    o.observation_text, c.ticker
    FROM observation_memory o JOIN companies c ON c.id = o.company_id
    ORDER BY o.id""")
observations = [dict(zip(['id','company_id','confidence','status','text','ticker'], row))
                for row in c.fetchall()]

print(f"Found {len(observations)} observations to process")

# Initialize engines
autopsy = AutopsyEngine()
failures = FailureAnalysis()
timeline = EvidenceTimeline()
calibrator = ConfidenceCalibrator()
repro = ReproducibilityTracker()
fw_perf = FrameworkPerformance()
memos = MemoEvolutionEngine()
edge = EdgeDiscovery()
challenges = ChallengeEngine()
audit_recorder = ReasoningAudit()
filter_ = AntiVanityFilter()

# ── 1. Score each observation (Autopsy) ──
print("\n--- 1. Scoring observations (AutopsyEngine) ---")
for obs in observations:
    scores = {
        'signal_strength': round(obs['confidence'] * 0.9, 2),
        'novelty_score': 0.7,
        'actionability_score': 0.65,
        'falsifiability_score': 0.8,
        'relevance_score': 0.85,
    }
    autopsy_id = autopsy.score_observation(obs['id'], scores, "Auto-seed from audit")
    print(f"  Obs {obs['id']} ({obs['ticker']}): scored -> autopsy_id={autopsy_id}")
    result = autopsy.calculate_evidence_score(obs['id'])
    print(f"    Evidence score: {result.get('evidence_score')} ({result.get('status')})")

# ── 2. Record validations ──
print("\n--- 2. Recording validations ---")
validation_statuses = {
    1: ('CONFIRMED', 'Credit cost trend confirmed by Q2 earnings. NII stable, provisions in line.'),
    2: ('PARTIALLY_CONFIRMED', 'NIM compression partially offset by fee income growth. Still monitoring.'),
    3: ('INVALIDATED', 'Price target missed but thesis direction correct on margin.'),
}

for obs in observations:
    oid = obs['id']
    status, evidence = validation_statuses.get(oid, ('ACTIVE', 'Pending review'))
    c.execute("""INSERT INTO observation_validations
        (observation_id, company_id, review_type, prior_status, new_status,
         validation_method, supporting_data, validation_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
        (oid, obs['company_id'], 'automated_audit', obs['status'], status,
         'evidence_cross_reference', evidence))
    vid = c.lastrowid
    conn.commit()

    # Update observation_memory validation_status
    c.execute("UPDATE observation_memory SET validation_status=%s WHERE id=%s", (status, oid))
    conn.commit()

    # Record reasoning factors
    factors = ['credit_cost_trend', 'earnings_call_analysis', 'regulatory_filing']
    primary = 'credit_cost_trend'
    audit_recorder.record_factors(vid, factors, primary, 0.85,
        f"Validated via {evidence[:40]}...")

    # Timeline: validation event
    timeline.record_event(oid, obs['company_id'], 'validation',
        f"Validation: {status}",
        f"Validation recorded by audit engine. Status: {status}",
        obs['status'], status, source='audit_engine')

    print(f"  Obs {oid} ({obs['ticker']}): {status}")

# ── 3. Record calibration outcomes ──
print("\n--- 3. Recording calibration outcomes ---")
calibration_outcomes = {
    1: 0.78,  # confidence 0.85, actual slightly lower
    2: 0.82,  # confidence 0.75, actual higher
    3: 0.85,  # confidence 0.50, actual much higher (de-risking worked)
}
for obs in observations:
    oid = obs['id']
    actual = calibration_outcomes.get(oid, 0.5)
    try:
        result = calibrator.record_outcome(oid, actual)
        err = result.get('confidence_error')
        err_str = f"{err:.3f}" if err is not None else "N/A"
        print(f"  Obs {oid} ({obs['ticker']}): predicted={obs['confidence']}, actual={actual}, "
              f"error={err_str}, bucket={result.get('calibration_bucket')}")
    except Exception as e:
        print(f"  Obs {oid}: calibration error: {e}")

# ── 4. Record timeline events ──
print("\n--- 4. Recording timeline events ---")
event_types = ['observation_created', 'initial_review', 'evidence_added', 'outcome_recorded', 'status_change']
for obs in observations:
    for etype in event_types:
        timeline.record_event(obs['id'], obs['company_id'], etype,
            f"{etype}: {obs['ticker']}",
            f"Auto-generated timeline event: {etype} for observation {obs['id']}",
            '', obs['status'], source='seed_script')
    print(f"  Obs {obs['id']}: {len(event_types)} events recorded")

# ── 5. Record failure analysis ──
print("\n--- 5. Recording failure analysis ---")
fail_severities = [
    ('medium', 'Signal degradation', 'Missed provisioning trend acceleration',
     'Assumed provisions would normalize', 'Cross-validate with macro credit indicators'),
    ('low', 'Timing mismatch', 'Entry too early on NIM compression thesis',
     'Rate cuts delayed by 2 quarters', 'Add macro rate path to timing models'),
]
for sever, cat, root, assump, lesson in fail_severities:
    fid = failures.record_failure(observations[0]['id'], cat, root, root, assump, lesson, sever)
    print(f"  Failure recorded: id={fid}, category={cat}, severity={sever}")

# ── 6. Log reproducibility ──
print("\n--- 6. Logging reproducibility ---")
for obs in observations:
    repro.log_reproducibility(
        obs['id'], obs['company_id'],
        filing_sources=json.dumps(["10-K FY2025", "10-Q Q1 2026"]),
        earnings_call_sources=json.dumps(["Q4 2025 earnings transcript"]),
        financial_inputs=json.dumps(["credit_cost", "nim", "cof"]),
        calculations_used=json.dumps(["credit_cost_growth", "nim_compression"]),
        model_version="1.0", agent_version="analyst-1.0"
    )
    print(f"  Obs {obs['id']}: reproducibility logged")

# ── 7. Update framework performance ──
print("\n--- 7. Updating framework performance ---")
frameworks = [
    ('credit_analysis', 'CREDIT', 'margin'),
    ('nim_analysis', 'FINANCIAL', 'margin'),
    ('earnings_quality', 'EARNINGS', 'quality'),
]
for fw_name, cat, metric in frameworks:
    for obs in observations:
        confirmed = obs['id'] != 3  # obs 3 is INVALIDATED
        fw_perf.update_performance(fw_name, cat, confirmed, obs['confidence'])
    print(f"  Framework '{fw_name}': updated")

# ── 8. Generate memos ──
print("\n--- 8. Generating research memos ---")
memo = memos.generate_memo(1, "MEMO-001", "evolution", "")
print(f"  Memo generated: {memo.get('memo_reference')}, quality={memo.get('overall_quality_score') or 'pending'}")

# ── 9. Create challenges ──
print("\n--- 9. Creating challenges ---")
for obs in observations:
    try:
        chal = challenges.create_challenge(
            obs['id'],
            "Bull case: Thesis supported by fundamental data",
            "Bear case: Market regime shift invalidates assumptions",
            "Counter: Framework adapts to regime changes",
            "cio"
        )
        chal_id = chal.get('id') or chal.get('challenge_id') or chal.get('lastrowid')
        print(f"  Challenge created for obs {obs['id']}: chal={chal}")
    except Exception as e:
        print(f"  Challenge error for obs {obs['id']}: {e}")
    if obs['id'] == 1:
        try:
            challenges.resolve_challenge(chal_id, True, "passed")
            print(f"    Resolved: passed")
        except Exception as e:
            print(f"    Resolve error: {e}")

# ── 10. Update credibility evidence ──
print("\n--- 10. Recording credibility evidence ---")
c.execute("""INSERT INTO credibility_evidence
    (evidence_type, description, status, source_url)
    VALUES (%s, %s, %s, %s)""",
    ('validation_outcome',
     'Credit cost acceleration observation validated by Q2 earnings and provisions data',
     'confirmed', 'https://example.com/audit/1'))
conn.commit()

conn.close()
print("\nSeed complete! Evidence engine populated.")
