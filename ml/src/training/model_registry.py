"""
Sentinel ML — Phase 6 Model Registry
====================================
Handles versioning and serialization of model artifacts.
"""

import json
import logging
from pathlib import Path
from typing import Any

import joblib

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "ml" / "models"
REPORTS_DIR = PROJECT_ROOT / "ml" / "reports"


def save_model_artifact(model: Any, model_name: str, metadata: dict[str, Any]) -> Path:
    """
    Save the trained model and its metadata securely.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Save model binary
    model_path = MODELS_DIR / f"{model_name}.joblib"
    joblib.dump(model, model_path)
    logger.info(f"Saved model binary to {model_path}")

    # Generate unified metadata file for the selected model
    if metadata.get("is_selected", False):
        metadata_path = MODELS_DIR / "model_metadata.json"

        # Enforce required metadata fields
        required_fields = [
            "model_name",
            "model_version",
            "training_timestamp",
            "features",
            "training_rows",
            "validation_rows",
            "test_rows",
            "random_seed",
            "metrics",
            "decision_threshold",
        ]
        for field in required_fields:
            if field not in metadata:
                logger.warning(f"Missing recommended metadata field: {field}")

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved primary model metadata to {metadata_path}")

    return model_path


def load_selected_model() -> tuple[Any, dict[str, Any]]:
    """
    Loads the primary selected model and its metadata for inference.
    """
    metadata_path = MODELS_DIR / "model_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Model metadata not found at {metadata_path}")

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    model_name = metadata.get("model_name")
    if not model_name:
        raise ValueError("Metadata missing 'model_name'")

    model_path = MODELS_DIR / f"{model_name}.joblib"
    if not model_path.exists():
        raise FileNotFoundError(f"Model binary not found at {model_path}")

    model = joblib.load(model_path)
    return model, metadata
