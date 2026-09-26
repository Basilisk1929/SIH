"""Tests for entity normalization logic."""

from nlp.normalizers.entity_normalizer import EntityNormalizer
from nlp.extractors.regex_extractor import RawEntity


def test_normalize_phone_to_e164():
    assert EntityNormalizer.normalize_phone("9836271527") == "+919836271527"
    assert EntityNormalizer.normalize_phone("+91 98362 71527") == "+919836271527"
    assert EntityNormalizer.normalize_phone("09836271527") == "+919836271527"


def test_normalize_amount_to_numeric():
    assert EntityNormalizer.normalize_amount("₹49,999.00") == 49999.0
    assert EntityNormalizer.normalize_amount("Rs. 25,000") == 25000.0
    assert EntityNormalizer.normalize_amount("10000 INR") == 10000.0


def test_normalize_bank_aliases():
    assert EntityNormalizer.normalize_bank("SBI") == "State Bank of Synth"
    assert EntityNormalizer.normalize_bank("HDFC") == "Synth HDFC Commercial Bank"
    assert EntityNormalizer.normalize_bank("ICICI") == "Synth ICICI Banking Corp"
    assert EntityNormalizer.normalize_bank("Punjab National Bank") == "Punjab & Synth National Bank"


def test_normalize_raw_entity_dispatch():
    raw_phone = RawEntity(text="9836271527", label="PHONE", start=0, end=10)
    norm = EntityNormalizer.normalize(raw_phone)
    assert norm.normalized_value == "+919836271527"

    raw_amt = RawEntity(text="₹49,999.00", label="AMOUNT", start=0, end=10)
    norm_amt = EntityNormalizer.normalize(raw_amt)
    assert norm_amt.normalized_value == 49999.0
