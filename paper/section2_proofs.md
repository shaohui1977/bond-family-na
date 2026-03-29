# Section 2: Bond-Based No-Arbitrage in Discrete Time

*Note: The main result appears as Proposition 2.3.1 in the paper
and as Theorem 2.6.1 here. The different labels reflect the
paper's emphasis on the result's elementary character.*

---

## 2.1 Model Setup

**Assumption 2.1.1 (Discrete-Time Bond Market).**
Let $(\Omega, \mathcal{F}, (\mathcal{F}_t)_{t=0,1,\ldots,N}, \mathbb{P})$ be a filtered probability space
with $\mathcal{F}_0 = \{\emptyset, \Omega\}$ and $\mathcal{F}_N = \mathcal{F}$, where $N \geq 2$ is the terminal time.

The market consists of:

(a) *Default-free zero-coupon bonds.* For each maturity $T \in \{1,\ldots,N\}$,
    a price process $(p(t,T))_{t=0,\ldots,T}$, adapted, satisfying:

      $p(T,T) = 1$    (maturity condition),
      $p(t,T) > 0$    $\mathbb{P}$-a.s. for all $0 \le t \le T$    (strict positivity).

(b) *Risky assets.* Finitely many price processes $X^1,\ldots,X^d$, each
    adapted, nonneg, with $X^i(0) > 0$.

We denote the full collection of tradable assets by

  $\mathcal{S} = (p(\cdot,1), p(\cdot,2), \ldots, p(\cdot,N), X^1, \ldots, X^d)$.

**Remark 2.1.1 (What is not assumed).**
No bank account or risk-free asset is assumed as a primitive of the
model. The quantities $r(t)$, $B(t)$ that appear later are constructed
from bond prices.

**Convention.** For $t > T$, we set $p(t,T) := 0$. A matured bond has zero
market value (its payoff has already been received).

---

## 2.2 Strategies and Self-Financing

**Definition 2.2.1 (Trading Strategy).**
A *trading strategy* is a pair $(\varphi, \psi)$ of predictable processes, where:

  $\varphi = (\varphi^1_t, \ldots, \varphi^N_t)_{t=1,\ldots,N}$,     $\varphi^T_t$ is $\mathcal{F}_{t-1}$-measurable,
  $\psi = (\psi^1_t, \ldots, \psi^d_t)_{t=1,\ldots,N}$,     $\psi^i_t$ is $\mathcal{F}_{t-1}$-measurable.

Here $\varphi^T_t$ denotes the number of T-bonds held during the period $(t-1, t]$,
and $\psi^i_t$ the number of units of risky asset $X^i$ held during $(t-1, t]$.
Predictability ($\mathcal{F}_{t-1}$-measurability) reflects the requirement that
portfolio decisions are made before observing prices at time $t$.

**Definition 2.2.2 (Portfolio Value and Self-Financing).**
The *portfolio value* at time $t$ is

  $$V_t = \sum_{T \geq t} \varphi^T_t \cdot p(t,T) + \sum_{i=1}^d \psi^i_t \cdot X^i(t).        \quad (2.1)$$

The sum over $T$ runs from $t$ to $N$ (only bonds not yet matured contribute).
We also define $V_0 := \sum_T \varphi^T_1 \cdot p(0,T) + \sum_i \psi^i_1 \cdot X^i(0)$.

The strategy is *self-financing* if for each $t = 1, \ldots, N$:

  $$V_t = V_{t-1} + \sum_{T=t}^N \varphi^T_t \cdot [p(t,T) - p(t-1,T)]
                  + \sum_{i=1}^d \psi^i_t \cdot [X^i(t) - X^i(t-1)].          \quad (2.2)$$

Equivalently, portfolio value changes arise solely from price movements
of held assets, with no injection or withdrawal of capital.

