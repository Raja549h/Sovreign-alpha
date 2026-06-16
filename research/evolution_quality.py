"""
Research Evolution Engine — Phases 1,3,4,5,6,7,8
==================================================
Implements post-research autopsy, reasoning audit,
failure analysis, edge discovery, confidence calibration,
memo evolution, and CIO challenge mode.
"""

import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

BASE_DIR = Path(__file__).parent.parent
BILLING_DIR = BASE_DIR / "billing"
RESEARCH_DB = BILLING_DIR / "research.db"

AUTOPSY_DIMENSIONS = [
    'signal_strength', 'novelty_score', 'actionability_score',
    'falsifiability_score', 'relevance_score',
]

FAILURE_CATEGORIES = [
    'incorrect_assumption', 'missing_variable', 'wrong_causal_chain',
    'timing_error', 'regime_shift', 'data_interpretation_error',
]

CONTRIBUTING_FACTORS = [
    'structural_analysis', 'capital_allocation', 'accounting_anomaly',
    'valuation_insight', 'macro_alignment', 'management_credibility',
    'competitive_positioning', 'regulatory_catalyst',
]


def _get_db():
    conn = sqlite3.connect(str(RESEARCH_DB))
    conn.row_factory = sqlite3.Row
    return conn


class AutopsyEngine:
    """Phase 1: Score every observation on 5 quality dimensions."""

    def score_observation(self, observation_id: int, scores: Dict[str, float], notes: str = "") -> int:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT company_id FROM observation_memory WHERE id = ?", (observation_id,))
            row = c.fetchone()
            if not row:
                raise ValueError(f"Observation {observation_id} not found")
            company_id = row['company_id']

            signal = min(max(float(scores.get('signal_strength', 0.5)), 0.0), 1.0)
            novelty = min(max(float(scores.get('novelty_score', 0.5)), 0.0), 1.0)
            actionability = min(max(float(scores.get('actionability_score', 0.5)), 0.0), 1.0)
            falsifiability = min(max(float(scores.get('falsifiability_score', 0.5)), 0.0), 1.0)
            relevance = min(max(float(scores.get('relevance_score', 0.5)), 0.0), 1.0)
            rqs = round((signal * 0.30 + novelty * 0.15 + actionability * 0.20 + falsifiability * 0.15 + relevance * 0.20), 4)

            c.execute("""
                INSERT INTO observation_autopsy
                (observation_id, company_id, signal_strength, novelty_score,
                 actionability_score, falsifiability_score, relevance_score,
                 research_quality_score, autopsy_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (observation_id, company_id, signal, novelty, actionability,
                  falsifiability, relevance, rqs, notes))
            conn.commit()
            return c.lastrowid

    def get_autopsy(self, observation_id: int) -> Optional[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM observation_autopsy WHERE observation_id = ? ORDER BY id DESC LIMIT 1", (observation_id,))
            row = c.fetchone()
            return dict(row) if row else None

    def get_all_autopsies(self, company_id: int = None, limit: int = 50) -> List[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            if company_id:
                c.execute("""SELECT oa.*, om.observation_text, om.category, om.validation_status, c.ticker
                             FROM observation_autopsy oa
                             JOIN observation_memory om ON om.id = oa.observation_id
                             JOIN companies c ON c.id = oa.company_id
                             WHERE oa.company_id = ?
                             ORDER BY oa.performed_at DESC LIMIT ?""", (company_id, limit))
            else:
                c.execute("""SELECT oa.*, om.observation_text, om.category, om.validation_status, c.ticker
                             FROM observation_autopsy oa
                             JOIN observation_memory om ON om.id = oa.observation_id
                             JOIN companies c ON c.id = oa.company_id
                             ORDER BY oa.performed_at DESC LIMIT ?""", (limit,))
            return [dict(r) for r in c.fetchall()]

    def get_quality_summary(self) -> Dict:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT COUNT(*) as total,
                       AVG(signal_strength) as avg_signal,
                       AVG(novelty_score) as avg_novelty,
                       AVG(actionability_score) as avg_actionability,
                       AVG(falsifiability_score) as avg_falsifiability,
                       AVG(relevance_score) as avg_relevance,
                       AVG(research_quality_score) as avg_rqs
                FROM observation_autopsy
            """)
            stats = dict(c.fetchone())
            return {
                'total_autopsied': stats.get('total', 0),
                'avg_signal_strength': round(stats.get('avg_signal') or 0, 4),
                'avg_novelty': round(stats.get('avg_novelty') or 0, 4),
                'avg_actionability': round(stats.get('avg_actionability') or 0, 4),
                'avg_falsifiability': round(stats.get('avg_falsifiability') or 0, 4),
                'avg_relevance': round(stats.get('avg_relevance') or 0, 4),
                'avg_research_quality_score': round(stats.get('avg_rqs') or 0, 4),
            }


