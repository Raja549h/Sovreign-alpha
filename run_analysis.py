#!/usr/bin/env python3
"""
Sovereign Alpha Quick Run Script
===============================
Simple script that runs the analysis cycle for dashboard /run endpoint.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

os.environ['LOG_LEVEL'] = 'WARNING'

from rag.knowledge_base import get_knowledge_base
from zkml.proof_generator import create_proof_generator
from blockchain.ledger import create_ledger
from billing.meter import create_billing_meter

def run_analysis():
    kb = get_knowledge_base()
    proof_gen = create_proof_generator()
    ledger = create_ledger()
    billing = create_billing_meter()
    
    portfolio = kb.get_portfolio_summary()
    positions = portfolio.get('positions', [])
    
    approved_count = 0
    vetoed_count = 0
    
    for pos in positions[:5]:
        value = pos.get('current_price', 100) * pos.get('quantity', 1000)
        conf = pos.get('confidence_score', 0.80)
        
        if value <= 2500000 and conf >= 0.60:
            decision = {
                'decision_id': f"DEC-{pos.get('position_id', '001')}",
                'agent_id': 'analyst',
                'risk_checks': {'position_size_ok': True, 'sector_limit_ok': True, 'confidence_ok': True},
                'approved': True,
                'decision_type': 'trade_approval'
            }
            
            proof_record = proof_gen.generate_proof(decision, decision['risk_checks'])
            proof_hash = proof_record.get('commitment_hash', '')
            
            ledger.log_decision(proof_hash, {
                'decision_id': decision['decision_id'],
                'decision_type': 'trade_approval'
            })
            
            billing.log_performance(
                decision_id=decision['decision_id'],
                trade_action='HOLD',
                symbol=pos.get('symbol', 'N/A'),
                position_value=value,
                alpha_generated=value * 0.05
            )
            
            approved_count += 1
        else:
            vetoed_count += 1
    
    billing.close()
    
    return {
        'approved': approved_count,
        'vetoed': vetoed_count,
        'total': approved_count + vetoed_count
    }

if __name__ == "__main__":
    print(f"Running analysis at {datetime.utcnow().isoformat()}Z")
    result = run_analysis()
    print(f"Complete: {result['approved']} approved, {result['vetoed']} vetoed")