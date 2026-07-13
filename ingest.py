"""
Islamic RAG — Complete Ingest Script
======================================
Ingests ALL available Islamic text files into ChromaDB.
Each chunk contains BOTH Arabic + English so Arabic queries work natively.

Files covered:
  ROOT format  (bukhari.json etc.)      → {"metadata":..., "hadiths":[...]}
  DATA format  (data/hadith-json/...)   → {"id","metadata","chapters","hadiths":[{arabic, english:{narrator,text}}]}
  RIYAD format (riyadussalihin.json)    → same as DATA format
  FORTIES      (nawawi40, qudsi40)      → {"id","metadata","chapters","hadiths":[...]}
  HISNUL MUSLIM (hisnulmuslim.txt)      → plain text, chunked by section
  QURAN        (quran-english.json)     → verse list
  TAFSEER      (en-tafsir-ibn-kathir)   → small JSON
"""

import os
import json
import re
import time
import chromadb
from chromadb.utils import embedding_functions

# ── CONFIG ────────────────────────────────────────────
CHROMA_PATH     = "./chroma_db"
COLLECTION_NAME = "islamic_texts"
BATCH_SIZE      = 200      # items per ChromaDB upsert call

# ── CONNECT CHROMADB ──────────────────────────────────
ef     = embedding_functions.DefaultEmbeddingFunction()
client = chromadb.PersistentClient(path=CHROMA_PATH)
col    = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=ef,
    metadata={"hnsw:space": "cosine"}
)

print(f"✅ Connected to ChromaDB — existing docs: {col.count():,}\n")


# ══════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════

def safe_str(val):
    return str(val).strip() if val else ""

def make_chunk_text(arabic: str, narrator: str, english: str) -> str:
    """
    Build the document text stored in ChromaDB.
    Arabic is included so Arabic-script queries match directly.
    English is included for English / Roman-Urdu queries.
    Format:
        [Arabic]
        <arabic text>

        [English]
        Narrator: ...
        <english text>
    """
    parts = []
    if arabic and arabic.strip():
        parts.append(f"[Arabic]\n{arabic.strip()}")
    eng_parts = []
    if narrator and narrator.strip():
        eng_parts.append(f"Narrator: {narrator.strip()}")
    if english and english.strip():
        eng_parts.append(english.strip())
    if eng_parts:
        parts.append("[English]\n" + "\n".join(eng_parts))
    return "\n\n".join(parts)

def upsert_batch(documents, ids, metadatas):
    """Upsert in batches, skip duplicates gracefully."""
    for i in range(0, len(documents), BATCH_SIZE):
        col.upsert(
            documents=documents[i:i+BATCH_SIZE],
            ids=ids[i:i+BATCH_SIZE],
            metadatas=metadatas[i:i+BATCH_SIZE],
        )

def already_ingested(prefix: str) -> bool:
    """Quick check: does ChromaDB already have docs with this source prefix?"""
    try:
        r = col.get(where={"source": prefix}, limit=1)
        return len(r["ids"]) > 0
    except Exception:
        return False


# ══════════════════════════════════════════════════════
#  FORMAT A — ROOT JSON  {"metadata":..., "hadiths":[...]}
#  Files: bukhari.json, muslim.json, abudawud.json,
#         tirmidhi.json, ibnmajah.json, nasai.json
# ══════════════════════════════════════════════════════

ROOT_HADITH_FILES = [
    ("bukhari.json",    "Sahih Bukhari",      "hadith"),
    ("muslim.json",     "Sahih Muslim",       "hadith"),
    ("abudawud.json",   "Sunan Abu Dawud",    "hadith"),
    ("tirmidhi.json",   "Jami Tirmidhi",      "hadith"),
    ("ibnmajah.json",   "Sunan Ibn Majah",    "hadith"),
    ("nasai.json",      "Sunan an-Nasai",     "hadith"),
    ("darimi.json",     "Sunan al-Darimi",    "hadith"),
    ("malik.json",      "Muwatta Malik",      "hadith"),
    ("ahmad.json",      "Musnad Ahmad",       "hadith"),
    ("mishkat.json",    "Mishkat al-Masabih", "hadith"),
    ("bulugh.json",     "Bulugh al-Maram",    "hadith"),
]

