from database import get_connection
"""
Portfolio Intelligence Engine
Analyzes multi-company portfolio risk including concentration,
hidden correlations, stress test scenarios, and forensic scoring.
"""

from pathlib import Path
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).parent.parent
BILLING_DIR = BASE_DIR / "billing"
RESEARCH_DB = BILLING_DIR / "research.db"

def get_connection():
    conn = get_connection()
    return conn

def create_portfolio(name: str, description: str = "", strategy: str = "") -> int:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO portfolios (name, description, strategy) VALUES (?, ?, ?)", (name, description, strategy))
        conn.commit()
        return c.lastrowid

def get_portfolios() -> List[Dict]:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM portfolios ORDER BY created_at DESC")
        return [dict(r) for r in c.fetchall()]

def get_portfolio(portfolio_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM portfolios WHERE id = ?", (portfolio_id,))
        r = c.fetchone()
        return dict(r) if r else None

def add_position(portfolio_id: int, company_id: int, weight_pct: float, cost_basis: float = None, notes: str = "") -> int:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO portfolio_positions (portfolio_id, company_id, weight_pct, cost_basis, notes) VALUES (?, ?, ?, ?, ?)", (portfolio_id, company_id, weight_pct, cost_basis, notes))
        conn.commit()
        return c.lastrowid

def get_positions(portfolio_id: int) -> List[Dict]:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT p.*, c.ticker, c.company_name, c.sector
            FROM portfolio_positions p
            JOIN companies c ON c.id = p.company_id
            WHERE p.portfolio_id = ?
            ORDER BY p.weight_pct DESC
        """, (portfolio_id,))
        return [dict(r) for r in c.fetchall()]

def delete_position(position_id: int):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM portfolio_positions WHERE id = ?", (position_id,))
        conn.commit()

def calculate_concentration(portfolio_id: int) -> Dict:
    positions = get_positions(portfolio_id)
    if not positions:
        return {"hhi": 0, "top_5_weight": 0, "num_positions": 0, "sector_exposure": {}, "largest_position": None, "concentration_risk": "LOW"}
    total_weight = sum(p["weight_pct"] for p in positions)
    if total_weight == 0:
        return {"hhi": 0, "top_5_weight": 0, "num_positions": len(positions), "sector_exposure": {}, "largest_position": None, "concentration_risk": "LOW"}
    weights = [p["weight_pct"] / total_weight for p in positions]
    hhi = sum(w * w * 10000 for w in weights)
    sorted_pos = sorted(positions, key=lambda x: x["weight_pct"], reverse=True)
    top_5_weight = sum(p["weight_pct"] for p in sorted_pos[:5])
    sector_exposure = {}
    for p in positions:
        sec = p.get("sector") or "UNKNOWN"
        sector_exposure[sec] = sector_exposure.get(sec, 0) + p["weight_pct"]
    largest = {"ticker": sorted_pos[0]["ticker"], "weight": sorted_pos[0]["weight_pct"]}
    if hhi > 2500:
        risk = "HIGH"
    elif hhi > 1500:
        risk = "MEDIUM"
    else:
        risk = "LOW"
    return {"hhi": round(hhi, 1), "top_5_weight": round(top_5_weight, 1), "num_positions": len(positions), "sector_exposure": sector_exposure, "largest_position": largest, "concentration_risk": risk}

def detect_hidden_correlations(portfolio_id: int) -> List[Dict]:
    positions = get_positions(portfolio_id)
    flags = []
    if len(positions) < 2:
        return flags
    for i, a in enumerate(positions):
        for b in positions[i+1:]:
            score = 0
            reasons = []
            if a.get("sector") and b.get("sector") and a["sector"] == b["sector"]:
                score += 30
                reasons.append(f"Same sector: {a['sector']}")
            if a.get("ticker") and b.get("ticker"):
                common_keywords = _get_common_exposures(a, b)
                for kw in common_keywords:
                    score += 15
                    reasons.append(f"Common exposure: {kw}")
            if score > 20:
                flags.append({"pair": f"{a['ticker']} / {b['ticker']}", "correlation_score": min(score, 100), "reasons": reasons, "risk_level": "HIGH" if score > 50 else "MEDIUM"})
    return flags

def _get_common_exposures(pos_a: Dict, pos_b: Dict) -> List[str]:
    keywords = []
    a_name = (pos_a.get("company_name") or "").lower()
    b_name = (pos_b.get("company_name") or "").lower()
    common = {"housing", "auto", "retail", "industrial", "energy", "digital", "infrastructure", "consumer", "corporate", "rural"}
    for kw in common:
        if kw in a_name and kw in b_name:
            keywords.append(kw)
    return keywords

def run_stress_test(portfolio_id: int, scenario: str = "rate_shock") -> Dict:
    positions = get_positions(portfolio_id)
    if not positions:
        return {"scenario": scenario, "impact_pct": 0, "impact_value": 0, "max_position_impact": None, "num_positions_affected": 0}
    positions_with_flags = []
    for p in positions:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT severity, flag_type FROM forensic_flags WHERE company_id = ?", (p["company_id"],))
            flags = [dict(r) for r in c.fetchall()]
        positions_with_flags.append({"position": p, "flags": flags})
    if scenario == "rate_shock":
        impact_fn = lambda p, flags: p["weight_pct"] * 0.08 * (1.0 + sum(1 for f in flags if f.get("severity") in ("HIGH", "CRITICAL")) * 0.3)
    elif scenario == "credit_cycle":
        impact_fn = lambda p, flags: p["weight_pct"] * 0.12 * (1.0 + sum(1 for f in flags if f.get("severity") in ("HIGH", "CRITICAL")) * 0.25) - (3.0 if any(f.get("flag_type") == "credit_cost_acceleration" for f in flags) else 0)
    elif scenario == "liquidity_tightening":
        impact_fn = lambda p, flags: p["weight_pct"] * 0.10 * (1.0 + sum(1 for f in flags if f.get("severity") in ("HIGH", "CRITICAL")) * 0.35) - (2.0 if any(f.get("flag_type") == "margin_compression" for f in flags) else 0)
    else:
        impact_fn = lambda p, flags: p["weight_pct"] * 0.05
    total_weight = sum(p["weight_pct"] for p in positions)
    total_impact = sum(impact_fn(p["position"], p["flags"]) for p in positions_with_flags)
    impact_pct = (total_impact / total_weight * 100) if total_weight > 0 else 0
    max_impact_pos = max(positions_with_flags, key=lambda x: impact_fn(x["position"], x["flags"]))
    num_affected = sum(1 for p in positions_with_flags if impact_fn(p["position"], p["flags"]) > 1.0)
    return {"scenario": scenario, "impact_pct": round(impact_pct, 2), "impact_value": round(total_impact, 2), "max_position_impact": max_impact_pos["position"]["ticker"], "num_positions_affected": num_affected, "total_positions": len(positions)}

def run_all_stress_tests(portfolio_id: int) -> List[Dict]:
    scenarios = ["rate_shock", "credit_cycle", "liquidity_tightening"]
    return [run_stress_test(portfolio_id, s) for s in scenarios]

def save_stress_results(portfolio_id: int, results: List[Dict]):
    with get_connection() as conn:
        c = conn.cursor()
        for r in results:
            c.execute("INSERT INTO portfolio_stress_results (portfolio_id, scenario, impact_pct, impact_value, max_position_impact, num_positions_affected) VALUES (?, ?, ?, ?, ?, ?)", (portfolio_id, r["scenario"], r["impact_pct"], r["impact_value"], r["max_position_impact"], r["num_positions_affected"]))
        conn.commit()

def get_stress_results(portfolio_id: int) -> List[Dict]:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM portfolio_stress_results WHERE portfolio_id = ? ORDER BY id DESC", (portfolio_id,))
        return [dict(r) for r in c.fetchall()]

def calculate_portfolio_score(portfolio_id: int) -> Dict:
    concentration = calculate_concentration(portfolio_id)
    positions = get_positions(portfolio_id)
    if not positions:
        return {"portfolio_id": portfolio_id, "diversification_score": 0, "concentration_penalty": 0, "sector_concentration_penalty": 0, "correlation_penalty": 0, "stress_impact_score": 0, "composite_score": 0, "grade": "F"}
    if concentration["concentration_risk"] == "LOW":
        diversity = 9
        conc_penalty = 0
    elif concentration["concentration_risk"] == "MEDIUM":
        diversity = 6
        conc_penalty = 15
    else:
        diversity = 3
        conc_penalty = 30
    sector_count = len(concentration.get("sector_exposure", {}))
    sector_penalty = max(0, (5 - sector_count)) * 8 if sector_count < 3 else 0
    correlations = detect_hidden_correlations(portfolio_id)
    corr_penalty = min(25, len(correlations) * 5 * (sum(c.get("correlation_score", 0) for c in correlations) / max(len(correlations), 1)) / 10)
    stress_results = run_all_stress_tests(portfolio_id)
    avg_stress_impact = sum(r["impact_pct"] for r in stress_results) / len(stress_results) if stress_results else 0
    stress_penalty = min(20, avg_stress_impact * 2)
    composite = round(max(0, min(100, diversity * 10 - conc_penalty - sector_penalty - corr_penalty - stress_penalty)), 1)
    score = {"portfolio_id": portfolio_id, "diversification_score": diversity * 10, "concentration_penalty": conc_penalty, "sector_concentration_penalty": sector_penalty, "correlation_penalty": round(corr_penalty, 1), "stress_impact_score": round(stress_penalty, 1), "composite_score": composite}
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO portfolio_scores (portfolio_id, diversification_score, concentration_penalty, sector_concentration_penalty, correlation_penalty, stress_impact_score, composite_score) VALUES (?, ?, ?, ?, ?, ?, ?)", (portfolio_id, score["diversification_score"], score["concentration_penalty"], score["sector_concentration_penalty"], score["correlation_penalty"], score["stress_impact_score"], score["composite_score"]))
        conn.commit()
    return score

def get_portfolio_scores(portfolio_id: int) -> List[Dict]:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM portfolio_scores WHERE portfolio_id = ? ORDER BY scored_at DESC", (portfolio_id,))
        return [dict(r) for r in c.fetchall()]

def grade_from_score(score: float) -> str:
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 55: return "C"
    if score >= 40: return "D"
    return "F"