**Remark 2.2.1 (Bond maturity within self-financing).**
When the $T$-bond matures at time $T$, the holder receives $p(T,T) = 1$ per
unit. In the self-financing condition (2.2), this appears as the gain
$\varphi^T_T \cdot [p(T,T) - p(T-1,T)] = \varphi^T_T \cdot [1 - p(T-1,T)]$. The maturity
payoff is automatically accounted for — it is just another price
increment, from $p(T-1,T)$ to $1$.

---

## 2.3 The Rolling Bond Strategy

The bank account B(t) will be constructed as the value of a specific
self-financing strategy that trades only in just-maturing bonds.

**Definition 2.3.1 (Just-maturing bond).**
The *just-maturing bond at time $t$* is the bond $p(\cdot,t)$ with maturity $T = t$.
Over the period $(t-1,t]$, it provides the one-period return

  $$\frac{p(t,t)}{p(t-1,t)} = \frac{1}{p(t-1,t)},$$

which is deterministic conditional on $\mathcal{F}_{t-1}$ (since $p(t-1,t)$ is
$\mathcal{F}_{t-1}$-measurable and $p(t,t) = 1$ with certainty).

**Proposition 2.3.1 (Construction of B).**
Define

  $$B(0) := 1,    B(t) := \prod_{s=1}^{t}  \frac{1}{p(s-1,s)},    t = 1,\ldots,N.    \quad (2.3)$$

Then:
(i)  $B(t) > 0$ for all $t$, $\mathbb{P}$-a.s.
(ii) $B(t)$ is $\mathcal{F}_{t-1}$-measurable for each $t \ge 1$.
(iii) $B$ is the value process of a self-financing trading strategy
     that uses only just-maturing bonds.

*Proof.*
(i) follows from $p(s-1,s) > 0$ for all $s$.

(ii) $B(t) = \prod_{s=1}^t 1/p(s-1,s)$. Each factor $1/p(s-1,s)$ is
$\mathcal{F}_{s-1}$-measurable, hence $\mathcal{F}_{t-1}$-measurable. The product is
$\mathcal{F}_{t-1}$-measurable.

(iii) Define the rolling strategy $\varphi^{\text{roll}}$ as follows. During each
period $(t-1,t]$, hold

  $$\varphi^t_t := \frac{B(t-1)}{p(t-1,t)}        \quad (2.4)$$

units of the $t$-bond, and zero units of all other assets. Note that
$\varphi^t_t$ is $\mathcal{F}_{t-1}$-measurable: $B(t-1)$ is $\mathcal{F}_{t-2}$-measurable (by part (ii))
and $p(t-1,t)$ is $\mathcal{F}_{t-1}$-measurable. Thus the strategy is predictable.

We verify self-financing by checking that the portfolio value at each
time equals the accumulated gains.

*Value at time $t-1$ (just before the period starts):*
The portfolio holds $\varphi^t_t$ units of the $t$-bond. Its value is

  $$V_{t-1} = \varphi^t_t \cdot p(t-1,t) = \left[\frac{B(t-1)}{p(t-1,t)}\right] \cdot p(t-1,t) = B(t-1).$$

*Value at time $t$ (the $t$-bond matures):*
The gain from holding $\varphi^t_t$ units of the $t$-bond is

  $$\varphi^t_t \cdot [p(t,t) - p(t-1,t)] = \varphi^t_t \cdot [1 - p(t-1,t)].$$

So $V_t = V_{t-1} + \varphi^t_t \cdot [1 - p(t-1,t)]$
       $= B(t-1) + \left[\frac{B(t-1)}{p(t-1,t)}\right] \cdot [1 - p(t-1,t)]$
       $= B(t-1) \cdot \left[1 + \frac{1 - p(t-1,t)}{p(t-1,t)}\right]$
       $= B(t-1) \cdot \left[\frac{1}{p(t-1,t)}\right]$
       $= B(t)$.

The proceeds $B(t)$ are then invested into $\varphi^{t+1}_{t+1} = B(t)/p(t,t+1)$
units of the $(t+1)$-bond, and the process repeats. No capital is injected
or withdrawn.        $\quad\square$

