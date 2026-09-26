import argparse
import hashlib
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Enable running both as module and standalone script
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd

from data.generators.config import (
    DEFAULT_SEED,
    OUTPUT_DIRS,
    SCALE_PROFILES,
    SYNTHETIC_DATA_DIR,
    ScaleProfile,
)
from data.generators.narrative_templates import generate_complaint_narrative
from data.generators.patterns import FraudPatternGenerator
from data.generators.vocabularies import (
    ACCOUNT_TYPES,
    CYBER_CRIME_HOTSPOTS,
    DEVICE_MODELS,
    FIRST_NAMES,
    INCOME_BRACKETS,
    INDIAN_STATES_DATA,
    LAST_NAMES,
    OCCUPATIONS,
    PAYMENT_CHANNELS,
    SYNTHETIC_BANKS,
    TELECOM_OPERATORS,
    TRANSACTION_TYPES,
    UPI_HANDLES,
)


class SyntheticDataEngine:
    """End-to-end generator orchestrating 10 domain entities and fraud typologies."""

    def __init__(self, profile: ScaleProfile, seed: int = DEFAULT_SEED, export_format: str = "both"):
        self.profile = profile
        self.seed = seed
        self.export_format = export_format
        random.seed(seed)

        # In-memory storage of generated datasets
        self.locations: List[Dict[str, Any]] = []
        self.customers: List[Dict[str, Any]] = []
        self.devices: List[Dict[str, Any]] = []
        self.phone_numbers: List[Dict[str, Any]] = []
        self.accounts: List[Dict[str, Any]] = []
        self.upi_ids: List[Dict[str, Any]] = []
        self.fraud_clusters: List[Dict[str, Any]] = []
        self.transactions: List[Dict[str, Any]] = []
        self.atm_interactions: List[Dict[str, Any]] = []
        self.complaints: List[Dict[str, Any]] = []

        # Fast lookup indices for referential integrity
        self.mule_accounts: List[Dict[str, Any]] = []
        self.normal_accounts: List[Dict[str, Any]] = []
        self.account_by_num: Dict[str, Dict[str, Any]] = {}
        self.device_by_id: Dict[str, Dict[str, Any]] = {}
        self.upi_by_vpa: Dict[str, Dict[str, Any]] = {}
        self.customer_by_id: Dict[str, Dict[str, Any]] = {}
        self.phone_by_num: Dict[str, Dict[str, Any]] = {}
        self.hotspot_locations: List[Dict[str, Any]] = []
        self.normal_locations: List[Dict[str, Any]] = []

    def generate_all(self):
        """Execute complete generation pipeline."""
        print(f"[*] Starting Synthetic Data Generation (Scale: {self.profile.name}, Seed: {self.seed})...")
        self._generate_locations()
        self._generate_customers()
        self._generate_devices()
        self._generate_phone_numbers()
        self._generate_bank_accounts()
        self._generate_upi_ids()
        self._generate_fraud_clusters()
        self._generate_normal_transactions()
        self._generate_fraud_patterns_and_complaints()
        self._generate_normal_atm_interactions()
        self._export_datasets()
        print(f"[✓] Generation complete! Files written to {SYNTHETIC_DATA_DIR}")

    def _generate_locations(self):
        """1. Generate locations including benchmark cyber threat hotspots."""
        print("  -> Generating locations...")
        loc_counter = 1

        # Designated Hotspots
        for hs in CYBER_CRIME_HOTSPOTS:
            loc = {
                "location_id": f"LOC_{loc_counter:05d}",
                "state": hs["state"],
                "district": hs["district"],
                "city": hs["name"].split()[0],
                "pincode": hs["pincode"],
                "latitude": hs["lat"],
                "longitude": hs["lng"],
                "is_cyber_hotspot": True,
                "hotspot_cluster_name": hs["name"],
            }
            self.locations.append(loc)
            self.hotspot_locations.append(loc)
            loc_counter += 1

        # Regular Indian Cities & Districts
        remaining = self.profile.num_locations - len(self.locations)
        for _ in range(remaining):
            state_info = random.choice(INDIAN_STATES_DATA)
            city_info = random.choice(state_info["cities"])
            city, base_pin, base_lat, base_lng = city_info
            pin_offset = random.randint(0, 80)
            pincode = f"{int(base_pin) + pin_offset:06d}"
            lat = round(base_lat + random.uniform(-0.15, 0.15), 4)
            lng = round(base_lng + random.uniform(-0.15, 0.15), 4)

            loc = {
                "location_id": f"LOC_{loc_counter:05d}",
                "state": state_info["state"],
                "district": city,
                "city": city,
                "pincode": pincode,
                "latitude": lat,
                "longitude": lng,
                "is_cyber_hotspot": False,
                "hotspot_cluster_name": "None",
            }
            self.locations.append(loc)
            self.normal_locations.append(loc)
            loc_counter += 1

    def _generate_customers(self):
        """2. Generate synthetic customer profiles."""
        print("  -> Generating customers...")
        base_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        mule_fraction = 0.12  # 12% potential mule personas

        for i in range(1, self.profile.num_customers + 1):
            cust_id = f"CUST_{i:07d}"
            fname = random.choice(FIRST_NAMES)
            lname = random.choice(LAST_NAMES)
            name = f"{fname} {lname}"
            dob_year = random.randint(1965, 2004)
            dob = f"{dob_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
            gender = random.choice(["M", "F"])
            is_mule = random.random() < mule_fraction
            risk_cat = random.choice(["HIGH", "CRITICAL"]) if is_mule else random.choice(["LOW", "LOW", "MEDIUM"])

            cust = {
                "customer_id": cust_id,
                "synthetic_name": name,
                "dob": dob,
                "gender": gender,
                "occupation": random.choice(OCCUPATIONS),
                "annual_income_bracket": random.choice(INCOME_BRACKETS),
                "risk_category": risk_cat,
                "is_mule_suspect": is_mule,
                "cluster_id": "NONE",
                "created_at": (base_date + timedelta(days=random.randint(1, 400))).isoformat(),
            }
            self.customers.append(cust)
            self.customer_by_id[cust_id] = cust

    def _generate_devices(self):
        """3. Generate devices with emulator and root flags."""
        print("  -> Generating devices...")
        for i in range(1, self.profile.num_devices + 1):
            dev_id = f"DEV_{i:07d}"
            model_info = random.choice(DEVICE_MODELS)
            model, maker, os_ver = model_info
            is_emulator = "Emulator" in maker or "BlueStacks" in maker
            is_rooted = is_emulator or (random.random() < 0.05)

            raw_imei = f"86{random.randint(1000000000000, 9999999999999)}"
            imei_hash = hashlib.sha256(raw_imei.encode()).hexdigest()[:16]

            ip_prefix = random.choice(["49.36", "106.198", "157.34", "223.187", "14.139"])
            ip_addr = f"{ip_prefix}.{random.randint(1, 254)}.{random.randint(1, 254)}"

            loc = random.choice(self.locations)
            dev = {
                "device_id": dev_id,
                "imei_hash": imei_hash,
                "device_model": model,
                "os_version": os_ver,
                "ip_address": ip_addr,
                "is_emulator": is_emulator,
                "is_rooted_jailbroken": is_rooted,
                "is_shared_device": is_emulator or (random.random() < 0.08),
                "primary_location_id": loc["location_id"],
                "created_at": "2023-04-15T00:00:00Z",
            }
            self.devices.append(dev)
            self.device_by_id[dev_id] = dev

    def _generate_phone_numbers(self):
        """4. Generate synthetic phone numbers linked to customers and devices."""
        print("  -> Generating phone numbers...")
        circles = ["MH", "DL", "KA", "TS", "UP", "RJ", "GJ", "WB", "HR", "JH"]

        for i, cust in enumerate(self.customers, 1):
            phone = f"+9198{random.randint(10000000, 99999999)}"
            dev = self.devices[min(i - 1, len(self.devices) - 1)]
            operator = random.choice(TELECOM_OPERATORS)
            is_suspect = cust["is_mule_suspect"]

            phone_entry = {
                "phone_number": phone,
                "operator": operator,
                "circle": random.choice(circles),
                "customer_id": cust["customer_id"],
                "device_id": dev["device_id"],
                "sim_activation_date": "2023-01-10",
                "is_virtual_voip": is_suspect and (random.random() < 0.25),
                "is_suspect": is_suspect,
                "cluster_id": "NONE",
            }
            self.phone_numbers.append(phone_entry)
            self.phone_by_num[phone] = phone_entry
            cust["phone_number"] = phone
            cust["primary_device_id"] = dev["device_id"]

    def _generate_bank_accounts(self):
        """5. Generate bank accounts with tier labels (0=Legit, 1=Receiver, 2=Distributor, 3=Cashout)."""
        print("  -> Generating bank accounts...")
        acc_counter = 1000000000

        for i in range(1, self.profile.num_accounts + 1):
            acc_num = f"SYN{acc_counter + i}"
            cust = self.customers[(i - 1) % len(self.customers)]
            bank_code, bank_name, _ = random.choice(SYNTHETIC_BANKS)
            branch_num = random.randint(101, 999)
            ifsc = f"{bank_code}000{branch_num}"

            is_mule = cust["is_mule_suspect"]
            mule_tier = random.choice([1, 2, 3]) if is_mule else 0
            loc = self.hotspot_locations[(i % len(self.hotspot_locations))] if is_mule else random.choice(self.normal_locations)

            acc = {
                "account_number": acc_num,
                "customer_id": cust["customer_id"],
                "bank_name": bank_name,
                "ifsc_code": ifsc,
                "branch_name": f"{loc['city']} Branch",
                "account_type": random.choice(ACCOUNT_TYPES),
                "opening_date": "2023-02-01",
                "current_balance": round(random.uniform(500.0, 15000.0) if is_mule else random.uniform(15000.0, 350000.0), 2),
                "is_mule": is_mule,
                "mule_tier": mule_tier,
                "cluster_id": "NONE",
                "status": "WATCHLIST" if is_mule else "ACTIVE",
                "location_id": loc["location_id"],
                "primary_device_id": cust["primary_device_id"],
            }
            self.accounts.append(acc)
            self.account_by_num[acc_num] = acc
            if is_mule:
                self.mule_accounts.append(acc)
            else:
                self.normal_accounts.append(acc)

    def _generate_upi_ids(self):
        """6. Generate synthetic UPI IDs linked to bank accounts and phones."""
        print("  -> Generating UPI IDs...")
        for i in range(1, self.profile.num_upi_ids + 1):
            acc = self.accounts[(i - 1) % len(self.accounts)]
            cust = self.customer_by_id[acc["customer_id"]]
            phone = cust.get("phone_number", "+919876543210")
            handle = random.choice(UPI_HANDLES)

            name_slug = cust["synthetic_name"].lower().replace(" ", ".")
            vpa = f"{name_slug}.{random.randint(10, 999)}@{handle}"

            upi_entry = {
                "vpa": vpa,
                "account_number": acc["account_number"],
                "linked_phone_number": phone,
                "psp_handle": f"@{handle}",
                "creation_date": "2023-03-01",
                "is_suspicious": acc["is_mule"],
                "status": "ACTIVE",
            }
            self.upi_ids.append(upi_entry)
            self.upi_by_vpa[vpa] = upi_entry
            acc["primary_upi_id"] = vpa

    def _generate_fraud_clusters(self):
        """7. Initialize syndicates / fraud clusters."""
        print("  -> Initializing fraud clusters...")
        cluster_types = [
            "MULE_RING_CHAIN", "MANY_TO_ONE_FUNNEL", "ONE_TO_MANY_SMURFING",
            "RAPID_CASHOUT_RING", "DIGITAL_ARREST_SYNDICATE", "TASK_SCAM_SYNDICATE"
        ]

        for i in range(1, self.profile.num_fraud_clusters + 1):
            cid = f"CLUSTER_{i:04d}"
            c_type = cluster_types[(i - 1) % len(cluster_types)]
            hotspot = self.hotspot_locations[(i - 1) % len(self.hotspot_locations)]

            cluster = {
                "cluster_id": cid,
                "cluster_type": c_type,
                "core_hotspot_id": hotspot["location_id"],
                "member_account_count": random.randint(4, 12),
                "member_device_count": random.randint(2, 6),
                "total_flow_amount": 0.0,
                "detected_patterns": c_type,
                "risk_severity": "CRITICAL" if "ARREST" in c_type or "CHAIN" in c_type else "HIGH",
            }
            self.fraud_clusters.append(cluster)

    def _generate_normal_transactions(self):
        """8. Generate normal background transactions (peer-to-peer, payments, cash-ins)."""
        print("  -> Generating normal transactions...")
        normal_target = int(self.profile.target_transactions * (1.0 - self.profile.fraud_transaction_ratio))
        base_time = datetime(2024, 8, 1, 0, 0, 0, tzinfo=timezone.utc)

        for i in range(1, normal_target + 1):
            sender = random.choice(self.normal_accounts)
            receiver = random.choice(self.normal_accounts)
            while receiver["account_number"] == sender["account_number"]:
                receiver = random.choice(self.normal_accounts)

            txn_type = random.choice(["TRANSFER", "TRANSFER", "PAYMENT", "CASH_IN"])
            channel = random.choice(["UPI", "UPI", "IMPS", "NEFT"])
            amt = round(random.choice([
                random.uniform(50, 2500),
                random.uniform(2500, 15000),
                random.uniform(15000, 45000),
            ]), 2)

            t_offset = timedelta(seconds=random.randint(1, 60 * 86400))
            txn_time = base_time + t_offset

            tx = {
                "transaction_id": f"TXN_{i:08d}",
                "sender_account_number": sender["account_number"],
                "receiver_account_number": receiver["account_number"],
                "sender_upi_id": sender.get("primary_upi_id", "N/A"),
                "receiver_upi_id": receiver.get("primary_upi_id", "N/A"),
                "sender_device_id": sender.get("primary_device_id", "N/A"),
                "receiver_device_id": receiver.get("primary_device_id", "N/A"),
                "sender_location_id": sender["location_id"],
                "receiver_location_id": receiver["location_id"],
                "transaction_type": txn_type,
                "payment_channel": channel,
                "amount": amt,
                "timestamp": txn_time.isoformat(),
                "is_fraud": False,
                "pattern_type": "NORMAL",
                "cluster_id": "NONE",
            }
            self.transactions.append(tx)

    def _generate_fraud_patterns_and_complaints(self):
        """9. Generate suspicious patterns and 100% referentially linked complaints."""
        print("  -> Generating suspicious patterns and linked complaints...")
        txn_counter = len(self.transactions) + 1
        atm_counter = 1
        complaint_counter = 1

        base_time = datetime(2024, 8, 15, 10, 0, 0, tzinfo=timezone.utc)
        fraud_categories = [
            "UPI fraud", "KYC fraud", "investment fraud", "fake customer care", "phishing",
            "loan scam", "job scam", "impersonation", "digital arrest scam", "online shopping fraud"
        ]

        # Partition mule accounts by tier
        l1_mules = [a for a in self.mule_accounts if a["mule_tier"] == 1] or self.mule_accounts[:len(self.mule_accounts)//3]
        l2_mules = [a for a in self.mule_accounts if a["mule_tier"] == 2] or self.mule_accounts[len(self.mule_accounts)//3: 2*len(self.mule_accounts)//3]
        l3_mules = [a for a in self.mule_accounts if a["mule_tier"] == 3] or self.mule_accounts[2*len(self.mule_accounts)//3:]

        while len(self.transactions) < self.profile.target_transactions and len(self.complaints) < self.profile.target_complaints:
            cluster = random.choice(self.fraud_clusters)
            category = fraud_categories[(complaint_counter - 1) % len(fraud_categories)]
            victim = random.choice(self.normal_accounts)
            l1 = random.choice(l1_mules)
            l2 = random.choice(l2_mules)
            l3 = random.choice(l3_mules)

            # Assign cluster tagging
            l1["cluster_id"] = cluster["cluster_id"]
            l2["cluster_id"] = cluster["cluster_id"]
            l3["cluster_id"] = cluster["cluster_id"]

            pattern_choice = random.choice([
                "rapid_velocity", "mule_chain", "many_to_one", "one_to_many",
                "rapid_cashout", "unusual_testing", "repeated_burst", "geo_anomaly"
            ])

            time_anchor = base_time + timedelta(hours=complaint_counter * 3, minutes=random.randint(1, 45))
            initial_fraud_txn = None
            generated_txns = []

            if pattern_choice == "rapid_velocity":
                amt = round(random.uniform(25000, 95000), 2)
                generated_txns = FraudPatternGenerator.generate_rapid_velocity(
                    cluster["cluster_id"], victim, l1, l2, time_anchor, amt, txn_counter
                )
                initial_fraud_txn = generated_txns[0]
                txn_counter += len(generated_txns)

            elif pattern_choice == "mule_chain":
                amt = round(random.uniform(45000, 180000), 2)
                generated_txns = FraudPatternGenerator.generate_mule_chain(
                    cluster["cluster_id"], victim, l1, l2, l3, time_anchor, amt, txn_counter
                )
                initial_fraud_txn = generated_txns[0]
                txn_counter += len(generated_txns)

            elif pattern_choice == "many_to_one":
                v_group = [victim] + random.sample(self.normal_accounts, min(4, len(self.normal_accounts)))
                generated_txns = FraudPatternGenerator.generate_many_to_one_funnel(
                    cluster["cluster_id"], v_group, l1, time_anchor, txn_counter
                )
                initial_fraud_txn = generated_txns[0]
                txn_counter += len(generated_txns)

            elif pattern_choice == "one_to_many":
                sub_mules = random.sample(l2_mules, min(4, len(l2_mules)))
                # First credit the distributor
                credit_tx = {
                    "transaction_id": f"TXN_{txn_counter:08d}",
                    "sender_account_number": victim["account_number"],
                    "receiver_account_number": l1["account_number"],
                    "sender_upi_id": victim.get("primary_upi_id", "N/A"),
                    "receiver_upi_id": l1.get("primary_upi_id", "N/A"),
                    "sender_device_id": victim.get("primary_device_id", "N/A"),
                    "receiver_device_id": l1.get("primary_device_id", "N/A"),
                    "sender_location_id": victim["location_id"],
                    "receiver_location_id": l1["location_id"],
                    "transaction_type": "TRANSFER",
                    "payment_channel": "UPI",
                    "amount": 49000.0,
                    "timestamp": time_anchor.isoformat(),
                    "is_fraud": True,
                    "pattern_type": "ONE_TO_MANY_FAN_OUT",
                    "cluster_id": cluster["cluster_id"],
                }
                generated_txns.append(credit_tx)
                txn_counter += 1
                smurfed = FraudPatternGenerator.generate_one_to_many_smurfing(
                    cluster["cluster_id"], l1, sub_mules, time_anchor + timedelta(minutes=2), txn_counter
                )
                generated_txns.extend(smurfed)
                initial_fraud_txn = credit_tx
                txn_counter += len(smurfed)

            elif pattern_choice == "rapid_cashout":
                amt = round(random.uniform(20000, 50000), 2)
                atm_loc = cluster["core_hotspot_id"]
                tx_list, atm_list = FraudPatternGenerator.generate_rapid_cashout(
                    cluster["cluster_id"], victim, l1, atm_loc, time_anchor, amt, txn_counter, atm_counter
                )
                generated_txns.extend(tx_list)
                self.atm_interactions.extend(atm_list)
                initial_fraud_txn = tx_list[0]
                txn_counter += len(tx_list)
                atm_counter += len(atm_list)

            elif pattern_choice == "unusual_testing":
                amt = round(random.uniform(35000, 120000), 2)
                generated_txns = FraudPatternGenerator.generate_unusual_amount_testing(
                    cluster["cluster_id"], victim, l1, time_anchor, amt, txn_counter
                )
                initial_fraud_txn = generated_txns[1]  # The drain transaction
                txn_counter += len(generated_txns)

            elif pattern_choice == "repeated_burst":
                chunk = float(random.choice([19999.0, 24999.0, 49999.0]))
                reps = random.randint(2, 4)
                generated_txns = FraudPatternGenerator.generate_repeated_burst(
                    cluster["cluster_id"], victim, l1, time_anchor, chunk, reps, txn_counter
                )
                initial_fraud_txn = generated_txns[0]
                txn_counter += len(generated_txns)

            else:  # geo_anomaly
                amt = round(random.uniform(15000, 60000), 2)
                hotspot_loc = cluster["core_hotspot_id"]
                generated_txns = FraudPatternGenerator.generate_geographic_anomaly(
                    cluster["cluster_id"], victim, l1, hotspot_loc, time_anchor, amt, txn_counter
                )
                initial_fraud_txn = generated_txns[0]
                txn_counter += len(generated_txns)

            self.transactions.extend(generated_txns)
            cluster["total_flow_amount"] += sum(t["amount"] for t in generated_txns)

            # Generate referentially consistent cybercrime complaint
            if initial_fraud_txn and len(self.complaints) < self.profile.target_complaints:
                victim_cust = self.customer_by_id[victim["customer_id"]]
                l1_cust = self.customer_by_id[l1["customer_id"]]

                incident_dt = datetime.fromisoformat(initial_fraud_txn["timestamp"])
                reporting_delay = random.randint(1, 48)
                reported_dt = incident_dt + timedelta(hours=reporting_delay)

                context = {
                    "category": category,
                    "victim_name": victim_cust["synthetic_name"],
                    "victim_account": victim["account_number"],
                    "suspect_account": l1["account_number"],
                    "suspect_upi": l1.get("primary_upi_id", "N/A"),
                    "suspect_phone": l1_cust.get("phone_number", "+919876543210"),
                    "suspect_device": l1.get("primary_device_id", "N/A"),
                    "amount": initial_fraud_txn["amount"],
                    "bank_name": l1["bank_name"],
                }
                narrative = generate_complaint_narrative(context)

                comp = {
                    "complaint_id": f"CMP_{complaint_counter:07d}",
                    "acknowledgement_no": f"NCRP-SYN-2024-{100000 + complaint_counter}",
                    "incident_date": incident_dt.isoformat(),
                    "reported_date": reported_dt.isoformat(),
                    "reporting_delay_hours": reporting_delay,
                    "category": category,
                    "reported_loss_amount": initial_fraud_txn["amount"],
                    "narrative_synthetic": narrative,
                    "victim_account_number": victim["account_number"],
                    "suspect_account_number": l1["account_number"],
                    "suspect_upi_id": l1.get("primary_upi_id", "N/A"),
                    "suspect_phone_number": l1_cust.get("phone_number", "+919876543210"),
                    "initial_transaction_id": initial_fraud_txn["transaction_id"],
                    "suspect_device_id": l1.get("primary_device_id", "N/A"),
                    "victim_state": victim["branch_name"].split()[0],
                    "suspect_state": l1["branch_name"].split()[0],
                    "cluster_id": cluster["cluster_id"],
                    "ground_truth_category": category,
                }
                self.complaints.append(comp)
                complaint_counter += 1

    def _generate_normal_atm_interactions(self):
        """10. Generate legitimate ATM cash interactions."""
        print("  -> Generating normal ATM cash transactions...")
        remaining = self.profile.target_atm_interactions - len(self.atm_interactions)
        base_time = datetime(2024, 8, 2, 0, 0, 0, tzinfo=timezone.utc)
        atm_start_id = len(self.atm_interactions) + 1
        txn_counter = len(self.transactions) + 1

        for i in range(remaining):
            acc = random.choice(self.normal_accounts)
            amt = float(random.choice([1000, 2000, 3000, 5000, 10000, 15000, 20000]))
            t_time = base_time + timedelta(seconds=random.randint(1, 40 * 86400))
            loc = random.choice(self.normal_locations)

            tx_id = f"TXN_{txn_counter:08d}"
            tx = {
                "transaction_id": tx_id,
                "sender_account_number": acc["account_number"],
                "receiver_account_number": "N/A",
                "sender_upi_id": "N/A",
                "receiver_upi_id": "N/A",
                "sender_device_id": "N/A",
                "receiver_device_id": "N/A",
                "sender_location_id": loc["location_id"],
                "receiver_location_id": loc["location_id"],
                "transaction_type": "CASH_OUT",
                "payment_channel": "ATM",
                "amount": amt,
                "timestamp": t_time.isoformat(),
                "is_fraud": False,
                "pattern_type": "NORMAL",
                "cluster_id": "NONE",
            }
            self.transactions.append(tx)
            txn_counter += 1

            atm_entry = {
                "atm_interaction_id": f"ATM_{atm_start_id + i:07d}",
                "account_number": acc["account_number"],
                "atm_id": f"ATM_SYN_{random.randint(1000, 9999)}",
                "location_id": loc["location_id"],
                "timestamp": t_time.isoformat(),
                "amount": amt,
                "status": "SUCCESS",
                "rapid_cashout_flag": False,
                "associated_transaction_id": tx_id,
            }
            self.atm_interactions.append(atm_entry)

    def _export_table(self, data: List[Dict[str, Any]], folder: Path, filename_base: str):
        """Helper to export DataFrame to CSV and/or Parquet."""
        folder.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(data)

        if self.export_format in ("csv", "both"):
            csv_path = folder / f"{filename_base}.csv"
            df.to_csv(csv_path, index=False)

        if self.export_format in ("parquet", "both"):
            try:
                parquet_path = folder / f"{filename_base}.parquet"
                df.to_parquet(parquet_path, index=False)
            except Exception as exc:
                print(f"    [!] Warning: Parquet export for {filename_base} skipped: {exc}")

    def _export_datasets(self):
        """Export all generated tables into specified folder hierarchy."""
        print("  -> Exporting synthetic datasets to disk...")
        self._export_table(self.accounts, OUTPUT_DIRS["accounts"], "bank_accounts")
        self._export_table(self.transactions, OUTPUT_DIRS["transactions"], "transactions")
        self._export_table(self.complaints, OUTPUT_DIRS["complaints"], "complaints")
        self._export_table(self.fraud_clusters, OUTPUT_DIRS["fraud_clusters"], "fraud_clusters")

        # Entities
        self._export_table(self.customers, OUTPUT_DIRS["entities"], "customers")
        self._export_table(self.devices, OUTPUT_DIRS["entities"], "devices")
        self._export_table(self.phone_numbers, OUTPUT_DIRS["entities"], "phone_numbers")
        self._export_table(self.upi_ids, OUTPUT_DIRS["entities"], "upi_ids")
        self._export_table(self.locations, OUTPUT_DIRS["entities"], "locations")
        self._export_table(self.atm_interactions, OUTPUT_DIRS["entities"], "atm_interactions")


def main():
    parser = argparse.ArgumentParser(description="Cybercrime Platform Synthetic Data Generator")
    parser.add_argument(
        "--scale",
        choices=["10K", "50K", "100K", "500K"],
        default="10K",
        help="Dataset scale profile (default: 10K)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "parquet", "both"],
        default="both",
        help="Export format (default: both)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Deterministic seed (default: {DEFAULT_SEED})",
    )

    args = parser.parse_args()
    profile = SCALE_PROFILES[args.scale]

    engine = SyntheticDataEngine(profile=profile, seed=args.seed, export_format=args.format)
    engine.generate_all()


if __name__ == "__main__":
    main()
