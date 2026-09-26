"""Tests for NLP entity extraction on cybercrime narratives."""

from nlp.extractors.entity_extractor import CybercrimeEntityExtractor
from nlp.classifiers.scam_classifier import ScamCategoryClassifier


def test_cybercrime_entity_extractor_finds_identifiers():
    """Verify regex and patterns extract VPA, phone, IFSC, and APK names."""
    sample_narrative = (
        "Victim was asked to transfer money to mule.88@oksbi or account 987654321098 "
        "at IFSC SBIN0001234. Suspect called from +919876543210 and asked to download BijliUpdate.apk."
    )
    entities = CybercrimeEntityExtractor.extract_entities(sample_narrative)

    assert "mule.88@oksbi" in entities["upi_ids"]
    assert "SBIN0001234" in entities["ifsc_codes"]
    assert any("BijliUpdate.apk" in apk.lower() for apk in entities["apk_files"])
    assert len(entities["phone_numbers"]) >= 1


def test_scam_category_classifier():
    """Verify narrative classification into fraud typology."""
    text = "Victim received call claiming electricity will be disconnected tonight. Asked to download APK."
    category, confidence = ScamCategoryClassifier.classify_narrative(text)
    assert category == "Phishing & Malware"
    assert confidence >= 0.50
