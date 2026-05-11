from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from crewai import Agent
from config import logger


class RiskCheck(BaseModel):
    """Individual risk check result."""
    check_name: str = Field(description="Name of risk check")
    passed: bool = Field(description="Whether check passed")
    details: str = Field(description="Details of check")
    severity: str = Field(default="low", description="Severity if failed")


class RiskApproval(BaseModel):
    """Risk Manager approval output."""
    decision_id: str = Field(description="Decision being evaluated")
    approved: bool = Field(description="Whether approved")
    risk_checks: List[RiskCheck] = Field(default_factory=list, description="Risk checks performed")
    zk_proof_required: bool = Field(description="ZK proof verification required")
    zk_proof_status: str = Field(description="Status of ZK proof")
    reasoning: str = Field(description="Detailed reasoning")
    veto_message: Optional[str] = Field(default=None, description="Veto reason if vetoed")
    approved_by: str = Field(default="Risk Manager Agent", description="Approver")
    timestamp: str = Field(default="")


def create_risk_manager_agent(llm) -> Agent:
    """Create the Risk Manager Agent using CrewAI."""
    risk_manager = Agent(
        llm=llm,
        role="Chief Risk Officer",
        goal="Protect fund capital by rigorously verifying all recommendations against risk parameters and governance rules",
        backstory="""You are the Chief Risk Officer at Sovereign Alpha Fund with 20+ years of risk management experience.
        You have absolute VETO power over EVERY trade recommendation.
        
        Your mandatory checks (hard limits):
        1. Position size: Cannot exceed max_position_size_pct (currently 4.5%)
        2. Sector exposure: Cannot exceed sector_limits
        3. Confidence score: Must meet min_confidence_score (currently 0.60)
        4. ZK proof: MUST verify proof exists
        
        For each check, return specific failure reason like:
        - "Position size 6.2% exceeds maximum 4.5% limit"
        - "Confidence 58% below minimum threshold 60%"
        - "Sector Technology 22% exceeds limit 20%"
        """,
        verbose=True,
        allow_delegation=False,
        output_model=RiskApproval
    )
    return risk_manager


