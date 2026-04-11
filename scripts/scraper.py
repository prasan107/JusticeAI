# scripts/scraper.py
# Playwright scraper for Indian Kanoon — optimized for maximum results
# Run from justiceai/ folder: python scripts/scraper.py

import json, os, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SEARCH_TERMS = [
    "murder conviction IPC 302",
    "theft acquittal IPC 379",
    "property dispute civil court",
    "domestic violence protection order",
    "bail application criminal",
    "cheque bounce NI Act 138",
    "rape conviction IPC 376",
    "dowry death IPC 304B",
    "fraud cheating IPC 420",
    "land acquisition compensation",
    "kidnapping abduction IPC 363",
    "corruption bribery Prevention of Corruption Act",
    "motor accident compensation MACT",
    "consumer complaint deficiency service",
    "wrongful termination employment labour court",
    "anticipatory bail sessions court",
    "divorce Hindu Marriage Act",
    "custody child maintenance",
    "defamation reputation damage",
    "contract breach damages",
]

def classify_case_type(query: str) -> str:
    q = query.lower()
    if any(x in q for x in ["murder", "theft", "rape", "bail", "ipc", "criminal", "fraud", "dowry", "kidnapping", "corruption"]):
        return "Criminal"
    elif any(x in q for x in ["property", "land", "civil", "compensation", "dispute", "accident", "consumer", "employment", "contract", "defamation"]):
        return "Civil"
    elif any(x in q for x in ["domestic violence", "divorce", "custody", "maintenance"]):
        return "Family"
    return "Other"

def extract_year_from_title(title: str) -> int:
    """Extract year from case title like 'X vs Y on 21 September, 1984'"""
    import re
    match = re.search(r'\b(19[5-9]\d|20[0-2]\d)\b', title)
    if match:
        return int(match.group())
    return 2000

def extract_court_from_title(title: str) -> str:
    """Guess court from title keywords"""
    title_lower = title.lower()
    if "supreme court" in title_lower:
        return "Supreme Court of India"
    elif "high court" in title_lower:
        # Try to extract which high court
        import re
        match = re.search(r'(\w+)\s+high court', title_lower)
        if match:
            return f"{match.group(1).title()} High Court"
        return "High Court"
    elif "sessions" in title_lower:
        return "Sessions Court"
    elif "district" in title_lower:
        return "District Court"
    elif "tribunal" in title_lower:
        return "Tribunal"
    return "Unknown"

def scrape_with_playwright():
    all_cases = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        for term in SEARCH_TERMS:
            print(f"\nScraping: '{term}'")
            term_cases = []

            for page_num in range(0, 10):   # up to 10 pages per term
                try:
                    url = f"https://indiankanoon.org/search/?formInput={term.replace(' ', '+')}&pagenum={page_num}"
                    page.goto(url, timeout=30000, wait_until="networkidle")
                    time.sleep(1.5)

                    # Get ALL /doc/ links on the page (these are judgment links)
                    # Filter out fragment links (docfragment) - we want full doc links
                    all_links = page.query_selector_all("a[href*='/doc/']")
                    
                    page_cases = []
                    seen_on_page = set()

                    for link in all_links:
                        try:
                            href = link.get_attribute("href") or ""
                            title = link.inner_text().strip()

                            # Skip fragment links, navigation links, empty titles
                            if not href or not title or len(title) < 10:
                                continue
                            if "docfragment" in href:
                                continue
                            if href in seen_on_page:
                                continue

                            seen_on_page.add(href)

                            # Extract case_id from URL like /doc/1234567/
                            parts = [p for p in href.split("/") if p]
                            case_id = parts[-1] if parts else href

                            year = extract_year_from_title(title)
                            court = extract_court_from_title(title)

                            page_cases.append({
                                "case_id": case_id,
                                "title": title,
                                "court": court,
                                "year": year,
                                "case_type": classify_case_type(term),
                                "full_text": title,  # will be enriched later
                                "url": "https://indiankanoon.org" + href,
                                "search_query": term
                            })
                        except Exception:
                            continue

                    term_cases.extend(page_cases)
                    print(f"  Page {page_num+1}: found {len(page_cases)} cases")

                    # Stop if no results found on this page
                    if len(page_cases) == 0:
                        print(f"  No more results, moving to next term")
                        break

                except Exception as e:
                    print(f"  Page {page_num+1} error: {e}")
                    break

                time.sleep(1.5)  # polite delay between pages

            all_cases.extend(term_cases)
            print(f"  Subtotal for '{term}': {len(term_cases)} cases")
            time.sleep(2)  # polite delay between search terms

        browser.close()

    # Remove duplicates by case_id
    seen = set()
    unique_cases = []
    for c in all_cases:
        if c["case_id"] not in seen:
            seen.add(c["case_id"])
            unique_cases.append(c)

    output_path = os.path.join(OUTPUT_DIR, "judgments_raw.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique_cases, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"Total unique cases scraped: {len(unique_cases)}")
    print(f"Saved to: {output_path}")
    print(f"{'='*50}")

    return unique_cases

if __name__ == "__main__":
    scrape_with_playwright()