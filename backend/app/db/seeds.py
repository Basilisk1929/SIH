"""Database seeding orchestrator populating PostgreSQL with synthetic cybercrime intelligence."""

import asyncio
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Tuple

# Ensure root path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import get_password_hash
from backend.app.db.session import AsyncSessionLocal, engine
from backend.app.models import (
    Base,
    Role,
    User,
    Bank,
    Account,
    ATM,
    Transaction,
    Case,
    Complaint,
    Alert,
    AuditLog,
)
from data.generators.config import ScaleProfile
from data.generators.narrative_templates import generate_complaint_narrative
from data.generators.vocabularies import (
    ACCOUNT_TYPES,
    CYBER_CRIME_HOTSPOTS,
    INDIAN_STATES_DATA,
    SYNTHETIC_BANKS,
)


SEED_SCALE_PROFILE = ScaleProfile(
    name="SEED",
    target_transactions=150,
    num_customers=40,
    num_accounts=50,
    num_upi_ids=60,
    num_devices=40,
    num_locations=25,
    num_fraud_clusters=8,
    target_complaints=25,
    target_atm_interactions=30,
    fraud_transaction_ratio=0.35,
)


async def seed_roles_and_users(db: AsyncSession) -> Tuple[Dict[str, Role], Dict[str, User]]:
    """Seed foundational RBAC roles and investigative officer users without plaintext credentials."""
    # 1. ROLES
    roles_def = [
        ("admin", "Full platform superuser privileges", ["*"]),
        ("supervisor", "Senior cyber investigator with account freeze and warrant approval authority", [
            "complaints:read", "complaints:write", "accounts:freeze", "cases:approve", "audit:read"
        ]),
        ("investigator", "Cyber cell investigative officer handling dossiers and trace requests", [
            "complaints:read", "complaints:write", "accounts:read", "cases:read", "cases:write", "export:data"
        ]),
        ("analyst", "Financial intelligence and transaction flow analyst", [
            "complaints:read", "transactions:read", "graph:analyze", "export:data"
        ]),
        ("auditor", "Compliance and legal oversight inspector", [
            "audit:read", "cases:read", "reports:read"
        ]),
    ]

    roles_map: Dict[str, Role] = {}
    for name, desc, perms in roles_def:
        existing = await db.scalar(select(Role).where(Role.name == name))
        if not existing:
            role = Role(
                id=uuid.uuid4(),
                name=name,
                description=desc,
                permissions=perms,
            )
            db.add(role)
            roles_map[name] = role
        else:
            roles_map[name] = existing

    await db.flush()

    # 2. USERS (NEVER plaintext passwords - always salted bcrypt)
    users_def = [
        ("admin@cybercell.gov.in", "Admin@Cyber#2024!", "Superintendent R. K. Sharma", "LEA-ADM-001", "Directorate General", "admin"),
        ("supervisor@cybercell.gov.in", "Supervisor@2024!", "Inspector Sunita Verma", "LEA-SUP-012", "Cyber Crime Operations", "supervisor"),
        ("investigator@cybercell.gov.in", "Investigate@2024!", "Sub-Inspector Arjun Das", "LEA-INV-042", "Digital Arrest Taskforce", "investigator"),
        ("analyst@cybercell.gov.in", "Analyst@2024!", "Analyst Priyanshu Mehta", "LEA-ANA-089", "Financial Crime & Mule Unit", "analyst"),
        ("auditor@cybercell.gov.in", "Auditor@2024!", "Chief Vigilance Officer P. Nair", "LEA-AUD-007", "Internal Vigilance", "auditor"),
    ]

    users_map: Dict[str, User] = {}
    for email, raw_pwd, full_name, badge, dept, role_name in users_def:
        existing_user = await db.scalar(select(User).where(User.email == email))
        if not existing_user:
            user = User(
                id=uuid.uuid4(),
                role_id=roles_map[role_name].id,
                email=email,
                hashed_password=get_password_hash(raw_pwd),
                full_name=full_name,
                badge_number=badge,
                department=dept,
                phone=f"+9198{random.randint(10000000, 99999999)}",
                is_active=True,
            )
            db.add(user)
            users_map[email] = user
        else:
            users_map[email] = existing_user

    await db.flush()
    return roles_map, users_map


