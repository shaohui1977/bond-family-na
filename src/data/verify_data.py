"""
verify_data.py — Sanity-check plots for the ECB yield curve dataset.

Generates paper/figures/yield_curve_overview.png with:
  (a) Yield curve shapes on 3 representative dates
  (b) Time series of 2Y, 10Y, 30Y yields

Usage:
    python src/data/verify_data.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
FIGURES_DIR = PROJECT_ROOT / "paper" / "figures"

MATURITIES = np.array([0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 25.0, 30.0])
MAT_LABELS = ["3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "15Y", "20Y", "25Y", "30Y"]
COLUMNS = [f"y_{T}" for T in [0.25, 0.5, 1, 2, 3, 5, 7, 10, 15, 20, 25, 30]]


def find_nearest_date(df: pd.DataFrame, target: str) -> pd.Timestamp:
    """Return the closest available date to target (within ±5 business days)."""
    target_ts = pd.Timestamp(target)
    idx = df.index
    # Find nearest
    nearest = idx[np.argmin(np.abs(idx - target_ts))]
    return nearest


def main() -> None:
    # Load data
    parquet_path = DATA_DIR / "ecb_yield_curves.parquet"
    df = pd.read_parquet(parquet_path)
    df.index = pd.to_datetime(df.index)
    print(f"Loaded {len(df)} observations from {df.index[0].date()} to {df.index[-1].date()}")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("ECB AAA EUR Government Bond Yield Curves (2014–2024)", fontsize=13)

    # --- Panel (a): Yield curve shapes on 3 representative dates ---
    ax = axes[0]
    dates_labels = [
        ("2015-01-02", "Jan 2015 (negative rates)"),
        ("2019-01-02", "Jan 2019 (low positive rates)"),
        ("2023-07-03", "Jul 2023 (post-tightening)"),
    ]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for (target, label), color in zip(dates_labels, colors):
        date = find_nearest_date(df, target)
        row = df.loc[date, COLUMNS].values
        ax.plot(MATURITIES, row, marker="o", markersize=4, label=f"{label}\n({date.date()})", color=color)
        print(f"  Curve date: {date.date()} (requested {target})")

    ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
    ax.set_xlabel("Maturity (years)")
    ax.set_ylabel("Zero-coupon yield (% p.a.)")
    ax.set_title("(a) Yield Curve Shapes")
    ax.set_xticks(MATURITIES)
    ax.set_xticklabels(MAT_LABELS, rotation=45, ha="right", fontsize=8)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # --- Panel (b): Time series of 2Y, 10Y, 30Y ---
    ax2 = axes[1]
    ts_cols = {"y_2": "2Y", "y_10": "10Y", "y_30": "30Y"}
    ts_colors = ["#9467bd", "#d62728", "#8c564b"]

    for (col, label), color in zip(ts_cols.items(), ts_colors):
        ax2.plot(df.index, df[col], linewidth=0.8, label=label, color=color)

    ax2.axhline(0, color="black", linewidth=0.5, linestyle="--")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Zero-coupon yield (% p.a.)")
    ax2.set_title("(b) Key Maturity Time Series")
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = FIGURES_DIR / "yield_curve_overview.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"\nSaved figure: {out_path}")
    plt.close()


if __name__ == "__main__":
    main()
