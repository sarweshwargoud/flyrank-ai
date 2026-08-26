import os
import sys
import time
from pathlib import Path
from urllib.parse import urljoin
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup

# Constants
BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/sarweshwargoud/flyrank-ai)"
REQUEST_TIMEOUT = 10.0
POLITE_DELAY_SECONDS = 0.5
MAX_CATALOGUE_PAGES = 3


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
    
    # Each book is in <article class="product_pod"><h3><a href="...">
    for article in soup.select("article.product_pod h3 a"):
        href = article.get("href")
        if href:
            absolute_url = urljoin(base_url, href)
            book_urls.append(absolute_url)
            
    return book_urls


def extract_next_page_url(html: str, base_url: str) -> str | None:
    """
    Finds the 'next' pagination link in the catalogue page.
    """
    soup = BeautifulSoup(html, "html.parser")
    next_tag = soup.select_one("li.next a")
    if next_tag and next_tag.get("href"):
        return urljoin(base_url, next_tag.get("href"))
    return None


def discover_catalogue(start_url: str, max_pages: int = MAX_CATALOGUE_PAGES) -> Tuple[int, List[str]]:
    """
    Crawls catalogue pages up to max_pages, extracting all book URLs.
    """
    current_url = start_url
    pages_crawled = 0
    all_book_urls = []

    while current_url and pages_crawled < max_pages:
        pages_crawled += 1
        cache_filename = f"catalogue-page-{pages_crawled}.html"
        
        html, _ = fetch_page_with_cache(current_url, cache_filename)
        urls = extract_book_urls(html, current_url)
        all_book_urls.extend(urls)
        
        # Follow pagination
        next_url = extract_next_page_url(html, current_url)
        current_url = next_url if (pages_crawled < max_pages) else None

    # Deduplicate while preserving order
    unique_urls = list(dict.fromkeys(all_book_urls))
    return pages_crawled, unique_urls


def main():
    print("=== FlyRank Polite Scraper (Stage 2) ===")
    pages_count, book_urls = discover_catalogue(START_URL, max_pages=MAX_CATALOGUE_PAGES)
    
    print(f"\ncatalogue_pages={pages_count} discovered={len(book_urls)} unique_urls={len(set(book_urls))}")
    if book_urls:
        print(f"Sample URL 1: {book_urls[0]}")
        print(f"Sample URL 60: {book_urls[-1]}")


if __name__ == "__main__":
    main()