def ingest_root_format(filepath: str, source_name: str, doc_type: str):
    if not os.path.exists(filepath):
        print(f"  ⚠️  Not found: {filepath}")
        return 0
    if already_ingested(source_name):
        print(f"  ✅ Already ingested: {source_name}")
        return 0

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    hadiths = []
    if isinstance(data, dict):
        hadiths = data.get("hadiths", [])
    elif isinstance(data, list):
        hadiths = data

    docs, ids, metas = [], [], []
    for h in hadiths:
        if not isinstance(h, dict):
            continue
        arabic   = safe_str(h.get("arabic", ""))
        eng      = h.get("english", {})
        if isinstance(eng, str):
            narrator, english = "", eng
        elif isinstance(eng, dict):
            narrator = safe_str(eng.get("narrator", ""))
            english  = safe_str(eng.get("text", ""))
        else:
            continue

        text = make_chunk_text(arabic, narrator, english)
        if len(text.strip()) < 20:
            continue

        hadith_id = safe_str(h.get("id", h.get("idInBook", "")))
        grade     = safe_str(h.get("grade", h.get("status", "")))
        chapter   = safe_str(h.get("chapterId", ""))

        docs.append(text)
        ids.append(f"{source_name.replace(' ','_')}_{hadith_id}")
        metas.append({
            "source":        source_name,
            "type":          doc_type,
            "hadith_number": hadith_id,
            "grade":         grade,
            "chapter":       chapter,
            "has_arabic":    "yes" if arabic else "no",
        })

    if docs:
        upsert_batch(docs, ids, metas)
    print(f"  ✅ {source_name}: {len(docs):,} hadiths ingested")
    return len(docs)


# ══════════════════════════════════════════════════════
#  FORMAT B — DATA/HADITH-JSON  {"id","metadata","chapters","hadiths":[...]}
#  Files: data/hadith-json/db/by_book/...
# ══════════════════════════════════════════════════════

DATA_HADITH_FILES = [
    ("data/hadith-json/db/by_book/the_9_books/bukhari.json",               "Sahih Bukhari",           "hadith"),
    ("data/hadith-json/db/by_book/the_9_books/muslim.json",                "Sahih Muslim",            "hadith"),
    ("data/hadith-json/db/by_book/the_9_books/abudawud.json",              "Sunan Abu Dawud",         "hadith"),
    ("data/hadith-json/db/by_book/the_9_books/ibnmajah.json",              "Sunan Ibn Majah",         "hadith"),
    ("data/hadith-json/db/by_book/the_9_books/malik.json",                 "Muwatta Malik",           "hadith"),
    ("data/hadith-json/db/by_book/the_9_books/darimi.json",                "Sunan al-Darimi",         "hadith"),
    ("data/hadith-json/db/by_book/the_9_books/ahmed.json",                 "Musnad Ahmad",            "hadith"),
    ("data/hadith-json/db/by_book/other_books/riyad_assalihin.json",       "Riyad as-Salihin",        "hadith"),
    ("data/hadith-json/db/by_book/other_books/bulugh_almaram.json",        "Bulugh al-Maram",         "hadith"),
    ("data/hadith-json/db/by_book/other_books/mishkat_almasabih.json",     "Mishkat al-Masabih",      "hadith"),
    ("data/hadith-json/db/by_book/other_books/aladab_almufrad.json",       "Al-Adab Al-Mufrad",       "hadith"),
    ("data/hadith-json/db/by_book/other_books/shamail_muhammadiyah.json",  "Shamail Muhammadiyah",    "hadith"),
    ("data/hadith-json/db/by_book/forties/nawawi40.json",                  "Forty Hadith Nawawi",     "hadith"),
    ("data/hadith-json/db/by_book/forties/qudsi40.json",                   "Forty Hadith Qudsi",      "hadith_qudsi"),
    ("data/hadith-json/db/by_book/forties/shahwaliullah40.json",           "Forty Hadith Shah Wali",  "hadith"),
]

