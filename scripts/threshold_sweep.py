"""Replay the confidence gate at different thresholds on a finished run (no new model calls).

    python scripts/threshold_sweep.py iter1_prompt_v2
Writes eval/results/<run>/threshold_sweep.csv. In-sample: use it to pick a threshold to
*re-test*, not as a held-out result.
"""
import csv
import sys

run = sys.argv[1]
rows = list(csv.DictReader(open(f"eval/results/{run}/results.csv")))
out = []
for t in [0.60, 0.65, 0.68, 0.70, 0.72, 0.75, 0.78, 0.80]:
    n = len(rows)
    passed = shown = halluc = 0
    for r in rows:
        other_ok = r["model_said_idk"] == "False" and r["valid_citations"] != ""
        s = other_ok and float(r["confidence"]) >= t
        shown += s
        halluc += s and r["judge_label"] == "hallucinated"
        if r["category"] == "out-of-scope":
            passed += not s
        else:
            passed += s and r["judge_label"] == "correct"
    out.append({"threshold": t, "pass_rate": round(passed / n, 4),
                "escalation_rate": round(1 - shown / n, 4),
                "hallucination_rate_shown": round(halluc / shown, 4) if shown else ""})
with open(f"eval/results/{run}/threshold_sweep.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
for o in out:
    print(o)
