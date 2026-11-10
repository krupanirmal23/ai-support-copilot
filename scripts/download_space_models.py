#!/usr/bin/env python3
"""Download only the models the hosted demo needs: the Qwen generator and the embedder.

The Phi-3.5 judge is eval-only and is intentionally not downloaded.
"""
from __future__ import annotations

import argparse
from pathlib import Path


GENERATOR_REPO = "Qwen/Qwen2.5-3B-Instruct-GGUF"
GENERATOR_FILE = "qwen2.5-3b-instruct-q4_k_m.gguf"
EMBEDDER = "BAAI/bge-small-en-v1.5"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models-dir", default="models")
    args = parser.parse_args()

    models_dir = Path(args.models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    from huggingface_hub import hf_hub_download

    dest = hf_hub_download(
        repo_id=GENERATOR_REPO,
        filename=GENERATOR_FILE,
        local_dir=str(models_dir),
    )
    print(f"generator: {dest}")

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBEDDER)
    # One encode call warms the load path that retrieve.py uses.
    _ = model.encode(["warmup"], normalize_embeddings=True)
    print(f"embedder: {EMBEDDER} loaded")


if __name__ == "__main__":
    main()
