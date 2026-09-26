"""Investigation graph service executing Cypher queries and returning explainable evidence."""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional
from neo4j import AsyncDriver, AsyncSession

from graph.queries.investigation_queries import (
    FIND_CONNECTED_ACCOUNTS,
    FIND_TRANSACTION_CHAINS,
    FIND_HIGH_DEGREE_ACCOUNTS,
    FIND_SUSPICIOUS_CLUSTERS,
    FIND_CASHOUT_PATHS,
    FIND_ACCOUNTS_CONNECTED_TO_COMPLAINTS,
    FIND_SHORTEST_SUSPICIOUS_PATHS,
)
from graph.services.evidence_models import (
    ConnectedAccountEvidence,
    TransactionChainEvidence,
    HighDegreeAccountEvidence,
    SuspiciousClusterEvidence,
    CashOutPathEvidence,
    ComplaintConnectionEvidence,
    ShortestPathEvidence,
)

logger = logging.getLogger(__name__)


class GraphInvestigationService:
    """Service executing parameterized Cypher queries to produce explainable investigative intelligence."""

    def __init__(self, driver_or_session: AsyncDriver | AsyncSession):
        self._target = driver_or_session

    async def _execute_query(self, query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run Cypher query safely with parameters and return records as dictionaries."""
        async def _run(session: AsyncSession) -> List[Dict[str, Any]]:
            result = await session.run(query, parameters)
            records = await result.data()
            return records

        if hasattr(self._target, "run") and callable(getattr(self._target, "run")):
            return await _run(self._target)
        elif hasattr(self._target, "session"):
            session_obj = self._target.session()
            if hasattr(session_obj, "__aenter__"):
                async with session_obj as session:
                    return await _run(session)
            else:
                return await _run(session_obj)
        else:
            return await _run(self._target)

    async def find_connected_accounts(
        self, account_number: str, limit: int = 50
    ) -> List[ConnectedAccountEvidence]:
        """1. Find accounts connected directly or via shared infrastructure (Device, Phone, UPI)."""
        records = await self._execute_query(
            FIND_CONNECTED_ACCOUNTS,
            {"account_number": account_number, "limit": limit},
        )
        evidence_list = []
        for r in records:
            if not r.get("connected_account"):
                continue
            evidence_list.append(
                ConnectedAccountEvidence(
                    source_account=r["source_account"],
                    connected_account=r["connected_account"],
                    connection_type=r["connection_type"],
                    hop_distance=r["hop_distance"],
                    shared_entity_id=r.get("shared_entity_id"),
                    total_amount_inr=Decimal(str(r.get("total_amount_inr") or 0)),
                    transaction_count=r.get("transaction_count") or 0,
                    is_mule=bool(r.get("is_mule")),
                    mule_tier=r.get("mule_tier"),
                    explanation=r["explanation"],
                )
            )
        return evidence_list

    async def find_transaction_chains(
        self, account_number: str, min_amount: float = 1000.0, limit: int = 20
    ) -> List[TransactionChainEvidence]:
        """2. Find multi-hop transaction layering chains and velocity anomalies."""
        records = await self._execute_query(
            FIND_TRANSACTION_CHAINS,
            {"account_number": account_number, "min_amount": min_amount, "limit": limit},
        )
        chains = []
        for r in records:
            chains.append(
                TransactionChainEvidence(
                    origin_account=r["origin_account"],
                    destination_account=r["destination_account"],
                    path_nodes=r["path_nodes"],
                    hop_count=r["hop_count"],
                    total_flow_amount_inr=Decimal(str(r["total_flow_amount_inr"])),
                    min_hop_amount_inr=Decimal(str(r["min_hop_amount_inr"])),
                    start_timestamp=str(r.get("start_timestamp")),
                    end_timestamp=str(r.get("end_timestamp")),
                    chain_duration_seconds=r.get("chain_duration_seconds"),
                    velocity_classification=r["velocity_classification"],
                    explanation=r["explanation"],
                )
            )
        return chains

    async def find_high_degree_accounts(
        self, min_degree: int = 4, limit: int = 50
    ) -> List[HighDegreeAccountEvidence]:
        """3. Find high-degree funnel nodes and fund dispersal hubs."""
        records = await self._execute_query(
            FIND_HIGH_DEGREE_ACCOUNTS,
            {"min_degree": min_degree, "limit": limit},
        )
        hubs = []
        for r in records:
            hubs.append(
                HighDegreeAccountEvidence(
                    account_number=r["account_number"],
                    bank_name=r["bank_name"],
                    in_degree=r["in_degree"],
                    out_degree=r["out_degree"],
                    total_degree=r["total_degree"],
                    unique_senders=r["unique_senders"],
                    unique_receivers=r["unique_receivers"],
                    hub_typology=r["hub_typology"],
                    total_credit_volume=Decimal(str(r["total_credit_volume"])),
                    total_debit_volume=Decimal(str(r["total_debit_volume"])),
                    is_mule=bool(r.get("is_mule")),
                    explanation=r["explanation"],
                )
            )
        return hubs

    async def find_suspicious_clusters(
        self, limit: int = 25
    ) -> List[SuspiciousClusterEvidence]:
        """4. Find criminal collusion rings operating across shared devices, phones, or circular loops."""
        records = await self._execute_query(
            FIND_SUSPICIOUS_CLUSTERS,
            {"limit": limit},
        )
        clusters = []
        for r in records:
            clusters.append(
                SuspiciousClusterEvidence(
                    cluster_id=r["cluster_id"],
                    cluster_type=r["cluster_type"],
                    member_accounts=r["member_accounts"],
                    member_count=r["member_count"],
                    shared_identifier=r["shared_identifier"],
                    total_cluster_volume_inr=Decimal(str(r["total_cluster_volume_inr"])),
                    risk_score=float(r["risk_score"]),
                    explanation=r["explanation"],
                )
            )
        return clusters

    async def find_cash_out_paths(
        self, account_number: str, limit: int = 20
    ) -> List[CashOutPathEvidence]:
        """5. Find fund flow trails terminating at ATM cash withdrawals."""
        records = await self._execute_query(
            FIND_CASHOUT_PATHS,
            {"account_number": account_number, "limit": limit},
        )
        cashouts = []
        for r in records:
            cashouts.append(
                CashOutPathEvidence(
                    origin_account=r["origin_account"],
                    cashout_account=r["cashout_account"],
                    atm_id=r["atm_id"],
                    atm_location=r["atm_location"],
                    withdrawn_amount_inr=Decimal(str(r["withdrawn_amount_inr"])),
                    withdrawal_timestamp=str(r["withdrawal_timestamp"]),
                    intermediary_mules=r.get("intermediary_mules") or [],
                    rapid_cashout=bool(r.get("rapid_cashout")),
                    explanation=r["explanation"],
                )
            )
        return cashouts

    async def find_accounts_connected_to_complaints(
        self, category: Optional[str] = None, min_loss: Optional[float] = None, limit: int = 50
    ) -> List[ComplaintConnectionEvidence]:
        """6. Find bank accounts directly named or receiving funds from NCRP cybercrime complaints."""
        records = await self._execute_query(
            FIND_ACCOUNTS_CONNECTED_TO_COMPLAINTS,
            {"category": category, "min_loss": min_loss, "limit": limit},
        )
        complaints = []
        for r in records:
            complaints.append(
                ComplaintConnectionEvidence(
                    acknowledgement_no=r["acknowledgement_no"],
                    category=r["category"],
                    reported_loss_inr=Decimal(str(r["reported_loss_inr"])),
                    connected_account=r["connected_account"],
                    connection_depth=r["connection_depth"],
                    connection_route=r["connection_route"],
                    complaint_reported_date=str(r["complaint_reported_date"]),
                    suspect_upi=r.get("suspect_upi"),
                    suspect_phone=r.get("suspect_phone"),
                    explanation=r["explanation"],
                )
            )
        return complaints

    async def find_shortest_suspicious_path(
        self, source_account: str, target_account: str
    ) -> Optional[ShortestPathEvidence]:
        """7. Find shortest financial path connecting victim to flagged mule or target node."""
        records = await self._execute_query(
            FIND_SHORTEST_SUSPICIOUS_PATHS,
            {"source_account": source_account, "target_account": target_account},
        )
        if not records:
            return None
        r = records[0]
        return ShortestPathEvidence(
            source_entity=r["source_entity"],
            target_entity=r["target_entity"],
            hop_count=r["hop_count"],
            path_nodes=r["path_nodes"],
            path_relationships=r["path_relationships"],
            total_amount_inr=Decimal(str(r["total_amount_inr"])),
            is_suspicious_path=bool(r["is_suspicious_path"]),
            explanation=r["explanation"],
        )
