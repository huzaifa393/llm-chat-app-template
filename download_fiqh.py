from datasets import load_dataset
import json

# Load dataset from HuggingFace
dataset = load_dataset("islamic-datasets/fiqh-maliki-talqin")

print(dataset)
print("Splits:", dataset.keys())

# usually it's "train"
data = dataset["train"]

print("Total samples:", len(data))

# inspect one sample
print("\nSAMPLE:\n")
print(data[0])

# save locally
with open("fiqh_maliki.json", "w", encoding="utf-8") as f:
    json.dump(data.to_list(), f, ensure_ascii=False, indent=2)

print("\nSaved -> fiqh_maliki.json")
