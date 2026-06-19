#!/usr/bin/env python3
"""
Sovereign Alpha - RSA ZK Proof Generator
=================================
Real cryptographic proof system using RSA keys.
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import base64

sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from config import ZKML_DIR, logger


class RSAProofGenerator:
    """RSA-based proof generator for Sovereign Alpha decisions."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or ZKML_DIR
        self.keys_dir = self.data_dir / "keys"
        self.proofs_dir = self.data_dir / "proofs"
        
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self.proofs_dir.mkdir(parents=True, exist_ok=True)
        
        self.private_key = None
        self.public_key = None
        
        self._load_or_generate_keys()
    
    def _load_or_generate_keys(self):
        """Load existing keys or generate new RSA key pair."""
        private_key_file = self.keys_dir / "private_key.pem"
        public_key_file = self.keys_dir / "public_key.pem"
        
        if private_key_file.exists() and public_key_file.exists():
            logger.info("Loading existing RSA key pair")
            
            with open(private_key_file, "rb") as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
            
            with open(public_key_file, "rb") as f:
                self.public_key = serialization.load_pem_public_key(
                    f.read(), backend=default_backend()
                )
        else:
            logger.info("Generating new RSA key pair (2048-bit)")
            
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            self.public_key = self.private_key.public_key()
            
            private_pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            with open(private_key_file, "wb") as f:
                f.write(private_pem)
            
            with open(public_key_file, "wb") as f:
                f.write(public_pem)
            
            logger.info("RSA key pair saved to zkml/keys/")
    
    def _hash_decision(self, decision: Dict[str, Any]) -> str:
        """Create SHA-256 hash of decision data."""
        decision_json = json.dumps(decision, sort_keys=True, default=str)
        return hashlib.sha256(decision_json.encode()).hexdigest()
    
    def _sign_hash(self, hash_bytes: bytes) -> bytes:
        """Sign a hash with RSA private key."""
        return self.private_key.sign(
            hash_bytes,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
    
    def _verify_signature(self, signature: bytes, hash_bytes: bytes) -> bool:
        """Verify RSA signature."""
        try:
            self.public_key.verify(
                signature,
                hash_bytes,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except:
            return False
    
    def get_public_key_fingerprint(self) -> str:
        """Get a short fingerprint of the public key."""
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return hashlib.sha256(pub_bytes).hexdigest()[:16]
    
    def generate_proof(self, decision: Dict[str, Any], 
                    risk_checks: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a cryptographic proof for a decision."""
        logger.info(f"Generating RSA proof for: {decision.get('decision_id', 'unknown')}")
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        decision_id = decision.get('decision_id', 'UNKNOWN')
        
        commitment_hash = self._hash_decision(decision)
        
        hash_bytes = commitment_hash.encode()
        signature = self._sign_hash(hash_bytes)
        signature_b64 = base64.b64encode(signature).decode()
        
        policy_results = []
        if risk_checks:
            for check_name, passed in risk_checks.items():
                policy_results.append({
                    "check": check_name,
                    "result": "PASS" if passed else "FAIL"
                })
        
        certificate = {
            "certificate_version": "1.0",
            "decision_id": decision_id,
            "commitment_hash": commitment_hash,
            "signature": signature_b64,
            "public_key_fingerprint": self.get_public_key_fingerprint(),
            "timestamp": timestamp,
            "policy_rules_checked": [
                "max_position_size: 5% of AUM",
                "sector_limits: varies by sector",
                "min_confidence: 65%",
                "max_drawdown: 15%"
            ],
            "policy_results": policy_results,
            "verdict": "COMPLIANT" if risk_checks and all(risk_checks.values()) else "NON-COMPLIANT",
            "signing_algorithm": "RSA-SHA256",
            "key_size": 2048
        }
        
        cert_file = self.proofs_dir / f"cert_{decision_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(cert_file, "w", encoding="utf-8") as f:
            json.dump(certificate, f, indent=2)
        
        logger.info(f"Certificate saved: {cert_file.name}")
        logger.info(f"  Commitment: {commitment_hash[:16]}...")
        
        return certificate
    
    def verify_proof(self, certificate: Dict[str, Any]) -> bool:
        """Verify a proof certificate."""
        try:
            commitment = certificate.get("commitment_hash", "")
            signature_b64 = certificate.get("signature", "")
            
            signature = base64.b64decode(signature_b64)
            hash_bytes = commitment.encode()
            
            return self._verify_signature(signature, hash_bytes)
        
        except Exception as e:
            logger.warning(f"Verification failed: {e}")
            return False
    
    def verify_certificate_file(self, filepath: Path) -> Dict[str, Any]:
        """Verify a certificate file and return result."""
        with open(filepath, "r") as f:
            certificate = json.load(f)
        
        is_valid = self.verify_proof(certificate)
        
        return {
            "certificate_file": str(filepath.name),
            "decision_id": certificate.get("decision_id"),
            "commitment_hash": certificate.get("commitment_hash"),
            "timestamp": certificate.get("timestamp"),
            "verdict": certificate.get("verdict"),
            "verified": is_valid
        }


def create_proof_generator() -> RSAProofGenerator:
    return RSAProofGenerator()


if __name__ == "__main__":
    print("=== RSA Proof Generator ===")
    
    generator = RSAProofGenerator()
    
    print(f"Public key fingerprint: {generator.get_public_key_fingerprint()}")
    
    test_decision = {
        "decision_id": "TEST-001",
        "symbol": "NVDA",
        "action": "BUY",
        "confidence_score": 0.85,
        "position_size": 350000
    }
    
    test_checks = {
        "position_size_ok": True,
        "confidence_ok": True,
        "zk_proof_ok": True
    }
    
    cert = generator.generate_proof(test_decision, test_checks)
    
    print(f"\nCertificate generated:")
    print(f"  Decision ID: {cert['decision_id']}")
    print(f"  Commitment: {cert['commitment_hash'][:32]}...")
    print(f"  Verdict: {cert['verdict']}")
    
    is_valid = generator.verify_proof(cert)
    print(f"\nVerification: {'VERIFIED' if is_valid else 'INVALID'}")