class ReasoningAudit:
    """Phase 3: Record contributing factors for confirmed observations."""

    def record_factors(self, validation_id: int, factors: List[str],
                       primary_factor: str = None, weight: float = None,
                       notes: str = "") -> int:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT ov.observation_id, ov.company_id, ov.accuracy_contribution
                         FROM observation_validations ov WHERE ov.id = ?""", (validation_id,))
            row = c.fetchone()
            if not row:
                raise ValueError(f"Validation {validation_id} not found")

            factor_str = json.dumps(factors)
            primary = primary_factor or (factors[0] if factors else 'unknown')
            weight = weight or 0.5

            c.execute("""
                INSERT INTO reasoning_audit
                (observation_id, company_id, validation_id, contributing_factors,
                 primary_factor, factor_weight, confidence_at_time, auditor_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (row['observation_id'], row['company_id'], validation_id,
                  factor_str, primary, weight,
                  row['accuracy_contribution'] or 0.5, notes))
            conn.commit()
            return c.lastrowid

    def get_factors(self, observation_id: int) -> List[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT ra.*, ov.new_status, ov.validation_method
                         FROM reasoning_audit ra
                         JOIN observation_validations ov ON ov.id = ra.validation_id
                         WHERE ra.observation_id = ?
                         ORDER BY ra.audited_at DESC""", (observation_id,))
            return [dict(r) for r in c.fetchall()]


class FailureAnalysis:
    """Phase 4: Structured lessons from invalidated observations."""

    def record_failure(self, observation_id: int, category: str,
                       root_cause: str = "", missed_signals: str = "",
                       incorrect_assumption: str = "", lessons: str = "",
                       severity: str = "medium") -> int:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT company_id, confidence FROM observation_memory WHERE id = ?""", (observation_id,))
            row = c.fetchone()
            if not row:
                raise ValueError(f"Observation {observation_id} not found")
            company_id = row['company_id']
            confidence_prior = row['confidence'] or 0.5

            c.execute("""
                INSERT INTO failure_analysis
                (observation_id, company_id, invalidated_at, failure_category,
                 root_cause, missed_signals, incorrect_assumption, lessons_learned,
                 confidence_prior, confidence_posterior, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (observation_id, company_id, datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                  category, root_cause, missed_signals, incorrect_assumption, lessons,
                  confidence_prior, 0.0, severity))
            conn.commit()
            return c.lastrowid

    def get_failures(self, company_id: int = None, limit: int = 50) -> List[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            if company_id:
                c.execute("""SELECT fa.*, om.observation_text, om.category, c.ticker
                             FROM failure_analysis fa
                             JOIN observation_memory om ON om.id = fa.observation_id
                             JOIN companies c ON c.id = fa.company_id
                             WHERE fa.company_id = ?
                             ORDER BY fa.analyzed_at DESC LIMIT ?""", (company_id, limit))
            else:
                c.execute("""SELECT fa.*, om.observation_text, om.category, c.ticker
                             FROM failure_analysis fa
                             JOIN observation_memory om ON om.id = fa.observation_id
                             JOIN companies c ON c.id = fa.company_id
                             ORDER BY fa.analyzed_at DESC LIMIT ?""", (limit,))
            return [dict(r) for r in c.fetchall()]

    def get_pattern_summary(self) -> Dict:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT failure_category, COUNT(*) as cnt
                         FROM failure_analysis GROUP BY failure_category
                         ORDER BY cnt DESC""")
            categories = {r['failure_category']: r['cnt'] for r in c.fetchall()}
            c.execute("""SELECT COUNT(*) as total FROM failure_analysis""")
            total = c.fetchone()['total']
            return {
                'total_failures': total,
                'by_category': categories,
            }


