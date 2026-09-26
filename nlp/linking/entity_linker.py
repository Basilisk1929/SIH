"""Entity linking module resolving normalized extracted entities to synthetic knowledge bases."""

import csv
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from nlp.normalizers.entity_normalizer import NormalizedEntity

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SYNTHETIC_DATA_DIR = PROJECT_ROOT / "data" / "synthetic"


class EntityLinker:
    """Links normalized entity tokens to synthetic cybercrime and banking registries."""

    def __init__(self, data_dir: Path = SYNTHETIC_DATA_DIR):
        self.data_dir = data_dir
        self._accounts_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._upi_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._phone_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._banks_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._locations_cache: Optional[Dict[str, Dict[str, Any]]] = None

    def _load_caches(self) -> None:
        """Lazily load lookup dictionaries from synthetic CSV files if available."""
        if self._accounts_cache is not None:
            return

        self._accounts_cache = {}
        self._upi_cache = {}
        self._phone_cache = {}
        self._banks_cache = {}
        self._locations_cache = {}

        # 1. Accounts
        acc_path = self.data_dir / "accounts" / "bank_accounts.csv"
        if acc_path.exists():
            try:
                with open(acc_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self._accounts_cache[row["account_number"]] = {
                            "account_number": row["account_number"],
                            "customer_id": row["customer_id"],
                            "bank_name": row["bank_name"],
                            "ifsc_code": row["ifsc_code"],
                            "is_mule": row["is_mule"].lower() == "true",
                            "mule_tier": int(row["mule_tier"]) if row["mule_tier"].isdigit() else 0,
                            "cluster_id": row["cluster_id"],
                        }
            except Exception as e:
                logger.warning(f"Error loading accounts cache for linking: {e}")

        # 2. UPI IDs
        upi_path = self.data_dir / "entities" / "upi_ids.csv"
        if upi_path.exists():
            try:
                with open(upi_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self._upi_cache[row["vpa"].lower()] = {
                            "vpa": row["vpa"],
                            "account_number": row["account_number"],
                            "linked_phone": row["linked_phone_number"],
                            "psp_handle": row["psp_handle"],
                            "is_suspicious": row["is_suspicious"].lower() == "true",
                        }
            except Exception as e:
                logger.warning(f"Error loading UPI cache for linking: {e}")

        # 3. Phone Numbers
        phone_path = self.data_dir / "entities" / "phone_numbers.csv"
        if phone_path.exists():
            try:
                with open(phone_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self._phone_cache[row["phone_number"]] = {
                            "phone_number": row["phone_number"],
                            "operator": row["operator"],
                            "circle": row["circle"],
                            "customer_id": row["customer_id"],
                            "is_suspect": row["is_suspect"].lower() == "true",
                            "cluster_id": row["cluster_id"],
                        }
            except Exception as e:
                logger.warning(f"Error loading phone cache for linking: {e}")

        # 4. Bank Registry
        from data.generators.vocabularies import SYNTHETIC_BANKS
        for code, name, cat in SYNTHETIC_BANKS:
            self._banks_cache[name.lower()] = {
                "bank_code": code,
                "bank_name": name,
                "category": cat,
                "is_known_entity": True,
            }

        # 5. Locations
        loc_path = self.data_dir / "entities" / "locations.csv"
        if loc_path.exists():
            try:
                with open(loc_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        city_key = row["city"].lower()
                        is_hotspot_str = row.get("is_cyber_hotspot") or row.get("is_cybercrime_hotspot", "false")
                        self._locations_cache[city_key] = {
                            "location_id": row["location_id"],
                            "city": row["city"],
                            "state": row["state"],
                            "latitude": float(row["latitude"]),
                            "longitude": float(row["longitude"]),
                            "is_cybercrime_hotspot": is_hotspot_str.lower() == "true",
                        }
            except Exception as e:
                logger.warning(f"Error loading locations cache for linking: {e}")

    def link_entity(self, entity: NormalizedEntity) -> NormalizedEntity:
        """Resolve normalized entity against knowledge base dictionaries."""
        self._load_caches()

        lbl = entity.label
        val = entity.normalized_value

        linked: Optional[Dict[str, Any]] = None

        if lbl == "ACCOUNT" and isinstance(val, str):
            record = self._accounts_cache.get(val)
            if record:
                linked = {
                    "entity_type": "Account",
                    "account_number": record["account_number"],
                    "bank_name": record["bank_name"],
                    "is_mule": record["is_mule"],
                    "mule_tier": record["mule_tier"],
                    "cluster_id": record["cluster_id"],
                    "is_known_entity": True,
                }
            else:
                linked = {"entity_type": "Account", "is_known_entity": False}

        elif lbl == "UPI_ID" and isinstance(val, str):
            record = self._upi_cache.get(val.lower())
            if record:
                linked = {
                    "entity_type": "UPI",
                    "vpa": record["vpa"],
                    "linked_account": record["account_number"],
                    "is_suspicious": record["is_suspicious"],
                    "is_known_entity": True,
                }
            else:
                linked = {"entity_type": "UPI", "is_known_entity": False}

        elif lbl == "PHONE" and isinstance(val, str):
            record = self._phone_cache.get(val)
            if record:
                linked = {
                    "entity_type": "Phone",
                    "phone_number": record["phone_number"],
                    "operator": record["operator"],
                    "circle": record["circle"],
                    "is_suspect": record["is_suspect"],
                    "cluster_id": record["cluster_id"],
                    "is_known_entity": True,
                }
            else:
                linked = {"entity_type": "Phone", "is_known_entity": False}

        elif lbl == "BANK" and isinstance(val, str):
            record = self._banks_cache.get(val.lower())
            if record:
                linked = {
                    "entity_type": "Bank",
                    "bank_code": record["bank_code"],
                    "bank_name": record["bank_name"],
                    "category": record["category"],
                    "is_known_entity": True,
                }
            else:
                linked = {"entity_type": "Bank", "is_known_entity": False}

        elif lbl == "LOCATION" and isinstance(val, str):
            record = self._locations_cache.get(val.lower())
            if record:
                linked = {
                    "entity_type": "Location",
                    "city": record["city"],
                    "state": record["state"],
                    "latitude": record["latitude"],
                    "longitude": record["longitude"],
                    "is_cybercrime_hotspot": record["is_cybercrime_hotspot"],
                    "is_known_entity": True,
                }
            else:
                linked = {"entity_type": "Location", "is_known_entity": False}

        entity.linked_entity = linked
        return entity
