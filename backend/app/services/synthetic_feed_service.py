"""Synthetic data feed and generator service for testing, demos, and SIH evaluation."""

import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.complaint import Complaint
from backend.app.models.transaction import BankAccount, Transaction

INDIAN_STATES = [
    "Maharashtra", "Delhi", "Karnataka", "Telangana", "Uttar Pradesh",
    "Tamil Nadu", "Gujarat", "Rajasthan", "West Bengal", "Haryana"
]

SCAM_CATEGORIES = [
    ("Financial Fraud", "UPI QR Code & Impersonation Scam"),
    ("Task / Job Fraud", "Telegram Part-Time Rating & Deposit Scam"),
    ("Malware & Phishing", "Fake Electricity Bill Update APK"),
    ("Loan App Extortion", "Unregistered Instant Loan Harassment"),
    ("Investment Fraud", "Fake Forex / Crypto High Yield Investment"),
    ("Sextortion", "WhatsApp Video Call Compromise & Blackmail"),
]

SYNTHETIC_BANKS = [
    ("SYNB000101", "State Bank of Synth", "Mumbai Nariman Point"),
    ("SYNB000202", "HDFC Synthetic Ltd", "Bengaluru Koramangala"),
    ("SYNB000303", "ICICI Synthetic Bank", "New Delhi Connaught Place"),
    ("SYNB000404", "Punjab Synth National Bank", "Chandigarh Sector 17"),
]


class SyntheticFeedService:
    """Generates strictly synthetic test data complying with non-disclosure & privacy constraints."""

    @staticmethod
    def generate_synthetic_complaint(index: int) -> Dict[str, Any]:
        random.seed(index + 100)
        cat, subcat = random.choice(SCAM_CATEGORIES)
        state = random.choice(INDIAN_STATES)
        loss = Decimal(random.randint(5, 450) * 1000)
        suspect_acc = f"SYN{random.randint(1000000000, 9999999999)}"
        suspect_vpa = f"suspect.{random.randint(100, 999)}@synthaxis"
        suspect_phone = f"+9198{random.randint(10000000, 99999999)}"
        
        now = datetime.now(timezone.utc)
        incident_time = now - timedelta(hours=random.randint(1, 72))

        risk_val = Decimal(str(round(random.uniform(0.35, 0.95), 4)))
        priority = "HIGH" if risk_val > Decimal("0.70") else ("MEDIUM" if risk_val > Decimal("0.50") else "LOW")

        return {
            "acknowledgement_no": f"NCRP-SYN-2024-{10000 + index}",
            "category": cat,
            "subcategory": subcat,
            "victim_state": state,
            "victim_district": f"{state} Metro Sector",
            "reported_loss_inr": loss,
            "suspect_upi": suspect_vpa,
            "suspect_account_number": suspect_acc,
            "suspect_ifsc": random.choice(SYNTHETIC_BANKS)[0],
            "suspect_phone": suspect_phone,
            "incident_timestamp": incident_time,
            "status": random.choice(["NEW", "UNDER_INVESTIGATION", "ESCALATED"]),
            "triage_priority": priority,
            "risk_score": risk_val,
            "description_synthetic": (
                f"Synthetic incident record #{index}: Complainant reports unauthorized {cat} "
                f"debit of ₹{loss:,.2f} diverted to suspect VPA {suspect_vpa}."
            ),
        }

    @staticmethod
    async def seed_initial_synthetic_data(db: AsyncSession, count: int = 25) -> int:
        """Seed the relational database with synthetic sample data for initial UI inspection."""
        from sqlalchemy import func, select
        result = await db.execute(select(func.count(Complaint.id)))
        existing_count = result.scalar_one()

        if existing_count >= count:
            return existing_count

        created = 0
        for i in range(count - existing_count):
            item_data = SyntheticFeedService.generate_synthetic_complaint(existing_count + i + 1)
            complaint = Complaint(**item_data)
            db.add(complaint)
            created += 1

        await db.flush()
        return created
