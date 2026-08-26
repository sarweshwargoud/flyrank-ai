# FlyRank Week 5 — The Polite Scraper

A robust, ethical web scraping pipeline built in Python using `requests`, `BeautifulSoup`, and `Pydantic`.

---

## Target Classification

* **Target Site**: [https://books.toscrape.com/](https://books.toscrape.com/)
* **Site Purpose & Appropriateness**: The target is a publicly hosted sandbox environment explicitly built for developers to practice web scraping. The homepage explicitly states:
  > *"Warning! This is a demo website for web scraping purposes. Prices and ratings here were randomly assigned and have no real meaning."*
* **Scope**: Exactly the first **3 catalogue pages** (`page-1.html`, `page-2.html`, `page-3.html`), yielding exactly **60 books**.
* **Data Collected**:
  - Book title
  - Product canonical URL
  - Price (raw text and normalized numeric GBP)
  - Availability status
  - Star rating
  - Product description
  - Source catalogue URL (provenance)
  - ISO fetch timestamp (provenance)
* **Robots.txt Inspection Result**:
  A single live request to `https://books.toscrape.com/robots.txt` returned **HTTP 404 Not Found** (*no robots file found*). A missing robots.txt file does not mean carte blanche; we restrict all operations to the designated sandbox and adhere to strict politeness standards.

> **Ethical Commitment**:
> "I will not reuse this code on another site without checking its rules and terms first."

---

## Engineering Concepts & Politeness Rules

1. **User-Agent Header**: Every outbound HTTP request introduces itself with an honest identification header (`FlyRankInternship-A9/1.0 (+https://github.com/sarweshwargoud/flyrank-ai)`).
2. **Request Timeouts**: All network calls enforce a strict timeout (e.g. 10 seconds) so the process never hangs indefinitely.
3. **HTTP Status Code Verification**: The scraper checks `status_code == 200` before inspecting response bodies.
4. **Local Disk Caching**: Raw HTML pages are saved locally to `cache/`. Repeated script runs read from the local cache instead of re-fetching from the live server.
5. **Rate Limiting**: A polite delay of at least 0.5 seconds is enforced between consecutive real network requests.
6. **Provenance & Canonical URLs**: Every extracted record stores its origin URL and fetch timestamp for auditability.
7. **Schema Validation**: Extracted records are validated using Pydantic schemas before persistence in `output/books.json`.
