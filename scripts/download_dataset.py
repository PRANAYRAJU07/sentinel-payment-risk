"""
Sentinel — Kaggle Dataset Downloader (Phase 3)
================================================
Downloads the Credit Card Fraud Detection dataset from Kaggle.

Usage:
    python scripts/download_dataset.py

Requirements (in .env, NEVER in source code):
    KAGGLE_USERNAME=your_kaggle_username
    KAGGLE_API_TOKEN=your_kaggle_api_token

Security rules:
    - Credentials are read from environment ONLY
    - The token is NEVER printed, logged, or returned
    - Raw datasets are gitignored and never committed

Dataset: mlg-ulb/creditcardfraud
"""
import os
import sys
import json
import hashlib
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

# ── Project root ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sentinel.downloader")

# ── Constants (no secrets) ────────────────────────────────────────────────────
KAGGLE_HANDLE = "mlg-ulb/creditcardfraud"
EXPECTED_FILES = ["creditcard.csv"]
RAW_DIR = PROJECT_ROOT / "ml" / "data" / "raw"
METADATA_PATH = PROJECT_ROOT / "ml" / "data" / "dataset_metadata.json"


# ─────────────────────────────────────────────────────────────────────────────
# Credential verification
# ─────────────────────────────────────────────────────────────────────────────

def get_kaggle_credentials() -> tuple[str, str]:
    """
    Read Kaggle credentials from environment variables.
    NEVER returns the token in any log or print statement.
    """
    username = os.environ.get("KAGGLE_USERNAME", "").strip()
    token = os.environ.get("KAGGLE_API_TOKEN", "").strip()

    if not username or not token:
        logger.error(
            "\n"
            "══════════════════════════════════════════════════\n"
            "  KAGGLE CREDENTIALS MISSING\n"
            "══════════════════════════════════════════════════\n"
            "\n"
            "  Set these in your .env file (NEVER in source code):\n"
            "\n"
            "      KAGGLE_USERNAME=your_kaggle_username\n"
            "      KAGGLE_API_TOKEN=your_kaggle_api_token\n"
            "\n"
            "  How to get credentials:\n"
            "  1. Go to https://www.kaggle.com\n"
            "  2. Click your profile → Account → API\n"
            "  3. Click 'Create New API Token'\n"
            "  4. Copy username and key into .env\n"
            "\n"
            "  NEVER paste credentials into chat or source code.\n"
            "══════════════════════════════════════════════════\n"
        )
        sys.exit(1)

    # Log username only — never the token
    logger.info(f"Kaggle credentials found for user: {username}")
    return username, token


# ─────────────────────────────────────────────────────────────────────────────
# File utilities
# ─────────────────────────────────────────────────────────────────────────────

def compute_sha256(filepath: Path, chunk_size: int = 65536) -> str:
    """Compute SHA256 checksum of a file in streaming fashion."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def find_csv_in_dir(directory: Path) -> list[Path]:
    """Recursively find all CSV files in a directory."""
    return list(directory.rglob("*.csv"))


# ─────────────────────────────────────────────────────────────────────────────
# Download via kagglehub (primary method)
# ─────────────────────────────────────────────────────────────────────────────

def download_via_kagglehub(username: str, token: str) -> Path:
    """
    Download dataset using kagglehub.
    Sets credentials in env before importing kagglehub.
    """
    # Set credentials for kagglehub — read from args (which came from env)
    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = token

    try:
        import kagglehub  # type: ignore
    except ImportError:
        raise ImportError("kagglehub not installed. Run: pip install kagglehub")

    logger.info(f"Downloading dataset: {KAGGLE_HANDLE}")
    logger.info("This may take a few minutes (~150 MB)...")

    # kagglehub downloads to a cache dir and returns the path
    cached_path = kagglehub.dataset_download(KAGGLE_HANDLE)
    logger.info(f"Dataset cached at: {cached_path}")
    return Path(cached_path)


# ─────────────────────────────────────────────────────────────────────────────
# Download via kaggle (fallback method)
# ─────────────────────────────────────────────────────────────────────────────

def download_via_kaggle_api(username: str, token: str) -> None:
    """
    Download dataset using the official kaggle package.
    Falls back to this if kagglehub fails.
    """
    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = token

    try:
        import kaggle  # type: ignore
        kaggle.api.authenticate()
    except ImportError:
        raise ImportError("kaggle not installed. Run: pip install kaggle")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Downloading via kaggle API to: {RAW_DIR}")

    kaggle.api.dataset_download_files(
        KAGGLE_HANDLE,
        path=str(RAW_DIR),
        unzip=True,
        quiet=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Copy files to project raw dir
# ─────────────────────────────────────────────────────────────────────────────

def stage_files(source_dir: Path) -> list[Path]:
    """Copy downloaded CSV files to ml/data/raw/."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = find_csv_in_dir(source_dir)
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in downloaded dataset at: {source_dir}"
        )

    staged = []
    for csv_path in csv_files:
        dest = RAW_DIR / csv_path.name
        if not dest.exists():
            shutil.copy2(csv_path, dest)
            logger.info(f"  Copied: {csv_path.name} → {dest}")
        else:
            logger.info(f"  Already exists: {dest} (skipping copy)")
        staged.append(dest)

    return staged


