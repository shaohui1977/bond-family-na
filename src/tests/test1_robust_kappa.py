"""
test1_robust_kappa.py — Re-run Test 1 with kappa1 lower bound = 0.05.

Saves results to data/test1_robust_summary.csv (same format as test1_summary.csv).
Logs per-segment log-likelihood change vs the original kappa1_lo=0.01 run.

Log-likelihood proxy: sum of squared residuals of the bond_vol_func fit to
each eigenvector loading. Lower SSR = better fit given the tighter bound.

Usage:
    python src/tests/test1_robust_kappa.py
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
warnings.filterwarnings("ignore")

from src.models.pca import bond_vol_func, fit_two_factor_from_cov
from src.models.gaussian_hjm import extract_market_price_of_risk
from src.tests.test1_lambda_gap import (
    SEGMENT_CAPS, WINDOW, ALL_MATURITIES,
    run_segment, compute_lambda_gaps, run_statistical_tests,
)

DATA_DIR = PROJECT_ROOT / "data"

KAPPA1_LO_OLD = 0.01
KAPPA1_LO_NEW = 0.05


# ---------------------------------------------------------------------------
# Fit SSR for one window — used to compute log-likelihood proxy
# ---------------------------------------------------------------------------

def fit_ssr(cov: np.ndarray, maturities: np.ndarray, kappa1_lo: float) -> float | None:
    """
    Return sum of squared residuals from the two-factor exponential fit.
    Lower = better fit of the model to the eigenvector loadings.
    """
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    eigvals = np.maximum(eigvals[order], 0.0)
    eigvecs = eigvecs[:, order]
    total_ssr = 0.0
    for k in range(2):
        loading = eigvecs[:, k] * np.sqrt(eigvals[k])
        if loading[np.argmax(np.abs(loading))] < 0:
            loading = -loading
        kappa_lo = kappa1_lo if k == 0 else 0.1
        kappa_hi = 0.8 if k == 0 else 5.0
        kappa_init = max(0.15, kappa_lo) if k == 0 else 0.8
        try:
            popt, _ = curve_fit(
                bond_vol_func, maturities, loading,
                p0=[max(loading.max(), 1e-6), kappa_init],
                bounds=([1e-8, kappa_lo], [np.inf, kappa_hi]),
                maxfev=2000,
            )
            fitted = bond_vol_func(maturities, *popt)
            total_ssr += np.sum((loading - fitted) ** 2)
        except (RuntimeError, ValueError):
            return None
    return total_ssr


def segment_loglik_comparison(yields: pd.DataFrame, max_maturity: float,
                               sample_every: int = 10) -> dict:
    """
    Compare mean fit SSR under kappa1_lo=0.01 vs 0.05 for a segment.
    Samples every `sample_every` dates for speed.
    Returns dict with mean_ssr_old, mean_ssr_new, delta_log_lik (new - old, negative = worse).
    """
    mask = ALL_MATURITIES <= max_maturity + 1e-9
    seg_mats = ALL_MATURITIES[mask]
    seg_cols = []
    for T in seg_mats:
        label = f"y_{int(T)}" if T == int(T) else f"y_{T}"
        if label in yields.columns:
            seg_cols.append(label)
    seg_mats = np.array([float(c.replace("y_", "")) for c in seg_cols])

    y = yields[seg_cols].values
    log_p = -(y / 100.0) * seg_mats[None, :]
    dlp = np.diff(log_p, axis=0)

    ssrs_old, ssrs_new = [], []
    for i in range(WINDOW - 1, len(dlp), sample_every):
        cov = np.cov(dlp[i - WINDOW + 1 : i + 1, :].T)
        s_old = fit_ssr(cov, seg_mats, KAPPA1_LO_OLD)
        s_new = fit_ssr(cov, seg_mats, KAPPA1_LO_NEW)
        if s_old is not None and s_new is not None:
            ssrs_old.append(s_old)
            ssrs_new.append(s_new)

    if not ssrs_old:
        return {}

    mean_old = np.mean(ssrs_old)
    mean_new = np.mean(ssrs_new)
    n = len(seg_mats)
    # Log-likelihood proxy: -n/2 * log(SSR/n) — change is n/2 * log(SSR_old/SSR_new)
    delta_ll = (n / 2.0) * np.log(mean_old / mean_new) if mean_old > 0 else np.nan
    return {
        "mean_ssr_old": mean_old,
        "mean_ssr_new": mean_new,
        "delta_log_lik": delta_ll,  # positive = new bound is WORSE
        "n_windows": len(ssrs_old),
    }


def main() -> None:
    yields = pd.read_parquet(DATA_DIR / "ecb_yield_curves.parquet")
    yields.index = pd.to_datetime(yields.index)
    yields.columns = [f"y_{int(T)}" if T == int(T) else f"y_{T}"
                      for T in [0.25, 0.5, 1, 2, 3, 5, 7, 10, 15, 20, 25, 30]]

    print(f"Re-running Test 1 with kappa1_lo = {KAPPA1_LO_NEW} (was {KAPPA1_LO_OLD})\n")

    # --- Log-likelihood comparison per segment ---
    print("Log-likelihood comparison (SSR of eigenvector fits):")
    print(f"{'Segment':<12} {'SSR_old':>12} {'SSR_new':>12} {'delta_ll':>12}  interpretation")
    print("-" * 65)
    for cap in SEGMENT_CAPS:
        ll = segment_loglik_comparison(yields, cap)
        if ll:
            interp = "new worse" if ll["delta_log_lik"] > 0 else "new better"
            print(f"<={int(cap)}Y{'':<8} {ll['mean_ssr_old']:>12.2e} {ll['mean_ssr_new']:>12.2e} "
                  f"{ll['delta_log_lik']:>12.3f}  {interp}  (n={ll['n_windows']})")

    # --- Re-run segments with new bound ---
    print(f"\nRunning segments with kappa1_lo = {KAPPA1_LO_NEW} ...")
    seg_results = {}
    for cap in SEGMENT_CAPS:
        print(f"  Segment <={int(cap)}Y ...", end=" ", flush=True)
        df = run_segment(yields, cap, kappa1_lo=KAPPA1_LO_NEW)
        seg_results[cap] = df
        if df.empty:
            print("EMPTY")
            continue
        mean_k1 = df["kappa1"].mean()
        at_bound = (df["kappa1"] < KAPPA1_LO_NEW + 0.001).mean()
        print(f"mean_kappa1={mean_k1:.4f}  at-bound={at_bound:.1%}  R2={df['r_squared'].mean():.3f}")

    # --- Lambda gaps + stats ---
    gaps = compute_lambda_gaps(seg_results)
    summary = run_statistical_tests(gaps)
    out_path = DATA_DIR / "test1_robust_summary.csv"
    summary.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}")

    # --- Side-by-side vs original ---
    orig = pd.read_csv(DATA_DIR / "test1_summary.csv")
    print(f"\n{'Pair':<14} {'mean_dL1_orig':>14} {'mean_dL1_rob':>14} {'t_orig':>9} {'t_rob':>9} {'p_adj_rob':>10}")
    print("-" * 75)
    for i, row in summary.iterrows():
        orig_row = orig[(orig["T_short"] == row["T_short"]) & (orig["T_long"] == row["T_long"])]
        if orig_row.empty:
            continue
        o = orig_row.iloc[0]
        print(f"{int(row['T_short'])}Y-{int(row['T_long'])}Y{'':<7}"
              f" {o['mean_dlambda1']:>14.4f} {row['mean_dlambda1']:>14.4f}"
              f" {o['t_stat_dlambda1']:>9.2f} {row['t_stat_dlambda1']:>9.2f}"
              f" {row['p_adj_dlambda1']:>10.4f}")

    n_sig_new = (summary["p_adj_dlambda1"] < 0.05).sum()
    n_sig_old = (orig["p_adj_dlambda1"] < 0.05).sum()
    print(f"\nPairs rejected (Bonf. 5%): original={n_sig_old}/15, robust={n_sig_new}/15")
    print("Done.")


if __name__ == "__main__":
    main()
