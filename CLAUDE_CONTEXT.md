*This file provides context for AI-assisted development sessions.*

# CLAUDE_CONTEXT.md — Bond-Family No-Arbitrage Project

## What This Is

A research project asking: does the bond market need a bank account?

Specifically: in a bond market, each tradable zero-coupon bond p(·,T)
provides a natural numéraire and a T-forward measure Q^T. We ask
whether this family {Q^T} is globally consistent — i.e., whether a
single risk-neutral measure Q exists. The bank account B appears as
the *output* of consistency, not a starting point.

## Paper Status

Working paper v5 (`paper/paper.md`). Structure:
- Section 2: Discrete-time proposition (automatic consistency, proof complete)
- Section 3: Continuous-time conjecture (HJM drift = consistency condition; §3.3 Sobolev trace obstruction)
- Section 4: Practical consequences (multi-curve, model risk, Solvency II)
- Section 5: Empirical test (complete — Tests 1 and 3 done, results in paper)
- Section 6: Mathematical open problems
- Section 7: Conclusion

PDF: `paper/paper.pdf` (built via `cd paper && make pdf`).

## Empirical Test Design (Section 5)

### Principle
Calibrate local pricing measures *independently* for different maturity
segments, then check whether they cohere. Bottom-up test, not top-down.

### Test 1: Market Price of Risk Stability (complete)
- Define segments I_k = [0, T_k], T_k = 5, 10, 15, 20, 25, 30 years
- For each segment: fit two-factor Gaussian HJM → market price of risk λ^{(k)}
- Compare λ^{(k)} across segments: Δλ(t; j,k) = λ^{(k)} − λ^{(j)}
- H₀: Δλ = 0 (consistency). H₁: Δλ depends on |T_k − T_j|
- **Result**: H₀ rejected 13/15 segment pairs (Bonferroni 5%); gap monotone in segment distance

### Test 2: Chain Rule Verification (dropped)
- Originally designed as a second diagnostic; dropped after Test 3 provided
  the discriminating comparison (model inadequacy vs structural inconsistency).
  Nice-to-have only.

### Test 3: Three-Factor Robustness (complete)
- Adds curvature factor: σ₃(τ) = σ₃·τ·exp(−κ₃·τ)
- **Result**: long-end gaps (≥15Y) vanish with 3 factors (model inadequacy);
  short-vs-long gaps (5Y vs ≥10Y) persist and widen (structural inconsistency)
- R² improves from 0.84 → 0.94 for 30Y segment; interpretation is clean

### Model
Two-factor Gaussian HJM (baseline):
  df(t,T) = μ(t,T)dt + σ₁ exp(−κ₁(T−t)) dW₁ + σ₂ exp(−κ₂(T−t)) dW₂

Parameters: Θ = (σ₁, σ₂, κ₁, κ₂, λ₁, λ₂)
All computations closed-form (Gaussian integrals). No Monte Carlo.

### Data
ECB daily zero-coupon yield curves, EUR AAA-rated government bonds.
Maturities (12 series): 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 15Y, 20Y, 25Y, 30Y.
All 12 maturities are used in calibration; sub-year points (3M, 6M) anchor
the short end of each segment.
Period: January 2014 – December 2024 (2,805 trading days).
Source: https://data-api.ecb.europa.eu/ (public, no API key required)

## Repository Structure

```
bond-family-na/
├── paper/
│   ├── paper.md              Working paper v5
│   ├── paper.pdf             Built output (make pdf)
│   ├── Makefile              PDF build: make pdf
│   ├── pandoc-header.tex     Font config (Cambria/Cambria Math)
│   ├── section2_proofs.md    Discrete-time proofs detail
│   └── figures/              Generated plots
├── src/
│   ├── data/
│   │   ├── fetch_ecb.py      Download ECB yield curves
│   │   └── verify_data.py    Data quality checks
│   ├── models/
│   │   ├── gaussian_hjm.py   2/3-factor HJM calibration
│   │   └── pca.py            PCA on forward rate changes
│   ├── tests/
│   │   ├── test1_lambda_gap.py     Main consistency test
│   │   ├── test1_robust_kappa.py   κ₁ bound sensitivity
│   │   └── test3_robustness.py     3-factor comparison
│   └── utils/
│       ├── yield_curve.py    Bond prices, forward rates
│       └── statistics.py     Newey-West, Bonferroni
├── prompts/                  Session working notes
├── data/                     Downloaded + computed (gitignored, reproducible)
├── CLAUDE_CONTEXT.md
├── requirements.txt
└── .gitignore
```

## Reproducing Results

```bash
# 1. Environment
conda create -n bondna python=3.11 -y
conda activate bondna
pip install -r requirements.txt

# 2. Data (ECB public API, no key required)
python src/data/fetch_ecb.py          # → data/ecb_yield_curves.parquet

# 3. Tests
python src/tests/test1_lambda_gap.py  # → data/test1_results.parquet, test1_summary.csv
python src/tests/test1_robust_kappa.py
python src/tests/test3_robustness.py  # → data/test3_summary.csv, test3_vs_test1.csv

# 4. PDF
conda install -c conda-forge pandoc tectonic -y
cd paper && make pdf
```

## Tech Stack

- Python 3.11 (conda environment "bondna")
- NumPy, SciPy, pandas, matplotlib, statsmodels
- Pandoc + Tectonic (XeLaTeX) for PDF
- No GPU, no ML frameworks, no Monte Carlo
- All closed-form Gaussian HJM computations

## Author

Shaohui Wang, PhD Financial Mathematics (Universität Ulm, 2008), DAV actuary.

## Working Style

- Claude.ai Opus for deep reasoning and paper development
- Claude Code (Sonnet) for implementation
- Financial intuition first, formalism second
- Challenge assumptions, flag errors, be direct
