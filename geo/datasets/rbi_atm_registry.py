"""Reserve Bank of India (RBI) Bank Branch & ATM Outlets Registry for Indian Geography.

Supports real Indian geographic distributions of bank branches, on-site/off-site ATMs,
cash recyclers (CRMs), and White-Label ATM (WLA) operators across Public, Private,
Small Finance, and Regional Rural Banks.
"""

from dataclasses import asdict, dataclass
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from geo.constants import EARTH_RADIUS_KM
from geo.indexing.h3_indexer import H3Indexer
from geo.validation.coordinate_validator import CoordinateValidator


@dataclass
class BankOutlet:
    outlet_id: str
    bank_name: str
    bank_code: str
    outlet_type: str  # ON_SITE_ATM, OFF_SITE_ATM, CASH_RECYCLER, BANK_BRANCH, WHITE_LABEL_ATM
    bank_category: str  # PUBLIC_SECTOR, PRIVATE_SECTOR, SMALL_FINANCE, REGIONAL_RURAL, WHITE_LABEL
    center_city: str
    district: str
    state: str
    pincode: str
    population_group: str  # METROPOLITAN, URBAN, SEMI_URBAN, RURAL
    latitude: float
    longitude: float
    h3_cell_res7: str
    is_operational: bool = True
    cash_dispenser_active: bool = True
    is_hotspot_adjacent: bool = False


