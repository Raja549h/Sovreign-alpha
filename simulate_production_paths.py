import os
# Force NEON_URL in environment BEFORE importing database
os.environ["NEON_URL"] = "postgresql://neondb_owner:npg_HxbKeITV73Gl@ep-super-art-adot6eyq-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

from dashboard.app import app

def simulate():
    client = app.test_client()
    
    records = []
    print("Simulating production paths...")
    
    # Create 10 Predictions
    from dashboard.app import save_prediction
    for i in range(10):
        print(f"Saving prediction v12_{i}...")
        save_prediction({
            'prediction_id': f'prod_pred_v12_{i}',
            'asset': 'TEST_ASSET',
            'sector': 'Test Sector',
            'thesis': 'Test Thesis',
            'confidence_score': 0.8,
            'status': 'pending'
        })
        records.append(f"Prediction: prod_pred_v12_{i}")
        
    print("Creating observations...")
        
    # Create 10 Observations via ObservationRegistry
    from research.observation_registry import ObservationRegistry
    reg = ObservationRegistry()
    obs_ids = []
    for i in range(10):
        oid = reg.register_observation(
            company_id=1,
            category='Test Category',
            observation_text=f'Test Observation v5 {i}',
            confidence=0.9,
            source='Automated Test',
            expected_implication='Test implication'
        )
        obs_ids.append(oid)
        records.append(f"Observation ID: {oid}")

    print("Running engines...")
    # Create 10 Timelines, 10 Validations via API
    for i, oid in enumerate(obs_ids):
        print(f"Running Autopsy Engine for Obs {oid}...")
        # Autopsy (Validation)
        from research.evolution_quality import AutopsyEngine
        ae = AutopsyEngine()
        aid = ae.score_observation(oid, {
            'signal_strength': 0.9,
            'novelty_score': 0.8,
            'actionability_score': 0.9,
            'falsifiability_score': 0.7,
            'relevance_score': 0.9
        }, notes="Simulated autopsy notes")
        records.append(f"Autopsy ID: {aid} for Obs: {oid}")

        print(f"Running Challenge Engine for Obs {oid}...")
        # Challenge
        from research.evolution_quality import ChallengeEngine
        ce = ChallengeEngine()
        cid = ce.create_challenge(oid, "Simulated Bull", "Simulated Bear", "Counter-evidence simulated", "red_team")
        records.append(f"Challenge ID: {cid} for Obs: {oid}")

        print(f"Running Failure Analysis for Obs {oid}...")
        # Failure Ledger
        from research.evolution_quality import FailureAnalysis
        fa = FailureAnalysis()
        fid = fa.record_failure(oid, "Prediction Failed", "Market condition changed", "Macro shift", 0.9)
        records.append(f"Failure ID: {fid} for Obs: {oid}")

        print(f"Running Calibration for Obs {oid}...")
        # Calibration
        from research.evolution_quality import ConfidenceCalibrator
        cc = ConfidenceCalibrator()
        try:
            cal_id = cc.record_outcome(oid, 1.0)
            records.append(f"Calibration ID: {cal_id} for Obs: {oid}")
        except Exception as e:
            records.append(f"Calibration log failed: {e}")

        print(f"Running Timeline for Obs {oid}...")
        # Timeline
        from research.evolution_quality import EvidenceTimeline
        et = EvidenceTimeline()
        try:
            tid = et.record_event(oid, 1, 'SIMULATED', 'Simulated timeline event', 'Simulated text', 'Simulated test')
            records.append(f"Timeline event added for Obs: {oid}")
        except Exception as e:
            records.append(f"Timeline event log failed: {e}")

        print(f"Running Framework update...")

        # Framework Performance
        from research.evolution_quality import FrameworkPerformance
        fp = FrameworkPerformance()
        try:
            fp.update_performance('sim_framework', 'predictive_accuracy', 0.8, 100)
            records.append(f"Framework Performance logged")
        except Exception as e:
            records.append(f"Framework log failed: {e}")

    with open('TEST_DATA_REPORT.md', 'w') as f:
        f.write("# Test Data Creation Report\n\n")
        for r in records:
            f.write(f"- {r}\n")
    print("Done! Wrote TEST_DATA_REPORT.md")

if __name__ == '__main__':
    simulate()
