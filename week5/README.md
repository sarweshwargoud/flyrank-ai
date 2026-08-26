# FlyRank Week 5 — The Polite Scraper

A robust, ethical, and idempotent web scraping pipeline built in Python using `requests`, `BeautifulSoup`, and `Pydantic`.

---

## Project Overview

This project implements the FlyRank Internship Backend Track (Week 5 / Assignment A9) scraping pipeline. It is architected around strict engineering discipline, politeness standards, failure isolation, and data schema validation.

The scraping pipeline executes in a structured multi-stage flow:
```text
Fetch (with custom User-Agent & timeout)
  └── Cache (local disk persistence)
        └── Discover (catalogue pagination & URL resolution)
              └── Extract (raw product fields & provenance)
                    └── Normalize (numeric price conversion)
                          └── Validate (Pydantic schema enforcement)
                                └── Store (idempotent JSON emission)
                                      └── Report (runtime metrics audit)
```

---

## Target Classification

* **Target URL**: [https://books.toscrape.com/](https://books.toscrape.com/)
* **Site Purpose & Appropriateness**: The target is a publicly hosted sandbox environment explicitly created by Zyte for developers to practice web scraping without impacting production commerce platforms. The homepage explicitly states:
  > *"Warning! This is a demo website for web scraping purposes. Prices and ratings here were randomly assigned and have no real meaning."*
* **Scope**: Strictly limited to the first **3 catalogue pages** (`page-1.html`, `page-2.html`, `page-3.html`), yielding exactly **60 unique books**.
* **Data Collected**:
  - `title`
  - `product_url` (canonical HTTPS URL)
  - `price_text` (raw currency string)
  - `price_gbp` (normalized numeric float)
  - `availability_text` (in-stock information)
  - `rating_text` (word-form star rating)
  - `description` (nullable product synopsis)
  - `source_page` (origin catalogue URL provenance)
  - `fetched_at` (ISO-8601 UTC timestamp provenance)
* **Robots.txt Inspection Result**:
  A single live request to `https://books.toscrape.com/robots.txt` returned **HTTP 404 Not Found** (*no robots file found*). A missing robots.txt file does not imply unrestricted permission; we restrict all operations to the designated sandbox and adhere to strict politeness standards.

> **Ethical Commitment**:
> "I will not reuse this code on another site without checking its rules and terms first."

---

## Python Lane

The solution is built using standard Python tools:
* **`requests`**: HTTP transport with custom headers, timeouts, and status code verification.
* **`beautifulsoup4`**: HTML parsing and CSS selector extraction.
* **`pydantic`**: Strict data validation, type checking, and URL validation.
* **`pytest`**: Automated unit testing suite with mocked HTTP interactions.
* **`json`**: Formatted and idempotent JSON serialization.

---

## Installation

To set up the project locally in under 2 minutes:

```bash
# 1. Navigate to week5 directory
cd week5

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
.venv\Scripts\activate.bat
# On Linux / macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## Run

Run the complete scraper pipeline with a single command from inside `week5/`:

```bash
python src/main.py
```

---

## Output

The scraper writes its results to the `output/` directory:

| Output File | Purpose |
| :--- | :--- |
| `output/books.json` | The final clean dataset containing all **60 validated book records**. |
| `output/errors.json` | Quarantine file for any records failing schema validation or detail page fetches (empty `[]` on a healthy run). |
| `output/run-report.json` | Execution telemetry report recording timing, request counts, cache hits, and status metrics. |

---

## Record Schema

Every stored record in `output/books.json` follows this schema:

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "It's hard to imagine a world without A Light in the Attic...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-08-26T19:36:46.942439+00:00"
}
```

* **Raw vs Normalized Price**: `price_text` (`"£51.77"`) preserves the exact original source value for auditing, while `price_gbp` (`51.77`) provides a floating-point numeric value suitable for mathematical sorting and aggregation.
* **Nullable Description**: If a book lacks a description, `description` is stored as `null` rather than fabricating placeholder text.
* **Provenance**: `source_page` and `fetched_at` establish a clear audit trail of where and when the fact was retrieved.

---

## Politeness Rules

1. **Honest User-Agent**: Every request identifies itself via `FlyRankInternship-A9/1.0 (+https://github.com/sarweshwargoud/flyrank-ai)`.
2. **Request Timeouts**: All network calls enforce a strict 10.0-second timeout.
3. **Status Code Verification**: Only `HTTP 200 OK` is treated as a valid page response.
4. **Rate Limiting**: A delay of at least **0.5 seconds** is enforced between consecutive live HTTP requests.
5. **Caching**: Raw HTML files are cached locally so repeated executions generate 0 live network calls.

---

## Caching

- On the **first run**, pages are fetched from the server and saved to `cache/` (e.g. `cache/catalogue-page-1.html`, `cache/book-a-light-in-the-attic_1000.html`). The terminal prints `FETCH ...`.
- On **subsequent runs**, cached files are detected on disk and loaded immediately. The terminal prints `CACHE HIT ...`.
- The `cache/` folder is listed in `.gitignore` to keep raw HTML files out of source control.

---

## URL Discovery

The scraper crawls catalogue pagination dynamically rather than using hardcoded URLs:
```text
Catalogue Page 1 ─(next link)─> Catalogue Page 2 ─(next link)─> Catalogue Page 3 ─(stop)
```
- Relative links (e.g. `a-light-in-the-attic_1000/index.html`) are resolved to canonical HTTPS URLs using `urllib.parse.urljoin()`.
- **Catalogue pages crawled**: 3
- **Discovered book URLs**: 60
- **Unique book URLs**: 60

---

## Validation & Error Routing

Every record is validated against a Pydantic `BookRecord` model.
- Valid records are written to `output/books.json`.
- Malformed records (e.g., unparseable prices, invalid URLs, empty titles) are segregated into `output/errors.json` alongside detailed diagnostic error messages.

---

## Idempotency

Running the scraper multiple times **rebuilds** the output files deterministically rather than appending. Whether run once or ten times, `output/books.json` contains exactly **60 unique records**.

---

## Failure Handling & Retry Rules

- **Failure Isolation**: Each detail page is fetched and parsed independently. A failure on one page is logged in `errors.json` and does not crash or abort the rest of the 59+ records.
- **Retry Policy**:
  - **Timeouts / HTTP 5xx Server Errors**: Retried **exactly once** after a 1.0s backoff pause.
  - **HTTP 404 Not Found**: **Never retried**. The page does not exist; retrying wastes bandwidth.
  - **HTTP 403 Forbidden**: **Never retried**. The server rejected access; retrying violates polite scraping practices.

---

## Execution Run Report (`output/run-report.json`)

| Metric Field | Definition |
| :--- | :--- |
| `start_time` | ISO-8601 UTC timestamp when pipeline execution began |
| `end_time` | ISO-8601 UTC timestamp when execution finished |
| `duration_seconds` | Total elapsed pipeline runtime |
| `catalogue_pages_crawled` | Number of catalogue pagination pages processed (3) |
| `detail_pages_attempted` | Total number of book detail pages queued for processing (60) |
| `pages_fetched` | Count of real network HTTP requests executed |
| `cache_hits` | Count of pages served directly from local disk cache |
| `valid_records` | Count of records passing Pydantic validation (60) |
| `invalid_records` | Count of records failing validation (0) |
| `failed_pages` | Count of pages encountering fatal network or HTTP errors (0) |
| `retries_performed` | Number of retries triggered for transient 5xx/timeout errors (0) |

### Real Production Run Report Output
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

---

## Failure-Test Verification Evidence

To verify resilience against broken pages, the pipeline includes a failure simulation mode (`python src/main.py --simulate-failure`), which injects an artificial 404 URL (`.../non-existent-broken-book-404_9999/index.html`):

* **Result**:
  - The pipeline completed normally without crashing.
  - `failed_pages` was recorded as `1` in `run-report.json`.
  - The failure reason was documented in `output/errors.json`.
  - All **60 valid records** in `output/books.json` remained completely intact.

---

## Automated Unit Testing

Run the test suite using `pytest`:

```bash
pytest tests/test_scraper.py -v
```

### Actual Test Output
```text
tests/test_scraper.py::test_price_normalization_valid PASSED             [  9%]
tests/test_scraper.py::test_price_normalization_invalid PASSED           [ 18%]
tests/test_scraper.py::test_valid_book_record PASSED                     [ 27%]
tests/test_scraper.py::test_nullable_description PASSED                  [ 36%]
tests/test_scraper.py::test_invalid_product_url PASSED                   [ 45%]
tests/test_scraper.py::test_relative_to_absolute_url_conversion PASSED   [ 54%]
tests/test_scraper.py::test_detail_parser_missing_description_fixture PASSED [ 63%]
tests/test_scraper.py::test_retry_on_500_server_error PASSED             [ 72%]
tests/test_scraper.py::test_no_retry_on_404_not_found PASSED             [ 81%]
tests/test_scraper.py::test_no_retry_on_403_forbidden PASSED             [ 90%]
tests/test_scraper.py::test_failure_isolation_in_batch PASSED            [100%]

============================= 11 passed in 0.79s ==============================
```

---

## Ethics & Responsible Scraping

1. **Use Official APIs**: Always prefer official APIs when available.
2. **Never Bypass Authentication or Paywalls**: Do not scrape behind logins or circumvent access controls.
3. **Never Circumvent Blocks**: Respect HTTP 403, 429, and CAPTCHAs.
4. **Collect Only Required Data**: Limit scrape depth to the minimum necessary fields and pages.
5. **Polite Resource Consumption**: Enforce rate limits, user-agents, and aggressive local caching.

---

## Why No Browser Automation?

A full browser automation tool (such as Playwright or Selenium) was intentionally avoided:
- **Server-Side Rendered HTML**: Books to Scrape delivers complete HTML in the initial server response without requiring client-side JavaScript execution.
- **Resource Efficiency**: `requests` + `BeautifulSoup` consumes a fraction of CPU and memory compared to headless Chromium instances.
- **Polite Footprint**: Static HTTP requests produce minimal server load compared to full browser sessions that fetch fonts, images, and trackers.

---

## Known Limitations

- **HTML Structure Dependency**: The extraction logic relies on the current CSS class structure (`article.product_pod`, `div.product_main`, `p.price_color`). Structural changes by the site operators would require updating the CSS selectors.
- **Fixed Pagination Depth**: The crawler is hard-capped at 3 catalogue pages (60 books) in accordance with the assignment specification.
