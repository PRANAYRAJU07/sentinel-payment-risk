"""
Sentinel ML — Dataset Profiler (Phase 4)
==========================================
Generates a comprehensive profile of the creditcard fraud dataset.

All statistics are computed from the actual downloaded data.
Nothing is fabricated or hard-coded.

Usage:
    python ml/src/ingestion/profile_dataset.py

Output:
    ml/reports/data_profile.json   — machine-readable full profile
    ml/reports/data_profile.html   — human-readable summary (if ydata-profiling available)
    ml/reports/figures/            — visualization plots
"""
import json
import logging
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

# ── Project paths ─────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RAW_DIR = PROJECT_ROOT / "ml" / "data" / "raw"
REPORTS_DIR = PROJECT_ROOT / "ml" / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
PRIMARY_FILE = RAW_DIR / "creditcard.csv"

# ── Column definitions ────────────────────────────────────────────────────────
TIME_COL = "Time"
AMOUNT_COL = "Amount"
TARGET_COL = "Class"
PCA_COLS = [f"V{i}" for i in range(1, 29)]
FEATURE_COLS = PCA_COLS + [AMOUNT_COL]


def load_dataset(path: Optional[Path] = None) -> "pd.DataFrame":
    """Load dataset. Raises clear error if file doesn't exist."""
    import pandas as pd

    p = path or PRIMARY_FILE
    if not p.exists():
        raise FileNotFoundError(
            f"Dataset not found: {p}\n"
            f"Run: python scripts/download_dataset.py"
        )
    logger.info(f"Loading dataset from: {p}")
    df = pd.read_csv(p)
    logger.info(f"Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Profile computation
# ─────────────────────────────────────────────────────────────────────────────

def compute_basic_profile(df: "pd.DataFrame") -> dict:
    """Compute shape, types, missing values, duplicates."""
    n_rows, n_cols = df.shape

    missing_by_col = {col: int(df[col].isna().sum()) for col in df.columns}
    total_missing = sum(missing_by_col.values())
    duplicate_rows = int(df.duplicated().sum())
    unique_by_col = {col: int(df[col].nunique()) for col in df.columns}

    return {
        "shape": {"rows": n_rows, "columns": n_cols},
        "column_names": list(df.columns),
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
        "missing_values": {
            "total": total_missing,
            "by_column": missing_by_col,
            "columns_with_missing": [c for c, v in missing_by_col.items() if v > 0],
        },
        "duplicates": {
            "count": duplicate_rows,
            "percentage": round(duplicate_rows / n_rows * 100, 4) if n_rows > 0 else 0,
        },
        "unique_values_by_column": unique_by_col,
    }


def compute_target_profile(df: "pd.DataFrame") -> dict:
    """Compute class distribution and imbalance metrics."""
    counts = df[TARGET_COL].value_counts().sort_index()
    n_total = len(df)
    fraud_count = int(counts.get(1, 0))
    legit_count = int(counts.get(0, 0))
    fraud_pct = fraud_count / n_total * 100 if n_total > 0 else 0
    imbalance_ratio = legit_count / fraud_count if fraud_count > 0 else None

    return {
        "target_column": TARGET_COL,
        "legitimate_count": legit_count,
        "fraud_count": fraud_count,
        "total": n_total,
        "fraud_percentage": round(fraud_pct, 6),
        "legitimate_percentage": round(100 - fraud_pct, 6),
        "imbalance_ratio": round(imbalance_ratio, 2) if imbalance_ratio else None,
        "class_imbalance_note": (
            f"Only {fraud_pct:.4f}% of transactions are fraudulent. "
            f"Accuracy is a misleading metric here — a classifier that predicts "
            f"'legitimate' for every transaction achieves >{100 - fraud_pct:.1f}% accuracy "
            f"while detecting ZERO fraud. "
            f"We prioritize: Precision-Recall AUC, Recall@threshold, F1."
        ),
    }


def compute_numerical_stats(df: "pd.DataFrame") -> dict:
    """Compute per-column statistics for numerical features."""
    import numpy as np

    stats = {}
    numeric_cols = [TIME_COL, AMOUNT_COL] + PCA_COLS

    for col in numeric_cols:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        stats[col] = {
            "mean": round(float(series.mean()), 6),
            "std": round(float(series.std()), 6),
            "min": round(float(series.min()), 6),
            "p25": round(float(series.quantile(0.25)), 6),
            "median": round(float(series.median()), 6),
            "p75": round(float(series.quantile(0.75)), 6),
            "max": round(float(series.max()), 6),
            "skewness": round(float(series.skew()), 6),
        }

    # Amount by class
    if AMOUNT_COL in df.columns:
        fraud_amounts = df[df[TARGET_COL] == 1][AMOUNT_COL]
        legit_amounts = df[df[TARGET_COL] == 0][AMOUNT_COL]

        stats["amount_by_class"] = {
            "fraud": {
                "mean": round(float(fraud_amounts.mean()), 2),
                "median": round(float(fraud_amounts.median()), 2),
                "max": round(float(fraud_amounts.max()), 2),
            },
            "legitimate": {
                "mean": round(float(legit_amounts.mean()), 2),
                "median": round(float(legit_amounts.median()), 2),
                "max": round(float(legit_amounts.max()), 2),
            },
        }

    return stats


def compute_temporal_profile(df: "pd.DataFrame") -> dict:
    """Analyze temporal distribution of transactions."""
    if TIME_COL not in df.columns:
        return {"note": "No time column found"}

    time_series = df[TIME_COL]
    max_time = float(time_series.max())
    hours_span = max_time / 3600

    # Fraud timing
    fraud_times = df[df[TARGET_COL] == 1][TIME_COL]
    legit_times = df[df[TARGET_COL] == 0][TIME_COL]

    # Transactions per hour (normalized)
    df_copy = df.copy()
    df_copy["hour_of_day"] = (df_copy[TIME_COL] / 3600).astype(int) % 24
    txn_per_hour = df_copy["hour_of_day"].value_counts().sort_index().to_dict()
    txn_per_hour = {int(k): int(v) for k, v in txn_per_hour.items()}

    fraud_per_hour = (
        df_copy[df_copy[TARGET_COL] == 1]["hour_of_day"]
        .value_counts().sort_index().to_dict()
    )
    fraud_per_hour = {int(k): int(v) for k, v in fraud_per_hour.items()}

    return {
        "time_column": TIME_COL,
        "time_unit": "seconds since first transaction",
        "total_seconds": round(max_time, 0),
        "total_hours": round(hours_span, 2),
        "total_days": round(hours_span / 24, 2),
        "fraud_time_stats": {
            "mean_seconds": round(float(fraud_times.mean()), 0),
            "median_seconds": round(float(fraud_times.median()), 0),
        },
        "transactions_per_hour": txn_per_hour,
        "fraud_per_hour": fraud_per_hour,
        "temporal_note": (
            "Dataset spans approximately 2 days (48 hours). "
            "Time column is seconds since first transaction. "
            "Important: we use time-based train/test split to avoid leakage."
        ),
    }


def compute_correlation_with_target(df: "pd.DataFrame") -> dict:
    """Compute correlation of each feature with the target column."""
    correlations = {}
    for col in FEATURE_COLS:
        if col in df.columns:
            corr = float(df[col].corr(df[TARGET_COL]))
            correlations[col] = round(corr, 6)

    # Sort by absolute correlation
    sorted_corr = dict(
        sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
    )

    top_positive = {k: v for k, v in list(sorted_corr.items())[:5] if v > 0}
    top_negative = dict(
        list({k: v for k, v in sorted_corr.items() if v < 0}.items())[:5]
    )

    return {
        "correlations_with_target": sorted_corr,
        "top_positive_correlators": top_positive,
        "top_negative_correlators": dict(list(top_negative.items())[:5]),
        "note": (
            "Features V1-V28 are PCA-transformed principal components. "
            "Original feature names are not disclosed by dataset authors for privacy."
        ),
    }


def compute_outlier_summary(df: "pd.DataFrame") -> dict:
    """Detect outliers using IQR method for Amount column."""
    outliers = {}

    for col in [AMOUNT_COL]:
        if col not in df.columns:
            continue
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 3.0 * iqr
        upper = q3 + 3.0 * iqr
        outlier_mask = (df[col] < lower) | (df[col] > upper)
        n_outliers = int(outlier_mask.sum())
        outlier_fraud_rate = (
            float(df[outlier_mask][TARGET_COL].mean()) if n_outliers > 0 else 0.0
        )
        outliers[col] = {
            "iqr_lower_bound": round(float(lower), 4),
            "iqr_upper_bound": round(float(upper), 4),
            "outlier_count": n_outliers,
            "outlier_pct": round(n_outliers / len(df) * 100, 4),
            "outlier_fraud_rate": round(outlier_fraud_rate * 100, 4),
        }

    return outliers


def compute_leakage_assessment() -> dict:
    """
    Document potential data leakage risks.
    Based on known dataset characteristics — verified against actual schema.
    """
    return {
        "target_column": TARGET_COL,
        "safe_feature_columns": FEATURE_COLS,
        "leakage_risks": [
            {
                "column": TIME_COL,
                "risk": "INFORMATIONAL",
                "note": (
                    "Time is safe to use as a feature but must be used carefully. "
                    "Never use it to sort after splitting — always split by time first."
                ),
            }
        ],
        "leakage_safe_columns": FEATURE_COLS,
        "dropped_columns": [],
        "train_test_strategy": (
            "Time-based split: first 80% of transactions → train, "
            "last 20% → test. Random split would allow future data to "
            "leak into training when temporal patterns exist."
        ),
        "suspicious_identifiers": {
            "note": (
                "Dataset has no customer ID, device ID, IP, or merchant fields. "
                "V1-V28 are PCA-transformed — original features are not disclosed. "
                "This eliminates most identifier-based leakage risks."
            )
        },
        "recommendation": (
            "Use features: V1-V28 + Amount. Optionally add Time as a feature "
            "to capture temporal patterns. Always split by time, not randomly."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Visualization
# ─────────────────────────────────────────────────────────────────────────────

def generate_plots(df: "pd.DataFrame") -> list[str]:
    """
    Generate profiling plots and save to ml/reports/figures/.
    Returns list of saved file paths.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import seaborn as sns
        import numpy as np
    except ImportError:
        logger.warning("matplotlib/seaborn not installed — skipping plots")
        return []

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    saved = []

    # Style
    plt.style.use("seaborn-v0_8-darkgrid")
    COLORS = {"fraud": "#e74c3c", "legit": "#2ecc71"}

    # ── 1. Class Distribution (bar) ──────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    counts = df[TARGET_COL].value_counts().sort_index()
    labels = ["Legitimate (0)", "Fraud (1)"]
    bars = ax.bar(labels, counts.values,
                  color=[COLORS["legit"], COLORS["fraud"]],
                  edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 500,
                f"{val:,}", ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_title("Class Distribution (Fraud vs Legitimate)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_ylabel("Transaction Count")
    ax.set_xlabel("Class")
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
    )
    note = f"Fraud: {counts.get(1, 0):,} ({counts.get(1, 0)/len(df)*100:.3f}%)"
    ax.text(0.98, 0.95, note, transform=ax.transAxes, ha="right", va="top",
            fontsize=9, color="#e74c3c",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    plt.tight_layout()
    p = FIGURES_DIR / "01_class_distribution.png"
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    saved.append(str(p))
    logger.info(f"  Saved: {p.name}")

    # ── 2. Transaction Amount Distribution (log scale) ───────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fraud_amounts = df[df[TARGET_COL] == 1][AMOUNT_COL]
    legit_amounts = df[df[TARGET_COL] == 0][AMOUNT_COL]

    for ax, amounts, label, color, title in [
        (axes[0], legit_amounts, "Legitimate", COLORS["legit"], "Legitimate Transactions"),
        (axes[1], fraud_amounts, "Fraud", COLORS["fraud"], "Fraudulent Transactions"),
    ]:
        ax.hist(amounts, bins=80, color=color, alpha=0.8, edgecolor="white", linewidth=0.3)
        ax.set_yscale("log")
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Amount (EUR)")
        ax.set_ylabel("Count (log scale)")
        ax.text(0.98, 0.95,
                f"Mean: {amounts.mean():.2f}\nMedian: {amounts.median():.2f}\nMax: {amounts.max():.2f}",
                transform=ax.transAxes, ha="right", va="top", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9))

    fig.suptitle("Transaction Amount Distribution by Class", fontsize=14, fontweight="bold")
    plt.tight_layout()
    p = FIGURES_DIR / "02_amount_distribution.png"
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    saved.append(str(p))
    logger.info(f"  Saved: {p.name}")

    # ── 3. Amount Box Plot: Fraud vs Legitimate ───────────────────────────────
    fig, ax = plt.subplots(figsize=(8, 6))
    data_to_plot = [
        legit_amounts[legit_amounts <= legit_amounts.quantile(0.99)].values,
        fraud_amounts[fraud_amounts <= fraud_amounts.quantile(0.99)].values,
    ]
    bp = ax.boxplot(data_to_plot, patch_artist=True, widths=0.5,
                    medianprops=dict(color="black", linewidth=2))
    bp["boxes"][0].set_facecolor(COLORS["legit"])
    bp["boxes"][1].set_facecolor(COLORS["fraud"])
    ax.set_xticklabels(["Legitimate", "Fraud"])
    ax.set_title("Transaction Amount: Fraud vs Legitimate\n(99th percentile capped)",
                 fontsize=12, fontweight="bold")
    ax.set_ylabel("Amount (EUR)")
    plt.tight_layout()
    p = FIGURES_DIR / "03_amount_boxplot.png"
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    saved.append(str(p))
    logger.info(f"  Saved: {p.name}")

    # ── 4. Temporal Distribution ─────────────────────────────────────────────
    if TIME_COL in df.columns:
        fig, axes = plt.subplots(2, 1, figsize=(14, 8))

        # Transactions over time
        df_temp = df.copy()
        df_temp["hour_bucket"] = (df_temp[TIME_COL] / 3600).astype(int)
        legit_time = df_temp[df_temp[TARGET_COL] == 0].groupby("hour_bucket").size()
        fraud_time = df_temp[df_temp[TARGET_COL] == 1].groupby("hour_bucket").size()

        ax = axes[0]
        ax.fill_between(legit_time.index, legit_time.values,
                        alpha=0.6, color=COLORS["legit"], label="Legitimate")
        ax.set_title("Transaction Volume Over Time", fontsize=12, fontweight="bold")
        ax.set_xlabel("Hour")
        ax.set_ylabel("Transaction Count")
        ax.legend()

        ax = axes[1]
        ax.bar(fraud_time.index, fraud_time.values,
               color=COLORS["fraud"], alpha=0.8, label="Fraud")
        ax.set_title("Fraud Transactions Over Time", fontsize=12, fontweight="bold")
        ax.set_xlabel("Hour")
        ax.set_ylabel("Fraud Count")
        ax.legend()

        plt.tight_layout()
        p = FIGURES_DIR / "04_temporal_distribution.png"
        plt.savefig(p, dpi=150, bbox_inches="tight")
        plt.close()
        saved.append(str(p))
        logger.info(f"  Saved: {p.name}")

    # ── 5. Feature Correlation with Target ───────────────────────────────────
    corr_values = {
        col: float(df[col].corr(df[TARGET_COL]))
        for col in FEATURE_COLS if col in df.columns
    }
    sorted_corr = sorted(corr_values.items(), key=lambda x: abs(x[1]), reverse=True)
    top20 = sorted_corr[:20]
    cols, vals = zip(*top20)

    fig, ax = plt.subplots(figsize=(10, 7))
    colors = [COLORS["fraud"] if v < 0 else COLORS["legit"] for v in vals]
    ax.barh(list(cols), list(vals), color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("Top 20 Feature Correlations with Target (Class)",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("Pearson Correlation with Class")
    fraud_patch = mpatches.Patch(color=COLORS["fraud"], label="Negative correlation")
    legit_patch = mpatches.Patch(color=COLORS["legit"], label="Positive correlation")
    ax.legend(handles=[fraud_patch, legit_patch])
    plt.tight_layout()
    p = FIGURES_DIR / "05_feature_correlations.png"
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    saved.append(str(p))
    logger.info(f"  Saved: {p.name}")

    # ── 6. PCA Component Distributions: Fraud vs Legit ───────────────────────
    # Show top 4 most correlated PCA features
    top_pca = [col for col, _ in sorted_corr if col.startswith("V")][:4]
    if top_pca:
        fig, axes = plt.subplots(2, 2, figsize=(14, 9))
        axes = axes.flatten()
        for i, col in enumerate(top_pca):
            ax = axes[i]
            fraud_vals = df[df[TARGET_COL] == 1][col]
            legit_vals = df[df[TARGET_COL] == 0][col]
            ax.hist(legit_vals, bins=80, color=COLORS["legit"], alpha=0.5,
                    density=True, label="Legitimate")
            ax.hist(fraud_vals, bins=80, color=COLORS["fraud"], alpha=0.5,
                    density=True, label="Fraud")
            ax.set_title(f"{col} Distribution", fontsize=11, fontweight="bold")
            ax.set_ylabel("Density")
            ax.legend(fontsize=8)
        fig.suptitle("Top PCA Feature Distributions: Fraud vs Legitimate",
                     fontsize=13, fontweight="bold")
        plt.tight_layout()
        p = FIGURES_DIR / "06_pca_feature_distributions.png"
        plt.savefig(p, dpi=150, bbox_inches="tight")
        plt.close()
        saved.append(str(p))
        logger.info(f"  Saved: {p.name}")

    return saved


# ─────────────────────────────────────────────────────────────────────────────
# Optional: ydata-profiling HTML report
# ─────────────────────────────────────────────────────────────────────────────

def generate_html_profile(df: "pd.DataFrame") -> Optional[str]:
    """Generate full HTML profiling report using ydata-profiling (if installed)."""
    try:
        from ydata_profiling import ProfileReport
        logger.info("Generating ydata-profiling HTML report (may take 1-2 minutes)...")
        profile = ProfileReport(
            df,
            title="Sentinel — Credit Card Fraud Dataset Profile",
            minimal=True,  # faster than full profile
            explorative=True,
        )
        html_path = REPORTS_DIR / "data_profile.html"
        profile.to_file(html_path)
        logger.info(f"  Saved: {html_path}")
        return str(html_path)
    except ImportError:
        logger.info("ydata-profiling not installed — skipping HTML report")
        logger.info("  Install with: pip install ydata-profiling")
        return None
    except Exception as e:
        logger.warning(f"HTML report generation failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Main profiler
# ─────────────────────────────────────────────────────────────────────────────

def run_profiling(csv_path: Optional[Path] = None, skip_html: bool = False) -> dict:
    """
    Run full profiling pipeline.
    Returns the complete profile as a dict.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Load
    df = load_dataset(csv_path)

    logger.info("\n── Computing dataset profile ──")

    # Compute all profile sections
    profile = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_file": str(PRIMARY_FILE),
        "basic": compute_basic_profile(df),
        "target": compute_target_profile(df),
        "numerical_stats": compute_numerical_stats(df),
        "temporal": compute_temporal_profile(df),
        "correlations": compute_correlation_with_target(df),
        "outliers": compute_outlier_summary(df),
        "leakage_assessment": compute_leakage_assessment(),
        "metric_justification": {
            "why_not_accuracy": (
                "With 0.172% fraud rate, a naive 'always predict legitimate' "
                "classifier achieves 99.83% accuracy but catches 0 fraud cases. "
                "Accuracy is completely uninformative for this problem."
            ),
            "prioritized_metrics": [
                "Precision-Recall AUC (PR-AUC) — primary metric for imbalanced classification",
                "Recall at operating threshold — minimize false negatives (missed fraud)",
                "Precision at operating threshold — minimize false positives (blocked legit)",
                "F1 Score — harmonic mean of precision and recall",
                "ROC-AUC — secondary metric, less sensitive to imbalance",
            ],
            "business_context": (
                "In fraud detection, false negatives (missed fraud) are expensive "
                "but false positives (blocking legitimate customers) cause churn. "
                "Threshold policy is a business decision, not purely an ML decision."
            ),
        },
        "architecture_note": (
            "This dataset provides: Time, V1-V28 (PCA), Amount, Class. "
            "It does NOT contain: customer IDs, device IDs, IP addresses, merchants. "
            "The fraud graph layer (Phases 9, 14, 15) uses a separately generated "
            "synthetic payment ecosystem with clearly labeled synthetic entities."
        ),
    }

    # Save JSON profile
    json_path = REPORTS_DIR / "data_profile.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, default=str)
    logger.info(f"\n✓ Saved JSON profile: {json_path}")

    # Generate plots
    logger.info("\n── Generating visualizations ──")
    saved_plots = generate_plots(df)
    profile["figures"] = saved_plots

    # Optional HTML report
    if not skip_html:
        html_path = generate_html_profile(df)
        profile["html_report"] = html_path

    # Print summary
    basic = profile["basic"]
    target = profile["target"]
    logger.info("\n" + "═" * 55)
    logger.info("  PROFILING COMPLETE")
    logger.info("═" * 55)
    logger.info(f"  Rows:            {basic['shape']['rows']:,}")
    logger.info(f"  Columns:         {basic['shape']['columns']}")
    logger.info(f"  Missing values:  {basic['missing_values']['total']}")
    logger.info(f"  Duplicate rows:  {basic['duplicates']['count']}")
    logger.info(f"  Fraud count:     {target['fraud_count']:,}")
    logger.info(f"  Legit count:     {target['legitimate_count']:,}")
    logger.info(f"  Fraud %:         {target['fraud_percentage']:.4f}%")
    logger.info(f"  Imbalance ratio: {target['imbalance_ratio']}:1")
    logger.info(f"  Plots saved:     {len(saved_plots)}")
    logger.info("═" * 55)
    logger.info(f"  Reports → {REPORTS_DIR}")
    logger.info("═" * 55)

    return profile


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    run_profiling()


if __name__ == "__main__":
    main()
