"""Semiconductor Early Warning and Decision Support Engine.

Orchestrates multi-model inference (Isolation Forest + Random Forest),
computes normalized composite risk scores (0-100), and classifies severity.
"""

from functools import lru_cache
import logging
import os
from typing import Dict, Any, List, Optional
import joblib
import numpy as np
import pandas as pd

from app.config import settings
from app.ml.feature_engineering import FeaturePipeline

logger = logging.getLogger("semiconductor.early_warning")


class EarlyWarningEngine:
    """Computes real-time multi-dimensional risk scores across fab machinery."""

    def __init__(self, models_dir: str = "models/trained", prep_dir: str = "models/preprocessing"):
        self.models_dir = models_dir
        self.prep_dir = prep_dir
        self.rf_model = None
        self.if_model = None
        self.scaler = None
        self.feature_names: List[str] = []
        self._load_artifacts()

    def _load_artifacts(self):
        """Load trained models and preprocessing transformers."""
        rf_path = os.path.join(self.models_dir, "random_forest.joblib")
        if_path = os.path.join(self.models_dir, "isolation_forest.joblib")
        scaler_path = os.path.join(self.prep_dir, "scaler.joblib")
        feat_path = os.path.join(self.prep_dir, "feature_names.joblib")

        if os.path.exists(rf_path) and os.path.exists(if_path) and os.path.exists(scaler_path):
            self.rf_model = joblib.load(rf_path)
            self.if_model = joblib.load(if_path)
            self.scaler = joblib.load(scaler_path)
            self.feature_names = joblib.load(feat_path)
            logger.info("Successfully loaded ML models and scalers into memory.")
        else:
            logger.warning("ML models not found on disk. Ensure train_models.py has been executed.")

    def evaluate_telemetry(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Compute ML probability, anomaly score, and composite early warning score."""
        # 1. Feature Transformation
        pipeline = FeaturePipeline(preprocessing_dir=self.prep_dir)
        df_single = pd.DataFrame([row_dict])
        df_eng = pipeline.engineer_features(df_single)
        
        # Ensure all required features are present
        for feat in self.feature_names:
            if feat not in df_eng.columns:
                df_eng[feat] = 0.0

        X_raw = df_eng[self.feature_names].values
        X_scaled = self.scaler.transform(X_raw) if self.scaler else X_raw

        # 2. Random Forest Disruption Probability
        if self.rf_model is not None:
            ml_prob = float(self.rf_model.predict_proba(X_scaled)[0, 1])
        else:
            ml_prob = 0.15

        # 3. Isolation Forest Anomaly Severity
        if self.if_model is not None:
            raw_score = float(self.if_model.score_samples(X_scaled)[0])
            # Calibrate anomaly score to 0 - 100
            anomaly_score = float(np.clip(((-raw_score) - 0.4) * 150.0, 0.0, 100.0))
            is_anomaly = bool(self.if_model.predict(X_scaled)[0] == -1)
        else:
            anomaly_score = 15.0
            is_anomaly = False

        # 4. Maintenance Wear Risk (0 - 100)
        wear_index = float(df_eng.get("Maintenance_Wear_Index", [0.5])[0])
        maint_risk = float(np.clip(wear_index * 40.0, 0.0, 100.0))

        # 5. Process Drift Deviation (0 - 100)
        temp_drift = float(df_eng.get("Temp_Process_Drift", [0.0])[0])
        vib_drift = float(df_eng.get("Vib_Process_Drift", [0.0])[0])
        drift_score = float(np.clip((temp_drift * 1.5 + vib_drift * 15.0), 0.0, 100.0))

        # 6. Composite Risk Score (0 - 100)
        # Normalized weighted sum
        w_ml = settings.WEIGHT_PREDICTION_RISK
        w_anom = settings.WEIGHT_ANOMALY_SEVERITY
        w_maint = settings.WEIGHT_BUSINESS_IMPACT
        w_drift = settings.WEIGHT_TREND_ESCALATION
        w_crit = settings.WEIGHT_PRODUCTION_CRITICALITY

        composite_risk = (
            (ml_prob * 100.0 * w_ml)
            + (anomaly_score * w_anom)
            + (maint_risk * w_maint)
            + (drift_score * w_drift)
            + (15.0 * w_crit)
        )
        composite_risk = float(round(np.clip(composite_risk, 0.0, 100.0), 1))

        # 7. Severity Tier Classification
        if composite_risk <= settings.THRESHOLD_NORMAL:
            severity = "NORMAL"
            severity_color = "#10B981"
        elif composite_risk <= settings.THRESHOLD_LOW:
            severity = "LOW"
            severity_color = "#3B82F6"
        elif composite_risk <= settings.THRESHOLD_MEDIUM:
            severity = "MEDIUM"
            severity_color = "#F59E0B"
        elif composite_risk <= settings.THRESHOLD_HIGH:
            severity = "HIGH"
            severity_color = "#F97316"
        else:
            severity = "CRITICAL"
            severity_color = "#EF4444"

        return {
            "machine_id": str(row_dict.get("Machine_ID", "UNKNOWN")),
            "process_stage": str(row_dict.get("Process_Stage", "General")),
            "composite_risk_score": composite_risk,
            "severity": severity,
            "severity_color": severity_color,
            "ml_disruption_probability": float(round(ml_prob * 100, 1)),
            "anomaly_score": float(round(anomaly_score, 1)),
            "is_anomaly": is_anomaly,
            "maintenance_wear_risk": float(round(maint_risk, 1)),
            "process_drift_score": float(round(drift_score, 1)),
            "temperature": float(round(float(row_dict.get("Temperature", 0)), 1)),
            "vibration": float(round(float(row_dict.get("Vibration", 0)), 2)),
            "pressure": float(round(float(row_dict.get("Pressure", 0)), 2)),
            "power_consumption": float(round(float(row_dict.get("Power_Consumption", 0)), 1)),
            "timestamp": str(row_dict.get("Timestamp", "")),
        }


@lru_cache()
def get_early_warning_engine() -> EarlyWarningEngine:
    """Cached singleton accessor for EarlyWarningEngine."""
    return EarlyWarningEngine()
