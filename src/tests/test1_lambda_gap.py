"""
test1_lambda_gap.py — Test 1: Market Price of Risk Stability

For each date, calibrate the two-factor Gaussian HJM independently on
maturity segments I_k = {maturities ≤ T_k} for T_k in {5,10,15,20,25,30}.
Compare the extracted market prices of risk λ^(k) across segments.

H₀: Δλ(t; j,k) = λ^(k)(t) - λ^(j)(t) = 0  (consistency)
H₁: Δλ depends systematically on |T_k - T_j|  (inconsistency)

Usage:
    python src/tests/test1_lambda_gap.py
"""

import sys
import warnings
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.pca import estimate_for_segment, fit_two_factor_from_cov
from src.models.gaussian_hjm import extract_market_price_of_risk
from src.utils.statistics import newey_west_ttest, bonferroni_correction

DATA_DIR = PROJECT_ROOT / "data"
FIGURES_DIR = PROJECT_ROOT / "paper" / "figures"

WINDOW = 60  # rolling window in trading days
SEGMENT_CAPS = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
ALL_MATURITIES = np.array([0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 25.0, 30.0])
COL_NAMES = [f"y_{T}" for T in [0.25, 0.5, 1, 2, 3, 5, 7, 10, 15, 20, 25, 30]]


# ---------------------------------------------------------------------------
# Step 1: For each segment cap, run rolling PCA + lambda extraction
# ---------------------------------------------------------------------------

def run_segment(yields: pd.DataFrame, max_maturity: float, kappa1_lo: float = 0.01) -> pd.DataFrame:
    """
    Run the full pipeline for one segment cap.
    Returns DataFrame indexed by date with: sigma1, kappa1, sigma2, kappa2,
    explained_var_ratio, lambda1, lambda2, r_squared.
    """
    mask = ALL_MATURITIES <= max_maturity + 1e-9
    seg_mats = ALL_MATURITIES[mask]
    # Build column names matching exactly what fetch_ecb.py wrote
    seg_cols = []
    for T in seg_mats:
        # Integer maturities stored without decimal (y_1 not y_1.0)
        label = f"y_{int(T)}" if T == int(T) else f"y_{T}"
        if label in yields.columns:
            seg_cols.append(label)
    seg_mats = np.array([float(c.replace("y_", "")) for c in seg_cols])

    if len(seg_cols) < 4:
        raise ValueError(f"Segment ≤{max_maturity}Y: only {len(seg_cols)} maturities.")

    yields_seg = yields[seg_cols].copy()

    # Bond log-returns
    log_p = -(yields_seg.values / 100.0) * seg_mats[np.newaxis, :]
    dlp = np.diff(log_p, axis=0)
    dates = yields_seg.index[1:]

    results = []
    n = len(dlp)

    for i in range(WINDOW - 1, n):
        date = dates[i]
        window_data = dlp[i - WINDOW + 1 : i + 1, :]
        cov = np.cov(window_data.T)

        vol = fit_two_factor_from_cov(cov, seg_mats, kappa1_lo=kappa1_lo)
        if vol is None:
            continue

        sigma = np.array([vol["sigma1"], vol["sigma2"]])
        kappa = np.array([vol["kappa1"], vol["kappa2"]])

        # Cross-sectional lambda extraction uses yields on date `date`
        y_obs = yields_seg.loc[date].values
        lam, r2 = extract_market_price_of_risk(y_obs, seg_mats, sigma, kappa)

        results.append({
            "date": date,
            "sigma1": vol["sigma1"],
            "kappa1": vol["kappa1"],
            "sigma2": vol["sigma2"],
            "kappa2": vol["kappa2"],
            "explained_var_ratio": vol["explained_var_ratio"],
            "lambda1": lam[0],
            "lambda2": lam[1],
            "r_squared": r2,
        })

    if not results:
        return pd.DataFrame()
    return pd.DataFrame(results).set_index("date")


# ---------------------------------------------------------------------------
# Step 2: Compute lambda gaps for all segment pairs
# ---------------------------------------------------------------------------

