"""retrieve -> generate -> parse citations -> confidence gate."""
import re
import time

from copilot.llm import generator_from_config
from copilot.prompts import SYSTEM_PROMPTS, build_user_prompt
from copilot.retrieve import Retriever

IDK_PATTERN = re.compile(r"\bI (do not|don't|dont) know\b", re.I)
CITE_PATTERN = re.compile(r"\[([^\[\]]+?)\]")


def parse_citations(answer: str, retrieved_ids: list[str]) -> tuple[list[str], list[str]]:
    """Map [S1], [S2, S3], [S1][S4] labels back to chunk ids.
    Returns (valid chunk ids, invalid labels such as [S9] when only 4 were retrieved)."""
    valid, invalid = [], []
    for group in CITE_PATTERN.findall(answer):
        for label in re.split(r"[,;]\s*|\s+and\s+", group):
            m = re.fullmatch(r"\s*S(\d+)\s*", label, flags=re.I)
            if not m:
                continue
            n = int(m.group(1))
            if 1 <= n <= len(retrieved_ids):
                if retrieved_ids[n - 1] not in valid:
                    valid.append(retrieved_ids[n - 1])
            elif label.strip() not in invalid:
                invalid.append(label.strip())
    return valid, invalid


def apply_gate(cfg: dict, answer: str, top_score: float, valid_citations: list[str]) -> tuple[bool, list[str]]:
    g = cfg["gate"]
    reasons = []
    is_idk = bool(IDK_PATTERN.search(answer)) and len(answer) < 200
    if g["escalate_on_idk"] and is_idk:
        reasons.append("model_said_idk")
    if top_score < g["min_retrieval_score"]:
        reasons.append("low_retrieval_score")
    if g["require_citation"] and not valid_citations and not is_idk:
        reasons.append("no_valid_citation")
    return (len(reasons) == 0), reasons


class Copilot:
    def __init__(self, cfg: dict, force_local: bool = False):
        self.cfg = cfg
        self.retriever = Retriever(cfg)
        self.llm = generator_from_config(cfg, force_local=force_local)

    def ask(self, question: str) -> dict:
        t0 = time.perf_counter()
        passages = self.retriever.search(question)
        retrieved_ids = [c["chunk_id"] for c in passages]
        top_score = passages[0]["score"] if passages else 0.0
        gen = self.llm.chat(SYSTEM_PROMPTS[self.cfg["generation"]["prompt_version"]],
                            build_user_prompt(question, passages),
                            max_tokens=self.cfg["generation"]["max_tokens"],
                            temperature=self.cfg["generation"]["temperature"])
        valid, invalid = parse_citations(gen["text"], retrieved_ids)
        shown, reasons = apply_gate(self.cfg, gen["text"], top_score, valid)
        return {
            "question": question,
            "answer": gen["text"],
            "shown_to_user": shown,
            "gate_reasons": reasons,
            "confidence": round(top_score, 4),
            "retrieved": [{"chunk_id": c["chunk_id"], "score": round(c["score"], 4),
                           "url": c["url"], "title": c["title"], "section": c["section"],
                           "text": c["text"]} for c in passages],
            "valid_citations": valid,
            "invalid_citations": invalid,
            "latency_s": round(time.perf_counter() - t0, 3),
            "llm_latency_s": round(gen["latency_s"], 3),
            "input_tokens": gen["input_tokens"],
            "output_tokens": gen["output_tokens"],
            "provider": gen["provider"],
            "model": gen["model"],
        }
