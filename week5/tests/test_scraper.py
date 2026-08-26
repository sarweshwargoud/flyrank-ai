import pytest
from src.models import BookRecord, normalize_price_gbp, validate_and_normalize_record
from src.main import extract_book_urls, parse_book_detail


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
