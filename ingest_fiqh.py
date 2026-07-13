import json
import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

client = chromadb.PersistentClient("./chroma_db")
col = client.get_collection("islamic_texts")

with open("fiqh_chunks.json", "r", encoding="utf-8") as f:
    data = json.load(f)

batch_size = 100

docs, metas, ids, embs = [], [], [], []

count = 0

for i, item in enumerate(data):

    text = item["text"]
    emb = model.encode(text).tolist()

    docs.append(text)

    metas.append({
        "type": "fiqh",
        "source": "fiqh-maliki-talqin"
    })

    ids.append(f"fiqh_{i}")
    embs.append(emb)

    if len(docs) == batch_size:
        col.add(
            documents=docs,
            metadatas=metas,
            ids=ids,
            embeddings=embs
        )

        count += len(docs)
        print("INGESTED:", count)

        docs, metas, ids, embs = [], [], [], []

if docs:
    col.add(
        documents=docs,
        metadatas=metas,
        ids=ids,
        embeddings=embs
    )

print("DONE. TOTAL:", count)
