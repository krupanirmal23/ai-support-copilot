"""Provider layer. Claude if ANTHROPIC_API_KEY is set, else a local GGUF model via llama.cpp.

Every call returns text + token counts + the exact model name, so each eval number
can be tied to the model that produced it.
"""
import os
import time
from functools import lru_cache

from copilot.config import p


@lru_cache(maxsize=4)
def _llama(path: str, n_ctx: int, n_threads: int):
    from llama_cpp import Llama
    return Llama(model_path=path, n_ctx=n_ctx, n_threads=n_threads, verbose=False, seed=0)


class LLM:
    def __init__(self, provider: str, model: str, local_path: str | None = None,
                 n_ctx: int = 4096, n_threads: int = 8):
        self.provider, self.model = provider, model
        self.local_path, self.n_ctx, self.n_threads = local_path, n_ctx, n_threads
        if provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic()

    def chat(self, system: str, user: str, max_tokens: int = 350, temperature: float = 0.0,
             json_schema: dict | None = None) -> dict:
        t0 = time.perf_counter()
        if self.provider == "anthropic":
            msg = self.client.messages.create(
                model=self.model, max_tokens=max_tokens, temperature=temperature,
                system=system, messages=[{"role": "user", "content": user}])
            text = "".join(b.text for b in msg.content if b.type == "text")
            usage = {"input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens}
        else:
            llm = _llama(str(p(self.local_path)), self.n_ctx, self.n_threads)
            kwargs = {}
            if json_schema:
                kwargs["response_format"] = {"type": "json_object", "schema": json_schema}
            out = llm.create_chat_completion(
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                max_tokens=max_tokens, temperature=temperature, **kwargs)
            text = out["choices"][0]["message"]["content"]
            usage = {"input_tokens": out["usage"]["prompt_tokens"],
                     "output_tokens": out["usage"]["completion_tokens"]}
        return {"text": text.strip(), "latency_s": time.perf_counter() - t0,
                "provider": self.provider, "model": self.model, **usage}


def generator_from_config(cfg: dict, force_local: bool = False) -> LLM:
    g = cfg["generation"]
    n_threads = int(os.environ.get("LLAMA_N_THREADS", g["n_threads"]))
    if os.environ.get("ANTHROPIC_API_KEY") and not force_local:
        return LLM("anthropic", g["claude_model"])
    return LLM("local", g["local_model_name"], g["local_model_path"], g["n_ctx"], n_threads)


def judge_from_config(cfg: dict, force_local: bool = False) -> LLM:
    j = cfg["judge"]
    if os.environ.get("ANTHROPIC_API_KEY") and not force_local:
        return LLM("anthropic", j["claude_model"])
    return LLM("local", j["local_model_name"], j["local_model_path"],
               cfg["generation"]["n_ctx"], cfg["generation"]["n_threads"])
