"""
test3_robustness.py — Test 3: Three-factor Gaussian HJM robustness check.

Repeats Test 1 (market price of risk stability) using a three-factor model
with a curvature (hump-shaped) factor:

  sigma1(tau) = sigma1 * exp(-kappa1*tau)              [level]
  sigma2(tau) = sigma2 * exp(-kappa2*tau)              [slope]
  sigma3(tau) = sigma3 * tau * exp(-kappa3*tau)        [curvature]

Key question: do the lambda1 gaps shrink when the curvature factor absorbs
the cross-sectional variation that the two-factor model attributes to lambda
inconsistency?

Outputs:
  data/test3_summary.csv        — same format as test1_summary.csv
  data/test3_vs_test1.csv       — side-by-side comparison per segment pair

Usage:
    python src/tests/test3_robustness.py
"""

import sys
import warnings
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
warnings.filterwarnings("ignore")

from src.models.pca import fit_three_factor_from_cov
from src.models.gaussian_hjm import extract_market_price_of_risk_3factor
from src.utils.statistics import newey_west_ttest, bonferroni_correction
from src.tests.test1_lambda_gap import (
    SEGMENT_CAPS, WINDOW, ALL_MATURITIES, compute_lambda_gaps, run_statistical_tests,
)

DATA_DIR = PROJECT_ROOT / "data"
FIGURES_DIR = PROJECT_ROOT / "paper" / "figures"


# ---------------------------------------------------------------------------
# Column name helper (mirrors test1)
# ---------------------------------------------------------------------------

def _seg_cols(yields_cols, max_maturity):
    mask = ALL_MATURITIES <= max_maturity + 1e-9
    seg_mats = ALL_MATURITIES[mask]
    cols = []
    for T in seg_mats:
        label = f"y_{int(T)}" if T == int(T) else f"y_{T}"
        if label in yields_cols:
            cols.append(label)
    mats = np.array([float(c.replace("y_", "")) for c in cols])
    return cols, mats


# ---------------------------------------------------------------------------
# Per-segment pipeline (3-factor)
# ---------------------------------------------------------------------------

def run_segment_3f(yields: pd.DataFrame, max_maturity: float) -> pd.DataFrame:
    """
    Three-factor version of run_segment from test1.
    Returns DataFrame with sigma1..3, kappa1..3, explained_var_ratio,
    lambda1..3, r_squared, indexed by date.
    """
    seg_cols, seg_mats = _seg_cols(yields.columns.tolist(), max_maturity)

    if len(seg_cols) < 5:
        raise ValueError(f"Segment <={max_maturity}Y: only {len(seg_cols)} maturities (need >=5).")

    yields_seg = yields[seg_cols].copy()
    log_p = -(yields_seg.values / 100.0) * seg_mats[None, :]
    dlp = np.diff(log_p, axis=0)
    dates = yields_seg.index[1:]

    results = []
    for i in range(WINDOW - 1, len(dlp)):
        date = dates[i]
        cov = np.cov(dlp[i - WINDOW + 1 : i + 1, :].T)
        vol = fit_three_factor_from_cov(cov, seg_mats, kappa1_lo=0.01)
        if vol is None:
            continue

        sigma = np.array([vol["sigma1"], vol["sigma2"], vol["sigma3"]])
        kappa = np.array([vol["kappa1"], vol["kappa2"], vol["kappa3"]])
        y_obs = yields_seg.loc[date].values
        lam, r2 = extract_market_price_of_risk_3factor(y_obs, seg_mats, sigma, kappa)

        results.append({
            "date": date,
            "sigma1": vol["sigma1"], "kappa1": vol["kappa1"],
            "sigma2": vol["sigma2"], "kappa2": vol["kappa2"],
            "sigma3": vol["sigma3"], "kappa3": vol["kappa3"],
            "explained_var_ratio": vol["explained_var_ratio"],
            "lambda1": lam[0], "lambda2": lam[1], "lambda3": lam[2],
            "r_squared": r2,
        })

    return pd.DataFrame(results).set_index("date") if results else pd.DataFrame()


# ---------------------------------------------------------------------------
# Lambda gaps (3-factor version — same logic, 3 lambda columns)
# ---------------------------------------------------------------------------

