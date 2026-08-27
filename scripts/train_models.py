"""Reproducible Model Training and Serialization Pipeline.

Executes:
1. Canonical dataset ingestion and fusion.
2. Leakage-free, time-aware feature engineering.
3. Multi-model training (Isolation Forest, Random Forest, Logistic Baseline).
4. Validation on future chronological test split.
5. Serialization of models, preprocessors, and metadata metrics.
"""

from datetime import datetime
import json
import logging
import os
import sys
import joblib

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.services.data_ingestion import DataIngestionService
from app.ml.feature_engineering import FeaturePipeline
from app.ml.models import FabModelSuite

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("train_models")


def main():
    logger.info("================================================================")
    logger.info("  SEMICONDUCTOR ML EARLY WARNING ENGINE - TRAINING PIPELINE")
    logger.info("================================================================")

    # 1. Ingest Data
    ingestion = DataIngestionService()
    fused_df, data_meta = ingestion.run_pipeline()
    logger.info(f"Loaded {len(fused_df)} fused observations across {data_meta['unique_machines']} machines.")

    # 2. Feature Engineering & Time-Aware Split
    pipeline = FeaturePipeline()
    train_df, test_df, X_train, X_test, y_train, y_test = pipeline.time_aware_split(fused_df, train_ratio=0.75)

    # 3. Model Suite Fitting & Evaluation
    suite = FabModelSuite(random_state=42)
    metrics = suite.train_all(X_train, y_train, X_test, y_test, pipeline.engineered_feature_cols)

    # 4. Model Persistence
    models_dir = settings.MODELS_DIR
    os.makedirs(models_dir, exist_ok=True)
    meta_dir = "models/metadata"
    os.makedirs(meta_dir, exist_ok=True)

    rf_path = os.path.join(models_dir, "random_forest.joblib")
    if_path = os.path.join(models_dir, "isolation_forest.joblib")
    lr_path = os.path.join(models_dir, "baseline_logistic.joblib")
    metrics_path = os.path.join(meta_dir, "model_metrics.json")

    joblib.dump(suite.random_forest, rf_path)
    joblib.dump(suite.isolation_forest, if_path)
    joblib.dump(suite.baseline_logistic, lr_path)

    metrics["training_timestamp"] = datetime.utcnow().isoformat()
    metrics["raw_dataset_source"] = "data/raw/fab_synthetic_data.xlsx"

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Saved models to {models_dir}")
    logger.info(f"Saved evaluation metrics to {metrics_path}")

    # 5. Display Evaluation Summary
    rf_m = metrics["random_forest"]
    lr_m = metrics["baseline_logistic"]
    logger.info("----------------------------------------------------------------")
    logger.info("  EVALUATION METRICS ON UNSEEN FUTURE TEST SET")
    logger.info("----------------------------------------------------------------")
    logger.info(f"  Random Forest      : PR-AUC={rf_m['pr_auc']:.3f} | ROC-AUC={rf_m['roc_auc']:.3f} | F1={rf_m['f1_score']:.3f} | Precision={rf_m['precision']:.3f} | Recall={rf_m['recall']:.3f}")
    logger.info(f"  Logistic Baseline  : PR-AUC={lr_m['pr_auc']:.3f} | ROC-AUC={lr_m['roc_auc']:.3f} | F1={lr_m['f1_score']:.3f} | Precision={lr_m['precision']:.3f} | Recall={lr_m['recall']:.3f}")
    logger.info("----------------------------------------------------------------")
    logger.info("  TOP CONTRIBUTING PROCESS ATTRIBUTES")
    logger.info("----------------------------------------------------------------")
    for idx, item in enumerate(metrics["top_features"][:6], 1):
        logger.info(f"  {idx}. {item['feature']:<30} : {item['importance']*100:.1f}%")
    logger.info("================================================================")
    logger.info("  MODEL TRAINING COMPLETED SUCCESSFULLY")
    logger.info("================================================================")


if __name__ == "__main__":
    main()
