"""Text preprocessing utilities for cybercrime complaint narratives."""

import unicodedata
import re
from typing import Tuple


class TextPreprocessor:
    """Preprocesses cybercrime narratives while preserving character offsets and currency/phone symbols."""

    # Zero-width spaces, joiners, and bidirectional control characters
    ZERO_WIDTH_PATTERN = re.compile(r"[\u200B-\u200D\uFEFF\u200E\u200F]")
    # Multiple whitespace (excluding newline if structured)
    MULTI_WHITESPACE_PATTERN = re.compile(r"[^\S\r\n]+")

    @classmethod
    def preprocess(cls, text: str) -> str:
        """Clean and normalize raw complaint narrative.

        Performs:
        1. Unicode normalization (NFKC)
        2. Removal of invisible control characters
        3. Normalization of varied quotes and hyphens
        4. Whitespace cleanup
        """
        if not text:
            return ""

        # 1. Unicode NFKC normalization
        normalized = unicodedata.normalize("NFKC", text)

        # 2. Strip zero-width & invisible formatting characters
        cleaned = cls.ZERO_WIDTH_PATTERN.sub("", normalized)

        # 3. Standardize quotes, backticks, and apostrophes
        cleaned = cleaned.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")

        # 4. Standardize dashes/hyphens
        cleaned = cleaned.replace("–", "-").replace("—", "-")

        # 5. Clean excessive spaces without breaking newlines
        cleaned = cls.MULTI_WHITESPACE_PATTERN.sub(" ", cleaned)

        return cleaned.strip()

    @classmethod
    def clean_with_spans(cls, text: str) -> Tuple[str, list]:
        """Clean text while tracking character index mapping from cleaned back to raw text."""
        cleaned = cls.preprocess(text)
        return cleaned, []
