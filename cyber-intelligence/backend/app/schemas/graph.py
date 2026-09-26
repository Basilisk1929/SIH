"""Pydantic schemas for Neo4j graph nodes, edges, and subgraphs."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str  # BankAccount, UPI_ID, Phone, Device, Complaint, MuleRing
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str  # TRANSFERRED_TO, LINKED_PHONE, ACCESSED_FROM_DEVICE, ASSOCIATED_WITH
    properties: Dict[str, Any] = Field(default_factory=dict)


class SubgraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    node_count: int
    edge_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MulePathHop(BaseModel):
    hop_number: int
    sender_account: str
    receiver_account: str
    amount_inr: float
    time_delta_seconds: Optional[int] = None
    rail_type: str


class MuleChainResponse(BaseModel):
    origin_complaint_ack: str
    victim_initial_outflow: float
    detected_hops: List[MulePathHop]
    total_hops: int
    layer_3_cashout_detected: bool
    suspect_accounts: List[str]