def ingest_data_format(filepath: str, source_name: str, doc_type: str):
    if not os.path.exists(filepath):
        print(f"  ⚠️  Not found: {filepath}")
        return 0
    if already_ingested(source_name):
        print(f"  ✅ Already ingested: {source_name}")
        return 0

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    hadiths = []
    if isinstance(data, dict):
        hadiths = data.get("hadiths", [])
    elif isinstance(data, list):
        hadiths = data

    docs, ids, metas = [], [], []
    for h in hadiths:
        if not isinstance(h, dict):
            continue
        arabic   = safe_str(h.get("arabic", ""))
        eng      = h.get("english", {})
        if isinstance(eng, str):
            narrator, english = "", eng
        elif isinstance(eng, dict):
            narrator = safe_str(eng.get("narrator", ""))
            english  = safe_str(eng.get("text", ""))
        else:
            continue

        text = make_chunk_text(arabic, narrator, english)
        if len(text.strip()) < 20:
            continue

        hadith_id = safe_str(h.get("idInBook", h.get("id", "")))
        grade     = safe_str(h.get("grade", ""))
        chapter   = safe_str(h.get("chapterId", ""))

        uid = f"{source_name.replace(' ','_')}_data_{hadith_id}"
        docs.append(text)
        ids.append(uid)
        metas.append({
            "source":        source_name,
            "type":          doc_type,
            "hadith_number": hadith_id,
            "grade":         grade,
            "chapter":       chapter,
            "has_arabic":    "yes" if arabic else "no",
        })

    if docs:
        upsert_batch(docs, ids, metas)
    print(f"  ✅ {source_name} (data/): {len(docs):,} hadiths ingested")
    return len(docs)


# ══════════════════════════════════════════════════════
#  STANDALONE FORTIES — nawawi40.json / qudsi40.json
#  in root directory  {"id","metadata","chapters","hadiths"?}
# ══════════════════════════════════════════════════════

FORTIES_FILES = [
    ("nawawi40.json",  "Forty Hadith Nawawi",    "hadith"),
    ("qudsi40.json",   "Forty Hadith Qudsi",     "hadith_qudsi"),
]

def ingest_forties(filepath: str, source_name: str, doc_type: str):
    if not os.path.exists(filepath):
        print(f"  ⚠️  Not found: {filepath}")
        return 0
    if already_ingested(source_name):
        print(f"  ✅ Already ingested: {source_name}")
        return 0

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    hadiths = []
    if isinstance(data, dict):
        hadiths = data.get("hadiths", [])
        # Some forties store under chapters
        if not hadiths:
            chapters = data.get("chapters", [])
            for ch in chapters:
                if isinstance(ch, dict):
                    hadiths += ch.get("hadiths", [])
    elif isinstance(data, list):
        hadiths = data

    docs, ids, metas = [], [], []
    for i, h in enumerate(hadiths):
        if not isinstance(h, dict):
            continue
        arabic   = safe_str(h.get("arabic", ""))
        eng      = h.get("english", {})
        if isinstance(eng, str):
            narrator, english = "", eng
        elif isinstance(eng, dict):
            narrator = safe_str(eng.get("narrator", ""))
            english  = safe_str(eng.get("text", ""))
        else:
            narrator, english = "", ""

        # fallback: text field directly
        if not english:
            english = safe_str(h.get("text", h.get("body", "")))
        if not arabic:
            arabic  = safe_str(h.get("arabic_text", ""))

        text = make_chunk_text(arabic, narrator, english)
        if len(text.strip()) < 20:
            continue

        hadith_id = safe_str(h.get("id", h.get("hadithNumber", i)))
        docs.append(text)
        ids.append(f"{source_name.replace(' ','_')}_root_{hadith_id}_{i}")
        metas.append({
            "source":        source_name,
            "type":          doc_type,
            "hadith_number": hadith_id,
            "grade":         safe_str(h.get("grade", "")),
            "chapter":       safe_str(h.get("chapterId", "")),
            "has_arabic":    "yes" if arabic else "no",
        })

    if docs:
        upsert_batch(docs, ids, metas)
    print(f"  ✅ {source_name}: {len(docs):,} hadiths ingested")
    return len(docs)


# ══════════════════════════════════════════════════════
#  STANDALONE RIYAD / MISHKAT / BULUGH  (root dir)
#  Same structure as data format
# ══════════════════════════════════════════════════════

STANDALONE_FILES = [
    ("riyadussalihin.json", "Riyad as-Salihin",   "hadith"),
    ("mishkat.json",        "Mishkat al-Masabih",  "hadith"),
    ("bulugh.json",         "Bulugh al-Maram",     "hadith"),
]

# Reuse ingest_root_format for these (same dict/list structure)


# ══════════════════════════════════════════════════════
#  QURAN — quran-english.json
# ══════════════════════════════════════════════════════