class EdgeDiscovery:
    """Phase 5: Rank frameworks/sectors/metrics by predictive value."""

    def update_framework(self, framework: str, metric: str, category: str,
                         confirmed: bool) -> None:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT id, total_observations, confirmed_count, invalidated_count
                         FROM edge_discovery_framework
                         WHERE framework_name = ? AND metric_name = ? AND category = ?""",
                      (framework, metric, category))
            row = c.fetchone()

            if row:
                fid = row['id']
                total = row['total_observations'] + 1
                confirmed_c = row['confirmed_count'] + (1 if confirmed else 0)
                invalidated_c = row['invalidated_count'] + (0 if confirmed else 1)
            else:
                fid = None
                total = 1
                confirmed_c = 1 if confirmed else 0
                invalidated_c = 0 if confirmed else 1

            accuracy = round(confirmed_c / (confirmed_c + invalidated_c), 4) if (confirmed_c + invalidated_c) > 0 else 0

            if row:
                c.execute("""
                    UPDATE edge_discovery_framework SET
                    total_observations = ?, confirmed_count = ?, invalidated_count = ?,
                    accuracy_rate = ?, last_updated = ?
                    WHERE id = ?
                """, (total, confirmed_c, invalidated_c, accuracy,
                      datetime.now(timezone.utc).strftime('%Y-%m-%d'), fid))
            else:
                c.execute("""
                    INSERT INTO edge_discovery_framework
                    (framework_name, metric_name, category, total_observations,
                     confirmed_count, invalidated_count, accuracy_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (framework, metric, category, total,
                      confirmed_c, invalidated_c, accuracy))
            conn.commit()

    def get_rankings(self, min_observations: int = 2) -> Dict:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT * FROM edge_discovery_framework
                         WHERE total_observations >= ?
                         ORDER BY accuracy_rate DESC""", (min_observations,))
            rows = [dict(r) for r in c.fetchall()]

            c.execute("""SELECT COUNT(*) as total FROM edge_discovery_framework
                         WHERE total_observations >= ?""", (min_observations,))
            total_frameworks = c.fetchone()['total']

            c.execute("""SELECT category, COUNT(*) as cnt, AVG(accuracy_rate) as avg_acc
                         FROM edge_discovery_framework
                         WHERE total_observations >= ?
                         GROUP BY category ORDER BY avg_acc DESC""", (min_observations,))
            by_category = [dict(r) for r in c.fetchall()]

            return {
                'total_frameworks': total_frameworks,
                'rankings': rows,
                'by_category': by_category,
            }


class ConfidenceCalibrator:
    """Phase 6: Track predicted vs actual, adjust future confidence."""

    def record_outcome(self, observation_id: int, actual_outcome: float) -> Dict:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT confidence, validation_status, category
                         FROM observation_memory WHERE id = ?""", (observation_id,))
            row = c.fetchone()
            if not row:
                raise ValueError(f"Observation {observation_id} not found")
            predicted = row['confidence'] or 0.5
            company_id = c.execute("SELECT company_id FROM observation_memory WHERE id = ?",
                                   (observation_id,)).fetchone()['company_id']

            error = actual_outcome - predicted
            bucket = self._calibration_bucket(predicted)

            adjusted = predicted + (error * 0.15)
            adjusted = min(max(adjusted, 0.05), 0.95)

            c.execute("""
                INSERT INTO confidence_calibration
                (observation_id, company_id, predicted_confidence, actual_outcome,
                 confidence_error, calibration_bucket, adjusted_confidence, calibration_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (observation_id, company_id, predicted, actual_outcome,
                  round(error, 4), bucket, round(adjusted, 4),
                  datetime.now(timezone.utc).strftime('%Y-%m-%d')))
            conn.commit()

            return {
                'observation_id': observation_id,
                'predicted': predicted,
                'actual': actual_outcome,
                'error': round(error, 4),
                'bucket': bucket,
                'adjusted_confidence': round(adjusted, 4),
            }

    def get_calibration_summary(self) -> Dict:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT calibration_bucket, COUNT(*) as cnt,
                       AVG(ABS(confidence_error)) as avg_abs_error
                FROM confidence_calibration
                GROUP BY calibration_bucket
                ORDER BY calibration_bucket
            """)
            by_bucket = [dict(r) for r in c.fetchall()]

            c.execute("""
                SELECT COUNT(*) as total, AVG(ABS(confidence_error)) as mae
                FROM confidence_calibration
            """)
            summary = dict(c.fetchone())
            return {
                'total_calibrated': summary.get('total', 0),
                'mean_absolute_error': round(summary.get('mae') or 0, 4),
                'by_bucket': by_bucket,
            }

    def _calibration_bucket(self, confidence: float) -> str:
        if confidence < 0.3: return 'very_low'
        if confidence < 0.5: return 'low'
        if confidence < 0.7: return 'medium'
        if confidence < 0.9: return 'high'
        return 'very_high'


