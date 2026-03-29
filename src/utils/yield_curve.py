"""
yield_curve.py — Core yield curve financial calculations.

Conventions:
  - Yields are in % per annum (as stored in ECB data), but bond price /
    forward rate formulas require decimal form → divide by 100 internally.
  - Maturities are in years (float array).
  - Bond prices: p(t,T) = exp(-y(t,T) * T)   [continuous compounding]
  - Forward rates: f(t,T1,T2) = [y(t,T2)*T2 - y(t,T1)*T1] / (T2 - T1)
"""

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

# Standard maturities (years) matching ECB data column order
STANDARD_MATURITIES = np.array([0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 25.0, 30.0])


# ---------------------------------------------------------------------------
# Bond prices
# ---------------------------------------------------------------------------


def yields_to_bond_prices(yields: pd.DataFrame, maturities: np.ndarray) -> pd.DataFrame:
    """
    Convert zero-coupon yields to bond prices.

    p(t,T) = exp(-y(t,T) * T)

    Parameters
    ----------
    yields : pd.DataFrame
        Rows = dates, columns = maturities. Yields in % p.a.
    maturities : np.ndarray
        Array of maturities in years, matching column order.

    Returns
    -------
    pd.DataFrame
        Bond prices in [0,1], same shape and index as yields.
        Columns renamed from y_{T} to p_{T}.
    """
    y_dec = yields.values / 100.0  # % → decimal
    prices = np.exp(-y_dec * maturities[np.newaxis, :])
    col_names = [f"p_{T}" for T in maturities]
    return pd.DataFrame(prices, index=yields.index, columns=col_names)


# ---------------------------------------------------------------------------
# Forward rates
# ---------------------------------------------------------------------------


def yields_to_forward_rates(yields: pd.DataFrame, maturities: np.ndarray) -> pd.DataFrame:
    """
    Compute forward rates between consecutive maturities.

    f(t, T_{i}, T_{i+1}) = [y(t,T_{i+1})*T_{i+1} - y(t,T_i)*T_i] / (T_{i+1} - T_i)

    Parameters
    ----------
    yields : pd.DataFrame
        Rows = dates, columns = maturities. Yields in % p.a.
    maturities : np.ndarray
        Array of maturities in years, matching column order.

    Returns
    -------
    pd.DataFrame
        Forward rates in % p.a. (N-1 columns for N maturities).
        Columns named f_{T1}_{T2}.
    """
    y_dec = yields.values / 100.0

    n_mat = len(maturities)
    fwd_values = np.empty((len(yields), n_mat - 1))
    col_names = []

    for i in range(n_mat - 1):
        T1, T2 = maturities[i], maturities[i + 1]
        fwd_values[:, i] = (y_dec[:, i + 1] * T2 - y_dec[:, i] * T1) / (T2 - T1)
        col_names.append(f"f_{T1}_{T2}")

    # Convert back to % p.a.
    return pd.DataFrame(fwd_values * 100.0, index=yields.index, columns=col_names)


# ---------------------------------------------------------------------------
# Forward rate changes
# ---------------------------------------------------------------------------


def daily_forward_rate_changes(forward_rates: pd.DataFrame) -> pd.DataFrame:
    """
    First differences of forward rates.

    Δf(t, T1, T2) = f(t, T1, T2) - f(t-1, T1, T2)

    Used for covariance estimation and PCA on forward rate dynamics.

    Parameters
    ----------
    forward_rates : pd.DataFrame
        Output of yields_to_forward_rates().

    Returns
    -------
    pd.DataFrame
        Daily changes in % p.a. Same columns, one fewer row.
    """
    return forward_rates.diff().dropna()


# ---------------------------------------------------------------------------
# Convenience loader
# ---------------------------------------------------------------------------


def load_yields(path: Path | None = None) -> pd.DataFrame:
    """Load ECB yield curve data from parquet file."""
    if path is None:
        path = DATA_DIR / "ecb_yield_curves.parquet"
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    return df
