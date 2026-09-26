"""High-performance ETL pipeline ingesting synthetic transactions, complaints, and entities into Neo4j."""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from neo4j import AsyncDriver, AsyncSession

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings
from backend.app.db.neo4j import get_neo4j_driver
from graph.schema.constraints import apply_graph_schema

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("graph.etl.loader")


# ==============================================================================
# UNWIND INGESTION CYPHER STATEMENTS (AURA OPTIMIZED)
# ==============================================================================

CYPHER_LOAD_LOCATIONS = """
UNWIND $batch AS row
MERGE (l:Location {location_id: row.location_id})
SET l.state = row.state,
    l.district = row.district,
    l.city = row.city,
    l.pincode = row.pincode,
    l.latitude = toFloat(row.latitude),
    l.longitude = toFloat(row.longitude),
    l.is_cyber_hotspot = toBoolean(row.is_cyber_hotspot),
    l.hotspot_cluster_name = row.hotspot_cluster_name
"""

CYPHER_LOAD_BANKS = """
UNWIND $batch AS row
MERGE (b:Bank {bank_code: row.bank_code})
SET b.bank_name = row.bank_name,
    b.bank_type = row.bank_type
"""

CYPHER_LOAD_CUSTOMERS = """
UNWIND $batch AS row
MERGE (c:Customer {customer_id: row.customer_id})
SET c.synthetic_name = row.synthetic_name,
    c.occupation = row.occupation,
    c.annual_income_bracket = row.annual_income_bracket,
    c.risk_category = row.risk_category,
    c.is_mule_suspect = toBoolean(row.is_mule_suspect),
    c.cluster_id = row.cluster_id
"""

CYPHER_LOAD_ACCOUNTS = """
UNWIND $batch AS row
MERGE (a:Account {account_number: row.account_number})
SET a.bank_name = row.bank_name,
    a.ifsc_code = row.ifsc_code,
    a.branch_name = row.branch_name,
    a.account_type = row.account_type,
    a.current_balance = toFloat(row.current_balance),
    a.is_mule = toBoolean(row.is_mule),
    a.mule_tier = toInteger(row.mule_tier),
    a.cluster_id = row.cluster_id,
    a.status = row.status

WITH a, row
WHERE row.customer_id IS NOT NULL
MATCH (c:Customer {customer_id: row.customer_id})
MERGE (c)-[:OWNS]->(a)

WITH a, row
WHERE row.ifsc_code IS NOT NULL
MATCH (b:Bank {bank_code: substring(row.ifsc_code, 0, 4)})
MERGE (a)-[:LINKED_TO]->(b)
"""

CYPHER_LOAD_DEVICES = """
UNWIND $batch AS row
MERGE (d:Device {device_id: row.device_id})
SET d.device_model = row.device_model,
    d.os_version = row.os_version,
    d.ip_address = row.ip_address,
    d.is_emulator = toBoolean(row.is_emulator),
    d.is_shared_device = toBoolean(row.is_shared_device)
"""

CYPHER_LINK_ACCOUNT_DEVICES = """
UNWIND $batch AS row
MATCH (a:Account {account_number: row.account_number})
MATCH (d:Device {device_id: row.primary_device_id})
MERGE (a)-[:USES_DEVICE]->(d)
"""

CYPHER_LOAD_PHONES = """
UNWIND $batch AS row
MERGE (p:Phone {phone_number: row.phone_number})
SET p.operator = row.operator,
    p.circle = row.circle,
    p.is_suspect = toBoolean(row.is_suspect),
    p.cluster_id = row.cluster_id
WITH p, row
WHERE row.customer_id IS NOT NULL
MATCH (c:Customer {customer_id: row.customer_id})
MERGE (c)-[:USES_PHONE]->(p)
"""

