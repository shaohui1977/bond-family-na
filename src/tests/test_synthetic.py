"""
test_synthetic.py — Synthetic validation of the forward-measure consistency test.

Addresses the identification critique: "your λ gaps could be model misspecification,
not genuine structural inconsistency."

Protocol:
  1. Generate yields from a known 3-factor Gaussian HJM (single Q by construction).
  2. Run the SAME 2-factor segment-wise calibration as test1.
  3. Run the SAME 3-factor segment-wise calibration as test3.
  4. Check whether synthetic 3F gaps are near zero UNIFORMLY across all pairs,
     while empirical 3F gaps show the DIVERGENT pattern (vanish long-end,
     amplify short-vs-long).

If synthetic 3F → uniform near-zero, empirical 3F → divergent:
  → the empirical divergence is evidence beyond misspecification alone.

Usage:
    python src/tests/test_synthetic.py [--quick]   # --quick uses 300 dates
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import warnings
warnings.filterwarnings("ignore")

from src.synthetic.generate_yields import main as generate_yields_main, build_synthetic_yields
from src.tests.test1_lambda_gap import (
    run_segment, compute_lambda_gaps, run_statistical_tests, SEGMENT_CAPS,
)
from src.tests.test3_robustness import (
    run_segment_3f, compute_lambda_gaps_3f, run_statistical_tests_3f,
)

DATA_DIR = PROJECT_ROOT / "data"
FIGURES_DIR = PROJECT_ROOT / "paper" / "figures"


# ---------------------------------------------------------------------------
# Run calibration pipelines on a yield DataFrame
# ---------------------------------------------------------------------------

def run_2factor_pipeline(yields: pd.DataFrame, label: str = "") -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """
    Run 2-factor segment-wise calibration on yields.

    Returns (seg_results, gaps, summary).
    """
    seg_results = {}
    for cap in SEGMENT_CAPS:
        print(f"  {label}2F segment <={int(cap)}Y ...", end=" ", flush=True)
        try:
            df = run_segment(yields, cap)
        except ValueError as e:
            print(f"SKIP ({e})")
            continue
        seg_results[cap] = df
        if df.empty:
            print("EMPTY")
        else:
            print(f"n={len(df)}")

    gaps = compute_lambda_gaps(seg_results)
    summary = run_statistical_tests(gaps)
    return seg_results, gaps, summary


def run_3factor_pipeline(yields: pd.DataFrame, label: str = "") -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """
    Run 3-factor segment-wise calibration on yields.

    Returns (seg_results, gaps, summary).
    """
    seg_results = {}
    for cap in SEGMENT_CAPS:
        print(f"  {label}3F segment <={int(cap)}Y ...", end=" ", flush=True)
        try:
            df = run_segment_3f(yields, cap)
        except ValueError as e:
            print(f"SKIP ({e})")
            continue
        seg_results[cap] = df
        if df.empty:
            print("EMPTY")
        else:
            print(f"n={len(df)}")

    gaps = compute_lambda_gaps_3f(seg_results)
    summary = run_statistical_tests_3f(gaps)
    return seg_results, gaps, summary


# ---------------------------------------------------------------------------
# Comparison table
# ---------------------------------------------------------------------------

def build_comparison_table(
    emp_2f: pd.DataFrame,
    emp_3f: pd.DataFrame,
    syn_2f: pd.DataFrame,
    syn_3f: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build side-by-side comparison of mean Δλ₁ across all four calibrations.
    """
    rows = []
    for _, r_e2 in emp_2f.iterrows():
        ts, tl = r_e2["T_short"], r_e2["T_long"]

        r_e3 = emp_3f[(emp_3f["T_short"] == ts) & (emp_3f["T_long"] == tl)]
        r_s2 = syn_2f[(syn_2f["T_short"] == ts) & (syn_2f["T_long"] == tl)]
        r_s3 = syn_3f[(syn_3f["T_short"] == ts) & (syn_3f["T_long"] == tl)]

        row = {
            "T_short": ts,
            "T_long": tl,
            "emp_2f_mean": r_e2["mean_dlambda1"],
            "emp_2f_t": r_e2["t_stat_dlambda1"],
            "emp_3f_mean": r_e3.iloc[0]["mean_dlambda1"] if not r_e3.empty else np.nan,
            "emp_3f_t": r_e3.iloc[0]["t_stat_dlambda1"] if not r_e3.empty else np.nan,
            "syn_2f_mean": r_s2.iloc[0]["mean_dlambda1"] if not r_s2.empty else np.nan,
            "syn_2f_t": r_s2.iloc[0]["t_stat_dlambda1"] if not r_s2.empty else np.nan,
            "syn_3f_mean": r_s3.iloc[0]["mean_dlambda1"] if not r_s3.empty else np.nan,
            "syn_3f_t": r_s3.iloc[0]["t_stat_dlambda1"] if not r_s3.empty else np.nan,
        }
        # Gap shrinkage ratios (|3F| / |2F|), smaller = better recovery
        if not np.isnan(row["emp_2f_mean"]) and abs(row["emp_2f_mean"]) > 1e-6:
            row["emp_shrinkage"] = abs(row["emp_3f_mean"]) / abs(row["emp_2f_mean"])
        else:
            row["emp_shrinkage"] = np.nan

        if not np.isnan(row["syn_2f_mean"]) and abs(row["syn_2f_mean"]) > 1e-6:
            row["syn_shrinkage"] = abs(row["syn_3f_mean"]) / abs(row["syn_2f_mean"])
        else:
            row["syn_shrinkage"] = np.nan

        rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def _make_heatmap(ax, values: dict, caps: list, title: str, vmax: float) -> None:
    """Fill ax with a heatmap of mean |Δλ₁| by segment pair."""
    n = len(caps)
    cap_idx = {c: i for i, c in enumerate(caps)}
    mat = np.full((n, n), np.nan)

    for (ts, tl), v in values.items():
        i, j = cap_idx[ts], cap_idx[tl]
        mat[i, j] = mat[j, i] = abs(v)

    labels = [f"{int(c)}Y" for c in caps]
    im = ax.imshow(mat, cmap="YlOrRd", vmin=0, vmax=vmax, aspect="auto")
    ax.set_xticks(range(n)); ax.set_xticklabels(labels, fontsize=8)
    ax.set_yticks(range(n)); ax.set_yticklabels(labels, fontsize=8)
    ax.set_title(title, fontsize=10)
    for i in range(n):
        for j in range(n):
            if not np.isnan(mat[i, j]):
                ax.text(j, i, f"{mat[i,j]:.3f}", ha="center", va="center", fontsize=7)
    return im


