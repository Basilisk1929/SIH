"""Data Normalization Engine for incoming cyber intelligence and banking feeds."""

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional

PHONE_CLEAN_REGEX = re.compile(r"[^\d+]")


class DataNormalizer:
    """Standardizes disparate formats across banking feeds, 1930 logs, and CSV uploads."""

    @staticmethod
    def normalize_phone_number(raw_phone: Optional[str]) -> str:
        """Standardize Indian phone numbers into E.164 (+91XXXXXXXXXX) format."""
        if not raw_phone or str(raw_phone).strip() in ("N/A", "nan", "None", ""):
            return "N/A"

        cleaned = PHONE_CLEAN_REGEX.sub("", str(raw_phone).strip())

        # If starts with +91 and 10 digits
        if cleaned.startswith("+91") and len(cleaned) == 13:
            return cleaned
        # If starts with 91 and 10 digits
        if cleaned.startswith("91") and len(cleaned) == 12:
            return f"+{cleaned}"
        # If 10 digits starting with [6-9]
        if len(cleaned) == 10 and cleaned[0] in "6789":
            return f"+91{cleaned}"
        # If starts with 0 and 10 digits
        if cleaned.startswith("0") and len(cleaned) == 11 and cleaned[1] in "6789":
            return f"+91{cleaned[1:]}"

        return cleaned if cleaned.startswith("+") else f"+91{cleaned[-10:]}"

    @staticmethod
    def normalize_ifsc(raw_ifsc: Optional[str]) -> str:
        """Uppercase and trim Indian Financial System Code."""
        if not raw_ifsc or str(raw_ifsc).strip() in ("N/A", "nan", "None", ""):
            return "N/A"
        return str(raw_ifsc).strip().upper()

    @staticmethod
    def normalize_vpa(raw_vpa: Optional[str]) -> str:
        """Lowercase and trim Virtual Payment Address."""
        if not raw_vpa or str(raw_vpa).strip() in ("N/A", "nan", "None", ""):
            return "N/A"
        return str(raw_vpa).strip().lower()

    @staticmethod
    def normalize_account_number(raw_acc: Optional[str]) -> str:
        """Strip whitespace, hyphens, and uppercase account numbers."""
        if not raw_acc or str(raw_acc).strip() in ("N/A", "nan", "None", ""):
            return "N/A"
        return str(raw_acc).replace("-", "").replace(" ", "").strip().upper()

    @staticmethod
    def normalize_amount(raw_amount: Any) -> Decimal:
        """Convert float/int/str amounts into 2-decimal rounded Decimal."""
        if raw_amount is None:
            return Decimal("0.00")
        try:
            if isinstance(raw_amount, (int, float)):
                return round(Decimal(str(raw_amount)), 2)
            cleaned = str(raw_amount).replace(",", "").replace("₹", "").replace("$", "").strip()
            return round(Decimal(cleaned), 2)
        except (InvalidOperation, ValueError):
            return Decimal("0.00")

    @staticmethod
    def normalize_timestamp(raw_ts: Any) -> datetime:
        """Parse varied date/time inputs into UTC timezone-aware datetime."""
        if isinstance(raw_ts, datetime):
            return raw_ts if raw_ts.tzinfo else raw_ts.replace(tzinfo=timezone.utc)
        if not raw_ts or str(raw_ts).strip() in ("N/A", "nan", "None", ""):
            return datetime.now(timezone.utc)

        ts_str = str(raw_ts).strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(ts_str)
        except ValueError:
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S%z",
                "%Y-%m-%d",
                "%d-%m-%Y %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%d/%m/%Y",
            ):
                try:
                    dt = datetime.strptime(ts_str, fmt)
                    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        return datetime.now(timezone.utc)

    @classmethod
    def normalize_record(cls, raw: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """Apply targeted normalizations across record dictionary based on entity type."""
        normalized = dict(raw)

        # Common Envelope normalization
        if "event_timestamp" in normalized:
            normalized["event_timestamp"] = cls.normalize_timestamp(normalized["event_timestamp"])
        if "ingestion_timestamp" in normalized:
            normalized["ingestion_timestamp"] = cls.normalize_timestamp(normalized["ingestion_timestamp"])

        if entity_type == "transaction":
            if "sender_account_number" in normalized:
                normalized["sender_account_number"] = cls.normalize_account_number(normalized["sender_account_number"])
            if "receiver_account_number" in normalized:
                normalized["receiver_account_number"] = cls.normalize_account_number(normalized["receiver_account_number"])
            if "sender_upi_id" in normalized:
                normalized["sender_upi_id"] = cls.normalize_vpa(normalized["sender_upi_id"])
            if "receiver_upi_id" in normalized:
                normalized["receiver_upi_id"] = cls.normalize_vpa(normalized["receiver_upi_id"])
            if "amount" in normalized:
                normalized["amount"] = cls.normalize_amount(normalized["amount"])
            if "timestamp" in normalized:
                normalized["event_timestamp"] = cls.normalize_timestamp(normalized["timestamp"])

        elif entity_type == "account":
            if "account_number" in normalized:
                normalized["account_number"] = cls.normalize_account_number(normalized["account_number"])
            if "ifsc_code" in normalized:
                normalized["ifsc_code"] = cls.normalize_ifsc(normalized["ifsc_code"])
            if "current_balance" in normalized:
                normalized["current_balance"] = cls.normalize_amount(normalized["current_balance"])

        elif entity_type == "complaint":
            if "victim_account_number" in normalized:
                normalized["victim_account_number"] = cls.normalize_account_number(normalized["victim_account_number"])
            if "suspect_account_number" in normalized:
                normalized["suspect_account_number"] = cls.normalize_account_number(normalized["suspect_account_number"])
            if "suspect_upi_id" in normalized:
                normalized["suspect_upi_id"] = cls.normalize_vpa(normalized["suspect_upi_id"])
            if "suspect_phone_number" in normalized:
                normalized["suspect_phone_number"] = cls.normalize_phone_number(normalized["suspect_phone_number"])
            if "reported_loss_amount" in normalized:
                normalized["reported_loss_amount"] = cls.normalize_amount(normalized["reported_loss_amount"])
            if "incident_date" in normalized:
                normalized["incident_date"] = cls.normalize_timestamp(normalized["incident_date"])
            if "reported_date" in normalized:
                normalized["reported_date"] = cls.normalize_timestamp(normalized["reported_date"])

        elif entity_type == "atm":
            if "account_number" in normalized:
                normalized["account_number"] = cls.normalize_account_number(normalized["account_number"])
            if "amount" in normalized:
                normalized["amount"] = cls.normalize_amount(normalized["amount"])
            if "timestamp" in normalized:
                normalized["event_timestamp"] = cls.normalize_timestamp(normalized["timestamp"])

        return normalized
