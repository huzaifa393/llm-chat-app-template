import json, os, chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "islamic_texts"
BATCH_SIZE = 100
MIN_CHUNK = 40

NEW_BOOKS = [
    ("malik.json",    "Muwatta Malik",       "malik"),
    ("darimi.json",   "Sunan ad-Darimi",     "darimi"),
    ("nawawi40.json", "Forty Hadith Nawawi", "nawawi40"),
    ("qudsi40.json",  "Forty Hadith Qudsi",  "qudsi40"),
]

client = chromadb.PersistentClient(path=CHROMA_PATH)
ef = embedding_functions.DefaultEmbeddingFunction()
col = client.get_or_create_collection(COLLECTION_NAME, embedding_function=ef, metadata={"hnsw:space": "cosine"})
print(f"Collection has {col.count():,} docs before ingest")

for filename, book_name, book_key in NEW_BOOKS:
    if not os.path.exists(filename):
        print(f"SKIP {filename} not found"); continue
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    hadiths = data.get("hadiths", data) if isinstance(data, dict) else data
    if isinstance(hadiths, dict): hadiths = list(hadiths.values())
    texts, ids, metas = [], [], []
    for item in hadiths:
        if not isinstance(item, dict): continue
        raw = ""
        for k in ["text", "body", "content", "hadith_english"]:
            v = item.get(k, "")
            if v and len(str(v)) > MIN_CHUNK: raw = str(v); break
        if not raw:
            eng = item.get("english", {})
            if isinstance(eng, dict):
                raw = (eng.get("narrator","") + " " + eng.get("text","")).strip()
            elif isinstance(eng, str):
                raw = eng
        if not raw or len(raw) < MIN_CHUNK: continue
        uid = f"{book_key}_h{item.get('id', len(texts))}"
        texts.append(raw[:800])
        ids.append(uid)
        metas.append({"source": book_name, "book_key": book_key, "type": "hadith",
                      "hadith_number": str(item.get("id","")), "arabic_number": "",
                      "book_number": "", "grade": "", "chunk_index": "0", "total_chunks": "1"})
    inserted = 0
    for start in range(0, len(texts), BATCH_SIZE):
        b_t = texts[start:start+BATCH_SIZE]
        b_i = ids[start:start+BATCH_SIZE]
        b_m = metas[start:start+BATCH_SIZE]
        try:
            col.add(documents=b_t, ids=b_i, metadatas=b_m)
            inserted += len(b_t)
        except Exception as e:
            for t,i,m in zip(b_t,b_i,b_m):
                try: col.add(documents=[t], ids=[i], metadatas=[m]); inserted+=1
                except: pass
    print(f"✅ {book_name}: {inserted}/{len(texts)} inserted")

print(f"\nDone! Collection now has {col.count():,} docs")
