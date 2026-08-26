import os
import sys
import time
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from typing import List, Tuple, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

# Constants
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.models import BookRecord, validate_and_normalize_record

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
CACHE_DIR = BASE_DIR / "cache"
OUTPUT_DIR = BASE_DIR / "output"
BOOKS_OUTPUT_FILE = OUTPUT_DIR / "books.json"
ERRORS_OUTPUT_FILE = OUTPUT_DIR / "errors.json"

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/sarweshwargoud/flyrank-ai)"
REQUEST_TIMEOUT = 10.0
POLITE_DELAY_SECONDS = 0.5
MAX_CATALOGUE_PAGES = 3


def get_cache_filename_for_url(url: str, is_catalogue: bool = False, page_num: int = 1) -> str:
    """Generates a deterministic filename for caching."""
    if is_catalogue:
        return f"catalogue-page-{page_num}.html"
    
    parts = url.rstrip("/").split("/")
    if parts[-1] == "index.html" and len(parts) >= 2:
        slug = parts[-2]
    else:
        slug = parts[-1]
    
    clean_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', slug)
    return f"book-{clean_slug}.html"


def fetch_page_with_cache(url: str, cache_filename: str) -> Tuple[str, bool]:
    """
    Fetches an HTML page with polite caching.
    Returns (html_content, is_cache_hit).
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / cache_filename

    # Check local cache first
    if cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        byte_size = len(html_content.encode("utf-8"))
        print(f"CACHE HIT {cache_path.relative_to(BASE_DIR)} bytes={byte_size}")
        return html_content, True

    # Polite rate-limiting delay before making real network request
    time.sleep(POLITE_DELAY_SECONDS)

    # Network Fetch
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        print(f"ERROR Fetching {url}: {e}")
        sys.exit(1)

    if response.status_code != 200:
        print(f"ERROR Unexpected status code {response.status_code} for {url}")
        sys.exit(1)

    response.encoding = "utf-8"
    html_content = response.text
    byte_size = len(html_content.encode("utf-8"))

    # Save to cache
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"FETCH {url} status={response.status_code} bytes={byte_size}")
    return html_content, False


def extract_book_urls(html: str, base_url: str) -> List[str]:
    """
    Parses a catalogue HTML page and extracts absolute product URLs.
    Uses urllib.parse.urljoin to resolve relative links.
    """
    soup = BeautifulSoup(html, "html.parser")
    book_urls = []
    
    for article in soup.select("article.product_pod h3 a"):
        href = article.get("href")
        if href:
            absolute_url = urljoin(base_url, href)
            book_urls.append(absolute_url)
            
    return book_urls


def extract_next_page_url(html: str, base_url: str) -> Optional[str]:
    """
    Finds the 'next' pagination link in the catalogue page.
    """
    soup = BeautifulSoup(html, "html.parser")
    next_tag = soup.select_one("li.next a")
    if next_tag and next_tag.get("href"):
        return urljoin(base_url, next_tag.get("href"))
    return None


def discover_catalogue(start_url: str, max_pages: int = MAX_CATALOGUE_PAGES) -> Tuple[int, List[Dict[str, str]]]:
    """
    Crawls catalogue pages up to max_pages.
    Returns (pages_count, list of dicts with 'product_url' and 'source_page').
    """
    current_url = start_url
    pages_crawled = 0
    discovered_items = []
    seen_urls = set()

    while current_url and pages_crawled < max_pages:
        pages_crawled += 1
        cache_filename = get_cache_filename_for_url(current_url, is_catalogue=True, page_num=pages_crawled)
        
        html, _ = fetch_page_with_cache(current_url, cache_filename)
        urls = extract_book_urls(html, current_url)
        
        for u in urls:
            if u not in seen_urls:
                seen_urls.add(u)
                discovered_items.append({
                    "product_url": u,
                    "source_page": current_url
                })
        
        next_url = extract_next_page_url(html, current_url)
        current_url = next_url if (pages_crawled < max_pages) else None

    return pages_crawled, discovered_items


def parse_book_detail(html: str, product_url: str, source_page: str, fetched_at: str) -> Dict[str, Any]:
    """
    Parses a single book detail HTML page and extracts all 8 raw fields.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Title: inside div.product_main h1
    title_elem = soup.select_one("div.product_main h1")
    title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

    # Price Text: inside p.price_color
    price_elem = soup.select_one("p.price_color")
    price_text = price_elem.get_text(strip=True).replace("Â", "") if price_elem else ""

    # Availability Text: inside p.availability
    avail_elem = soup.select_one("p.availability")
    availability_text = avail_elem.get_text(strip=True) if avail_elem else ""

    # Star Rating: class on p.star-rating
    star_elem = soup.select_one("p.star-rating")
    rating_text = "None"
    if star_elem:
        classes = [c for c in star_elem.get("class", []) if c != "star-rating"]
        rating_text = classes[0] if classes else "None"

    # Description: paragraph immediately following #product_description
    desc_elem = soup.select_one("#product_description ~ p")
    description = desc_elem.get_text(strip=True) if desc_elem else None

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at
    }


def scrape_and_validate_all(discovered_items: List[Dict[str, str]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Fetches, extracts, normalizes, and validates records for all discovered items.
    Enforces deduplication using canonical product_url.
    Returns (valid_records, invalid_records).
    """
    valid_records = []
    invalid_records = []
    seen_canonical_urls = set()

    for item in discovered_items:
        product_url = item["product_url"]
        source_page = item["source_page"]

        # Deduplication check
        if product_url in seen_canonical_urls:
            continue
        seen_canonical_urls.add(product_url)

        cache_filename = get_cache_filename_for_url(product_url)
        fetch_time = datetime.now(timezone.utc).isoformat()

        html, _ = fetch_page_with_cache(product_url, cache_filename)
        raw_record = parse_book_detail(
            html=html,
            product_url=product_url,
            source_page=source_page,
            fetched_at=fetch_time
        )

        # Stage 4: Normalize & Validate with Pydantic
        validated_record, error_reason = validate_and_normalize_record(raw_record)
        if validated_record:
            valid_records.append(validated_record.model_dump())
        else:
            invalid_records.append({
                "raw_record": raw_record,
                "error": error_reason
            })

    return valid_records, invalid_records


def save_output_files(valid_records: List[Dict[str, Any]], invalid_records: List[Dict[str, Any]]) -> None:
    """
    Saves validated records to output/books.json and errors to output/errors.json idempotently.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(BOOKS_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(valid_records, f, indent=2, ensure_ascii=False)

    with open(ERRORS_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(invalid_records, f, indent=2, ensure_ascii=False)


def main():
    print("=== FlyRank Polite Scraper (Stage 4) ===")
    
    # Step 1: Discover catalogue
    pages_count, discovered_items = discover_catalogue(START_URL, max_pages=MAX_CATALOGUE_PAGES)
    print(f"\ncatalogue_pages={pages_count} discovered={len(discovered_items)} unique_urls={len(discovered_items)}\n")
    
    # Step 2: Scrape, normalize, validate
    valid_records, invalid_records = scrape_and_validate_all(discovered_items)
    
    # Step 3: Save to output files
    save_output_files(valid_records, invalid_records)
    
    # Checkpoint output
    unique_product_urls = len(set(r["product_url"] for r in valid_records))
    print(f"\nvalid_records={len(valid_records)}")
    print(f"invalid_records={len(invalid_records)}")
    print(f"unique_urls={unique_product_urls}")
    
    print("\n--- Complete Normalized Record Example ---")
    if valid_records:
        print(json.dumps(valid_records[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