**Remark 2.3.2 (Financial interpretation).**
$B(t)$ is the value at time $t$ of one unit of currency invested at time 0
into the shortest-maturity bond, rolled over at each period. The
one-period gross return is $1/p(t-1,t)$, and the one-period net return is

  $$R_t^{(\text{rf})} := \frac{1}{p(t-1,t)} - 1 = \frac{1 - p(t-1,t)}{p(t-1,t)}.         \quad (2.5)$$

This is $\mathcal{F}_{t-1}$-measurable — deterministic given the information at
time $t-1$. It is the discrete-time analogue of the risk-free rate.

**Remark 2.3.3 (Why just-maturing).**
The bond $p(\cdot,t)$ is the unique bond whose one-period return over $(t-1,t)$
is known at time $t-1$. Any other bond $p(\cdot,T)$ with $T > t$ has a random
return over $(t-1,t)$, since $p(t,T)$ is $\mathcal{F}_t$-measurable but not (in general)
$\mathcal{F}_{t-1}$-measurable. This is why the rolling strategy produces a
"riskless" accumulation process.

---

## 2.4 No-Arbitrage

**Definition 2.4.1 (Arbitrage).**
An *arbitrage* is a self-financing strategy $(\varphi, \psi)$ with

  (i)   $V_0 = 0$,
  (ii)  $V_N \geq 0$    $\mathbb{P}$-a.s.,
  (iii) $\mathbb{P}(V_N > 0) > 0$.

**Definition 2.4.2 (BBNA).**
The market satisfies *Bond-Based No-Arbitrage* (BBNA) if no arbitrage
exists among self-financing strategies in $\mathcal{S}$.

**Lemma 2.4.1 (Strategy space equivalence).**
The set of terminal payoffs attainable by self-financing strategies in
$\mathcal{S}$ coincides with the set of terminal payoffs attainable by self-financing
strategies in $\mathcal{S} \cup \{B\}$.

*Proof.*
Every strategy in $\mathcal{S}$ is trivially a strategy in $\mathcal{S} \cup \{B\}$ (set the
holding in $B$ to zero). Conversely, any strategy that holds $B$ can be
replicated by executing the rolling bond strategy of Proposition 2.3.1.
Since the rolling strategy is self-financing in the original assets $\mathcal{S}$,
the attainable payoff sets coincide.       $\quad\square$

**Corollary 2.4.2.**
BBNA is equivalent to classical NA in the market $\mathcal{S} \cup \{B\}$, where $B$ is
treated as a tradable asset.

This corollary is the key observation: *the bank account is not an
independent degree of freedom in a bond market.* It can be synthesized
from bonds, so including or excluding it from the strategy space makes
no difference.

---

## 2.5 Numeraire Invariance for Traded Numeraires

The following lemma is standard but is needed for the main theorem.
It is the special case of Wang (2008, Theorem 3.3.1) in which the
numeraire is tradable.

**Lemma 2.5.1 (Numeraire invariance, discrete time).**
Let $N$ be a tradable asset with $N(t) > 0$ $\mathbb{P}$-a.s. for all $t$, and let
$(\varphi, \psi)$ be a self-financing strategy in $\mathcal{S}$ (where $N \in \mathcal{S}$). Then:

$$(\text{a}) \quad V_t/N(t) = V_0/N(0) + \sum_{s=1}^t \sum_j \theta^j_s \cdot \Delta(S^j/N)_s,$$

where the sum is over all assets $S^j$ in $\mathcal{S}$, $\theta^j_s = \varphi^j_s$ (or $\psi^j_s$)
is the holding, and $\Delta(S^j/N)_s := S^j(s)/N(s) - S^j(s-1)/N(s-1)$.

