"""
Sentinel — Profiling Runner Script
====================================
Convenience script to run Phase 4 data profiling.

Usage:
    python scripts/run_profiling.py

Prerequisites:
    1. python scripts/download_dataset.py  (downloads creditcard.csv)
    2. pip install -r ml/requirements.txt

Output:
    ml/reports/data_profile.json
    ml/reports/data_profile.html  (if ydata-profiling installed)
    ml/reports/figures/*.png
"""

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)

from ml.src.ingestion.profile_dataset import run_profiling

if __name__ == "__main__":
    run_profiling()
