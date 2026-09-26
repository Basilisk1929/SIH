"""Reference centroids and risk profiles for simulated Indian cybercrime clusters.

NOTE: Used strictly as spatial benchmarks for testing clustering algorithms on synthetic data.
"""

from typing import Dict, List, TypedDict


class HotspotInfo(TypedDict):
    name: str
    state: str
    lat: float
    lng: float
    primary_modus: str
    baseline_risk_weight: float


INDIAN_CYBER_REFERENCE_HUBS: List[HotspotInfo] = [
    {
        "name": "Mewat-Nuh Region",
        "state": "Haryana",
        "lat": 28.1128,
        "lng": 77.0017,
        "primary_modus": "OLX / Marketplace & Armed Impersonation",
        "baseline_risk_weight": 0.88,
    },
    {
        "name": "Jamtara-Karmatanr Hub",
        "state": "Jharkhand",
        "lat": 23.9614,
        "lng": 86.8016,
        "primary_modus": "Bank OTP Phishing & AnyDesk Screen Share",
        "baseline_risk_weight": 0.92,
    },
    {
        "name": "Bharatpur-Alwar Belt",
        "state": "Rajasthan",
        "lat": 27.2152,
        "lng": 77.5030,
        "primary_modus": "Sextortion & Fake Job Portals",
        "baseline_risk_weight": 0.84,
    },
    {
        "name": "Cyberabad-Hitech City",
        "state": "Telangana",
        "lat": 17.4435,
        "lng": 78.3772,
        "primary_modus": "Investment App & Task Telegram Scams",
        "baseline_risk_weight": 0.76,
    },
    {
        "name": "Noida Sector-62 Call Centers",
        "state": "Uttar Pradesh",
        "lat": 28.6280,
        "lng": 77.3649,
        "primary_modus": "Tech Support & IRS/CBI Impersonation",
        "baseline_risk_weight": 0.82,
    },
]