def compute_lambda_gaps_3f(seg_results: dict) -> pd.DataFrame:
    """Compute pairwise Δλ₁, Δλ₂, Δλ₃ across all segment pairs."""
    records = []
    caps = sorted(seg_results.keys())
    lambda_cols = ["lambda1", "lambda2", "lambda3"]

    for T_j, T_k in combinations(caps, 2):
        df_j = seg_results[T_j][lambda_cols + ["r_squared"]]
        df_k = seg_results[T_k][lambda_cols + ["r_squared"]]
        common = df_j.index.intersection(df_k.index)
        if len(common) == 0:
            continue

        pair = pd.DataFrame({
            "segment_short": T_j,
            "segment_long": T_k,
            "delta_lambda1": df_k.loc[common, "lambda1"].values - df_j.loc[common, "lambda1"].values,
            "delta_lambda2": df_k.loc[common, "lambda2"].values - df_j.loc[common, "lambda2"].values,
            "delta_lambda3": df_k.loc[common, "lambda3"].values - df_j.loc[common, "lambda3"].values,
            "r_squared_short": df_j.loc[common, "r_squared"].values,
            "r_squared_long":  df_k.loc[common, "r_squared"].values,
        }, index=common)
        records.append(pair)

    return pd.concat(records).sort_index() if records else pd.DataFrame()


# ---------------------------------------------------------------------------
# Statistical tests (3-factor — same NW/Bonferroni logic extended)
# ---------------------------------------------------------------------------

def run_statistical_tests_3f(gaps: pd.DataFrame) -> pd.DataFrame:
    pairs = gaps.groupby(["segment_short", "segment_long"])
    rows = []
    for (T_j, T_k), group in pairs:
        r1 = newey_west_ttest(group["delta_lambda1"])
        r2 = newey_west_ttest(group["delta_lambda2"])
        r3 = newey_west_ttest(group["delta_lambda3"])
        rows.append({
            "T_short": T_j, "T_long": T_k, "n_obs": len(group),
            "mean_dlambda1": r1["mean"], "std_nw_dlambda1": r1["std_nw"],
            "t_stat_dlambda1": r1["t_stat"], "p_value_dlambda1": r1["p_value"],
            "mean_dlambda2": r2["mean"], "std_nw_dlambda2": r2["std_nw"],
            "t_stat_dlambda2": r2["t_stat"], "p_value_dlambda2": r2["p_value"],
            "mean_dlambda3": r3["mean"], "std_nw_dlambda3": r3["std_nw"],
            "t_stat_dlambda3": r3["t_stat"], "p_value_dlambda3": r3["p_value"],
        })

    summary = pd.DataFrame(rows)
    if summary.empty:
        return summary

    all_p = np.concatenate([
        summary["p_value_dlambda1"].values,
        summary["p_value_dlambda2"].values,
        summary["p_value_dlambda3"].values,
    ])
    all_p_adj = bonferroni_correction(all_p)
    n = len(summary)
    summary["p_adj_dlambda1"] = all_p_adj[:n]
    summary["p_adj_dlambda2"] = all_p_adj[n:2*n]
    summary["p_adj_dlambda3"] = all_p_adj[2*n:]
    return summary


# ---------------------------------------------------------------------------
# Comparison table: 2-factor vs 3-factor per pair
# ---------------------------------------------------------------------------

