"""
gaussian_hjm.py — Two-factor Gaussian HJM: convexity adjustment and
market price of risk extraction via cross-sectional OLS.

Model:
  y^obs(t, T) = alpha(t) + lambda1(t)*g1(T) + lambda2(t)*g2(T) + eps

where g_k(T) = (sigma_k / kappa_k) * (1 - exp(-kappa_k * T))
and alpha absorbs the level / forward curve.
"""

import numpy as np


# ---------------------------------------------------------------------------
# Basis functions
# ---------------------------------------------------------------------------

ANNUALIZE = np.sqrt(252.0)   # daily → annual volatility
PCT = 100.0                   # decimal → % p.a. (to match yield units)
VOL_SCALE = ANNUALIZE * PCT   # combined scale factor: daily decimal → annual %


def risk_premium_basis(
    tau: np.ndarray,
    sigma: np.ndarray,
    kappa: np.ndarray,
) -> np.ndarray:
    """
    Compute the two basis functions:
      g_k(T) = (sigma_k_annual_pct / kappa_k) * (1 - exp(-kappa_k*T))

    sigma from PCA is in daily decimal units; multiply by VOL_SCALE to
    convert to annual % units matching the observed yield cross-section.

    Parameters
    ----------
    tau : (n_mat,) maturities in years
    sigma : [sigma1, sigma2]  (daily decimal units from PCA)
    kappa : [kappa1, kappa2]

    Returns
    -------
    X : (n_mat, 2) design matrix, columns are g1(tau), g2(tau)  [in % p.a. units]
    """
    sigma_ann_pct = np.array(sigma) * VOL_SCALE
    X = np.column_stack([
        (sigma_ann_pct[k] / kappa[k]) * (1.0 - np.exp(-kappa[k] * tau))
        for k in range(2)
    ])
    return X


# ---------------------------------------------------------------------------
# Convexity adjustment (Jensen's inequality term)
# ---------------------------------------------------------------------------

def convexity_adjustment(
    tau: np.ndarray,
    sigma: np.ndarray,
    kappa: np.ndarray,
) -> np.ndarray:
    """
    Gaussian HJM convexity adjustment (subtracted from observed yield to
    isolate the lambda-linear part).

    adj(T) = -1/2 * sum_k [ (sigma_k/kappa_k)^2 *
              (T - 2/kappa_k*(1-exp(-kappa_k*T)) + 1/(2*kappa_k)*(1-exp(-2*kappa_k*T))) ]

    The sign convention: risk_premium = lambda_term - convexity_adjustment,
    so convexity_adjustment > 0 lowers the yield.

    Parameters
    ----------
    tau : (n_mat,) maturities in years
    sigma : [sigma1, sigma2]
    kappa : [kappa1, kappa2]

    Returns
    -------
    adj : (n_mat,) convexity adjustment in decimal (not %)
    """
    adj = np.zeros(len(tau))
    for k in range(2):
        sk, kk = sigma[k], kappa[k]
        a = (sk / kk) ** 2
        adj += 0.5 * a * (
            tau
            - (2.0 / kk) * (1.0 - np.exp(-kk * tau))
            + (1.0 / (2.0 * kk)) * (1.0 - np.exp(-2.0 * kk * tau))
        )
    return adj


# ---------------------------------------------------------------------------
# Cross-sectional OLS: extract lambda
# ---------------------------------------------------------------------------

