"""
reingest_hisnul.py — Re-ingest Hisnul Muslim from the txt file properly.
Parses each dua section with: occasion, transliteration, translation, reference.
Run ONCE after deploying the new code.
"""
import re
import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = "./chroma_db"
COLLECTION  = "islamic_texts"
TXT_FILE    = "hisnulmuslim.txt"

ef  = embedding_functions.DefaultEmbeddingFunction()
cli = chromadb.PersistentClient(path=CHROMA_PATH)
col = cli.get_or_create_collection(name=COLLECTION, embedding_function=ef)

# ── DELETE OLD HISNUL MUSLIM CHUNKS ───────────────────
existing = col.get(where={"source": "Hisnul Muslim"})
if existing["ids"]:
    col.delete(ids=existing["ids"])
    print(f"Deleted {len(existing['ids'])} old chunks")

# ── PARSE TXT FILE ────────────────────────────────────
with open(TXT_FILE, encoding="utf-8") as f:
    raw = f.read()

# Split on "Hisn al-Muslim N" markers
sections = re.split(r'(?=Hisn al-Muslim \d+)', raw)

docs, ids, metas = [], [], []

for section in sections:
    section = section.strip()
    if not section or len(section) < 40:
        continue

    # Extract Hisn al-Muslim number
    num_match = re.match(r'Hisn al-Muslim (\d+)', section)
    if not num_match:
        continue
    hisn_num = num_match.group(1)

    # Extract Chapter heading (before this section, find "Chapter N: ...")
    chapter_match = re.search(r'Chapter\s+\d+[:\s]+([^\n]+)', section)
    chapter = chapter_match.group(1).strip() if chapter_match else ""

    # Extract Transliteration block
    translit_match = re.search(
        r'Transliteration[:\s]*\n(.*?)(?=Translation|Reference|Hisn al-Muslim|\Z)',
        section, re.DOTALL | re.IGNORECASE
    )
    translit = translit_match.group(1).strip() if translit_match else ""

    # Extract Translation block
    trans_match = re.search(
        r'Translation[:\s]*\n(.*?)(?=Reference|Hisn al-Muslim|\Z)',
        section, re.DOTALL | re.IGNORECASE
    )
    translation = trans_match.group(1).strip() if trans_match else ""

    # Extract Reference block
    ref_match = re.search(
        r'Reference[:\s]*\n?(.*?)(?=Hisn al-Muslim|\Z)',
        section, re.DOTALL | re.IGNORECASE
    )
    reference = ref_match.group(1).strip() if ref_match else ""
    # Clean dashes from reference
    reference = re.sub(r'-{3,}', '', reference).strip()

    if not translit and not translation:
        continue

    # Build chunk text
    parts = [f"[Hisnul Muslim — Section {hisn_num}]"]
    if chapter:
        parts.append(f"Occasion: {chapter}")
    if translit:
        parts.append(f"\n[Transliteration]\n{translit}")
    if translation:
        parts.append(f"\n[Translation]\n{translation}")
    if reference:
        ref_clean = reference[:200]
        parts.append(f"\n[Reference]\n{ref_clean}")

    chunk_text = "\n".join(parts)
    if len(chunk_text.strip()) < 40:
        continue

    docs.append(chunk_text)
    ids.append(f"HisnulMuslim_v2_{hisn_num}")
    metas.append({
        "source":        "Hisnul Muslim",
        "type":          "dua",
        "hadith_number": hisn_num,
        "chapter":       chapter[:100] if chapter else "",
        "has_arabic":    "no",
        "reference":     reference[:200] if reference else "",
    })

# Batch upsert
BATCH = 100
for i in range(0, len(docs), BATCH):
    col.upsert(
        documents=docs[i:i+BATCH],
        ids=ids[i:i+BATCH],
        metadatas=metas[i:i+BATCH]
    )

print(f"✅ Ingested {len(docs)} Hisnul Muslim duas")
print(f"📦 Total in ChromaDB: {col.count():,}")

# Quick test
r = col.query(query_texts=["dua before sleeping"], n_results=2)
print("\n--- Test: dua before sleeping ---")
for i in range(len(r["documents"][0])):
    print(r["metadatas"][0][i])
    print(r["documents"][0][i][:250])
    print()
