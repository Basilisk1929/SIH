"""Tests for NLP text preprocessing module."""

from nlp.preprocessing.text_preprocessor import TextPreprocessor


def test_text_preprocessor_removes_invisible_characters():
    # String with zero-width space and joiners
    raw = "Citizen\u200B Neha\uFEFF Singh \u200Ereports fraud."
    cleaned = TextPreprocessor.preprocess(raw)
    assert cleaned == "Citizen Neha Singh reports fraud."
    assert "\u200B" not in cleaned
    assert "\uFEFF" not in cleaned


def test_text_preprocessor_standardizes_quotes_and_dashes():
    raw = "“Suspicious call” from ‘handler’ – money transferred — immediately."
    cleaned = TextPreprocessor.preprocess(raw)
    assert '"Suspicious call"' in cleaned
    assert "'handler'" in cleaned
    assert " - money transferred - " in cleaned


def test_text_preprocessor_preserves_currency_and_symbols():
    raw = "Unauthorized debit of ₹49,999.00 to suspect@oksbi (+919876543210)."
    cleaned = TextPreprocessor.preprocess(raw)
    assert "₹49,999.00" in cleaned
    assert "suspect@oksbi" in cleaned
    assert "+919876543210" in cleaned


def test_text_preprocessor_empty_input():
    assert TextPreprocessor.preprocess("") == ""
    assert TextPreprocessor.preprocess(None) == ""
