"""
retriever.py — 2-stage hybrid retrieval engine.
Stage 1: Metadata-filtered vector search (NO global retrieval)
Stage 2: Re-rank by keyword overlap + source quality + grade + semantic score

ZERO HALLUCINATION — only returns verified database content.
"""
import re
import chromadb
from chromadb.utils import embedding_functions
from config import (
    CHROMA_PATH, COLLECTION_NAME, MIN_SCORE_THRESHOLD,
    MIN_CHUNK_LENGTH, NOISE_PATTERNS, MAX_CONTEXT_CHARS,
    INTENT_TYPE_FILTER, SOURCE_PRIORITY, GRADE_SCORES,
    INTENT_FIQH, INTENT_DUA, INTENT_HADITH,
    INTENT_QURAN, INTENT_TAFSEER, INTENT_MIXED
)

_collection = None


def get_collection():
    global _collection
    if _collection is None:
        ef = embedding_functions.DefaultEmbeddingFunction()
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_collection(
            name=COLLECTION_NAME, embedding_function=ef
        )
    return _collection


# ═══════════════════════════════════════════════════════
#  STAGE 1 HELPERS
# ═══════════════════════════════════════════════════════

def _validate_chunk(doc: str, meta: dict) -> bool:
    """Strict validation — reject invalid/noise chunks."""
    if not isinstance(meta, dict):
        return False
    if not meta.get("source") or not meta.get("type"):
        return False
    if not doc or len(doc.strip()) < MIN_CHUNK_LENGTH:
        return False
    doc_lower = doc.lower().strip()
    for pattern in NOISE_PATTERNS:
        if pattern in doc_lower and len(doc.strip()) < 250:
            return False
    return True


def _build_where_filter(intent: str, source_filter: str) -> dict | None:
    """
    Build strict ChromaDB metadata filter.
    NEVER returns None for typed intents — always filter.
    """
    # UI filter overrides everything
    ui_map = {
        "Hadith Only":       {"type": "hadith"},
        "Quran Only":        {"type": "quran"},
        "Dua Only":          {"type": "dua"},
        "Hadith Qudsi Only": {"type": "hadith_qudsi"},
        "Tafseer Only":      {"type": "tafseer"},
        "Fiqh Only":         {"type": "fiqh"},
    }
    if source_filter in ui_map:
        return ui_map[source_filter]

    # DUA: absolute strict — ONLY dua type
    if intent == INTENT_DUA:
        return {"type": "dua"}

    # QURAN: only quran type
    if intent == INTENT_QURAN:
        return {"type": "quran"}

    # TAFSEER: tafseer + quran
    if intent == INTENT_TAFSEER:
        return {"$or": [{"type": "tafseer"}, {"type": "quran"}]}

    # HADITH: hadith + hadith_qudsi
    if intent == INTENT_HADITH:
        return {"$or": [{"type": "hadith"}, {"type": "hadith_qudsi"}]}

    # FIQH: fiqh first, hadith as support
    if intent == INTENT_FIQH:
        return {"$or": [{"type": "fiqh"}, {"type": "hadith"}]}

    # MIXED / GENERAL: no filter (all sources)
    return None


# ═══════════════════════════════════════════════════════
#  STAGE 2 — RE-RANKING
# ═══════════════════════════════════════════════════════

def _keyword_overlap_score(text: str, query: str) -> float:
    """Score how many query keywords appear in the chunk text."""
    query_words = set(re.findall(r'\b\w{3,}\b', query.lower()))
    text_words  = set(re.findall(r'\b\w{3,}\b', text.lower()))
    if not query_words:
        return 0.0
    overlap = query_words & text_words
    return (len(overlap) / len(query_words)) * 15.0


def _exact_phrase_score(text: str, query: str) -> float:
    """Boost if exact phrase from query appears in text."""
    q = query.lower().strip()
    t = text.lower()
    # Check 3+ word phrases
    words = q.split()
    if len(words) >= 3:
        for i in range(len(words) - 2):
            phrase = " ".join(words[i:i+3])
            if phrase in t:
                return 10.0
    return 0.0


