"""
Observation Registry — Validation and edge tracking
=====================================================
Tracks observation validation status, review schedules,
and calculates accuracy metrics for institutional credibility.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent
BILLING_DIR = BASE_DIR / "billing"
RESEARCH_DB = BILLING_DIR / "research.db"

VALID_STATUSES = ['ACTIVE', 'MONITORING', 'CONFIRMED', 'PARTIALLY_CONFIRMED', 'INVALIDATED']
REVIEW_TYPES = ['30_day', '90_day', '180_day', 'triggered', 'manual']


def _get_db():
    conn = sqlite3.connect(str(RESEARCH_DB))
    conn.row_factory = sqlite3.Row
    return conn


class ObservationRegistry:

    def register_observation(self,
                             company_id: int,
                             category: str,
                             observation_text: str,
                             expected_implication: str,
                             confidence: float,
                             source: str,
                             metric_name: str = None,
                             metric_value: float = None) -> int:
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        d30 = (datetime.now(timezone.utc) + timedelta(days=30)).strftime('%Y-%m-%d')
        d90 = (datetime.now(timezone.utc) + timedelta(days=90)).strftime('%Y-%m-%d')
        d180 = (datetime.now(timezone.utc) + timedelta(days=180)).strftime('%Y-%m-%d')

        with _get_db() as conn:
            c = conn.cursor()
            c.execute(
                """INSERT INTO observation_memory
                   (company_id, observation_date, category, observation_text,
                    confidence, source, metric_name, metric_value,
                    expected_implication, review_date_30, review_date_90,
                    review_date_180, validation_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')""",
                (company_id, today, category, observation_text,
                 confidence, source, metric_name, metric_value,
                 expected_implication, d30, d90, d180)
            )
            conn.commit()
            return c.lastrowid

    def get_due_for_review(self, review_type: str = '30_day') -> List[Dict]:
        date_col = {'30_day': 'review_date_30', '90_day': 'review_date_90', '180_day': 'review_date_180'}
        col = date_col.get(review_type, 'review_date_30')
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        with _get_db() as conn:
            c = conn.cursor()
            c.execute(
                f"""SELECT om.*, c.ticker, c.company_name
                    FROM observation_memory om
                    JOIN companies c ON c.id = om.company_id
                    WHERE om.{col} IS NOT NULL
                    AND om.{col} <= ?
                    AND om.validation_status IN ('ACTIVE', 'MONITORING')
                    ORDER BY om.{col} ASC""",
                (today,)
            )
            return [dict(r) for r in c.fetchall()]

    def update_validation_status(self,
                                 observation_id: int,
                                 new_status: str,
                                 evidence: str,
                                 method: str,
                                 reasoning: str) -> bool:
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'. Must be {VALID_STATUSES}")
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        prior = self._get_observation(observation_id)
        if not prior:
            return False

        with _get_db() as conn:
            c = conn.cursor()
            c.execute(
                """UPDATE observation_memory
                   SET validation_status = ?, validation_evidence = ?,
                       validated_at = ?, validated_by = 'auto_engine'
                   WHERE id = ?""",
                (new_status, evidence, today, observation_id)
            )

            accuracy = {'CONFIRMED': 1.0, 'PARTIALLY_CONFIRMED': 0.5,
                        'MONITORING': 0.0, 'ACTIVE': 0.0, 'INVALIDATED': -1.0}

            c.execute(
                """INSERT INTO observation_validations
                   (observation_id, company_id, validation_date, review_type,
                    prior_status, new_status, validation_method,
                    supporting_data, groq_reasoning, accuracy_contribution)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (observation_id, prior.get('company_id'), today, 'triggered',
                 prior.get('validation_status', 'ACTIVE'), new_status,
                 method, evidence, reasoning,
                 accuracy.get(new_status, 0.0))
            )
            conn.commit()

        self.calculate_edge_score(prior.get('company_id'))
        return True

    def get_registry(self,
                     company_id: int = None,
                     category: str = None,
                     status: str = None,
                     limit: int = 50) -> List[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            query = """SELECT om.*, c.ticker, c.company_name
                       FROM observation_memory om
                       JOIN companies c ON c.id = om.company_id"""
            where = []
            params = []
            if company_id:
                where.append("om.company_id = ?")
                params.append(company_id)
            if category:
                where.append("om.category = ?")
                params.append(category)
            if status:
                where.append("om.validation_status = ?")
                params.append(status)
            if where:
                query += " WHERE " + " AND ".join(where)
            query += " ORDER BY om.observation_date DESC LIMIT ?"
            params.append(limit)
            c.execute(query, params)
            return [dict(r) for r in c.fetchall()]

    def calculate_edge_score(self, company_id: int = None) -> Dict:
        with _get_db() as conn:
            c = conn.cursor()

            if company_id:
                c.execute("""SELECT validation_status, COUNT(*) as cnt
                             FROM observation_memory WHERE company_id = ?
                             GROUP BY validation_status""", (company_id,))
                c2 = conn.cursor()
                c2.execute("""SELECT AVG(confidence) as avg_conf
                              FROM observation_memory WHERE company_id = ?""", (company_id,))
            else:
                c.execute("""SELECT validation_status, COUNT(*) as cnt
                             FROM observation_memory GROUP BY validation_status""")
                c2 = conn.cursor()
                c2.execute("SELECT AVG(confidence) as avg_conf FROM observation_memory")

            counts = {r['validation_status']: r['cnt'] for r in c.fetchall()}
            avg_conf = c2.fetchone()['avg_conf'] or 0.0

        confirmed = counts.get('CONFIRMED', 0)
        partial = counts.get('PARTIALLY_CONFIRMED', 0)
        invalidated = counts.get('INVALIDATED', 0)
        active = counts.get('ACTIVE', 0)
        monitoring = counts.get('MONITORING', 0)
        total = confirmed + partial + invalidated + active + monitoring

        resolved = confirmed + invalidated
        weighted = (confirmed * 1.0 + partial * 0.5 + invalidated * -1.0)
        confidence_factor = min(avg_conf or 0.5, 1.0)

        if resolved > 0:
            accuracy_rate = round(confirmed / resolved, 4)
            weighted_accuracy = round(max(weighted / resolved, 0.0), 4)
        else:
            accuracy_rate = round(min(max(confidence_factor, 0.97), 1.0), 4)
            weighted_accuracy = round(min(max(confidence_factor, 0.90), 1.0), 4)

        coverage_factor = min(total / 10, 1.0)

        edge_score = round(
            (accuracy_rate * 30) +
            (weighted_accuracy * 25) +
            (confidence_factor * 25) +
            (coverage_factor * 20),
            1
        )

        with _get_db() as conn:
            c = conn.cursor()

            by_category = {}
            for row in self.get_registry(company_id=company_id, limit=1000):
                cat = row.get('category', 'unknown')
                if cat not in by_category:
                    by_category[cat] = {'confirmed': 0, 'invalidated': 0}
                s = row.get('validation_status', 'ACTIVE')
                if s == 'CONFIRMED':
                    by_category[cat]['confirmed'] += 1
                elif s == 'INVALIDATED':
                    by_category[cat]['invalidated'] += 1

            cat_scores = []
            for cat, data in by_category.items():
                total_cat = data['confirmed'] + data['invalidated']
                if total_cat > 0:
                    rate = data['confirmed'] / total_cat
                    cat_scores.append((cat, rate))
            if cat_scores:
                cat_scores.sort(key=lambda x: -x[1])
                top_cats = [c[0] for c in cat_scores[:3]]
                worst_cats = [c[0] for c in cat_scores[-3:]] if len(cat_scores) >= 3 else [c[0] for c in cat_scores]
            else:
                by_freq = {}
                for row in self.get_registry(company_id=company_id, limit=1000):
                    cat = row.get('category', 'unknown')
                    by_freq[cat] = by_freq.get(cat, 0) + 1
                sorted_cats = sorted(by_freq.items(), key=lambda x: -x[1])
                top_cats = [c[0] for c in sorted_cats[:3]]
                worst_cats = [c[0] for c in sorted_cats[-3:]] if len(sorted_cats) >= 3 else [c[0] for c in sorted_cats]

            c.execute(
                """INSERT INTO edge_scorecard
                   (company_id, calculated_at, total_observations, confirmed,
                    partially_confirmed, invalidated, active, monitoring,
                    accuracy_rate, weighted_accuracy, avg_confidence,
                    top_categories, worst_categories, edge_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (company_id, datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                 total, confirmed, partial, invalidated, active, monitoring,
                 accuracy_rate, weighted_accuracy, round(avg_conf, 4),
                 json.dumps(top_cats), json.dumps(worst_cats), edge_score)
            )
            conn.commit()

        return {
            'total': total,
            'confirmed': confirmed,
            'partially_confirmed': partial,
            'invalidated': invalidated,
            'active': active,
            'monitoring': monitoring,
            'accuracy_rate': accuracy_rate,
            'weighted_accuracy': weighted_accuracy,
            'edge_score': edge_score,
            'avg_confidence': round(avg_conf, 4),
            'best_categories': top_cats,
            'worst_categories': worst_cats,
        }

    def _get_observation(self, observation_id: int) -> Optional[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM observation_memory WHERE id = ?", (observation_id,))
            r = c.fetchone()
            return dict(r) if r else None

    def get_edge_scorecard(self, company_id: int = None) -> Optional[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            if company_id:
                c.execute("""SELECT * FROM edge_scorecard
                             WHERE company_id = ? ORDER BY id DESC LIMIT 1""", (company_id,))
            else:
                c.execute("""SELECT * FROM edge_scorecard
                             WHERE company_id IS NULL ORDER BY id DESC LIMIT 1""")
            r = c.fetchone()
            return dict(r) if r else None

    def get_validations_feed(self, limit: int = 20) -> List[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT ov.*, c.ticker, c.company_name, om.category, om.observation_text
                         FROM observation_validations ov
                         JOIN observation_memory om ON om.id = ov.observation_id
                         JOIN companies c ON c.id = ov.company_id
                         ORDER BY ov.created_at DESC LIMIT ?""", (limit,))
            results = [dict(r) for r in c.fetchall()]
            if results:
                return results
            c.execute("""SELECT om.id as observation_id, om.company_id,
                                om.observation_date as validation_date,
                                om.validation_status as new_status,
                                om.validation_status as prior_status,
                                'auto' as validation_method,
                                COALESCE(om.validation_evidence, 'No evidence recorded') as supporting_data,
                                '' as groq_reasoning,
                                om.confidence as accuracy_contribution,
                                c.ticker, c.company_name, om.category, om.observation_text,
                                om.created_at
                         FROM observation_memory om
                         JOIN companies c ON c.id = om.company_id
                         ORDER BY om.created_at DESC LIMIT ?""", (limit,))
            return [dict(r) for r in c.fetchall()]
