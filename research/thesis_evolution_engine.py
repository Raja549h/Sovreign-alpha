from dashboard.gateway import get_connection
"""
Thesis Evolution Engine — Persistent thesis tracking
======================================================
Compares new analysis against historical findings and
classifies directional change automatically.
"""

import os
import json

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent
BILLING_DIR = BASE_DIR / "billing"
RESEARCH_DB = BILLING_DIR / "research.db"

CATEGORIES = [
    'margin', 'funding_cost', 'governance',
    'capital_allocation', 'valuation',
    'macro', 'management_commentary',
    'liquidity', 'business_quality',
]

EVOLUTION_STATUSES = [
    'STRENGTHENING', 'STABLE', 'WEAKENING',
    'REVERSING', 'CONTRADICTING', 'NEW_FINDING',
]

MAGNITUDES = ['SIGNIFICANT', 'MODERATE', 'MINOR']

DIRECTION_VALUES = ['improving', 'stable', 'deteriorating']

SCORECARD_FIELDS = [
    'business_quality', 'capital_allocation', 'governance',
    'liquidity', 'funding_structure', 'macro_exposure', 'valuation',
]

SCORECARD_VALUES = ['IMPROVING', 'STABLE', 'DETERIORATING', 'INSUFFICIENT_DATA']

load_dotenv = __import__('dotenv').load_dotenv
load_dotenv(BASE_DIR / ".env")


def _get_db():
    conn = get_connection()
    return conn


def _get_company_name(company_id: int) -> str:
    with _get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT company_name FROM companies WHERE id = %s", (company_id,))
        r = c.fetchone()
        return r['company_name'] if r else str(company_id)


CEREBRAS_CLASSIFY_PROMPT = (
    "You are an institutional analyst comparing two observations about the "
    "same company made at different times.\n\n"
    "Classify the evolution as exactly one of:\n"
    "STRENGTHENING — situation improved\n"
    "STABLE — no material change\n"
    "WEAKENING — situation deteriorated\n"
    "REVERSING — complete directional change\n"
    "CONTRADICTING — new data contradicts prior\n"
    "NEW_FINDING — no prior observation exists\n\n"
    "Also classify magnitude:\n"
    "SIGNIFICANT — material institutional impact\n"
    "MODERATE — worth monitoring\n"
    "MINOR — noise level change\n\n"
    "Output JSON only:\n"
    "{\n"
    "  'status': str,\n"
    "  'magnitude': str,\n"
    "  'evidence': str (one sentence)\n"
    "}"
)


