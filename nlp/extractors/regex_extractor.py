"""Regex-based structured entity extractor for high-fidelity cybercrime indicators."""

from dataclasses import dataclass
import re
from typing import List


@dataclass
class RawEntity:
    """Represents an extracted entity span before normalization and linking."""
    text: str
    label: str  # PERSON, BANK, ACCOUNT, PHONE, UPI_ID, AMOUNT, LOCATION, DATE, TRANSACTION_ID, SCAM_TYPE
    start: int
    end: int
    confidence: float = 1.0
    extractor: str = "regex"


class RegexStructuredExtractor:
    """High-precision regex extractor for Indian financial cybercrime narratives."""

    # 1. Indian Mobile Numbers (+91 9XXXXXXXXX, 09XXXXXXXXX, 9XXXXXXXXX)
    PHONE_REGEX = re.compile(
        r"(?:\+91[\-\s]?|91[\-\s]?|0)?[6-9]\d{9}\b"
    )

    # 2. UPI VPAs / Handles (user@bank, firstname.lastname.123@synoksbi)
    UPI_REGEX = re.compile(
        r"\b[a-zA-Z0-9][a-zA-Z0-9.\-_]{1,64}@[a-zA-Z0-9_\-]{2,32}\b",
        re.IGNORECASE,
    )

    # 3. Bank Account Numbers:
    # Explicit synthetic prefix (SYN + 10 digits) OR preceded by account context keywords
    ACCOUNT_SYN_REGEX = re.compile(r"\bSYN\d{10}\b")
    ACCOUNT_KEYWORD_REGEX = re.compile(
        r"\b(?:a/c|a/c:|account|beneficiary account|current account|savings account)\s*[:#\-]?\s*([0-9]{9,18})\b",
        re.IGNORECASE,
    )
    ACCOUNT_LONG_NUMERIC_REGEX = re.compile(r"\b\d{11,18}\b")

    # 4. Monetary Amounts (₹49,999.00, Rs. 25,000, 10000 INR, etc.)
    AMOUNT_SYMBOL_REGEX = re.compile(
        r"(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d{1,2})?",
        re.IGNORECASE,
    )
    AMOUNT_SUFFIX_REGEX = re.compile(
        r"\b[\d,]+(?:\.\d{1,2})?\s*(?:INR|rupees|Rs\.?)\b",
        re.IGNORECASE,
    )

    # 5. Transaction IDs (TXN_00038001, UTR123456789012, RRN123456789012)
    TRANSACTION_ID_REGEX = re.compile(
        r"\b(?:TXN_\d{8}|UTR\d{12}|RRN\d{12})\b",
        re.IGNORECASE,
    )
    TRANSACTION_PREFIX_REGEX = re.compile(
        r"\b(?:UTR|RRN|Txn ID|Transaction ID|Ref No|Reference No)\s*[:#\-]?\s*([A-Za-z0-9]{8,24})\b",
        re.IGNORECASE,
    )

    # 6. Dates & Timestamps
    DATE_ISO_REGEX = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\+\d{2}:\d{2})?)?\b")
    DATE_INDIAN_REGEX = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")
    TIME_REGEX = re.compile(r"\b\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)\b")

    @classmethod
    def extract_structured_entities(cls, text: str) -> List[RawEntity]:
        """Extract high-confidence structured entities via regular expressions."""
        if not text:
            return []

        entities: List[RawEntity] = []

        # 1. Extract UPI IDs
        for match in cls.UPI_REGEX.finditer(text):
            val = match.group().strip()
            # Exclude common email domains if they are not UPI VPAs
            if not val.lower().endswith((".com", ".org", ".net", ".edu", ".gov")):
                entities.append(
                    RawEntity(
                        text=val,
                        label="UPI_ID",
                        start=match.start(),
                        end=match.end(),
                        confidence=0.98,
                        extractor="regex",
                    )
                )

        # 2. Extract Phone Numbers
        for match in cls.PHONE_REGEX.finditer(text):
            val = match.group().strip()
            entities.append(
                RawEntity(
                    text=val,
                    label="PHONE",
                    start=match.start(),
                    end=match.end(),
                    confidence=0.95,
                    extractor="regex",
                )
            )

        # 3. Extract Bank Accounts
        for match in cls.ACCOUNT_SYN_REGEX.finditer(text):
            val = match.group().strip()
            entities.append(
                RawEntity(
                    text=val,
                    label="ACCOUNT",
                    start=match.start(),
                    end=match.end(),
                    confidence=0.99,
                    extractor="regex",
                )
            )

        for match in cls.ACCOUNT_KEYWORD_REGEX.finditer(text):
            val = match.group(1).strip()
            entities.append(
                RawEntity(
                    text=val,
                    label="ACCOUNT",
                    start=match.start(1),
                    end=match.end(1),
                    confidence=0.92,
                    extractor="regex",
                )
            )

        for match in cls.ACCOUNT_LONG_NUMERIC_REGEX.finditer(text):
            val = match.group().strip()
            entities.append(
                RawEntity(
                    text=val,
                    label="ACCOUNT",
                    start=match.start(),
                    end=match.end(),
                    confidence=0.88,
                    extractor="regex",
                )
            )

        # 4. Extract Amounts
        for match in cls.AMOUNT_SYMBOL_REGEX.finditer(text):
            val = match.group().strip()
            entities.append(
                RawEntity(
                    text=val,
                    label="AMOUNT",
                    start=match.start(),
                    end=match.end(),
                    confidence=0.96,
                    extractor="regex",
                )
            )

        for match in cls.AMOUNT_SUFFIX_REGEX.finditer(text):
            val = match.group().strip()
            entities.append(
                RawEntity(
                    text=val,
                    label="AMOUNT",
                    start=match.start(),
                    end=match.end(),
                    confidence=0.94,
                    extractor="regex",
                )
            )

        # 5. Extract Transaction IDs
        for match in cls.TRANSACTION_ID_REGEX.finditer(text):
            val = match.group().strip()
            entities.append(
                RawEntity(
                    text=val,
                    label="TRANSACTION_ID",
                    start=match.start(),
                    end=match.end(),
                    confidence=0.98,
                    extractor="regex",
                )
            )

        for match in cls.TRANSACTION_PREFIX_REGEX.finditer(text):
            val = match.group(1).strip()
            entities.append(
                RawEntity(
                    text=val,
                    label="TRANSACTION_ID",
                    start=match.start(1),
                    end=match.end(1),
                    confidence=0.91,
                    extractor="regex",
                )
            )

        # 6. Extract Dates & Times
        for match in cls.DATE_ISO_REGEX.finditer(text):
            val = match.group().strip()
            entities.append(
                RawEntity(
                    text=val,
                    label="DATE",
                    start=match.start(),
                    end=match.end(),
                    confidence=0.96,
                    extractor="regex",
                )
            )

        for match in cls.DATE_INDIAN_REGEX.finditer(text):
            val = match.group().strip()
            entities.append(
                RawEntity(
                    text=val,
                    label="DATE",
                    start=match.start(),
                    end=match.end(),
                    confidence=0.92,
                    extractor="regex",
                )
            )

        for match in cls.TIME_REGEX.finditer(text):
            val = match.group().strip()
            entities.append(
                RawEntity(
                    text=val,
                    label="DATE",
                    start=match.start(),
                    end=match.end(),
                    confidence=0.85,
                    extractor="regex",
                )
            )

        return entities
