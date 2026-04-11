import json

DATA_PATH = "data/processed/judgments_clean.json"

with open(DATA_PATH, encoding="utf-8") as f:
    cases = json.load(f)

print(f"Total before: {len(cases)}")

# Keep only CSV cases (your real dataset)
clean = [c for c in cases if str(c.get("case_id", "")).startswith("csv")]

print(f"CSV cases kept: {len(clean)}")
print(f"Junk removed: {len(cases) - len(clean)}")

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(clean, f, ensure_ascii=False, indent=2)

print("✅ Saved clean judgments_clean.json")