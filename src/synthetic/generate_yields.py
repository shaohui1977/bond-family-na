"""
generate_yields.py — Synthetic yield generator for single-Q validation.

Generates a yield panel from a known 3-factor Gaussian HJM DGP where
a single risk-neutral measure Q exists by construction.

DGP:
    y(t, τ) = ȳ(τ) + Σₖ xₖ(t) · gₖ*(τ) + ε(t, τ)

where:
  ȳ(τ)      = empirical mean yield (constant baseline)
  gₖ*(τ)    = 3-factor HJM basis evaluated at DGP params σₖ*, κₖ*
  xₖ(t)     = OU factor, long-run mean = λₖ* (from 30Y 3-factor calibration)
  ε(t, τ)   ~ N(0, σ_noise²), iid

Because gₖ*(τ) does not depend on the maturity segment used for calibration,
any correctly-specified 3-factor regression recovers the same xₖ(t) regardless
of which segment is used → single Q holds by construction.

Run as script to generate data/synthetic_yields.csv and
data/synthetic_dgp_params.json.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.pca import fit_three_factor_from_cov
from src.models.gaussian_hjm import (
    risk_premium_basis_3factor,
    extract_market_price_of_risk_3factor,
)
from src.tests.test1_lambda_gap import WINDOW, ALL_MATURITIES

DATA_DIR = PROJECT_ROOT / "data"

COL_NAMES_ALL = [
    f"y_{int(T)}" if T == int(T) else f"y_{T}"
    for T in ALL_MATURITIES
]

SEED = 42
SIGMA_NOISE = 0.005  # 0.5 bp in % p.a. units


# ---------------------------------------------------------------------------
# Step 1: Extract DGP parameters from 30Y 3-factor calibration
# ---------------------------------------------------------------------------

def extract_30y_3factor_params(yields: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """
    Run rolling 3-factor PCA + cross-sectional regression on the full 30Y segment.

    Returns
    -------
    dgp : dict with sigma_star, kappa_star, lambda_star, lambda_std (lists of 3)
    lambda_df : per-date lambda time series (for diagnostics)
    """
    col_names = [c for c in COL_NAMES_ALL if c in yields.columns]
    mats = np.array([float(c.replace("y_", "")) for c in col_names])

    yields_seg = yields[col_names]
    log_p = -(yields_seg.values / 100.0) * mats[np.newaxis, :]
    dlp = np.diff(log_p, axis=0)
    dates = yields_seg.index[1:]

    print("  Running 30Y 3-factor rolling PCA ...")
    vol_records = []
    for i in range(WINDOW - 1, len(dlp)):
        cov = np.cov(dlp[i - WINDOW + 1 : i + 1, :].T)
        vol = fit_three_factor_from_cov(cov, mats, kappa1_lo=0.01)
        if vol is None:
            continue
        vol["date"] = dates[i]
        vol_records.append(vol)

    if not vol_records:
        raise RuntimeError("3-factor PCA returned no results for 30Y segment.")

    vol_df = pd.DataFrame(vol_records).set_index("date")
    print(f"  Vol estimates: {len(vol_df)} dates")

    # Median vol parameters (DGP parameters)
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

    # Cross-sectional regression with fixed median params to get lambda time series
    print("  Extracting lambda time series with fixed DGP params ...")
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

    lambda_df = pd.DataFrame(lambda_records).set_index("date")

    # DGP: long-run mean and stationary std for each OU factor
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

    dgp = {
        "sigma_star": sigma_star.tolist(),
        "kappa_star": kappa_star.tolist(),
        "lambda_star": lambda_star.tolist(),
        "lambda_std": lambda_std.tolist(),
        "sigma_noise": SIGMA_NOISE,
        "seed": SEED,
    }

    return dgp, lambda_df


# ---------------------------------------------------------------------------
# Step 2: OU factor path generator
# ---------------------------------------------------------------------------

def generate_ou_factors(
    n_dates: int,
    lambda_star: np.ndarray,
    lambda_std: np.ndarray,
    kappa_star: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Generate 3 OU factor paths with shape (n_dates, 3).

    Each factor: x_k(t+Δ) = ρ_k x_k(t) + (1−ρ_k) λₖ* + N(0, σ_innov_k²)

    where ρ_k = exp(-κₖ* Δ) and σ_innov_k = λ_std_k * sqrt(1 - ρ_k²).
    This gives E[x_k] = λₖ* and Var[x_k] = λ_std_k² in stationarity.

    Parameters
    ----------
    n_dates : number of time steps
    lambda_star : (3,) long-run mean for each factor
    lambda_std : (3,) stationary std for each factor
    kappa_star : (3,) mean-reversion speeds (annual)
    rng : numpy random generator
    """
    delta = 1.0 / 252.0
    n_factors = len(lambda_star)
    X = np.empty((n_dates, n_factors))
    X[0] = lambda_star  # start at long-run mean

    rho = np.exp(-kappa_star * delta)  # (3,)
    innov_std = lambda_std * np.sqrt(1.0 - rho ** 2)  # (3,)

    for t in range(1, n_dates):
        innovations = rng.standard_normal(n_factors) * innov_std
        X[t] = rho * X[t - 1] + (1.0 - rho) * lambda_star + innovations

    return X


