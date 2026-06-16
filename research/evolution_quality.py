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


class EvidenceTimeline:
    """Module 7: Permanent chronological timeline for every observation."""

    def record_event(self, observation_id: int, company_id: int, event_type: str,
                     event_label: str = "", event_detail: str = "",
                     old_status: str = "", new_status: str = "",
                     source: str = "system") -> int:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO evidence_timeline
                (observation_id, company_id, event_type, event_label, event_detail,
                 old_status, new_status, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (observation_id, company_id, event_type, event_label, event_detail,
                  old_status, new_status, source))
            conn.commit()
            return c.lastrowid

    def get_timeline(self, company_id: int = None, observation_id: int = None,
                     event_type: str = None, limit: int = 100) -> List[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            parts = ["SELECT et.*, om.observation_text, c.ticker FROM evidence_timeline et"]
            parts.append("LEFT JOIN observation_memory om ON om.id = et.observation_id")
            parts.append("LEFT JOIN companies c ON c.id = et.company_id")
            where = []
            params = []
            if company_id:
                where.append("et.company_id = ?")
                params.append(company_id)
            if observation_id:
                where.append("et.observation_id = ?")
                params.append(observation_id)
            if event_type:
                where.append("et.event_type = ?")
                params.append(event_type)
            if where:
                parts.append("WHERE " + " AND ".join(where))
            parts.append("ORDER BY et.created_at DESC LIMIT ?")
            params.append(limit)
            c.execute(" ".join(parts), params)
            return [dict(r) for r in c.fetchall()]


class FrameworkPerformance:
    """Module 4: Ranked framework performance by evidence."""

    def update_performance(self, framework_name: str, category: str,
                           confirmed: bool, confidence: float = 0.5) -> None:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT id, observation_count, confirmed_count, invalidated_count
                         FROM framework_performance
                         WHERE framework_name = ? AND category = ?""",
                      (framework_name, category))
            row = c.fetchone()
            if row:
                fid = row['id']
                obs_count = row['observation_count'] + 1
                conf_count = row['confirmed_count'] + (1 if confirmed else 0)
                inv_count = row['invalidated_count'] + (0 if confirmed else 1)
            else:
                fid = None
                obs_count = 1
                conf_count = 1 if confirmed else 0
                inv_count = 0 if confirmed else 1
            conf_rate = round(conf_count / (conf_count + inv_count), 4) if (conf_count + inv_count) > 0 else 0
            if fid:
                c.execute("""UPDATE framework_performance SET observation_count = ?,
                             confirmed_count = ?, invalidated_count = ?,
                             confirmation_rate = ?, last_observation_date = ?
                             WHERE id = ?""",
                          (obs_count, conf_count, inv_count, conf_rate,
                           datetime.now(timezone.utc).strftime('%Y-%m-%d'), fid))
            else:
                c.execute("""INSERT INTO framework_performance
                             (framework_name, category, observation_count, confirmed_count,
                              invalidated_count, confirmation_rate, avg_confidence,
                              last_observation_date)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                          (framework_name, category, obs_count, conf_count, inv_count,
                           conf_rate, confidence, datetime.now(timezone.utc).strftime('%Y-%m-%d')))
            conn.commit()
            self._recalc_alpha(framework_name, category)

    def _recalc_alpha(self, framework: str, category: str) -> None:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT confirmation_rate FROM framework_performance
                         WHERE framework_name = ? AND category = ?""", (framework, category))
            row = c.fetchone()
            if row and row['confirmation_rate']:
                alpha = round((row['confirmation_rate'] - 0.5) * 100, 2)
                c.execute("""UPDATE framework_performance SET total_alpha_pct = ?
                             WHERE framework_name = ? AND category = ?""",
                          (alpha, framework, category))
                conn.commit()

    def get_performance_rankings(self, min_observations: int = 2) -> Dict:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT * FROM framework_performance
                         WHERE observation_count >= ?
                         ORDER BY confirmation_rate DESC""", (min_observations,))
            rows = [dict(r) for r in c.fetchall()]
            c.execute("""SELECT category, COUNT(*) as cnt,
                                AVG(confirmation_rate) as avg_conf_rate,
                                SUM(total_alpha_pct) as total_alpha
                         FROM framework_performance
                         WHERE observation_count >= ?
                         GROUP BY category ORDER BY avg_conf_rate DESC""", (min_observations,))
            by_category = [dict(r) for r in c.fetchall()]
            return {
                'total_frameworks': len(rows),
                'rankings': rows,
                'by_category': by_category,
            }


