import pytest
import requests
from unittest.mock import patch, MagicMock
from src.models import BookRecord, normalize_price_gbp, validate_and_normalize_record
from src.main import (
    extract_book_urls,
    parse_book_detail,
    fetch_page_with_cache,
    ScraperStats,
    scrape_and_validate_all
)


def test_price_normalization_valid():
    assert normalize_price_gbp("£51.77") == 51.77
    assert normalize_price_gbp("£0.99") == 0.99
    assert normalize_price_gbp("12.34") == 12.34
    assert normalize_price_gbp("Price: £123.45 incl tax") == 123.45


def test_price_normalization_invalid():
    assert normalize_price_gbp("Free") is None
    assert normalize_price_gbp("") is None
    assert normalize_price_gbp("£N/A") is None


def test_valid_book_record():
    raw = {
        "title": "A Light in the Attic",
        "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "price_text": "£51.77",
        "availability_text": "In stock (22 available)",
        "rating_text": "Three",
        "description": "A wonderful poetry collection.",
        "source_page": "https://books.toscrape.com/catalogue/page-1.html",
        "fetched_at": "2026-08-27T00:00:00Z"
    }
    record, err = validate_and_normalize_record(raw)
    assert err is None
    assert isinstance(record, BookRecord)
    assert record.price_gbp == 51.77
    assert record.title == "A Light in the Attic"
    assert record.price_text == "£51.77"


def test_nullable_description():
    raw = {
        "title": "Book Without Description",
        "product_url": "https://books.toscrape.com/catalogue/no-desc_999/index.html",
        "price_text": "£10.00",
        "availability_text": "In stock",
        "rating_text": "One",
        "description": None,
        "source_page": "https://books.toscrape.com/catalogue/page-1.html",
        "fetched_at": "2026-08-27T00:00:00Z"
    }
    record, err = validate_and_normalize_record(raw)
    assert err is None
    assert record.description is None


def test_invalid_product_url():
    raw = {
        "title": "Bad URL Book",
        "product_url": "invalid-relative-url.html",
        "price_text": "£15.00",
        "availability_text": "In stock",
        "rating_text": "Two",
        "description": None,
        "source_page": "https://books.toscrape.com/catalogue/page-1.html",
        "fetched_at": "2026-08-27T00:00:00Z"
    }
    record, err = validate_and_normalize_record(raw)
    assert record is None
    assert "URL must be an absolute HTTP/HTTPS URL" in err


def test_relative_to_absolute_url_conversion():
    catalogue_html = """
    <article class="product_pod">
        <h3><a href="a-light-in-the-attic_1000/index.html" title="A Light in the Attic">A Light in the ...</a></h3>
    </article>
    """
    base_url = "https://books.toscrape.com/catalogue/page-1.html"
    urls = extract_book_urls(catalogue_html, base_url)
    assert len(urls) == 1
    assert urls[0] == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"


def test_detail_parser_missing_description_fixture():
    detail_html = """
    <div class="product_main">
        <h1>Test Minimal Book</h1>
        <p class="price_color">£19.99</p>
        <p class="availability">In stock (5 available)</p>
        <p class="star-rating Five"></p>
    </div>
    """
    res = parse_book_detail(
        html=detail_html,
        product_url="https://books.toscrape.com/catalogue/test-minimal_1/index.html",
        source_page="https://books.toscrape.com/catalogue/page-1.html",
        fetched_at="2026-08-27T00:00:00Z"
    )
    assert res["title"] == "Test Minimal Book"
    assert res["price_text"] == "£19.99"
    assert res["rating_text"] == "Five"
    assert res["description"] is None


# -------------------------------------------------------------
# Stage 5 Failure & Retry Tests
# -------------------------------------------------------------
@patch("src.main.time.sleep")
@patch("src.main.requests.get")
def test_retry_on_500_server_error(mock_get, mock_sleep, tmp_path):
    stats = ScraperStats()
    # First attempt: 500 Server Error, Second attempt: 200 OK
    resp_500 = MagicMock(status_code=500)
    resp_200 = MagicMock(status_code=200, text="<html><body>Success</body></html>", encoding="utf-8")
    mock_get.side_effect = [resp_500, resp_200]

    with patch("src.main.CACHE_DIR", tmp_path):
        html, is_cache, err = fetch_page_with_cache(
            url="https://books.toscrape.com/test-500",
            cache_filename="test-500.html",
            stats=stats
        )
        assert err is None
        assert html == "<html><body>Success</body></html>"
        assert stats.retries == 1
        assert stats.network_requests == 2


@patch("src.main.time.sleep")
@patch("src.main.requests.get")
def test_no_retry_on_404_not_found(mock_get, mock_sleep, tmp_path):
    stats = ScraperStats()
    resp_404 = MagicMock(status_code=404)
    mock_get.return_value = resp_404

    with patch("src.main.CACHE_DIR", tmp_path):
        html, is_cache, err = fetch_page_with_cache(
            url="https://books.toscrape.com/test-404",
            cache_filename="test-404.html",
            stats=stats
        )
        assert html is None
        assert "HTTP 404" in err
        assert stats.retries == 0
        assert stats.network_requests == 1  # Called only once, no retry


@patch("src.main.time.sleep")
@patch("src.main.requests.get")
def test_no_retry_on_403_forbidden(mock_get, mock_sleep, tmp_path):
    stats = ScraperStats()
    resp_403 = MagicMock(status_code=403)
    mock_get.return_value = resp_403

    with patch("src.main.CACHE_DIR", tmp_path):
        html, is_cache, err = fetch_page_with_cache(
            url="https://books.toscrape.com/test-403",
            cache_filename="test-403.html",
            stats=stats
        )
        assert html is None
        assert "HTTP 403" in err
        assert stats.retries == 0
        assert stats.network_requests == 1


def test_failure_isolation_in_batch(tmp_path):
    stats = ScraperStats()
    sample_items = [
        {"product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html", "source_page": "https://books.toscrape.com/catalogue/page-1.html"},
        {"product_url": "https://books.toscrape.com/catalogue/fake-broken-404/index.html", "source_page": "https://books.toscrape.com/catalogue/page-1.html"}
    ]

    with patch("src.main.fetch_page_with_cache") as mock_fetch:
        valid_html = """
        <div class="product_main">
            <h1>A Light in the Attic</h1>
            <p class="price_color">£51.77</p>
            <p class="availability">In stock (22 available)</p>
            <p class="star-rating Three"></p>
        </div>
        """
        # First book succeeds, second fails with 404 error
        mock_fetch.side_effect = [
            (valid_html, True, None),
            (None, False, "HTTP 404 client error (no retry)")
        ]

        valid_records, invalid_records = scrape_and_validate_all(sample_items, stats)
        assert len(valid_records) == 1
        assert len(invalid_records) == 1
        assert stats.failed_pages == 1
        assert stats.valid_records == 1
        assert valid_records[0]["title"] == "A Light in the Attic"
