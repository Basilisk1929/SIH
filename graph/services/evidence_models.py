"""Pydantic models representing structured, explainable graph evidence for investigative queries."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConnectedAccountEvidence(BaseModel):
    """Explainable evidence for accounts connected via direct transfer or shared entity."""

    source_account: str = Field(..., description="Inquired origin account number")
    connected_account: str = Field(..., description="Discovered neighboring account number")
    connection_type: str = Field(..., description="TRANSFER_OUT, TRANSFER_IN, SHARED_DEVICE, SHARED_PHONE, SHARED_UPI")
    hop_distance: int = Field(..., description="Graph distance in hops (1 or 2)")
    shared_entity_id: Optional[str] = Field(None, description="Identifier of shared node (e.g. device_id or phone)")
    total_amount_inr: Decimal = Field(Decimal("0.00"), description="Total money transferred between accounts")
    transaction_count: int = Field(0, description="Count of transfers between accounts")
    is_mule: bool = Field(False, description="Flag indicating if connected account is a designated mule")
    mule_tier: Optional[int] = Field(None, description="Identified mule layering tier (1, 2, 3)")
    explanation: str = Field(..., description="Human-readable investigative rationale")


class TransactionChainEvidence(BaseModel):
    """Explainable evidence for multi-hop money laundering velocity chains."""

    origin_account: str = Field(..., description="Starting sender account")
    destination_account: str = Field(..., description="Final terminal recipient account")
    path_nodes: List[str] = Field(..., description="Ordered list of account numbers in the chain")
    hop_count: int = Field(..., description="Number of hops in the chain")
    total_flow_amount_inr: Decimal = Field(..., description="Total or initial money input into the chain")
    min_hop_amount_inr: Decimal = Field(..., description="Bottleneck amount transferred along the chain")
    start_timestamp: Optional[str] = Field(None, description="First transaction timestamp")
    end_timestamp: Optional[str] = Field(None, description="Last transaction timestamp")
    chain_duration_seconds: Optional[float] = Field(None, description="Elapsed time in seconds across entire chain")
    velocity_classification: str = Field(..., description="RAPID_PASSTHROUGH, MEDIUM_VELOCITY, NORMAL_TIMING")
    explanation: str = Field(..., description="Human-readable investigative evidence summary")


class HighDegreeAccountEvidence(BaseModel):
    """Explainable evidence for high-degree funnel or dispersal hubs."""

    account_number: str = Field(..., description="Bank account number under scrutiny")
    bank_name: str = Field(..., description="Bank denomination")
    in_degree: int = Field(..., description="Number of inward incoming transfer edges")
    out_degree: int = Field(..., description="Number of outward outgoing transfer edges")
    total_degree: int = Field(..., description="Sum of incoming and outgoing transfer edges")
    unique_senders: int = Field(..., description="Distinct source accounts sending funds")
    unique_receivers: int = Field(..., description="Distinct target accounts receiving funds")
    hub_typology: str = Field(..., description="FUNNEL_COLLECTOR, DISPERSION_HUB, HIGH_VELOCITY_PASSTHROUGH, HIGH_VOLUME")
    total_credit_volume: Decimal = Field(..., description="Total inward volume in INR")
    total_debit_volume: Decimal = Field(..., description="Total outward volume in INR")
    is_mule: bool = Field(False, description="Whether account is flagged as mule")
    explanation: str = Field(..., description="Human-readable investigative evidence summary")


class SuspiciousClusterEvidence(BaseModel):
    """Explainable evidence for criminal collusion clusters sharing infrastructure or cyclic transfers."""

    cluster_id: str = Field(..., description="Unique cluster or shared entity identifier")
    cluster_type: str = Field(..., description="SHARED_DEVICE_RING, SHARED_PHONE_RING, SHARED_UPI_SYNDICATE, CIRCULAR_TRANSFER_LOOP")
    member_accounts: List[str] = Field(..., description="List of accounts operating within the cluster")
    member_count: int = Field(..., description="Number of accounts in the ring")
    shared_identifier: str = Field(..., description="Hardware IMEI, phone number, or VPA binding the cluster")
    total_cluster_volume_inr: Decimal = Field(..., description="Combined financial velocity moved across members")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Calculated syndicate risk score")
    explanation: str = Field(..., description="Human-readable forensic justification")


class CashOutPathEvidence(BaseModel):
    """Explainable evidence for fund liquidation trails ending at physical ATM withdrawals."""

    origin_account: str = Field(..., description="Initial source or victim account")
    cashout_account: str = Field(..., description="Terminal mule account performing cash withdrawal")
    atm_id: str = Field(..., description="Physical ATM terminal hardware kiosk identifier")
    atm_location: str = Field(..., description="ATM kiosk location name, city, and state")
    withdrawn_amount_inr: Decimal = Field(..., description="Amount dispensed in cash")
    withdrawal_timestamp: str = Field(..., description="Timestamp of ATM cash withdrawal")
    intermediary_mules: List[str] = Field(default_factory=list, description="Ordered intermediate pass-through accounts")
    latency_hours: Optional[float] = Field(None, description="Hours between initial victim debit and ATM withdrawal")
    rapid_cashout: bool = Field(False, description="Flagged as rapid cash-out (< 3 hours from deposit)")
    explanation: str = Field(..., description="Human-readable forensic chain narrative")


class ComplaintConnectionEvidence(BaseModel):
    """Explainable evidence connecting NCRP complaints to suspect mule networks."""

    acknowledgement_no: str = Field(..., description="NCRP / 1930 Citizen complaint reference")
    category: str = Field(..., description="Scam typology category (e.g. digital arrest, UPI fraud)")
    reported_loss_inr: Decimal = Field(..., description="Citizen financial loss reported")
    connected_account: str = Field(..., description="Account number surfaced in connection with the complaint")
    connection_depth: int = Field(..., description="0 = Primary suspect named in complaint, 1 = Layer-1 recipient, 2 = Layer-2 beneficiary")
    connection_route: str = Field(..., description="DIRECT_REPORT, BENEFICIARY_TRANSFER, SHARED_INFRASTRUCTURE")
    complaint_reported_date: str = Field(..., description="Date complaint was filed on NCRP")
    suspect_upi: Optional[str] = Field(None, description="Suspect UPI handle in complaint")
    suspect_phone: Optional[str] = Field(None, description="Suspect caller phone number")
    explanation: str = Field(..., description="Human-readable investigative summary")


class ShortestPathEvidence(BaseModel):
    """Explainable shortest trail connecting two target entities in the risk graph."""

    source_entity: str = Field(..., description="Origin node identifier (Account, Victim, or Complaint)")
    target_entity: str = Field(..., description="Destination node identifier (Suspect, Mule, or ATM)")
    hop_count: int = Field(..., description="Number of edges traversed in the shortest path")
    path_nodes: List[Dict[str, Any]] = Field(..., description="Sequence of nodes in path with labels and properties")
    path_relationships: List[Dict[str, Any]] = Field(..., description="Sequence of edge details (type, amount, txn_id, timestamp)")
    total_amount_inr: Decimal = Field(..., description="Cumulative funds passed along the shortest trail")
    is_suspicious_path: bool = Field(False, description="Whether any intermediary node or edge is flagged suspicious")
    explanation: str = Field(..., description="Human-readable traversal explanation")