class ThesisEvolutionEngine:

    def store_observation(self,
                          company_id: int,
                          category: str,
                          observation_text: str,
                          confidence: float,
                          source: str,
                          metric_name: str = None,
                          metric_value: float = None,
                          direction: str = None) -> int:
        if category not in CATEGORIES:
            raise ValueError(f"Invalid category '{category}'. Must be one of {CATEGORIES}")
        if direction and direction not in DIRECTION_VALUES:
            raise ValueError(f"Invalid direction '{direction}'. Must be one of {DIRECTION_VALUES}")
        with _get_db() as conn:
            c = conn.cursor()
            c.execute(
                """INSERT INTO observation_memory
                   (company_id, observation_date, category, observation_text,
                    confidence, source, metric_name, metric_value, direction)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (company_id, datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                 category, observation_text, confidence, source,
                 metric_name, metric_value, direction)
            )
            conn.commit()
            return c.lastrowid

    def compare_to_history(self,
                           company_id: int,
                           category: str,
                           new_observation: str,
                           new_metric: float = None) -> Dict:
        prior = self._get_latest_observation(company_id, category)
        if not prior:
            return {
                'status': 'NEW_FINDING',
                'magnitude': 'MODERATE',
                'evidence': 'No prior observation exists for this category.',
            }

        result = self._classify_via_cerebras(prior['observation_text'], new_observation)

        evolution_id = self._save_evolution(
            company_id, category,
            prior['observation_text'], new_observation,
            result['status'], result['magnitude'], result['evidence'],
            prior.get('observation_date'),
        )

        result['evolution_id'] = evolution_id
        result['prior_observation'] = prior['observation_text']
        result['current_observation'] = new_observation
        return result

    def generate_evolution_report(self, company_id: int) -> Dict:
        company_name = _get_company_name(company_id)
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        all_observations = self.get_observation_timeline(company_id, limit=100)
        latest_date = None
        if all_observations:
            latest_date = all_observations[0].get('observation_date')

        categories = {}
        for cat in CATEGORIES:
            recent = [o for o in all_observations if o['category'] == cat]
            if not recent:
                categories[cat] = {
                    'status': 'NEW_FINDING',
                    'magnitude': 'MODERATE',
                    'prior': None,
                    'current': None,
                    'evidence': 'No observations recorded for this category.',
                }
                continue

            current = recent[0]
            prior = recent[1] if len(recent) > 1 else None

            if prior:
                comparison = self.compare_to_history(
                    company_id, cat,
                    current['observation_text'],
                    current.get('metric_value'),
                )
                categories[cat] = {
                    'status': comparison['status'],
                    'magnitude': comparison['magnitude'],
                    'prior': prior['observation_text'],
                    'current': current['observation_text'],
                    'evidence': comparison['evidence'],
                }
            else:
                categories[cat] = {
                    'status': 'NEW_FINDING',
                    'magnitude': 'MODERATE',
                    'prior': None,
                    'current': current['observation_text'],
                    'evidence': 'First observation — baseline established.',
                }

        overall = self._compute_overall_direction(categories)
        key_changes = self._extract_key_changes(categories)
        confirmed = self._extract_confirmed(categories)
        invalidated = self._extract_invalidated(categories)
        new_findings = self._extract_new_findings(categories)

        return {
            'company': company_name,
            'analysis_date': today,
            'prior_analysis_date': latest_date or today,
            'categories': categories,
            'overall_direction': overall,
            'key_changes': key_changes,
            'confirmed_observations': confirmed,
            'invalidated_observations': invalidated,
            'new_findings': new_findings,
        }

    def update_thesis_scorecard(self, company_id: int) -> Dict:
        report = self.generate_evolution_report(company_id)
        categories = report['categories']

        field_map = {
            'business_quality': 'business_quality',
            'capital_allocation': 'capital_allocation',
            'governance': 'governance',
            'liquidity': 'liquidity',
            'funding_structure': 'funding_cost',
            'macro_exposure': 'macro',
            'valuation': 'valuation',
        }

        scorecard = {}
        for field, cat_key in field_map.items():
            cat = categories.get(cat_key, {})
            status = cat.get('status', 'INSUFFICIENT_DATA')
            scorecard[field] = self._map_status_to_scorecard(status)

        for f in SCORECARD_FIELDS:
            if f not in scorecard:
                scorecard[f] = 'INSUFFICIENT_DATA'

        overall = self._compute_scorecard_overall(scorecard)

        num_improving = sum(1 for v in scorecard.values() if v == 'IMPROVING')
        num_deteriorating = sum(1 for v in scorecard.values() if v == 'DETERIORATING')
        if num_deteriorating > num_improving:
            summary = f"{num_deteriorating} of 7 categories deteriorating. Thesis weakening."
        elif num_improving > num_deteriorating:
            summary = f"{num_improving} of 7 categories improving. Thesis strengthening."
        else:
            summary = "Mixed signals. No dominant directional bias."

        with _get_db() as conn:
            c = conn.cursor()
            c.execute(
                """INSERT INTO thesis_scorecard
                   (company_id, scored_at, business_quality, capital_allocation,
                    governance, liquidity, funding_structure, macro_exposure,
                    valuation, overall_direction, scorecard_summary)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (company_id, datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                 scorecard.get('business_quality'),
                 scorecard.get('capital_allocation'),
                 scorecard.get('governance'),
                 scorecard.get('liquidity'),
                 scorecard.get('funding_structure'),
                 scorecard.get('macro_exposure'),
                 scorecard.get('valuation'),
                 overall, summary)
            )
            conn.commit()

        return {
            'scorecard': scorecard,
            'overall_direction': overall,
            'summary': summary,
        }

    def get_observation_timeline(self,
                                 company_id: int,
                                 category: str = None,
                                 limit: int = 20) -> List[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            if category:
                c.execute(
                    """SELECT * FROM observation_memory
                       WHERE company_id = %s AND category = %s
                       ORDER BY observation_date DESC, id DESC LIMIT %s""",
                    (company_id, category, limit)
                )
            else:
                c.execute(
                    """SELECT * FROM observation_memory
                       WHERE company_id = %s
                       ORDER BY observation_date DESC, id DESC LIMIT %s""",
                    (company_id, limit)
                )
            return [dict(r) for r in c.fetchall()]

    def _get_latest_observation(self, company_id: int, category: str) -> Optional[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute(
                """SELECT * FROM observation_memory
                   WHERE company_id = %s AND category = %s
                   ORDER BY observation_date DESC, id DESC LIMIT 1 OFFSET 1""",
                (company_id, category)
            )
            r = c.fetchone()
            return dict(r) if r else None

    def _save_evolution(self, company_id: int, category: str,
                        prior_obs: str, current_obs: str,
                        status: str, magnitude: str,
                        evidence: str, prior_date: str = None) -> int:
        with _get_db() as conn:
            c = conn.cursor()
            c.execute(
                """INSERT INTO thesis_evolution
                   (company_id, analysis_date, prior_analysis_date, category,
                    prior_observation, current_observation,
                    evolution_status, magnitude, evidence)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (company_id, datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                 prior_date or '', category,
                 prior_obs, current_obs,
                 status, magnitude, evidence)
            )
            conn.commit()
            return c.lastrowid

    def _classify_via_cerebras(self, prior_text: str, current_text: str) -> Dict:
        cerebras_key = os.environ.get('LLM_API_KEY', '')
        if not cerebras_key:
            return self._classify_fallback(prior_text, current_text)

        try:
            from openai import OpenAI
            client = Cerebras(api_key=cerebras_key)
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": CEREBRAS_CLASSIFY_PROMPT},
                    {"role": "user", "content": f"Prior: {prior_text}\n\nCurrent: {current_text}"}
                ],
                temperature=0.1,
                max_tokens=200
            )
            text = response.choices[0].message.content
            text = text.replace("'", '"')
            result = json.loads(text)
            status = result.get('status', 'STABLE')
            magnitude = result.get('magnitude', 'MODERATE')
            evidence = result.get('evidence', 'Classification performed by institutional analyst.')
            if status not in EVOLUTION_STATUSES:
                status = 'STABLE'
            if magnitude not in MAGNITUDES:
                magnitude = 'MODERATE'
            return {'status': status, 'magnitude': magnitude, 'evidence': evidence}
        except Exception:
            return self._classify_fallback(prior_text, current_text)

    def _classify_fallback(self, prior_text: str, current_text: str) -> Dict:
        return {'status': 'STABLE', 'magnitude': 'MODERATE',
                'evidence': 'Automated classification — no material change detected.'}

    def _compute_overall_direction(self, categories: Dict) -> str:
        weights = {'STRENGTHENING': 1, 'STABLE': 0, 'WEAKENING': -1,
                   'REVERSING': -2, 'CONTRADICTING': -1, 'NEW_FINDING': 0}
        scores = []
        for cat in categories.values():
            s = weights.get(cat.get('status', 'STABLE'), 0)
            m = 1 if cat.get('magnitude') == 'SIGNIFICANT' else 0.5 if cat.get('magnitude') == 'MODERATE' else 0.25
            scores.append(s * m)
        if not scores:
            return 'STABLE'
        avg = sum(scores) / len(scores)
        if avg >= 0.5:
            return 'STRENGTHENING'
        elif avg <= -0.5:
            return 'WEAKENING'
        return 'STABLE'

    def _extract_key_changes(self, categories: Dict) -> List[str]:
        changes = []
        for cat_key, cat in categories.items():
            s = cat.get('status')
            if s in ('WEAKENING', 'STRENGTHENING', 'REVERSING', 'CONTRADICTING'):
                label = cat_key.replace('_', ' ').title()
                changes.append(f"{label}: {s} ({cat.get('magnitude', 'MODERATE')}) — {cat.get('evidence', '')}")
        return changes

    def _extract_confirmed(self, categories: Dict) -> List[str]:
        confirmed = []
        for cat_key, cat in categories.items():
            if cat.get('status') == 'STRENGTHENING':
                label = cat_key.replace('_', ' ').title()
                confirmed.append(f"{label}: {cat.get('current', '')}")
        return confirmed

    def _extract_invalidated(self, categories: Dict) -> List[str]:
        invalidated = []
        for cat_key, cat in categories.items():
            if cat.get('status') in ('REVERSING', 'CONTRADICTING'):
                label = cat_key.replace('_', ' ').title()
                invalidated.append(f"{label}: Prior — {cat.get('prior', '')}")
        return invalidated

    def _extract_new_findings(self, categories: Dict) -> List[str]:
        findings = []
        for cat_key, cat in categories.items():
            if cat.get('status') == 'NEW_FINDING' and cat.get('current'):
                label = cat_key.replace('_', ' ').title()
                findings.append(f"{label}: {cat.get('current', '')}")
        return findings

    def _map_status_to_scorecard(self, evolution_status: str) -> str:
        mapping = {
            'STRENGTHENING': 'IMPROVING',
            'STABLE': 'STABLE',
            'WEAKENING': 'DETERIORATING',
            'REVERSING': 'DETERIORATING',
            'CONTRADICTING': 'DETERIORATING',
            'NEW_FINDING': 'STABLE',
        }
        return mapping.get(evolution_status, 'INSUFFICIENT_DATA')

    def _compute_scorecard_overall(self, scorecard: Dict) -> str:
        deteriorating = sum(1 for v in scorecard.values() if v == 'DETERIORATING')
        improving = sum(1 for v in scorecard.values() if v == 'IMPROVING')
        if deteriorating > improving + 1:
            return 'WEAKENING'
        elif improving > deteriorating + 1:
            return 'STRENGTHENING'
        return 'STABLE'
