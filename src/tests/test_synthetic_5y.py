"""
test_synthetic_5y.py — Synthetic validation with 5Y-segment DGP.

Robustness check: re-run the synthetic validation using median parameters
from the 5Y segment (maturities ≤ 5Y) as the DGP instead of the 30Y segment.

Research question: Does the 5Y DGP produce the same uniform-bias pattern
(synthetic 3F gaps near zero) as the 30Y DGP? If yes, the finding is robust
to DGP choice. If the 5Y DGP produces divergent gaps, the validation is
compromised because short-segment parameters may under-identify curvature.

Output:
  data/synthetic_5y_yields.csv        — synthetic yields under 5Y DGP
  data/synthetic_5y_dgp_params.json   — 5Y DGP parameters
  data/synthetic_5y_summary.csv       — 4-column comparison table

Comparison table columns:
  T_short, T_long,
  emp_3f_mean    (empirical 3F Δλ₁),
  syn30y_3f_mean (synthetic 30Y DGP 3F Δλ₁, loaded from synthetic_summary.csv),
  syn5y_3f_mean  (synthetic 5Y DGP 3F Δλ₁, computed here)

Usage:
    python src/tests/test_synthetic_5y.py [--quick]
"""

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

warnings.filterwarnings("ignore")

from src.models.pca import fit_three_factor_from_cov
from src.models.gaussian_hjm import (
    risk_premium_basis_3factor,
    extract_market_price_of_risk_3factor,
)
from src.synthetic.generate_yields import build_synthetic_yields, SEED, SIGMA_NOISE
from src.tests.test1_lambda_gap import WINDOW, ALL_MATURITIES, SEGMENT_CAPS
from src.tests.test_synthetic import run_2factor_pipeline, run_3factor_pipeline

DATA_DIR = PROJECT_ROOT / "data"

COL_NAMES_ALL = [
    f"y_{int(T)}" if T == int(T) else f"y_{T}"
    for T in ALL_MATURITIES
]

# 5Y segment: maturities ≤ 5Y
SEG_5Y_MATS = ALL_MATURITIES[ALL_MATURITIES <= 5.0 + 1e-9]  # [0.25, 0.5, 1, 2, 3, 5]
SEG_5Y_COLS = [
    f"y_{int(T)}" if T == int(T) else f"y_{T}"
    for T in SEG_5Y_MATS
]


# ---------------------------------------------------------------------------
# Extract DGP parameters from 5Y 3-factor calibration
# ---------------------------------------------------------------------------