def plot_comparison_heatmap(comparison: pd.DataFrame) -> None:
    """
    Four-panel heatmap: empirical/synthetic × 2F/3F.
    Saved to figures/synthetic_comparison_heatmap.png
    """
    caps = sorted(SEGMENT_CAPS)

    # Build lookup dicts
    def _to_dict(df, col):
        return {(row["T_short"], row["T_long"]): row[col] for _, row in df.iterrows()}

    emp2 = _to_dict(comparison, "emp_2f_mean")
    emp3 = _to_dict(comparison, "emp_3f_mean")
    syn2 = _to_dict(comparison, "syn_2f_mean")
    syn3 = _to_dict(comparison, "syn_3f_mean")

    all_vals = [abs(v) for d in [emp2, emp3, syn2, syn3] for v in d.values() if not np.isnan(v)]
    vmax = max(all_vals) if all_vals else 1.0

    fig, axes = plt.subplots(2, 2, figsize=(13, 11))
    panels = [
        (axes[0, 0], emp2, "Empirical — 2-factor"),
        (axes[0, 1], emp3, "Empirical — 3-factor"),
        (axes[1, 0], syn2, "Synthetic — 2-factor (mis-spec.)"),
        (axes[1, 1], syn3, "Synthetic — 3-factor (true model)"),
    ]
    for ax, vals, title in panels:
        im = _make_heatmap(ax, vals, caps, title, vmax)

    fig.colorbar(im, ax=axes, label="Mean |Δλ₁|", shrink=0.6)
    fig.suptitle(
        "Synthetic Validation: λ₁ Gaps — Empirical vs Synthetic × 2F vs 3F\n"
        "(Synthetic 3F should show uniform near-zero; empirical 3F shows divergent pattern)",
        fontsize=11,
    )
    plt.tight_layout(rect=[0, 0, 0.88, 0.95])
    out = FIGURES_DIR / "synthetic_comparison_heatmap.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out}")


