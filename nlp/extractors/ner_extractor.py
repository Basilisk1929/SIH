"""spaCy-based Named Entity Recognition extractor for cybercrime narratives."""

import logging
import re
from typing import List, Optional
import spacy
from spacy.language import Language
from spacy.matcher import PhraseMatcher

from nlp.extractors.regex_extractor import RawEntity

logger = logging.getLogger(__name__)

# Known Indian & Synthetic Banks
KNOWN_BANKS = [
    "State Bank of Synth",
    "Synth HDFC Commercial Bank",
    "Synth ICICI Banking Corp",
    "Synth Axis Finance Bank",
    "Punjab & Synth National Bank",
    "Kotak Synth Mahindra Bank",
    "Bank of Synth Baroda",
    "Union Synth Bank of India",
    "Synth Payments & Small Finance Bank",
    "Jan-Synth Gramin Vikas Bank",
    "State Bank of India",
    "SBI",
    "HDFC Bank",
    "HDFC",
    "ICICI Bank",
    "ICICI",
    "Axis Bank",
    "Punjab National Bank",
    "PNB",
    "Bank of Baroda",
    "Canara Bank",
    "Union Bank",
    "Kotak Mahindra Bank",
    "Reserve Bank of India",
    "RBI",
]

# Known Indian Cities & Cybercrime Hotspots
KNOWN_LOCATIONS = [
    "Mumbai", "Pune", "Nagpur", "New Delhi", "Delhi", "Dwarka", "Rohini",
    "Bengaluru", "Mysuru", "Hubballi", "Hyderabad", "Secunderabad", "Warangal",
    "Noida", "Lucknow", "Kanpur", "Jaipur", "Jodhpur", "Kota", "Ahmedabad",
    "Surat", "Vadodara", "Kolkata", "Bidhannagar", "Siliguri", "Gurugram",
    "Faridabad", "Ambala", "Ranchi", "Jamshedpur", "Dhanbad", "Chennai",
    "Coimbatore", "Madurai", "Patna", "Gaya", "Muzaffarpur",
    "Jamtara", "Jamtara-Karmatanr", "Mewat", "Mewat-Nuh", "Bharatpur",
    "Bharatpur-Deeg", "Alwar", "Alwar-Ramgarh",
]

# Known Cyber Scam Typologies
KNOWN_SCAM_TYPES = [
    "UPI fraud",
    "KYC fraud",
    "investment fraud",
    "fake customer care",
    "phishing",
    "loan scam",
    "job scam",
    "impersonation",
    "digital arrest",
    "digital arrest scam",
    "online shopping fraud",
    "sextortion",
]


class SpacyNERExtractor:
    """Named Entity Recognizer combining spaCy models with gazetteers and phrase matchers."""

    COMPLAINANT_PREFIX_REGEX = re.compile(
        r"\b(?:Complainant|Citizen|Victim|Senior citizen|Admin)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
    )

    def __init__(self, model_name: str = "en_core_web_sm"):
        try:
            self.nlp: Language = spacy.load(model_name)
        except Exception:
            logger.warning(f"Could not load '{model_name}'. Falling back to spacy.blank('en').")
            self.nlp: Language = spacy.blank("en")
            if "sentencizer" not in self.nlp.pipe_names:
                self.nlp.add_pipe("sentencizer")

        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self._init_phrase_matchers()

    def _init_phrase_matchers(self) -> None:
        """Register domain phrase matchers for Banks, Locations, and Scam Types."""
        bank_patterns = [self.nlp.make_doc(b) for b in KNOWN_BANKS]
        self.matcher.add("BANK", bank_patterns)

        loc_patterns = [self.nlp.make_doc(loc) for loc in KNOWN_LOCATIONS]
        self.matcher.add("LOCATION", loc_patterns)

        scam_patterns = [self.nlp.make_doc(st) for st in KNOWN_SCAM_TYPES]
        self.matcher.add("SCAM_TYPE", scam_patterns)

    def extract_entities(self, text: str) -> List[RawEntity]:
        """Extract PERSON, BANK, LOCATION, DATE, and SCAM_TYPE spans."""
        if not text:
            return []

        doc = self.nlp(text)
        raw_entities: List[RawEntity] = []

        # 1. Process spaCy Model's Statistical NER (if pipe available)
        if "ner" in self.nlp.pipe_names:
            for ent in doc.ents:
                label = ent.label_
                clean_text = ent.text.strip()
                if not clean_text:
                    continue

                if label == "PERSON":
                    if "@" not in clean_text and not any(ch.isdigit() for ch in clean_text):
                        raw_entities.append(
                            RawEntity(
                                text=clean_text,
                                label="PERSON",
                                start=ent.start_char,
                                end=ent.end_char,
                                confidence=0.88,
                                extractor="spacy_ner",
                            )
                        )
                elif label in ("GPE", "LOC"):
                    raw_entities.append(
                        RawEntity(
                            text=clean_text,
                            label="LOCATION",
                            start=ent.start_char,
                            end=ent.end_char,
                            confidence=0.85,
                            extractor="spacy_ner",
                        )
                    )
                elif label in ("DATE", "TIME"):
                    raw_entities.append(
                        RawEntity(
                            text=clean_text,
                            label="DATE",
                            start=ent.start_char,
                            end=ent.end_char,
                            confidence=0.85,
                            extractor="spacy_ner",
                        )
                    )
                elif label == "MONEY":
                    raw_entities.append(
                        RawEntity(
                            text=clean_text,
                            label="AMOUNT",
                            start=ent.start_char,
                            end=ent.end_char,
                            confidence=0.85,
                            extractor="spacy_ner",
                        )
                    )
                elif label == "ORG" and any(k.lower() in clean_text.lower() for k in ["bank", "corp", "finance", "rbi"]):
                    raw_entities.append(
                        RawEntity(
                            text=clean_text,
                            label="BANK",
                            start=ent.start_char,
                            end=ent.end_char,
                            confidence=0.90,
                            extractor="spacy_ner",
                        )
                    )

        # 2. Process Domain Phrase Matcher (High Priority Gazetteers)
        matches = self.matcher(doc)
        for match_id, start_token, end_token in matches:
            span = doc[start_token:end_token]
            match_label = self.nlp.vocab.strings[match_id]
            raw_entities.append(
                RawEntity(
                    text=span.text.strip(),
                    label=match_label,
                    start=span.start_char,
                    end=span.end_char,
                    confidence=0.96,
                    extractor="spacy_matcher",
                )
            )

        # 3. Process Complainant & Citizen Name Pattern Matching
        for match in self.COMPLAINANT_PREFIX_REGEX.finditer(text):
            name_val = match.group(1).strip()
            if name_val not in KNOWN_BANKS and name_val not in KNOWN_LOCATIONS:
                raw_entities.append(
                    RawEntity(
                        text=name_val,
                        label="PERSON",
                        start=match.start(1),
                        end=match.end(1),
                        confidence=0.95,
                        extractor="spacy_matcher",
                    )
                )

        return raw_entities
