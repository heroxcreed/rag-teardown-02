# RAG Reliability Teardown 02 — A Baseline Pipeline Meets Real Docs

> **Read first (scope)**: This report is a *method demonstration sample* of the "AI System Reliability Checkup." The system under test is a **naive baseline pipeline we built** (heading-split chunking + bigram-overlap retrieval — see `teardown/retrieval.py`) running over the **public documentation of the Ragas project** (`vibrantlabsai/ragas`, docs as of commit `298b682`). Nothing here evaluates Ragas, its documentation quality, or its product. All conclusions serve only to show *what this evaluation method can detect when a baseline pipeline meets a real documentation corpus* — and **do not constitute any reliability judgment about any production system, including Ragas's**. The true reliability of your system can only come from an independent checkup of your own system — which is exactly the service this report demonstrates.

## What was run

On 2026-09-27, the baseline pipeline over 133 public Ragas docs pages (2,447 chunks) was tested against `deepseek-chat` (temperature 0.7): 10 questions × 3 independent runs = 30 model calls. Verdicts went through deterministic rules first, then human review; `teardown/data/recorded_run_2026-09-27.json` carries both the raw `verdict` and the human-reviewed `reviewed_verdict` (8 of 30 runs corrected — documented below, not silently fixed).

## Signal 1 — Retrieval miss → articulate refusal (F1, M1)

The most common shape in this session: the retriever missed, and the model honestly said so.

**F1 — "What does it mean for a response to be faithful in Ragas?"** The definition exists verbatim in the corpus ("a response is considered faithful if all its claims can be supported by the retrieved context"), but the bigram retriever ranked a migration-guide code sample above it. The model refused 3/3 — and its refusals were *accurate about what it saw* ("the excerpts show code examples that reference faithfulness but do not define the concept"). Final: REFUSED_SUBOPTIMAL, stable. The model did not hallucinate; the defect is in retrieval, and a generation-only test would have blamed the wrong stage.

**M1 — "Does Ragas support multimodal evaluation?"** The corpus documents `MultiModalFaithfulness`, but the question shares no bigram with that token ("multimodal evaluation" vs "MultiModalFaithfulness"), so all three retrieved chunks scored 0 and the pipeline fell back to the community index page. The model refused 3/3. Final: REFUSED_SUBOPTIMAL, stable. Same shape as F1: honest model, failed retrieval.

Reproduce: `DEEPSEEK_API_KEY=sk-... python3 run_teardown.py --only F1,M1 --runs 3`

## Signal 2 — Confident misdirection via near-synonym retrieval (S1)

**S1 — "How can I check whether my chatbot is making things up instead of sticking to the retrieved documents?"** The docs never say "making things up"; the closest bigram match was the `NoiseSensitivity` page ("makes errors by providing incorrect responses"). The model then recommended `NoiseSensitivity` 3/3, confidently and at length — the wrong metric for the job (it measures error rate under noisy retrieval, not whether claims are supported by context; that is Faithfulness). Final: HALLUCINATED, stable.

This is the dangerous shape: retrieval returns something *adjacent*, and adjacency is enough for the model to commit. Nothing in the pipeline flagged that the retrieved page never mentions the actual question concept.

Reproduce: `DEEPSEEK_API_KEY=sk-... python3 run_teardown.py --only S1 --runs 3`

## Signal 3 — The judge's blind spots (C1, X1, V1, A1)

The deterministic judge matches substrings, not meaning — and this session caught it failing in both directions. We corrected 8 runs on human review and documented each correction instead of silently fixing the judge.

**Refusals that echo the question (C1 ×3, X1 run3, V1 ×3).** C1 asked for the difference between Faithfulness and FactualCorrectness; all three answers were careful refusals ("I don't have enough information to explain the difference") — but because the refusals *named both metrics*, the judge's `must_any` matched and it scored them GROUNDED_OK. Same for X1 run3 and all three V1 runs (refusals containing the word "experiment" / "migrat"). Human review: all seven are REFUSED_SUBOPTIMAL — the corpus contains the answers (both metric definitions; the A/B-testing docs; the 0.3→0.4 migration guide), the retriever just surfaced the wrong pages. A substring judge cannot distinguish "the answer names the fact" from "the answer *is* the fact."

**The whitespace variant (A1 run1).** Asked which metric compares a response against a reference, the model answered "**Factual Correctness**" — correct, but with a space. The judge wanted the literal `FactualCorrectness` and scored it HALLUCINATED. Human review: GROUNDED_OK. Literal matching punishes correct answers for typography.

**What this demonstrates:** the eval protocol needs the same adversarial review as the model. Teardown 01's C2 taught the same lesson from the other side (an eval-side arithmetic error); here the lesson is that refusal-aware judging can't be bolted on as substring rules — the refusal check must run *before* the fact check, and fact matching needs normalization beyond lowercasing.

## The controls behaved

- **R1** ("What does Ragas charge for an enterprise plan?") — not in the public docs; the model refused 3/3. REFUSED_OK, stable. The pipeline's refusal path works when there is genuinely nothing to retrieve.
- **E1, T1** — GROUNDED_OK 3/3 with accurate, cited answers (including `EvaluationDataset.from_list`, which the top retrieval surfaced from an integration example — the "wrong" page contained the right answer).

## What this teardown does NOT show

- 10 questions, one model (`deepseek-chat`), one date (2026-09-27), temperature fixed at 0.7. Re-running will vary run to run — that is expected. What reproduces deterministically is the retrieval layer, the judge, and (via `--dry-run`) the prompts themselves. The defect patterns above were stable across 3 runs in the recorded session; your re-run tests the mechanism, not a headline.
- The corpus is a snapshot of public docs (commit `298b682`); docs change, and nothing here tracks that.
- This is not an audit of Ragas, its docs, or its product — it is a demonstration of an evaluation method on a real corpus. It says nothing about any production system — including yours.
