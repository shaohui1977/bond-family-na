# Does the Bond Market Need a Bank Account?

**Forward Measure Consistency and Interest Rate Pricing**

Shaohui Wang — Working paper, 2026

## Summary

As Samuelson (1938) asked whether observed consumer choices imply the
existence of a utility function, we ask whether observed bond prices
imply the existence of a risk-neutral measure.

In a bond market, each zero-coupon bond provides a natural numéraire
and a T-forward measure Q^T. This paper investigates whether the
family {Q^T} is globally consistent — i.e., whether a single
risk-neutral measure Q exists. If it does, the bank account B
emerges as a derived object; if it doesn't, the classical framework
has a structural limitation.

We prove the discrete-time case (automatic consistency), formulate
the continuous-time conjecture (HJM drift condition as consistency
condition), and test empirically using EUR government bond data
(ECB, 2014–2024). The test rejects consistency for 13 of 15 maturity
segment pairs; a three-factor comparison separates model inadequacy
from structural inconsistency.

## Reproducing Results

### Setup

```bash
conda create -n bondna python=3.11 -y
conda activate bondna
pip install -r requirements.txt
```

### Download Data

Data is fetched from the ECB Statistical Data Warehouse (public API, no key required).

```bash
python src/data/fetch_ecb.py
```

### Run Tests

```bash
python src/tests/test1_lambda_gap.py      # Main consistency test
python src/tests/test1_robust_kappa.py    # κ₁ bound sensitivity
python src/tests/test3_robustness.py      # 3-factor comparison
```

### Build PDF

```bash
conda install -c conda-forge pandoc tectonic -y
cd paper && make pdf
```

## Structure

```
paper/          Working paper (paper.md), PDF (bond_family_na.pdf), Makefile
src/data/       ECB data download
src/models/     Gaussian HJM calibration (2- and 3-factor)
src/tests/      Empirical consistency tests
src/utils/      Yield curve and statistics utilities
data/           Downloaded data (gitignored, reproducible via above)
```

## License

Paper: All rights reserved.
Code: MIT License.
