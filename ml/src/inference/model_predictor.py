"""
Sentinel ML — Inference API (Phase 6.21)
========================================
Loads the canonical feature pipeline and the best selected model.
Exposes real-time scoring endpoints for individual transactions.
"""

import logging
from typing import Any

from ml.src.features.inference import TransactionTransformer
from ml.src.training.model_registry import load_selected_model

logger = logging.getLogger(__name__)


class RiskPredictor:
    """
    Combines the feature engineering pipeline and the trained ML model
    to provide risk scores and decisions for incoming transactions.
    """

    def __init__(self):
        logger.info("Initializing RiskPredictor...")

        # Load feature transformer
        self.transformer = TransactionTransformer()

        # Load selected model and metadata
        self.model, self.metadata = load_selected_model()

        self.threshold = self.metadata.get("decision_threshold", 0.5)
        self.model_name = self.metadata.get("model_name", "unknown")

        logger.info(f"Loaded {self.model_name} with threshold {self.threshold}")

    def predict_proba(self, transaction: dict[str, Any]) -> float:
        """Returns the raw probability of fraud (0.0 to 1.0)."""
        # Transform raw dictionary to features
        X_features = self.transformer.transform_transaction(transaction)

        # Predict probability
        if hasattr(self.model, "predict_proba"):
            prob = self.model.predict_proba(X_features)[0, 1]
        else:
            prob = self.model.predict(X_features)[0]

        return float(prob)

    def predict(self, transaction: dict[str, Any]) -> int:
        """Returns binary prediction (0 or 1) based on the learned threshold."""
        prob = self.predict_proba(transaction)
        return int(prob >= self.threshold)

    def score_transaction(self, transaction: dict[str, Any]) -> dict[str, Any]:
        """
        Returns a rich scoring payload including risk score mapping.
        Note: Risk Score mapping (prob * 100) is a prototype and not
        strictly a calibrated loss probability.
        """
        prob = self.predict_proba(transaction)

        # 6.22 - Risk Score Mapping (0-100)
        risk_score = int(round(prob * 100))

        # Decision logic based on optimal threshold
        if prob >= self.threshold:
            decision = "HOLD"
        elif prob >= (self.threshold * 0.5):  # Arbitrary review zone for prototype
            decision = "REVIEW"
        else:
            decision = "APPROVE"

        return {
            "probability": prob,
            "risk_score": risk_score,
            "decision": decision,
            "threshold_used": self.threshold,
            "model_used": self.model_name,
        }
