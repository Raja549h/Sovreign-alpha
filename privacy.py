# privacy.py - Sovereign Alpha Privacy & Security Module
# Zero raw data in logs, Fernet encryption, tenant isolation, proof-only output

import os
import sys
import hashlib
import logging
import base64
import time
from datetime import datetime
from typing import Optional, Any, Dict, List
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    FERNET_AVAILABLE = True
except ImportError:
    FERNET_AVAILABLE = False

FERNET_KEY = os.environ.get("FERNET_KEY", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "")

_fernet: Optional[Fernet] = None

def _get_fernet() -> Optional[Fernet]:
    global _fernet
    if not FERNET_AVAILABLE:
        return None
    if _fernet is None and FERNET_KEY:
        _fernet = Fernet(FERNET_KEY.encode())
    return _fernet

def setup_privacy_logger(name: str = "sovereign_alpha", level: int = logging.WARNING) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_privacy_logger()

def sanitize_log_data(data: Dict[str, Any], tenant_id: str = "unknown") -> Dict[str, Any]:
    safe_keys = {'count', 'status', 'id', 'timestamp', 'type', 'source'}
    return {k: v for k, v in data.items() if k.lower() in safe_keys}

def log_safe(logger: logging.Logger, level: int, msg: str, **kwargs):
    safe_kwargs = sanitize_log_data(kwargs)
    logger.log(level, f"{msg} | tenant={safe_kwargs.get('tenant_id', 'unknown')}")

def encrypt_data(data: bytes) -> bytes:
    f = _get_fernet()
    if f:
        return f.encrypt(data)
    return data

def decrypt_data(data: bytes) -> bytes:
    f = _get_fernet()
    if f:
        return f.decrypt(data)
    return data

def encrypt_json(data: Dict) -> str:
    import json
    json_bytes = json.dumps(data).encode()
    encrypted = encrypt_data(json_bytes)
    return base64.b64encode(encrypted).decode()

def decrypt_json(data: str) -> Dict:
    encrypted = base64.b64decode(data.encode())
    decrypted = decrypt_data(encrypted)
    import json
    return json.loads(decrypted.decode())

class TenantScopedData:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.prefix = f"tenant_{tenant_id}_"
    
    def scope_key(self, key: str) -> str:
        return f"{self.prefix}{key}"
    
    def scope_collection(self, collection: str) -> str:
        return f"{self.prefix}{collection}"
    
    def scope_db_table(self, table: str) -> str:
        return f"{self.prefix}{table}"

def generate_proof(decision_id: str, policy_hash: str, timestamp: Optional[str] = None) -> Dict[str, Any]:
    ts = timestamp or datetime.utcnow().isoformat() + 'Z'
    data = f"{decision_id}|{policy_hash}|{ts}"
    proof_hash = hashlib.sha256(data.encode()).hexdigest()
    return {
        "proof": f"0x{proof_hash}",
        "policy_compliant": True,
        "timestamp": ts,
        "version": "1.0"
    }

def generate_policy_hash(risk_params: Dict, governance: Dict) -> str:
    policy_data = {
        "max_position": risk_params.get("max_position_size_pct", 4.5),
        "sectors": list(risk_params.get("sector_limits", {}).keys()),
        "min_confidence": governance.get("min_confidence_score", 0.60)
    }
    import json
    return hashlib.sha256(json.dumps(policy_data, sort_keys=True).encode()).hexdigest()

def proof_only_response(decision_id: str, compliant: bool, fee: float = 0.0) -> Dict[str, Any]:
    return {
        "proof": f"0x{hashlib.sha256(decision_id.encode()).hexdigest()[:64]}",
        "policy_compliant": compliant,
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "fee_charged": fee if compliant else 0.0,
        "status": "verified" if compliant else "rejected"
    }

def clear_sensitive(obj: Any) -> None:
    if hasattr(obj, '__dict__'):
        for key in list(obj.__dict__.keys()):
            if any(s in key.lower() for s in ['key', 'secret', 'token', 'password']):
                obj.__dict__['key'] = None

def validate_secrets(required: List[str] = None) -> bool:
    if required is None:
        required = ['FERNET_KEY']
    missing = [s for s in required if not os.environ.get(s)]
    if missing:
        logger.warning(f"Missing secrets (ok for dev): {missing}")
        return False
    return True

def safe_error_response(e: Exception) -> Dict[str, Any]:
    logger.error(f"Error occurred | type={type(e).__name__}")
    return {
        "error": "An error occurred",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "status": "failed"
    }

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _get_jwt_secret() -> str:
    secret = JWT_SECRET or os.environ.get('SECRET_KEY')
    if not secret:
        raise RuntimeError("JWT_SECRET or SECRET_KEY environment variable must be set in production")
    return secret

def create_session_token(fund_id: str) -> str:
    secret = _get_jwt_secret()
    token_data = f"{fund_id}:{int(time.time())}"
    signature = hashlib.sha256(f"{token_data}:{secret}".encode()).hexdigest()
    return base64.b64encode(f"{token_data}:{signature}".encode()).decode()

_revoked_tokens = set()

def revoke_token(token: str):
    _revoked_tokens.add(token)

def verify_session_token(token: str) -> Optional[str]:
    if token in _revoked_tokens:
        return None
    try:
        secret = _get_jwt_secret()
        decoded = base64.b64decode(token.encode()).decode()
        parts = decoded.rsplit(':', 1)
        if len(parts) != 2:
            return None
        token_data, provided_sig = parts
        expected_sig = hashlib.sha256(f"{token_data}:{secret}".encode()).hexdigest()
        if provided_sig == expected_sig:
            fund_id = token_data.split(':')[0]
            timestamp = int(token_data.split(':')[1])
            if time.time() - timestamp > 86400:
                return None
            return fund_id
        return None
    except Exception:
        return None

def validate_password(input_password: str, stored_password: str = None) -> bool:
    import hmac
    fund_password = os.environ.get("FUND_PASSWORD", "")
    return hmac.compare_digest(input_password.encode('utf-8'), fund_password.encode('utf-8'))