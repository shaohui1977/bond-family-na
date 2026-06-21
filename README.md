# Does the Bond Market Need a Bank Account?

**Forward Measure Consistency and Interest Rate Pricing**

Shaohui Wang — Working paper, June 2026

## The Question

The standard no-arbitrage framework for bond markets assumes a tradable
bank account B as universal numéraire. But B is not directly traded —
it must be synthesized from zero-coupon bonds via a rolling strategy
that, in continuous time, requires continuous rebalancing. Meanwhile
practitioners price using T-forward measures Q^T, each derived from a
single tradable bond, without invoking B.

This paper asks: does the family {Q^T}, built from tradable bonds
alone, necessarily cohere into a single global measure Q — or is Q (and
therefore B) an additional assumption?

## What the Paper Establishes

**Proof of concept (Section 2).** In discrete time the answer is yes:
the bank account emerges as a self-financing rolling strategy, via a
four-way FTAP equivalence. The discreteness that does the work is
discreteness of *trading*, not of the maturity set.

**A precise, Q-free definition (Section 3).** Definition 3.2.1 states
forward-measure consistency using only bond prices and the family
{Q^T}, presupposing no global Q or numéraire. Lemma 2.4.1 shows the
pairwise consistency conditions self-propagate to all finite orders
(the cocycle is automatic) and exclude bond-ratio bubbles — so
finite-level incompatibility is never the source of failure.

**The obstruction, located (Section 3.4).** Given Lemma 2.4.1, the only
thing that can fail in continuous time is the construction of the
numéraire B itself — not measure incompatibility, and not a
projective-limit extension problem (every Q^T already lives on the same
probability space). The risk-neutral measure is anchored by B, not by
any single Q^T. Whether a consistent family can exist without an
underlying (Q, B) is the open question.

**Empirical content, honestly scoped (Section 4).** A descriptive
exercise — independent Gaussian-HJM calibration on EUR government curve
segments (ECB, 2014–2024) — finds the implied market prices of risk
differ systematically across maturity segments, in a divergent pattern
that the synthetic controls examined do not reproduce. This does NOT
answer the question: the pattern is a model-bundled proxy (it
presupposes the Gaussian-HJM class and a maturity-independent market
price of risk), and is consistent with either absence of Q or model
inadequacy. It establishes only that the question has empirical
content.

The paper does not resolve the continuous-time existence question, and
states precisely (Section 5) where the residual gap to the
large-financial-markets results of Klein–Schmidt–Teichmann (2016) lies,
without claiming to bridge it.

## Reproducing Results

### Setup

```bash
conda create -n bondna python=3.11 -y
conda activate bondna
pip install -r requirements.txt
```

### Download Data

ECB Statistical Data Warehouse spot rates (Svensson-fitted), public
API, no key required.

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
cd paper && make arxiv
```

## Structure

```
paper/              Working paper (paper.md, paper.tex), figures
src/data/           ECB data download
src/models/         Gaussian HJM calibration (2- and 3-factor)
src/synthetic/      Synthetic yield generation for the controls
src/tests/          Empirical exercises and synthetic controls
src/utils/          Yield curve and statistics utilities
data/               Downloaded and generated data (gitignored, reproducible)
```

## Key References

- Klein, Schmidt, and Teichmann (2016). "No arbitrage theory for bond
  markets." — Closest prior work; bond markets without a bank account.
- Herdegen (2017). "No-arbitrage in a numéraire-independent modeling
  framework." — Numéraire-free FTAP for general markets.
- Musiela and Rutkowski (1997). — Uniqueness of the implied savings
  account (existence assumed; our question is the complement).

## Acknowledgments

Developed in collaboration with Claude (Anthropic). See the paper's
Acknowledgments section for details.

## License

Paper: All rights reserved.
Code: MIT License.
