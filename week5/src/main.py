import os
import sys
import time
import json
import re
import argparse
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
REPORT_OUTPUT_FILE = OUTPUT_DIR / "run-report.json"

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/sarweshwargoud/flyrank-ai)"
REQUEST_TIMEOUT = 10.0
POLITE_DELAY_SECONDS = 0.5
MAX_CATALOGUE_PAGES = 3


class ScraperStats:
    """Tracks runtime execution metrics for run-report.json."""
    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self.catalogue_pages = 0
        self.detail_pages_attempted = 0
        self.network_requests = 0
        self.cache_hits = 0
        self.valid_records = 0
        self.invalid_records = 0
        self.failed_pages = 0
        self.retries = 0

    def generate_report(self) -> Dict[str, Any]:
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.start_time).total_seconds()
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": round(duration, 3),
            "catalogue_pages_crawled": self.catalogue_pages,
            "detail_pages_attempted": self.detail_pages_attempted,
            "pages_fetched": self.network_requests,
            "cache_hits": self.cache_hits,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "failed_pages": self.failed_pages,
            "retries_performed": self.retries
        }


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


def fetch_page_with_cache(
    url: str,
    cache_filename: str,
    stats: Optional[ScraperStats] = None
) -> Tuple[Optional[str], bool, Optional[str]]:
    """
    Fetches an HTML page with polite caching and failure resilience.
    Retry rules:
      - Timeout or 5xx: Retries ONCE after a brief 1-second pause.
      - 404 or 403: No retry.
    Returns (html_content, is_cache_hit, error_message).
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / cache_filename

    # 1. Check local cache first
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            byte_size = len(html_content.encode("utf-8"))
            if stats:
                stats.cache_hits += 1
            print(f"CACHE HIT {cache_path.relative_to(BASE_DIR)} bytes={byte_size}")
            return html_content, True, None
        except Exception as e:
            print(f"WARN Cache read error for {cache_path}: {e}")

    # 2. Network Fetch with polite delay & single retry for timeouts/5xx
    headers = {"User-Agent": USER_AGENT}
    max_attempts = 2  # 1 initial + max 1 retry for 5xx/timeouts

    for attempt in range(1, max_attempts + 1):
        time.sleep(POLITE_DELAY_SECONDS)
        if stats:
            stats.network_requests += 1

        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            
            # Successful response
            if response.status_code == 200:
                response.encoding = "utf-8"
                html_content = response.text
                byte_size = len(html_content.encode("utf-8"))

                # Write to local cache
                with open(cache_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

                print(f"FETCH {url} status=200 bytes={byte_size}")
                return html_content, False, None

            # Non-retryable HTTP client errors (404, 403, 4xx)
            if 400 <= response.status_code < 500:
                err_msg = f"HTTP {response.status_code} client error (no retry)"
                print(f"FAILED {url} status={response.status_code} ({err_msg})")
                return None, False, err_msg

            # Server error 5xx (retryable once)
            if 500 <= response.status_code < 600:
                if attempt < max_attempts:
                    if stats:
                        stats.retries += 1
                    print(f"WARN HTTP {response.status_code} on {url}, retrying once in 1s...")
                    time.sleep(1.0)
                    continue
                else:
                    err_msg = f"HTTP {response.status_code} server error after retry"
                    print(f"FAILED {url} status={response.status_code} ({err_msg})")
                    return None, False, err_msg

            # Other status codes
            err_msg = f"Unexpected HTTP status {response.status_code}"
            return None, False, err_msg

        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt < max_attempts:
                if stats:
                    stats.retries += 1
                print(f"WARN Network error ({e}) on {url}, retrying once in 1s...")
                time.sleep(1.0)
                continue
            else:
                err_msg = f"Network failure after retry: {str(e)}"
                print(f"FAILED {url} error={err_msg}")
                return None, False, err_msg
        except Exception as e:
            err_msg = f"Unexpected request exception: {str(e)}"
            print(f"FAILED {url} error={err_msg}")
            return None, False, err_msg

    return None, False, "Max attempts exceeded"


def extract_book_urls(html: str, base_url: str) -> List[str]:
    """
    Parses a catalogue HTML page and extracts absolute product URLs.
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