def compute_lambda_gaps(seg_results: dict[float, pd.DataFrame]) -> pd.DataFrame:
    """
    For each pair (T_j, T_k) with j < k, compute daily Δλ_i = λ_i^(k) - λ_i^(j).
    Returns DataFrame with columns: segment_short, segment_long, delta_lambda1,
    delta_lambda2, plus vol params for both segments.
    """
    records = []
    caps = sorted(seg_results.keys())

    for T_j, T_k in combinations(caps, 2):
        df_j = seg_results[T_j][["lambda1", "lambda2", "sigma1", "kappa1",
                                   "sigma2", "kappa2", "r_squared", "explained_var_ratio"]]
        df_k = seg_results[T_k][["lambda1", "lambda2", "sigma1", "kappa1",
                                   "sigma2", "kappa2", "r_squared", "explained_var_ratio"]]

        common = df_j.index.intersection(df_k.index)
        if len(common) == 0:
            continue

        dj = df_j.loc[common]
        dk = df_k.loc[common]

        pair_df = pd.DataFrame({
            "segment_short": T_j,
            "segment_long": T_k,
            "delta_lambda1": dk["lambda1"].values - dj["lambda1"].values,
            "delta_lambda2": dk["lambda2"].values - dj["lambda2"].values,
            "sigma1_short": dj["sigma1"].values,
            "kappa1_short": dj["kappa1"].values,
            "sigma2_short": dj["sigma2"].values,
            "kappa2_short": dj["kappa2"].values,
            "r_squared_short": dj["r_squared"].values,
            "sigma1_long": dk["sigma1"].values,
            "kappa1_long": dk["kappa1"].values,
            "sigma2_long": dk["sigma2"].values,
            "kappa2_long": dk["kappa2"].values,
            "r_squared_long": dk["r_squared"].values,
        }, index=common)
        records.append(pair_df)

    if not records:
        return pd.DataFrame()
    return pd.concat(records).sort_index()


# ---------------------------------------------------------------------------
# Step 3: Statistical tests
# ---------------------------------------------------------------------------

def run_statistical_tests(gaps: pd.DataFrame) -> pd.DataFrame:
    """
    For each segment pair, test H₀: E[Δλ₁] = 0 and E[Δλ₂] = 0
    using Newey-West t-tests with Bonferroni correction.
    """
    pairs = gaps.groupby(["segment_short", "segment_long"])
    rows = []

    for (T_j, T_k), group in pairs:
        res1 = newey_west_ttest(group["delta_lambda1"])
        res2 = newey_west_ttest(group["delta_lambda2"])
        rows.append({
            "T_short": T_j,
            "T_long": T_k,
            "n_obs": len(group),
            "mean_dlambda1": res1["mean"],
            "std_nw_dlambda1": res1["std_nw"],
            "t_stat_dlambda1": res1["t_stat"],
            "p_value_dlambda1": res1["p_value"],
            "mean_dlambda2": res2["mean"],
            "std_nw_dlambda2": res2["std_nw"],
            "t_stat_dlambda2": res2["t_stat"],
            "p_value_dlambda2": res2["p_value"],
        })

    summary = pd.DataFrame(rows)
    if summary.empty:
        return summary

    # Bonferroni correction across all pairs
    p1 = summary["p_value_dlambda1"].values
    p2 = summary["p_value_dlambda2"].values
    all_p = np.concatenate([p1, p2])
    all_p_adj = bonferroni_correction(all_p)
    n_pairs = len(summary)
    summary["p_adj_dlambda1"] = all_p_adj[:n_pairs]
    summary["p_adj_dlambda2"] = all_p_adj[n_pairs:]

    return summary


# ---------------------------------------------------------------------------
# Step 4: Plots
# ---------------------------------------------------------------------------

def plot_timeseries(gaps: pd.DataFrame, seg_results: dict) -> None:
    """Time series of Δλ₁(t; 5Y, 30Y) with ±2 NW std bands."""
    sub = gaps[(gaps["segment_short"] == 5.0) & (gaps["segment_long"] == 30.0)].copy()
    if sub.empty:
        print("WARNING: no data for 5Y-30Y gap.")
        return

    res = newey_west_ttest(sub["delta_lambda1"])
    std_nw = res["std_nw"]
    mean_dl = res["mean"]

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(sub.index, sub["delta_lambda1"], color="#1f77b4", linewidth=0.8, label="Δλ₁ (5Y→30Y)")
    ax.axhline(mean_dl, color="navy", linewidth=1.0, linestyle="--", label=f"Mean = {mean_dl:.3f}")
    ax.axhline(mean_dl + 2 * std_nw, color="red", linewidth=0.7, linestyle=":", alpha=0.7)
    ax.axhline(mean_dl - 2 * std_nw, color="red", linewidth=0.7, linestyle=":", alpha=0.7, label="±2 NW std")
    ax.fill_between(sub.index, mean_dl - 2 * std_nw, mean_dl + 2 * std_nw, alpha=0.1, color="red")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xlabel("Date")
    ax.set_ylabel("Δλ₁")
    ax.set_title("Test 1: Market Price of Risk Gap Δλ₁(t; 5Y→30Y)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = FIGURES_DIR / "test1_lambda_gap_timeseries.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out}")


