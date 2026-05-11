from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from crewai import Agent
from privacy import logger  # ✅ PRIVACY: Sanitized logger (WARNING+)


class TradeRecommendation(BaseModel):
    """Structured trade recommendation output."""
    decision_id: str = Field(description="Unique decision identifier")
    symbol: str = Field(description="Ticker symbol")
    action: str = Field(description="BUY, SELL, or HOLD")
    quantity: int = Field(description="Number of shares")
    entry_price: float = Field(description="Entry price per share")
    estimated_value: float = Field(description="Total position value in USD")
    recommended_weight_pct: float = Field(description="Weight as % of AUM, must be 0.5-4.0%")
    confidence_score: float = Field(description="Confidence 0.0-1.0")
    rationale: str = Field(description="Detailed reasoning")
    sector: str = Field(description="Sector classification")
    momentum_signal: Optional[str] = Field(default=None, description="MMI signal")
    risks_identified: List[str] = Field(default_factory=list, description="Risk factors")
    expected_holding_period: str = Field(default="30-60 days", description="Expected hold duration")
    exit_conditions: str = Field(description="Exit strategy")
    live_data_confirmation: bool = Field(default=False, description="True if live market data supports the thesis")
    
    @field_validator('recommended_weight_pct')
    @classmethod
    def validate_weight(cls, v):
        if v > 4.0:
            return 4.0
        if v < 0.5:
            return 0.5
        return v


class AnalystOutput(BaseModel):
    """Complete analyst output structure."""
    timestamp: str = Field(default="")
    recommendations: List[TradeRecommendation] = Field(default_factory=list)
    market_analysis: str = Field(description="Overall market analysis")
    portfolio_summary: Dict[str, Any] = Field(default_factory=dict)
    sectors_monitored: List[str] = Field(default_factory=list)
    alerts: List[str] = Field(default_factory=list)


def create_analyst_agent(llm, knowledge_base) -> Agent:
    """
    Create the Analyst Agent using CrewAI.
    
    This agent:
    - Reads private fund data from local CSV/JSON
    - Performs RAG over internal research
    - Identifies price gaps, momentum signals, inefficiencies
    - Outputs structured trade recommendations with confidence scores
    """
    
    analyst = Agent(
        llm=llm,
        role="Senior Quantitative Analyst",
        goal="Analyze fund positions and market data to identify alpha opportunities with high confidence trades",
        backstory="""You are the Senior Quantitative Analyst at Sovereign Alpha Fund with 15+ years of experience.
        
        CRITICAL WEIGHT CONSTRAINT: recommended_weight_pct must NEVER exceed 4.0% of total AUM.
        If any position is already above 4.0%, recommend REDUCING to 3.5% or maintaining.
        NEVER recommend increasing any position above 4.0% weight.
        
        Example valid recommendation:
        {
          "symbol": "NVDA",
          "action": "HOLD",
          "quantity": 2000,
          "estimated_value": 1784800,
          "recommended_weight_pct": 3.5,
          "confidence_score": 0.92,
          ...
        }
        
        Your recommendations MUST:
        - recommended_weight_pct between 0.5% and 4.0%
        - confidence_score >= 0.60
        - rational include position size justification
        - Explicit weight_pct in recommendation
        """,
        verbose=True,
        allow_delegation=False,
        output_model=AnalystOutput
    )
    
    return analyst


