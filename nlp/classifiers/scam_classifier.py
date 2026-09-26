"""NLP classifier categorizing unstructured cyber incident reports into fraud typologies."""

from typing import Dict, Tuple


class ScamCategoryClassifier:
    """Keyword and semantic pattern classifier for cybercrime reports."""

    CATEGORY_KEYWORDS = {
        "Financial Fraud - UPI/QR": [
            "upi", "qr code", "scan to receive", "gpay", "phonepe", "paytm", "pin", "reverse debit"
        ],
        "Part-Time Job / Task Scam": [
            "telegram", "hotel review", "youtube like", "daily salary", "crypto deposit", "task investment"
        ],
        "Phishing & Malware": [
            "electricity bill", "power disconnect", "apk", "officer call", "update pan", "sim block"
        ],
        "Illegal Loan Extortion": [
            "instant loan", "contacts accessed", "morphed photo", "recovery agent", "harassment", "7 days"
        ],
        "Sextortion": [
            "video call", "nude", "recording", "blackmail", "youtube upload", "police impersonation"
        ],
    }

    @classmethod
    def classify_narrative(cls, text: str) -> Tuple[str, float]:
        """Classify report narrative into top scam category with confidence score."""
        if not text:
            return "General Cyber Fraud", 0.30

        lower_text = text.lower()
        scores: Dict[str, int] = {}

        for category, keywords in cls.CATEGORY_KEYWORDS.items():
            match_count = sum(1 for kw in keywords if kw in lower_text)
            if match_count > 0:
                scores[category] = match_count

        if not scores:
            return "General Cyber Fraud", 0.40

        top_category = max(scores, key=scores.get)
        confidence = min(0.95, 0.45 + (scores[top_category] * 0.15))
        return top_category, round(confidence, 2)
