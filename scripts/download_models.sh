#!/usr/bin/env bash
# Downloads the local models used for every reported number (≈4.4 GB total).
set -euo pipefail
mkdir -p models
hf download Qwen/Qwen2.5-3B-Instruct-GGUF qwen2.5-3b-instruct-q4_k_m.gguf --local-dir models      # generator
hf download bartowski/Phi-3.5-mini-instruct-GGUF Phi-3.5-mini-instruct-Q4_K_M.gguf --local-dir models  # judge
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"  # embeddings
