"""Reproducible training pipeline for financial transaction risk engine."""

import datetime
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
import xgboost as xgb

from ml.constants import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_MODEL_PATH,
    FEATURE_COLUMNS,
)
from ml.pipeline.data_loader import RiskDataLoader
from ml.pipeline.evaluator import ModelEvaluator, RiskEvaluationMetrics
from ml.pipeline.explainer import RiskFeatureExplainer
from ml.pipeline.feature_engineering import TransactionFeatureEngineer
from ml.pipeline.preprocessor import TransactionPreprocessor
from ml.pipeline.splitter import TimeAwareSplitter

logger = logging.getLogger(__name__)


class RiskModelTrainer:
    """Orchestrates end-to-end reproducible training and evaluation pipeline."""

    def __init__(
        self,
        data_loader: Optional[RiskDataLoader] = None,
        model_path: Path = DEFAULT_MODEL_PATH,
        config_path: Path = DEFAULT_CONFIG_PATH,
    ):
        self.data_loader = data_loader or RiskDataLoader()
        self.model_path = model_path
        self.config_path = config_path

    def run_pipeline(
        self,
        sample_limit: Optional[int] = 25000,
        n_estimators: int = 150,
        max_depth: int = 5,
        learning_rate: float = 0.08,
    ) -> Dict[str, Any]:
        """Execute complete reproducible ML lifecycle:
        raw data -> preprocessing -> feature engineering -> split -> train -> evaluate -> serialize.
        """
        logger.info("[1/7] Loading synthetic datasets...")
        datasets = self.data_loader.load_all_datasets(sample_transactions=sample_limit)
        tx_raw = datasets["transactions"]

        logger.info("[2/7] Preprocessing & chronological sorting...")
        tx_clean = TransactionPreprocessor.preprocess_transactions(tx_raw)

        # Filter to overlapping concurrent observation period to avoid artificial truncation artifacts
        t_start = pd.to_datetime("2024-08-15T13:12:00Z")
        t_end = pd.to_datetime("2024-09-29T23:57:14Z")
        tx_concurrent = tx_clean[(tx_clean["timestamp"] >= t_start) & (tx_clean["timestamp"] <= t_end)].copy()
        if not tx_concurrent.empty and tx_concurrent["is_fraud"].nunique() > 1:
            tx_clean = tx_concurrent.sort_values(by="timestamp").reset_index(drop=True)

        logger.info("[3/7] Feature engineering (12 risk features without lookahead leakage)...")
        engineer = TransactionFeatureEngineer(
            accounts_df=datasets["accounts"],
            complaints_df=None,  # Do not leak post-incident complaints
            locations_df=datasets["locations"],
            atms_df=datasets["atms"],
        )
        X = engineer.compute_features(tx_clean)
        y = tx_clean["is_fraud"]

        logger.info("[4/7] Time-aware chronological train/val/test splitting...")
        splitter = TimeAwareSplitter(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15)
        splits = splitter.split(X, y)

        logger.info("[5/7] Training XGBoost classifier...")
        pos_count = int(splits.y_train.sum())
        neg_count = len(splits.y_train) - pos_count
        raw_scale = float(neg_count / max(1, pos_count))
        scale_pos_weight = min(5.0, max(1.0, raw_scale))

        model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=0.85,
            colsample_bytree=0.85,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            random_state=42,
        )

        model.fit(
            splits.X_train,
            splits.y_train,
            eval_set=[(splits.X_val, splits.y_val)],
            verbose=False,
        )

        logger.info("[6/7] Evaluating model on unseen holdout test split...")
        test_probs = model.predict_proba(splits.X_test)[:, 1]
        metrics: RiskEvaluationMetrics = ModelEvaluator.evaluate_predictions(
            splits.y_test.values,
            test_probs,
            threshold=0.50,
        )

        # Feature importances & distribution stats
        importances = {
            col: float(imp) for col, imp in zip(FEATURE_COLUMNS, model.feature_importances_)
        }
        medians = {col: float(splits.X_train[col].median()) for col in FEATURE_COLUMNS}
        stds = {col: float(max(1e-4, splits.X_train[col].std())) for col in FEATURE_COLUMNS}

        config = {
            "model_type": "XGBClassifier",
            "version": "1.0.0",
            "trained_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "feature_names": FEATURE_COLUMNS,
            "feature_importances": importances,
            "feature_medians": medians,
            "feature_stds": stds,
            "metrics": metrics.to_dict(),
            "train_samples": len(splits.X_train),
            "val_samples": len(splits.X_val),
            "test_samples": len(splits.X_test),
        }

        logger.info("[7/7] Serializing trained model and configuration...")
        from ml.models.risk_engine import TransactionRiskEngine

        engine = TransactionRiskEngine(
            model=model,
            model_path=self.model_path,
            config_path=self.config_path,
        )
        engine.config = config
        engine.explainer = RiskFeatureExplainer(
            feature_names=FEATURE_COLUMNS,
            feature_importances=importances,
            feature_medians=medians,
            feature_stds=stds,
        )
        engine.save()

        logger.info(
            f"[✓] Training complete! Test Metrics: ROC-AUC={metrics.roc_auc:.4f}, "
            f"PR-AUC={metrics.pr_auc:.4f}, F1={metrics.f1:.4f}, Precision={metrics.precision:.4f}, Recall={metrics.recall:.4f}"
        )

        return config
