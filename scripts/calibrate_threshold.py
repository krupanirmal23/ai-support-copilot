"""Pick the retrieval-score gate threshold on a small DEV set that is NOT part of eval/questions.csv.

Writes eval/calibration/dev_scores.json. The threshold is then set by hand in config.yaml.
"""
import json
import statistics

from copilot.config import load_config, p
from copilot.retrieve import Retriever

IN_SCOPE = [
    "How do I send a password reset email?",
    "How do I enable sign in with GitHub?",
    "What claims are always present in a Supabase JWT?",
    "How do I link a Google identity to an existing user?",
    "How do I verify a phone OTP?",
    "How do I customise the confirmation email template?",
    "How do I set up passkeys?",
    "What is the auth schema used for?",
]
OUT_OF_SCOPE = [
    "How do I set up Stripe billing webhooks?",
    "How do I create a cron job in Postgres?",
    "How do I upgrade my compute size?",
    "How do I write a database function in PL/pgSQL?",
    "How do I use Supabase with LangChain?",
    "How do I change my organization's billing email?",
    "What regions can I host my project in?",
    "How do I bulk import CSV data into a table?",
]


def main():
    cfg = load_config()
    r = Retriever(cfg)
    out = {"embedding_model": cfg["embedding"]["model"], "in_scope": [], "out_of_scope": []}
    for key, qs in (("in_scope", IN_SCOPE), ("out_of_scope", OUT_OF_SCOPE)):
        for q in qs:
            hits = r.search(q, k=1)
            out[key].append({"question": q, "top1_score": round(hits[0]["score"], 4),
                             "top1_chunk": hits[0]["chunk_id"]})
    for key in ("in_scope", "out_of_scope"):
        s = [x["top1_score"] for x in out[key]]
        out[f"{key}_summary"] = {"min": min(s), "median": statistics.median(s), "max": max(s)}
    json.dump(out, open(p("eval/calibration/dev_scores.json"), "w"), indent=2)
    print(json.dumps({k: v for k, v in out.items() if k.endswith("summary")}, indent=2))
    for key in ("in_scope", "out_of_scope"):
        for x in out[key]:
            print(key, x["top1_score"], x["question"])


if __name__ == "__main__":
    main()