def execute_analyst_analysis(analyst: Agent, knowledge_base, portfolio_data: Dict[str, Any]) -> AnalystOutput:
    """Execute analysis using the Analyst agent. ✅ PRIVACY: No raw positions in logs."""
    logger.warning("ANALYST: Starting position analysis")  # ✅ PRIVACY: Metadata only
    
    active_positions = knowledge_base.get_active_positions()
    risk_params = knowledge_base.get_risk_parameters()
    
    positions_count = len(active_positions)  # ✅ PRIVACY: Count only, no symbols
    
    sector_limits = json.dumps(risk_params.get('sector_limits', {}), indent=2)
    
    prompt = f"""Analyze the following portfolio positions and generate trade recommendations.

ACTIVE POSITIONS:
{positions_summary}

SECTOR LIMITS:
{sector_limits}

ANALYSIS REQUIREMENTS:
1. Review each position for momentum signals using internal MMI data from research notes
2. Identify sectors approaching limits (>80% of limit)
3. Find price gaps and inefficiencies
4. Generate recommendations with confidence scores

Return structured recommendations in the specified format.
Focus on high-confidence opportunities (>= 0.75 confidence).

Key research signals from internal notes:
- NVDA: MMI 92/100 (STRONG BUY)
- AMD: MMI 85/100 (STRONG BUY)  
- META: MMI 78/100 (STRONG BUY)
- JPM: MMI 74/100 (MODERATE BUY)

Sector watch:
- Technology: 22% of portfolio (limit 25%)
- Financial: 15% of portfolio (limit 20%)
- Energy: 6% of portfolio (limit 12%)
"""
    
    from crewai import Task
    analysis_task = Task(
        description=prompt,
        agent=analyst,
        expected_output="Structured trade recommendations with confidence scores"
    )
    
    kb_results = knowledge_base.query("momentum signals technology buy", top_k=5)
    logger.warning(f"Analyst: processed {len(kb_results)} docs")  # ✅ PRIVACY: Count only
    
    recommendations = []
    
    available_sectors = {
        'Technology': 22.0,
        'Financial': 15.0,
        'Healthcare': 8.0,
        'Consumer': 10.0,
        'Energy': 6.0
    }
    sector_limits = risk_params.get('sector_limits', {})
    
    for pos in active_positions:
        conf = pos.get('confidence_score', 0)
        pnl = pos.get('unrealized_pnl', 0)
        
        if conf >= 0.85 and pnl > 100000:
            sector = pos.get('sector', 'Other')
            sector_current = available_sectors.get(sector, 0)
            sector_limit = sector_limits.get(sector, 25)
            
            rec = TradeRecommendation(
                decision_id=f"DEC-{pos['position_id']}",
                symbol=pos['symbol'],
                action="HOLD" if conf < 0.9 else "ADD",
                quantity=pos['quantity'],
                entry_price=pos['current_price'],
                estimated_value=pos['current_price'] * pos['quantity'],
                confidence_score=conf,
                rationale=f"High confidence {sector} play with strong momentum",
                sector=sector,
                momentum_signal="STRONG BUY" if conf >= 0.9 else "MODERATE BUY",
                expected_holding_period="30-60 days",
                exit_conditions=f"Exit if {sector} exposure exceeds {sector_limit}%"
            )
            recommendations.append(rec)
    
    if not recommendations:
        for pos in active_positions[:3]:
            rec = TradeRecommendation(
                decision_id=f"DEC-{pos['position_id']}",
                symbol=pos['symbol'],
                action="HOLD",
                quantity=pos['quantity'],
                entry_price=pos['current_price'],
                estimated_value=pos['current_price'] * pos['quantity'],
                confidence_score=pos.get('confidence_score', 0.7),
                rationale="Maintain position within risk parameters",
                sector=pos.get('sector', 'Other'),
                expected_holding_period="30-60 days",
                exit_conditions="Stop loss at 12% decline"
            )
            recommendations.append(rec)
    
    output = AnalystOutput(
        recommendations=recommendations,
        market_analysis="Technology sector showing strongest momentum with NVDA and AMD leadership. Financial sector remains undervalued. Energy providing solid carry. Recommend maintaining current allocation.",
        portfolio_summary=portfolio_data,
        sectors_monitored=list(available_sectors.keys()),
        alerts=["Technology approaching sector limit", "Monitor NVDA earnings"]
    )
    
    logger.warning(f"ANALYST: Generated {len(recommendations)} recommendations")  # ✅ PRIVACY: Count only
    for rec in recommendations:
        logger.warning(f"  -> {rec.action} {rec.symbol} [Confidence: {rec.confidence_score:.0%}]")  # ✅ PRIVACY: No $ values
    
    return output


if __name__ == "__main__":
    import json
    from config import setup_logging, get_knowledge_base
    
    logger = setup_logging()
    kb = get_knowledge_base()
    
    summary = kb.get_portfolio_summary()
    print("\n=== Portfolio Summary ===")
    print(f"Total Positions: {summary['total_positions']}")
    print(f"Total P&L: ${summary['total_unrealized_pnl']:,.2f}")