CYPHER_LOAD_UPIS = """
UNWIND $batch AS row
MERGE (u:UPI {vpa: row.vpa})
SET u.psp_handle = row.psp_handle,
    u.is_suspicious = toBoolean(row.is_suspicious),
    u.status = row.status
WITH u, row
WHERE row.account_number IS NOT NULL
MATCH (a:Account {account_number: row.account_number})
MERGE (a)-[:USES_UPI]->(u)
"""

CYPHER_LOAD_ATMS = """
UNWIND $batch AS row
MERGE (atm:ATM {atm_id: row.atm_id})
SET atm.location_id = row.location_id
WITH atm, row
WHERE row.location_id IS NOT NULL
MATCH (l:Location {location_id: row.location_id})
MERGE (atm)-[:LOCATED_AT]->(l)
"""

CYPHER_LOAD_TRANSACTIONS = """
UNWIND $batch AS row
MERGE (t:Transaction {transaction_id: row.transaction_id})
SET t.amount = toFloat(row.amount),
    t.rail_type = row.payment_channel,
    t.timestamp = row.timestamp,
    t.is_fraud = toBoolean(row.is_fraud),
    t.pattern_type = row.pattern_type,
    t.cluster_id = row.cluster_id

WITH t, row
MATCH (sender:Account {account_number: row.sender_account_number})
MERGE (t)-[:LINKED_TO]->(sender)

WITH t, sender, row
WHERE row.receiver_account_number IS NOT NULL AND row.receiver_account_number <> 'ATM_DISPENSE'
MATCH (receiver:Account {account_number: row.receiver_account_number})
MERGE (sender)-[r:TRANSFERRED_TO {txn_id: row.transaction_id}]->(receiver)
SET r.amount = toFloat(row.amount),
    r.rail_type = row.payment_channel,
    r.timestamp = row.timestamp,
    r.is_suspicious = toBoolean(row.is_fraud),
    r.pattern_type = row.pattern_type
"""

CYPHER_LOAD_ATM_INTERACTIONS = """
UNWIND $batch AS row
MATCH (a:Account {account_number: row.account_number})
MATCH (atm:ATM {atm_id: row.atm_id})
MERGE (a)-[w:WITHDREW_AT {txn_id: row.atm_interaction_id}]->(atm)
SET w.amount = toFloat(row.amount),
    w.timestamp = row.timestamp,
    w.rapid_cashout = toBoolean(row.rapid_cashout_flag)
"""

CYPHER_LOAD_COMPLAINTS = """
UNWIND $batch AS row
MERGE (cmp:Complaint {acknowledgement_no: row.acknowledgement_no})
SET cmp.complaint_id = row.complaint_id,
    cmp.category = row.category,
    cmp.reported_loss_amount = toFloat(row.reported_loss_amount),
    cmp.reported_date = row.reported_date,
    cmp.incident_date = row.incident_date,
    cmp.suspect_upi_id = row.suspect_upi_id,
    cmp.suspect_phone_number = row.suspect_phone_number,
    cmp.cluster_id = row.cluster_id

WITH cmp, row
WHERE row.suspect_account_number IS NOT NULL
MATCH (acc:Account {account_number: row.suspect_account_number})
MERGE (acc)-[:MENTIONED_IN]->(cmp)

WITH cmp, row
WHERE row.suspect_upi_id IS NOT NULL
MATCH (u:UPI {vpa: row.suspect_upi_id})
MERGE (u)-[:MENTIONED_IN]->(cmp)

WITH cmp, row
WHERE row.suspect_phone_number IS NOT NULL
MATCH (p:Phone {phone_number: row.suspect_phone_number})
MERGE (p)-[:MENTIONED_IN]->(cmp)
"""


