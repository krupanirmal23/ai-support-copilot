"""One-command eval harness.

    python -m copilot.evaluate --run-name baseline            # local models (no API key needed)
    ANTHROPIC_API_KEY=... python -m copilot.evaluate --run-name claude   # Claude generator + judge

Outputs (eval/results/<run-name>/):
    config_snapshot.yaml  exact config used
    run_info.json         models, versions, machine, timings
    generations.jsonl     raw copilot outputs (answer, retrieved chunks, gate decision, latency, tokens)
    judgments.jsonl       raw judge outputs
    results.csv           one row per question (everything needed to recompute metrics)
    metrics.json          aggregate metrics (computed only from results.csv)
    spot_check.csv        ~20% stratified sample for a human to verify the judge
"""
import argparse
import csv
import json
import os
import platform
import random
import statistics
import time
from collections import Counter

import yaml

from copilot.config import load_config, p
from copilot.llm import judge_from_config
from copilot.pipeline import IDK_PATTERN, Copilot

JUDGE_SYSTEM = """You are a strict grader for a customer-support assistant. Compare the CANDIDATE answer with the REFERENCE answer for the QUESTION.
Choose exactly one label:
- "correct": the candidate conveys the key facts of the reference and adds nothing that contradicts it or is invented. If the reference says part of the question is not covered by the docs, the candidate must not invent that part.
- "partially correct": some key facts are right, but important facts are missing or vague. Nothing is invented.
- "wrong": the key facts are missing or contradict the reference, or it answers a different question, without inventing specific details.
- "hallucinated": the candidate states specific details (numbers, limits, prices, settings, steps, product features or URLs) that are not in the reference and look made up, OR it gives a substantive answer when the reference says the question is out of scope.
Return JSON: {"label": "...", "reason": "<one short sentence>"}"""

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {"type": "string", "enum": ["correct", "partially correct", "wrong", "hallucinated"]},
        "reason": {"type": "string"},
    },
    "required": ["label", "reason"],
}


def is_idk(answer: str) -> bool:
    return bool(IDK_PATTERN.search(answer)) and len(answer) < 200


def judge_one(judge, q: dict, answer: str) -> dict:
    user = (f"QUESTION: {q['question']}\n\nREFERENCE: {q['expected_answer']}\n\n"
            f"CANDIDATE: {answer}\n\nReturn the JSON now.")
    out = judge.chat(JUDGE_SYSTEM, user, max_tokens=120, temperature=0.0, json_schema=JUDGE_SCHEMA)
    try:
        parsed = json.loads(out["text"])
        label, reason = parsed["label"], parsed.get("reason", "")
    except Exception:
        label, reason = "judge_parse_error", out["text"][:300]
    return {"label": label, "reason": reason, "judge_model": out["model"],
            "judge_latency_s": round(out["latency_s"], 3),
            "judge_input_tokens": out["input_tokens"], "judge_output_tokens": out["output_tokens"]}


def item_pass(row: dict) -> bool:
    if row["category"] == "out-of-scope":
        return not row["shown_to_user"]                        # must be escalated / not answered
    return row["shown_to_user"] and row["judge_label"] == "correct"


