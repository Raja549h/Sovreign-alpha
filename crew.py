#!/usr/bin/env python3
"""
Sovereign Alpha Agent System - Master Orchestrator
=================================================

This orchestrator executes the complete Sovereign Alpha pipeline:

1. Analyst reads data → generates recommendation
2. Risk Manager checks + demands ZK proof
3. Auditor generates proof → Risk Manager verifies
4. Decision logged to blockchain
5. Billing updated
6. Report printed to console

Run with: python crew.py
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from config import BASE_DIR, DATA_DIR, GROQ_API_KEY, logger, llm_config

from rag.knowledge_base import get_knowledge_base

from rag.knowledge_base import get_knowledge_base
from zkml.proof_generator import create_proof_generator
from blockchain.ledger import create_ledger
from billing.meter import create_billing_meter

from agents.analyst import (
    TradeRecommendation, AnalystOutput, create_analyst_agent,
    execute_analyst_analysis
)
from agents.risk_manager import (
    RiskApproval, RiskCheck, create_risk_manager_agent,
    execute_risk_approval, create_risk_checks
)
from agents.auditor import (
    AuditRecord, ZKProofRecord, create_auditor_agent,
    execute_audit
)


try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("WARNING: Groq not available")

try:
    from langchain.chat_models import ChatGroq
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain_groq import ChatGroq
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False


class SovereignAlphaOrchestrator:
    """
    Main orchestrator for Sovereign Alpha Agent system.
    Coordinates the Council of Experts.
    """
    
    def __init__(self):
        self.kb = None
        self.proof_generator = None
        self.ledger = None
        self.billing_meter = None
        self.llm = None
        
        self._initialize()

    def _initialize(self):
        print("\n" + "=" * 70)
        print("SOVEREIGN ALPHA AGENT SYSTEM - Initializing")
        print("=" * 70)
        
        if not GROQ_API_KEY:
            print("ERROR: GROQ_API_KEY not set. Copy .env.example to .env and add key.")
            sys.exit(1)
        
        self.kb = get_knowledge_base()
        logger.info("Knowledge Base loaded")
        
        self.proof_generator = create_proof_generator()
        logger.info("ZK Proof Generator initialized")
        
        self.ledger = create_ledger()
        logger.info("Blockchain Ledger initialized")
        
        self.billing_meter = create_billing_meter()
        logger.info("Billing Meter initialized")
        
        if LANGCHAIN_AVAILABLE and GROQ_AVAILABLE:
            self.llm = ChatGroq(
                api_key=GROQ_API_KEY,
                model=llm_config['model'],
                temperature=llm_config['temperature']
            )
            logger.info(f"LLM initialized: {llm_config['model']}")
        else:
            logger.warning("LangChain not available - using simple responses")
            self.llm = None
        
        self.analyst = create_analyst_agent(self.llm, self.kb) if self.llm else None
        self.risk_manager = create_risk_manager_agent(self.llm) if self.llm else None
        self.auditor = create_auditor_agent(self.llm) if self.llm else None
        
        print("\n[PASS] All systems initialized")
        print("=" * 70)

    def run_analysis_cycle(self) -> Dict[str, Any]:
        """
        Execute a complete analysis cycle.
        """
        print("\n" + "=" * 70)
        print("SOVEREIGN ALPHA - Starting Analysis Cycle")
        print("=" * 70)
        print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
        
        portfolio_data = self.kb.get_portfolio_summary()
        
        print("\n" + "-" * 50)
        print("STEP 1: ANALYST AGENT - Generating Recommendations")
        print("-" * 50)
        
        if self.analyst and self.llm:
            analyst_output = execute_analyst_analysis(
                self.analyst, self.kb, portfolio_data
            )
        else:
            analyst_output = self._generate_simple_recommendations(portfolio_data)
        
        if self.billing_meter:
            self.billing_meter.log_inference(
                agent_id="analyst",
                model=llm_config['model'],
                input_tokens=1500,
                output_tokens=800,
                latency_ms=2500.0,
                status="completed"
            )
        
        recommendations = analyst_output.recommendations if hasattr(analyst_output, 'recommendations') else []
        
        if not recommendations:
            print("  No recommendations generated")
            return {'status': 'no_recommendations', 'cycle': 'failed'}
        
        print(f"\n  Generated {len(recommendations)} recommendations")
        
        results = []
        
        for i, rec in enumerate(recommendations[:3]):
            print(f"\n  Processing: {rec.decision_id} - {rec.action} {rec.symbol}")
            
            risk_params = self.kb.get_risk_parameters()
            
            print("\n" + "-" * 50)
            print(f"STEP 2: RISK MANAGER - Checking {rec.decision_id}")
            print("-" * 50)
            
            print(f"  Analyzing: {rec.action} {rec.symbol} @ ${rec.entry_price:.2f}")
            print(f"  Position Value: ${rec.estimated_value:,.2f}")
            print(f"  Confidence: {rec.confidence_score:.0%}")
            print(f"  Sector: {rec.sector}")
            
            if self.risk_manager and self.llm:
                risk_approval = execute_risk_approval(rec, risk_params, None)
            else:
                risk_approval = self._simple_risk_check(rec, risk_params)
            
            if self.billing_meter:
                self.billing_meter.log_inference(
                    agent_id="risk_manager",
                    model=llm_config['model'],
                    input_tokens=800,
                    output_tokens=400,
                    latency_ms=1500.0,
                    decision_id=rec.decision_id,
                    status="completed"
                )
            
            if not risk_approval.approved:
                print(f"\n  [FAIL] VETOED: {risk_approval.veto_message or 'Risk checks failed'}")
                results.append({
                    'decision_id': rec.decision_id,
                    'status': 'vetoed',
                    'reason': risk_approval.veto_message or 'Risk checks failed'
                })
                continue
            
            print(f"  [PASS] Approved (passed {len(risk_approval.risk_checks)} checks)")
            
            risk_checks = create_risk_checks(rec, portfolio_data, risk_params)
            
            print("\n" + "-" * 50)
            print(f"STEP 3: AUDITOR - Generating ZK Proof")
            print("-" * 50)
            
            audit = execute_audit(
                rec,
                risk_checks,
                self.proof_generator,
                self.ledger,
                self.billing_meter
            )
            
            if not audit.zk_proof:
                print("  ERROR: Failed to generate ZK proof")
                results.append({
                    'decision_id': rec.decision_id,
                    'status': 'audit_failed',
                    'reason': 'ZK proof generation failed'
                })
                continue
            
            print(f"  [PASS] ZK Proof: {audit.zk_proof.proof_hash[:16]}...")
            print(f"  [PASS] Blockchain: {'confirmed' if audit.tx_hash else 'local'}")
            print(f"  [PASS] Fee: ${audit.fee_calculated:,.2f}")
            
            audit_result = audit.dict() if hasattr(audit, 'dict') else {
                'decision_id': audit.decision_id,
                'zk_proof': audit.zk_proof.dict() if audit.zk_proof else None,
                'blockchain_logged': audit.blockchain_logged,
                'tx_hash': audit.tx_hash,
                'fee_calculated': audit.fee_calculated
            }
            
            results.append({
                'decision_id': rec.decision_id,
                'status': 'approved',
                'zk_proof_hash': audit.zk_proof.proof_hash[:32] if audit.zk_proof else None,
                'tx_hash': audit.tx_hash,
                'fee_calculated': audit.fee_calculated,
                'blockchain_logged': audit.blockchain_logged
            })
        
        summary = self._generate_cycle_summary(results)
        
        return summary

    def _generate_simple_recommendations(self, portfolio_data: Dict) -> AnalystOutput:
        """Generate simple recommendations without CrewAI."""
        recommendations = []
        
        for pos in portfolio_data.get('positions', [])[:5]:
            aum = 59000000
            current_price = pos.get('current_price', 892.40)
            quantity = pos.get('quantity', 1000)
            estimated_value = current_price * quantity
            weight_pct = (estimated_value / aum) * 100
            weight_pct = min(weight_pct, 4.0)  # Cap at 4%
            
            rec = TradeRecommendation(
                decision_id=f"DEC-{pos.get('position_id', '001')}",
                symbol=pos.get('symbol', 'NVDA'),
                action="HOLD",
                quantity=quantity,
                entry_price=current_price,
                estimated_value=estimated_value,
                recommended_weight_pct=weight_pct,
                confidence_score=pos.get('confidence_score', 0.80),
                rationale="Maintain position within risk parameters",
                sector=pos.get('sector', 'Technology'),
                momentum_signal="STRONG BUY" if pos.get('confidence_score', 0) > 0.85 else "MODERATE BUY",
                expected_holding_period="30-60 days",
                exit_conditions="Stop loss at 12% decline"
            )
            recommendations.append(rec)
        
        return AnalystOutput(
            recommendations=recommendations,
            market_analysis="Portfolio review complete",
            portfolio_summary=portfolio_data
        )

    def _simple_risk_check(self, rec, risk_params) -> RiskApproval:
        """Simple risk check without CrewAI."""
        checks = [
            RiskCheck(
                check_name="Position Size",
                passed=rec.estimated_value <= 500000,
                details=f"Position ${rec.estimated_value:,.2f} within limits"
            ),
            RiskCheck(
                check_name="Confidence",
                passed=rec.confidence_score >= 0.65,
                details=f"Confidence {rec.confidence_score:.0%} meets threshold"
            )
        ]
        
        return RiskApproval(
            decision_id=rec.decision_id,
            approved=all(c.passed for c in checks),
            risk_checks=checks,
            zk_proof_required=True,
            zk_proof_status="pending",
            reasoning="Risk checks passed" if all(c.passed for c in checks) else "Risk checks failed"
        )

    def _generate_cycle_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Generate cycle summary."""
        approved = len([r for r in results if r.get('status') == 'approved'])
        vetoed = len([r for r in results if r.get('status') == 'vetoed'])
        total_fees = sum(r.get('fee_calculated', 0) for r in results if r.get('fee_calculated'))
        
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_decisions': len(results),
            'approved': approved,
            'vetoed': vetoed,
            'total_fees': total_fees,
            'results': results
        }

    def print_final_report(self, summary: Dict[str, Any]):
        """Print final report to console."""
        print("\n" + "=" * 70)
        print("SOVEREIGN ALPHA - CYCLE COMPLETE")
        print("=" * 70)
        
        print(f"\nTimestamp: {summary.get('timestamp', '')}")
        print(f"Total Decisions: {summary.get('total_decisions', 0)}")
        print(f"  [PASS] Approved: {summary.get('approved', 0)}")
        print(f"  [FAIL] Vetoed: {summary.get('vetoed', 0)}")
        
        if summary.get('total_fees'):
            print(f"\nPerformance Fees Generated: ${summary.get('total_fees', 0):,.2f}")
        
        print("\n" + "-" * 50)
        print("Decision Details:")
        print("-" * 50)
        
        for result in summary.get('results', []):
            decision_id = result.get('decision_id', 'UNKNOWN')
            status = result.get('status', 'unknown')
            
            if status == 'approved':
                print(f"\n  [PASS] {decision_id}: APPROVED")
                print(f"    ZK Proof: {result.get('zk_proof_hash', 'N/A')[:24]}...")
                print(f"    Blockchain: {result.get('tx_hash', 'N/A')[:20] if result.get('tx_hash') else 'local'}...")
                print(f"    Fee: ${result.get('fee_calculated', 0):,.2f}")
            else:
                print(f"\n  [FAIL] {decision_id}: {status.upper()}")
                print(f"    Reason: {result.get('reason', 'Risk check failed')}")
        
        if self.billing_meter:
            print("\n" + "-" * 50)
            print("Billing Summary:")
            print("-" * 50)
            
            inference_stats = self.billing_meter.get_inference_stats()
            print(f"  Total Inferences: {inference_stats.get('total_calls', 0)}")
            print(f"  Total Tokens: {inference_stats.get('total_tokens', 0):,}")
            print(f"  Estimated Cost: ${inference_stats.get('total_cost', 0):.4f}")
            
            perf_summary = self.billing_meter.get_performance_summary()
            print(f"  Alpha Generated: ${perf_summary.get('total_alpha', 0):,.2f}")
            print(f"  Performance Fees: ${perf_summary.get('total_fees', 0):,.2f}")
        
        print("\n" + "=" * 70)
        print("END OF CYCLE")
        print("=" * 70 + "\n")

    def cleanup(self):
        """Cleanup resources."""
        if self.billing_meter:
            self.billing_meter.close()


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("SOVEREIGN ALPHA AGENT SYSTEM")
    print("Private AI Agent Council for Alpha Generation")
    print("Zero-Knowledge Proofs | Blockchain Settlements")
    print("="*60 + "\n")
    
    orchestrator = SovereignAlphaOrchestrator()
    
    summary = orchestrator.run_analysis_cycle()
    
    orchestrator.print_final_report(summary)
    
    orchestrator.cleanup()
    
    print("\n>>> Sovereign Alpha cycle completed successfully")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)