$$(\text{b}) \quad \text{In particular, if } Q \sim \mathbb{P} \text{ is such that } S^j(t)/N(t) \text{ is a}
Q\text{-martingale for all } j, \text{ and } (\varphi, \psi) \text{ is self-financing with } V_0 = 0,
\text{ then } V_t/N(t) \text{ is a } Q\text{-martingale with } V_0/N(0) = 0.$$

*Proof.*
(a) The self-financing condition has two equivalent readings:

  $$V_t = V_{t-1} + \sum_j \theta^j_t (S^j_t - S^j_{t-1})        \quad (\star)$$

and, equivalently:

  $$V_t = \sum_j \theta^j_t S^j_t \quad \text{and} \quad V_{t-1} = \sum_j \theta^j_t S^j_{t-1}.  \quad (\star\star)$$

The second equation in $(\star\star)$ is the *costless rebalancing* condition:
the value of the new portfolio $(\theta_t)$, evaluated at the old prices
(time $t-1$), equals the old portfolio value. This holds because
rebalancing does not inject or withdraw capital.

Using $(\star\star)$:

$$V_t/N(t) - V_{t-1}/N(t-1)
  = \sum_j \theta^j_t S^j_t/N(t) - \sum_j \theta^j_t S^j_{t-1}/N(t-1)
  = \sum_j \theta^j_t \cdot [S^j_t/N(t) - S^j_{t-1}/N(t-1)]
  = \sum_j \theta^j_t \cdot \Delta(S^j/N)_t.$$

(b) Each increment $\Delta(S^j/N)_s$ is a $Q$-martingale difference (since
$S^j/N$ is a $Q$-martingale and $\Delta(S^j/N)_s$ is $\mathcal{F}_s$-measurable with
$E^Q[\Delta(S^j/N)_s \mid \mathcal{F}_{s-1}] = 0$). Since $\theta^j_s$ is $\mathcal{F}_{s-1}$-measurable,
the sum $\sum_j \theta^j_s \Delta(S^j/N)_s$ is a $Q$-martingale difference. Therefore
$V_t/N(t)$ is a $Q$-martingale.        $\quad\square$

**Remark 2.5.1.**
The proof uses critically that $N$ is a traded asset: this ensures that
rebalancing into $(\theta_t)$ at prices $(S^j_{t-1})$ is costless, which gives
the identity $V_{t-1} = \sum_j \theta^j_t S^j_{t-1}$. Wang (2008, Theorem 3.3.1)
proves a more general version in which $N$ need not be tradable; the
proof then requires Itô's formula (product rule) and involves
quadratic covariation terms that vanish when $N$ is tradable.

---

## 2.6 The Main Theorem

**Theorem 2.6.1 (Bond-Based FTAP, Discrete Time).**
Under Assumption 2.1.1, the following are equivalent:

**(NA)** No arbitrage exists among self-financing strategies in S.

**(EMM)** There exists Q ~ P such that S(t)/B(t) is a Q-martingale
for every tradable asset S and all t = 0, ..., N.

**(Wang)** There exists Q ~ P such that for every tradable asset S
with S(t−1) > 0:

  E^Q[R_t^S | F_{t−1}] = R_t^{(rf)},    t = 1, ..., N,            (2.6)

where R_t^S := [S(t) − S(t−1)]/S(t−1) and R_t^{(rf)} is defined
by (2.5).

**(BF)** For each maturity T ∈ {1, ..., N}, there exists Q^T ~ P
such that S(t)/p(t,T) is a Q^T-martingale for every tradable asset S
and all t = 0, ..., T.

Moreover, if any (hence all) of these conditions hold, the measures
{Q^T}_{T=1,...,N} satisfy the consistency relation

  dQ^{T₁}/dQ^{T₂}|_{F_{T₁}} = p(0,T₂) / [p(0,T₁) · p(T₁,T₂)]   (2.7)

for all 1 ≤ T₁ < T₂ ≤ N.

---

**Proof of Theorem 2.6.1.**