async def seed_banks_and_atms(db: AsyncSession) -> Tuple[Dict[str, Bank], List[ATM]]:
    """Seed financial institutions and ATM terminals."""
    banks_map: Dict[str, Bank] = {}
    for code, name, bank_type in SYNTHETIC_BANKS:
        existing = await db.scalar(select(Bank).where(Bank.bank_code == code))
        if not existing:
            bank = Bank(
                id=uuid.uuid4(),
                bank_code=code,
                bank_name=name,
                bank_type=bank_type,
                headquarters=f"{random.choice(['Mumbai', 'New Delhi', 'Bengaluru', 'Chennai'])}, India",
                nodal_officer_name=f"Nodal Officer {name.split()[0]}",
                nodal_officer_email=f"nodal.cyber@{code.lower()}.synth",
                nodal_officer_phone=f"+9111{random.randint(20000000, 89999999)}",
                is_active=True,
            )
            db.add(bank)
            banks_map[code] = bank
        else:
            banks_map[code] = existing

    await db.flush()

    # Seed ATMs
    atms: List[ATM] = []
    atm_models = ["NCR SelfServ 84", "Diebold Nixdorf CS 7700", "Hyosung Monimax 7600T", "Hitachi Money Spot 200"]
    atm_counter = 1

    for state_data in INDIAN_STATES_DATA[:6]:
        state = state_data["state"]
        for city_info in state_data["cities"]:
            city, pincode, lat, lng = city_info
            bank_code = random.choice(list(banks_map.keys()))
            atm_id = f"ATM_{bank_code}_{atm_counter:04d}"

            existing_atm = await db.scalar(select(ATM).where(ATM.atm_id == atm_id))
            if not existing_atm:
                atm = ATM(
                    id=uuid.uuid4(),
                    atm_id=atm_id,
                    bank_id=banks_map[bank_code].id,
                    terminal_model=random.choice(atm_models),
                    location_id=f"LOC_{atm_counter:05d}",
                    location_name=f"{banks_map[bank_code].bank_name} e-Lobby, {city} Branch",
                    address=f"Plot {random.randint(10, 999)}, Commercial Hub, {city}",
                    city=city,
                    state=state,
                    pincode=pincode,
                    latitude=Decimal(str(round(lat + random.uniform(-0.02, 0.02), 7))),
                    longitude=Decimal(str(round(lng + random.uniform(-0.02, 0.02), 7))),
                    is_active=True,
                )
                db.add(atm)
                atms.append(atm)
                atm_counter += 1
            else:
                atms.append(existing_atm)

    await db.flush()
    return banks_map, atms


