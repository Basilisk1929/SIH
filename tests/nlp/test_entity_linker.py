"""Tests for entity linking module."""

from nlp.linking.entity_linker import EntityLinker
from nlp.normalizers.entity_normalizer import NormalizedEntity


def test_linker_resolves_known_synthetic_account():
    linker = EntityLinker()
    ent = NormalizedEntity(
        text="SYN1000000001",
        label="ACCOUNT",
        start=0,
        end=13,
        normalized_value="SYN1000000001",
        confidence=0.99,
        extractor="regex",
    )
    linked = linker.link_entity(ent)
    assert linked.linked_entity is not None
    assert linked.linked_entity["is_known_entity"] is True
    assert linked.linked_entity["account_number"] == "SYN1000000001"


def test_linker_resolves_known_bank():
    linker = EntityLinker()
    ent = NormalizedEntity(
        text="State Bank of Synth",
        label="BANK",
        start=0,
        end=19,
        normalized_value="State Bank of Synth",
        confidence=0.95,
        extractor="spacy_ner",
    )
    linked = linker.link_entity(ent)
    assert linked.linked_entity is not None
    assert linked.linked_entity["bank_code"] == "SYNB"


def test_linker_handles_unknown_entity_gracefully():
    linker = EntityLinker()
    ent = NormalizedEntity(
        text="SYN9999999999",
        label="ACCOUNT",
        start=0,
        end=13,
        normalized_value="SYN9999999999",
        confidence=0.90,
        extractor="regex",
    )
    linked = linker.link_entity(ent)
    assert linked.linked_entity is not None
    assert linked.linked_entity["is_known_entity"] is False
