from datasets import load_dataset
import json

dataset = load_dataset("M-AI-C/hisnulmuslim", split="train")

print("TOTAL:", len(dataset))

data = []

for row in dataset:
    data.append({
        "type": "dua",
        "source": "hisnulmuslim_hf",
        "reference": row.get("reference", ""),
        "title": row.get("title", ""),
        "arabic": row.get("arabic", ""),
        "english": row.get("english", ""),
        "text": f"{row.get('title','')}\n\n{row.get('arabic','')}\n\n{row.get('english','')}"
    })

with open("hisnulmuslim_clean.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("SAVED -> hisnulmuslim_clean.json")
