import json

with open("fiqh_maliki.json", "r", encoding="utf-8") as f:
    data = json.load(f)

chunks = []

for item in data:
    q = item.get("question", "").strip()
    a = item.get("answer", "").strip()

    if len(q) < 5 or len(a) < 10:
        continue

    text = f"""
FIQH QUESTION:
{q}

ANSWER:
{a}
""".strip()

    chunks.append({
        "type": "fiqh",
        "source": "fiqh-maliki-talqin",
        "text": text,
        "question": q,
        "answer": a
    })

print("TOTAL CHUNKS:", len(chunks))

with open("fiqh_chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)