def build_comparison(summary3: pd.DataFrame) -> pd.DataFrame:
    summary1 = pd.read_csv(DATA_DIR / "test1_summary.csv")
    rows = []
    for _, r3 in summary3.iterrows():
        r1 = summary1[
            (summary1["T_short"] == r3["T_short"]) &
            (summary1["T_long"]  == r3["T_long"])
        ]
        if r1.empty:
            continue
        r1 = r1.iloc[0]
        rows.append({
            "T_short": r3["T_short"],
            "T_long":  r3["T_long"],
            "mean_dlambda1_2f": r1["mean_dlambda1"],
            "mean_dlambda1_3f": r3["mean_dlambda1"],
            "t_stat_dlambda1_2f": r1["t_stat_dlambda1"],
            "t_stat_dlambda1_3f": r3["t_stat_dlambda1"],
            "p_adj_dlambda1_2f": r1["p_adj_dlambda1"],
            "p_adj_dlambda1_3f": r3["p_adj_dlambda1"],
            "mean_dlambda2_2f": r1["mean_dlambda2"],
            "mean_dlambda2_3f": r3["mean_dlambda2"],
            "t_stat_dlambda2_2f": r1["t_stat_dlambda2"],
            "t_stat_dlambda2_3f": r3["t_stat_dlambda2"],
            "mean_dlambda3_3f": r3["mean_dlambda3"],
            "t_stat_dlambda3_3f": r3["t_stat_dlambda3"],
            "p_adj_dlambda3_3f": r3["p_adj_dlambda3"],
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Plot: lambda1 gap shrinkage heatmap (2f vs 3f)
# ---------------------------------------------------------------------------

def plot_gap_shrinkage(comparison: pd.DataFrame) -> None:
    caps = sorted(SEGMENT_CAPS)
    n = len(caps)
    cap_idx = {c: i for i, c in enumerate(caps)}

    mat2 = np.full((n, n), np.nan)
    mat3 = np.full((n, n), np.nan)

    for _, row in comparison.iterrows():
        i, j = cap_idx[row["T_short"]], cap_idx[row["T_long"]]
        mat2[i, j] = mat2[j, i] = abs(row["mean_dlambda1_2f"])
        mat3[i, j] = mat3[j, i] = abs(row["mean_dlambda1_3f"])

    labels = [f"{int(c)}Y" for c in caps]
    vmax = max(np.nanmax(mat2), np.nanmax(mat3))

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, mat, title in zip(axes, [mat2, mat3], ["2-factor", "3-factor"]):
        im = ax.imshow(mat, cmap="YlOrRd", vmin=0, vmax=vmax)
        plt.colorbar(im, ax=ax, label="Mean |Δλ₁|")
        ax.set_xticks(range(n)); ax.set_xticklabels(labels)
        ax.set_yticks(range(n)); ax.set_yticklabels(labels)
        ax.set_title(f"Mean |Δλ₁| — {title}")
        for i in range(n):
            for j in range(n):
                if not np.isnan(mat[i, j]):
                    ax.text(j, i, f"{mat[i,j]:.3f}", ha="center", va="center", fontsize=7)

    fig.suptitle("Test 3: Lambda Gap Shrinkage — 2-factor vs 3-factor", fontsize=12)
    plt.tight_layout()
    out = FIGURES_DIR / "test3_gap_shrinkage.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    yields = pd.read_parquet(DATA_DIR / "ecb_yield_curves.parquet")
    yields.index = pd.to_datetime(yields.index)
    yields.columns = [
        f"y_{int(T)}" if T == int(T) else f"y_{T}"
        for T in [0.25, 0.5, 1, 2, 3, 5, 7, 10, 15, 20, 25, 30]
    ]
    print(f"Loaded {len(yields)} observations.\n")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # --- Run each segment ---
    seg_results = {}
    for cap in SEGMENT_CAPS:
        print(f"Segment <={int(cap)}Y ...", end=" ", flush=True)
        try:
            df = run_segment_3f(yields, cap)
        except ValueError as e:
            print(f"SKIP ({e})")
            continue
        seg_results[cap] = df
        if df.empty:
            print("EMPTY")
            continue
        ev  = df["explained_var_ratio"].mean()
        r2  = df["r_squared"].mean()
        k3  = df["kappa3"].mean()
        s3  = df["sigma3"].mean()
        print(f"n={len(df)}  ev={ev:.3f}  R2={r2:.3f}  mean_kappa3={k3:.3f}  mean_sigma3={s3:.5f}")
        if ev < 0.97:
            print(f"  WARNING: mean explained variance {ev:.3f} < 0.97")

    # --- Lambda gaps + stats ---
    print("\nComputing lambda gaps (3-factor) ...")
    gaps = compute_lambda_gaps_3f(seg_results)
    summary = run_statistical_tests_3f(gaps)
    summary.to_csv(DATA_DIR / "test3_summary.csv", index=False)
    print("Saved test3_summary.csv")

    # --- Comparison with Test 1 ---
    comparison = build_comparison(summary)
    comparison.to_csv(DATA_DIR / "test3_vs_test1.csv", index=False)
    print("Saved test3_vs_test1.csv")

    # --- Console output ---
    n_sig2 = (pd.read_csv(DATA_DIR / "test1_summary.csv")["p_adj_dlambda1"] < 0.05).sum()
    n_sig3 = (summary["p_adj_dlambda1"] < 0.05).sum()
    print(f"\n=== TEST 3 SUMMARY (lambda1 gaps) ===")
    print(f"Pairs rejected 2-factor: {n_sig2}/15  |  3-factor: {n_sig3}/15")

    print(f"\n{'Pair':<10} {'dL1_2f':>9} {'dL1_3f':>9} {'t_2f':>7} {'t_3f':>7} "
          f"{'dL2_2f':>9} {'dL2_3f':>9} {'dL3_3f':>9}  shrinks?")
    print("-" * 82)
    for _, row in comparison.iterrows():
        shrinks = abs(row["mean_dlambda1_3f"]) < abs(row["mean_dlambda1_2f"])
        marker = "YES" if shrinks else "no"
        print(f"{int(row['T_short'])}Y-{int(row['T_long'])}Y{'':<3}"
              f" {row['mean_dlambda1_2f']:>9.4f} {row['mean_dlambda1_3f']:>9.4f}"
              f" {row['t_stat_dlambda1_2f']:>7.2f} {row['t_stat_dlambda1_3f']:>7.2f}"
              f" {row['mean_dlambda2_2f']:>9.4f} {row['mean_dlambda2_3f']:>9.4f}"
              f" {row['mean_dlambda3_3f']:>9.4f}  {marker}")

    # --- Plot ---
    print("\nGenerating plot ...")
    plot_gap_shrinkage(comparison)
    print("Done.")


if __name__ == "__main__":
    main()
