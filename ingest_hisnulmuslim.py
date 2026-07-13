import json
import chromadb
from sentence_transformers import SentenceTransformer

# load data
with open("hisnulmuslim_clean.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# init embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# connect chroma
client = chromadb.PersistentClient("./chroma_db")
col = client.get_or_create_collection("islamic_texts")

texts = []
metas = []
ids = []

for i, item in enumerate(data):
    texts.append(item["text"])
    metas.append({
        "type": "dua",
        "source": item["source"],
        "reference": item["reference"],
        "title": item["title"]
    })
    ids.append(f"hisn_{i}")

    if len(texts) == 100 or i == len(data)-1:
        embeddings = model.encode(texts).tolist()

        col.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metas,
            ids=ids
        )

        print(f"INGESTED: {i+1}")

        texts, metas, ids = [], [], []

print("DONE INGESTION")