def discover_catalogue(
    start_url: str,
    max_pages: int = MAX_CATALOGUE_PAGES,
    stats: Optional[ScraperStats] = None
) -> Tuple[int, List[Dict[str, str]]]:
    """
    Crawls catalogue pages up to max_pages.
    """
    current_url = start_url
    pages_crawled = 0
    discovered_items = []
    seen_urls = set()

    while current_url and pages_crawled < max_pages:
        pages_crawled += 1
        if stats:
            stats.catalogue_pages += 1
            
        cache_filename = get_cache_filename_for_url(current_url, is_catalogue=True, page_num=pages_crawled)
        
        html, _, err = fetch_page_with_cache(current_url, cache_filename, stats=stats)
        if not html:
            print(f"ERROR Failed to fetch catalogue page {pages_crawled}: {err}")
            break

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

    title_elem = soup.select_one("div.product_main h1")
    title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

    price_elem = soup.select_one("p.price_color")
    price_text = price_elem.get_text(strip=True).replace("Â", "") if price_elem else ""

    avail_elem = soup.select_one("p.availability")
    availability_text = avail_elem.get_text(strip=True) if avail_elem else ""

    star_elem = soup.select_one("p.star-rating")
    rating_text = "None"
    if star_elem:
        classes = [c for c in star_elem.get("class", []) if c != "star-rating"]
        rating_text = classes[0] if classes else "None"

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


def scrape_and_validate_all(
    discovered_items: List[Dict[str, str]],
    stats: ScraperStats
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Processes all items with failure isolation, retry handling, and validation.
    """
    valid_records = []
    invalid_records = []
    seen_canonical_urls = set()

    for item in discovered_items:
        product_url = item["product_url"]
        source_page = item["source_page"]

        if product_url in seen_canonical_urls:
            continue
        seen_canonical_urls.add(product_url)

        stats.detail_pages_attempted += 1
        cache_filename = get_cache_filename_for_url(product_url)
        fetch_time = datetime.now(timezone.utc).isoformat()

        # Isolated fetch per page
        html, _, err = fetch_page_with_cache(product_url, cache_filename, stats=stats)
        
        if err or not html:
            stats.failed_pages += 1
            invalid_records.append({
                "product_url": product_url,
                "source_page": source_page,
                "error": f"Failed to fetch page: {err}"
            })
            continue

        # Parse & Validate
        try:
            raw_record = parse_book_detail(
                html=html,
                product_url=product_url,
                source_page=source_page,
                fetched_at=fetch_time
            )

            validated_record, error_reason = validate_and_normalize_record(raw_record)
            if validated_record:
                valid_records.append(validated_record.model_dump())
                stats.valid_records += 1
            else:
                stats.invalid_records += 1
                invalid_records.append({
                    "raw_record": raw_record,
                    "error": error_reason
                })
        except Exception as parse_exc:
            stats.failed_pages += 1
            invalid_records.append({
                "product_url": product_url,
                "error": f"Parse exception: {str(parse_exc)}"
            })

    return valid_records, invalid_records


def save_output_files(
    valid_records: List[Dict[str, Any]],
    invalid_records: List[Dict[str, Any]],
    stats: ScraperStats
) -> Dict[str, Any]:
    """
    Saves validated books, error records, and run-report.json.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(BOOKS_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(valid_records, f, indent=2, ensure_ascii=False)

    with open(ERRORS_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(invalid_records, f, indent=2, ensure_ascii=False)

    report = stats.generate_report()
    with open(REPORT_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


def run_pipeline(simulate_fake_url: bool = False) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Runs the complete scraper pipeline.
    """
    stats = ScraperStats()
    
    # 1. Discover catalogue
    pages_count, discovered_items = discover_catalogue(START_URL, max_pages=MAX_CATALOGUE_PAGES, stats=stats)
    
    # Inject 1 fake broken URL locally if requested for Stage 5 failure test
    if simulate_fake_url:
        fake_url = "https://books.toscrape.com/catalogue/non-existent-broken-book-404_9999/index.html"
        discovered_items.append({
            "product_url": fake_url,
            "source_page": START_URL
        })
        print(f"\n[SIMULATION] Injected 1 fake URL for failure test: {fake_url}")

    # 2. Scrape & Validate
    valid_records, invalid_records = scrape_and_validate_all(discovered_items, stats)
    
    # 3. Save Outputs & Report
    report = save_output_files(valid_records, invalid_records, stats)
    
    return valid_records, invalid_records, report


def main():
    parser = argparse.ArgumentParser(description="FlyRank Polite Scraper")
    parser.add_argument("--simulate-failure", action="store_true", help="Injects one fake URL to test failure isolation")
    args = parser.parse_args()

    print("=== FlyRank Polite Scraper (Stage 5) ===")
    valid_records, invalid_records, report = run_pipeline(simulate_fake_url=args.simulate_failure)
    
    unique_product_urls = len(set(r["product_url"] for r in valid_records))
    print(f"\nvalid_records={len(valid_records)}")
    print(f"invalid_records={len(invalid_records)}")
    print(f"failed_pages={report['failed_pages']}")
    print(f"unique_urls={unique_product_urls}")
    
    print("\n--- Execution Run Report (output/run-report.json) ---")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
