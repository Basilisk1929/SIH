"""Natural language evidentiary explanation generator for predicted cash-out ATMs."""

from typing import Any, Dict, List


class CashoutExplainer:
    """Generates human-readable, evidence-based tactical reasons for ATM ranking."""

    @staticmethod
    def generate_explanations(candidate_dict: Dict[str, Any]) -> List[str]:
        """Produce tactical reason bullet points from engineered features."""
        features = candidate_dict.get("features", {})
        reasons: List[str] = []

        # 1. Proximity to Recent Activity
        dist_km = float(candidate_dict.get("distance_km", 0.0))
        if dist_km <= 1.5:
            reasons.append(f"Close to recent account activity ({dist_km:.1f} km)")
        elif dist_km <= 5.0:
            reasons.append(f"Within rapid transit distance ({dist_km:.1f} km from recent activity)")
        else:
            reasons.append(f"Accessible regional ATM outlet ({dist_km:.1f} km)")

        # 2. H3 Cell Cybercrime & Cash-out Risk
        cell_risk = float(features.get("h3_cell_risk", 0.0))
        h3_cell = str(candidate_dict.get("h3_cell", ""))
        if cell_risk >= 60.0:
            reasons.append(f"Elevated cash-out activity in H3 cell {h3_cell} (Risk score: {cell_risk:.1f})")
        elif cell_risk >= 30.0:
            reasons.append(f"Moderate spatial cybercrime density in H3 cell {h3_cell}")

        # 3. Known Cybercrime Corridor / DBSCAN Hotspot
        if candidate_dict.get("is_hotspot_adjacent"):
            city = candidate_dict.get("city", "")
            district = candidate_dict.get("district", "")
            loc_label = f" ({city})" if city else f" ({district})" if district else ""
            reasons.append(f"Located in known cybercrime surveillance corridor{loc_label}")

        # 4. Proximity to Prior Account Cash-Out Locations
        prior_dist = features.get("prior_cashout_dist_km")
        if prior_dist is not None:
            if prior_dist <= 3.0:
                reasons.append(f"Historical cash-out proximity ({prior_dist:.1f} km from prior withdrawal location)")
            elif prior_dist <= 8.0:
                reasons.append(f"Near account's historical cash-out corridor ({prior_dist:.1f} km)")

        # 5. Transaction Velocity Burst & Urgent Liquidation
        velocity = int(features.get("transactions_last_1h", 0))
        ratio = float(features.get("cashout_ratio", 0.0))
        if velocity >= 4:
            reasons.append(f"Current transaction burst ({velocity} txns in last 1h) indicates urgent cash-out dissipation")
        elif ratio >= 0.7:
            reasons.append(f"Elevated cash-out ratio ({ratio:.0%}) signals imminent physical cash withdrawal")

        # 6. ATM / Outlet Characteristics
        outlet_type = str(candidate_dict.get("outlet_type", "ON_SITE_ATM"))
        bank_name = str(candidate_dict.get("bank_name", "Scheduled Commercial Bank"))

        if outlet_type == "CASH_RECYCLER":
            reasons.append("High-throughput 24/7 cash recycler (CRM) with elevated withdrawal limits")
        elif outlet_type == "OFF_SITE_ATM":
            reasons.append("Unmanned off-site ATM providing 24/7 cash withdrawal access")
        elif outlet_type == "WHITE_LABEL_ATM":
            reasons.append(f"White-label ATM ({bank_name}) in high-cash turnover corridor")
        elif outlet_type == "ON_SITE_ATM":
            reasons.append(f"Operational on-site ATM operated by {bank_name}")

        return reasons
