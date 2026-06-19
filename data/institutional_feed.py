"""
Institutional Feed — Macro and market intelligence aggregator
==============================================================
Provides institutional-grade market context and regime analysis.
Note: Core functionality is integrated into research/intelligence/regime_connector.py.
This module re-exports for backward compatibility.
"""

import sys
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from research.intelligence.regime_connector import (
    get_regime_context,
    assess_regime_sensitivity,
    calculate_regime_sensitivity_score,
    SECTOR_SENSITIVITY,
)


def get_market_regime() -> Dict:
    """
    Get current market regime classification.
    
    Returns:
        Dict with regime, confidence, and factors
    """
    return get_regime_context()


def get_sector_sensitivity(sector: str) -> Dict:
    """
    Get sensitivity profile for a sector.
    
    Args:
        sector: Sector name (e.g., 'NBFC', 'BANK', 'TECHNOLOGY')
    
    Returns:
        Dict with high/medium/low sensitivity factors
    """
    return SECTOR_SENSITIVITY.get(sector.upper(), {
        'high_sensitivity': ['rates', 'equity_markets'],
        'medium_sensitivity': ['credit_spreads'],
        'low_sensitivity': ['commodities'],
    })


def assess_company_regime_impact(company_id: int, sector: str) -> Dict:
    """
    Assess how current regime affects a specific company.
    
    Args:
        company_id: Company database ID
        sector: Company sector
    
    Returns:
        Dict with regime impact assessment
    """
    return assess_regime_sensitivity(company_id, sector)


def get_regime_score(company_id: int, sector: str) -> float:
    """
    Calculate regime sensitivity score for a company.
    
    Args:
        company_id: Company database ID
        sector: Company sector
    
    Returns:
        Float score 0-10
    """
    return calculate_regime_sensitivity_score(company_id, sector)


def get_all_regime_factors() -> List[str]:
    """
    Get list of all regime factors tracked.
    
    Returns:
        List of factor names
    """
    factors = set()
    for sector_data in SECTOR_SENSITIVITY.values():
        for sensitivity_level in sector_data.values():
            factors.update(sensitivity_level)
    return sorted(list(factors))