# ---------------------------------------------------------------------------
# Step 3: Synthetic yield construction
# ---------------------------------------------------------------------------

def build_synthetic_yields(
    yields_empirical: pd.DataFrame,
    dgp: dict,
    seed: int = SEED,
) -> pd.DataFrame:
    """
    Construct synthetic yield panel:

        y(t, τ) = ȳ(τ) + Σₖ xₖ(t) · gₖ*(τ) + ε(t, τ)

    Parameters
    ----------
    yields_empirical : empirical yields, shape (n_dates, n_mats)
    dgp : dict from extract_30y_3factor_params

    Returns
    -------
    DataFrame with same index and columns as yields_empirical
    """
    col_names = [c for c in COL_NAMES_ALL if c in yields_empirical.columns]
    mats = np.array([float(c.replace("y_", "")) for c in col_names])
    n_dates = len(yields_empirical)
    n_mats = len(col_names)

    sigma_star = np.array(dgp["sigma_star"])
    kappa_star = np.array(dgp["kappa_star"])
    lambda_star = np.array(dgp["lambda_star"])
    lambda_std = np.array(dgp["lambda_std"])
    sigma_noise = dgp["sigma_noise"]

    # Empirical mean yield: (n_mats,)
    y_bar = yields_empirical[col_names].mean(axis=0).values

    # DGP basis matrix: (n_mats, 3)
    G = risk_premium_basis_3factor(mats, sigma_star, kappa_star)

    rng = np.random.default_rng(seed)

    # OU factors: (n_dates, 3)
    X = generate_ou_factors(n_dates, lambda_star, lambda_std, kappa_star, rng)

    # Noise: (n_dates, n_mats)
    noise = rng.standard_normal((n_dates, n_mats)) * sigma_noise

    # y(t, τ) = ȳ(τ) + Σₖ xₖ(t) gₖ(τ) + ε
    Y = y_bar[np.newaxis, :] + (X @ G.T) + noise  # (n_dates, n_mats)

    return pd.DataFrame(Y, index=yields_empirical.index, columns=col_names)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> dict:
    yields = pd.read_parquet(DATA_DIR / "ecb_yield_curves.parquet")
    yields.index = pd.to_datetime(yields.index)
    yields.columns = [
        f"y_{int(T)}" if T == int(T) else f"y_{T}"
        for T in [0.25, 0.5, 1, 2, 3, 5, 7, 10, 15, 20, 25, 30]
    ]
    print(f"Loaded {len(yields)} empirical observations.")

    # --- Extract DGP parameters ---
    print("\n[Step 1] Extracting DGP parameters from 30Y 3-factor calibration ...")
    dgp, lambda_df = extract_30y_3factor_params(yields)

    print("\n=== DGP Parameters ===")
    for k in range(3):
        print(
            f"  Factor {k+1}: "
            f"σ*={dgp['sigma_star'][k]:.6f} (daily dec)  "
            f"κ*={dgp['kappa_star'][k]:.4f} (annual)  "
            f"λ*={dgp['lambda_star'][k]:.4f}  "
            f"λ_std={dgp['lambda_std'][k]:.4f}"
        )

    # --- Generate synthetic yields ---
    print("\n[Step 2] Generating synthetic yields ...")
    synth = build_synthetic_yields(yields, dgp, seed=SEED)

    print(f"  Shape: {synth.shape}")
    print(f"  Yield range (synthetic):  [{synth.values.min():.3f}, {synth.values.max():.3f}] %")
    print(f"  Yield range (empirical):  [{yields.values.min():.3f}, {yields.values.max():.3f}] %")
    print(f"  Mean yield (synthetic):   {synth.values.mean():.3f} %")
    print(f"  Mean yield (empirical):   {yields.values.mean():.3f} %")

    # --- Save ---
    synth.to_csv(DATA_DIR / "synthetic_yields.csv")
    print(f"\nSaved: data/synthetic_yields.csv")

    with open(DATA_DIR / "synthetic_dgp_params.json", "w") as f:
        json.dump(dgp, f, indent=2)
    print("Saved: data/synthetic_dgp_params.json")

    return dgp


if __name__ == "__main__":
    main()