class ReproducibilityTracker:
    """Module 6: Store model version, agent version, data sources per observation."""

    def log_reproducibility(self, observation_id: int, company_id: int,
                            filing_sources: str = "", earnings_call_sources: str = "",
                            financial_inputs: str = "", calculations_used: str = "",
                            model_version: str = "1.0", agent_version: str = "analyst-1.0") -> int:
        with _get_db() as conn:
            c = conn.cursor()
            import hashlib
            raw = f"{observation_id}|{filing_sources}|{financial_inputs}|{model_version}|{agent_version}"
            data_signature = hashlib.sha256(raw.encode()).hexdigest()[:16]
            c.execute("""UPDATE observation_memory SET model_version = ?, agent_version = ?,
                         data_sources = ?, filings_used = ?, calculations_used = ?
                         WHERE id = ?""",
                      (model_version, agent_version,
                       json.dumps(filing_sources.split(",") if filing_sources else []),
                       json.dumps(earnings_call_sources.split(",") if earnings_call_sources else []),
                       calculations_used, observation_id))
            c.execute("""INSERT INTO reproducibility_log
                         (observation_id, company_id, filing_sources, earnings_call_sources,
                          financial_inputs, calculations_used, model_version, agent_version,
                          data_signature)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (observation_id, company_id, filing_sources, earnings_call_sources,
                       financial_inputs, calculations_used, model_version, agent_version,
                       data_signature))
            conn.commit()
            return c.lastrowid

    def get_reproducibility(self, observation_id: int) -> Optional[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT * FROM reproducibility_log
                         WHERE observation_id = ? ORDER BY logged_at DESC LIMIT 1""",
                      (observation_id,))
            row = c.fetchone()
            return dict(row) if row else None