def ingest_quran():
    filepath = "quran-english.json"
    source   = "Quran"
    if not os.path.exists(filepath):
        print(f"  ⚠️  Not found: {filepath}")
        return 0
    if already_ingested(source):
        print(f"  ✅ Already ingested: {source}")
        return 0

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    # Common Quran JSON formats:
    # [{verse_key, surah, ayah, text}, ...] or
    # [{chapter, verse, text, arabic}, ...] or
    # nested by surah

    verses = []
    if isinstance(data, list):
        verses = data
    elif isinstance(data, dict):
        # Try common keys
        for key in ["verses", "quran", "data", "ayahs"]:
            if key in data and isinstance(data[key], list):
                verses = data[key]
                break
        if not verses:
            # Nested: {1: [{...}], 2: [...]}
            for v in data.values():
                if isinstance(v, list):
                    verses.extend(v)

    docs, ids, metas = [], [], []
    for v in verses:
        if not isinstance(v, dict):
            continue
        # Try multiple field name patterns
        arabic  = safe_str(v.get("arabic", v.get("text_arabic", v.get("ar", ""))))
        english = safe_str(v.get("text",   v.get("translation", v.get("en", v.get("english", "")))))
        surah   = safe_str(v.get("chapter", v.get("surah", v.get("sura", v.get("surahNo", "")))))
        ayah    = safe_str(v.get("verse",   v.get("ayah",  v.get("verseNo", v.get("aya", "")))))

        if not english:
            continue

        text  = make_chunk_text(arabic, "", english)
        ref   = f"{surah}:{ayah}" if surah and ayah else safe_str(v.get("id", len(docs)))

        docs.append(text)
        ids.append(f"Quran_{surah}_{ayah}_{len(docs)}")
        metas.append({
            "source":        "Quran",
            "type":          "quran",
            "hadith_number": ref,
            "surah":         surah,
            "ayah":          ayah,
            "has_arabic":    "yes" if arabic else "no",
        })

    if docs:
        upsert_batch(docs, ids, metas)
    print(f"  ✅ Quran: {len(docs):,} verses ingested")
    return len(docs)


# ══════════════════════════════════════════════════════
#  QURAN URDU — quran-urdu.json
# ══════════════════════════════════════════════════════

def ingest_quran_urdu():
    filepath = "quran-urdu.json"
    source   = "Quran Urdu"
    if not os.path.exists(filepath):
        print(f"  ⚠️  Not found: {filepath}")
        return 0

    with open(filepath, encoding="utf-8") as f:
        raw = f.read().strip()
    if len(raw) < 20:
        print(f"  ⚠️  {filepath} is empty or placeholder")
        return 0
    if already_ingested(source):
        print(f"  ✅ Already ingested: {source}")
        return 0

    data   = json.loads(raw)
    verses = data if isinstance(data, list) else data.get("verses", data.get("data", []))

    docs, ids, metas = [], [], []
    for v in verses:
        if not isinstance(v, dict):
            continue
        urdu    = safe_str(v.get("text", v.get("urdu", v.get("translation", ""))))
        arabic  = safe_str(v.get("arabic", ""))
        surah   = safe_str(v.get("chapter", v.get("surah", "")))
        ayah    = safe_str(v.get("verse",   v.get("ayah", "")))
        if not urdu:
            continue
        text = f"[Arabic]\n{arabic}\n\n[Urdu]\n{urdu}" if arabic else f"[Urdu]\n{urdu}"
        docs.append(text)
        ids.append(f"QuranUrdu_{surah}_{ayah}_{len(docs)}")
        metas.append({
            "source": "Quran Urdu", "type": "quran",
            "hadith_number": f"{surah}:{ayah}",
            "surah": surah, "ayah": ayah,
            "has_arabic": "yes" if arabic else "no",
        })

    if docs:
        upsert_batch(docs, ids, metas)
    print(f"  ✅ Quran Urdu: {len(docs):,} verses ingested")
    return len(docs)


# ══════════════════════════════════════════════════════
#  TAFSEER — en-tafsir-ibn-kathir.json
# ══════════════════════════════════════════════════════

