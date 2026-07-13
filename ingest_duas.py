import json
import chromadb
from sentence_transformers import SentenceTransformer

# -----------------------------
# LOAD EMBEDDING MODEL
# -----------------------------
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# -----------------------------
# CONNECT CHROMA
# -----------------------------
client = chromadb.PersistentClient("./chroma_db")

collection = client.get_collection("islamic_texts")

# -----------------------------
# LOAD DATASET
# -----------------------------
with open("dua_dataset.json", "r", encoding="utf-8") as f:
    duas = json.load(f)

print("TOTAL DUAS:", len(duas))

# -----------------------------
# INGEST
# -----------------------------
batch_size = 100

documents = []
metadatas = []
ids = []
embeddings = []

count = 0

for idx, dua in enumerate(duas):

    arabic = dua.get("arabic", "").strip()
    english = dua.get("english", "").strip()

    if not arabic or not english:
        continue

    text = f"""
Arabic:
{arabic}

English:
{english}
"""

    embedding = model.encode(text).tolist()

    documents.append(text)

    metadatas.append({
        "type": "dua",
        "source": "Dua Dataset",
        "book": dua.get("book", ""),
        "hadith_id": str(dua.get("hadith_id", ""))
    })

    ids.append(f"dua_{idx}")

    embeddings.append(embedding)

    # batch insert
    if len(documents) >= batch_size:

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )

        count += len(documents)

        print(f"INGESTED: {count}")

        documents = []
        metadatas = []
        ids = []
        embeddings = []

# remaining
if documents:
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings
    )

    count += len(documents)

print("\nDONE")
print("TOTAL INGESTED:", count)

