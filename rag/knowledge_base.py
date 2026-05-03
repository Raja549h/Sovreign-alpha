import os
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("WARNING: ChromaDB not available, using fallback search")

try:
    from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
    from llama_index.core import Document as LIDocument
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.vector_stores.chroma import ChromaVectorStore
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    try:
        from llama_index import VectorStoreIndex, SimpleDirectoryReader
        from llama_index.embeddings import HuggingFaceEmbedding
        LLAMA_INDEX_AVAILABLE = True
    except ImportError:
        LLAMA_INDEX_AVAILABLE = False
        print("WARNING: LlamaIndex not available, using simple fallback")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

from config import (
    DATA_DIR, CHROMA_PERSIST_DIR, GROQ_API_KEY,
    embedding_model, logger
)


class KnowledgeBase:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DATA_DIR
        self.chroma_dir = Path(CHROMA_PERSIST_DIR)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        
        self.positions: List[Dict[str, Any]] = []
        self.research_notes: List[Dict[str, Any]] = []
        self.risk_params: Dict[str, Any] = {}
        
        self.index = None
        self.embedding_model = None
        self.client = None
        
        self._initialize()

    def _initialize(self):
        logger.info("Initializing Knowledge Base...")
        self._load_data()
        self._setup_vector_store()
        logger.info(f"Knowledge base ready with {len(self.positions)} positions and {len(self.research_notes)} research notes")

    def _load_data(self):
        positions_file = self.data_dir / "sample_positions.csv"
        if positions_file.exists():
            df = pd.read_csv(positions_file)
            self.positions = df.to_dict('records')
            logger.info(f"Loaded {len(self.positions)} positions from CSV")

        research_file = self.data_dir / "sample_research.txt"
        if research_file.exists():
            content = research_file.read_text(encoding='utf-8')
            self.research_notes = [{'content': content, 'source': 'sample_research.txt'}]
            logger.info(f"Loaded research notes from {research_file.name}")

        risk_file = self.data_dir / "risk_parameters.json"
        if risk_file.exists():
            self.risk_params = json.loads(risk_file.read_text(encoding='utf-8'))
            logger.info("Loaded risk parameters")

    def _setup_vector_store(self):
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available, using in-memory fallback")
            self.client = None
            return

        try:
            self.client = chromadb.Client(Settings(
                persist_directory=str(self.chroma_dir),
                anonymized_telemetry=False
            ))
            
            collection_name = "sovereign_alpha_kb"
            try:
                self.collection = self.client.get_collection(collection_name)
                self.client.delete_collection(collection_name)
            except:
                pass
            
            self.collection = self.client.create_collection(
                collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            self._embed_documents()
            
        except Exception as e:
            logger.warning(f"ChromaDB setup failed: {e}, using fallback")
            self.client = None

    def _embed_documents(self):
        if not self.client:
            return

        docs = []
        ids = []
        metadatas = []

        for i, pos in enumerate(self.positions):
            doc_text = (
                f"Position {pos.get('position_id', '')}: "
                f"{pos.get('symbol', '')} in {pos.get('sector', '')} sector. "
                f"Entry: ${pos.get('entry_price', 0)}, Current: ${pos.get('current_price', 0)}, "
                f"Quantity: {pos.get('quantity', 0)}, P&L: ${pos.get('unrealized_pnl', 0)}. "
                f"Confidence: {pos.get('confidence_score', 0)}, Status: {pos.get('status', '')}"
            )
            docs.append(doc_text)
            ids.append(f"pos_{i}")
            metadatas.append({"type": "position", "symbol": pos.get('symbol', '')})

        for i, note in enumerate(self.research_notes):
            doc_text = note.get('content', '')
            docs.append(doc_text)
            ids.append(f"research_{i}")
            metadatas.append({"type": "research", "source": note.get('source', '')})

        if self.risk_params:
            risk_text = json.dumps(self.risk_params)
            docs.append(risk_text)
            ids.append("risk_params")
            metadatas.append({"type": "risk_params"})

        if docs:
            try:
                self._generate_embeddings(docs, ids, metadatas)
            except Exception as e:
                logger.warning(f"Embedding generation failed: {e}")

    def _generate_embeddings(self, texts: List[str], ids: List[str], metadatas: List[Dict]):
        if not GROQ_AVAILABLE:
            logger.warning("Groq not available for embeddings, using hash fallback")
            for i, text in enumerate(texts):
                embedding = self._simple_hash_embedding(text)
                self.collection.upsert(
                    ids=[ids[i]],
                    embeddings=[embedding],
                    metadatas=[metadatas[i]]
                )
            return

        try:
            client = Groq(api_key=GROQ_API_KEY)
            
            for i, text in enumerate(texts):
                try:
                    response = client.embeddings.create(
                        model=embedding_model,
                        input=text
                    )
                    embedding = response.data[0].embedding
                    self.collection.upsert(
                        ids=[ids[i]],
                        embeddings=[embedding],
                        metadatas=[metadatas[i]]
                    )
                except Exception as e:
                    logger.warning(f"Embedding failed for {ids[i]}: {e}")
                    embedding = self._simple_hash_embedding(text)
                    self.collection.upsert(
                        ids=[ids[i]],
                        embeddings=[embedding],
                        metadatas=[metadatas[i]]
                    )
                    
        except Exception as e:
            logger.warning(f"Groq embedding setup failed: {e}")
            for i, text in enumerate(texts):
                embedding = self._simple_hash_embedding(text)
                self.collection.upsert(
                    ids=[ids[i]],
                    embeddings=[embedding],
                    metadatas=[metadatas[i]]
                )

    def _simple_hash_embedding(self, text: str) -> List[float]:
        hash_val = int(hashlib.sha256(text.encode()).hexdigest(), 16)
        embedding = []
        for i in range(384):
            embedding.append(((hash_val >> i) & 1) * 2 - 1)
        return embedding

    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.client:
            return self._fallback_query(query_text, top_k)

        try:
            if not GROQ_AVAILABLE:
                query_embedding = self._simple_hash_embedding(query_text)
            else:
                client = Groq(api_key=GROQ_API_KEY)
                response = client.embeddings.create(
                    model=embedding_model,
                    input=query_text
                )
                query_embedding = response.data[0].embedding

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )

            responses = []
            if results.get('ids') and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    responses.append({
                        'id': doc_id,
                        'content': results.get('documents', [[]])[0][i] if results.get('documents') else '',
                        'metadata': results.get('metadatas', [[]])[0][i] if results.get('metadatas') else {},
                        'distance': results.get('distances', [[]])[0][i] if results.get('distances') else 0.0
                    })
            
            return responses
            
        except Exception as e:
            logger.warning(f"Query failed: {e}")
            return self._fallback_query(query_text, top_k)

    def _fallback_query(self, query_text: str, top_k: int) -> List[Dict[str, Any]]:
        results = []
        query_lower = query_text.lower()
        
        for pos in self.positions:
            score = 0.0
            if any(kw in pos.get('symbol', '').lower() for kw in query_lower.split()):
                score = 1.0
            elif any(kw in pos.get('sector', '').lower() for kw in query_lower.split()):
                score = 0.8
            if score > 0:
                results.append({
                    'id': pos.get('position_id', ''),
                    'content': f"{pos.get('symbol', '')}: {pos}",
                    'metadata': {'type': 'position'},
                    'distance': 1 - score
                })
        
        return results[:top_k]

    def get_position_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        for pos in self.positions:
            if pos.get('symbol', '').upper() == symbol.upper():
                return pos
        return None

    def get_active_positions(self) -> List[Dict[str, Any]]:
        return [p for p in self.positions if p.get('status', '') == 'active']

    def get_portfolio_summary(self) -> Dict[str, Any]:
        active = self.get_active_positions()
        
        total_value = sum(p.get('unrealized_pnl', 0) for p in active)
        positions_by_sector = {}
        
        for pos in active:
            sector = pos.get('sector', 'Other')
            if sector not in positions_by_sector:
                positions_by_sector[sector] = {'count': 0, 'pnl': 0, 'value': 0}
            positions_by_sector[sector]['count'] += 1
            positions_by_sector[sector]['pnl'] += pos.get('unrealized_pnl', 0)
            positions_by_sector[sector]['value'] += pos.get('current_price', 0) * pos.get('quantity', 0)
        
        return {
            'total_positions': len(active),
            'total_unrealized_pnl': total_value,
            'by_sector': positions_by_sector,
            'positions': active
        }

    def get_risk_parameters(self) -> Dict[str, Any]:
        return self.risk_params
    
    def refresh_live_data(self) -> bool:
        """Fetch fresh market data and re-ingest into ChromaDB."""
        try:
            from pathlib import Path
            import subprocess
            
            base_dir = Path(__file__).parent.parent
            
            result = subprocess.run(
                [sys.executable, str(base_dir / "data" / "market_feed.py")],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning(f"market_feed.py failed: {result.stderr}")
                return False
            
            result = subprocess.run(
                [sys.executable, str(base_dir / "data" / "market_signals.py")],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning(f"market_signals.py failed: {result.stderr}")
                return False
            
            self._ingest_live_data()
            
            return True
        
        except Exception as e:
            logger.warning(f"refresh_live_data failed: {e}")
            return False
    
    def _ingest_live_data(self):
        """Ingest live market data and signals into ChromaDB."""
        if not self.client:
            return
        
        base_dir = Path(__file__).parent.parent
        market_data_file = base_dir / "data" / "live_market_data.json"
        signals_file = base_dir / "data" / "live_signals.json"
        
        try:
            live_market_collection = self.client.get_collection("live_market_data")
            self.client.delete_collection("live_market_data")
        except:
            pass
        
        live_market_collection = self.client.create_collection(
            "live_market_data",
            metadata={"hnsw:space": "cosine"}
        )
        
        if market_data_file.exists():
            with open(market_data_file, "r") as f:
                market_data = json.load(f)
            
            for ticker, data in market_data.get("tickers", {}).items():
                if "error" in data:
                    continue
                
                doc_text = (
                    f"{ticker}: Price ${data.get('current_price', 0)}, "
                    f"RSI {data.get('rsi_14', 0)}, "
                    f"Volume 2x: {data.get('volume_ratio', 1) > 2}, "
                    f"MA50 ${data.get('ma50', 0)}, "
                    f"MA200 ${data.get('ma200', 0)}, "
                    f"Analyst Target: ${data.get('analyst_target', 'N/A')}"
                )
                
                live_market_collection.add(
                    documents=[doc_text],
                    ids=[f"live_{ticker}"],
                    metadatas=[{"type": "live_market", "symbol": ticker}]
                )
        
        try:
            signals_collection = self.client.get_collection("market_signals")
            self.client.delete_collection("market_signals")
        except:
            pass
        
        signals_collection = self.client.create_collection(
            "market_signals",
            metadata={"hnsw:space": "cosine"}
        )
        
        if signals_file.exists():
            with open(signals_file, "r") as f:
                signals = json.load(f)
            
            for signal_type in ["oversold", "overbought", "unusual_volume", "below_target", "near_high", "near_low"]:
                for item in signals.get(signal_type, []):
                    doc_text = (
                        f"{item.get('symbol', '')}: {signal_type.replace('_', ' ')} - "
                        f"{item.get('reason', '')}"
                    )
                    
                    signals_collection.add(
                        documents=[doc_text],
                        ids=[f"signal_{item.get('symbol', '')}_{signal_type}"],
                        metadatas=[{"type": "signal", "signal_type": signal_type}]
                    )
        
        logger.info("Live market data ingested into ChromaDB")
    
    def get_live_market_data(self) -> Dict[str, Any]:
        """Get live market data from JSON."""
        base_dir = Path(__file__).parent.parent
        market_data_file = base_dir / "data" / "live_market_data.json"
        
        if market_data_file.exists():
            with open(market_data_file, "r") as f:
                return json.load(f)
        return {}
    
    def get_live_signals(self) -> Dict[str, Any]:
        """Get live signals from JSON."""
        base_dir = Path(__file__).parent.parent
        signals_file = base_dir / "data" / "live_signals.json"
        
        if signals_file.exists():
            with open(signals_file, "r") as f:
                return json.load(f)
        return {}


def get_knowledge_base() -> KnowledgeBase:
    return KnowledgeBase()


if __name__ == "__main__":
    kb = get_knowledge_base()
    print("\n=== Portfolio Summary ===")
    summary = kb.get_portfolio_summary()
    print(f"Total Active Positions: {summary['total_positions']}")
    print(f"Total Unrealized P&L: ${summary['total_unrealized_pnl']:,.2f}")
    print("\nBy Sector:")
    for sector, data in summary['by_sector'].items():
        print(f"  {sector}: {data['count']} positions, ${data['pnl']:,.2f} P&L")
    
    print("\n=== Test Query ===")
    results = kb.query("NVIDIA technology position")
    for r in results:
        print(f"- {r['id']}: {r['content'][:100]}...")