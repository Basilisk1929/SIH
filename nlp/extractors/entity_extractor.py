"""Natural Language Processing entity extractor for Indian cybercrime narratives.

Extracts suspect identifiers:
- UPI VPAs (e.g. suspect@oksbi, mule99@paytm)
- Indian Mobile Numbers (+91 9XXXX XXXXX, 09XXXX XXXXX)
- Indian Bank Account Numbers (9 to 18 digits)
- IFSC Codes (e.g. SBIN0001234, HDFC0000240)
- Fraudulent APK filenames (e.g. BijliUpdate.apk, LoanEasy.apk)
"""

import re
from typing import Dict, List, Set


class CybercrimeEntityExtractor:
    """Extracts forensic entities from citizen incident descriptions."""

    # Regex patterns tailored to Indian cybercrime indicators
    VPA_PATTERN = re.compile(r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b", re.IGNORECASE)
    PHONE_PATTERN = re.compile(r"(?:\+91[\-\s]?|91[\-\s]?|0)?[6-9]\d{9}\b")
    IFSC_PATTERN = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")
    ACCOUNT_PATTERN = re.compile(r"\b\d{9,18}\b")
    APK_PATTERN = re.compile(r"\b[a-zA-Z0-9_\-]+\.apk\b", re.IGNORECASE)

    @classmethod
    def extract_entities(cls, text: str) -> Dict[str, List[str]]:
        """Extract all potential suspect identifiers from unstructured complaint narrative."""
        if not text:
            return {
                "upi_ids": [],
                "phone_numbers": [],
                "ifsc_codes": [],
                "account_candidates": [],
                "apk_files": [],
            }

        vpas = list(set(cls.VPA_PATTERN.findall(text)))
        phones = list(set(cls.PHONE_PATTERN.findall(text)))
        ifscs = list(set(cls.IFSC_PATTERN.findall(text)))
        accounts = list(set(cls.ACCOUNT_PATTERN.findall(text)))
        apks = list(set(cls.APK_PATTERN.findall(text)))

        # Filter out accounts that match phone numbers
        cleaned_accounts = [acc for acc in accounts if not any(acc in p for p in phones)]

        return {
            "upi_ids": vpas,
            "phone_numbers": phones,
            "ifsc_codes": ifscs,
            "account_candidates": cleaned_accounts,
            "apk_files": apks,
        }
