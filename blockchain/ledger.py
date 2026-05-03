import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from config import BLOCKCHAIN_DIR, WEB3_RPC_URL, PRIVATE_KEY, WALLET_ADDRESS, logger

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("WARNING: web3.py not available")


class BlockchainLedger:
    """
    Blockchain Ledger for Sovereign Alpha Fund.
    
    Records proof hashes to Base testnet (Sepolia).
    Provides immutable audit trail for all decisions.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or BLOCKCHAIN_DIR
        self.tx_dir = self.data_dir / "transactions"
        self.tx_dir.mkdir(parents=True, exist_ok=True)
        
        self.w3: Optional[Any] = None
        self.account = None
        self.chain_id: int = 84532
        
        self.local_ledger: List[Dict[str, Any]] = []
        
        self._initialize()

    def _initialize(self):
        logger.info("Initializing Blockchain Ledger...")
        
        if not WEB3_AVAILABLE:
            logger.warning("web3.py not available, using local ledger")
            return

        try:
            self.w3 = Web3(Web3.HTTPProvider(WEB3_RPC_URL))
            
            if self.w3.is_connected():
                logger.info(f"Connected to Base Sepolia: {self.w3.eth.chain_id}")
                self.chain_id = self.w3.eth.chain_id or 84532
            
            if PRIVATE_KEY and WALLET_ADDRESS:
                from eth_account import Account
                self.account = Account.from_key(PRIVATE_KEY)
                logger.info(f"Wallet configured: {WALLET_ADDRESS[:10]}...")
            else:
                logger.warning("No wallet configured - using local ledger only")
                
        except Exception as e:
            logger.warning(f"Web3 setup failed: {e}, using local ledger")
            self.w3 = None

    def log_decision(self, proof_hash: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log a decision proof hash to the ledger.
        Attempts on-chain transaction first, falls back to local.
        """
        decision_id = metadata.get('decision_id', 'UNKNOWN')
        logger.info(f"Logging decision to ledger: {decision_id}")
        
        tx_record = {
            'decision_id': decision_id,
            'proof_hash': proof_hash,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'metadata': metadata,
            'tx_hash': None,
            'status': 'pending',
            'block_number': None,
            'network': 'base-sepolia' if self.w3 else 'local'
        }
        
        if self.w3 and self.account:
            try:
                tx_hash = self._send_transaction(proof_hash, metadata)
                tx_record['tx_hash'] = tx_hash
                tx_record['status'] = 'confirmed'
                
                logger.info(f"Transaction sent: {tx_hash[:20]}...")
                
            except Exception as e:
                logger.warning(f"On-chain tx failed: {e}, using local ledger")
                tx_record = self._save_local_transaction(tx_record)
        else:
            tx_record = self._save_local_transaction(tx_record)
        
        self.local_ledger.append(tx_record)
        return tx_record

    def _send_transaction(self, proof_hash: str, metadata: Dict[str, Any]) -> str:
        """Send transaction to Base testnet."""
        if not self.w3 or not self.account:
            raise ValueError("Web3 or account not initialized")
        
        message = f"Sovereign Alpha Decision: {metadata.get('decision_id', '')}"
        
        tx = {
            'from': self.account.address,
            'to': self.account.address,
            'value': 0,
            'data': Web3.to_bytes(hexstr=proof_hash[:64]),
            'chainId': self.chain_id,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 21000,
            'gasPrice': self.w3.eth.gas_price
        }
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        return tx_hash.hex()

    def _save_local_transaction(self, tx_record: Dict[str, Any]) -> Dict[str, Any]:
        """Save transaction to local ledger file."""
        decision_id = tx_record['decision_id']
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"tx_{decision_id}_{timestamp}.json"
        
        filepath = self.tx_dir / filename
        
        tx_record['tx_hash'] = self._generate_local_tx_hash(tx_record)
        tx_record['status'] = 'local'
        
        with open(filepath, 'w') as f:
            json.dump(tx_record, f, indent=2, default=str)
        
        logger.info(f"Local transaction saved: {tx_record['tx_hash'][:16]}...")
        
        return tx_record

    def _generate_local_tx_hash(self, tx_record: Dict[str, Any]) -> str:
        """Generate deterministic tx hash for local transactions."""
        import hashlib
        
        data = f"{tx_record['decision_id']}{tx_record['proof_hash']}{tx_record['timestamp']}"
        return "0x" + hashlib.sha256(data.encode()).hexdigest()[:64]

    def get_transaction(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve transaction by decision ID."""
        for tx in self.local_ledger:
            if tx.get('decision_id') == decision_id:
                return tx
        
        return None

    def get_all_transactions(self) -> List[Dict[str, Any]]:
        """Get all transactions from ledger."""
        return self.local_ledger

    def verify_on_chain(self, tx_hash: str) -> Dict[str, Any]:
        """Verify transaction exists on chain."""
        if not self.w3:
            return {'verified': False, 'reason': 'no_web3_connection'}
        
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            return {
                'verified': receipt is not None,
                'block_number': receipt.get('blockNumber') if receipt else None,
                'confirmations': 1 if receipt else 0,
                'status': 'confirmed' if receipt else 'not_found'
            }
            
        except Exception as e:
            return {'verified': False, 'reason': str(e)}

    def get_ledger_summary(self) -> Dict[str, Any]:
        """Get summary of ledger activity."""
        total = len(self.local_ledger)
        confirmed = len([tx for tx in self.local_ledger if tx.get('status') == 'confirmed'])
        local = len([tx for tx in self.local_ledger if tx.get('status') == 'local'])
        
        return {
            'total_transactions': total,
            'on_chain': confirmed,
            'local': local,
            'network': 'base-sepolia' if self.w3 else 'local_only',
            'chain_id': self.chain_id
        }


def create_ledger() -> BlockchainLedger:
    return BlockchainLedger()


if __name__ == "__main__":
    ledger = create_ledger()
    
    print("\n=== Testing Blockchain Ledger ===")
    
    test_metadata = {
        'decision_id': 'DEC-001',
        'decision_type': 'trade_approval',
        'symbol': 'NVDA',
        'action': 'BUY',
        'quantity': 1000,
        'value_usd': 892400
    }
    
    test_proof_hash = "0x" + "a" * 64
    
    result = ledger.log_decision(test_proof_hash, test_metadata)
    
    print(f"Decision ID: {result['decision_id']}")
    print(f"Transaction Hash: {result['tx_hash'][:20] if result['tx_hash'] else 'N/A'}...")
    print(f"Status: {result['status']}")
    
    print("\n=== Ledger Summary ===")
    summary = ledger.get_ledger_summary()
    print(f"Total Transactions: {summary['total_transactions']}")
    print(f"On-Chain: {summary['on_chain']}")
    print(f"Local: {summary['local']}")
    print(f"Network: {summary['network']}")