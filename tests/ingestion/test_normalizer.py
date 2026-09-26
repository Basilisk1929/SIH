"""Unit tests for DataNormalizer engine."""

from decimal import Decimal
from ingestion.app.services.normalizer import DataNormalizer


def test_phone_number_normalization():
    """Verify conversion of various Indian phone formats to standard E.164."""
    assert DataNormalizer.normalize_phone_number("9876543210") == "+919876543210"
    assert DataNormalizer.normalize_phone_number("+91 98765 43210") == "+919876543210"
    assert DataNormalizer.normalize_phone_number("09876543210") == "+919876543210"
    assert DataNormalizer.normalize_phone_number("91-98765-43210") == "+919876543210"
    assert DataNormalizer.normalize_phone_number("N/A") == "N/A"
    assert DataNormalizer.normalize_phone_number(None) == "N/A"


def test_ifsc_normalization():
    """Verify IFSC uppercase and trimming."""
    assert DataNormalizer.normalize_ifsc(" synb0001091 ") == "SYNB0001091"
    assert DataNormalizer.normalize_ifsc("hdfc0000240") == "HDFC0000240"
    assert DataNormalizer.normalize_ifsc(None) == "N/A"


def test_vpa_normalization():
    """Verify UPI VPA lowercasing and trimming."""
    assert DataNormalizer.normalize_vpa(" Citizen.42@SYNAXIS ") == "citizen.42@synaxis"
    assert DataNormalizer.normalize_vpa("MULE@OKSBI") == "mule@oksbi"
    assert DataNormalizer.normalize_vpa("") == "N/A"


def test_amount_normalization():
    """Verify currency cleaning and decimal conversion."""
    assert DataNormalizer.normalize_amount("₹ 45,000.50") == Decimal("45000.50")
    assert DataNormalizer.normalize_amount(12500) == Decimal("12500.00")
    assert DataNormalizer.normalize_amount("100.999") == Decimal("101.00")
    assert DataNormalizer.normalize_amount(None) == Decimal("0.00")


def test_record_normalization():
    """Verify bulk record dictionary normalization."""
    raw = {
        "sender_account_number": " syn-100-01 ",
        "sender_upi_id": " USER@SYNAXIS ",
        "amount": "₹ 24,999.00",
        "timestamp": "2024-08-15 10:30:00",
    }
    normalized = DataNormalizer.normalize_record(raw, "transaction")
    assert normalized["sender_account_number"] == "SYN10001"
    assert normalized["sender_upi_id"] == "user@synaxis"
    assert normalized["amount"] == Decimal("24999.00")
    assert normalized["event_timestamp"].year == 2024
