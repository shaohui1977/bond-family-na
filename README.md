# Does the Bond Market Need a Bank Account?

**Forward Measure Consistency and Interest Rate Pricing**

Shaohui Wang — Working paper, April 2026

## The Question

The standard no-arbitrage framework for bond markets assumes the
existence of a tradable bank account B as universal numéraire. But B
is not directly traded — it must be synthesized via a rolling bond
strategy that, in continuous time, requires rebalancing through
uncountably many maturities.

Meanwhile, practitioners price and hedge using T-forward measures
Q^T, each derived from a single tradable bond, without invoking B.

This paper asks: does the family {Q^T}, built from tradable bonds
alone, necessarily cohere into a single global measure Q — or is Q
an additional assumption?

## What the Paper Does

**Proof of concept (Section 2).** In discrete time, consistency is
automatic: the bank account emerges as a self-financing rolling
strategy. A four-way FTAP equivalence identifies the precise point
where the argument uses finiteness.

**The question formalized (Section 3).** A Q-free, B-free definition
of forward-measure consistency (Definition 3.2.1), with the question
stated in falsifiable form. The diagonal singularity of the forward
rate surface is identified as a possible mechanism for failure.

**Empirical exercise (Section 4).** Independent calibration of
Gaussian HJM models on different maturity segments of the EUR
government bond market (ECB data, 2014–2024). The implied market
prices of risk differ systematically across segments in a divergent
pattern that synthetic controls cannot replicate. This does not
answer the question — the pattern is consistent with either absence
of Q or inadequacy of the model class — but it establishes the
question has empirical content.

## Reproducing Results

### Setup

```bash
conda create -n bondna python=3.11 -y
conda activate bondna
pip install -r requirements.txt
```

### Download Data

Data is fetched from the ECB Statistical Data Warehouse (public API,
no key required).

```bash
python src/data/fetch_ecb.py
```

### Run Tests

```bash
python src/tests/test1_lambda_gap.py      # Two-factor segment-wise calibration
python src/tests/test1_robust_kappa.py    # κ₁ bound sensitivity check
python src/tests/test3_robustness.py      # Three-factor comparison
python src/tests/test_synthetic.py        # Synthetic validation (30Y and 5Y DGPs)
```

### Build PDF

```bash
conda install -c conda-forge pandoc tectonic -y
cd paper && make pdf
```

## Structure

```
paper/              Working paper (paper.md, paper.tex), figures
src/data/           ECB data download
src/models/         Gaussian HJM calibration (2- and 3-factor)
src/synthetic/      Synthetic yield generation for validation
src/tests/          Empirical exercises and synthetic validation
src/utils/          Yield curve and statistics utilities
data/               Downloaded and generated data (gitignored, reproducible)
```

## Key References

- Klein, Schmidt, and Teichmann (2016). "No arbitrage theory for
  bond markets." — Closest prior work; bond markets without bank account.
- Herdegen (2017). "No-arbitrage in a numéraire-independent modeling
  framework." — Numéraire-free FTAP for general markets.
- Musiela and Rutkowski (1997). — Uniqueness of implied savings
  account (existence taken as given; our question is the complement).

## Acknowledgments

Developed in collaboration with Claude (Anthropic, Opus). See the
paper's Acknowledgments section for details.

## License

Paper: All rights reserved.
Code: MIT License.
