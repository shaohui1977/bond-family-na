"""
pca.py — PCA on bond log-returns and exponential volatility fitting.

Fits two-factor Gaussian HJM volatility structure:
  v_k(T) = (sigma_k / kappa_k) * (1 - exp(-kappa_k * T))   [bond volatility]

from eigenvectors of the bond log-return covariance matrix.
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Bond volatility basis function
# ---------------------------------------------------------------------------

def bond_vol_func(T: np.ndarray, a: float, kappa: float) -> np.ndarray:
    """v(T) = a * (1 - exp(-kappa * T)), where a = sigma/kappa."""
    return a * (1.0 - np.exp(-kappa * T))


def curvature_vol_func(T: np.ndarray, b: float, kappa: float) -> np.ndarray:
    """
    Bond volatility for the curvature (hump-shaped) factor.

    Forward-rate vol: sigma3(tau) = sigma3 * tau * exp(-kappa3 * tau)
    Bond vol (integral): v3(T) = b * (1 - (1 + kappa*T)*exp(-kappa*T))
    where b = sigma3 / kappa^2.
    """
    return b * (1.0 - (1.0 + kappa * T) * np.exp(-kappa * T))


# ---------------------------------------------------------------------------
# Core PCA + fit for a single covariance matrix
# ---------------------------------------------------------------------------

def fit_two_factor_from_cov(
    cov: np.ndarray,
    maturities: np.ndarray,
    kappa1_lo: float = 0.01,
) -> dict | None:
    """
    Given a covariance matrix of bond log-returns (shape n_mat × n_mat),
    extract two-factor Gaussian HJM parameters.

    Returns dict with sigma1, kappa1, sigma2, kappa2, explained_var_ratio,
    or None if fitting fails.
    """
    n = len(maturities)
    if n < 4:
        return None

    # Eigendecomposition — descending order
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]

    # Clip negative eigenvalues (numerical noise)
    eigvals = np.maximum(eigvals, 0.0)
    total_var = eigvals.sum()
    if total_var <= 0:
        return None

    explained = eigvals[:2].sum() / total_var

    params = []
    for k in range(2):
        vec = eigvecs[:, k]
        # Scale: eigenvector norm * sqrt(eigenvalue) gives the actual volatility loading
        # v_k(T) ∝ eigvec_k(T), scaled so that cov ≈ v1·v1' + v2·v2'
        # The loading magnitude is sqrt(eigenvalue)
        loading = vec * np.sqrt(eigvals[k])

        # Ensure positive orientation (largest element positive)
        if loading[np.argmax(np.abs(loading))] < 0:
            loading = -loading

        # Fit v_k(T) = a * (1 - exp(-kappa * T))
        # Slow factor: kappa in [kappa1_lo, 0.8], fast factor: kappa in [0.3, 5.0]
        if k == 0:
            kappa_init, kappa_lo, kappa_hi = max(0.15, kappa1_lo), kappa1_lo, 0.8
        else:
            kappa_init, kappa_lo, kappa_hi = 0.8, 0.1, 5.0
        a_init = max(loading.max(), 1e-6)

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                popt, _ = curve_fit(
                    bond_vol_func,
                    maturities,
                    loading,
                    p0=[a_init, kappa_init],
                    bounds=([1e-8, kappa_lo], [np.inf, kappa_hi]),
                    maxfev=2000,
                )
            a_k, kappa_k = popt
            sigma_k = a_k * kappa_k  # recover sigma from a = sigma/kappa
            params.append((sigma_k, kappa_k))
        except (RuntimeError, ValueError):
            return None

    if len(params) < 2:
        return None

    return {
        "sigma1": params[0][0],
        "kappa1": params[0][1],
        "sigma2": params[1][0],
        "kappa2": params[1][1],
        "explained_var_ratio": float(explained),
    }


# ---------------------------------------------------------------------------
# Three-factor PCA + fit
# ---------------------------------------------------------------------------

def fit_three_factor_from_cov(
    cov: np.ndarray,
    maturities: np.ndarray,
    kappa1_lo: float = 0.01,
) -> dict | None:
    """
    Fit three-factor Gaussian HJM from a bond log-return covariance matrix.

    Factors:
      1. Level:     v1(T) = a1 * (1 - exp(-kappa1*T))          [standard]
      2. Slope:     v2(T) = a2 * (1 - exp(-kappa2*T))          [standard]
      3. Curvature: v3(T) = b3 * (1 - (1+kappa3*T)*exp(-kappa3*T))  [hump]

    Returns dict with sigma1..3, kappa1..3, explained_var_ratio, or None.
    """
    n = len(maturities)
    if n < 5:
        return None

    eigvals, eigvecs = np.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    eigvals = np.maximum(eigvals[order], 0.0)
    eigvecs = eigvecs[:, order]

    total_var = eigvals.sum()
    if total_var <= 0:
        return None

    explained = eigvals[:3].sum() / total_var

    params = []
    for k in range(3):
        loading = eigvecs[:, k] * np.sqrt(eigvals[k])
        if loading[np.argmax(np.abs(loading))] < 0:
            loading = -loading

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                if k == 0:
                    # Level: same as two-factor
                    popt, _ = curve_fit(
                        bond_vol_func, maturities, loading,
                        p0=[max(loading.max(), 1e-6), max(0.15, kappa1_lo)],
                        bounds=([1e-8, kappa1_lo], [np.inf, 0.8]),
                        maxfev=2000,
                    )
                    a, kappa = popt
                    params.append({"sigma": a * kappa, "kappa": kappa})

                elif k == 1:
                    # Slope: same as two-factor fast factor
                    popt, _ = curve_fit(
                        bond_vol_func, maturities, loading,
                        p0=[max(loading.max(), 1e-6), 0.8],
                        bounds=([1e-8, 0.1], [np.inf, 5.0]),
                        maxfev=2000,
                    )
                    a, kappa = popt
                    params.append({"sigma": a * kappa, "kappa": kappa})

                else:
                    # Curvature: hump-shaped, kappa3 in [0.05, 2.0]
                    b_init = max(abs(loading).max(), 1e-6)
                    popt, _ = curve_fit(
                        curvature_vol_func, maturities, loading,
                        p0=[b_init, 0.5],
                        bounds=([0.0, 0.05], [np.inf, 2.0]),
                        maxfev=2000,
                    )
                    b, kappa = popt
                    # sigma3 = b * kappa^2
                    params.append({"sigma": b * kappa ** 2, "kappa": kappa})

        except (RuntimeError, ValueError):
            return None

    if len(params) < 3:
        return None

    return {
        "sigma1": params[0]["sigma"],
        "kappa1": params[0]["kappa"],
        "sigma2": params[1]["sigma"],
        "kappa2": params[1]["kappa"],
        "sigma3": params[2]["sigma"],
        "kappa3": params[2]["kappa"],
        "explained_var_ratio": float(explained),
    }


# ---------------------------------------------------------------------------
# Rolling estimation
# ---------------------------------------------------------------------------

def estimate_volatility_structure(
    yields: pd.DataFrame,
    maturities: np.ndarray,
    n_factors: int = 2,
    window: int = 60,
) -> pd.DataFrame:
    """
    Rolling-window estimation of two-factor Gaussian HJM volatility structure
    from bond log-return covariances.

    Parameters
    ----------
    yields : pd.DataFrame
        Daily zero-coupon yields (% p.a.), rows = dates, columns = maturities.
    maturities : np.ndarray
        Maturities in years matching column order of yields.
    n_factors : int
        Number of PCA factors (currently only 2 supported).
    window : int
        Rolling window in trading days.

    Returns
    -------
    pd.DataFrame
        Columns: date, sigma1, kappa1, sigma2, kappa2, explained_var_ratio.
        Dates without enough data are dropped.
    """
    # Bond log-returns: Δ log p(t,T) = -(y(t,T)·T - y(t-1,T)·T) / 100
    log_p = -(yields.values / 100.0) * maturities[np.newaxis, :]  # log bond prices
    dlp = np.diff(log_p, axis=0)  # shape (T-1, n_mat)
    dates = yields.index[1:]  # aligned with dlp rows

    records = []
    for i in range(window - 1, len(dlp)):
        window_data = dlp[i - window + 1 : i + 1, :]  # (window, n_mat)
        cov = np.cov(window_data.T)  # (n_mat, n_mat)

        result = fit_two_factor_from_cov(cov, maturities)
        if result is not None:
            result["date"] = dates[i]
            records.append(result)

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records).set_index("date")
    return df


# ---------------------------------------------------------------------------
# Segment-restricted estimation
# ---------------------------------------------------------------------------

def estimate_for_segment(
    yields: pd.DataFrame,
    all_maturities: np.ndarray,
    max_maturity: float,
    window: int = 60,
) -> pd.DataFrame:
    """
    Estimate volatility structure using only maturities ≤ max_maturity.

    Returns DataFrame indexed by date with sigma1, kappa1, sigma2, kappa2,
    explained_var_ratio columns.
    """
    mask = all_maturities <= max_maturity + 1e-9
    seg_mats = all_maturities[mask]
    col_names = [f"y_{T}" for T in seg_mats]
    # Filter to columns that exist
    col_names = [c for c in col_names if c in yields.columns]

    if len(col_names) < 4:
        raise ValueError(
            f"Segment ≤{max_maturity}Y has only {len(col_names)} maturities — need ≥ 4."
        )

    yields_seg = yields[col_names]
    mats_seg = np.array([float(c.replace("y_", "")) for c in col_names])

    return estimate_volatility_structure(yields_seg, mats_seg, window=window)
