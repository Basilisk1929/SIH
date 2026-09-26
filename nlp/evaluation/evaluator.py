"""Evaluation framework calculating Precision, Recall, and F1 score against synthetic ground-truth complaints."""

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from nlp.pipelines.cybercrime_nlp_pipeline import CybercrimeNLPPipeline

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
COMPLAINTS_CSV_PATH = PROJECT_ROOT / "data" / "synthetic" / "complaints" / "complaints.csv"


class NLPEvaluationMetrics:
    """Calculates and formats classification and entity extraction metrics."""

    @staticmethod
    def compute_prf1(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
        """Compute Precision, Recall, and F1 score."""
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        return round(precision, 4), round(recall, 4), round(f1, 4)


class ComplaintGroundTruthEvaluator:
    """Evaluates the NLP pipeline against synthetic ground truth."""

    def __init__(
        self,
        pipeline: Optional[CybercrimeNLPPipeline] = None,
        complaints_path: Path = COMPLAINTS_CSV_PATH,
    ):
        self.pipeline = pipeline or CybercrimeNLPPipeline()
        self.complaints_path = complaints_path

    def load_complaints(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load complaints dataset with ground-truth fields."""
        if not self.complaints_path.exists():
            raise FileNotFoundError(f"Complaints file not found at {self.complaints_path}")

        records: List[Dict[str, Any]] = []
        with open(self.complaints_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if limit and idx >= limit:
                    break
                records.append(row)
        return records

    def evaluate(self, sample_size: int = 100) -> Dict[str, Any]:
        """Run full evaluation on sample_size complaints and compute Precision, Recall, and F1."""
        complaints = self.load_complaints(limit=sample_size)
        if not complaints:
            return {"error": "No complaints available for evaluation"}

        # Tracking TP, FP, FN per entity type
        entity_counters: Dict[str, Dict[str, int]] = {
            "ACCOUNT": {"tp": 0, "fp": 0, "fn": 0},
            "UPI_ID": {"tp": 0, "fp": 0, "fn": 0},
            "PHONE": {"tp": 0, "fp": 0, "fn": 0},
            "AMOUNT": {"tp": 0, "fp": 0, "fn": 0},
            "SCAM_TYPE": {"tp": 0, "fp": 0, "fn": 0},
        }

        correct_categories = 0
        total_complaints = len(complaints)

        for row in complaints:
            narrative = row["narrative_synthetic"]
            result = self.pipeline.process(narrative, link_entities=False)

            # 1. Evaluate Scam Category
            gt_category = row.get("ground_truth_category") or row.get("category", "")
            pred_category = result.scam_type

            if pred_category.lower() == gt_category.lower():
                correct_categories += 1
                entity_counters["SCAM_TYPE"]["tp"] += 1
            else:
                entity_counters["SCAM_TYPE"]["fp"] += 1
                entity_counters["SCAM_TYPE"]["fn"] += 1

            # Build ground truth entity sets for this narrative
            gt_accounts = {row.get("victim_account_number"), row.get("suspect_account_number")} - {None, ""}
            gt_upis = {row.get("suspect_upi_id")} - {None, ""}
            gt_phones = {row.get("suspect_phone_number")} - {None, ""}

            # Extract normalized amounts
            gt_amount = float(row.get("reported_loss_amount", 0.0))

            # Predicted entity maps
            pred_accounts = {
                e.normalized_value for e in result.entities if e.label == "ACCOUNT"
            }
            pred_upis = {
                e.normalized_value for e in result.entities if e.label == "UPI_ID"
            }
            pred_phones = {
                e.normalized_value for e in result.entities if e.label == "PHONE"
            }
            pred_amounts = {
                e.normalized_value for e in result.entities if e.label == "AMOUNT"
            }

            # Evaluate ACCOUNTS
            for acc in pred_accounts:
                if acc in gt_accounts or any(acc in n for n in [narrative]):
                    entity_counters["ACCOUNT"]["tp"] += 1
                else:
                    entity_counters["ACCOUNT"]["fp"] += 1
            for gt_acc in gt_accounts:
                if gt_acc in narrative and gt_acc not in pred_accounts:
                    entity_counters["ACCOUNT"]["fn"] += 1

            # Evaluate UPI IDs
            for upi in pred_upis:
                if upi in gt_upis or upi in narrative.lower():
                    entity_counters["UPI_ID"]["tp"] += 1
                else:
                    entity_counters["UPI_ID"]["fp"] += 1
            for gt_upi in gt_upis:
                if gt_upi.lower() in narrative.lower() and gt_upi.lower() not in [u.lower() for u in pred_upis]:
                    entity_counters["UPI_ID"]["fn"] += 1

            # Evaluate PHONE NUMBERS
            for phone in pred_phones:
                if phone in gt_phones or phone[-10:] in narrative.replace(" ", "").replace("-", ""):
                    entity_counters["PHONE"]["tp"] += 1
                else:
                    entity_counters["PHONE"]["fp"] += 1
            for gt_phone in gt_phones:
                digits = gt_phone[-10:]
                if digits in narrative.replace(" ", "").replace("-", "") and not any(p[-10:] == digits for p in pred_phones):
                    entity_counters["PHONE"]["fn"] += 1

            # Evaluate AMOUNT
            amount_matched = False
            for amt in pred_amounts:
                if isinstance(amt, (int, float)) and abs(amt - gt_amount) < 1.0:
                    amount_matched = True
                    entity_counters["AMOUNT"]["tp"] += 1
                    break
            if not amount_matched and gt_amount > 0 and (f"{gt_amount:,.2f}" in narrative or str(int(gt_amount)) in narrative):
                entity_counters["AMOUNT"]["fn"] += 1

        # Calculate PRF1 metrics
        metrics_by_entity: Dict[str, Dict[str, float]] = {}
        total_tp = 0
        total_fp = 0
        total_fn = 0

        for ent_name, counts in entity_counters.items():
            p, r, f1 = NLPEvaluationMetrics.compute_prf1(counts["tp"], counts["fp"], counts["fn"])
            metrics_by_entity[ent_name] = {
                "precision": p,
                "recall": r,
                "f1_score": f1,
                "true_positives": counts["tp"],
                "false_positives": counts["fp"],
                "false_negatives": counts["fn"],
            }
            total_tp += counts["tp"]
            total_fp += counts["fp"]
            total_fn += counts["fn"]

        micro_p, micro_r, micro_f1 = NLPEvaluationMetrics.compute_prf1(total_tp, total_fp, total_fn)
        macro_p = round(sum(m["precision"] for m in metrics_by_entity.values()) / len(metrics_by_entity), 4)
        macro_r = round(sum(m["recall"] for m in metrics_by_entity.values()) / len(metrics_by_entity), 4)
        macro_f1 = round(sum(m["f1_score"] for m in metrics_by_entity.values()) / len(metrics_by_entity), 4)

        return {
            "evaluated_complaints_count": total_complaints,
            "scam_classification_accuracy": round(correct_categories / total_complaints, 4),
            "macro_averages": {
                "precision": macro_p,
                "recall": macro_r,
                "f1_score": macro_f1,
            },
            "micro_averages": {
                "precision": micro_p,
                "recall": micro_r,
                "f1_score": micro_f1,
            },
            "per_entity_metrics": metrics_by_entity,
        }