def plot_gap_shrinkage(comparison: pd.DataFrame) -> None:
    """
    Bar chart: gap shrinkage ratio |Δλ₁_3F| / |Δλ₁_2F| by pair, empirical vs synthetic.

    Key insight: synthetic shrinkage should be uniform and small;
    empirical shrinkage is heterogeneous (long-end → near 0, short-vs-long → >1).
    Saved to figures/synthetic_gap_shrinkage.png
    """
    df = comparison.dropna(subset=["emp_shrinkage", "syn_shrinkage"]).copy()
    df["pair"] = df.apply(lambda r: f"{int(r.T_short)}Y-{int(r.T_long)}Y", axis=1)

    x = np.arange(len(df))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(x - width / 2, df["emp_shrinkage"], width, label="Empirical", color="#1f77b4", alpha=0.8)
    ax.bar(x + width / 2, df["syn_shrinkage"], width, label="Synthetic", color="#ff7f0e", alpha=0.8)
    ax.axhline(1.0, color="black", linewidth=0.8, linestyle="--", label="No change (ratio=1)")
    ax.axhline(0.0, color="gray", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(df["pair"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Gap shrinkage ratio |Δλ₁_3F| / |Δλ₁_2F|")
    ax.set_title(
        "Synthetic Validation: Gap Shrinkage when Moving from 2-factor to 3-factor\n"
        "Synthetic (true 3F DGP) should shrink uniformly to ~0; "
        "empirical shows heterogeneous shrinkage"
    )
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    out = FIGURES_DIR / "synthetic_gap_shrinkage.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out}")


# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------

def print_summary(comparison: pd.DataFrame, syn_2f_summary: pd.DataFrame, syn_3f_summary: pd.DataFrame) -> None:
    n_syn_2f_reject = (syn_2f_summary["p_adj_dlambda1"] < 0.05).sum()
    n_syn_3f_reject = (syn_3f_summary["p_adj_dlambda1"] < 0.05).sum()
    n_pairs = len(comparison)

    syn_3f_max_gap = comparison["syn_3f_mean"].abs().max()
    emp_3f_max_gap = comparison["emp_3f_mean"].abs().max()

    print("\n" + "=" * 70)
    print("SYNTHETIC VALIDATION SUMMARY")
    print("=" * 70)
    print(f"\nSynthetic 2F: {n_syn_2f_reject}/{n_pairs} pairs reject H0 (Bonf. 5%)")
    print(f"Synthetic 3F: {n_syn_3f_reject}/{n_pairs} pairs reject H0 (Bonf. 5%)")
    print(f"\nMax |dlambda1| synthetic 3F: {syn_3f_max_gap:.4f}")
    print(f"Max |dlambda1| empirical 3F: {emp_3f_max_gap:.4f}")

    print(f"\n{'Pair':<10}  {'Emp 2F':>8}  {'Emp 3F':>8}  {'Syn 2F':>8}  {'Syn 3F':>8}  "
          f"{'Emp shr':>8}  {'Syn shr':>8}")
    print("-" * 72)
    for _, r in comparison.iterrows():
        print(
            f"{int(r.T_short)}Y-{int(r.T_long)}Y{'':<2} "
            f"{r.emp_2f_mean:>8.4f}  {r.emp_3f_mean:>8.4f}  "
            f"{r.syn_2f_mean:>8.4f}  {r.syn_3f_mean:>8.4f}  "
            f"{r.emp_shrinkage:>8.3f}  {r.syn_shrinkage:>8.3f}"
        )

    # Diagnostic conclusion
    print("\n--- Interpretation ---")

    # Criterion 1: synthetic 2F rejects
    ok1 = n_syn_2f_reject >= n_pairs // 2
    print(f"[{'PASS' if ok1 else 'FAIL'}] Synthetic 2F detects misspecification "
          f"({n_syn_2f_reject}/{n_pairs} pairs rejected)")

    # Criterion 2: synthetic 3F near-zero uniformly
    ok2 = n_syn_3f_reject == 0
    print(f"[{'PASS' if ok2 else 'FAIL'}] Synthetic 3F shows near-zero gaps uniformly "
          f"({n_syn_3f_reject}/{n_pairs} pairs rejected)")

    # Criterion 3: empirical 3F pattern is divergent (not uniform)
    syn_shr = comparison["syn_shrinkage"].dropna()
    emp_shr = comparison["emp_shrinkage"].dropna()
    syn_shr_std = syn_shr.std()
    emp_shr_std = emp_shr.std()
    ok3 = emp_shr_std > 2 * syn_shr_std
    print(
        f"[{'PASS' if ok3 else 'FAIL'}] Empirical 3F shows divergent pattern vs synthetic 3F "
        f"(emp_shrinkage_std={emp_shr_std:.3f}, syn_shrinkage_std={syn_shr_std:.3f})"
    )

    if ok1 and ok2 and ok3:
        print("\nCONCLUSION: Synthetic validation supports the identification claim.")
        print("The empirical lambda-gap pattern (divergent under 3F) is NOT attributable")
        print("to model misspecification alone.")
    elif ok1 and not ok2:
        print("\nCONCLUSION: NEGATIVE RESULT — synthetic 3F also shows non-zero gaps.")
        print("The test itself may have structural bias. Empirical divergence is not diagnostic.")
    else:
        print("\nCONCLUSION: Mixed results — see comparison table above.")

    print("=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(quick: bool = False) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # --- Load or generate synthetic yields ---
    synth_path = DATA_DIR / "synthetic_yields.csv"
    dgp_path = DATA_DIR / "synthetic_dgp_params.json"

    if synth_path.exists() and dgp_path.exists():
        print("Loading existing synthetic yields ...")
        synth = pd.read_csv(synth_path, index_col=0, parse_dates=True)
        import json
        with open(dgp_path) as f:
            dgp = json.load(f)
        print(f"  Loaded: {synth.shape}")
    else:
        print("Synthetic yields not found — generating ...")
        dgp = generate_yields_main()
        synth = pd.read_csv(synth_path, index_col=0, parse_dates=True)

    # --- Load empirical yields ---
    yields_emp = pd.read_parquet(DATA_DIR / "ecb_yield_curves.parquet")
    yields_emp.index = pd.to_datetime(yields_emp.index)
    yields_emp.columns = [
        f"y_{int(T)}" if T == int(T) else f"y_{T}"
        for T in [0.25, 0.5, 1, 2, 3, 5, 7, 10, 15, 20, 25, 30]
    ]

    # Optional: restrict to quick subset for testing
    if quick:
        n_quick = 300
        print(f"\n[QUICK MODE] Using first {n_quick} dates.")
        synth = synth.iloc[:n_quick]

    print(f"\nSynthetic yields: {synth.shape[0]} dates × {synth.shape[1]} maturities")

    # --- Run calibrations on synthetic data ---
    print("\n[2-factor calibration on synthetic yields]")
    _, syn_gaps_2f, syn_summary_2f = run_2factor_pipeline(synth, label="syn ")
    syn_summary_2f.to_csv(DATA_DIR / "synthetic_test1_results.csv", index=False)
    print("  Saved: data/synthetic_test1_results.csv")

    print("\n[3-factor calibration on synthetic yields]")
    _, syn_gaps_3f, syn_summary_3f = run_3factor_pipeline(synth, label="syn ")
    syn_summary_3f.to_csv(DATA_DIR / "synthetic_test3_results.csv", index=False)
    print("  Saved: data/synthetic_test3_results.csv")

    # --- Load empirical summaries ---
    emp_summary_2f = pd.read_csv(DATA_DIR / "test1_summary.csv")
    emp_summary_3f = pd.read_csv(DATA_DIR / "test3_summary.csv")

    # --- Build comparison ---
    comparison = build_comparison_table(
        emp_summary_2f, emp_summary_3f,
        syn_summary_2f, syn_summary_3f,
    )
    comparison.to_csv(DATA_DIR / "synthetic_summary.csv", index=False)
    print("  Saved: data/synthetic_summary.csv")

    # --- Console summary ---
    print_summary(comparison, syn_summary_2f, syn_summary_3f)

    # --- Figures ---
    print("\nGenerating figures ...")
    plot_comparison_heatmap(comparison)
    plot_gap_shrinkage(comparison)

    print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true",
                        help="Run on first 300 dates only (for pipeline testing)")
    args = parser.parse_args()
    main(quick=args.quick)