async def seed_accounts_and_transactions(
    db: AsyncSession,
    banks_map: Dict[str, Bank],
    atms: List[ATM],
) -> Tuple[List[Account], List[Transaction]]:
    """Seed accounts (both normal and mule clusters) and money trail transactions."""
    first_names = ["Aarav", "Pooja", "Vikram", "Sneha", "Rahul", "Ananya", "Rohan", "Meera", "Deepak", "Kavita"]
    last_names = ["Sharma", "Verma", "Gupta", "Patel", "Reddy", "Iyer", "Singh", "Joshi", "Mishra", "Deshmukh"]

    accounts: List[Account] = []
    account_num_counter = 1000000001
    bank_codes = list(banks_map.keys())

    # Create 50 accounts: 35 normal, 15 mule (layers 1-3)
    for i in range(50):
        acc_num = f"SYN{account_num_counter + i}"
        existing = await db.scalar(select(Account).where(Account.account_number == acc_num))
        if existing:
            accounts.append(existing)
            continue

        b_code = random.choice(bank_codes)
        bank = banks_map[b_code]
        is_mule = (i >= 35)
        layer = random.randint(1, 3) if is_mule else 0
        risk = Decimal(str(round(random.uniform(0.70, 0.98), 4))) if is_mule else Decimal(str(round(random.uniform(0.01, 0.25), 4)))

        flagged_reasons = (
            ["High Outflow Velocity", f"Layer {layer} Mule Chain", "Rapid Cash-Out"]
            if is_mule
            else []
        )

        acc = Account(
            id=uuid.uuid4(),
            account_number=acc_num,
            bank_id=bank.id,
            bank_name=bank.bank_name,
            ifsc_code=f"{b_code}000{random.randint(1000, 9999)}",
            branch_name=f"{random.choice(['Main', 'Bandra', 'Connaught Place', 'Indiranagar', 'Koramangala'])} Branch",
            customer_id=f"CUST_{i+1:05d}",
            holder_name=f"{random.choice(first_names)} {random.choice(last_names)}",
            phone_linked=f"+9198{random.randint(10000000, 99999999)}",
            account_type=random.choice(["SAVINGS", "CURRENT"]),
            balance_inr=Decimal(str(random.randint(5000, 850000))) if not is_mule else Decimal(str(random.randint(1000, 35000))),
            total_credit_volume_inr=Decimal(str(random.randint(50000, 2500000))),
            total_debit_volume_inr=Decimal(str(random.randint(40000, 2450000))),
            is_frozen=(is_mule and layer == 1),
            risk_score=risk,
            mule_layer_detected=layer,
            flagged_reasons=flagged_reasons,
            first_seen=datetime.now(timezone.utc) - timedelta(days=random.randint(30, 180)),
            last_seen=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48)),
        )
        db.add(acc)
        accounts.append(acc)

    await db.flush()

    # Seed Transactions
    transactions: List[Transaction] = []
    rails = ["UPI", "IMPS", "NEFT", "RTGS", "CASH_OUT"]
    now = datetime.now(timezone.utc)

    for i in range(120):
        sender = random.choice(accounts)
        receiver = random.choice(accounts)
        while receiver.id == sender.id:
            receiver = random.choice(accounts)

        is_suspicious = (sender.mule_layer_detected > 0 or receiver.mule_layer_detected > 0)
        rail = "CASH_OUT" if (is_suspicious and random.random() < 0.3) else random.choice(["UPI", "IMPS", "NEFT"])
        assigned_atm = random.choice(atms) if rail == "CASH_OUT" else None

        txn_ref = f"{rail}/{random.randint(100000000000, 999999999999)}/SYN"
        existing_txn = await db.scalar(select(Transaction).where(Transaction.txn_ref_no == txn_ref))
        if existing_txn:
            transactions.append(existing_txn)
            continue

        amount = Decimal(str(random.choice([5000, 10000, 25000, 48000, 95000, 140000, 490000])))
        txn = Transaction(
            id=uuid.uuid4(),
            txn_ref_no=txn_ref,
            sender_account_id=sender.id,
            receiver_account_id=receiver.id if rail != "CASH_OUT" else None,
            sender_account_number=sender.account_number,
            receiver_account_number=receiver.account_number if rail != "CASH_OUT" else "ATM_DISPENSE",
            sender_upi=f"{sender.holder_name.lower().replace(' ', '.')}@synaxis",
            receiver_upi=f"{receiver.holder_name.lower().replace(' ', '.')}@synaxis" if rail != "CASH_OUT" else "N/A",
            sender_device_id=f"DEV_{random.randint(100, 999):05d}",
            receiver_device_id=f"DEV_{random.randint(100, 999):05d}" if rail != "CASH_OUT" else "ATM_HARDWARE",
            atm_id=assigned_atm.id if assigned_atm else None,
            amount_inr=amount,
            rail_type=rail,
            status="SUCCESS",
            timestamp=now - timedelta(hours=random.randint(1, 168)),
            layer_depth=max(sender.mule_layer_detected, receiver.mule_layer_detected, 1),
            is_flagged_suspicious=is_suspicious,
            anomaly_score=Decimal(str(round(random.uniform(0.75, 0.99), 4))) if is_suspicious else Decimal("0.0200"),
        )
        db.add(txn)
        transactions.append(txn)

    await db.flush()
    return accounts, transactions