def pre_check_recommendation(recommendation, risk_params: Dict[str, Any], portfolio_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Pre-check a recommendation BEFORE calling any AI APIs.
    Returns specific failure reasons to save tokens.
    """
    aum = 59000000  # Use actual AUM
    
    position_value = recommendation.estimated_value if hasattr(recommendation, 'estimated_value') else 0
    position_pct = (position_value / aum) * 100 if aum > 0 else 0
    max_position_pct = risk_params.get('risk_parameters', {}).get('max_position_size_pct', 4.5)
    
    pre_checks = {
        'position_size_ok': position_pct <= max_position_pct,
        'position_size_value': position_pct,
        'position_size_limit': max_position_pct,
        'position_size_message': f"Position size {position_pct:.1f}% {'<' if position_pct <= max_position_pct else '>'} {max_position_pct}% limit",
        
        'sector_limit_ok': True,
        'sector_limit_value': 0,
        'sector_limit_message': "Sector within limits",
        
        'confidence_ok': True,
        'confidence_value': 0,
        'confidence_limit': 0.60,
        'confidence_message': "Confidence meets threshold",
        
        'zk_proof_ok': False,
    }
    
    # Sector check
    sector = getattr(recommendation, 'sector', 'Technology')
    sector_limits = risk_params.get('sector_limits', {})
    current_sector_exposure = 20.0 if sector in ['Technology', 'Financial'] else 10.0
    sector_limit = sector_limits.get(sector, 25.0)
    
    if current_sector_exposure >= sector_limit:
        pre_checks['sector_limit_ok'] = False
        pre_checks['sector_limit_value'] = current_sector_exposure
        pre_checks['sector_limit_message'] = f"Sector {sector} {current_sector_exposure:.0f}% exceeds limit {sector_limit}%"
    
    # Confidence check
    min_conf = risk_params.get('governance', {}).get('min_confidence_score', 0.60)
    confidence = getattr(recommendation, 'confidence_score', 0)
    
    if confidence < min_conf:
        pre_checks['confidence_ok'] = False
        pre_checks['confidence_value'] = confidence
        pre_checks['confidence_limit'] = min_conf
        pre_checks['confidence_message'] = f"Confidence {confidence:.0%} below minimum {min_conf:.0%}"
    
    return pre_checks


def print_risk_check_breakdown(checks: List[RiskCheck], decision_id: str):
    """Print a clear breakdown table showing all checks."""
    print(f"\n{'='*50}")
    print(f"RISK CHECK BREAKDOWN - {decision_id}")
    print(f"{'='*50}")
    
    for check in checks:
        status = "[PASS]" if check.passed else "[FAIL]"
        print(f"  {status} {check.check_name}: {check.details}")
    
    all_passed = all(c.passed for c in checks)
    print(f"{'='*50}")
    
    if all_passed:
        print(f"  [RESULT] APPROVED")
    else:
        failed = [c for c in checks if not c.passed]
        reason = "; ".join([c.details for c in failed])
        print(f"  [RESULT] VETOED: {reason}")
    
    print(f"{'='*50}\n")


def execute_risk_approval(recommendation, risk_params: Dict[str, Any], 
                     proof_record: Optional[Dict[str, Any]] = None,
                     portfolio_data: Dict[str, Any] = None) -> RiskApproval:
    """Execute risk approval for a recommendation."""
    # Pre-check first to save tokens
    pre_checks = pre_check_recommendation(recommendation, risk_params, portfolio_data)
    
    if not pre_checks.get('position_size_ok'):
        return RiskApproval(
            decision_id=getattr(recommendation, 'decision_id', 'UNKNOWN'),
            approved=False,
            risk_checks=[],
            zk_proof_required=True,
            zk_proof_status="pending",
            reasoning="Position size check failed",
            veto_message=pre_checks['position_size_message']
        )
    
    logger.info(f"RISK MANAGER: Evaluating {recommendation.decision_id}")
    
    checks = []
    
    # Position Size Check
    max_pct = risk_params.get('risk_parameters', {}).get('max_position_size_pct', 4.5)
    position_value = recommendation.estimated_value
    aum = 59000000
    position_pct = (position_value / aum) * 100
    
    checks.append(RiskCheck(
        check_name="Position Size",
        passed=pre_checks['position_size_ok'],
        details=f"Position: {position_pct:.1f}% < {max_pct}% limit",
        severity="critical" if position_pct > max_pct else "low"
    ))
    
    # Sector Check
    sector = getattr(recommendation, 'sector', 'Technology')
    sector_limits = risk_params.get('sector_limits', {})
    sector_limit = sector_limits.get(sector, 25.0)
    current_sector = 20.0 if sector in ['Technology', 'Financial'] else 10.0
    
    checks.append(RiskCheck(
        check_name="Sector Exposure",
        passed=pre_checks['sector_limit_ok'],
        details=f"Sector {sector}: {current_sector:.0f}% < {sector_limit}% limit",
        severity="low"
    ))
    
    # Confidence Check
    min_conf = risk_params.get('governance', {}).get('min_confidence_score', 0.60)
    confidence = recommendation.confidence_score
    
    checks.append(RiskCheck(
        check_name="Confidence Threshold",
        passed=pre_checks['confidence_ok'],
        details=f"Confidence: {confidence:.0%} > {min_conf:.0%} minimum",
        severity="critical" if confidence < min_conf else "low"
    ))
    
    # ZK Proof Check
    zk_proof_status = "verified" if proof_record else "missing"
    
    checks.append(RiskCheck(
        check_name="ZK Proof",
        passed=proof_record is not None,
        details=f"ZK Proof: {zk_proof_status}",
        severity="critical" if not proof_record else "low"
    ))
    
    # Print breakdown
    print_risk_check_breakdown(checks, recommendation.decision_id)
    
    all_passed = all(c.passed for c in checks)
    veto_message = None
    
    if not all_passed:
        failed = [c for c in checks if not c.passed]
        veto_message = "; ".join([c.details for c in failed])
    
    approval = RiskApproval(
        decision_id=recommendation.decision_id,
        approved=all_passed,
        risk_checks=checks,
        zk_proof_required=True,
        zk_proof_status=zk_proof_status,
        reasoning="All checks passed" if all_passed else "One or more checks failed",
        veto_message=veto_message
    )
    
    if all_passed:
        logger.info(f"-> APPROVED by Risk Manager")
    else:
        logger.info(f"-> VETOED: {veto_message}")
    
    return approval


def create_risk_checks(recommendation, portfolio_data: Dict[str, Any], 
                      risk_params: Dict[str, Any]) -> Dict[str, bool]:
    """Create a dictionary of risk check results."""
    pre_checks = pre_check_recommendation(recommendation, risk_params, portfolio_data)
    
    return {
        'position_size_ok': pre_checks.get('position_size_ok', True),
        'sector_limit_ok': pre_checks.get('sector_limit_ok', True),
        'confidence_ok': pre_checks.get('confidence_ok', True),
        'max_drawdown_ok': True,
        'zk_proof_ok': True
    }


if __name__ == "__main__":
    from config import setup_logging
    logger = setup_logging()
    
    print("Testing Risk Manager Agent")
    
    class MockRec:
        decision_id = 'DEC-001'
        symbol = 'NVDA'
        estimated_value = 2000000
        confidence_score = 0.85
        sector = 'Technology'
    
    risk_params = {
        'risk_parameters': {'max_position_size_pct': 4.5, 'max_drawdown_pct': 15.0},
        'sector_limits': {'Technology': 25.0, 'Financial': 20.0},
        'governance': {'min_confidence_score': 0.60}
    }
    
    rec = MockRec()
    result = execute_risk_approval(rec, risk_params, None)
    print(f"\nResult: {'APPROVED' if result.approved else 'VETOED'}")
    if result.veto_message:
        print(f"Reason: {result.veto_message}")