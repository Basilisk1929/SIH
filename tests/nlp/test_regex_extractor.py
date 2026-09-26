"""Tests for structured regex extractor."""

from nlp.extractors.regex_extractor import RegexStructuredExtractor


def test_regex_extracts_all_structured_entity_types():
    narrative = (
        "Transfer of ₹49,999.00 from account SYN1000004465 to beneficiary account 987654321098. "
        "Sent via UPI ID nikhil.mishra.971@synoksbi. Suspect called from +919836271527. "
        "Reference Txn ID: TXN_00038001 dated 2024-08-15 at 10:30 AM."
    )
    entities = RegexStructuredExtractor.extract_structured_entities(narrative)
    labels = {e.label: [x.text for x in entities if x.label == e.label] for e in entities}

    assert "AMOUNT" in labels
    assert "₹49,999.00" in labels["AMOUNT"]

    assert "ACCOUNT" in labels
    assert "SYN1000004465" in labels["ACCOUNT"]
    assert "987654321098" in labels["ACCOUNT"]

    assert "UPI_ID" in labels
    assert "nikhil.mishra.971@synoksbi" in labels["UPI_ID"]

    assert "PHONE" in labels
    assert any("9836271527" in p for p in labels["PHONE"])

    assert "TRANSACTION_ID" in labels
    assert "TXN_00038001" in labels["TRANSACTION_ID"]

    assert "DATE" in labels
    assert any("2024-08-15" in d for d in labels["DATE"])


def test_regex_extracts_amounts_in_various_currencies():
    narratives = [
        ("Debited Rs. 25,000 immediately.", "25,000"),
        ("Transferred 15000 INR to handler.", "15000"),
        ("Loss of ₹1,00,000 reported.", "1,00,000"),
    ]
    for text, expected in narratives:
        entities = RegexStructuredExtractor.extract_structured_entities(text)
        amounts = [e.text for e in entities if e.label == "AMOUNT"]
        assert len(amounts) >= 1
        assert any(expected in a for a in amounts)
