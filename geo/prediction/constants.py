"""Constants, scoring weights, and statutory disclaimers for Cash-Out Location Prediction."""

from typing import Dict

# Candidate ATM Search Defaults
DEFAULT_CANDIDATE_RADIUS_KM: float = 15.0
MAX_CANDIDATE_RADIUS_KM: float = 50.0
MIN_CANDIDATE_RADIUS_KM: float = 1.0
DEFAULT_PREDICTION_TOP_K: int = 5
MAX_PREDICTION_TOP_K: int = 25

# Multi-Factor Scoring Weights (Sum to 1.0)
# Proximity is the dominant physical constraint for urgent mule cash-outs
WEIGHT_DISTANCE: float = 0.35
WEIGHT_H3_RISK: float = 0.20
WEIGHT_HOTSPOT: float = 0.15
WEIGHT_OUTLET_PROFILE: float = 0.10
WEIGHT_TEMPORAL: float = 0.10
WEIGHT_BURST_URGENCY: float = 0.10

# Outlet Typology Feasibility Weights (0.0 to 1.0)
# Off-site and cash recyclers provide 24/7 liquidity with reduced branch surveillance
OUTLET_FEASIBILITY_WEIGHTS: Dict[str, float] = {
    "CASH_RECYCLER": 1.00,       # High cash availability, high limits, 24/7
    "OFF_SITE_ATM": 0.90,        # Unmanned, 24/7 access, lower physical guard density
    "WHITE_LABEL_ATM": 0.85,     # Common in rural/semi-urban cashout corridors
    "ON_SITE_ATM": 0.70,         # Branch-attached, security guards often present
    "BANK_BRANCH": 0.35,         # Counter service only during banking hours
}

# Bank Category Risk Propensity (Relative weighting for cash liquidity)
BANK_CATEGORY_WEIGHTS: Dict[str, float] = {
    "PUBLIC_SECTOR": 1.00,       # Deepest cash availability & widest network
    "PRIVATE_SECTOR": 0.95,      # High density urban/metro coverage
    "SMALL_FINANCE": 0.80,       # Semi-urban presence
    "WHITE_LABEL": 0.90,         # High presence in cashout hubs (e.g. Mewat, Bharatpur)
    "REGIONAL_RURAL": 0.75,
}

# Distance Decay Parameters
# Exponential decay scale lambda: half-life ~ 2.5 km
DISTANCE_DECAY_SCALE_KM: float = 2.5

# Statutory Notice & Explicit Data Limitation
CASHOUT_DATA_LIMITATION_DISCLAIMER: str = (
    "DISCLAIMER & DATA LIMITATION: This cash-out location prediction model is an investigative "
    "prototype evaluated on synthetic financial transactions and Reserve Bank of India (RBI) ATM outlet "
    "registries. PaySim and synthetic transaction benchmarks do not contain genuine Indian ATM-level "
    "destination identifiers. Predictions represent tactical likelihood ranking based on spatial proximity, "
    "H3 cybercrime cell risk, outlet accessibility, and transaction velocity. It must NOT be claimed that this "
    "prediction identifies the actual ATM used for criminal cash withdrawal."
)
