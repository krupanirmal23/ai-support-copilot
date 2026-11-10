"""Dense retrieval over the FAISS index (cosine similarity on normalised bge-small vectors)."""
import json
from functools import lru_cache

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from copilot.config import p


@lru_cache(maxsize=2)
def _embedder(name: str):
    return SentenceTransformer(name)


class Retriever:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        idx_dir = p(cfg["corpus"]["index_dir"])
        self.index = faiss.read_index(str(idx_dir / "faiss.index"))
        self.chunks = [json.loads(l) for l in open(idx_dir / "chunks.jsonl")]
        self.model = _embedder(cfg["embedding"]["model"])

    def search(self, query: str, k: int | None = None) -> list[dict]:
        k = k or self.cfg["retrieval"]["top_k"]
        q = self.model.encode([self.cfg["embedding"]["query_prefix"] + query],
                              normalize_embeddings=True)
        scores, ids = self.index.search(np.asarray(q, dtype="float32"), k)
        return [{**self.chunks[i], "score": float(s)} for s, i in zip(scores[0], ids[0]) if i >= 0]