The proof proceeds via (NA) ⟺ (EMM) ⟹ (Wang) ⟹ (EMM) and
(EMM) ⟹ (BF) ⟹ (NA).

---

**(NA) $\iff$ (EMM).**

By Proposition 2.3.1, $B$ is the value process of a self-financing strategy
in $\mathcal{S}$ with $B(t) > 0$ for all $t$. By Lemma 2.4.1, the set of attainable
terminal payoffs is unchanged by including $B$ as a tradable asset.

With $B$ available as a strictly positive tradable numéraire, the classical
discrete-time FTAP of Harrison and Pliska (1981) --- or its
finite-probability-space version, or the general finite-dimensional
version of Dalang, Morton, and Willinger (1990) --- gives:

  $$\text{NA} \iff \exists Q \sim \mathbb{P} \text{ such that } S/B \text{ is a } Q\text{-martingale for all } S \in \mathcal{S}.$$

The mathematical content of this equivalence is entirely Harrison-Pliska.
Our contribution is the observation that $B$ is constructible from the
bond market (Proposition 2.3.1), making the classical theorem applicable
without assuming $B$ as a model primitive.                               $\quad\square$

---

**(EMM) $\Rightarrow$ (Wang).**

Let $Q$ be as in (EMM). For any tradable asset $S$ with $S(t-1) > 0$:

  $$E^Q[S(t)/B(t) \mid \mathcal{F}_{t-1}] = S(t-1)/B(t-1)$$

  $$\iff E^Q[S(t)/S(t-1) \mid \mathcal{F}_{t-1}] = B(t)/B(t-1)$$

  $$\iff E^Q[1 + R_t^S \mid \mathcal{F}_{t-1}] = 1/p(t-1,t) = 1 + R_t^{(\text{rf})}$$

  $$\iff E^Q[R_t^S \mid \mathcal{F}_{t-1}] = R_t^{(\text{rf})}.$$

All steps are multiplication or division by positive $\mathcal{F}_{t-1}$-measurable
quantities. The equivalence is algebraic.                              $\quad\square$

**(Wang) $\Rightarrow$ (EMM).**

The same chain of equivalences in reverse. Given $Q$ satisfying (Wang),
the final line reads $E^Q[S(t)/B(t) \mid \mathcal{F}_{t-1}] = S(t-1)/B(t-1)$,
which is the $Q$-martingale property of $S/B$.                             $\quad\square$

**Remark 2.6.1.**
The equivalence $(\text{EMM}) \iff (\text{Wang})$ is the content of Wang (2008,
Theorem 3.2.1). It is an algebraic reformulation of the martingale
condition, not a separate theorem. Its value is interpretive: (Wang)
states that expected returns equal the riskless return --- the return on
the just-maturing bond --- which is the quantity directly observed by
fixed-income traders. For background on risk-neutral pricing and the EMM
framework, see Bingham and Kiesel (2004).

---

**(EMM) $\Rightarrow$ (BF).**

Let $Q$ be as in (EMM). For each $T \in \{1,\ldots,N\}$, the process

  $$Z^T_t := p(t,T) / [B(t) \cdot p(0,T)],   t = 0, \ldots, T,             \quad (2.8)$$

is a strictly positive $Q$-martingale with $Z^T_0 = 1$ (since $p(\cdot,T)/B$
is a $Q$-martingale by (EMM), and dividing by the constant $p(0,T)$
preserves the martingale property).

Define $Q^T$ on $\mathcal{F}_T$ by

  $$\frac{d Q^T}{d Q} \bigg|_{\mathcal{F}_t} = Z^T_t,   t = 0, \ldots, T.                       \quad (2.9)$$

Since $Z^T_t > 0$ and $E^Q[Z^T_T] = Z^T_0 = 1$, $Q^T$ is a well-defined
probability measure equivalent to $Q$ (hence to $\mathbb{P}$) on $\mathcal{F}_T$.