def ingest_tafseer():
    filepath = "en-tafsir-ibn-kathir.json"
    source   = "Tafseer Ibn Kathir"
    if not os.path.exists(filepath):
        print(f"  ⚠️  Not found: {filepath}")
        return 0
    if already_ingested(source):
        print(f"  ✅ Already ingested: {source}")
        return 0

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    entries = data if isinstance(data, list) else data.get("data", data.get("tafsir", []))

    docs, ids, metas = [], [], []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        text_en = safe_str(entry.get("text", entry.get("tafsir", entry.get("english", ""))))
        arabic  = safe_str(entry.get("arabic", ""))
        surah   = safe_str(entry.get("surah",  entry.get("chapter", "")))
        ayah    = safe_str(entry.get("ayah",   entry.get("verse", "")))
        if not text_en:
            continue

        chunk = f"[Tafseer Ibn Kathir — Quran {surah}:{ayah}]\n"
        if arabic:
            chunk += f"[Arabic]\n{arabic}\n\n"
        chunk += f"[Tafseer]\n{text_en}"

        docs.append(chunk)
        ids.append(f"TafseerIbnKathir_{surah}_{ayah}_{i}")
        metas.append({
            "source": "Tafseer Ibn Kathir", "type": "tafseer",
            "hadith_number": f"{surah}:{ayah}",
            "surah": surah, "ayah": ayah,
            "has_arabic": "yes" if arabic else "no",
        })

    if docs:
        upsert_batch(docs, ids, metas)
    print(f"  ✅ Tafseer Ibn Kathir: {len(docs):,} entries ingested")
    return len(docs)


# ══════════════════════════════════════════════════════
#  HISNUL MUSLIM — hisnulmuslim.txt
#  Plain text — split by numbered sections
# ══════════════════════════════════════════════════════

def ingest_hisnul_muslim():
    filepath = "hisnulmuslim.txt"
    source   = "Hisnul Muslim"
    if not os.path.exists(filepath):
        print(f"  ⚠️  Not found: {filepath}")
        return 0
    if already_ingested(source):
        print(f"  ✅ Already ingested: {source}")
        return 0

    with open(filepath, encoding="utf-8") as f:
        raw = f.read()

    # Split on numbered section headings like "1. When waking up" or "\n42."
    sections = re.split(r'\n(?=\d+\.)', raw)
    docs, ids, metas = [], [], []

    for i, section in enumerate(sections):
        section = section.strip()
        if len(section) < 30:
            continue
        # Extract section number and title from first line
        lines    = section.split("\n")
        title    = lines[0].strip()
        body     = "\n".join(lines[1:]).strip()
        num_match = re.match(r'^(\d+)\.?\s*(.*)', title)
        num      = num_match.group(1) if num_match else str(i)
        name     = num_match.group(2) if num_match else title

        chunk = f"[Hisnul Muslim — Section {num}: {name}]\n{body or section}"

        docs.append(chunk)
        ids.append(f"HisnulMuslim_{num}_{i}")
        metas.append({
            "source":        "Hisnul Muslim",
            "type":          "dua",
            "hadith_number": num,
            "chapter":       name,
            "has_arabic":    "yes" if re.search(r'[\u0600-\u06FF]', section) else "no",
        })

    if docs:
        upsert_batch(docs, ids, metas)
    print(f"  ✅ Hisnul Muslim (txt): {len(docs):,} sections ingested")
    return len(docs)


# ══════════════════════════════════════════════════════
#  HISNUL MUSLIM JSON — hisnul_muslim.json (root)
# ══════════════════════════════════════════════════════

def ingest_hisnul_muslim_json():
    filepath = "hisnul_muslim.json"
    source   = "Hisnul Muslim"
    if not os.path.exists(filepath):
        return 0

    with open(filepath, encoding="utf-8") as f:
        raw = f.read().strip()
    if len(raw) < 20:
        return 0
    if already_ingested(source):
        print(f"  ✅ Already ingested: {source}")
        return 0

    data = json.loads(raw)
    entries = data if isinstance(data, list) else data.get("data", data.get("duas", []))
    docs, ids, metas = [], [], []

    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        arabic  = safe_str(entry.get("arabic", ""))
        english = safe_str(entry.get("english", entry.get("translation", entry.get("text", ""))))
        translit = safe_str(entry.get("transliteration", entry.get("transliteration_en", "")))
        title   = safe_str(entry.get("title", entry.get("category", entry.get("occasion", ""))))
        idx     = safe_str(entry.get("id", entry.get("index", i)))

        if not english and not arabic:
            continue

        chunk = f"[Hisnul Muslim — {title}]\n"
        if arabic:
            chunk += f"[Arabic]\n{arabic}\n\n"
        if translit:
            chunk += f"[Transliteration]\n{translit}\n\n"
        if english:
            chunk += f"[English]\n{english}"

        docs.append(chunk)
        ids.append(f"HisnulMuslimJSON_{idx}_{i}")
        metas.append({
            "source":        "Hisnul Muslim",
            "type":          "dua",
            "hadith_number": idx,
            "chapter":       title,
            "has_arabic":    "yes" if arabic else "no",
        })

    if docs:
        upsert_batch(docs, ids, metas)
    print(f"  ✅ Hisnul Muslim (JSON): {len(docs):,} duas ingested")
    return len(docs)