def compute_metrics(rows: list[dict], cfg: dict, gen_model: str, judge_model: str) -> dict:
    n = len(rows)
    shown = [r for r in rows if r["shown_to_user"]]
    drafts = [r for r in rows if not r["model_said_idk"]]       # substantive answers, judged
    in_scope = [r for r in rows if r["category"] != "out-of-scope"]
    shown_in_scope = [r for r in shown if r["category"] != "out-of-scope"]

    def rate(a, b):
        return round(a / b, 4) if b else None

    cats = sorted(set(r["category"] for r in rows))
    lat = [r["latency_s"] for r in rows]
    cost_100 = 0.0
    if rows[0]["provider"] == "anthropic":
        price = cfg["pricing_usd_per_mtok"][gen_model]
        per_q = [(r["input_tokens"] * price["input"] + r["output_tokens"] * price["output"]) / 1e6 for r in rows]
        cost_100 = round(statistics.mean(per_q) * 100, 4)
    cit_hits = [r for r in shown_in_scope if r["cited_expected_source"]]
    return {
        "n_questions": n,
        "by_category_count": dict(Counter(r["category"] for r in rows)),
        "generator_model": gen_model,
        "judge_model": judge_model,
        "pass_rate": rate(sum(item_pass(r) for r in rows), n),
        "pass_rate_by_category": {c: rate(sum(item_pass(r) for r in rows if r["category"] == c),
                                          sum(r["category"] == c for r in rows)) for c in cats},
        "escalation_rate": rate(n - len(shown), n),
        "escalation_rate_by_category": {c: rate(sum((not r["shown_to_user"]) for r in rows if r["category"] == c),
                                                sum(r["category"] == c for r in rows)) for c in cats},
        "hallucination_rate_shown": rate(sum(r["judge_label"] == "hallucinated" for r in shown), len(shown)),
        "hallucination_rate_all_drafts": rate(sum(r["judge_label"] == "hallucinated" for r in drafts), len(drafts)),
        "accuracy_of_shown_answers": rate(sum(r["judge_label"] == "correct" for r in shown), len(shown)),
        "judge_label_counts_all_drafts": dict(Counter(r["judge_label"] for r in drafts)),
        "judge_label_counts_shown": dict(Counter(r["judge_label"] for r in shown)),
        "model_idk_count": sum(r["model_said_idk"] for r in rows),
        "citation_accuracy": rate(len(cit_hits), len(shown_in_scope)),
        "citation_accuracy_definition": "share of in-scope answers shown to the user that cite >=1 chunk from an expected source page",
        "invalid_citation_answers": sum(1 for r in rows if r["invalid_citations"]),
        "retrieval_hit_rate_at_k": rate(sum(r["expected_source_retrieved"] for r in in_scope), len(in_scope)),
        "top_k": cfg["retrieval"]["top_k"],
        "median_latency_s": round(statistics.median(lat), 2),
        "p90_latency_s": round(sorted(lat)[int(0.9 * (n - 1))], 2),
        "cost_per_100_queries_usd": cost_100,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--questions", default="eval/questions.csv")
    ap.add_argument("--force-local", action="store_true", help="ignore ANTHROPIC_API_KEY")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--set", nargs="*", default=[], help="config overrides, e.g. retrieval.top_k=6")
    args = ap.parse_args()

    overrides = {}
    for kv in args.set:
        k, v = kv.split("=", 1)
        overrides[k] = yaml.safe_load(v)
    cfg = load_config(overrides=overrides)
    out_dir = p(f"eval/results/{args.run_name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    yaml.safe_dump(cfg, open(out_dir / "config_snapshot.yaml", "w"), sort_keys=False)

    questions = list(csv.DictReader(open(p(args.questions))))[: args.limit]
    t_start = time.time()

    # 1) generation
    copilot = Copilot(cfg, force_local=args.force_local)
    gens = []
    with open(out_dir / "generations.jsonl", "w") as f:
        for i, q in enumerate(questions, 1):
            r = copilot.ask(q["question"])
            r["id"] = q["id"]
            gens.append(r)
            f.write(json.dumps(r) + "\n")
            f.flush()
            print(f"[gen {i}/{len(questions)}] {q['id']} {r['latency_s']:.1f}s shown={r['shown_to_user']} {r['gate_reasons']}", flush=True)
    gen_model = gens[0]["model"]
    t_gen = time.time()

    # 2) judge (substantive answers only; "I don't know" is scored by rule)
    judge = judge_from_config(cfg, force_local=args.force_local)
    rows = []
    with open(out_dir / "judgments.jsonl", "w") as f:
        for i, (q, g) in enumerate(zip(questions, gens), 1):
            idk = is_idk(g["answer"])
            j = {"label": "abstained", "reason": "model said I don't know", "judge_model": None} if idk \
                else judge_one(judge, q, g["answer"])
            f.write(json.dumps({"id": q["id"], **j}) + "\n")
            f.flush()
            expected = [s for s in q["source"].split("|") if s]
            cited_pages = {c.split("#")[0] for c in g["valid_citations"]}
            retrieved_pages = {c["chunk_id"].split("#")[0] for c in g["retrieved"]}
            rows.append({
                "id": q["id"], "category": q["category"], "question": q["question"],
                "expected_answer": q["expected_answer"], "expected_source": q["source"],
                "answer": g["answer"], "shown_to_user": g["shown_to_user"],
                "gate_reasons": ";".join(g["gate_reasons"]), "confidence": g["confidence"],
                "model_said_idk": idk, "judge_label": j["label"], "judge_reason": j["reason"],
                "valid_citations": ";".join(g["valid_citations"]),
                "invalid_citations": ";".join(g["invalid_citations"]),
                "cited_expected_source": bool(cited_pages & set(expected)),
                "expected_source_retrieved": bool(retrieved_pages & set(expected)),
                "retrieved": ";".join(c["chunk_id"] for c in g["retrieved"]),
                "latency_s": g["latency_s"], "input_tokens": g["input_tokens"],
                "output_tokens": g["output_tokens"], "provider": g["provider"], "model": g["model"],
            })
            print(f"[judge {i}/{len(questions)}] {q['id']} {j['label']}", flush=True)
    judge_model = judge.model
    t_end = time.time()

    with open(out_dir / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    metrics = compute_metrics(rows, cfg, gen_model, judge_model)
    json.dump(metrics, open(out_dir / "metrics.json", "w"), indent=2)

    # 3) spot-check sheet: 20% stratified by category, fixed seed
    rng = random.Random(42)
    sample = []
    for c in sorted(set(r["category"] for r in rows)):
        items = [r for r in rows if r["category"] == c]
        sample += rng.sample(items, max(1, round(0.2 * len(items))))
    with open(out_dir / "spot_check.csv", "w", newline="") as f:
        cols = ["id", "category", "question", "expected_answer", "answer", "shown_to_user",
                "judge_label", "judge_reason"]
        w = csv.DictWriter(f, fieldnames=cols + ["human_label", "human_notes"])
        w.writeheader()
        for r in sample:
            w.writerow({**{k: r[k] for k in cols}, "human_label": "", "human_notes": ""})

    import llama_cpp, sentence_transformers
    json.dump({
        "run_name": args.run_name,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(t_start)),
        "generation_seconds": round(t_gen - t_start, 1),
        "judge_seconds": round(t_end - t_gen, 1),
        "generator_model": gen_model, "judge_model": judge_model,
        "embedding_model": cfg["embedding"]["model"],
        "overrides": overrides,
        "anthropic_key_present": bool(os.environ.get("ANTHROPIC_API_KEY")) and not args.force_local,
        "machine": {"platform": platform.platform(), "cpu_count": os.cpu_count(),
                    "python": platform.python_version()},
        "versions": {"llama_cpp_python": llama_cpp.__version__,
                     "sentence_transformers": sentence_transformers.__version__},
    }, open(out_dir / "run_info.json", "w"), indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
