# Does the Bond Market Need a Bank Account?

**Forward-Measure Families, Pricing Kernels, and When the Savings Account Is a Numéraire**

Shaohui Wang — September 2026

## The Question

Practitioners price interest-rate derivatives with $T$-forward measures, each
anchored by a traded bond; the textbook theory starts from a bank account that
is not traded. This note asks what the family of forward measures implies by
itself, and in particular whether it implies a bank account.

## What the Paper Establishes

**Pricing needs no bank account (Section 3).** A consistent family of
forward measures — defined without reference to any risk-neutral measure or
account (Definition 3.1) — is shown to be exactly a pricing kernel in other
coordinates (Theorem 3.2), with no semimartingale property, no supermartingale
property, and no path regularity implied beyond it. The terminal bond is
always a numéraire.

**At every finite tenor structure the bank account exists (Section 4.1).**
For any finite set of roll-over dates, the roll-over strategy in
just-maturing bonds is a numéraire under consistency alone (Proposition
4.1) — no further condition is needed. This is the discrete-time bank
account of Section 2, generalized, and the spot LIBOR measure of Jamshidian
(1997).

**In continuous time the account need not be a numéraire (Section 4.2–4.3).**
A savings account — a predictable numéraire of finite variation — exists if
and only if the terminal bond's generator is *good* in the sense of Döberlein
and Schweizer (2001): its multiplicative decomposition has a *true*
martingale factor. Consistency does not imply goodness. An explicit example
— built on Platen's minimal market model and used for this purpose by Klein,
Schmidt, and Teichmann (2016) — has a smooth, strictly decreasing term
structure and a zero short rate, and no savings account: every finite
roll-over is priced at par, and the limit is not (Propositions 4.8–4.9,
Appendix B).

**What data can and cannot say (Section 5).** Existence of a pricing kernel
has no model-free testable content on a panel of bond prices; whether the
account is a numéraire is a statement about states a sample does not visit.
Both questions can only be probed jointly with a parametric model class. The
segment-wise Gaussian-HJM calibration exercise in this repository (see
below) is discussed in this light: disagreement in the calibrated market
price of risk across maturity segments is a diagnostic of the model class,
not evidence for or against either question.

This is a theory note, not a question paper: (i) and (ii) settle what
practitioners' forward-measure approach implies on its own; (iii) is a known
result (the benchmark-approach / bubble literature), reformulated and proved
elementarily in the forward-measure language used here. See the paper's
§1.3 for the precise attribution of what is new and what is not.

## Reproducing the Empirical Illustration

The calibration exercise below is a diagnostic discussed in Section 5, not a
test of the paper's theorems (which are settled by construction).

### Setup

```bash
conda create -n bondna python=3.11 -y
conda activate bondna
pip install -r requirements.txt
```

### Download Data

ECB Statistical Data Warehouse spot rates (Svensson-fitted), public API, no
key required.

```bash
python src/data/fetch_ecb.py
```

### Run Exercises

```bash
python src/tests/test1_lambda_gap.py      # Two-factor segment-wise calibration
python src/tests/test1_robust_kappa.py    # kappa_1 bound sensitivity
python src/tests/test3_robustness.py      # Three-factor comparison
python src/tests/test_synthetic.py        # Synthetic controls (30Y and 5Y DGPs)
```

### Build PDF

```bash
conda install -c conda-forge pandoc tectonic -y
cd paper && make pdf
```

## Structure

```
paper/              Paper (paper.md, paper.pdf), figures
src/data/           ECB data download
src/models/         Gaussian HJM calibration (2- and 3-factor)
src/synthetic/      Synthetic yield generation for the controls
src/tests/          Empirical exercises and synthetic controls
src/utils/          Yield curve and statistics utilities
data/               Downloaded and generated data (gitignored, reproducible)
```

## Key References

- Döberlein, F. and Schweizer, M. (2001). "On savings accounts in
  semimartingale term structure models." — Goodness; the existence
  mechanism for a savings account.
- Klein, I., Schmidt, T., and Teichmann, J. (2016). "No arbitrage theory for
  bond markets." — Terminal-bond numéraire; the example used in Section 4.3.
- Musiela, M. and Rutkowski, M. (1997). "Continuous-time term structure
  models: forward measure approach." — The forward-measure axiomatization
  this note takes as primitive.

## Acknowledgments

Developed in extended collaboration with Claude (Anthropic). See the paper's
Acknowledgments section for details.

## License

Paper: All rights reserved.
Code: MIT License.