def plot_heatmap(summary: pd.DataFrame) -> None:
    """Heatmap of mean |Δλ₁| for each (T_j, T_k) pair."""
    caps = sorted(SEGMENT_CAPS)
    n = len(caps)
    mat = np.full((n, n), np.nan)
    cap_idx = {c: i for i, c in enumerate(caps)}

    for _, row in summary.iterrows():
        i = cap_idx[row["T_short"]]
        j = cap_idx[row["T_long"]]
        mat[i, j] = abs(row["mean_dlambda1"])
        mat[j, i] = abs(row["mean_dlambda1"])

    fig, ax = plt.subplots(figsize=(7, 6))
    labels = [f"{int(c)}Y" for c in caps]
    im = ax.imshow(mat, cmap="YlOrRd", aspect="auto", vmin=0)
    plt.colorbar(im, ax=ax, label="Mean |Δλ₁|")
    ax.set_xticks(range(n)); ax.set_xticklabels(labels)
    ax.set_yticks(range(n)); ax.set_yticklabels(labels)
    ax.set_title("Test 1: Mean |Δλ₁| by Segment Pair")

    for i in range(n):
        for j in range(n):
            if not np.isnan(mat[i, j]):
                ax.text(j, i, f"{mat[i,j]:.2f}", ha="center", va="center", fontsize=8)

    plt.tight_layout()
    out = FIGURES_DIR / "test1_lambda_gap_heatmap.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out}")


def plot_parameter_stability(seg_results: dict) -> None:
    """Time series of σ₁, κ₁, σ₂, κ₂ for the 30Y (full) segment."""
    df = seg_results.get(30.0)
    if df is None or df.empty:
        return

    fig, axes = plt.subplots(2, 2, figsize=(12, 6), sharex=True)
    fig.suptitle("Parameter Stability — Full Segment (≤30Y)", fontsize=12)

    for ax, col, label in zip(
        axes.flat,
        ["sigma1", "kappa1", "sigma2", "kappa2"],
        ["σ₁", "κ₁", "σ₂", "κ₂"],
    ):
        ax.plot(df.index, df[col], linewidth=0.8)
        ax.set_title(label)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = FIGURES_DIR / "test1_parameter_stability.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Load data
    yields = pd.read_parquet(DATA_DIR / "ecb_yield_curves.parquet")
    yields.index = pd.to_datetime(yields.index)
    yields.columns = COL_NAMES
    print(f"Loaded {len(yields)} observations.")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # --- Run each segment ---
    seg_results: dict[float, pd.DataFrame] = {}
    for cap in SEGMENT_CAPS:
        print(f"\nSegment <={int(cap)}Y ...")
        df = run_segment(yields, cap)
        seg_results[cap] = df
        if df.empty:
            print(f"  WARNING: no results for segment <={int(cap)}Y")
            continue

        # Sanity checks
        mean_ev = df["explained_var_ratio"].mean()
        mean_r2 = df["r_squared"].mean()
        print(f"  Dates: {len(df)} | Mean explained var: {mean_ev:.3f} | Mean R2: {mean_r2:.3f}")
        if mean_ev < 0.95:
            print(f"  WARNING: mean explained variance {mean_ev:.3f} < 0.95 -- 2-factor model may be inadequate.")
        if mean_r2 < 0.9:
            print(f"  WARNING: mean OLS R2 {mean_r2:.3f} < 0.9")

    # --- Lambda gaps ---
    print("\nComputing lambda gaps ...")
    gaps = compute_lambda_gaps(seg_results)
    if gaps.empty:
        print("ERROR: no lambda gaps computed. Check segment results.")
        return

    gaps.to_parquet(DATA_DIR / "test1_results.parquet")
    print(f"Saved test1_results.parquet ({len(gaps)} rows).")

    # --- Statistical tests ---
    print("\nRunning statistical tests ...")
    summary = run_statistical_tests(gaps)
    summary.to_csv(DATA_DIR / "test1_summary.csv", index=False)
    print("Saved test1_summary.csv")

    # --- Console summary ---
    n_dates = seg_results[30.0].index.nunique() if 30.0 in seg_results else 0
    n_pairs = len(summary)
    if n_pairs > 0:
        sig1 = (summary["p_adj_dlambda1"] < 0.05).sum()
        sig2 = (summary["p_adj_dlambda2"] < 0.05).sum()
        max_gap1 = gaps["delta_lambda1"].abs().max()
        print(f"\n=== TEST 1 SUMMARY ===")
        print(f"Dates tested (30Y segment): {n_dates}")
        print(f"Segment pairs: {n_pairs}")
        print(f"Pairs where H0 rejected (d_lambda1, Bonf. 5%): {sig1}/{n_pairs}")
        print(f"Pairs where H0 rejected (d_lambda2, Bonf. 5%): {sig2}/{n_pairs}")
        print(f"Max |d_lambda1| observed: {max_gap1:.4f}")
        print("\nPer-pair results:")
        print(summary[["T_short","T_long","n_obs","mean_dlambda1","t_stat_dlambda1",
                        "p_adj_dlambda1","mean_dlambda2","t_stat_dlambda2","p_adj_dlambda2"]
               ].to_string(index=False, float_format="{:.3f}".format))

    # --- Plots ---
    print("\nGenerating plots ...")
    plot_timeseries(gaps, seg_results)
    plot_heatmap(summary)
    plot_parameter_stability(seg_results)
    print("\nDone.")


if __name__ == "__main__":
    main()
