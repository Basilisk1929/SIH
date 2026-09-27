"""Unit and integration tests for Cash-Out Location Prediction subsystem."""

from fastapi.testclient import TestClient
import pytest

from geo.api.service import app
from geo.datasets.rbi_atm_registry import RBIAtmRegistry
from geo.intelligence import GeospatialIntelligenceEngine
from geo.prediction.candidate_generator import CandidateATMGenerator
from geo.prediction.constants import (
    CASHOUT_DATA_LIMITATION_DISCLAIMER,
    DEFAULT_CANDIDATE_RADIUS_KM,
)
from geo.prediction.explainer import CashoutExplainer
from geo.prediction.feature_engineering import CashoutFeatureExtractor
from geo.prediction.predictor import CashoutLocationPredictor
from geo.prediction.schemas import (
    CashoutPredictionRequest,
    CashoutPredictionResponse,
    PredictedATM,
)
from geo.prediction.scorer import CashoutLocationScorer
from geo.prediction.synthetic_linkage import SyntheticCashoutLinkage

client = TestClient(app)


@pytest.fixture(scope="module")
def geo_engine():
    eng = GeospatialIntelligenceEngine()
    eng.load_synthetic_data()
    return eng


@pytest.fixture(scope="module")
def predictor(geo_engine):
    return CashoutLocationPredictor(rbi_registry=geo_engine.rbi_registry, geo_engine=geo_engine)


# ==============================================================================
# 1. CANDIDATE GENERATION & FILTERING TESTS
# ==============================================================================

def test_anchor_resolution_explicit_coordinates():
    gen = CandidateATMGenerator()
    res = gen.resolve_anchor_point(current_lat=28.6139, current_lng=77.2090)
    assert res["latitude"] == 28.6139
    assert res["longitude"] == 77.2090
    assert res["source"] == "explicit_current_location"


def test_anchor_resolution_from_recent_transactions():
    gen = CandidateATMGenerator()
    txns = [
        {"transaction_id": "TX1", "amount": 1000.0},
        {"transaction_id": "TX2", "latitude": 19.0760, "longitude": 72.8777, "timestamp": "2026-09-26T10:00:00Z"},
    ]
    res = gen.resolve_anchor_point(recent_transactions=txns)
    assert res["latitude"] == 19.076
    assert res["longitude"] == 72.8777
    assert res["source"] == "recent_transaction_latest"


def test_anchor_resolution_failure_raises_value_error():
    gen = CandidateATMGenerator()
    with pytest.raises(ValueError, match="Unable to resolve geographic anchor"):
        gen.resolve_anchor_point(recent_transactions=[{"amount": 500.0}])


def test_candidate_atms_filtering_within_radius():
    gen = CandidateATMGenerator()
    # Query Connaught Place, New Delhi
    candidates = gen.generate_candidate_atms(
        anchor_lat=28.6315,
        anchor_lng=77.2167,
        candidate_radius_km=5.0,
    )
    assert len(candidates) > 0
    for cand in candidates:
        assert cand["distance_km"] <= 5.0
        assert "atm_id" in cand
        assert "bank_name" in cand
        assert "outlet_type" in cand
        assert cand["outlet_type"] in ["ON_SITE_ATM", "OFF_SITE_ATM", "CASH_RECYCLER", "WHITE_LABEL_ATM"]


def test_candidate_filtering_empty_when_remote():
    gen = CandidateATMGenerator()
    # Remote location in Thar Desert far from banking centers with tiny 0.5 km radius
    candidates = gen.generate_candidate_atms(
        anchor_lat=27.0,
        anchor_lng=71.0,
        candidate_radius_km=0.5,
    )
    assert len(candidates) == 0


# ==============================================================================
# 2. FEATURE ENGINEERING TESTS
# ==============================================================================

def test_feature_extractor_distance_decay(geo_engine):
    extractor = CashoutFeatureExtractor(geo_engine=geo_engine)
    cand_close = {"distance_km": 0.5, "latitude": 28.6315, "longitude": 77.2167}
    cand_far = {"distance_km": 8.0, "latitude": 28.7000, "longitude": 77.3000}

    feats_close = extractor.extract_features(cand_close, 28.6315, 77.2167)
    feats_far = extractor.extract_features(cand_far, 28.6315, 77.2167)

    assert feats_close["dist_score"] > feats_far["dist_score"]


