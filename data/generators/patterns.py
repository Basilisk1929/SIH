"""Suspicious behavioral patterns generator for financial cybercrime fraud detection.

Implements 8 core typologies:
1. Rapid transaction velocity
2. Mule account chains (multi-hop Layer 1 -> Layer 2 -> Layer 3)
3. Many-to-one transfers (fan-in funnel accounts)
4. One-to-many transfers (fan-out smurfing)
5. Rapid cash-out (immediate ATM withdrawal post-credit)
6. Unusual transaction amounts (micro-testing + drain)
7. Repeated transactions (burst identical transfers)
8. Geographic anomalies (impossible travel / cybercrime hotspot destination)
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple


class FraudPatternGenerator:
    """Generates synthetic suspicious patterns with ground-truth behavioral labels."""

    @staticmethod
    def generate_rapid_velocity(
        cluster_id: str,
        victim_acc: Dict[str, Any],
        l1_mule_acc: Dict[str, Any],
        l2_mule_acc: Dict[str, Any],
        base_time: datetime,
        amount: float,
        txn_counter: int,
    ) -> List[Dict[str, Any]]:
        """Pattern 1: Rapid transaction velocity (funds drained within 45 to 180 seconds)."""
        txns = []

        # Hop 1: Victim -> L1 Mule (Initial Fraud Transfer)
        t1_time = base_time
        tx1 = {
            "transaction_id": f"TXN_{txn_counter:08d}",
            "sender_account_number": victim_acc["account_number"],
            "receiver_account_number": l1_mule_acc["account_number"],
            "sender_upi_id": victim_acc.get("primary_upi_id", "N/A"),
            "receiver_upi_id": l1_mule_acc.get("primary_upi_id", "N/A"),
            "sender_device_id": victim_acc.get("primary_device_id", "N/A"),
            "receiver_device_id": l1_mule_acc.get("primary_device_id", "N/A"),
            "sender_location_id": victim_acc["location_id"],
            "receiver_location_id": l1_mule_acc["location_id"],
            "transaction_type": "TRANSFER",
            "payment_channel": "UPI",
            "amount": amount,
            "timestamp": t1_time.isoformat(),
            "is_fraud": True,
            "pattern_type": "RAPID_VELOCITY",
            "cluster_id": cluster_id,
        }
        txns.append(tx1)

        # Hop 2: L1 Mule -> L2 Mule (Drained in 60-120 seconds, keeping ~4% cut)
        t2_time = t1_time + timedelta(seconds=random.randint(45, 130))
        l2_amount = round(amount * random.uniform(0.94, 0.97), 2)
        tx2 = {
            "transaction_id": f"TXN_{(txn_counter + 1):08d}",
            "sender_account_number": l1_mule_acc["account_number"],
            "receiver_account_number": l2_mule_acc["account_number"],
            "sender_upi_id": l1_mule_acc.get("primary_upi_id", "N/A"),
            "receiver_upi_id": l2_mule_acc.get("primary_upi_id", "N/A"),
            "sender_device_id": l1_mule_acc.get("primary_device_id", "N/A"),
            "receiver_device_id": l2_mule_acc.get("primary_device_id", "N/A"),
            "sender_location_id": l1_mule_acc["location_id"],
            "receiver_location_id": l2_mule_acc["location_id"],
            "transaction_type": "TRANSFER",
            "payment_channel": "IMPS",
            "amount": l2_amount,
            "timestamp": t2_time.isoformat(),
            "is_fraud": True,
            "pattern_type": "RAPID_VELOCITY",
            "cluster_id": cluster_id,
        }
        txns.append(tx2)
        return txns

    @staticmethod
    def generate_mule_chain(
        cluster_id: str,
        victim_acc: Dict[str, Any],
        l1_mule_acc: Dict[str, Any],
        l2_mule_acc: Dict[str, Any],
        l3_mule_acc: Dict[str, Any],
        base_time: datetime,
        amount: float,
        txn_counter: int,
    ) -> List[Dict[str, Any]]:
        """Pattern 2: Multi-hop mule account chain (Layer 1 -> Layer 2 -> Layer 3)."""
        txns = []

        # Hop 1: Victim -> Layer 1 Primary Receiver
        t1 = base_time
        tx1 = {
            "transaction_id": f"TXN_{txn_counter:08d}",
            "sender_account_number": victim_acc["account_number"],
            "receiver_account_number": l1_mule_acc["account_number"],
            "sender_upi_id": victim_acc.get("primary_upi_id", "N/A"),
            "receiver_upi_id": l1_mule_acc.get("primary_upi_id", "N/A"),
            "sender_device_id": victim_acc.get("primary_device_id", "N/A"),
            "receiver_device_id": l1_mule_acc.get("primary_device_id", "N/A"),
            "sender_location_id": victim_acc["location_id"],
            "receiver_location_id": l1_mule_acc["location_id"],
            "transaction_type": "TRANSFER",
            "payment_channel": "UPI",
            "amount": amount,
            "timestamp": t1.isoformat(),
            "is_fraud": True,
            "pattern_type": "MULE_CHAIN_HOP1",
            "cluster_id": cluster_id,
        }
        txns.append(tx1)

        # Hop 2: Layer 1 -> Layer 2 Distributor (3-5 minutes later)
        t2 = t1 + timedelta(minutes=random.randint(2, 5))
        hop2_amount = round(amount * 0.95, 2)
        tx2 = {
            "transaction_id": f"TXN_{(txn_counter + 1):08d}",
            "sender_account_number": l1_mule_acc["account_number"],
            "receiver_account_number": l2_mule_acc["account_number"],
            "sender_upi_id": l1_mule_acc.get("primary_upi_id", "N/A"),
            "receiver_upi_id": l2_mule_acc.get("primary_upi_id", "N/A"),
            "sender_device_id": l1_mule_acc.get("primary_device_id", "N/A"),
            "receiver_device_id": l2_mule_acc.get("primary_device_id", "N/A"),
            "sender_location_id": l1_mule_acc["location_id"],
            "receiver_location_id": l2_mule_acc["location_id"],
            "transaction_type": "TRANSFER",
            "payment_channel": "IMPS",
            "amount": hop2_amount,
            "timestamp": t2.isoformat(),
            "is_fraud": True,
            "pattern_type": "MULE_CHAIN_HOP2",
            "cluster_id": cluster_id,
        }
        txns.append(tx2)

        # Hop 3: Layer 2 -> Layer 3 Cashout Consolidator (5-10 minutes later)
        t3 = t2 + timedelta(minutes=random.randint(4, 9))
        hop3_amount = round(hop2_amount * 0.95, 2)
        tx3 = {
            "transaction_id": f"TXN_{(txn_counter + 2):08d}",
            "sender_account_number": l2_mule_acc["account_number"],
            "receiver_account_number": l3_mule_acc["account_number"],
            "sender_upi_id": l2_mule_acc.get("primary_upi_id", "N/A"),
            "receiver_upi_id": l3_mule_acc.get("primary_upi_id", "N/A"),
            "sender_device_id": l2_mule_acc.get("primary_device_id", "N/A"),
            "receiver_device_id": l3_mule_acc.get("primary_device_id", "N/A"),
            "sender_location_id": l2_mule_acc["location_id"],
            "receiver_location_id": l3_mule_acc["location_id"],
            "transaction_type": "TRANSFER",
            "payment_channel": "NEFT",
            "amount": hop3_amount,
            "timestamp": t3.isoformat(),
            "is_fraud": True,
            "pattern_type": "MULE_CHAIN_HOP3",
            "cluster_id": cluster_id,
        }
        txns.append(tx3)

        return txns

    @staticmethod
    def generate_many_to_one_funnel(
        cluster_id: str,
        victim_accounts: List[Dict[str, Any]],
        funnel_account: Dict[str, Any],
        base_time: datetime,
        start_counter: int,
    ) -> List[Dict[str, Any]]:
        """Pattern 3: Many-to-One transfers (fan-in / funnel aggregator account)."""
        txns = []
        for i, vic in enumerate(victim_accounts):
            time_offset = timedelta(minutes=i * random.randint(3, 12))
            amt = round(random.uniform(5000, 45000), 2)
            tx = {
                "transaction_id": f"TXN_{(start_counter + i):08d}",
                "sender_account_number": vic["account_number"],
                "receiver_account_number": funnel_account["account_number"],
                "sender_upi_id": vic.get("primary_upi_id", "N/A"),
                "receiver_upi_id": funnel_account.get("primary_upi_id", "N/A"),
                "sender_device_id": vic.get("primary_device_id", "N/A"),
                "receiver_device_id": funnel_account.get("primary_device_id", "N/A"),
                "sender_location_id": vic["location_id"],
                "receiver_location_id": funnel_account["location_id"],
                "transaction_type": "TRANSFER",
                "payment_channel": "UPI",
                "amount": amt,
                "timestamp": (base_time + time_offset).isoformat(),
                "is_fraud": True,
                "pattern_type": "MANY_TO_ONE_FAN_IN",
                "cluster_id": cluster_id,
            }
            txns.append(tx)
        return txns

    @staticmethod
    def generate_one_to_many_smurfing(
        cluster_id: str,
        sender_account: Dict[str, Any],
        sub_mule_accounts: List[Dict[str, Any]],
        base_time: datetime,
        start_counter: int,
    ) -> List[Dict[str, Any]]:
        """Pattern 4: One-to-Many transfers (fan-out / smurfing below threshold)."""
        txns = []
        for i, sub_mule in enumerate(sub_mule_accounts):
            time_offset = timedelta(seconds=i * random.randint(15, 60))
            # Structured just below round alert threshold (e.g. ₹9,900 or ₹4,850)
            amt = round(random.choice([4950.0, 9850.0, 9900.0, 14900.0, 19800.0]), 2)
            tx = {
                "transaction_id": f"TXN_{(start_counter + i):08d}",
                "sender_account_number": sender_account["account_number"],
                "receiver_account_number": sub_mule["account_number"],
                "sender_upi_id": sender_account.get("primary_upi_id", "N/A"),
                "receiver_upi_id": sub_mule.get("primary_upi_id", "N/A"),
                "sender_device_id": sender_account.get("primary_device_id", "N/A"),
                "receiver_device_id": sub_mule.get("primary_device_id", "N/A"),
                "sender_location_id": sender_account["location_id"],
                "receiver_location_id": sub_mule["location_id"],
                "transaction_type": "TRANSFER",
                "payment_channel": "IMPS",
                "amount": amt,
                "timestamp": (base_time + time_offset).isoformat(),
                "is_fraud": True,
                "pattern_type": "ONE_TO_MANY_FAN_OUT",
                "cluster_id": cluster_id,
            }
            txns.append(tx)
        return txns

    @staticmethod
    def generate_rapid_cashout(
        cluster_id: str,
        victim_acc: Dict[str, Any],
        mule_acc: Dict[str, Any],
        atm_location_id: str,
        base_time: datetime,
        amount: float,
        txn_counter: int,
        atm_counter: int,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Pattern 5: Rapid cash-out (immediate ATM drain within 2-10 minutes of credit)."""
        txns = []
        atms = []

        # Step 1: Inflow into mule account
        t1 = base_time
        tx_in = {
            "transaction_id": f"TXN_{txn_counter:08d}",
            "sender_account_number": victim_acc["account_number"],
            "receiver_account_number": mule_acc["account_number"],
            "sender_upi_id": victim_acc.get("primary_upi_id", "N/A"),
            "receiver_upi_id": mule_acc.get("primary_upi_id", "N/A"),
            "sender_device_id": victim_acc.get("primary_device_id", "N/A"),
            "receiver_device_id": mule_acc.get("primary_device_id", "N/A"),
            "sender_location_id": victim_acc["location_id"],
            "receiver_location_id": mule_acc["location_id"],
            "transaction_type": "TRANSFER",
            "payment_channel": "UPI",
            "amount": amount,
            "timestamp": t1.isoformat(),
            "is_fraud": True,
            "pattern_type": "RAPID_CASHOUT",
            "cluster_id": cluster_id,
        }
        txns.append(tx_in)

        # Step 2: ATM Cash-out in 1 or 2 quick withdrawals
        withdrawal_time = t1 + timedelta(minutes=random.randint(2, 8))
        cashout_tx_id = f"TXN_{(txn_counter + 1):08d}"
        atm_amt = min(amount, 40000.0)

        tx_out = {
            "transaction_id": cashout_tx_id,
            "sender_account_number": mule_acc["account_number"],
            "receiver_account_number": "N/A",  # Cash withdrawal
            "sender_upi_id": "N/A",
            "receiver_upi_id": "N/A",
            "sender_device_id": "N/A",
            "receiver_device_id": "N/A",
            "sender_location_id": atm_location_id,
            "receiver_location_id": atm_location_id,
            "transaction_type": "CASH_OUT",
            "payment_channel": "ATM",
            "amount": atm_amt,
            "timestamp": withdrawal_time.isoformat(),
            "is_fraud": True,
            "pattern_type": "RAPID_CASHOUT",
            "cluster_id": cluster_id,
        }
        txns.append(tx_out)

        atm_entry = {
            "atm_interaction_id": f"ATM_{atm_counter:07d}",
            "account_number": mule_acc["account_number"],
            "atm_id": f"ATM_SYN_{random.randint(1000, 9999)}",
            "location_id": atm_location_id,
            "timestamp": withdrawal_time.isoformat(),
            "amount": atm_amt,
            "status": "SUCCESS",
            "rapid_cashout_flag": True,
            "associated_transaction_id": cashout_tx_id,
        }
        atms.append(atm_entry)

        return txns, atms

    @staticmethod
    def generate_unusual_amount_testing(
        cluster_id: str,
        victim_acc: Dict[str, Any],
        mule_acc: Dict[str, Any],
        base_time: datetime,
        drain_amount: float,
        txn_counter: int,
    ) -> List[Dict[str, Any]]:
        """Pattern 6: Micro-amount testing (₹1 or ₹5 test probe) followed by large drain."""
        txns = []

        # Micro-test probe
        test_time = base_time
        test_amt = float(random.choice([1.0, 5.0, 10.0]))
        tx_test = {
            "transaction_id": f"TXN_{txn_counter:08d}",
            "sender_account_number": victim_acc["account_number"],
            "receiver_account_number": mule_acc["account_number"],
            "sender_upi_id": victim_acc.get("primary_upi_id", "N/A"),
            "receiver_upi_id": mule_acc.get("primary_upi_id", "N/A"),
            "sender_device_id": victim_acc.get("primary_device_id", "N/A"),
            "receiver_device_id": mule_acc.get("primary_device_id", "N/A"),
            "sender_location_id": victim_acc["location_id"],
            "receiver_location_id": mule_acc["location_id"],
            "transaction_type": "TRANSFER",
            "payment_channel": "UPI",
            "amount": test_amt,
            "timestamp": test_time.isoformat(),
            "is_fraud": True,
            "pattern_type": "UNUSUAL_AMOUNT_TESTING",
            "cluster_id": cluster_id,
        }
        txns.append(tx_test)

        # Huge drain transfer 30-90 seconds later
        drain_time = test_time + timedelta(seconds=random.randint(30, 90))
        tx_drain = {
            "transaction_id": f"TXN_{(txn_counter + 1):08d}",
            "sender_account_number": victim_acc["account_number"],
            "receiver_account_number": mule_acc["account_number"],
            "sender_upi_id": victim_acc.get("primary_upi_id", "N/A"),
            "receiver_upi_id": mule_acc.get("primary_upi_id", "N/A"),
            "sender_device_id": victim_acc.get("primary_device_id", "N/A"),
            "receiver_device_id": mule_acc.get("primary_device_id", "N/A"),
            "sender_location_id": victim_acc["location_id"],
            "receiver_location_id": mule_acc["location_id"],
            "transaction_type": "TRANSFER",
            "payment_channel": "UPI",
            "amount": drain_amount,
            "timestamp": drain_time.isoformat(),
            "is_fraud": True,
            "pattern_type": "UNUSUAL_AMOUNT_TESTING",
            "cluster_id": cluster_id,
        }
        txns.append(tx_drain)
        return txns

    @staticmethod
    def generate_repeated_burst(
        cluster_id: str,
        victim_acc: Dict[str, Any],
        mule_acc: Dict[str, Any],
        base_time: datetime,
        chunk_amount: float,
        repetitions: int,
        start_counter: int,
    ) -> List[Dict[str, Any]]:
        """Pattern 7: Repeated identical transactions (burst transfers to bypass single-txn limits)."""
        txns = []
        for i in range(repetitions):
            t_time = base_time + timedelta(seconds=i * random.randint(20, 50))
            tx = {
                "transaction_id": f"TXN_{(start_counter + i):08d}",
                "sender_account_number": victim_acc["account_number"],
                "receiver_account_number": mule_acc["account_number"],
                "sender_upi_id": victim_acc.get("primary_upi_id", "N/A"),
                "receiver_upi_id": mule_acc.get("primary_upi_id", "N/A"),
                "sender_device_id": victim_acc.get("primary_device_id", "N/A"),
                "receiver_device_id": mule_acc.get("primary_device_id", "N/A"),
                "sender_location_id": victim_acc["location_id"],
                "receiver_location_id": mule_acc["location_id"],
                "transaction_type": "TRANSFER",
                "payment_channel": "UPI",
                "amount": chunk_amount,
                "timestamp": t_time.isoformat(),
                "is_fraud": True,
                "pattern_type": "REPEATED_BURST",
                "cluster_id": cluster_id,
            }
            txns.append(tx)
        return txns

    @staticmethod
    def generate_geographic_anomaly(
        cluster_id: str,
        victim_acc: Dict[str, Any],
        mule_acc: Dict[str, Any],
        hotspot_location_id: str,
        base_time: datetime,
        amount: float,
        txn_counter: int,
    ) -> List[Dict[str, Any]]:
        """Pattern 8: Geographic anomaly (victim in southern/western state, funds collected in known cyber hotzone)."""
        t1 = base_time
        tx = {
            "transaction_id": f"TXN_{txn_counter:08d}",
            "sender_account_number": victim_acc["account_number"],
            "receiver_account_number": mule_acc["account_number"],
            "sender_upi_id": victim_acc.get("primary_upi_id", "N/A"),
            "receiver_upi_id": mule_acc.get("primary_upi_id", "N/A"),
            "sender_device_id": victim_acc.get("primary_device_id", "N/A"),
            "receiver_device_id": mule_acc.get("primary_device_id", "N/A"),
            "sender_location_id": victim_acc["location_id"],
            "receiver_location_id": hotspot_location_id,
            "transaction_type": "TRANSFER",
            "payment_channel": "UPI",
            "amount": amount,
            "timestamp": t1.isoformat(),
            "is_fraud": True,
            "pattern_type": "GEOGRAPHIC_ANOMALY",
            "cluster_id": cluster_id,
        }
        return [tx]
