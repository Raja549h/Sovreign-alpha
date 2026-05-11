import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
AGENTS_DIR = BASE_DIR / "agents"
RAG_DIR = BASE_DIR / "rag"
ZKML_DIR = BASE_DIR / "zkml"
BLOCKCHAIN_DIR = BASE_DIR / "blockchain"
BILLING_DIR = BASE_DIR / "billing"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not found. Copy .env.example to .env and add your key.")

WEB3_RPC_URL = os.getenv("WEB3_RPC_URL", "https://sepolia.base.org")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
COINBASE_AGENT_KIT_TOKEN = os.getenv("COINBASE_AGENT_KIT_TOKEN", "")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "")

LLAMA_33_70B = "llama-3.3-70b-versatile"
LLAMA_31_8B = "llama-3.1-8b-instant"

llm_config = {
    "model": LLAMA_33_70B,
    "api_key": GROQ_API_KEY,
    "temperature": 0.3,
    "max_tokens": 2048
}

quick_llm_config = {
    "model": LLAMA_31_8B,
    "api_key": GROQ_API_KEY,
    "temperature": 0.1,
    "max_tokens": 1024
}

embedding_model = "embed-english-v3.0"

CHROMA_PERSIST_DIR = str(DATA_DIR / "chroma_db")

chroma_persist_dir = CHROMA_PERSIST_DIR

PERFORMANCE_FEE_PCT = 12.0

LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")  # ✅ PRIVACY: Default WARNING, no raw data in logs

def setup_logging():
    import logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    return logging.getLogger(__name__)

logger = setup_logging()