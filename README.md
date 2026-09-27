# rag-teardown-02 — Reproducible RAG Reliability Teardown (public-docs corpus)

> **Read first (scope)**: This report is a *method demonstration sample* of the "AI System Reliability Checkup." The system under test is a **naive baseline pipeline we built** (heading-split chunking + bigram-overlap retrieval) running over the **public documentation of the Ragas project** (`vibrantlabsai/ragas`, docs as of commit `298b682`). Nothing here evaluates Ragas, its documentation, or its product. All conclusions serve only to show *what this evaluation method can detect* and **do not constitute any reliability judgment about any production system — including yours**. The true reliability of your system can only come from an independent checkup of your own system — which is exactly the service this report demonstrates.

## What this is

Teardown 01 ran the method against a small fictional corpus with known seeded defects. Teardown 02 runs the same method against a **real documentation corpus**: 133 pages of public Ragas docs (2,447 chunks), a deliberately naive baseline pipeline, and `deepseek-chat`. On 2026-09-27 we ran 10 questions × 3 runs (30 model calls, temperature 0.7) and caught three failure signals: **retrieval miss → articulate refusal**, **confident misdirection via near-synonym retrieval**, and **the judge's own blind spots** (8 of 30 runs needed human-review correction — documented, not silently fixed). This repo ships all 10 questions, the exact retrieval code, the deterministic judge, and the recorded answers — so you can re-run the mechanism instead of taking our word for it. The story of each signal is in [NOTES.md](NOTES.md).

## Reproduce in 3 steps

```bash
git clone https://github.com/heroxcreed/rag-teardown-02.git
cd rag-teardown-02

# 1) Inspect without spending a cent: prompts + retrieval, no API calls
python3 teardown/run_teardown.py --dry-run

# 2) Full reproduction (~10 model calls, 1 run per question)
DEEPSEEK_API_KEY=sk-... python3 teardown/run_teardown.py

# 3) Compare your verdicts against the recorded session
#    teardown/data/recorded_run_2026-09-27.json
#    (raw `verdict` = pipeline output; `reviewed_verdict` = human-reviewed final)
```

Targeted re-runs: `python3 teardown/run_teardown.py --only F1,M1 --runs 3`, `--only S1 --runs 3`, `--only C1,X1,V1,A1 --runs 3`.

## Requirements

- Python 3.8+, standard library only (no `pip install` needed).
- A DeepSeek API key (`DEEPSEEK_API_KEY`), billed to your own account. The script reads it from the environment, never stores it, never logs it. Without it, only `--dry-run` works.

## The 10 questions (sampling logic)

One reproducible example per signal, plus the controls that keep the interpretation honest — all drawn from the recorded 2026-09-27 session:

| ID | Signal | Role in this teardown |
|----|--------|----------------------|
| F1 | retrieval miss → refusal | signal example: faithfulness definition exists in corpus, retriever ranked a migration guide above it; model refused 3/3, accurately describing what it saw |
| M1 | retrieval miss → refusal | signal example: `MultiModalFaithfulness` documented, but zero bigram overlap ("multimodal evaluation"); fallback to community page, refusal 3/3 |
| S1 | confident misdirection | signal example: "making things up" bigram-matched `NoiseSensitivity`; model recommended the wrong metric 3/3, at length |
| C1 | judge blind spot | 3/3 articulate refusals scored GROUNDED_OK because the refusals named both metrics; human review → REFUSED_SUBOPTIMAL |
| X1 | judge blind spot | run3 refusal containing "experiment" scored GROUNDED_OK; human review → REFUSED_SUBOPTIMAL |
| V1 | judge blind spot | 3/3 refusals containing "migrat" scored GROUNDED_OK; human review → REFUSED_SUBOPTIMAL |
| A1 | judge blind spot | run1 correct answer "Factual Correctness" (with space) scored HALLUCINATED; human review → GROUNDED_OK |
| E1 | grounded control | `EvaluationDataset.from_list` correctly cited 3/3 — the "wrong" top hit contained the right answer |
| T1 | grounded control | `TestsetGenerator` correctly cited 3/3 |
| R1 | refusal control | enterprise pricing not in public docs; correct refusal 3/3 |

## Honesty notes

- 10 questions; single model (`deepseek-chat`); single date (2026-09-27); temperature fixed at 0.7.
- `recorded_run_2026-09-27.json` carries both the deterministic `verdict` and the **human-reviewed `reviewed_verdict`**. 8 of 30 runs were corrected on review (C1 ×3, X1 run3, A1 run1, V1 ×3) — each correction is documented in NOTES.md "Signal 3". Fresh re-runs use the deterministic judge only; run-to-run variation is expected (sampling), the defect patterns were stable across 3 runs in the recorded session.
- The corpus is a snapshot of **public** Ragas documentation (commit `298b682`); only markdown docs pages, no notebooks, no code. Nothing was taken from behind a login.
- Corpus and questions are in English: this retrieval layer is language-sensitive; translating them changes the results.
- This is a method demonstration, not an audit of Ragas or its documentation. It says nothing about any production system — including yours.
- Contact: heroxcreed — heroxcreed275@gmail.com (email only, no calls).