For any tradable asset $S$ and $0 \le s \le t \le T$, by abstract Bayes' formula:

  $$E^{Q^T}[S(t)/p(t,T) \mid \mathcal{F}_s]
    = E^Q[Z^T_t \cdot S(t)/p(t,T) \mid \mathcal{F}_s] / Z^T_s$$
    $$= E^Q[S(t)/(B(t)\cdot p(0,T)) \mid \mathcal{F}_s] / [p(s,T)/(B(s)\cdot p(0,T))]$$
    $$= E^Q[S(t)/B(t) \mid \mathcal{F}_s] \cdot B(s)/p(s,T)$$
    $$= [S(s)/B(s)] \cdot B(s)/p(s,T)$$
    $$= S(s)/p(s,T).$$

Therefore $S/p(\cdot,T)$ is a $Q^T$-martingale.                               $\quad\square$

---

**(BF) $\Rightarrow$ (NA).**

Suppose, for contradiction, that an arbitrage $(\varphi, \psi)$ exists:
$V_0 = 0$, $V_N \ge 0$ $\mathbb{P}$-a.s., $\mathbb{P}(V_N > 0) > 0$.

By (BF) with $T = N$, there exists $Q^N \sim \mathbb{P}$ such that $S(t)/p(t,N)$ is
a $Q^N$-martingale for every traded asset $S$.

Since $p(\cdot,N)$ is itself a traded asset with $p(t,N) > 0$ for all $t \le N$,
Lemma 2.5.1(b) applies: $V_t/p(t,N)$ is a $Q^N$-martingale.

In particular:

  $$V_0/p(0,N) = E^{Q^N}[V_N/p(N,N)] = E^{Q^N}[V_N].$$

Since $V_0 = 0$, we obtain $E^{Q^N}[V_N] = 0$. Combined with $V_N \ge 0$
$\mathbb{P}$-a.s. (hence $Q^N$-a.s., since $Q^N \sim \mathbb{P}$), this yields $V_N = 0$  $Q^N$-a.s.,
hence $\mathbb{P}$-a.s. This contradicts $\mathbb{P}(V_N > 0) > 0$.                        $\quad\square$

---

**Consistency (2.7).**

Assuming (EMM) holds with measure $Q$, the density process $Z^T$ is defined
by (2.8). For $T_1 < T_2$:

  $$\frac{d Q^{T_1}}{d Q^{T_2}} \bigg|_{\mathcal{F}_{T_1}} = Z^{T_1}_{T_1} / Z^{T_2}_{T_1}$$
    $$= [p(T_1,T_1)/(B(T_1)\cdot p(0,T_1))] / [p(T_1,T_2)/(B(T_1)\cdot p(0,T_2))]$$
    $$= [1\cdot p(0,T_2)] / [p(0,T_1)\cdot p(T_1,T_2)]$$
    $$= p(0,T_2) / [p(0,T_1)\cdot p(T_1,T_2)].$$

Note that $B(T_1)$ cancels. The consistency relation (2.7) involves only
bond prices --- no reference to $B$ is required.                          $\quad\square$

**Remark 2.6.2 (Consistency is automatic in discrete time).**
The consistency relation (2.7) was derived as a *consequence* of (EMM).
In the other direction, (BF) alone forces consistency without any
additional assumption: under $Q^{T_2}$, the process $p(t,T_1)/p(t,T_2)$
is a martingale (by the Bond-Family condition applied to $S = p(\cdot,T_1)$).
Since $p(T_1,T_1) = 1$, this martingale evaluates at time $T_1$ to $1/p(T_1,T_2)$,
which determines the Radon-Nikodym derivative $d Q^{T_1}/d Q^{T_2}|_{\mathcal{F}_{T_1}}$
uniquely as a function of bond prices. The consistency is not an
additional condition --- it is implied.

**Remark 2.6.3 (Why automaticity may fail in continuous time).**
The mechanism behind Remark 2.6.2 deserves scrutiny, because it
reveals precisely where the continuous-time difficulty lies.

