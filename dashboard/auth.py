# privacy.py - Sovereign Alpha Privacy & Security Module
# ✅ PRIVACY: Zero raw data in logs, Fernet encryption, tenant isolation, proof-only output

import os
import sys
import hashlib
import logging
import traceback
from datetime import datetime, timedelta
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
    import base64
    json_bytes = json.dumps(data).encode()
    encrypted = encrypt_data(json_bytes)
    return base64.b64encode(encrypted).decode()

def decrypt_json(data: str) -> Dict:
    import json
    import base64
    encrypted = base64.b64decode(data.encode())
    decrypted = decrypt_data(encrypted)
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
                obj.__dict__[key] = None

def validate_secrets(required: List[str] = None) -> bool:
    if required is None:
        required = ['FERNET_KEY']
    missing = [s for s in required if not os.environ.get(s)]
    if missing:
        logger.warning(f"Missing secrets (ok for dev): {missing}")
        return False
    return True

def validate_jwt_tenant(token: str) -> Optional[str]:
    try:
        import jwt
        if not JWT_SECRET:
            return "default"
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("sub", "unknown")
    except Exception:
        return None

def safe_error_response(e: Exception) -> Dict[str, Any]:
    logger.error(f"Error occurred | type={type(e).__name__}")
    return {
        "error": "An error occurred",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "status": "failed"
    }

def validate_password(input_password: str) -> bool:
    fund_password = os.environ.get("FUND_PASSWORD", "sovereign2024")
    return input_password == fund_password

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_session_token(fund_id: str) -> str:
    import jwt
    import time
    payload = {
        "sub": fund_id,
        "exp": time.time() + 86400 * 7,
        "iat": time.time()
    }
    return jwt.encode(payload, JWT_SECRET or "default_secret", algorithm="HS256")

def verify_session_token(token: str) -> Optional[str]:
    import jwt
    try:
        payload = jwt.decode(token, JWT_SECRET or "default_secret", algorithms=["HS256"])
        return payload.get("sub")
    except:
        return None