class MemoEvolutionEngine:
    """Module 5: Research evolution memos that learn from past failures."""

    def generate_memo(self, company_id: int, memo_reference: str,
                      memo_type: str = "evolution",
                      prior_memo_reference: str = "") -> Dict:
        with _get_db() as conn:
            c = conn.cursor()
            failures = c.execute("""SELECT failure_category, root_cause, missed_signals,
                                           incorrect_assumption, lessons_learned
                                    FROM failure_analysis WHERE company_id = ?
                                    ORDER BY analyzed_at DESC LIMIT 5""",
                                 (company_id,)).fetchall()
            lessons_applied = 0
            lessons_ignored = 0
            new_insights = 0
            applied_lessons_list = []
            ignored_lessons_list = []
            for f in failures:
                f = dict(f)
                if f.get('lessons_learned'):
                    lessons_applied += 1
                    applied_lessons_list.append(f['lessons_learned'])
                else:
                    lessons_ignored += 1
                    ignored_lessons_list.append(f.get('failure_category', 'unknown'))
            quality_delta = round((lessons_applied * 0.2) - (lessons_ignored * 0.1), 4)
            c.execute("""INSERT INTO memo_evolution
                         (company_id, memo_reference, memo_type, prior_memo_reference,
                          quality_delta, new_insights_count, lessons_applied_count,
                          lessons_ignored_count, overall_quality_score)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (company_id, memo_reference, memo_type, prior_memo_reference,
                       quality_delta, new_insights, lessons_applied, lessons_ignored,
                       round(0.5 + quality_delta, 4)))
            conn.commit()
            return {
                'memo_reference': memo_reference,
                'company_id': company_id,
                'quality_delta': quality_delta,
                'lessons_applied': lessons_applied,
                'lessons_ignored': lessons_ignored,
                'applied_lessons': applied_lessons_list,
                'ignored_lessons': ignored_lessons_list,
            }

    def get_memos(self, company_id: int = None, limit: int = 20) -> List[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            if company_id:
                c.execute("""SELECT me.*, c.ticker FROM memo_evolution me
                             JOIN companies c ON c.id = me.company_id
                             WHERE me.company_id = ? ORDER BY me.generated_at DESC LIMIT ?""",
                          (company_id, limit))
            else:
                c.execute("""SELECT me.*, c.ticker FROM memo_evolution me
                             JOIN companies c ON c.id = me.company_id
                             ORDER BY me.generated_at DESC LIMIT ?""", (limit,))
            return [dict(r) for r in c.fetchall()]


class AntiVanityFilter:
    """Module 9: Reject unsupported metrics with INSUFFICIENT DATA tag."""

    def audit_metrics(self, min_validations: int = 10) -> Dict:
        with _get_db() as conn:
            c = conn.cursor()
            results = {}
            c.execute("SELECT COUNT(*) as total FROM observation_memory")
            total_obs = c.fetchone()['total']
            c.execute("SELECT COUNT(*) as cnt FROM observation_validations")
            total_validations = c.fetchone()['cnt']
            has_sufficient_validations = total_validations >= min_validations
            results['total_observations'] = total_obs
            results['total_validations'] = total_validations
            results['min_validations_required'] = min_validations
            results['has_sufficient_validations'] = has_sufficient_validations
            c.execute("""SELECT metric_name, COUNT(*) as cnt FROM financial_series
                         GROUP BY metric_name ORDER BY cnt DESC LIMIT 20""")
            metrics = [dict(r) for r in c.fetchall()]
            results['metrics'] = []
            for m in metrics:
                results['metrics'].append({
                    'metric': m['metric_name'],
                    'count': m['cnt'],
                    'status': 'SUFFICIENT' if m['cnt'] >= 3 else 'INSUFFICIENT_DATA',
                })
            c.execute("SELECT COUNT(*) as cnt FROM observation_memory WHERE confidence > 0.8")
            high_conf = c.fetchone()['cnt']
            if not has_sufficient_validations and total_obs > 0:
                results['verdict'] = 'INSUFFICIENT_DATA: Less than {} validated observations. All accuracy/edge metrics are unsubstantiated.'.format(min_validations)
                results['high_confidence_count'] = high_conf
                results['high_conf_flag'] = ('VANITY_FLAG' if high_conf > 0 and not has_sufficient_validations
                                              else 'OK')
            else:
                results['verdict'] = 'SUFFICIENT_DATA: Validation threshold met. Metrics are credible.'
                results['high_confidence_count'] = high_conf
                results['high_conf_flag'] = 'OK'
            return results

    def check_metric(self, metric_name: str, min_data_points: int = 3) -> Dict:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as cnt FROM financial_series WHERE metric_name = ?",
                      (metric_name,))
            cnt = c.fetchone()['cnt']
            return {
                'metric': metric_name,
                'data_points': cnt,
                'status': 'SUFFICIENT' if cnt >= min_data_points else 'INSUFFICIENT_DATA',
                'verdict': '' if cnt >= min_data_points else f'Only {cnt} data points (need {min_data_points}). Do not cite this metric.',
            }


class WeeklyICReport:
    """Module 10: Weekly Investment Committee report generator."""

    def generate_report(self) -> Dict:
        from research.storage.research_db import get_all_companies
        report = {
            'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
            'period': 'Weekly IC Report',
            'sections': {},
        }
        companies = get_all_companies()
        report['sections']['coverage'] = {
            'companies_tracked': len(companies),
            'tickers': [c.get('ticker', '?') for c in companies[:50]],
        }
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as cnt FROM failure_analysis")
            report['sections']['failures'] = {'total_failures': c.fetchone()['cnt']}
            c.execute("SELECT COUNT(*) as cnt FROM observation_memory")
            report['sections']['observations'] = {'total_observations': c.fetchone()['cnt']}
            c.execute("""SELECT failure_category, COUNT(*) as cnt
                         FROM failure_analysis GROUP BY failure_category ORDER BY cnt DESC""")
            report['sections']['failure_patterns'] = [dict(r) for r in c.fetchall()]
            c.execute("""SELECT COUNT(*) as cnt FROM observation_validations
                         WHERE validated_at >= date('now', '-7 days')""")
            report['sections']['weekly_validations'] = {'last_7_days': c.fetchone()['cnt']}
            c.execute("""SELECT COUNT(*) as cnt FROM shadow_trades
                         WHERE closed_at >= date('now', '-7 days')""")
            report['sections']['weekly_trades'] = {'closed_last_7d': c.fetchone()['cnt']}
            reg = ObservationRegistry()
            score = reg.calculate_edge_score()
            report['sections']['edge_scorecard'] = {
                'edge_score': score.get('edge_score'),
                'accuracy_rate': score.get('accuracy_rate'),
                'confirmed': score.get('confirmed', 0),
                'invalidated': score.get('invalidated', 0),
                'total': score.get('total', 0),
            }
            c.execute("""SELECT SUM(CASE WHEN actual_outcome > predicted_confidence THEN 1 ELSE 0 END) as overconfident,
                                COUNT(*) as total_calibrated
                         FROM confidence_calibration""")
            cal = dict(c.fetchone())
            cal['overconfidence_rate'] = round(cal.get('overconfident', 0) / cal.get('total_calibrated', 1), 4)
            report['sections']['calibration'] = cal
            try:
                from research.observation_registry import ObservationRegistry
                observations_module = __import__('research.observation_registry', fromlist=[''])
            except ImportError:
                observations_module = None
            report['recommendations'] = self._generate_recommendations(report['sections'])
        return report

    def _generate_recommendations(self, sections: Dict) -> List[str]:
        recs = []
        failures = sections.get('failures', {}).get('total_failures', 0)
        if failures > 5:
            recs.append("HIGH FAILURE COUNT: Review top failure patterns and adjust research methodology.")
        edge = sections.get('edge_scorecard', {})
        if edge.get('accuracy_rate', 0) and edge['accuracy_rate'] < 0.5:
            recs.append("ACCURACY BELOW 50%: System underperforms random. Reconsider research frameworks.")
        cal = sections.get('calibration', {})
        if cal.get('overconfidence_rate', 0) > 0.3:
            recs.append("OVERCONFIDENCE BIAS: System overconfident >30% of the time. Apply calibration penalty.")
        trades = sections.get('weekly_trades', {}).get('closed_last_7d', 0)
        if trades == 0:
            recs.append("NO TRADES THIS WEEK: Portfolio may be inactive. Consider reviewing watchlist.")
        return recs