def test_feature_extractor_prior_cashout_proximity(geo_engine):
    extractor = CashoutFeatureExtractor(geo_engine=geo_engine)
    cand = {"distance_km": 1.2, "latitude": 28.6300, "longitude": 77.2150}

    # Case A: Past cashout nearby
    txns_with_co = [
        {"transaction_type": "CASH_OUT", "latitude": 28.6310, "longitude": 77.2160}
    ]
    feats_with_co = extractor.extract_features(cand, 28.6300, 77.2150, recent_transactions=txns_with_co)
    assert feats_with_co["prior_cashout_dist_km"] is not None
    assert feats_with_co["prior_cashout_dist_km"] < 1.0
    assert feats_with_co["prior_cashout_score"] > 0.7

    # Case B: No prior cashouts in history
    feats_no_co = extractor.extract_features(cand, 28.6300, 77.2150, recent_transactions=[])
    assert feats_no_co["prior_cashout_dist_km"] is None
    assert feats_no_co["prior_cashout_score"] == 0.5


def test_feature_extractor_urgency_burst(geo_engine):
    extractor = CashoutFeatureExtractor(geo_engine=geo_engine)
    cand = {"distance_km": 1.0, "latitude": 28.6315, "longitude": 77.2167}

    feats_urgent = extractor.extract_features(cand, 28.6315, 77.2167, transactions_last_1h=12, cashout_ratio=0.95)
    feats_calm = extractor.extract_features(cand, 28.6315, 77.2167, transactions_last_1h=0, cashout_ratio=0.1)

    assert feats_urgent["velocity_urgency"] > feats_calm["velocity_urgency"]


# ==============================================================================
# 3. SCORING & RANKING TESTS
# ==============================================================================

def test_scorer_monotonicity():
    cand_high = {
        "candidate": {"atm_id": "ATM_1", "bank_name": "SBI", "distance_km": 0.8},
        "features": {
            "dist_score": 0.95,
            "h3_risk_score": 0.85,
            "hotspot_score": 0.90,
            "atm_characteristics_score": 1.0,
            "time_of_day_score": 0.90,
            "day_of_week_score": 0.85,
            "velocity_urgency": 1.0,
            "distance_km": 0.8,
            "transactions_last_1h": 8,
            "is_hotspot_adjacent": True,
            "prior_cashout_dist_km": 1.2,
        },
    }
    cand_low = {
        "candidate": {"atm_id": "ATM_2", "bank_name": "PNB", "distance_km": 12.0},
        "features": {
            "dist_score": 0.20,
            "h3_risk_score": 0.15,
            "hotspot_score": 0.35,
            "atm_characteristics_score": 0.6,
            "time_of_day_score": 0.50,
            "day_of_week_score": 0.60,
            "velocity_urgency": 0.4,
            "distance_km": 12.0,
            "transactions_last_1h": 0,
            "is_hotspot_adjacent": False,
            "prior_cashout_dist_km": None,
        },
    }

    score_high = CashoutLocationScorer.score_candidate(cand_high["features"])
    score_low = CashoutLocationScorer.score_candidate(cand_low["features"])

    assert score_high > score_low
    assert 50.0 <= score_high <= 98.5
    assert 5.0 <= score_low <= 50.0

    ranked = CashoutLocationScorer.rank_candidates([cand_low, cand_high], top_k=2)
    assert ranked[0]["atm_id"] == "ATM_1"
    assert ranked[0]["rank"] == 1
    assert ranked[1]["atm_id"] == "ATM_2"
    assert ranked[1]["rank"] == 2


# ==============================================================================
# 4. EXPLANATION GENERATION TESTS
# ==============================================================================

def test_explanation_generation_content():
    cand_dict = {
        "atm_id": "ATM_102",
        "bank_name": "State Bank of India",
        "outlet_type": "CASH_RECYCLER",
        "distance_km": 1.2,
        "h3_cell": "873da1146ffffff",
        "is_hotspot_adjacent": True,
        "city": "Noida",
        "features": {
            "h3_cell_risk": 78.5,
            "transactions_last_1h": 6,
            "cashout_ratio": 0.88,
            "prior_cashout_dist_km": 1.5,
        },
    }
    reasons = CashoutExplainer.generate_explanations(cand_dict)
    assert len(reasons) >= 4
    # Verify reasons reflect the example in user requirements
    assert any("Close to recent account activity" in r for r in reasons)
    assert any("Elevated cash-out activity in H3 cell" in r for r in reasons)
    assert any("Historical cash-out proximity" in r for r in reasons)
    assert any("Current transaction burst" in r for r in reasons)
    assert any("cash recycler" in r.lower() for r in reasons)


# ==============================================================================
# 5. END-TO-END PREDICTOR TESTS
# ==============================================================================

