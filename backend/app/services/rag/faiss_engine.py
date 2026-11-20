import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from backend.app.core.config import settings

logger = logging.getLogger("evidencerag.faiss")

class FAISSVectorStore:
    """
    High-performance semantic vector retrieval engine using FAISS and Sentence Transformers.
    - Indexes applicant documents & approved regulatory guidelines
    - Normalizes embeddings for cosine similarity search (IndexFlatIP)
    - Enforces tenant isolation preventing cross-applicant data leakage
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.encoder = None
        self.dimension = 384  # Default for all-MiniLM-L6-v2
        self.index = None
        self.metadata: List[Dict[str, Any]] = []

        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.encoder = SentenceTransformer(self.model_name)
                sample_emb = self.encoder.encode(["Test embedding dimension"], convert_to_numpy=True)
                self.dimension = sample_emb.shape[1]
                logger.info(f"Loaded embedding model '{self.model_name}', dimension: {self.dimension}")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer '{self.model_name}': {e}")

        if FAISS_AVAILABLE:
            self.index = faiss.IndexFlatIP(self.dimension)
            logger.info(f"Initialized FAISS IndexFlatIP (dim={self.dimension})")

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1e-12
        return vectors / norms

    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]]):
        """Encode and add text chunks to the FAISS index with metadata."""
        if not texts or self.index is None or self.encoder is None:
            return

        try:
            embeddings = self.encoder.encode(texts, convert_to_numpy=True)
            norm_embeddings = self._normalize(embeddings).astype(np.float32)
            self.index.add(norm_embeddings)
            for text, meta in zip(texts, metadatas):
                item = dict(meta)
                if "text" not in item:
                    item["text"] = text
                self.metadata.append(item)
            logger.info(f"Added {len(texts)} chunks to FAISS index. Total indexed: {self.index.ntotal}")
        except Exception as e:
            logger.error(f"Error adding documents to FAISS index: {e}")

    def search(
        self,
        query: str,
        top_k: int = 4,
        user_id: Optional[int] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity search.
        Filters by user_id to prevent cross-applicant data leakage.
        """
        if self.index is None or self.encoder is None or self.index.ntotal == 0:
            return []

        try:
            query_emb = self.encoder.encode([query], convert_to_numpy=True)
            norm_query = self._normalize(query_emb).astype(np.float32)

            # Retrieve top_k * 3 candidates to allow metadata filtering
            fetch_k = min(self.index.ntotal, max(top_k * 3, 10))
            scores, indices = self.index.search(norm_query, fetch_k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self.metadata):
                    continue

                meta = self.metadata[idx]

                # Tenant isolation filter: allow if public/guideline or owned by user
                if user_id is not None and meta.get("user_id") is not None and meta.get("user_id") != user_id:
                    continue

                # Category filter
                if category and meta.get("category") and meta.get("category").lower() != category.lower():
                    continue

                results.append({
                    "score": float(score),
                    "text": meta.get("text", ""),
                    "source": meta.get("source", ""),
                    "document_id": meta.get("document_id"),
                    "page_number": meta.get("page_number", 1),
                    "category": meta.get("category", ""),
                    "rule_id": meta.get("rule_id")
                })

                if len(results) >= top_k:
                    break

            return results
        except Exception as e:
            logger.error(f"Error during FAISS search: {e}")
            return []

    def reset(self):
        """Clear index and metadata."""
        if self.index is not None:
            self.index.reset()
        self.metadata = []

# Global singleton instance
faiss_store = FAISSVectorStore()
