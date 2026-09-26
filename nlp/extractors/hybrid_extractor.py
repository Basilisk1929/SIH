"""Hybrid entity extractor resolving overlaps between Regex structured patterns and spaCy NER."""

from typing import List
from nlp.extractors.regex_extractor import RawEntity, RegexStructuredExtractor
from nlp.extractors.ner_extractor import SpacyNERExtractor


class HybridEntityExtractor:
    """Orchestrates regex extraction and spaCy NER with deterministic conflict resolution."""

    # Priority ordering for conflicting spans (higher index = higher priority)
    LABEL_PRIORITY = {
        "DATE": 1,
        "LOCATION": 2,
        "PERSON": 3,
        "BANK": 4,
        "SCAM_TYPE": 5,
        "AMOUNT": 6,
        "TRANSACTION_ID": 7,
        "ACCOUNT": 8,
        "PHONE": 9,
        "UPI_ID": 10,
    }

    def __init__(self, spacy_extractor: SpacyNERExtractor | None = None):
        self.spacy_extractor = spacy_extractor or SpacyNERExtractor()
        self.regex_extractor = RegexStructuredExtractor()

    def extract_all(self, text: str) -> List[RawEntity]:
        """Extract all candidate entities and resolve overlapping spans."""
        if not text:
            return []

        # 1. Gather all candidates from both extractors
        regex_entities = self.regex_extractor.extract_structured_entities(text)
        ner_entities = self.spacy_extractor.extract_entities(text)

        all_candidates = regex_entities + ner_entities

        # 2. Sort candidates:
        # High-priority structured labels first, then longest spans, then earlier start index
        all_candidates.sort(
            key=lambda e: (
                -self.LABEL_PRIORITY.get(e.label, 0),
                -(e.end - e.start),
                e.start,
            )
        )

        # 3. Greedy non-overlapping span selection
        chosen_entities: List[RawEntity] = []

        for candidate in all_candidates:
            # Check overlap with already chosen entities
            overlap = False
            for existing in chosen_entities:
                # Two spans overlap if max(start1, start2) < min(end1, end2)
                if max(candidate.start, existing.start) < min(candidate.end, existing.end):
                    overlap = True
                    break

            if not overlap:
                chosen_entities.append(candidate)

        # 4. Final sort by start position in text
        chosen_entities.sort(key=lambda e: e.start)
        return chosen_entities