def extract_5y_3factor_params(yields: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """
    Run rolling 3-factor PCA + cross-sectional regression on the 5Y segment.

    Returns
    -------
    dgp  : dict with sigma_star, kappa_star, lambda_star, lambda_std (lists of 3)
    lambda_df : per-date lambda time series
    """
    col_names = [c for c in SEG_5Y_COLS if c in yields.columns]
    mats = np.array([float(c.replace("y_", "")) for c in col_names])

    if len(col_names) < 4:
        raise ValueError(f"5Y segment: only {len(col_names)} maturities available.")

    yields_seg = yields[col_names]
    log_p = -(yields_seg.values / 100.0) * mats[np.newaxis, :]
    dlp = np.diff(log_p, axis=0)
    dates = yields_seg.index[1:]

    print(f"  5Y segment maturities ({len(col_names)}): {col_names}")
    print(f"  Running 5Y 3-factor rolling PCA ({WINDOW}-day window) ...")

    vol_records = []
    for i in range(WINDOW - 1, len(dlp)):
        cov = np.cov(dlp[i - WINDOW + 1 : i + 1, :].T)
        vol = fit_three_factor_from_cov(cov, mats, kappa1_lo=0.01)
        if vol is None:
            continue
        vol["date"] = dates[i]
        vol_records.append(vol)

    if not vol_records:
        raise RuntimeError("3-factor PCA returned no results for 5Y segment.")

    vol_df = pd.DataFrame(vol_records).set_index("date")
    print(f"  Vol estimates: {len(vol_df)} dates")

    # Median parameters over the full sample
    sigma_star = np.array([
        vol_df["sigma1"].median(),
        vol_df["sigma2"].median(),
        vol_df["sigma3"].median(),
    ])
    kappa_star = np.array([
        vol_df["kappa1"].median(),
        vol_df["kappa2"].median(),
        vol_df["kappa3"].median(),
    ])

    print(f"  5Y DGP sigma*: {sigma_star}")
    print(f"  5Y DGP kappa*: {kappa_star}")

    # Cross-sectional regression with fixed params on the 5Y segment
    print("  Extracting lambda time series (5Y segment, fixed DGP params) ...")
    lambda_records = []
    for date in vol_df.index:
        if date not in yields.index:
            continue
        y_obs = yields.loc[date, col_names].values
        lam, r2 = extract_market_price_of_risk_3factor(y_obs, mats, sigma_star, kappa_star)
        if not np.any(np.isnan(lam)):
            lambda_records.append({
                "date": date,
                "lambda1": lam[0],
                "lambda2": lam[1],
                "lambda3": lam[2],
                "r_squared": r2,
            })

    if not lambda_records:
        raise RuntimeError("No lambda records extracted from 5Y segment.")

    lambda_df = pd.DataFrame(lambda_records).set_index("date")
    print(f"  Lambda records: {len(lambda_df)} dates  (median R²={lambda_df['r_squared'].median():.4f})")

    lambda_star = np.array([
        lambda_df["lambda1"].median(),
        lambda_df["lambda2"].median(),
        lambda_df["lambda3"].median(),
    ])
    lambda_std = np.array([
        lambda_df["lambda1"].std(),
        lambda_df["lambda2"].std(),
        lambda_df["lambda3"].std(),
    ])

    print(f"  5Y DGP lambda*: {lambda_star}")
    print(f"  5Y DGP lambda_std: {lambda_std}")

    dgp = {
        "source_segment": "5Y",
        "sigma_star": sigma_star.tolist(),
        "kappa_star": kappa_star.tolist(),
        "lambda_star": lambda_star.tolist(),
        "lambda_std": lambda_std.tolist(),
        "sigma_noise": SIGMA_NOISE,
        "seed": SEED,
    }

    return dgp, lambda_df


# ---------------------------------------------------------------------------
# Build the 4-column comparison table
# ---------------------------------------------------------------------------

def build_4col_comparison(
    emp_3f: pd.DataFrame,
    syn30y_summary: pd.DataFrame,
    syn5y_3f: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge emp_3f, syn30y_3f_mean (from existing synthetic_summary.csv),
    and syn5y_3f into a single table keyed by (T_short, T_long).

    Columns: T_short, T_long, emp_3f_mean, syn30y_3f_mean, syn5y_3f_mean
    """
    rows = []
    for _, r_e in emp_3f.iterrows():
        ts, tl = r_e["T_short"], r_e["T_long"]

        # Syn-30Y: from pre-existing synthetic_summary.csv
        r_s30 = syn30y_summary[
            (syn30y_summary["T_short"] == ts) & (syn30y_summary["T_long"] == tl)
        ]

        # Syn-5Y: from this run
        r_s5 = syn5y_3f[
            (syn5y_3f["T_short"] == ts) & (syn5y_3f["T_long"] == tl)
        ]

        rows.append({
            "T_short": ts,
            "T_long": tl,
            "emp_3f_mean": r_e["mean_dlambda1"],
            "emp_3f_t": r_e["t_stat_dlambda1"],
            "syn30y_3f_mean": r_s30.iloc[0]["syn_3f_mean"] if not r_s30.empty else np.nan,
            "syn30y_3f_t": r_s30.iloc[0]["syn_3f_t"] if not r_s30.empty else np.nan,
            "syn5y_3f_mean": r_s5.iloc[0]["mean_dlambda1"] if not r_s5.empty else np.nan,
            "syn5y_3f_t": r_s5.iloc[0]["t_stat_dlambda1"] if not r_s5.empty else np.nan,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------

def print_summary(comparison: pd.DataFrame, syn5y_3f_summary: pd.DataFrame) -> None:
    n_pairs = len(comparison)
    n_5y_reject = (syn5y_3f_summary["p_adj_dlambda1"] < 0.05).sum()

    print("\n" + "=" * 80)
    print("SYNTHETIC VALIDATION — 5Y DGP vs 30Y DGP")
    print("=" * 80)
    print(f"\nSyn-5Y 3F: {n_5y_reject}/{n_pairs} pairs reject H0 (Bonf. 5%)")

    max_5y = comparison["syn5y_3f_mean"].abs().max()
    max_30y = comparison["syn30y_3f_mean"].abs().max()
    max_emp = comparison["emp_3f_mean"].abs().max()

    print(f"\nMax |Δλ₁|  empirical 3F : {max_emp:.4f}")
    print(f"Max |Δλ₁|  Syn-30Y 3F   : {max_30y:.4f}")
    print(f"Max |Δλ₁|  Syn-5Y  3F   : {max_5y:.4f}")

    hdr = f"\n{'Pair':<12}  {'Emp 3F Δλ₁':>12}  {'Syn-30Y 3F Δλ₁':>16}  {'Syn-5Y 3F Δλ₁':>15}"
    print(hdr)
    print("-" * 65)
    for _, r in comparison.iterrows():
        pair = f"{int(r.T_short)}Y-{int(r.T_long)}Y"
        print(
            f"{pair:<12}  "
            f"{r.emp_3f_mean:>12.4f}  "
            f"{r.syn30y_3f_mean:>16.4f}  "
            f"{r.syn5y_3f_mean:>15.4f}"
        )

    print("\n--- Interpretation ---")

    # Key test: do syn-5Y 3F gaps remain near zero uniformly?
    ok_near_zero = n_5y_reject == 0
    print(
        f"[{'PASS' if ok_near_zero else 'FAIL'}] Syn-5Y 3F shows near-zero gaps uniformly "
        f"({n_5y_reject}/{n_pairs} pairs rejected at Bonf. 5%)"
    )

    # Does the 5Y DGP produce similar pattern to 30Y DGP?
    syn30y_vals = comparison["syn30y_3f_mean"].dropna().abs()
    syn5y_vals = comparison["syn5y_3f_mean"].dropna().abs()
    corr = syn30y_vals.corr(syn5y_vals)
    max_ratio = (syn5y_vals.max() / max_emp) if max_emp > 1e-6 else np.nan
    print(f"\n  Correlation(Syn-30Y, Syn-5Y) 3F mean gaps: {corr:.3f}")
    print(f"  Syn-5Y max gap / Emp max gap: {max_ratio:.3f}  (expect << 1 for near-zero)")

    if ok_near_zero:
        print("\nCONCLUSION: Syn-5Y validation PASSES.")
        print("The near-zero synthetic 3F result is robust to DGP choice (5Y vs 30Y).")
        print("Short-segment parameters are sufficient to identify a single-Q DGP.")
    else:
        print("\nCONCLUSION: Syn-5Y validation FAILS — non-zero gaps under 5Y DGP.")
        print("5Y segment parameters may under-identify the curvature factor (κ₃),")
        print("causing residual gaps even in the true single-Q world.")
        print("The 30Y DGP remains the preferred synthetic benchmark.")

    print("=" * 80)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(quick: bool = False) -> None:
    # --- Load empirical yields ---
    yields = pd.read_parquet(DATA_DIR / "ecb_yield_curves.parquet")
    yields.index = pd.to_datetime(yields.index)
    yields.columns = [
        f"y_{int(T)}" if T == int(T) else f"y_{T}"
        for T in [0.25, 0.5, 1, 2, 3, 5, 7, 10, 15, 20, 25, 30]
    ]
    print(f"Loaded {len(yields)} empirical observations.")

    # --- Extract 5Y DGP parameters ---
    dgp_path = DATA_DIR / "synthetic_5y_dgp_params.json"
    synth_path = DATA_DIR / "synthetic_5y_yields.csv"

    if synth_path.exists() and dgp_path.exists():
        print("\nLoading cached 5Y synthetic yields ...")
        synth = pd.read_csv(synth_path, index_col=0, parse_dates=True)
        with open(dgp_path) as f:
            dgp = json.load(f)
        print(f"  Loaded: {synth.shape}")
    else:
        print("\n[Step 1] Extracting DGP parameters from 5Y segment ...")
        dgp, _ = extract_5y_3factor_params(yields)

        print("\n=== 5Y DGP Parameters ===")
        for k in range(3):
            print(
                f"  Factor {k+1}: "
                f"σ*={dgp['sigma_star'][k]:.6f}  "
                f"κ*={dgp['kappa_star'][k]:.4f}  "
                f"λ*={dgp['lambda_star'][k]:.4f}  "
                f"λ_std={dgp['lambda_std'][k]:.4f}"
            )

        print("\n[Step 2] Generating synthetic yields from 5Y DGP ...")
        synth = build_synthetic_yields(yields, dgp, seed=SEED)
        print(f"  Shape: {synth.shape}")
        print(f"  Yield range: [{synth.values.min():.3f}, {synth.values.max():.3f}] %")

        synth.to_csv(synth_path)
        print(f"  Saved: {synth_path.name}")

        with open(dgp_path, "w") as f:
            json.dump(dgp, f, indent=2)
        print(f"  Saved: {dgp_path.name}")

    if quick:
        n_quick = 300
        print(f"\n[QUICK MODE] Using first {n_quick} dates.")
        synth = synth.iloc[:n_quick]

    print(f"\nSynthetic yields (5Y DGP): {synth.shape[0]} dates × {synth.shape[1]} maturities")

    # --- Run 2F and 3F pipelines on 5Y synthetic data ---
    print("\n[2-factor calibration on 5Y synthetic yields]")
    _, _, syn5y_summary_2f = run_2factor_pipeline(synth, label="syn5y ")
    syn5y_summary_2f.to_csv(DATA_DIR / "synthetic_5y_test1_results.csv", index=False)
    print("  Saved: data/synthetic_5y_test1_results.csv")

    print("\n[3-factor calibration on 5Y synthetic yields]")
    _, _, syn5y_summary_3f = run_3factor_pipeline(synth, label="syn5y ")
    syn5y_summary_3f.to_csv(DATA_DIR / "synthetic_5y_test3_results.csv", index=False)
    print("  Saved: data/synthetic_5y_test3_results.csv")

    # --- Load reference data ---
    emp_summary_3f = pd.read_csv(DATA_DIR / "test3_summary.csv")
    syn30y_summary = pd.read_csv(DATA_DIR / "synthetic_summary.csv")  # has syn_3f_mean column

    # --- Build 4-column comparison ---
    comparison = build_4col_comparison(emp_summary_3f, syn30y_summary, syn5y_summary_3f)
    comparison.to_csv(DATA_DIR / "synthetic_5y_summary.csv", index=False)
    print("\n  Saved: data/synthetic_5y_summary.csv")

    # --- Console summary ---
    print_summary(comparison, syn5y_summary_3f)

    print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true",
                        help="Run on first 300 dates only")
    args = parser.parse_args()
    main(quick=args.quick)