async def seed_cases_complaints_alerts(
    db: AsyncSession,
    users_map: Dict[str, User],
    accounts: List[Account],
    transactions: List[Transaction],
) -> Tuple[List[Case], List[Complaint], List[Alert]]:
    """Seed cases, NCRP citizen complaints, and algorithmic alerts."""
    investigator = users_map["investigator@cybercell.gov.in"]
    supervisor = users_map["supervisor@cybercell.gov.in"]

    cases_def = [
        ("CASE-2024-00101", "Digital Arrest Extortion Syndicate - Mumbai Suburban", "Multi-layered mule ring impersonating CBI/Customs officials targeting senior citizens.", "CRITICAL", Decimal("4850000.00"), Decimal("1250000.00")),
        ("CASE-2024-00102", "Instant Loan App APK Harassment Ring", "Illegal lending syndicate deploying remote access APKs and demanding predatory repayments.", "HIGH", Decimal("1820000.00"), Decimal("450000.00")),
        ("CASE-2024-00103", "Telegram Work-From-Home Investment Scam", "Ponzi investment operation funneling victim deposits via rapid mule fan-out chains.", "HIGH", Decimal("3200000.00"), Decimal("800000.00")),
    ]

    cases: List[Case] = []
    for case_no, title, desc, priority, total_fraud, recovered in cases_def:
        existing = await db.scalar(select(Case).where(Case.case_number == case_no))
        if not existing:
            c = Case(
                id=uuid.uuid4(),
                case_number=case_no,
                title=title,
                description=desc,
                priority=priority,
                status="ACTIVE",
                assigned_to_user_id=investigator.id,
                created_by_user_id=supervisor.id,
                total_fraud_amount_inr=total_fraud,
                recovered_amount_inr=recovered,
            )
            db.add(c)
            cases.append(c)
        else:
            cases.append(existing)

    await db.flush()

    # Seed Complaints
    complaints: List[Complaint] = []
    scam_types = [
        ("digital arrest scam", "Victim kept on Skype video call under threat of fictitious CBI warrant.", 450000.00),
        ("UPI fraud", "Victim asked to scan QR code on OLX to receive marketplace payment.", 35000.00),
        ("investment fraud", "Promised 300% weekly return on bogus cryptocurrency exchange trading bot.", 280000.00),
        ("KYC fraud", "SMS warning SIM card deactivation unless electricity bill / KYC updated.", 65000.00),
        ("job scam", "Victim paid processing fees for fictitious overseas hotel employment.", 95000.00),
    ]

    mule_accounts = [a for a in accounts if a.mule_layer_detected > 0]
    now = datetime.now(timezone.utc)

    for i in range(20):
        ack_no = f"NCRP-SYN-2024-{100001 + i}"
        existing = await db.scalar(select(Complaint).where(Complaint.acknowledgement_no == ack_no))
        if existing:
            complaints.append(existing)
            continue

        stype, narrative, default_loss = random.choice(scam_types)
        suspect_acc = random.choice(mule_accounts) if mule_accounts else random.choice(accounts)
        assigned_case = random.choice(cases) if random.random() < 0.75 else None

        loss = Decimal(str(round(default_loss * random.uniform(0.8, 1.5), 2)))
        comp = Complaint(
            id=uuid.uuid4(),
            acknowledgement_no=ack_no,
            case_id=assigned_case.id if assigned_case else None,
            category=stype,
            subcategory=f"Simulated Modus - {stype.title()}",
            victim_name=f"Complainant {i+1}",
            victim_phone=f"+9198{random.randint(10000000, 99999999)}",
            victim_state=random.choice(["Maharashtra", "Delhi", "Karnataka", "Rajasthan", "Telangana"]),
            victim_district=f"District {random.randint(1, 5)}",
            reported_loss_inr=loss,
            suspect_upi=f"suspect.{suspect_acc.account_number[-4:]}@synaxis",
            suspect_account_number=suspect_acc.account_number,
            suspect_account_id=suspect_acc.id,
            suspect_ifsc=suspect_acc.ifsc_code,
            suspect_phone=suspect_acc.phone_linked,
            incident_timestamp=now - timedelta(days=random.randint(2, 20)),
            reported_timestamp=now - timedelta(days=random.randint(1, 10)),
            status=random.choice(["NEW", "UNDER_INVESTIGATION", "TRIAGED", "ESCALATED"]),
            triage_priority=random.choice(["CRITICAL", "HIGH", "MEDIUM"]),
            risk_score=Decimal(str(round(random.uniform(0.65, 0.95), 4))),
            description_synthetic=narrative,
        )
        db.add(comp)
        complaints.append(comp)

    await db.flush()

    # Seed Alerts
    alerts: List[Alert] = []
    suspicious_txns = [t for t in transactions if t.is_flagged_suspicious]
    alert_types = [
        ("RAPID_VELOCITY", "HIGH", "High-frequency fund transfers within 60-second window"),
        ("MULE_CHAIN", "CRITICAL", "Multi-hop layered routing across known high-risk accounts"),
        ("RAPID_CASH_OUT", "CRITICAL", "Immediate ATM cash liquidation post high-value inward credit"),
        ("HIGH_VALUE_ANOMALY", "MEDIUM", "Transaction amount exceeds account standard deviation by 4x"),
    ]

    for i in range(15):
        alt_id = f"ALT_{i+1:07d}"
        existing = await db.scalar(select(Alert).where(Alert.alert_id == alt_id))
        if existing:
            alerts.append(existing)
            continue

        atype, sev, flag_desc = random.choice(alert_types)
        txn = random.choice(suspicious_txns) if suspicious_txns else random.choice(transactions)
        acc = random.choice(mule_accounts) if mule_accounts else random.choice(accounts)
        assigned_case = random.choice(cases)

        alert = Alert(
            id=uuid.uuid4(),
            alert_id=alt_id,
            alert_type=atype,
            severity=sev,
            status=random.choice(["OPEN", "INVESTIGATING", "RESOLVED"]),
            risk_score=Decimal(str(round(random.uniform(0.70, 0.98), 4))),
            triggered_entity_type="ACCOUNT" if random.random() < 0.5 else "TRANSACTION",
            triggered_entity_id=acc.account_number if random.random() < 0.5 else txn.txn_ref_no,
            account_id=acc.id,
            transaction_id=txn.id,
            case_id=assigned_case.id,
            rule_flags={"indicator": atype, "explanation": flag_desc, "threshold_exceeded": True},
        )
        db.add(alert)
        alerts.append(alert)

    # Seed Audit Logs
    audit_logs_def = [
        (investigator.id, "FREEZE_ACCOUNT", "ACCOUNT", mule_accounts[0].account_number if mule_accounts else "SYN1000000035", {"reason": "Section 102 CrPC Freeze Notice", "case_id": str(cases[0].id)}),
        (supervisor.id, "CREATE_CASE", "CASE", cases[0].case_number, {"title": cases[0].title, "priority": "CRITICAL"}),
        (users_map["analyst@cybercell.gov.in"].id, "EXPORT_MONEY_TRAIL", "GRAPH", "CLUSTER_SYN_01", {"nodes": 18, "format": "CSV"}),
    ]

    for u_id, action, rtype, rid, details in audit_logs_def:
        audit = AuditLog(
            id=uuid.uuid4(),
            user_id=u_id,
            action=action,
            resource_type=rtype,
            resource_id=rid,
            details=details,
            client_ip="10.20.40.108",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) CyberShield-Client/1.0",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(10, 600)),
        )
        db.add(audit)

    await db.flush()
    return cases, complaints, alerts


