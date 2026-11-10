Generator: Qwen2.5-3B-Instruct (GGUF Q4_K_M, llama.cpp) · Judge: Phi-3.5-mini-instruct (GGUF Q4_K_M, llama.cpp)

| Metric | baseline | iter1_prompt_v2 |
|---|---|---|
| Pass rate (all 50) | 58.0% | 78.0% |
|   answerable (30) | 60.0% | 86.7% |
|   partially answerable (10) | 20.0% | 40.0% |
|   out-of-scope (10) | 90.0% | 90.0% |
| Hallucination rate, answers shown to user | 3.3% | 2.7% |
| Hallucination rate, all drafts | 2.6% | 9.1% |
| Accuracy of answers shown | 66.7% | 81.1% |
| Citation accuracy (shown, in-scope) | 96.5% | 97.2% |
| Escalation rate (all 50) | 40.0% | 26.0% |
|   answerable | 23.3% | 3.3% |
|   out-of-scope | 90.0% | 90.0% |
| Retrieval hit rate @k (in-scope) | 100.0% | 100.0% |
| Median latency (s) | 11.94 | 11.7 |
| p90 latency (s) | 16.73 | 15.67 |
| Cost per 100 queries (USD) | 0.0 | 0.0 |
