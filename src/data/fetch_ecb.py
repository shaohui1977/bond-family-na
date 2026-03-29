"""
fetch_ecb.py — Download ECB AAA-rated EUR government bond yield curves.

Fetches daily zero-coupon yields for maturities:
  3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 15Y, 20Y, 25Y, 30Y

Period: 2014-01-01 to 2024-12-31
Source: ECB Statistical Data Warehouse (SDW) REST API

Usage:
    python src/data/fetch_ecb.py
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

START_DATE = "2014-01-01"
END_DATE = "2024-12-31"

# Maturity label → ECB series key suffix (years as float)
# ECB uses SR_3M, SR_6M for sub-year, and SR_1Y, SR_2Y, ... for annual maturities
MATURITIES: dict[str, float] = {
    "SR_3M": 0.25,
    "SR_6M": 0.5,
    "SR_1Y": 1.0,
    "SR_2Y": 2.0,
    "SR_3Y": 3.0,
    "SR_5Y": 5.0,
    "SR_7Y": 7.0,
    "SR_10Y": 10.0,
    "SR_15Y": 15.0,
    "SR_20Y": 20.0,
    "SR_25Y": 25.0,
    "SR_30Y": 30.0,
}

# Column names in the output DataFrame
COL_NAMES = {
    "SR_3M": "y_0.25",
    "SR_6M": "y_0.5",
    "SR_1Y": "y_1",
    "SR_2Y": "y_2",
    "SR_3Y": "y_3",
    "SR_5Y": "y_5",
    "SR_7Y": "y_7",
    "SR_10Y": "y_10",
    "SR_15Y": "y_15",
    "SR_20Y": "y_20",
    "SR_25Y": "y_25",
    "SR_30Y": "y_30",
}

ECB_API_BASE = "https://data-api.ecb.europa.eu/service/data/YC"
SERIES_PREFIX = "B.U2.EUR.4F.G_N_A.SV_C_YM"


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------


def _build_url(maturity_key: str) -> str:
    series_key = f"{SERIES_PREFIX}.{maturity_key}"
    return (
        f"{ECB_API_BASE}/{series_key}"
        f"?format=csvdata"
        f"&startPeriod={START_DATE}"
        f"&endPeriod={END_DATE}"
    )


def _fetch_single_maturity(maturity_key: str) -> pd.Series | None:
    """Download one maturity series from ECB SDW. Returns a date-indexed Series."""
    url = _build_url(maturity_key)
    print(f"  Fetching {maturity_key} ... URL: {url}")
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"  ERROR fetching {maturity_key}: {exc}")
        print(f"  URL tried: {url}")
        return None

    # ECB csvdata format: header rows, then data rows with TIME_PERIOD,OBS_VALUE,...
    from io import StringIO

    try:
        df = pd.read_csv(StringIO(resp.text))
    except Exception as exc:
        print(f"  ERROR parsing CSV for {maturity_key}: {exc}")
        print(f"  First 500 chars of response:\n{resp.text[:500]}")
        return None

    # Locate the date and value columns (case-insensitive)
    col_lower = {c.lower(): c for c in df.columns}
    date_col = col_lower.get("time_period") or col_lower.get("date")
    val_col = col_lower.get("obs_value") or col_lower.get("value")

    if date_col is None or val_col is None:
        print(f"  ERROR: could not find TIME_PERIOD/OBS_VALUE in columns: {df.columns.tolist()}")
        return None

    series = df[[date_col, val_col]].copy()
    series[date_col] = pd.to_datetime(series[date_col], errors="coerce")
    series[val_col] = pd.to_numeric(series[val_col], errors="coerce")
    series = series.dropna(subset=[date_col]).set_index(date_col)[val_col]
    series.index.name = "date"
    return series


# ---------------------------------------------------------------------------
# Main download function
# ---------------------------------------------------------------------------


def download_ecb_yields() -> pd.DataFrame:
    """
    Download all 12 maturity series from ECB SDW.
    Returns DataFrame with columns y_0.25 … y_30 (yields in % per annum).
    """
    print(f"\nDownloading ECB yield curves [{START_DATE} – {END_DATE}]")
    print(f"Maturities: {list(MATURITIES.keys())}\n")

    series_list: list[pd.Series] = []
    failed: list[str] = []

    for key in MATURITIES:
        s = _fetch_single_maturity(key)
        if s is not None:
            s.name = COL_NAMES[key]
            series_list.append(s)
        else:
            failed.append(key)
        time.sleep(0.3)  # polite pause between API calls

    if failed:
        print(f"\nWARNING: Failed to download: {failed}")

    if not series_list:
        raise RuntimeError("All downloads failed. Check internet connection and ECB API status.")

    df = pd.concat(series_list, axis=1)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    # Keep only business days in the requested range
    df = df.loc[START_DATE:END_DATE]

    return df


# ---------------------------------------------------------------------------
# Missing value handling
# ---------------------------------------------------------------------------


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Forward-fill then backward-fill isolated gaps (up to 5 business days).
    Remaining NaNs after filling are reported.
    """
    original_na = df.isna().sum().sum()
    df_filled = df.ffill(limit=5).bfill(limit=5)
    remaining_na = df_filled.isna().sum().sum()

    if original_na > 0:
        print(f"\nMissing value handling:")
        print(f"  Original NaNs:  {original_na}")
        print(f"  After filling:  {remaining_na}")
        if remaining_na > 0:
            print("  Columns with remaining NaNs:")
            for col in df_filled.columns[df_filled.isna().any()]:
                print(f"    {col}: {df_filled[col].isna().sum()} NaNs")

    return df_filled


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------


def print_summary(df: pd.DataFrame) -> None:
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print(f"Date range:        {df.index[0].date()} – {df.index[-1].date()}")
    print(f"Observations:      {len(df)}")

    # Check for gaps in date index
    bdays = pd.bdate_range(df.index[0], df.index[-1])
    missing_bdays = bdays.difference(df.index)
    if len(missing_bdays) > 0:
        print(f"Missing business days: {len(missing_bdays)}")
        if len(missing_bdays) <= 10:
            print(f"  Dates: {[str(d.date()) for d in missing_bdays]}")
    else:
        print("Missing business days: 0")

    print("\nYield range by maturity (% p.a.):")
    print(f"{'Maturity':<12} {'Min':>8} {'Max':>8} {'Mean':>8} {'NaNs':>8}")
    print("-" * 50)
    for col in df.columns:
        mat = col.replace("y_", "")
        print(
            f"{mat+'Y':<12} {df[col].min():>8.3f} {df[col].max():>8.3f} "
            f"{df[col].mean():>8.3f} {df[col].isna().sum():>8}"
        )


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------


def save_data(df: pd.DataFrame) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    parquet_path = DATA_DIR / "ecb_yield_curves.parquet"
    csv_path = DATA_DIR / "ecb_yield_curves.csv"
    df.to_parquet(parquet_path)
    df.to_csv(csv_path)
    print(f"\nSaved:")
    print(f"  {parquet_path}")
    print(f"  {csv_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    df_raw = download_ecb_yields()
    df = handle_missing_values(df_raw)
    print_summary(df)
    save_data(df)
    print("\nDone.")


if __name__ == "__main__":
    main()
