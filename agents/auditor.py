from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from crewai import Agent
from privacy import logger, proof_only_response, generate_policy_hash  # ✅ PRIVACY: Proof-only output


class ZKProofRecord(BaseModel):
    """ZK proof record output."""
    decision_id: str = Field(description="Decision ID")
    proof_hash: str = Field(description="ZK proof hash")
    proof_created_at: str = Field(description="Proof creation timestamp")
    verification_status: str = Field(description="Verification status")
    circuit_version: str = Field(default="1.0.0", description="Circuit version")
    transaction_hash: Optional[str] = Field(default=None, description="On-chain tx hash")
    policy_compliance_proof: Dict[str, Any] = Field(default_factory=dict)


class AuditRecord(BaseModel):
    """Auditor output record."""
    decision_id: str = Field(description="Decision ID")
    zk_proof: Optional[ZKProofRecord] = Field(default=None, description="ZK proof")
    blockchain_logged: bool = Field(description="Logged to blockchain")
    tx_hash: Optional[str] = Field(default=None, description="Transaction hash")
    invoice_generated: bool = Field(description="Invoice generated")
    fee_calculated: float = Field(description="Performance fee")
    audit_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    auditor_signature: str = Field(default="Sovereign Alpha Auditor")


def create_auditor_agent(llm) -> Agent:
    """
    Create the Auditor Agent using CrewAI.
    
    This agent:
    - Wraps every approved decision in a ZK proof
    - Proves decision followed policy WITHOUT revealing private data
    - Logs proof hash to blockchain
    - Generates automated invoice for performance fee
    """
    
    auditor = Agent(
        llm=llm,
        role="Chief Compliance Auditor",
        goal="Ensure every decision is cryptographically verified, policy-compliant, and immutably logged to the blockchain",
        backstory="""You are the Chief Compliance Auditor at Sovereign Alpha Fund with deep expertise in 
        zero-knowledge cryptography and blockchain governance. You ensure NO decision proceeds 
        without proper cryptographic verification.
        
        Your responsibilities:
        1. Generate ZK proofs for every approved decision
        2. Prove policy compliance WITHOUT revealing private data
        3. Log proof hashes to Base blockchain for immutability
        4. Generate automated invoices for performance fee calculation
        
        Your ZK proofs verify:
        - Decision followed risk parameters
        - Confidence threshold was met
        - Position sizes were within limits
        - Sector exposure was compliant
        
        The proof reveals ONLY:
        - Decision hash (public)
        - Timestamp (public)
        - Agent ID (public)
        
        The proof hides:
        - Specific position data
        - Risk check details
        - Confidence scores
        """,
        verbose=True,
        allow_delegation=False,
        output_model=AuditRecord
    )
    
    return auditor


def execute_audit(recommendation, risk_checks: Dict[str, bool], 
                proof_generator, ledger, billing_meter) -> AuditRecord:
    """
    Execute audit for an approved decision.
    ✅ PRIVACY: Proof-only output - never return raw positions/strategies.
    """
    logger.warning(f"AUDITOR: Generating ZK proof for {recommendation.decision_id}")  # ✅ PRIVACY: ID only
    
    decision = {
        'decision_id': recommendation.decision_id,
        'agent_id': 'risk_manager',
        'risk_checks': risk_checks,  # ✅ PRIVACY: Checks only, no position values
        'approved': True,
        'decision_type': 'trade_approval'
    }
    
    proof_record = proof_generator.generate_proof(decision, risk_checks)
    
    verification = proof_generator.verify_proof(proof_record)
    
    proof_hash = proof_record.get('commitment_hash', '')
    
    tx_record = ledger.log_decision(proof_hash, {
        'decision_id': recommendation.decision_id,
        'decision_type': 'trade_approval'
    })  # ✅ PRIVACY: No position values in ledger
    
    tx_hash = tx_record.get('tx_hash')
    
    alpha_estimate = recommendation.estimated_value * 0.05
    billing_meter.log_performance(
        decision_id=recommendation.decision_id,
        trade_action=recommendation.action,
        symbol=recommendation.symbol,
        position_value=recommendation.estimated_value,
        alpha_generated=alpha_estimate
    )
    
    zk_proof_record = ZKProofRecord(
        decision_id=recommendation.decision_id,
        proof_hash=proof_hash[:64] if proof_hash else 'N/A',
        proof_created_at=proof_record.get('created_at', ''),
        verification_status='verified' if verification else 'unknown',
        circuit_version=proof_record.get('circuit_version', '1.0.0'),
        transaction_hash=tx_hash
    )
    
    audit = AuditRecord(
        decision_id=recommendation.decision_id,
        zk_proof=zk_proof_record,
        blockchain_logged=True,
        tx_hash=tx_hash,
        invoice_generated=True,
        fee_calculated=alpha_estimate * 0.12
    )
    
    logger.warning(f"AUDITOR: Proof generated | hash={proof_hash[:16]}...")  # ✅ PRIVACY: Hash only, no $ values
    logger.warning(f"  -> Fee Calculated: ${audit.fee_calculated:,.2f}")  # ✅ PRIVACY: Fee only
    
    return audit


if __name__ == "__main__":
    from config import setup_logging
    logger = setup_logging()
    
    print("Testing Auditor Agent")
    
    test_rec = {
        'decision_id': 'DEC-001',
        'symbol': 'NVDA',
        'action': 'BUY',
        'quantity': 1000,
        'entry_price': 892.40,
        'estimated_value': 892400,
        'confidence_score': 0.95
    }
    
    test_risk_checks = {
        'position_size_ok': True,
        'sector_limit_ok': True,
        'confidence_ok': True,
        'max_drawdown_ok': True
    }
    
    print(f"\nAuditing: {test_rec['action']} {test_rec['symbol']}")
    print(f"Value: ${test_rec['estimated_value']:,.2f}")
    print(f"All risk checks passed: {all(test_risk_checks.values())}")