# ─────────────────────────────────────────────────────────────────────────────
# Validate dataset
# ─────────────────────────────────────────────────────────────────────────────

def validate_and_report(file_path: Path, username: str) -> dict:
    """
    Validate the downloaded dataset and collect metadata.
    All statistics come from the actual file — never fabricated.
    """
    import pandas as pd

    logger.info(f"\nValidating: {file_path.name}")

    # File info
    size_bytes = file_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    sha256 = compute_sha256(file_path)

    logger.info(f"  File size: {size_mb:.1f} MB")
    logger.info(f"  SHA256: {sha256}")

    # Load dataset
    logger.info("  Loading CSV (this takes ~5 seconds)...")
    df = pd.read_csv(file_path)

    # Actual statistics — nothing fabricated
    n_rows, n_cols = df.shape
    col_names = list(df.columns)
    dtypes = {col: str(df[col].dtype) for col in df.columns}
    missing = {col: int(df[col].isna().sum()) for col in df.columns}
    total_missing = sum(missing.values())
    n_duplicates = int(df.duplicated().sum())

    logger.info(f"  Rows:      {n_rows:,}")
    logger.info(f"  Columns:   {n_cols}")
    logger.info(f"  Column names: {col_names}")
    logger.info(f"  Missing values: {total_missing}")
    logger.info(f"  Duplicate rows: {n_duplicates}")

    # Target column
    target_col = "Class"
    if target_col not in df.columns:
        available = list(df.columns)
        raise ValueError(
            f"Expected target column '{target_col}' not found. "
            f"Available columns: {available}"
        )

    target_dist = df[target_col].value_counts().to_dict()
    target_dist = {int(k): int(v) for k, v in target_dist.items()}
    fraud_count = target_dist.get(1, 0)
    legit_count = target_dist.get(0, 0)
    fraud_pct = (fraud_count / n_rows) * 100 if n_rows > 0 else 0
    imbalance_ratio = legit_count / fraud_count if fraud_count > 0 else None

    logger.info(f"\n  ── Target Distribution ──")
    logger.info(f"  Legitimate (0): {legit_count:,}")
    logger.info(f"  Fraud (1):      {fraud_count:,}")
    logger.info(f"  Fraud %:        {fraud_pct:.4f}%")
    logger.info(f"  Imbalance ratio (legit:fraud): {imbalance_ratio:.1f}:1")

    # Amount statistics
    if "Amount" in df.columns:
        amount_stats = df["Amount"].describe().to_dict()
        logger.info(f"\n  ── Amount Statistics ──")
        logger.info(f"  Min:    {amount_stats['min']:.2f}")
        logger.info(f"  Max:    {amount_stats['max']:.2f}")
        logger.info(f"  Mean:   {amount_stats['mean']:.2f}")
        logger.info(f"  Median: {df['Amount'].median():.2f}")

    # Time statistics
    if "Time" in df.columns:
        time_span_hours = df["Time"].max() / 3600
        logger.info(f"\n  ── Temporal Coverage ──")
        logger.info(f"  Time span: {time_span_hours:.1f} hours ({time_span_hours/24:.1f} days)")

    metadata = {
        "dataset_name": "Credit Card Fraud Detection",
        "source": "Kaggle",
        "handle": KAGGLE_HANDLE,
        "license": "Database Contents License (DbCL) v1.0",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "downloaded_by_user": username,  # username only, NEVER the token
        "files": [
            {
                "filename": file_path.name,
                "size_bytes": size_bytes,
                "size_mb": round(size_mb, 2),
                "sha256": sha256,
            }
        ],
        "dimensions": {
            "rows": n_rows,
            "columns": n_cols,
            "column_names": col_names,
        },
        "target_column": target_col,
        "target_distribution": {
            "legitimate_count": legit_count,
            "fraud_count": fraud_count,
            "fraud_percentage": round(fraud_pct, 4),
            "imbalance_ratio": round(imbalance_ratio, 1) if imbalance_ratio else None,
        },
        "data_quality": {
            "total_missing_values": total_missing,
            "duplicate_rows": n_duplicates,
            "column_dtypes": dtypes,
            "missing_by_column": missing,
        },
        "architecture_note": (
            "This dataset contains PCA-transformed features (V1-V28) only. "
            "It does NOT contain merchant, device, IP, or customer relationship data. "
            "Those graph-layer relationships will be built using a clearly labeled "
            "synthetic payment ecosystem — never fabricated from this dataset."
        ),
        "git_note": "Raw dataset is gitignored. Run scripts/download_dataset.py to obtain it.",
    }

    return metadata


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("═" * 55)
    logger.info("  Sentinel — Kaggle Dataset Downloader")
    logger.info("  Dataset: mlg-ulb/creditcardfraud")
    logger.info("═" * 55)

    # Step 1: Verify credentials (exits if missing)
    username, token = get_kaggle_credentials()

    # Step 2: Check if already downloaded
    expected_file = RAW_DIR / "creditcard.csv"
    if expected_file.exists():
        size_mb = expected_file.stat().st_size / (1024 * 1024)
        logger.info(
            f"\n✓ Dataset already exists: {expected_file}\n"
            f"  Size: {size_mb:.1f} MB\n"
            f"  Use --force to re-download."
        )
        # Still validate and regenerate metadata
    else:
        # Step 3: Download
        download_success = False

        # Try kagglehub first (cleaner API)
        try:
            logger.info("\nAttempting download via kagglehub...")
            source_dir = download_via_kagglehub(username, token)
            staged_files = stage_files(source_dir)
            download_success = True
            logger.info(f"✓ kagglehub download succeeded")
        except Exception as e:
            logger.warning(f"kagglehub failed: {e}")
            logger.info("Falling back to kaggle API...")

        # Fallback: kaggle package
        if not download_success:
            try:
                download_via_kaggle_api(username, token)
                download_success = True
                logger.info("✓ kaggle API download succeeded")
            except Exception as e:
                logger.error(f"Both download methods failed: {e}")
                logger.error(
                    "\nTroubleshooting:\n"
                    "  1. Verify KAGGLE_USERNAME and KAGGLE_API_TOKEN in .env\n"
                    "  2. Ensure you accepted the dataset license at:\n"
                    "     https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud\n"
                    "  3. Check internet connectivity\n"
                    "  4. Try: pip install --upgrade kagglehub kaggle\n"
                )
                sys.exit(1)

    # Step 4: Validate dataset
    if not expected_file.exists():
        logger.error(f"Expected file not found after download: {expected_file}")
        logger.error(f"Files in {RAW_DIR}: {list(RAW_DIR.iterdir())}")
        sys.exit(1)

    metadata = validate_and_report(expected_file, username)

    # Step 5: Save metadata
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"\n✓ Metadata saved: {METADATA_PATH}")

    # Step 6: Final summary
    dims = metadata["dimensions"]
    dist = metadata["target_distribution"]
    logger.info("\n" + "═" * 55)
    logger.info("  DOWNLOAD COMPLETE")
    logger.info("═" * 55)
    logger.info(f"  File:       {expected_file.name}")
    logger.info(f"  Rows:       {dims['rows']:,}")
    logger.info(f"  Columns:    {dims['columns']}")
    logger.info(f"  Fraud:      {dist['fraud_count']:,} ({dist['fraud_percentage']:.4f}%)")
    logger.info(f"  Legitimate: {dist['legitimate_count']:,}")
    logger.info(f"  Imbalance:  {dist['imbalance_ratio']}:1")
    logger.info("═" * 55)
    logger.info("  ⚠️  Raw data is gitignored. NEVER commit it.")
    logger.info("  Next: python scripts/run_profiling.py")
    logger.info("═" * 55)


if __name__ == "__main__":
    main()
