"""Tests for spaCy NER extractor."""

from nlp.extractors.ner_extractor import SpacyNERExtractor


def test_spacy_extracts_banks_locations_and_persons():
    extractor = SpacyNERExtractor()
    narrative = (
        "Complainant Suresh Bhatia from Mumbai lodged complaint against State Bank of Synth. "
        "Incident involved digital arrest scam near Jamtara-Karmatanr."
    )
    entities = extractor.extract_entities(narrative)
    labels = {e.label: [x.text for x in entities if x.label == e.label] for e in entities}

    assert "PERSON" in labels
    assert any("Suresh Bhatia" in p for p in labels["PERSON"])

    assert "BANK" in labels
    assert any("State Bank of Synth" in b for b in labels["BANK"])

    assert "LOCATION" in labels
    assert any("Mumbai" in l for l in labels["LOCATION"])
    assert any("Jamtara" in l for l in labels["LOCATION"])

    assert "SCAM_TYPE" in labels
    assert any("digital arrest" in s.lower() for s in labels["SCAM_TYPE"])


def test_spacy_empty_text():
    extractor = SpacyNERExtractor()
    assert extractor.extract_entities("") == []
