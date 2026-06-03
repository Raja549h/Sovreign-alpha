"""
Auto Review Engine — Scheduled observation validation
======================================================
Reviews due observations against current financial data
and updates validation status automatically.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent

GROQ_VALIDATION_PROMPT = """You are an institutional analyst validating a prior research observation.

Original observation (made {date}):
{observation_text}

Expected implication:
{expected_implication}

Current financial data:
{current_metrics}

Recent developments:
{recent_news}

Has this observation been validated?

Output JSON only:
{{
  'status': 'CONFIRMED' | 'PARTIALLY_CONFIRMED' | 'MONITORING' | 'INVALIDATED',
  'evidence': str (specific data point proving/disproving),
  'reasoning': str (2 sentences max, institutional tone),
  'confidence': float (0-1)
}}

CONFIRMED: Observation clearly proven by subsequent data.
PARTIALLY_CONFIRMED: Directionally correct but not fully materialised.
MONITORING: Too early to validate, check again next review.
INVALIDATED: Subsequent data clearly contradicts the observation."""


class AutoReviewEngine:

    def __init__(self):
        from research.observation_registry import ObservationRegistry
        self.registry = ObservationRegistry()

    def run_scheduled_reviews(self) -> Dict:
        results = {
            '30_day': [], '90_day': [], '180_day': [],
            'total_reviewed': 0,
            'confirmed': 0, 'invalidated': 0, 'monitoring': 0,
            'partial': 0,
        }

        for review_type in ['30_day', '90_day', '180_day']:
            due = self.registry.get_due_for_review(review_type)
            for obs in due:
                result = self.review_observation(obs)
                results['total_reviewed'] += 1
                results[review_type].append({
                    'observation_id': obs.get('id'),
                    'status': result.get('new_status', 'MONITORING'),
                })
                s = result.get('new_status', 'MONITORING').lower()
                if s == 'confirmed':
                    results['confirmed'] += 1
                elif s == 'invalidated':
                    results['invalidated'] += 1
                elif s == 'monitoring':
                    results['monitoring'] += 1
                elif s == 'partially_confirmed':
                    results['partial'] += 1

        self.registry.calculate_edge_score()
        return results

    def review_observation(self, observation: Dict) -> Dict:
        obs_id = observation.get('id')
        company_id = observation.get('company_id')
        obs_text = observation.get('observation_text', '')
        expected = observation.get('expected_implication', '')
        obs_date = observation.get('observation_date', '')
        ticker = observation.get('ticker', '')

        current_metrics = self._fetch_current_metrics(ticker, company_id)
        recent_news = self._fetch_recent_news(ticker)

        classification = self._classify_via_groq(
            obs_date, obs_text, expected,
            current_metrics, recent_news
        )

        new_status = classification.get('status', 'MONITORING')
        evidence = classification.get('evidence', '')
        reasoning = classification.get('reasoning', '')
        groq_confidence = classification.get('confidence', 0.5)

        review_type = self._determine_review_type(observation)

        with self.registry._get_db() as conn:
            c = conn.cursor()
            c.execute(
                """UPDATE observation_memory
                   SET validation_status = ?, validation_evidence = ?,
                       validated_at = ?, validated_by = 'auto_engine'
                   WHERE id = ?""",
                (new_status, evidence,
                 datetime.now(timezone.utc).strftime('%Y-%m-%d'), obs_id)
            )

            accuracy = {'CONFIRMED': 1.0, 'PARTIALLY_CONFIRMED': 0.5,
                        'MONITORING': 0.0, 'ACTIVE': 0.0, 'INVALIDATED': -1.0}

            c.execute(
                """INSERT INTO observation_validations
                   (observation_id, company_id, validation_date, review_type,
                    prior_status, new_status, validation_method,
                    supporting_data, groq_reasoning, accuracy_contribution)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (obs_id, company_id,
                 datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                 review_type, observation.get('validation_status', 'ACTIVE'),
                 new_status, 'financial_results',
                 json.dumps({'metrics': current_metrics, 'news': recent_news}),
                 reasoning, accuracy.get(new_status, 0.0))
            )
            conn.commit()

        self.registry.calculate_edge_score(company_id)

        return {
            'observation_id': obs_id,
            'prior_status': observation.get('validation_status', 'ACTIVE'),
            'new_status': new_status,
            'evidence': evidence,
            'reasoning': reasoning,
            'confidence': groq_confidence,
        }

    def trigger_review(self, company_id: int, trigger: str) -> List[Dict]:
        active = self.registry.get_registry(
            company_id=company_id,
            status='ACTIVE',
            limit=200
        )
        results = []
        for obs in active:
            obs_dict = dict(obs)
            obs_dict['company_id'] = company_id
            result = self.review_observation(obs_dict)
            results.append(result)
        return results

    def _fetch_current_metrics(self, ticker: str, company_id: int) -> Dict:
        metrics = {}
        try:
            import yfinance as yf
            t = yf.Ticker(ticker + ".NS")
            info = t.info or {}
            for key, label in [('trailingPE', 'PE'), ('priceToBook', 'PBV'),
                               ('returnOnEquity', 'ROE'), ('revenueGrowth', 'REVENUE_GROWTH'),
                               ('earningsGrowth', 'EARNINGS_GROWTH'),
                               ('debtToEquity', 'DEBT_EQUITY'),
                               ('currentRatio', 'CURRENT_RATIO'),
                               ('operatingMargins', 'OPERATING_MARGIN'),
                               ('profitMargins', 'PROFIT_MARGIN')]:
                val = info.get(key)
                if val is not None:
                    metrics[label] = round(val, 4)
        except Exception:
            pass
        try:
            from research.storage.research_db import get_metric_series
            for metric in ['NIM', 'ROE', 'ROA', 'CREDIT_COST', 'COF']:
                series = get_metric_series(company_id, metric)
                if series:
                    metrics[metric] = series[-1].get('value')
        except Exception:
            pass
        return metrics

    def _fetch_recent_news(self, ticker: str) -> List[str]:
        news = []
        try:
            from research.web_researcher import research_company
            data = research_company(ticker, ticker, '')
            commentary = data.get('management_commentary', '')
            if commentary:
                news.append(commentary[:500])
        except Exception:
            pass
        return news

    def _classify_via_groq(self, date: str, text: str, expected: str,
                           metrics: Dict, news: List) -> Dict:
        groq_key = os.environ.get('GROQ_API_KEY', '')
        if not groq_key:
            return {'status': 'MONITORING', 'evidence': '',
                    'reasoning': 'Groq unavailable for classification.',
                    'confidence': 0.5}

        prompt = GROQ_VALIDATION_PROMPT.format(
            date=date or 'unknown date',
            observation_text=text or 'No observation text',
            expected_implication=expected or 'Not specified',
            current_metrics=json.dumps(metrics, indent=2)[:1500],
            recent_news=json.dumps(news, indent=2)[:1000],
        )

        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an institutional analyst validating research observations. Output JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            text = response.choices[0].message.content
            text = text.replace("'", '"')
            result = json.loads(text)
            for key in ['status', 'evidence', 'reasoning']:
                if key not in result:
                    result[key] = 'MONITORING' if key == 'status' else ''
            return result
        except Exception:
            return {'status': 'MONITORING', 'evidence': '',
                    'reasoning': 'Groq classification failed. Remains MONITORING.',
                    'confidence': 0.5}

    def _determine_review_type(self, observation: Dict) -> str:
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        for rt, col in [('180_day', 'review_date_180'), ('90_day', 'review_date_90'),
                        ('30_day', 'review_date_30')]:
            val = observation.get(col)
            if val and val <= today:
                return rt
        return 'triggered'
