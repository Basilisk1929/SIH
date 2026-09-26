"""Entity normalizer standardizing raw forensic spans into canonical formats."""

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Any, Dict, Optional
from nlp.extractors.regex_extractor import RawEntity


@dataclass
class NormalizedEntity:
    """Standardized entity with canonical value representation and linking slots."""
    text: str
    label: str  # PERSON, BANK, ACCOUNT, PHONE, UPI_ID, AMOUNT, LOCATION, DATE, TRANSACTION_ID, SCAM_TYPE
    start: int
    end: int
    normalized_value: Any
    confidence: float
    extractor: str
    linked_entity: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert normalized entity to serializable dictionary."""
        return {
            "text": self.text,
            "label": self.label,
            "start": self.start,
            "end": self.end,
            "normalized_value": self.normalized_value,
            "confidence": round(self.confidence, 2),
            "extractor": self.extractor,
            "linked_entity": self.linked_entity,
        }


class EntityNormalizer:
    """Normalizes heterogeneous raw text spans into standard forensic schema values."""

    # Person prefixes to strip
    PERSON_PREFIXES = re.compile(
        r"^(?:complainant|senior\s+citizen|citizen|victim|admin|handler|recruiter|officer|dcp|mr\.?|ms\.?|mrs\.?|shri)\s+",
        re.IGNORECASE,
    )

    # Bank alias dictionary
    BANK_ALIASES: Dict[str, str] = {
        "sbi": "State Bank of Synth",
        "state bank": "State Bank of Synth",
        "state bank of india": "State Bank of Synth",
        "state bank of synth": "State Bank of Synth",
        "hdfc": "Synth HDFC Commercial Bank",
        "hdfc bank": "Synth HDFC Commercial Bank",
        "synth hdfc": "Synth HDFC Commercial Bank",
        "synth hdfc commercial bank": "Synth HDFC Commercial Bank",
        "icici": "Synth ICICI Banking Corp",
        "icici bank": "Synth ICICI Banking Corp",
        "synth icici": "Synth ICICI Banking Corp",
        "synth icici banking corp": "Synth ICICI Banking Corp",
        "axis": "Synth Axis Finance Bank",
        "axis bank": "Synth Axis Finance Bank",
        "synth axis finance bank": "Synth Axis Finance Bank",
        "pnb": "Punjab & Synth National Bank",
        "punjab national bank": "Punjab & Synth National Bank",
        "punjab & synth national bank": "Punjab & Synth National Bank",
        "kotak": "Kotak Synth Mahindra Bank",
        "kotak synth mahindra bank": "Kotak Synth Mahindra Bank",
        "baroda": "Bank of Synth Baroda",
        "bank of baroda": "Bank of Synth Baroda",
        "bank of synth baroda": "Bank of Synth Baroda",
        "union bank": "Union Synth Bank of India",
        "union synth bank of india": "Union Synth Bank of India",
        "payments bank": "Synth Payments & Small Finance Bank",
        "synth payments & small finance bank": "Synth Payments & Small Finance Bank",
        "gramin vikas bank": "Jan-Synth Gramin Vikas Bank",
        "jan-synth gramin vikas bank": "Jan-Synth Gramin Vikas Bank",
        "rbi": "Reserve Bank of India",
        "reserve bank of india": "Reserve Bank of India",
    }

    @classmethod
    def normalize_phone(cls, raw: str) -> str:
        """Standardize Indian mobile phone numbers to E.164 (+91XXXXXXXXXX)."""
        digits = re.sub(r"\D", "", raw)
        if len(digits) == 10 and digits[0] in "6789":
            return f"+91{digits}"
        elif len(digits) == 11 and digits.startswith("0"):
            return f"+91{digits[1:]}"
        elif len(digits) == 12 and digits.startswith("91"):
            return f"+{digits}"
        return f"+91{digits[-10:]}" if len(digits) >= 10 else raw

    @classmethod
    def normalize_amount(cls, raw: str) -> float:
        """Standardize currency string into float amount in INR."""
        # Strip currency symbols and text first (e.g. Rs., INR, ₹)
        clean_str = re.sub(r"^(?:₹|Rs\.?|INR)\s*", "", raw.strip(), flags=re.IGNORECASE)
        clean_str = re.sub(r"\s*(?:INR|rupees|Rs\.?)$", "", clean_str, flags=re.IGNORECASE)
        cleaned = re.sub(r"[^\d.]", "", clean_str.replace(",", ""))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @classmethod
    def normalize_upi(cls, raw: str) -> str:
        """Standardize UPI handle to lowercase stripped format."""
        cleaned = raw.strip().rstrip(".,:;!?)")
        return cleaned.lower()

    @classmethod
    def normalize_account(cls, raw: str) -> str:
        """Standardize bank account identifier."""
        cleaned = re.sub(r"[\s\-]", "", raw)
        return cleaned.upper()

    @classmethod
    def normalize_bank(cls, raw: str) -> str:
        """Map bank name variations to canonical institution names."""
        clean = raw.strip().lower()
        for alias, canonical in cls.BANK_ALIASES.items():
            if alias in clean or clean in alias:
                return canonical
        return raw.strip().title()

    @classmethod
    def normalize_person(cls, raw: str) -> str:
        """Strip introductory labels and title-case person names."""
        stripped = cls.PERSON_PREFIXES.sub("", raw.strip())
        return stripped.strip().title()

    @classmethod
    def normalize_date(cls, raw: str) -> str:
        """Standardize date strings."""
        clean = raw.strip()
        # If DD/MM/YYYY or DD-MM-YYYY
        d_match = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", clean)
        if d_match:
            day, month, year = d_match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        return clean

    @classmethod
    def normalize(cls, raw_entity: RawEntity) -> NormalizedEntity:
        """Dispatch entity normalization according to label type."""
        lbl = raw_entity.label
        raw_text = raw_entity.text
        norm_val: Any = raw_text

        if lbl == "PHONE":
            norm_val = cls.normalize_phone(raw_text)
        elif lbl == "AMOUNT":
            norm_val = cls.normalize_amount(raw_text)
        elif lbl == "UPI_ID":
            norm_val = cls.normalize_upi(raw_text)
        elif lbl == "ACCOUNT":
            norm_val = cls.normalize_account(raw_text)
        elif lbl == "BANK":
            norm_val = cls.normalize_bank(raw_text)
        elif lbl == "PERSON":
            norm_val = cls.normalize_person(raw_text)
        elif lbl == "DATE":
            norm_val = cls.normalize_date(raw_text)
        elif lbl == "TRANSACTION_ID":
            norm_val = raw_text.strip().upper()
        elif lbl == "LOCATION":
            norm_val = raw_text.strip().title()
        elif lbl == "SCAM_TYPE":
            norm_val = raw_text.strip()

        return NormalizedEntity(
            text=raw_text,
            label=lbl,
            start=raw_entity.start,
            end=raw_entity.end,
            normalized_value=norm_val,
            confidence=raw_entity.confidence,
            extractor=raw_entity.extractor,
        )
