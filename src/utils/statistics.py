"""
statistics.py — Statistical utilities for HAC inference and multiple testing.
"""

import numpy as np
import pandas as pd
from scipy import stats


def newey_west_ttest(series: pd.Series, max_lag: int = 10) -> dict:
    """
    Test H₀: E[series] = 0 using Newey-West HAC standard errors.

    Parameters
    ----------
    series : pd.Series (no NaNs expected; will be dropped internally)
    max_lag : int, bandwidth for Bartlett kernel

    Returns
    -------
    dict with keys: mean, std_nw, t_stat, p_value
    """
    x = series.dropna().values
    n = len(x)
    if n < 5:
        return {"mean": np.nan, "std_nw": np.nan, "t_stat": np.nan, "p_value": np.nan}

    mu = x.mean()
    u = x - mu  # demeaned

    # Newey-West variance estimator: V = gamma_0 + 2 * sum_{l=1}^{L} w_l * gamma_l
    gamma_0 = np.dot(u, u) / n
    nw_var = gamma_0
    for lag in range(1, max_lag + 1):
        w = 1.0 - lag / (max_lag + 1)  # Bartlett weight
        gamma_l = np.dot(u[lag:], u[:-lag]) / n
        nw_var += 2.0 * w * gamma_l

    # Variance of the sample mean
    var_mean = nw_var / n
    std_nw = np.sqrt(max(var_mean, 0.0))

    t_stat = mu / std_nw if std_nw > 1e-12 else np.nan
    p_value = 2.0 * stats.t.sf(np.abs(t_stat), df=n - 1) if not np.isnan(t_stat) else np.nan

    return {
        "mean": float(mu),
        "std_nw": float(std_nw),
        "t_stat": float(t_stat),
        "p_value": float(p_value),
    }


def bonferroni_correction(p_values: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """
    Bonferroni-adjusted p-values: p_adj = min(n * p, 1).

    Parameters
    ----------
    p_values : array of raw p-values
    alpha : significance level (unused in output, but conventional to pass)

    Returns
    -------
    adjusted p-values (same shape as input)
    """
    n = len(p_values)
    return np.minimum(n * p_values, 1.0)