# ══════════════════════════════════════════════════════
#  AZKAR — Azkar.json
# ══════════════════════════════════════════════════════

def ingest_azkar():
    filepath = "Azkar.json"
    source   = "Azkar"
    if not os.path.exists(filepath):
        return 0

    with open(filepath, encoding="utf-8") as f:
        raw = f.read().strip()
    if len(raw) < 20:
        print(f"  ⚠️  Azkar.json is empty/placeholder")
        return 0
    if already_ingested(source):
        print(f"  ✅ Already ingested: {source}")
        return 0

    data    = json.loads(raw)
    entries = data if isinstance(data, list) else data.get("azkar", data.get("data", []))
    docs, ids, metas = [], [], []

    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        arabic  = safe_str(entry.get("arabic", entry.get("zikr", "")))
        english = safe_str(entry.get("english", entry.get("translation", entry.get("meaning", ""))))
        category = safe_str(entry.get("category", entry.get("type", "")))
        count    = safe_str(entry.get("count", entry.get("repeat", "")))

        if not arabic and not english:
            continue

        chunk = f"[Azkar — {category}]\n"
        if arabic:
            chunk += f"[Arabic]\n{arabic}\n\n"
        if english:
            chunk += f"[English]\n{english}"
        if count:
            chunk += f"\n[Repeat: {count} times]"

        docs.append(chunk)
        ids.append(f"Azkar_{i}")
        metas.append({
            "source": "Azkar", "type": "dua",
            "hadith_number": str(i), "chapter": category,
            "has_arabic": "yes" if arabic else "no",
        })

    if docs:
        upsert_batch(docs, ids, metas)
    print(f"  ✅ Azkar: {len(docs):,} entries ingested")
    return len(docs)


# ══════════════════════════════════════════════════════
#  MAIN — Run all ingesters
# ══════════════════════════════════════════════════════

def main():
    t0    = time.time()
    total = 0

    print("=" * 55)
    print("  ISLAMIC RAG — FULL INGEST")
    print("=" * 55)

    # ── 1. ROOT FORMAT HADITHS ────────────────────────
    print("\n📚 ROOT FORMAT HADITHS")
    for fpath, name, dtype in ROOT_HADITH_FILES:
        total += ingest_root_format(fpath, name, dtype)

    # ── 2. STANDALONE ROOT FILES ──────────────────────
    print("\n📚 STANDALONE HADITH FILES (root dir)")
    for fpath, name, dtype in STANDALONE_FILES:
        total += ingest_root_format(fpath, name, dtype)

    # ── 3. FORTIES ────────────────────────────────────
    print("\n📚 FORTY HADITH COLLECTIONS (root dir)")
    for fpath, name, dtype in FORTIES_FILES:
        total += ingest_forties(fpath, name, dtype)

    # ── 4. DATA/HADITH-JSON FORMAT ────────────────────
    print("\n📚 DATA/HADITH-JSON FORMAT")
    for fpath, name, dtype in DATA_HADITH_FILES:
        total += ingest_data_format(fpath, name, dtype)

    # ── 5. QURAN ──────────────────────────────────────
    print("\n📖 QURAN")
    total += ingest_quran()
    total += ingest_quran_urdu()

    # ── 6. TAFSEER ────────────────────────────────────
    print("\n📖 TAFSEER")
    total += ingest_tafseer()

    # ── 7. DUA / AZKAR ───────────────────────────────
    print("\n🤲 DUA & AZKAR")
    total += ingest_hisnul_muslim_json()
    total += ingest_hisnul_muslim()
    total += ingest_azkar()

    # ── SUMMARY ───────────────────────────────────────
    elapsed = round(time.time() - t0, 1)
    final   = col.count()
    print("\n" + "=" * 55)
    print(f"  ✅ Ingested this run : {total:,} new documents")
    print(f"  📦 Total in ChromaDB : {final:,} documents")
    print(f"  ⏱️  Time taken        : {elapsed}s")
    print("=" * 55)


if __name__ == "__main__":
    main()
