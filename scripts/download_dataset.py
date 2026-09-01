"""
Sentinel — Kaggle Dataset Downloader
====================================
Downloads the fraud detection dataset from Kaggle.

Usage:
    python scripts/download_dataset.py

Requirements:
    Set in .env:
        KAGGLE_USERNAME=your_username
        KAGGLE_API_TOKEN=your_token

NEVER store credentials in this file.
NEVER commit the downloaded dataset to Git.
"""
import os
import sys
import json
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv(project_root / ".env")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("dataset_downloader")


def check_kaggle_credentials() -> tuple[str, str]:
    """
    Verify Kaggle credentials are in environment.
    NEVER read them from code.
    """
    username = os.environ.get("KAGGLE_USERNAME", "").strip()
    token = os.environ.get("KAGGLE_API_TOKEN", "").strip()

    if not username or not token:
        logger.error(
            "\n"
            "══════════════════════════════════════════════\n"
            "  KAGGLE CREDENTIALS NOT CONFIGURED\n"
            "══════════════════════════════════════════════\n"
            "\n"
            "  To download the dataset, you need Kaggle credentials.\n"
            "\n"
            "  Steps:\n"
            "  1. Go to https://www.kaggle.com → Account → API\n"
            "  2. Click 'Create New API Token'\n"
            "  3. This downloads kaggle.json with your username and key\n"
            "  4. Open your .env file\n"
            "  5. Set:\n"
            "       KAGGLE_USERNAME=your_kaggle_username\n"
            "       KAGGLE_API_TOKEN=your_kaggle_api_token\n"
            "\n"
            "  NEVER put your token in source code.\n"
            "  NEVER commit .env to Git.\n"
            "══════════════════════════════════════════════\n"
        )
        sys.exit(1)

    logger.info(f"Kaggle credentials found for user: {username}")
    return username, token


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def download_dataset() -> None:
    """Download the primary fraud detection dataset from Kaggle."""
    from ml.src.ingestion.dataset_registry import (
        ACTIVE_DATASET,
        RAW_DATA_DIR,
        METADATA_FILE,
    )

    username, token = check_kaggle_credentials()

    # Set environment variables for kaggle library
    # These are read from env, not hardcoded
    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = token

    logger.info(f"Dataset: {ACTIVE_DATASET.dataset_name}")
    logger.info(f"Handle: {ACTIVE_DATASET.kaggle_handle}")
    logger.info(f"License: {ACTIVE_DATASET.license_note}")

    raw_dir = project_root / RAW_DATA_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading to: {raw_dir}")

    try:
        import kaggle  # type: ignore
        kaggle.api.authenticate()

        # Download dataset
        owner, dataset_name = ACTIVE_DATASET.kaggle_handle.split("/")
        kaggle.api.dataset_download_files(
            ACTIVE_DATASET.kaggle_handle,
            path=str(raw_dir),
            unzip=True,
            quiet=False,
        )
        logger.info("Download complete.")

    except ImportError:
        logger.error(
            "kaggle package not installed. Run: pip install kaggle"
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Download failed: {e}")
        logger.info(
            "\nTroubleshooting:\n"
            "  1. Verify KAGGLE_USERNAME and KAGGLE_API_TOKEN in .env\n"
            "  2. Check you have accepted the dataset license on Kaggle\n"
            "  3. Verify internet connection\n"
        )
        sys.exit(1)

    # Verify expected files
    files_found = []
    checksums = {}
    total_rows = None
    total_cols = None

    for expected_file in ACTIVE_DATASET.expected_files:
        file_path = raw_dir / expected_file
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            checksum = compute_sha256(file_path)
            checksums[expected_file] = checksum
            files_found.append({
                "filename": expected_file,
                "size_mb": round(size_mb, 2),
                "sha256": checksum,
            })
            logger.info(f"  ✓ {expected_file} — {size_mb:.1f} MB")
            logger.info(f"    SHA256: {checksum}")

            # Print dataset dimensions
            if expected_file.endswith(".csv"):
                try:
                    import pandas as pd
                    df = pd.read_csv(file_path, nrows=5)
                    total_cols = len(df.columns)
                    # Count all rows
                    total_rows = sum(1 for _ in open(file_path)) - 1
                    logger.info(f"    Rows: {total_rows:,}")
                    logger.info(f"    Columns: {total_cols}")
                    logger.info(f"    Columns: {list(df.columns)}")
                except Exception as e:
                    logger.warning(f"Could not read CSV dimensions: {e}")
        else:
            logger.warning(f"  ✗ Expected file not found: {expected_file}")

    if not files_found:
        logger.error("No expected files found after download!")
        sys.exit(1)

    # Save metadata
    metadata_path = project_root / METADATA_FILE
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    metadata = {
        "dataset_name": ACTIVE_DATASET.dataset_name,
        "source": "Kaggle",
        "handle": ACTIVE_DATASET.kaggle_handle,
        "license": ACTIVE_DATASET.license_note,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "downloaded_by_user": username,  # safe — not the token
        "files": files_found,
        "sha256": checksums,
        "dimensions": {
            "rows": total_rows,
            "columns": total_cols,
        },
        "note": "Dataset is gitignored. Never commit raw data.",
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"\n✓ Metadata saved to: {metadata_path}")
    logger.info("\n═══════════════════════════════════════")
    logger.info("  Dataset download COMPLETE")
    logger.info(f"  Files: {[f['filename'] for f in files_found]}")
    logger.info(f"  Location: {raw_dir}")
    logger.info(
        "\n  ⚠️  Raw data is gitignored — NEVER commit it to Git."
    )
    logger.info("═══════════════════════════════════════\n")

    logger.info("Next step: python scripts/train_model.py")


if __name__ == "__main__":
    download_dataset()