def _source_quality_score(chunk: dict, intent: str) -> float:
    """Score based on source type priority and hadith grade."""
    score = 0.0
    ctype = chunk.get("type", "")
    grade = str(chunk.get("grade", "")).lower().strip()

    # Source type priority boost
    priority = SOURCE_PRIORITY.get(ctype, 7)
    score += (8 - priority) * 2.0   # lower priority number = higher score

    # Intent type match boost — strict separation
    expected = INTENT_TYPE_FILTER.get(intent, [])
    if expected and ctype in expected:
        # Primary match (first in list = most preferred)
        if ctype == expected[0]:
            score += 20.0
        else:
            score += 8.0
    elif expected and ctype not in expected:
        score -= 15.0   # hard penalty for wrong type

    # Grade boost
    for grade_key, grade_boost in GRADE_SCORES.items():
        if grade_key in grade:
            score += grade_boost
            break

    # Arabic content boost
    if chunk.get("has_arabic") == "yes":
        score += 3.0

    # Completeness boost
    text_len = len(chunk.get("text", ""))
    if text_len > 500:
        score += 3.0
    elif text_len > 300:
        score += 1.5
    elif text_len < 150:
        score -= 2.0

    return score


def _rerank(chunks: list, original_query: str, intent: str) -> list:
    """
    Stage 2 re-ranking combining:
    - Semantic similarity score (from vector search)
    - Keyword overlap score
    - Exact phrase match score
    - Source quality + type priority score
    - Grade score
    """
    for c in chunks:
        semantic  = c["score"]
        keyword   = _keyword_overlap_score(c["text"], original_query)
        phrase    = _exact_phrase_score(c["text"], original_query)
        quality   = _source_quality_score(c, intent)
        c["final_score"] = round(semantic + keyword + phrase + quality, 2)

    chunks.sort(key=lambda x: x["final_score"], reverse=True)
    return chunks


def _deduplicate(chunks: list) -> list:
    """Remove duplicates by Arabic fingerprint or source+ref."""
    seen_arabic = set()
    seen_ref    = set()
    out = []
    for c in chunks:
        text = c.get("text", "")

        ar_match = re.search(r'\[Arabic\]\n(.{30,})', text, re.DOTALL)
        if ar_match:
            ar_fp = ar_match.group(1)[:80].strip()
            if ar_fp in seen_arabic:
                continue
            seen_arabic.add(ar_fp)

        ref_key = f"{c.get('source','')}_{c.get('hadith_number','')}"
        if ref_key and ref_key not in ("_?", "_None", "_") and ref_key in seen_ref:
            continue
        seen_ref.add(ref_key)
        out.append(c)
    return out


# ═══════════════════════════════════════════════════════
#  MAIN SEARCH FUNCTION
# ═══════════════════════════════════════════════════════