In discrete time, the argument is: under $Q^{T_2}$, the bond price ratio
$p(t,T_1)/p(t,T_2)$ is a martingale (by (BF) applied to $S = p(\cdot,T_1)$
with numéraire $p(\cdot,T_2)$). This martingale terminates at time $T_1$ with
the value $p(T_1,T_1)/p(T_1,T_2) = 1/p(T_1,T_2)$, and this terminal value
determines the Radon-Nikodym derivative $d Q^{T_1}/d Q^{T_2}|_{\mathcal{F}_{T_1}}$.
The consistency relation is not imposed --- it is *read off* from the
martingale property of a bond price ratio.

With finitely many maturities, the chain rule

  $$\frac{d Q^{T_1}}{d Q^{T_3}} = \left(\frac{d Q^{T_1}}{d Q^{T_2}}\right) \cdot \left(\frac{d Q^{T_2}}{d Q^{T_3}}\right)    \quad (2.10)$$

for $T_1 < T_2 < T_3$ is a finite number of conditions, each following
from the above construction. In continuous time, with $T_1, T_2, T_3$
ranging over $[0,T^*]$, this becomes an uncountable family of conditions
that must hold simultaneously.

To see why this is non-trivial, consider the limit $T_2 \downarrow T_1$. The
Radon-Nikodym derivative $d Q^{T_1}/d Q^{T_2}|_{\mathcal{F}_{T_1}}$ equals

  $$p(0,T_2) / [p(0,T_1) \cdot p(T_1,T_2)].$$

As $T_2 \to T_1$, both $p(0,T_2) \to p(0,T_1)$ and $p(T_1,T_2) \to p(T_1,T_1) = 1$,
so the derivative approaches $1$ --- nearby forward measures are close, as
expected. But the *rate of approach* is governed by

  $$1 - \frac{d Q^{T_1}}{d Q^{T_2}} \approx \frac{p(0,T_1)\cdot p(T_1,T_2) - p(0,T_2)}{p(0,T_1)\cdot p(T_1,T_2)}$$

and in the infinitesimal limit ($T_2 = T_1 + dT$), the leading-order term
involves the derivative $\partial p(T_1,T)/\partial T|_{T=T_1}$, which is related to the
forward rate $f(T_1,T_1) = r(T_1)$ --- the short rate.

This is the *diagonal singularity* discussed in Section 3.3: the
infinitesimal chaining of forward measures requires evaluating the
forward rate surface $f(t,T)$ on the diagonal $T = t$. If this diagonal
restriction is singular --- if $r(t) = f(t,t)$ is not well-defined or not
integrable --- then the infinitesimal chain rule breaks down, the
projective limit of the family $\{Q^T\}$ may not exist, and the global
measure $Q$ cannot be assembled from the local pieces.

In short: in discrete time, the chain (2.10) is a *finite* product of
well-defined factors. In continuous time, it becomes an *infinite*
product whose convergence depends on the regularity of the forward
rate surface at the diagonal. The automatic consistency of the
discrete-time case is a consequence of finitude, not of structure.

---

## 2.7 Where This Breaks in Continuous Time

The proof of Theorem 2.6.1 relies on three ingredients:

(I) The rolling bond strategy is a well-defined self-financing portfolio
    (Proposition 2.3.1).

(II) B(t) > 0 for all t, so B serves as a valid numéraire.

(III) The Harrison-Pliska theorem applies to the finite-dimensional
     discrete-time market with B as numéraire.

In continuous time, **(I) fails.** Constructing B(t) = exp(∫₀ᵗ r(s)ds)
requires:

  — Trading at every instant t ∈ [0,T*].
  — At each instant, selling the just-maturing bond and purchasing the
    next — an operation involving uncountably many bonds.
  — The short rate r(t) = f(t,t) to be well-defined, which requires
    evaluating the forward rate surface on the diagonal (see Section 3.3).

