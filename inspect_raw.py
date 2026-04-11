import json

with open("data/raw/judgments_raw.json", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total records: {len(data)}")
print(f"Keys: {list(data[0].keys())}")
print()

# Show first 3 records fully (except full_text truncated)
for i, r in enumerate(data[:3]):
    print(f"=== Record {i} ===")
    for k, v in r.items():
        if k == "full_text":
            print(f"  full_text: {repr(str(v)[:400])}")
        else:
            print(f"  {k}: {repr(v)}")
    print()

# Check search_query distribution
queries = {}
for r in data:
    q = r.get("search_query", "unknown")
    queries[q] = queries.get(q, 0) + 1

print("Search query distribution:")
for k, v in sorted(queries.items(), key=lambda x: -x[1])[:15]:
    print(f"  {v}  {k}")

# Check how many have real full_text
has_text = sum(1 for r in data if len(str(r.get("full_text", ""))) > 200)
print(f"\nRecords with substantial full_text (>200 chars): {has_text}/{len(data)}")