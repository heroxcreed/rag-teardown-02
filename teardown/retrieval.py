"""Baseline retrieval layer for the teardown-02 demo pipeline.

This is a deliberately NAIVE baseline, not a production retriever: it exists
so the teardown can study how ordinary pipeline choices interact with a real
documentation corpus (Ragas public docs). Every choice below is documented;
nothing here pretends to be state of the art.

Baseline choices (under study, not hidden):
  chunking:
    1. split on markdown headings; each section is one chunk;
    2. sections longer than CHUNK_MAX_CHARS are hard-cut with no overlap —
       long reference pages get sliced mid-paragraph;
    3. code fences are kept inline (not separated), so a chunk can be
       dominated by code tokens that drown out prose;
  retrieval:
    1. word-bigram overlap only — synonym queries ("grade answers" vs
       "answer correctness") score ~0;
    2. no relevance threshold — top-k chunks are returned even when the best
       score is 0, so the generator answers from whatever came back.

Deterministic: ties broken by document order, then chunk order.
"""

import os
import re

CHUNK_MAX_CHARS = 1500
TOP_K = 3
KB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "kb")


def load_documents(kb_dir=KB_DIR):
    docs = []
    for name in sorted(os.listdir(kb_dir)):
        if name.endswith(".md"):
            with open(os.path.join(kb_dir, name), encoding="utf-8") as f:
                docs.append((name, f.read()))
    return docs


def split_sections(text):
    """Split markdown into (heading, section_text) on ATX headings."""
    parts = re.split(r"(?m)^(#{1,4}\s+.*)$", text)
    sections = []
    if parts[0].strip():
        sections.append(("(preamble)", parts[0]))
    for i in range(1, len(parts) - 1, 2):
        heading = parts[i].strip()
        body = parts[i + 1]
        sections.append((heading, heading + "\n" + body))
    return sections


def chunk_text(text, max_chars=CHUNK_MAX_CHARS):
    chunks = []
    for heading, section in split_sections(text):
        s = section.strip()
        if not s:
            continue
        while len(s) > max_chars:
            chunks.append((heading, s[:max_chars]))
            s = s[max_chars:]
        chunks.append((heading, s))
    return chunks


def build_chunks(kb_dir=KB_DIR):
    result = []
    for doc_id, text in load_documents(kb_dir):
        for i, (heading, ctext) in enumerate(chunk_text(text)):
            result.append((doc_id, heading, i, ctext))
    return result


_STOPWORDS = frozenset(
    "the a an of to in for on with and or is are was were be been by as at "
    "from that this it its into than then so such no not can how what which "
    "who when where why do does did will would should could have has had "
    "there their them they we you your our us about over under between "
    "both each other more most some any all only also just very use used "
    "using per via within without".split()
)


def _tokens(text):
    return [t for t in re.findall(r"[a-z0-9]+", text.lower())
            if t not in _STOPWORDS and len(t) > 1]


def _bigrams(text):
    toks = _tokens(text)
    return {" ".join(toks[i:i + 2]) for i in range(len(toks) - 1)} or set(_tokens(text))


def retrieve(question, chunks, top_k=TOP_K):
    """Returns [(score, doc_id, heading, chunk_index, chunk_text)], score desc,
    then document order asc. Deterministic. Returns top_k even if best is 0."""
    q = _bigrams(question)
    scored = []
    for order, (doc_id, heading, idx, ctext) in enumerate(chunks):
        scored.append((len(q & _bigrams(ctext)), order, doc_id, heading, idx, ctext))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [(s, doc_id, heading, i, t) for s, _, doc_id, heading, i, t in scored[:top_k]]