def test_predictor_full_flow(predictor):
    request = CashoutPredictionRequest(
        account_id="SYN1000004465",
        current_latitude=28.6280,
        current_longitude=77.3649,  # Noida Sector-62 Cyber Corridor
        candidate_radius_km=10.0,
        top_k=3,
        account_risk_score=92.0,
        cashout_ratio=0.94,
        transactions_last_1h=8,
    )

    response = predictor.predict(request)

    assert isinstance(response, CashoutPredictionResponse)
    assert response.account_id == "SYN1000004465"
    assert response.total_candidates_evaluated > 0
    assert len(response.predicted_atms) == 3
    assert response.urgency_level == "CRITICAL"
    assert "DISCLAIMER & DATA LIMITATION" in response.disclaimer

    # Verify fields of top predicted ATM
    top_atm = response.predicted_atms[0]
    assert top_atm.rank == 1
    assert top_atm.prediction_score > 50.0
    assert top_atm.distance_km <= 10.0
    assert len(top_atm.explanations) > 0
    assert top_atm.atm_id is not None
    assert top_atm.bank_name is not None
    assert top_atm.latitude is not None
    assert top_atm.longitude is not None


def test_predictor_via_recent_transactions(predictor):
    request = CashoutPredictionRequest(
        account_id="SYN1000009999",
        recent_transactions=[
            {
                "transaction_id": "TXN_A",
                "latitude": 18.9220,
                "longitude": 72.8347,  # Mumbai City
                "amount": 45000.0,
                "transaction_type": "TRANSFER",
            },
            {
                "transaction_id": "TXN_B",
                "latitude": 18.9230,
                "longitude": 72.8350,
                "amount": 20000.0,
                "transaction_type": "CASH_OUT",
            },
        ],
        candidate_radius_km=8.0,
        top_k=5,
    )

    response = predictor.predict(request)
    assert response.total_candidates_evaluated > 0
    assert len(response.predicted_atms) <= 5
    assert response.anchor_location["source"] == "recent_transaction_latest"
    assert response.predicted_atms[0].rank == 1


# ==============================================================================
# 6. FASTAPI REST API TESTS
# ==============================================================================

def test_api_predict_cashout_location():
    payload = {
        "account_id": "SYN1000008888",
        "current_latitude": 28.6315,
        "current_longitude": 77.2167,
        "candidate_radius_km": 10.0,
        "top_k": 3,
        "account_risk_score": 85.0,
        "cashout_ratio": 0.90,
        "transactions_last_1h": 5,
    }

    res = client.post("/geo/predict-cashout-location", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["account_id"] == "SYN1000008888"
    assert "prediction_timestamp" in data
    assert "anchor_location" in data
    assert "predicted_atms" in data
    assert len(data["predicted_atms"]) == 3

    top = data["predicted_atms"][0]
    assert "atm_id" in top
    assert "bank_name" in top
    assert "latitude" in top
    assert "longitude" in top
    assert "distance_km" in top
    assert "prediction_score" in top
    assert "rank" in top
    assert "explanations" in top
    assert len(top["explanations"]) >= 1

    assert "disclaimer" in data
    assert "identifies the actual ATM" in data["disclaimer"]
    assert "DISCLAIMER & DATA LIMITATION" in data["disclaimer"]


def test_api_predict_cashout_location_invalid_coords():
    # Outside India coordinate
    payload = {
        "account_id": "SYN1000008888",
        "current_latitude": 0.0,
        "current_longitude": 0.0,
    }
    res = client.post("/geo/predict-cashout-location", json=payload)
    assert res.status_code == 400


def test_api_synthetic_linkage_metadata():
    res = client.get("/geo/prediction/linkage-metadata")
    assert res.status_code == 200
    data = res.json()
    assert data["is_synthetic_benchmark"] is True
    assert data["is_real_indian_atm_logs"] is False
    assert "PaySim" in data["source_transaction_dataset"]
    assert "Reserve Bank of India" in data["source_atm_registry"]


# ==============================================================================
# 7. SYNTHETIC LINKAGE & DATA LIMITATION TESTS
# ==============================================================================

def test_synthetic_cashout_linkage_module():
    linkage = SyntheticCashoutLinkage()
    meta = linkage.get_metadata()

    assert meta["is_synthetic_benchmark"] is True
    assert meta["is_real_indian_atm_logs"] is False
    assert CASHOUT_DATA_LIMITATION_DISCLAIMER in meta["disclaimer"]

    # Verify correlations run without exceptions
    correlations = linkage.extract_synthetic_cashout_correlations(max_events=50)
    assert "status" in correlations
    assert "metadata" in correlations