async def seed_database(db: AsyncSession) -> Dict[str, int]:
    """Execute complete database seeding with synthetic dataset."""
    print("[*] Starting PostgreSQL Database Seeding...")

    roles_map, users_map = await seed_roles_and_users(db)
    print(f"  -> Seeded {len(roles_map)} roles, {len(users_map)} investigative users.")

    banks_map, atms = await seed_banks_and_atms(db)
    print(f"  -> Seeded {len(banks_map)} banks, {len(atms)} ATM terminals.")

    accounts, transactions = await seed_accounts_and_transactions(db, banks_map, atms)
    print(f"  -> Seeded {len(accounts)} accounts, {len(transactions)} money trail transactions.")

    cases, complaints, alerts = await seed_cases_complaints_alerts(db, users_map, accounts, transactions)
    print(f"  -> Seeded {len(cases)} cases, {len(complaints)} complaints, {len(alerts)} alerts.")

    await db.commit()
    print("[✓] Database seeding successfully committed!")

    return {
        "roles": len(roles_map),
        "users": len(users_map),
        "banks": len(banks_map),
        "atms": len(atms),
        "accounts": len(accounts),
        "transactions": len(transactions),
        "cases": len(cases),
        "complaints": len(complaints),
        "alerts": len(alerts),
    }


async def main():
    """CLI runner for seed script."""
    async with AsyncSessionLocal() as session:
        try:
            await seed_database(session)
        except Exception as e:
            await session.rollback()
            print(f"[!] Error during seeding: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