def search(queries: list, intent: str, n: int = 7,
           source_filter: str = "All Sources") -> list:
    """
    2-stage hybrid retrieval:
    Stage 1 — metadata-filtered vector search (top 20 candidates)
    Stage 2 — re-rank by keyword + quality + grade + semantic score → top n

    Returns empty list if nothing passes validation thresholds.
    """
    try:
        col = get_collection()
    except Exception:
        return []

    total = col.count()
    if total == 0:
        return []

    # Stage 1: retrieve more candidates for re-ranking
    n_candidates = min(20, total)
    where = _build_where_filter(intent, source_filter)
    seen_fp: dict = {}

    for query in queries:
        kwargs = dict(
            query_texts=[query],
            n_results=n_candidates,
            include=["documents", "distances", "metadatas"]
        )
        if where:
            kwargs["where"] = where

        try:
            results = col.query(**kwargs)
        except Exception:
            # If filter matched nothing, retry without filter only for mixed/general
            if intent in (INTENT_MIXED, "general"):
                kwargs.pop("where", None)
                try:
                    results = col.query(**kwargs)
                except Exception:
                    continue
            else:
                continue

        docs      = results.get("documents",  [[]])[0] or []
        distances = results.get("distances",  [[]])[0] or []
        metadatas = results.get("metadatas",  [[]])[0] or []

        for doc, dist, meta in zip(docs, distances, metadatas):
            if not isinstance(meta, dict):
                meta = {}

            score = round((1 - dist) * 100, 1)

            # Hard minimum threshold
            if score < MIN_SCORE_THRESHOLD:
                continue

            # Strict validation
            if not _validate_chunk(doc, meta):
                continue

            fp = doc[:100].strip()
            if fp not in seen_fp or score > seen_fp[fp]["score"]:
                seen_fp[fp] = {
                    "text":          doc,
                    "source":        str(meta.get("source", "Unknown")),
                    "hadith_number": str(meta.get("hadith_number",
                                         meta.get("idInBook",
                                         meta.get("number", "?")))),
                    "grade":         str(meta.get("grade", "")),
                    "type":          str(meta.get("type", "text")),
                    "score":         score,
                    "chapter":       str(meta.get("chapter",
                                         meta.get("chapter_name", ""))),
                    "has_arabic":    str(meta.get("has_arabic", "no")),
                    "surah":         str(meta.get("surah", "")),
                    "ayah":          str(meta.get("ayah", "")),
                }

    if not seen_fp:
        return []

    candidates = list(seen_fp.values())

    # Stage 2: re-rank top 20 candidates
    candidates = _rerank(candidates, queries[0], intent)

    # Deduplication
    candidates = _deduplicate(candidates)

    return candidates[:n]


# ═══════════════════════════════════════════════════════
#  CONTEXT FORMATTING — SEPARATED BY TYPE
# ═══════════════════════════════════════════════════════

def format_context(chunks: list) -> str:
    """
    Format retrieved chunks separated by type.
    This prevents semantic contamination between source types.
    """
    # Group by type
    groups = {}
    for c in chunks:
        t = c.get("type", "text")
        groups.setdefault(t, []).append(c)

    type_labels = {
        "quran":        "QURAN CONTEXT",
        "tafseer":      "TAFSEER CONTEXT",
        "hadith_qudsi": "HADITH QUDSI CONTEXT",
        "hadith":       "HADITH CONTEXT",
        "fiqh":         "FIQH CONTEXT",
        "dua":          "DUA / DHIKR CONTEXT",
    }

    # Priority order for display
    type_order = ["quran", "tafseer", "hadith_qudsi", "hadith", "fiqh", "dua"]
    remaining  = [t for t in groups if t not in type_order]

    sections = []
    for t in type_order + remaining:
        if t not in groups:
            continue
        label   = type_labels.get(t, t.upper() + " CONTEXT")
        section = [f"{'═'*55}", f"[{label}]", f"{'═'*55}"]

        for i, c in enumerate(groups[t]):
            lines = [f"\n[Source {i+1}]"]
            lines.append(f"Book    : {c['source']}")
            ref = c.get("hadith_number", "")
            if ref and ref not in ("?", "None", ""):
                lines.append(f"Ref     : #{ref}")
            surah = c.get("surah", "")
            ayah  = c.get("ayah", "")
            if surah and surah not in ("", "None"):
                lines.append(f"Verse   : {surah}:{ayah}")
            chapter = c.get("chapter", "")
            if chapter and chapter not in ("", "None"):
                lines.append(f"Chapter : {chapter[:60]}")
            grade = c.get("grade", "")
            lines.append(f"Grade   : {grade if grade and grade not in ('','None') else 'Not specified'}")
            lines.append(f"Type    : {c['type']}")
            lines.append(f"Match   : {c['score']}%")
            lines.append("")
            lines.append(c["text"])
            section.append("\n".join(lines))

        sections.append("\n".join(section))

    context = "\n\n".join(sections)
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n\n[...truncated...]"
    return context


def db_stats() -> dict:
    try:
        col = get_collection()
        return {"total": col.count(), "ready": True}
    except Exception as e:
        return {"total": 0, "ready": False, "error": str(e)}