class ChallengeEngine:
    """Phase 8: Bull/bear/counterargument attack before publishing."""

    def create_challenge(self, observation_id: int, bull_case: str,
                         bear_case: str, counterargument: str,
                         challenger_type: str = 'cio') -> Dict:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT company_id, observation_text, confidence
                         FROM observation_memory WHERE id = ?""", (observation_id,))
            row = c.fetchone()
            if not row:
                raise ValueError(f"Observation {observation_id} not found")

            c.execute("""
                INSERT INTO challenge_records
                (observation_id, company_id, challenger_type, bull_case,
                 bear_case, counterargument, challenge_outcome, passed_challenge)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (observation_id, row['company_id'], challenger_type,
                  bull_case, bear_case, counterargument, 'pending', 0))
            conn.commit()
            challenge_id = c.lastrowid

            return {
                'challenge_id': challenge_id,
                'observation_id': observation_id,
                'bull_case': bull_case,
                'bear_case': bear_case,
                'counterargument': counterargument,
                'observation_text': row['observation_text'],
            }

    def resolve_challenge(self, challenge_id: int, passed: bool,
                          outcome: str = "") -> None:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE challenge_records
                SET passed_challenge = ?, challenge_outcome = ?,
                    observation_survived = ?
                WHERE id = ?
            """, (1 if passed else 0, outcome, 1 if passed else 0, challenge_id))
            conn.commit()

    def get_challenges(self, observation_id: int = None, limit: int = 20) -> List[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            if observation_id:
                c.execute("""SELECT cr.*, om.observation_text, om.category, c.ticker
                             FROM challenge_records cr
                             JOIN observation_memory om ON om.id = cr.observation_id
                             JOIN companies c ON c.id = cr.company_id
                             WHERE cr.observation_id = ?
                             ORDER BY cr.challenged_at DESC""", (observation_id,))
            else:
                c.execute("""SELECT cr.*, om.observation_text, om.category, c.ticker
                             FROM challenge_records cr
                             JOIN observation_memory om ON om.id = cr.observation_id
                             JOIN companies c ON c.id = cr.company_id
                             ORDER BY cr.challenged_at DESC LIMIT ?""", (limit,))
            return [dict(r) for r in c.fetchall()]

    def get_challenge_stats(self) -> Dict:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT COUNT(*) as total FROM challenge_records""")
            total = c.fetchone()['total']
            c.execute("""SELECT COUNT(*) as passed FROM challenge_records WHERE passed_challenge = 1""")
            passed = c.fetchone()['passed']
            c.execute("""SELECT COUNT(*) as survived FROM challenge_records WHERE observation_survived = 1""")
            survived = c.fetchone()['survived']
            return {
                'total_challenges': total,
                'passed': passed,
                'observation_survived': survived,
                'pass_rate': round(passed / total * 100, 1) if total > 0 else 0,
            }


class ResearchQualityAggregator:
    """Aggregates all evolution phases into unified quality metrics."""

    def __init__(self):
        self.autopsy = AutopsyEngine()
        self.calibrator = ConfidenceCalibrator()
        self.discovery = EdgeDiscovery()

    def get_unified_quality(self) -> Dict:
        quality = self.autopsy.get_quality_summary()
        calibration = self.calibrator.get_calibration_summary()
        rankings = self.discovery.get_rankings(min_observations=1)

        total_autopsied = quality.get('total_autopsied', 0)
        avg_rqs = quality.get('avg_research_quality_score', 0)
        mae = calibration.get('mean_absolute_error', 0)

        if total_autopsied >= 10:
            coverage_score = min(total_autopsied / 50, 1.0)
        elif total_autopsied >= 5:
            coverage_score = 0.5
        elif total_autopsied >= 1:
            coverage_score = 0.2
        else:
            coverage_score = 0

        quality_score = round(
            (avg_rqs * 0.40) +
            ((1.0 - mae) * 0.30) +
            (coverage_score * 0.15) +
            (min(len(rankings.get('rankings', [])) / 10, 1.0) * 0.15),
            4
        )

        return {
            'overall_quality_score': quality_score,
            'avg_research_quality': avg_rqs,
            'calibration_mae': mae,
            'autopsy_coverage': coverage_score,
            'frameworks_tracked': rankings.get('total_frameworks', 0),
            'autopsy': quality,
            'calibration': calibration,
            'edge_rankings': rankings,
        }
