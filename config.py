import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
IS_CLOUD = bool(os.environ.get("SPACE_ID")) or os.environ.get("RENDER", "false").lower() == "true"
PERSISTENT_DIR = Path(os.environ.get("PERSISTENT_DIR", "/data" if IS_CLOUD else BASE_DIR))

if IS_CLOUD and not PERSISTENT_DIR.exists():
    try:
        PERSISTENT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        print(f"WARNING: Cannot create {PERSISTENT_DIR}. Falling back to BASE_DIR.")
        PERSISTENT_DIR = BASE_DIR


DATA_DIR = PERSISTENT_DIR / "data"
BILLING_DIR = PERSISTENT_DIR / "billing"
RESULTS_DIR = PERSISTENT_DIR / "results"

AGENTS_DIR = BASE_DIR / "agents"
ENGINE_DIR = BASE_DIR / "engine"
RAG_DIR = BASE_DIR / "rag"
ZKML_DIR = BASE_DIR / "zkml"
BLOCKCHAIN_DIR = BASE_DIR / "blockchain"
DASHBOARD_DIR = BASE_DIR / "dashboard"

LLM_PROVIDER = "cerebras"
LLM_API_KEY = os.environ.get("CEREBRAS_API_KEY", "")
LLM_BASE_URL = "https://api.cerebras.ai/v1"

if not LLM_API_KEY:
    print("WARNING: CEREBRAS_API_KEY not found. Copy .env.example to .env and add your key.")

WEB3_RPC_URL = os.getenv("WEB3_RPC_URL", "https://sepolia.base.org")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
COINBASE_AGENT_KIT_TOKEN = os.getenv("COINBASE_AGENT_KIT_TOKEN", "")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "")

LLM_MODEL = os.environ.get("CEREBRAS_MODEL", "gpt-oss-120b")
LLM_MODEL_FAST = os.environ.get("CEREBRAS_MODEL_FAST", "gpt-oss-120b")

llm_config = {
    "model": LLM_MODEL,
    "api_key": LLM_API_KEY,
    "base_url": LLM_BASE_URL,
    "temperature": 0.3,
    "max_tokens": 2048
}

quick_llm_config = {
    "model": LLM_MODEL_FAST,
    "api_key": LLM_API_KEY,
    "base_url": LLM_BASE_URL,
    "temperature": 0.1,
    "max_tokens": 1024
}

CHROMA_PERSIST_DIR = str(DATA_DIR / "chroma_db")

PERFORMANCE_FEE_PCT = 12.0

LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")

def setup_logging():
    import logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    return logging.getLogger(__name__)

logger = setup_logging()