The rolling strategy is not a stochastic integral with respect to
finitely many semimartingales. Whether it constitutes a self-financing
portfolio in any rigorous sense is itself a non-trivial question (cf.
Björk et al. 1997, Döberlein and Schweizer 2001).

**Consequence.** The implication chain

  (NA) ⟹ [B is a tradable s.f. portfolio] ⟹ [FTAP applies] ⟹ (EMM)

breaks at the first arrow. Without the rolling strategy, we cannot
invoke the classical FTAP.

**This motivates the Bond-Family formulation.** Each condition (BF)_T
requires only the single bond p(·,T) as numéraire — a genuinely
tradable asset. The full Bond-Family condition is well-defined in
continuous time without assuming B exists. The question becomes:

  *Does the consistency of the family {Q^T}_{T ∈ [0,T*]} force the
  existence of a single measure Q and a process B such that
  B-normalized prices are Q-martingales?*

In discrete time, we proved this affirmatively (Theorem 2.6.1).
In continuous time, it is an open problem (Section 3).

---

## 2.8 Relationship to Herdegen (2017)

We briefly compare our approach to the numéraire-independent FTAP of
Herdegen (2017, Mathematical Finance 27(2), 568–603).

Herdegen works in a general market (not specific to bonds) and defines
no-arbitrage via *share maximality*: the zero strategy is maximal if no
self-financing strategy dominates it in the sense that its terminal
value, measured in shares of every asset, is at least as large a.s. and
strictly larger with positive probability.

In our bond market with strictly positive prices, this simplifies:

(a) The share comparison V^ψ_N/S^i_N ≥ V^φ_N/S^i_N reduces to
    V^ψ_N ≥ V^φ_N (multiply by S^i_N > 0).

(b) Maximality of the zero strategy becomes: no zero-cost strategy
    produces V_N ≥ 0 a.s. with P(V_N > 0) > 0.

Therefore, in our setting:

  NA^{ni} (Herdegen) = classical NA = BBNA.

The three notions coincide in a discrete-time bond market with strictly
positive prices.

**What our approach adds.** In discrete time, the mathematical
equivalence is unsurprising. Our approach contributes:

1. *Explicit identification of the deflator.* Herdegen's theorem
   guarantees existence of a strictly positive supermartingale deflator.
   We identify it concretely as 1/B, the reciprocal of the rolling
   bond strategy.

2. *The Wang reformulation.* Condition (Wang) expresses the EMM
   property as "expected return = riskless return" — financially
   transparent for fixed-income practitioners.

3. *The Bond-Family formulation.* Condition (BF) is equivalent to the
   others in discrete time, but it is the *only* formulation that
   extends cleanly to continuous time: each $\text{(BF)}_T$ involves a single
   tradable numéraire, with no reference to $B$.

**In continuous time,** the relationship to Herdegen changes structurally.
His $\text{NA}^{\text{ni}}$ remains well-defined (it does not require $B$), but it
ignores the maturity structure of bonds. Our Bond-Family condition
exploits $p(T,T) = 1$ and the inter-maturity consistency of the $Q^T$
family --- features that Herdegen's general framework neither uses nor
can access.

---

## 2.9 Summary

We collect the results of this section.

*Established results:*

- The bank account $B$ is constructible as a self-financing rolling bond
  strategy (Proposition 2.3.1). In discrete time, $B$ is tradable.

- BBNA is equivalent to classical NA, to the EMM condition with
  numéraire $B$, to the Wang expected-return condition, and to the
  Bond-Family condition (Theorem 2.6.1).

- The consistency of the forward measure family $\{Q^T\}$ is automatic
  in discrete time (Remark 2.6.2).

- The Herdegen (2017) share-maximality condition coincides with BBNA
  in bond markets with strictly positive prices (Section 2.8).

*The discrete-time section is foundational, not the main contribution.*
Its purpose is to establish the Bond-Family formulation and the
equivalences that become non-trivial when the rolling strategy
breaks down in continuous time.
