#!/usr/bin/env python3
"""
Sovereign Alpha - Verify Proof
===========================
Standalone proof verification script.
Usage: python zkml/verify_proof.py zkml/proofs/cert_NVDA_20260503.json
"""

import sys
import json
from pathlib import Path

# Get the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ZKML_DIR = PROJECT_ROOT / "zkml"

sys.path.insert(0, str(PROJECT_ROOT))

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import base64


def verify_proof(cert_path: Path) -> dict:
    """Verify a proof certificate using the public key."""
    
    public_key_file = ZKML_DIR / "keys" / "public_key.pem"
    
    if not public_key_file.exists():
        return {
            "verified": False,
            "error": "Public key not found. Run proof_generator.py first."
        }
    
    with open(public_key_file, "rb") as f:
        public_key = serialization.load_pem_public_key(
            f.read(), backend=default_backend()
        )
    
    # Check multiple locations
    search_paths = [
        cert_path,
        ZKML_DIR / "proofs" / cert_path.name,
        Path(str(cert_path)),
    ]
    
    actual_path = None
    for sp in search_paths:
        if sp.exists():
            actual_path = sp
            break
    
    if not actual_path:
        return {
            "verified": False,
            "error": f"Certificate not found: {cert_path}"
        }
    
    with open(actual_path, "r") as f:
        certificate = json.load(f)
    
    commitment = certificate.get("commitment_hash", "")
    signature_b64 = certificate.get("signature", "")
    
    if not commitment or not signature_b64:
        return {
            "verified": False,
            "error": "Invalid certificate format"
        }
    
    try:
        signature = base64.b64decode(signature_b64)
        hash_bytes = commitment.encode()
        
        public_key.verify(
            signature,
            hash_bytes,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        return {
            "verified": True,
            "certificate_file": str(actual_path.name),
            "decision_id": certificate.get("decision_id"),
            "commitment_hash": commitment,
            "timestamp": certificate.get("timestamp"),
            "verdict": certificate.get("verdict"),
            "policy_results": certificate.get("policy_results"),
            "message": "VERIFIED - RSA signature is valid"
        }
    
    except Exception as e:
        return {
            "verified": False,
            "error": str(e),
            "message": "INVALID - Signature verification failed"
        }


def main():
    """Main entry point."""
    print("=" * 60)
    print("SOVEREIGN ALPHA - Proof Verifier")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nUsage: python zkml/verify_proof.py <certificate_file>")
        print("\nExample: python zkml/verify_proof.py zkml/proofs/cert_NVDA_20260503_143022.json")
        
        proofs_dir = PROJECT_ROOT / "zkml" / "proofs"
        certs = list(proofs_dir.glob("cert_*.json"))
        if certs:
            print(f"\nAvailable certificates ({len(certs)}):")
            for c in certs[-5:]:
                print(f"  - {c.name}")
        
        return 1
    
    cert_path = Path(sys.argv[1])
    
    # If relative, look in zkml/proofs
    if not cert_path.is_absolute():
        cert_path = PROJECT_ROOT / "zkml" / "proofs" / cert_path
    
    print(f"\nVerifying: {cert_path.name}")
    print("-" * 40)
    
    result = verify_proof(cert_path)
    
    if result["verified"]:
        print("\n[VERIFIED]")
        print(f"  Decision ID: {result.get('decision_id')}")
        print(f"  Timestamp:  {result.get('timestamp')}")
        print(f"  Verdict:     {result.get('verdict')}")
        
        policy_results = result.get("policy_results", [])
        if policy_results:
            print(f"\n  Policy Checks:")
            for pr in policy_results:
                status = "PASS" if pr.get("result") == "PASS" else "FAIL"
                print(f"    - {pr.get('check')}: {status}")
        
        print(f"\n  Commitment Hash:")
        print(f"    {result.get('commitment_hash')}")
        
        print(f"\n  Message: {result.get('message')}")
    else:
        print("\n[INVALID]")
        print(f"  Error: {result.get('error')}")
        print(f"  Message: {result.get('message')}")
    
    print("\n" + "=" * 60)
    
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)