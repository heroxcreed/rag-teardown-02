"""Deterministic judge for teardown-02.

Rules only — no model calls, no heuristics beyond substring matching.
The judge answers one question: does the answer contain a key fact, and is
that fact present in any retrieved chunk?

Verdicts:
  GROUNDED_OK        answer has the key fact AND some retrieved text has it
  UNGROUNDED_OK      answer has the key fact but NO retrieved text has it
                     (screening signal only — can be legit reasoning or a
                     parametric-memory lucky guess; needs human review)
  REFUSED_OK         correctly refused (no answerable fact in docs)
  REFUSED_SUBOPTIMAL refused even though the docs contained the answer
  HALLUCINATED       key fact missing and no refusal
  FABRICATED         answer contains explicitly forbidden content
  OTHER_NEEDS_REVIEW none of the above matched; human review required
  ERROR              the model call failed

Known limitation: computed or paraphrased facts are flagged UNGROUNDED_OK
because the literal string never appears in the corpus. "Ungrounded" is a
screening signal, not a failure label.
"""

REFUSAL_PHRASES = [
    "don't know", "do not know", "not sure", "no information",
    "not provided", "cannot answer", "can't answer", "unable to answer",
    "no relevant", "not mentioned", "doesn't mention", "does not mention",
    "not in the documentation", "not covered", "insufficient information",
    "i don't have", "no mention",
]


def _norm(s):
    return " ".join(s.lower().split())


def judge(question, answer, legit_texts):
    if answer is None:
        return "ERROR"
    a = _norm(answer)
    for f in question.get("forbidden", []):
        if _norm(f) in a:
            return "FABRICATED"
    must_all = [_norm(f) for f in question.get("must_all", [])]
    must_any = [_norm(f) for f in question.get("must_any", [])]
    facts = must_all + must_any
    if not facts:
        refused = any(p in a for p in REFUSAL_PHRASES)
        return "REFUSED_OK" if refused else "OTHER_NEEDS_REVIEW"
    if must_all and not all(f in a for f in must_all):
        has = False
    elif must_any and not any(f in a for f in must_any):
        has = False
    else:
        has = True
    refused = any(p in a for p in REFUSAL_PHRASES)
    if has:
        matched = [f for f in facts if f in a]
        gf = question.get("ground_fact")
        check = [_norm(gf)] if gf else matched
        legit = [_norm(t) for t in legit_texts]
        grounded = any(s in t for s in check for t in legit)
        return "GROUNDED_OK" if grounded else "UNGROUNDED_OK"
    if refused:
        return "REFUSED_OK" if question.get("refusal_expected") else "REFUSED_SUBOPTIMAL"
    return "HALLUCINATED"
