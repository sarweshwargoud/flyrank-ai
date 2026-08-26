import os
import sys
from pathlib import Path
import requests

# Constants
BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
CATALOGUE_PAGE_1_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/sarweshwargoud/flyrank-ai)"
REQUEST_TIMEOUT = 10.0


def fetch_page_with_cache(url: str, cache_filename: str) -> str:
    """
    Fetches an HTML page with polite caching.
    If the file exists locally in cache/, it is loaded without making a network request.
    Otherwise, an HTTP GET request is performed with User-Agent and timeout headers,
    the HTTP status is verified, and the content is saved to cache/.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / cache_filename

    # Check local cache first
    if cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        byte_size = len(html_content.encode("utf-8"))
        print(f"CACHE HIT {cache_path.relative_to(BASE_DIR)} bytes={byte_size}")
        return html_content

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
    return html_content


def main():
    print("=== FlyRank Polite Scraper (Stage 1) ===")
    html = fetch_page_with_cache(
        url=CATALOGUE_PAGE_1_URL,
        cache_filename="catalogue-page-1.html"
    )
    print(f"Page 1 loaded successfully (length: {len(html)} chars).")


if __name__ == "__main__":
    main()
