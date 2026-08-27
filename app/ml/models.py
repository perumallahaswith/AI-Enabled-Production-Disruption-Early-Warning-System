"""Multi-Model Architecture Definitions for Semiconductor Fab Intelligence.

Implements Isolation Forest anomaly detector, Random Forest disruption classifier,
and Logistic Regression baseline model with calibrated outputs.
"""

import logging
from typing import Dict, Any, Tuple
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, confusion_matrix, brier_score_loss
)

logger = logging.getLogger("semiconductor.models")


class FabModelSuite:
    """Encapsulates the multi-model architecture for early disruption detection."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        
        # 1. Anomaly Detection Model
        self.isolation_forest = IsolationForest(
            n_estimators=150,
            contamination=0.03,
            max_features=0.85,
            random_state=self.random_state,
            n_jobs=-1,
        )

        # 2. Primary Disruption Risk Classifier
        self.random_forest = RandomForestClassifier(
            n_estimators=120,
            max_depth=8,
            min_samples_split=6,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=self.random_state,
            n_jobs=-1,
        )

        # 3. Interpretable Baseline Classifier
        self.baseline_logistic = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=self.random_state,
            C=1.0,
        )

    def train_all(
        self, X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, feature_names: list
    ) -> Dict[str, Any]:
        """Train all models, evaluate on future test split, and collect benchmark metrics."""
        logger.info("Training Isolation Forest on training split...")
        self.isolation_forest.fit(X_train)

        logger.info("Training Random Forest Disruption Classifier...")
        self.random_forest.fit(X_train, y_train)

        logger.info("Training Baseline Logistic Regression...")
        self.baseline_logistic.fit(X_train, y_train)

        # Predictions on Future Test Set
        # Random Forest Evaluation
        rf_prob = self.random_forest.predict_proba(X_test)[:, 1]
        rf_pred = (rf_prob >= 0.5).astype(int)

        # Baseline Evaluation
        lr_prob = self.baseline_logistic.predict_proba(X_test)[:, 1]
        lr_pred = (lr_prob >= 0.5).astype(int)

        # Isolation Forest Evaluation
        if_scores = self.isolation_forest.score_samples(X_test)
        # Normalize score to 0 (normal) to 100 (highly anomalous)
        min_s, max_s = if_scores.min(), if_scores.max()
        if_norm_scores = 100.0 * (1.0 - (if_scores - min_s) / (max_s - min_s + 1e-6))

        # Metrics Dictionary
        def compute_metrics(y_true, y_pred, y_prob):
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
            return {
                "precision": float(round(precision_score(y_true, y_pred, zero_division=0), 4)),
                "recall": float(round(recall_score(y_true, y_pred, zero_division=0), 4)),
                "f1_score": float(round(f1_score(y_true, y_pred, zero_division=0), 4)),
                "roc_auc": float(round(roc_auc_score(y_true, y_prob), 4)) if len(np.unique(y_true)) > 1 else 0.5,
                "pr_auc": float(round(average_precision_score(y_true, y_prob), 4)) if len(np.unique(y_true)) > 1 else 0.0,
                "brier_score": float(round(brier_score_loss(y_true, y_prob), 4)),
                "confusion_matrix": {
                    "true_negatives": int(tn),
                    "false_positives": int(fp),
                    "false_negatives": int(fn),
                    "true_positives": int(tp),
                },
            }

        rf_metrics = compute_metrics(y_test, rf_pred, rf_prob)
        lr_metrics = compute_metrics(y_test, lr_pred, lr_prob)

        # Feature Importance Ranking
        importances = self.random_forest.feature_importances_
        feature_importance_list = [
            {"feature": f, "importance": float(round(imp, 4))}
            for f, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
        ]

        metrics_report = {
            "model_version": "v1.0.0",
            "dataset_info": {
                "train_samples": int(len(X_train)),
                "test_samples": int(len(X_test)),
                "features_count": int(len(feature_names)),
                "positive_rate_train": float(round(float(y_train.mean()) * 100, 2)),
                "positive_rate_test": float(round(float(y_test.mean()) * 100, 2)),
            },
            "random_forest": rf_metrics,
            "baseline_logistic": lr_metrics,
            "isolation_forest": {
                "avg_anomaly_score": float(round(float(if_norm_scores.mean()), 2)),
                "anomaly_rate_pct": float(round(float((self.isolation_forest.predict(X_test) == -1).mean()) * 100, 2)),
            },
            "top_features": feature_importance_list[:10],
        }

        return metrics_report
