import re
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel, HttpUrl, field_validator


def normalize_price_gbp(price_text: str) -> Optional[float]:
    """
    Extracts a numeric float price from price text like '£51.77'.
    Returns None if no valid price pattern is found.
    """
    if not price_text:
        return None
    
    # Remove currency symbols and search for decimal number
    match = re.search(r'(\d+\.\d{2})', price_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


class BookRecord(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: Optional[str] = None
    source_page: str
    fetched_at: str

    @field_validator("product_url", "source_page")
    @classmethod
    def validate_https_url(cls, v: str) -> str:
        if not v.startswith("https://") and not v.startswith("http://"):
            raise ValueError("URL must be an absolute HTTP/HTTPS URL")
        return v

    @field_validator("title", "price_text", "availability_text", "rating_text", "fetched_at")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


def validate_and_normalize_record(raw_record: Dict[str, Any]) -> Tuple[Optional[BookRecord], Optional[str]]:
    """
    Normalizes price_gbp and validates raw_record against BookRecord Pydantic schema.
    Returns (BookRecord, None) on success, or (None, error_reason) on failure.
    """
    price_text = raw_record.get("price_text", "")
    price_gbp = normalize_price_gbp(price_text)
    
    if price_gbp is None:
        return None, f"Failed to normalize price_gbp from price_text: '{price_text}'"

    normalized_data = dict(raw_record)
    normalized_data["price_gbp"] = price_gbp

    try:
        validated_record = BookRecord(**normalized_data)
        return validated_record, None
    except Exception as e:
        return None, f"Pydantic Validation Error: {str(e)}"
