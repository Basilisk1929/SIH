"""Synthetic data generation engine for SIH Prototype.

Generates realistic Indian banking, UPI, and NCRP/1930 cybercrime complaints
without using any real-world personally identifiable information (PII).
"""

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

INDIAN_STATES = [
    "Maharashtra", "Delhi", "Karnataka", "Telangana", "Uttar Pradesh",
    "Tamil Nadu", "Gujarat", "Rajasthan", "West Bengal", "Haryana"
]

SCAM_MODUS_OPERANDI = [
    {
        "category": "Financial Fraud",
        "subcategory": "UPI QR Code Impersonation",
        "narratives": [
            "Complainant was deceived while selling a second-hand item online. Suspect sent QR code stating 'Scan to receive money'. Upon scanning, ₹{amount} was debited.",
            "Victim received a call purporting to be customer support for an e-wallet. Asked to enter UPI PIN on link, resulting in unauthorized deduction of ₹{amount}.",
        ],
    },
    {
        "category": "Task / Job Scam",
        "subcategory": "Telegram Review & Rating Fraud",
        "narratives": [
            "Victim was added to a Telegram group offering ₹500/day for liking videos. After initial payouts, victim was coerced to invest ₹{amount} in high-yield crypto task.",
            "Received WhatsApp message regarding part-time Google Maps hotel review job. Promised 30% return, lost ₹{amount} across 3 transfers.",
        ],
    },
    {
        "category": "Malware & Phishing",
        "subcategory": "Fake Electricity Bill APK",
        "narratives": [
            "Received SMS: 'Dear consumer, your electricity power will be disconnected tonight at 9:30 PM. Call officer or download MahaBijli.apk'. Debited ₹{amount}.",
        ],
    },
]

SYNTHETIC_IFSC_CODES = [
    ("SYNB0001001", "State Bank of Synth", "Mumbai Fort"),
    ("SYNB0002002", "HDFC Synthetic Bank", "Bengaluru Whitefield"),
    ("SYNB0003003", "ICICI Synthetic Bank", "Delhi Connaught Place"),
    ("SYNB0004004", "Punjab Synthetic Bank", "Chandigarh Sector 22"),
]


def generate_synthetic_dataset(num_complaints: int = 50, seed: int = 42) -> Dict[str, List[Dict[str, Any]]]:
    """Generate coupled synthetic complaints and mule transaction records."""
    random.seed(seed)
    complaints = []
    transactions = []

    base_time = datetime.now(timezone.utc) - timedelta(days=7)

    for i in range(num_complaints):
        scam = random.choice(SCAM_MODUS_OPERANDI)
        amount = float(random.randint(5, 120) * 1000)
        state = random.choice(INDIAN_STATES)
        ack_no = f"NCRP-SYN-2024-{10000 + i}"
        
        narrative_template = random.choice(scam["narratives"])
        description = narrative_template.format(amount=f"{amount:,.2f}")

        suspect_vpa = f"mule.{random.randint(100, 999)}@synthaxis"
        suspect_acc = f"SYN{random.randint(1000000000, 9999999999)}"
        suspect_phone = f"+9198{random.randint(10000000, 99999999)}"
        ifsc, bank, branch = random.choice(SYNTHETIC_IFSC_CODES)

        incident_time = base_time + timedelta(hours=i * 2 + random.randint(1, 4))

        complaint = {
            "acknowledgement_no": ack_no,
            "category": scam["category"],
            "subcategory": scam["subcategory"],
            "victim_state": state,
            "victim_district": f"{state} Central",
            "reported_loss_inr": amount,
            "suspect_upi": suspect_vpa,
            "suspect_account_number": suspect_acc,
            "suspect_ifsc": ifsc,
            "suspect_phone": suspect_phone,
            "incident_timestamp": incident_time.isoformat(),
            "status": "NEW" if i > 30 else ("UNDER_INVESTIGATION" if i > 10 else "FROZEN"),
            "risk_score": round(random.uniform(0.40, 0.95), 4),
            "description_synthetic": description,
        }
        complaints.append(complaint)

        # Coupled Layer-1 Transaction (Victim -> Layer 1 Mule)
        txn_1_time = incident_time
        tx1 = {
            "txn_ref_no": f"UPI/4289{10000 + i}/SYN",
            "sender_account": f"VIC{random.randint(10000000, 99999999)}",
            "receiver_account": suspect_acc,
            "sender_upi": f"victim_{i}@synthbank",
            "receiver_upi": suspect_vpa,
            "amount_inr": amount,
            "rail_type": "UPI",
            "timestamp": txn_1_time.isoformat(),
            "layer_depth": 1,
            "is_flagged_suspicious": True,
            "anomaly_score": 0.85,
        }
        transactions.append(tx1)

        # Coupled Layer-2 Transaction (Layer 1 Mule -> Layer 2 Distributing Mule, rapid drain within 5 mins)
        layer2_amount = round(amount * 0.96, 2)
        txn_2_time = txn_1_time + timedelta(minutes=random.randint(2, 6))
        layer2_acc = f"MULE_L2_{random.randint(100, 999)}"
        tx2 = {
            "txn_ref_no": f"IMPS/4289{20000 + i}/SYN",
            "sender_account": suspect_acc,
            "receiver_account": layer2_acc,
            "sender_upi": suspect_vpa,
            "receiver_upi": f"distributor_{i}@synthaxis",
            "amount_inr": layer2_amount,
            "rail_type": "IMPS",
            "timestamp": txn_2_time.isoformat(),
            "layer_depth": 2,
            "is_flagged_suspicious": True,
            "anomaly_score": 0.92,
        }
        transactions.append(tx2)

    return {"complaints": complaints, "transactions": transactions}


def main():
    """CLI generator utility writing sample synthetic JSON data."""
    output_dir = Path(__file__).resolve().parent.parent / "synthetic"
    output_dir.mkdir(parents=True, exist_ok=True)

    data = generate_synthetic_dataset(num_complaints=50)

    complaints_file = output_dir / "sample_complaints.json"
    with open(complaints_file, "w", encoding="utf-8") as f:
        json.dump(data["complaints"], f, indent=2)

    transactions_file = output_dir / "sample_transactions.json"
    with open(transactions_file, "w", encoding="utf-8") as f:
        json.dump(data["transactions"], f, indent=2)

    print(f"Generated {len(data['complaints'])} synthetic complaints in {complaints_file}")
    print(f"Generated {len(data['transactions'])} synthetic transactions in {transactions_file}")


if __name__ == "__main__":
    main()
