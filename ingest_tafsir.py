import urllib.request, json, chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "islamic_texts"
BATCH_SIZE = 100
BASE_URL = "https://raw.githubusercontent.com/spa5k/tafsir_api/main/tafsir/en-tafisr-ibn-kathir"

client = chromadb.PersistentClient(path=CHROMA_PATH)
ef = embedding_functions.DefaultEmbeddingFunction()
col = client.get_or_create_collection(COLLECTION_NAME, embedding_function=ef, metadata={"hnsw:space": "cosine"})
print(f"Collection has {col.count():,} docs before ingest")

texts, ids, metas = [], [], []

for surah in range(1, 115):
    for ayah in range(1, 300):
        url = f"{BASE_URL}/{surah}/{ayah}.json"
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                data = json.loads(r.read())
            text = data.get("text", "").strip()
            if len(text) < 40:
                continue
            texts.append(text[:800])
            ids.append(f"tafsir_ik_s{surah}_a{ayah}")
            metas.append({"source": "Tafsir Ibn Kathir", "book_key": "tafsir_ik",
                          "type": "tafsir", "hadith_number": f"{surah}:{ayah}",
                          "arabic_number": str(surah), "book_number": str(surah),
                          "grade": "", "chunk_index": "0", "total_chunks": "1"})
        except urllib.error.HTTPError:
            break  # no more ayahs in this surah
        except Exception as e:
            print(f"  s{surah}:a{ayah} error: {e}")
            break
    print(f"  Surah {surah} done, total chunks so far: {len(texts)}")

# Ingest in batches
inserted = 0
for start in range(0, len(texts), BATCH_SIZE):
    b_t = texts[start:start+BATCH_SIZE]
    b_i = ids[start:start+BATCH_SIZE]
    b_m = metas[start:start+BATCH_SIZE]
    try:
        col.add(documents=b_t, ids=b_i, metadatas=b_m)
        inserted += len(b_t)
    except Exception:
        for t,i,m in zip(b_t,b_i,b_m):
            try: col.add(documents=[t], ids=[i], metadatas=[m]); inserted+=1
            except: pass

print(f"\nDone! Inserted {inserted} chunks. Total: {col.count():,}")
