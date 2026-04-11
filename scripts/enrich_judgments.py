"""
Phase 2: Enrich judgments_raw.json by fetching actual judgment text.
Run from project root: python scripts/enrich_judgments.py

Resume-safe: skips already-enriched cases.
Time: ~1-2 hrs for 1993 cases with polite delays.
"""
import json, os, re, time, random
from pathlib import Path
from playwright.sync_api import sync_playwright

RAW_PATH    = Path("data/raw/judgments_raw.json")
OUTPUT_PATH = Path("data/raw/judgments_enriched.json")


def extract_year(text: str) -> int:
    m = re.search(r'\b(19[5-9]\d|20[0-2]\d)\b', text)
    return int(m.group()) if m else 2020


def extract_court(text: str) -> str:
    t = text[:1000]
    if "Supreme Court of India" in t:
        return "Supreme Court of India"
    m = re.search(r'([\w\s]+High Court)', t)
    if m:
        return m.group(1).strip()
    if "Sessions Court" in t:
        return "Sessions Court"
    if "District Court" in t:
        return "District Court"
    return "Unknown"


def enrich():
    with open(RAW_PATH, encoding="utf-8") as f:
        records = json.load(f)

    print(f"Total records: {len(records)}")

    # Load already-enriched (resume support)
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            enriched = json.load(f)
        done_ids = {r["case_id"] for r in enriched if r.get("full_text", "") not in ("", "Full Document")}
        print(f"Already enriched: {len(done_ids)}, resuming...")
    else:
        enriched = []
        done_ids = set()

    to_scrape = [r for r in records if r["case_id"] not in done_ids]
    print(f"Remaining to scrape: {len(to_scrape)}")

    failed = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        for i, record in enumerate(to_scrape):
            url = record.get("url", "")
            if not url:
                continue

            try:
                page.goto(url, timeout=20000, wait_until="domcontentloaded")
                time.sleep(1.0)

                # ── Extract title from <title> tag ──
                title_raw = page.title() or ""
                # "Shatrughan vs State(Govt. Of Nct Of Delhi) on 20 April, 2010"
                title = re.sub(r'\s*[-|]\s*Indian Kanoon.*$', '', title_raw).strip()
                title = re.sub(r'\s+on\s+\d{1,2}\s+\w+,?\s*\d{4}\s*$', '', title).strip()

                # ── Extract judgment text ──
                # Try the main judgment div first
                full_text = ""
                for selector in ["#judgments", ".judgments", "#main_judgment",
                                 ".judgment_div", "#doc_fragment", ".doc_fragment"]:
                    el = page.query_selector(selector)
                    if el:
                        full_text = el.inner_text().strip()
                        if len(full_text) > 200:
                            break

                # Fallback: get all paragraph text in main content
                if len(full_text) < 200:
                    paragraphs = page.query_selector_all("p")
                    full_text = "\n".join(
                        p.inner_text().strip() for p in paragraphs
                        if len(p.inner_text().strip()) > 30
                    )

                # Final fallback: body text minus nav
                if len(full_text) < 200:
                    full_text = page.inner_text("body")
                    # Remove navigation noise
                    full_text = re.sub(r'Skip to main content.*?Search Indian laws', '', full_text, flags=re.DOTALL)

                year  = extract_year(title_raw + " " + full_text[:500])
                court = extract_court(full_text)

                if len(full_text) > 200:
                    new_record = {
                        "case_id":      record["case_id"],
                        "title":        title if title and title != "Full Document" else "Unknown Case",
                        "court":        court,
                        "year":         year,
                        "case_type":    record.get("case_type", "Unknown"),
                        "full_text":    full_text[:8000],
                        "url":          url,
                        "search_query": record.get("search_query", ""),
                        "outcome":      None,
                        "source":       "scraped",
                    }
                    enriched.append(new_record)
                    done_ids.add(record["case_id"])
                    print(f"  [{i+1}/{len(to_scrape)}] ✅ {title[:60]} ({year})")
                else:
                    print(f"  [{i+1}/{len(to_scrape)}] ⚠️  Empty text: {url}")
                    failed += 1

            except Exception as e:
                print(f"  [{i+1}/{len(to_scrape)}] ❌ {e}")
                failed += 1

            # Save every 50 records
            if (i + 1) % 50 == 0:
                with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
                    json.dump(enriched, f, ensure_ascii=False, indent=2)
                print(f"  💾 Saved {len(enriched)} enriched records...")

            # Polite delay
            time.sleep(random.uniform(1.5, 2.5))

        browser.close()

    # Final save
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done! Enriched: {len(enriched)}, Failed: {failed}")
    print(f"Saved to: {OUTPUT_PATH}")
    print(f"\nNext steps:")
    print(f"  1. python scripts/merge_datasets.py   # merge with cases.csv")
    print(f"  2. python relabel_and_retrain.py")
    print(f"  3. python scripts/ingest_to_vectordb.py")


if __name__ == "__main__":
    enrich()