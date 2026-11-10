# PRD: AI Support Copilot (Supabase Auth docs)

**Author:** Krupa Nirmal · **Status:** prototype, evaluated offline · **Corpus:** 41 public Supabase Auth docs pages (Apache-2.0)

## User
1. **End customer** (a developer building on Supabase) who has an Auth question and wants an answer now, not after a ticket round-trip.
2. **Support agent** who owns the human-review queue and handles anything the copilot is not confident about.

## Problem
Most Auth questions ("why did my invite redirect to the Site URL?", "how long is a magic link valid?") are already answered somewhere in the docs, but customers can't find the right paragraph and file tickets instead. A plain chatbot is risky: a confident wrong answer about auth settings can break a customer's login flow. We need an assistant that answers **only from the docs, shows its sources, and hands off to a human when it isn't sure**.

## Solution (prototype scope)
- Retrieval over the docs (local embeddings + FAISS) → LLM answer that must cite the passages it used and may say "I don't know".
- Confidence gate: answer is shown only if the retrieval score clears a threshold, the answer cites a retrieved passage, and the model didn't abstain. Everything else goes to a **human-review queue** (SQLite) with the draft attached.
- "Escalate to human" button on every answer.
- Offline eval set (50 questions written for this project) + one-command eval harness.

## Success metrics
| Metric | Why it matters | How it's measured here |
|---|---|---|
| **Pass rate** (primary) | Customer got a correct answer, or the bot correctly declined | LLM-judge label + gate decision, per question |
| **Hallucination rate of shown answers** (guardrail) | Wrong auth advice is worse than no answer | Judge label "hallucinated" among answers shown to the user |
| **Citation accuracy** | Customers and agents can verify the answer | Shown answer cites ≥1 chunk from the expected docs page |
| **Escalation rate** | Cost/load on the support team; too low = risky, too high = useless | Share of questions sent to the review queue |
| **Median latency** | Customers abandon slow chat | End-to-end seconds per question |
| **Cost per 100 queries** | Unit economics | Token usage × price (0 for the local model) |

Measured values are in the README results table; each one links to the raw run files. The launch bar is a **proposal** in README §Launch bar.

## Non-goals
- No account-specific actions (resetting a user's password, changing project settings).
- No answers outside the indexed docs (billing, other Supabase products, general Postgres).
- No multi-turn memory; each question is answered on its own.
- No real customer data: the eval questions were written for this project, not taken from user logs.

## Risks and mitigations
| Risk | Mitigation |
|---|---|
| Hallucinated settings, limits or prices | Answer only from retrieved context; citations required; gate + human queue; hallucination rate is a launch guardrail |
| Stale docs (limits change, e.g. default email rate limit) | Corpus pinned to a commit; re-ingest is one command; production would re-index on docs deploys |
| Over-escalation floods the support team | Track escalation rate per category; tune the threshold in `config.yaml` with data |
| Weak evaluator (small local judge) | 20% spot-check sheet for a human; re-run with a stronger judge (Claude) is one command |
| Prompt injection via docs content | Docs come from a trusted, pinned source; the model has no tools or actions |
