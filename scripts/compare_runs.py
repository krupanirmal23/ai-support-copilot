"""Build the before/after table from two metrics.json files (no hand-typed numbers).

    python scripts/compare_runs.py baseline iter1_prompt_v2 > eval/results/comparison.md
"""
import json
import sys

a, b = sys.argv[1], sys.argv[2]
A = json.load(open(f"eval/results/{a}/metrics.json"))
B = json.load(open(f"eval/results/{b}/metrics.json"))


def pct(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


rows = [
    ("Pass rate (all 50)", pct(A["pass_rate"]), pct(B["pass_rate"])),
    ("  answerable (30)", pct(A["pass_rate_by_category"]["answerable"]), pct(B["pass_rate_by_category"]["answerable"])),
    ("  partially answerable (10)", pct(A["pass_rate_by_category"]["partially answerable"]), pct(B["pass_rate_by_category"]["partially answerable"])),
    ("  out-of-scope (10)", pct(A["pass_rate_by_category"]["out-of-scope"]), pct(B["pass_rate_by_category"]["out-of-scope"])),
    ("Hallucination rate, answers shown to user", pct(A["hallucination_rate_shown"]), pct(B["hallucination_rate_shown"])),
    ("Hallucination rate, all drafts", pct(A["hallucination_rate_all_drafts"]), pct(B["hallucination_rate_all_drafts"])),
    ("Accuracy of answers shown", pct(A["accuracy_of_shown_answers"]), pct(B["accuracy_of_shown_answers"])),
    ("Citation accuracy (shown, in-scope)", pct(A["citation_accuracy"]), pct(B["citation_accuracy"])),
    ("Escalation rate (all 50)", pct(A["escalation_rate"]), pct(B["escalation_rate"])),
    ("  answerable", pct(A["escalation_rate_by_category"]["answerable"]), pct(B["escalation_rate_by_category"]["answerable"])),
    ("  out-of-scope", pct(A["escalation_rate_by_category"]["out-of-scope"]), pct(B["escalation_rate_by_category"]["out-of-scope"])),
    ("Retrieval hit rate @k (in-scope)", pct(A["retrieval_hit_rate_at_k"]), pct(B["retrieval_hit_rate_at_k"])),
    ("Median latency (s)", f"{A['median_latency_s']}", f"{B['median_latency_s']}"),
    ("p90 latency (s)", f"{A['p90_latency_s']}", f"{B['p90_latency_s']}"),
    ("Cost per 100 queries (USD)", f"{A['cost_per_100_queries_usd']}", f"{B['cost_per_100_queries_usd']}"),
]
print(f"Generator: {A['generator_model']} · Judge: {A['judge_model']}\n")
print(f"| Metric | {a} | {b} |\n|---|---|---|")
for r in rows:
    print(f"| {r[0]} | {r[1]} | {r[2]} |")
