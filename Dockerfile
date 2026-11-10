# Hugging Face Spaces (Docker SDK) — CPU-only runtime for the Streamlit copilot.
# Uses a prebuilt manylinux llama-cpp-python wheel so the image does not compile llama.cpp.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Spaces run the container as UID 1000.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    LLAMA_N_THREADS=2 \
    HF_HOME=/home/user/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/user/.cache/huggingface/hub \
    SENTENCE_TRANSFORMERS_HOME=/home/user/.cache/sentence_transformers \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHERUSAGESTATS=false

WORKDIR /home/user/app

# 1) Python deps (cached unless requirements change)
COPY --chown=user requirements-space.txt /tmp/requirements-space.txt
# Official 0.3.36 CPU wheel for glibc/manylinux (the /whl/cpu index serves musl wheels).
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir \
        https://github.com/abetlen/llama-cpp-python/releases/download/v0.3.36/llama_cpp_python-0.3.36-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl \
 && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        torch==2.15.0 \
 && pip install --no-cache-dir -r /tmp/requirements-space.txt

# 2) Download the answer model + embedder at build time (not the Phi-3.5 judge).
COPY --chown=user scripts/download_space_models.py /tmp/download_space_models.py
RUN python /tmp/download_space_models.py --models-dir /home/user/app/models

# 3) Application source, including the shipped FAISS index.
COPY --chown=user . /home/user/app

EXPOSE 7860
CMD ["streamlit", "run", "app.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false", \
     "--browser.gatherUsageStats=false"]
