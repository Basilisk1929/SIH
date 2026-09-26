"""Comprehensive evaluation metrics for transaction risk classification."""

from dataclasses import dataclass
import logging
from typing import Any, Dict, List
import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

logger = logging.getLogger(__name__)


@dataclass
class RiskEvaluationMetrics:
    """Container holding standard financial fraud classification metrics."""
    precision: float
    recall: float
    f1: float
    roc_auc: float
    pr_auc: float
    confusion_matrix: List[List[int]]  # [[TN, FP], [FN, TP]]
    threshold: float
    sample_count: int
    positive_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "roc_auc": round(self.roc_auc, 4),
            "pr_auc": round(self.pr_auc, 4),
            "confusion_matrix": self.confusion_matrix,
            "threshold": self.threshold,
            "sample_count": self.sample_count,
            "positive_count": self.positive_count,
        }


class ModelEvaluator:
    """Evaluates classifier predictions against true fraud binary labels."""

    @classmethod
    def evaluate_predictions(
        cls,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        threshold: float = 0.50,
    ) -> RiskEvaluationMetrics:
        """Calculate Precision, Recall, F1, ROC-AUC, PR-AUC, and Confusion Matrix."""
        y_true = np.asarray(y_true, dtype=int)
        y_prob = np.asarray(y_prob, dtype=float)
        y_pred = (y_prob >= threshold).astype(int)

        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        # Check if single class present
        if len(np.unique(y_true)) > 1:
            roc_auc = float(roc_auc_score(y_true, y_prob))
            pr_auc = float(average_precision_score(y_true, y_prob))
        else:
            roc_auc = 0.5
            pr_auc = float(np.mean(y_true))

        cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()

        return RiskEvaluationMetrics(
            precision=prec,
            recall=rec,
            f1=f1,
            roc_auc=roc_auc,
            pr_auc=pr_auc,
            confusion_matrix=cm,
            threshold=threshold,
            sample_count=len(y_true),
            positive_count=int(np.sum(y_true)),
        )
