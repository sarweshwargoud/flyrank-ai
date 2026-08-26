# FlyRank Week 5 — The Polite Scraper

A robust, ethical web scraping pipeline built in Python using `requests`, `BeautifulSoup`, and `Pydantic`.

---

## Target Classification

* **Target Site**: [https://books.toscrape.com/](https://books.toscrape.com/)
* **Site Purpose & Appropriateness**: The target is a publicly hosted sandbox environment explicitly built for developers to practice web scraping. The homepage states:
  > *"Warning! This is a demo website for web scraping purposes. Prices and ratings here were randomly assigned and have no real meaning."*
* **Scope**: Exactly the first **3 catalogue pages** (`page-1.html`, `page-2.html`, `page-3.html`), yielding exactly **60 books**.
* **Data Collected**:
  - Book title
  - Product canonical URL
  - Price (raw text `price_text` and normalized numeric float `price_gbp`)
  - Availability status
  - Star rating
  - Product description (nullable)
  - Source catalogue URL (provenance)
  - ISO fetch timestamp (provenance)
* **Robots.txt Inspection Result**:
  A single live request to `https://books.toscrape.com/robots.txt` returned **HTTP 404 Not Found** (*no robots file found*). A missing robots.txt file does not mean carte blanche; we restrict all operations to the designated sandbox and adhere to strict politeness standards.

> **Ethical Commitment**:
> "I will not reuse this code on another site without checking its rules and terms first."

---

## Engineering Concepts & Politeness Rules

1. **User-Agent Header**: Every outbound HTTP request introduces itself with an honest identification header (`FlyRankInternship-A9/1.0 (+https://github.com/sarweshwargoud/flyrank-ai)`).
2. **Request Timeouts**: All network calls enforce a strict 10.0-second timeout so the scraper never hangs indefinitely.
3. **HTTP Status Code Verification**: The scraper checks `status_code == 200` before inspecting response bodies.
4. **Local Disk Caching**: Raw HTML pages are saved locally to `cache/`. Repeated script runs read from the local cache instead of re-fetching from the live server.
5. **Rate Limiting**: A polite delay of at least 0.5 seconds is enforced between consecutive real network requests.
6. **Provenance & Canonical URLs**: Every extracted record stores its origin URL and fetch timestamp for auditability.
7. **Schema Validation**: Extracted records are validated using Pydantic schemas before persistence in `output/books.json`.
8. **Failure Isolation & Non-Fatal Errors**: Each book detail page is fetched and parsed independently. A failure on one page is recorded in `output/errors.json` and does not abort the entire pipeline.
9. **Polite Retry Policy**:
   - **Timeouts / 5xx Server Errors**: Retried **exactly once** after a 1.0s backoff.
   - **404 Not Found**: **Never retried**. The resource does not exist; asking again will not create it.
   - **403 Forbidden**: **Never retried**. The server explicitly rejected access; asking again turns a polite robot into a nuisance.

---

## Execution Run Report (`output/run-report.json`)

Every scraper execution produces a comprehensive summary metrics report:

| Metric Field | Definition |
| :--- | :--- |
| `start_time` | ISO-8601 UTC timestamp when the pipeline started |
| `end_time` | ISO-8601 UTC timestamp when the pipeline completed |
| `duration_seconds` | Total elapsed pipeline runtime |
| `catalogue_pages_crawled` | Number of catalogue pagination pages processed (up to 3) |
| `detail_pages_attempted` | Total number of book detail pages queued for processing |
| `pages_fetched` | Count of real network HTTP requests initiated |
| `cache_hits` | Count of pages served directly from local disk cache |
| `valid_records` | Number of records passing Pydantic validation |
| `invalid_records` | Number of records failing validation |
| `failed_pages` | Count of detail pages that encountered fatal HTTP or parse errors |
| `retries_performed` | Number of retry attempts made for transient network/5xx errors |

### Sample Production Run Report
```json
{
  "start_time": "2026-08-26T19:36:46.942439+00:00",
  "end_time": "2026-08-26T19:36:48.014712+00:00",
  "duration_seconds": 1.072,
  "catalogue_pages_crawled": 3,
  "detail_pages_attempted": 60,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0,
  "retries_performed": 0
}
```

### Failure Test Verification Evidence
Running `python src/main.py --simulate-failure` injects one artificial 404 URL (`.../non-existent-broken-book-404_9999/index.html`).
- **Pipeline Status**: Successfully completed without crashing.
- **`books.json`**: Preserved all **60 valid records**.
- **`errors.json`**: Recorded the failure (`"Failed to fetch page: HTTP 404 client error (no retry)"`).
- **`run-report.json`**: Reported `failed_pages: 1`.

---

## Running the Project

```bash
# 1. Run full scraper pipeline
python src/main.py

# 2. Run with failure simulation test
python src/main.py --simulate-failure

# 3. Run automated unit test suite
pytest tests/test_scraper.py -v
```