class GraphETLPipeline:
    """Orchestrates extraction from synthetic datasets and streaming batch insertion into Neo4j."""

    def __init__(
        self,
        driver: Optional[AsyncDriver] = None,
        data_dir: Path = PROJECT_ROOT / "data" / "synthetic",
        batch_size: int = 1000,
    ):
        self.driver = driver
        self.data_dir = data_dir
        self.batch_size = batch_size

    def _chunk_list(self, data: List[Dict[str, Any]], size: int) -> List[List[Dict[str, Any]]]:
        """Divide a records list into batches for UNWIND."""
        return [data[i : i + size] for i in range(0, len(data), size)]

    async def _execute_batch_query(self, session: AsyncSession, cypher: str, rows: List[Dict[str, Any]], label: str) -> int:
        """Execute UNWIND batches sequentially inside session."""
        chunks = self._chunk_list(rows, self.batch_size)
        total_ingested = 0
        for idx, chunk in enumerate(chunks, 1):
            await session.run(cypher, {"batch": chunk})
            total_ingested += len(chunk)
            if idx % 5 == 0 or idx == len(chunks):
                logger.info(f"  [{label}] Processed batch {idx}/{len(chunks)} ({total_ingested}/{len(rows)} records)")
        return total_ingested

    def extract_dataset(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extract and clean records from CSV / Parquet synthetic datasets."""
        datasets: Dict[str, List[Dict[str, Any]]] = {}

        file_mappings = {
            "locations": self.data_dir / "entities" / "locations.csv",
            "customers": self.data_dir / "entities" / "customers.csv",
            "accounts": self.data_dir / "accounts" / "bank_accounts.csv",
            "devices": self.data_dir / "entities" / "devices.csv",
            "phones": self.data_dir / "entities" / "phone_numbers.csv",
            "upis": self.data_dir / "entities" / "upi_ids.csv",
            "atms": self.data_dir / "entities" / "atm_interactions.csv",
            "transactions": self.data_dir / "transactions" / "transactions.csv",
            "complaints": self.data_dir / "complaints" / "complaints.csv",
        }

        for key, filepath in file_mappings.items():
            if filepath.exists():
                df = pd.read_csv(filepath)
                # Fill NAs cleanly for Cypher NULL mapping
                df = df.where(pd.notnull(df), None)
                datasets[key] = df.to_dict(orient="records")
                logger.info(f"Loaded {len(datasets[key])} {key} from {filepath.name}")
            else:
                logger.warning(f"File not found: {filepath}. Setting empty batch for {key}.")
                datasets[key] = []

        # Derive distinct Banks from accounts
        bank_names = set()
        banks_list = []
        for acc in datasets.get("accounts", []):
            b_name = acc.get("bank_name")
            ifsc = str(acc.get("ifsc_code") or "")
            b_code = ifsc[:4] if len(ifsc) >= 4 else "SYNB"
            if b_code not in bank_names:
                bank_names.add(b_code)
                banks_list.append({
                    "bank_code": b_code,
                    "bank_name": b_name or "Commercial Bank",
                    "bank_type": "Commercial",
                })
        datasets["banks"] = banks_list

        # Derive distinct ATMs from atm_interactions
        distinct_atms = {}
        for atm_row in datasets.get("atms", []):
            aid = atm_row.get("atm_id")
            if aid and aid not in distinct_atms:
                distinct_atms[aid] = {
                    "atm_id": aid,
                    "location_id": atm_row.get("location_id"),
                }
        datasets["distinct_atms"] = list(distinct_atms.values())

        return datasets

    async def run_pipeline(self) -> Dict[str, int]:
        """Execute full extraction, schema migration, and loading pipeline."""
        logger.info("[*] Starting Neo4j Graph ETL Ingestion Pipeline...")
        datasets = self.extract_dataset()

        if self.driver is None:
            self.driver = get_neo4j_driver()

        # Step 1: Ensure Constraints & Indexes
        logger.info("[1/10] Applying Neo4j schema constraints and indexes...")
        await apply_graph_schema(self.driver)

        metrics: Dict[str, int] = {}

        async with self.driver.session() as session:
            # Step 2: Ingest Locations
            logger.info("[2/10] Ingesting Locations...")
            metrics["locations"] = await self._execute_batch_query(
                session, CYPHER_LOAD_LOCATIONS, datasets["locations"], "Locations"
            )

            # Step 3: Ingest Banks
            logger.info("[3/10] Ingesting Banks...")
            metrics["banks"] = await self._execute_batch_query(
                session, CYPHER_LOAD_BANKS, datasets["banks"], "Banks"
            )

            # Step 4: Ingest Customers
            logger.info("[4/10] Ingesting Customers...")
            metrics["customers"] = await self._execute_batch_query(
                session, CYPHER_LOAD_CUSTOMERS, datasets["customers"], "Customers"
            )

            # Step 5: Ingest Accounts & (OWNS, LINKED_TO)
            logger.info("[5/10] Ingesting Accounts & Relationships...")
            metrics["accounts"] = await self._execute_batch_query(
                session, CYPHER_LOAD_ACCOUNTS, datasets["accounts"], "Accounts"
            )

            # Step 6: Ingest Devices, Phones, UPIs & Linkages
            logger.info("[6/10] Ingesting Devices, Phones, UPIs & USES_* Relationships...")
            metrics["devices"] = await self._execute_batch_query(
                session, CYPHER_LOAD_DEVICES, datasets["devices"], "Devices"
            )
            # Link accounts to primary devices
            await self._execute_batch_query(
                session, CYPHER_LINK_ACCOUNT_DEVICES, datasets["accounts"], "Account-Device-Link"
            )
            metrics["phones"] = await self._execute_batch_query(
                session, CYPHER_LOAD_PHONES, datasets["phones"], "Phones"
            )
            metrics["upis"] = await self._execute_batch_query(
                session, CYPHER_LOAD_UPIS, datasets["upis"], "UPIs"
            )

            # Step 7: Ingest ATMs
            logger.info("[7/10] Ingesting ATMs & LOCATED_AT Relationships...")
            metrics["atms"] = await self._execute_batch_query(
                session, CYPHER_LOAD_ATMS, datasets["distinct_atms"], "ATMs"
            )

            # Step 8: Ingest Transactions & TRANSFERRED_TO
            logger.info("[8/10] Ingesting Transactions & TRANSFERRED_TO Relationships...")
            metrics["transactions"] = await self._execute_batch_query(
                session, CYPHER_LOAD_TRANSACTIONS, datasets["transactions"], "Transactions"
            )

            # Step 9: Ingest ATM Interactions (WITHDREW_AT)
            logger.info("[9/10] Ingesting ATM Withdrawals & WITHDREW_AT Relationships...")
            metrics["atm_withdrawals"] = await self._execute_batch_query(
                session, CYPHER_LOAD_ATM_INTERACTIONS, datasets["atms"], "ATM_Withdrawals"
            )

            # Step 10: Ingest Complaints & MENTIONED_IN
            logger.info("[10/10] Ingesting Complaints & MENTIONED_IN Relationships...")
            metrics["complaints"] = await self._execute_batch_query(
                session, CYPHER_LOAD_COMPLAINTS, datasets["complaints"], "Complaints"
            )

        logger.info(f"[✓] ETL Ingestion Pipeline Complete! Ingested metrics: {metrics}")
        return metrics


async def main():
    parser = argparse.ArgumentParser(description="Ingest synthetic datasets into Neo4j Aura")
    parser.add_argument("--data-dir", default=str(PROJECT_ROOT / "data" / "synthetic"), help="Path to synthetic data directory")
    parser.add_argument("--batch-size", type=int, default=1000, help="UNWIND batch size")
    args = parser.parse_args()

    pipeline = GraphETLPipeline(data_dir=Path(args.data_dir), batch_size=args.batch_size)
    try:
        await pipeline.run_pipeline()
    finally:
        if pipeline.driver is not None:
            await pipeline.driver.close()


if __name__ == "__main__":
    asyncio.run(main())