def extract_market_price_of_risk(
    yields_obs: np.ndarray,
    maturities: np.ndarray,
    sigma: np.ndarray,
    kappa: np.ndarray,
    forward_yields: np.ndarray | None = None,
) -> tuple[np.ndarray, float]:
    """
    Extract (lambda1, lambda2) by cross-sectional OLS.

    Fits:  y^obs(T) = alpha + lambda1*g1(T) + lambda2*g2(T) + eps

    where g_k(T) = (sigma_k/kappa_k)*(1-exp(-kappa_k*T)).

    The alpha intercept absorbs the level. The lambdas capture the
    slope/curvature of the risk premium across maturities.

    Parameters
    ----------
    yields_obs : (n_mat,) observed yields in % p.a.
    maturities : (n_mat,) in years
    sigma : [sigma1, sigma2]
    kappa : [kappa1, kappa2]
    forward_yields : ignored (absorbed into alpha); kept for interface compatibility

    Returns
    -------
    lambdas : (2,) [lambda1, lambda2]
    r_squared : float
    """
    tau = maturities
    g = risk_premium_basis(tau, sigma, kappa)  # (n_mat, 2)

    # Design matrix with intercept
    X = np.column_stack([np.ones(len(tau)), g])  # (n_mat, 3)
    y = yields_obs  # (n_mat,)

    # Ridge regression: beta = (X'X + alpha*I)^{-1} X'y
    # Small alpha stabilises near-collinear basis functions (e.g. when sigma2 ~ 0)
    alpha_ridge = 1e-6 * np.trace(X.T @ X) / X.shape[1]
    try:
        A = X.T @ X + alpha_ridge * np.eye(X.shape[1])
        b = X.T @ y
        beta = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return np.array([np.nan, np.nan]), np.nan

    lambdas = beta[1:]  # drop intercept
    y_hat = X @ beta
    ss_res = np.sum((y - y_hat) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else np.nan

    return lambdas, float(r2)


# ---------------------------------------------------------------------------
# Three-factor basis and extraction
# ---------------------------------------------------------------------------

def risk_premium_basis_3factor(
    tau: np.ndarray,
    sigma: np.ndarray,
    kappa: np.ndarray,
) -> np.ndarray:
    """
    Three-factor basis matrix for cross-sectional regression.

    Factors:
      g1(T) = (sigma1_ann_pct / kappa1) * (1 - exp(-kappa1*T))
      g2(T) = (sigma2_ann_pct / kappa2) * (1 - exp(-kappa2*T))
      g3(T) = (sigma3_ann_pct / kappa3^2) * (1 - (1+kappa3*T)*exp(-kappa3*T))

    sigma from PCA is in daily decimal units; VOL_SCALE converts to annual %.

    Parameters
    ----------
    tau : (n_mat,) maturities in years
    sigma : [sigma1, sigma2, sigma3]  (daily decimal units)
    kappa : [kappa1, kappa2, kappa3]

    Returns
    -------
    X : (n_mat, 3) design matrix [in % p.a. units]
    """
    s = np.array(sigma) * VOL_SCALE
    k = np.array(kappa)
    cols = [
        (s[0] / k[0]) * (1.0 - np.exp(-k[0] * tau)),
        (s[1] / k[1]) * (1.0 - np.exp(-k[1] * tau)),
        (s[2] / k[2] ** 2) * (1.0 - (1.0 + k[2] * tau) * np.exp(-k[2] * tau)),
    ]
    return np.column_stack(cols)


def extract_market_price_of_risk_3factor(
    yields_obs: np.ndarray,
    maturities: np.ndarray,
    sigma: np.ndarray,
    kappa: np.ndarray,
) -> tuple[np.ndarray, float]:
    """
    Extract (lambda1, lambda2, lambda3) by cross-sectional ridge regression.

    Fits: y^obs(T) = alpha + lambda1*g1(T) + lambda2*g2(T) + lambda3*g3(T) + eps

    Returns
    -------
    lambdas : (3,) [lambda1, lambda2, lambda3]
    r_squared : float
    """
    g = risk_premium_basis_3factor(maturities, sigma, kappa)  # (n_mat, 3)
    X = np.column_stack([np.ones(len(maturities)), g])         # (n_mat, 4)
    y = yields_obs

    alpha_ridge = 1e-6 * np.trace(X.T @ X) / X.shape[1]
    try:
        A = X.T @ X + alpha_ridge * np.eye(X.shape[1])
        beta = np.linalg.solve(A, X.T @ y)
    except np.linalg.LinAlgError:
        return np.full(3, np.nan), np.nan

    lambdas = beta[1:]
    y_hat = X @ beta
    ss_res = np.sum((y - y_hat) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else np.nan

    return lambdas, float(r2)


# ---------------------------------------------------------------------------
# Batch extraction: apply to every date
# ---------------------------------------------------------------------------

def extract_lambdas_timeseries(
    yields: np.ndarray,
    dates: np.ndarray,
    maturities: np.ndarray,
    vol_params: "pd.DataFrame",
) -> "pd.DataFrame":
    """
    For each date in vol_params.index, extract lambda1, lambda2 using
    the sigma/kappa estimated on that date.

    Parameters
    ----------
    yields : (n_dates, n_mat) array of observed yields (% p.a.)
    dates : (n_dates,) DatetimeIndex aligned with yields rows
    maturities : (n_mat,) in years
    vol_params : DataFrame indexed by date with sigma1, kappa1, sigma2, kappa2

    Returns
    -------
    DataFrame with columns: lambda1, lambda2, r_squared, indexed by date
    """
    import pandas as pd

    yields_df = pd.DataFrame(yields, index=dates)
    records = []

    for date, row in vol_params.iterrows():
        if date not in yields_df.index:
            continue
        y_obs = yields_df.loc[date].values
        sigma = np.array([row["sigma1"], row["sigma2"]])
        kappa = np.array([row["kappa1"], row["kappa2"]])

        lam, r2 = extract_market_price_of_risk(y_obs, maturities, sigma, kappa)
        records.append({
            "date": date,
            "lambda1": lam[0],
            "lambda2": lam[1],
            "r_squared": r2,
        })

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records).set_index("date")