# Curated Seed Centroids for Indian Banking Centers and Cybercrime Triage Zones
INDIAN_BANKING_CENTERS = [
    # Metros & Commercial Capitals
    {"city": "Mumbai", "district": "Mumbai City", "state": "Maharashtra", "lat": 18.9220, "lng": 72.8347, "pop": "METROPOLITAN", "pin": "400001", "hotspot": False},
    {"city": "Bandra-Kurla Complex", "district": "Mumbai Suburban", "state": "Maharashtra", "lat": 19.0657, "lng": 72.8687, "pop": "METROPOLITAN", "pin": "400051", "hotspot": False},
    {"city": "New Delhi - Connaught Place", "district": "New Delhi", "state": "Delhi", "lat": 28.6315, "lng": 77.2167, "pop": "METROPOLITAN", "pin": "110001", "hotspot": False},
    {"city": "South Delhi - Nehru Place", "district": "South Delhi", "state": "Delhi", "lat": 28.5494, "lng": 77.2528, "pop": "METROPOLITAN", "pin": "110019", "hotspot": False},
    {"city": "Bengaluru - MG Road", "district": "Bengaluru Urban", "state": "Karnataka", "lat": 12.9756, "lng": 77.6066, "pop": "METROPOLITAN", "pin": "560001", "hotspot": False},
    {"city": "Bengaluru - Whitefield", "district": "Bengaluru Urban", "state": "Karnataka", "lat": 12.9698, "lng": 77.7500, "pop": "METROPOLITAN", "pin": "560066", "hotspot": False},
    {"city": "Hyderabad - Banjara Hills", "district": "Hyderabad", "state": "Telangana", "lat": 17.4156, "lng": 78.4350, "pop": "METROPOLITAN", "pin": "500034", "hotspot": False},
    {"city": "Kolkata - BBD Bagh", "district": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lng": 88.3639, "pop": "METROPOLITAN", "pin": "700001", "hotspot": False},
    {"city": "Chennai - Anna Salai", "district": "Chennai", "state": "Tamil Nadu", "lat": 13.0604, "lng": 80.2496, "pop": "METROPOLITAN", "pin": "600002", "hotspot": False},
    {"city": "Ahmedabad - Ashram Road", "district": "Ahmedabad", "state": "Gujarat", "lat": 23.0338, "lng": 72.5694, "pop": "METROPOLITAN", "pin": "380009", "hotspot": False},
    {"city": "Pune - Shivajinagar", "district": "Pune", "state": "Maharashtra", "lat": 18.5314, "lng": 73.8446, "pop": "METROPOLITAN", "pin": "411005", "hotspot": False},

    # Cybercrime Surveillance Hubs & Cashout Corridors
    {"city": "Jamtara-Karmatanr", "district": "Jamtara", "state": "Jharkhand", "lat": 23.9614, "lng": 86.8016, "pop": "RURAL", "pin": "815351", "hotspot": True},
    {"city": "Mewat-Nuh", "district": "Nuh", "state": "Haryana", "lat": 28.1128, "lng": 77.0017, "pop": "RURAL", "pin": "122107", "hotspot": True},
    {"city": "Bharatpur-Deeg", "district": "Bharatpur", "state": "Rajasthan", "lat": 27.2152, "lng": 77.5030, "pop": "SEMI_URBAN", "pin": "321001", "hotspot": True},
    {"city": "Alwar-Ramgarh", "district": "Alwar", "state": "Rajasthan", "lat": 27.5530, "lng": 76.6346, "pop": "SEMI_URBAN", "pin": "301001", "hotspot": True},
    {"city": "Cyberabad - Hitec City", "district": "Hyderabad", "state": "Telangana", "lat": 17.4435, "lng": 78.3772, "pop": "URBAN", "pin": "500081", "hotspot": True},
    {"city": "Noida Sector-62", "district": "Gautam Buddha Nagar", "state": "Uttar Pradesh", "lat": 28.6280, "lng": 77.3649, "pop": "URBAN", "pin": "201309", "hotspot": True},
    {"city": "Bidhannagar Salt Lake", "district": "North 24 Parganas", "state": "West Bengal", "lat": 22.5804, "lng": 88.4174, "pop": "URBAN", "pin": "700091", "hotspot": True},

    # Regional Banking Hubs
    {"city": "Lucknow - Hazratganj", "district": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lng": 80.9462, "pop": "URBAN", "pin": "226001", "hotspot": False},
    {"city": "Patna - Gandhi Maidan", "district": "Patna", "state": "Bihar", "lat": 25.6186, "lng": 85.1444, "pop": "URBAN", "pin": "800001", "hotspot": False},
    {"city": "Ranchi - Main Road", "district": "Ranchi", "state": "Jharkhand", "lat": 23.3441, "lng": 85.3096, "pop": "URBAN", "pin": "834001", "hotspot": False},
    {"city": "Jaipur - MI Road", "district": "Jaipur", "state": "Rajasthan", "lat": 26.9168, "lng": 75.8115, "pop": "URBAN", "pin": "302001", "hotspot": False},
    {"city": "Gurugram - Cyber City", "district": "Gurugram", "state": "Haryana", "lat": 28.4950, "lng": 77.0895, "pop": "URBAN", "pin": "122002", "hotspot": False},
    {"city": "Faridabad", "district": "Faridabad", "state": "Haryana", "lat": 28.4089, "lng": 77.3178, "pop": "URBAN", "pin": "121001", "hotspot": False},
]

BANKS_CATALOG = [
    {"name": "State Bank of India", "code": "SBI", "cat": "PUBLIC_SECTOR"},
    {"name": "Punjab National Bank", "code": "PNB", "cat": "PUBLIC_SECTOR"},
    {"name": "Bank of Baroda", "code": "BOB", "cat": "PUBLIC_SECTOR"},
    {"name": "Canara Bank", "code": "CANARA", "cat": "PUBLIC_SECTOR"},
    {"name": "Union Bank of India", "code": "UBI", "cat": "PUBLIC_SECTOR"},
    {"name": "HDFC Bank", "code": "HDFC", "cat": "PRIVATE_SECTOR"},
    {"name": "ICICI Bank", "code": "ICICI", "cat": "PRIVATE_SECTOR"},
    {"name": "Axis Bank", "code": "AXIS", "cat": "PRIVATE_SECTOR"},
    {"name": "Kotak Mahindra Bank", "code": "KOTAK", "cat": "PRIVATE_SECTOR"},
    {"name": "IndusInd Bank", "code": "INDUS", "cat": "PRIVATE_SECTOR"},
    {"name": "AU Small Finance Bank", "code": "AU_SFB", "cat": "SMALL_FINANCE"},
    {"name": "Tata Indicash White-Label", "code": "INDICASH", "cat": "WHITE_LABEL"},
    {"name": "India1 Payments WLA", "code": "INDIA1", "cat": "WHITE_LABEL"},
]


class RBIAtmRegistry:
    """In-memory and file-backed repository for Indian bank branches and ATM outlets."""

    def __init__(self, csv_path: Optional[str] = None):
        self.csv_path = (
            Path(csv_path)
            if csv_path
            else Path("/Users/ronitsingh/Anti/SIH/data/rbi/rbi_atm_outlets.csv")
        )
        self._df: Optional[pd.DataFrame] = None
        self._load_or_generate()

    def _load_or_generate(self) -> None:
        """Load outlets from CSV if available, or generate a realistic dataset."""
        if self.csv_path.exists():
            df = pd.read_csv(self.csv_path)
            self._df = df
            return

        # Generate realistic distribution
        outlets: List[BankOutlet] = []
        counter = 1

        for center in INDIAN_BANKING_CENTERS:
            base_lat = center["lat"]
            base_lng = center["lng"]
            city = center["city"]
            district = center["district"]
            state = center["state"]
            pop_group = center["pop"]
            pincode = center["pin"]
            is_hotspot = center["hotspot"]

            # Each center has 10-18 outlets across major banks and types
            num_outlets = 16 if is_hotspot or pop_group == "METROPOLITAN" else 10
            for i in range(num_outlets):
                bank = BANKS_CATALOG[i % len(BANKS_CATALOG)]
                
                # Offset coordinate slightly within 1.5 km of center
                angle = (i * 2.0 * math.pi) / num_outlets
                dist_km = 0.15 + (i * 0.08)
                # approx 1 deg lat = 111 km, 1 deg lng = 111 * cos(lat) km
                d_lat = (dist_km * math.cos(angle)) / 111.0
                d_lng = (dist_km * math.sin(angle)) / (111.0 * math.cos(math.radians(base_lat)))

                lat = round(base_lat + d_lat, 6)
                lng = round(base_lng + d_lng, 6)

                outlet_type = (
                    "ON_SITE_ATM" if i % 4 == 0
                    else "OFF_SITE_ATM" if i % 4 == 1
                    else "CASH_RECYCLER" if i % 4 == 2
                    else "WHITE_LABEL_ATM" if bank["cat"] == "WHITE_LABEL"
                    else "BANK_BRANCH"
                )

                h3_cell = H3Indexer.point_to_h3(lat, lng, resolution=7, validate=False)
                outlet = BankOutlet(
                    outlet_id=f"RBI_OUTLET_{counter:06d}",
                    bank_name=bank["name"],
                    bank_code=bank["code"],
                    outlet_type=outlet_type,
                    bank_category=bank["cat"],
                    center_city=city,
                    district=district,
                    state=state,
                    pincode=pincode,
                    population_group=pop_group,
                    latitude=lat,
                    longitude=lng,
                    h3_cell_res7=h3_cell,
                    is_operational=True,
                    cash_dispenser_active=outlet_type != "BANK_BRANCH",
                    is_hotspot_adjacent=is_hotspot,
                )
                outlets.append(outlet)
                counter += 1

        self._df = pd.DataFrame([asdict(o) for o in outlets])
        # Save to disk for persistence
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self._df.to_csv(self.csv_path, index=False)

    @property
    def dataframe(self) -> pd.DataFrame:
        """Access underlying DataFrame of bank and ATM outlets."""
        if self._df is None:
            self._load_or_generate()
        return self._df.copy()

    def get_all_outlets(self) -> pd.DataFrame:
        """Return all registered outlets."""
        return self.dataframe

    def get_atms_only(self) -> pd.DataFrame:
        """Filter to operational cash-dispensing outlets (ATMs and Cash Recyclers)."""
        df = self.dataframe
        return df[df["cash_dispenser_active"] & df["is_operational"]].copy()

    def get_outlets_in_h3(self, h3_cell: str) -> pd.DataFrame:
        """Find all outlets located within a specified H3 cell (res 7)."""
        df = self.dataframe
        return df[df["h3_cell_res7"] == str(h3_cell).strip()].copy()

    def get_outlets_in_state(self, state: str) -> pd.DataFrame:
        """Filter outlets by Indian state."""
        df = self.dataframe
        return df[df["state"].str.lower() == state.strip().lower()].copy()

    def find_nearest_atms(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find the nearest cash-dispensing ATMs to a given coordinate."""
        atms_df = self.get_atms_only()
        if atms_df.empty:
            return []

        results: List[Dict[str, Any]] = []
        for _, row in atms_df.iterrows():
            atm_lat = row["latitude"]
            atm_lng = row["longitude"]

            # Haversine distance
            dlat = math.radians(atm_lat - lat)
            dlng = math.radians(atm_lng - lng)
            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(math.radians(lat))
                * math.cos(math.radians(atm_lat))
                * math.sin(dlng / 2) ** 2
            )
            dist_km = EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            if dist_km <= radius_km:
                atm_info = row.to_dict()
                atm_info["city"] = atm_info.get("center_city")
                atm_info["distance_km"] = round(dist_km, 3)
                atm_info["distance_meters"] = round(dist_km * 1000.0, 1)
                results.append(atm_info)

        # Sort by distance
        results.sort(key=lambda x: x["distance_km"])
        return results[:top_k]
