#!/usr/bin/env python3
"""
fix_tex.py — post-process pandoc-generated paper.tex for arXiv submission.

Usage:
    python fix_tex.py <input.tex> <output.tex>

Applies:
    1. natbib package insertion
    2. Unicode character fixes (sigma, geq outside math mode)
    3. All inline citation → \\cite{} replacements
    4. Corrupted includegraphics fix
    5. References section → \\bibliographystyle + \\bibliography
"""

import re
import sys


# ---------------------------------------------------------------------------
# Citation replacement table
# Order matters: compound/multi-author groups before their sub-parts.
# Each entry: (exact string in pandoc output, LaTeX replacement)
# ---------------------------------------------------------------------------
CITATIONS = [
    # --- Multi-author parenthetical groups (must come before sub-patterns) ---
    (
        "(Filipović and Trolle\n2013, Crépey et al.~2015, Grbac and Runggaldier 2015)",
        r"\citep{FilipovicTrolle2013,Crepey2015,GrbacRunggaldier2015}",
    ),
    (
        "(Filipović and Trolle 2013, Crépey et al.~2015, Grbac and Runggaldier 2015)",
        r"\citep{FilipovicTrolle2013,Crepey2015,GrbacRunggaldier2015}",
    ),
    (
        "(Cuchiero, Klein, and Teichmann 2016; De Donno 2004; Takaoka and\nSchweizer 2014)",
        r"\citep{CuchieroKleinTeichmann2016,DeDonno2004,TakokaSchweizer2014}",
    ),
    (
        "(Cuchiero, Klein, and Teichmann 2016; De Donno 2004; Takaoka and Schweizer 2014)",
        r"\citep{CuchieroKleinTeichmann2016,DeDonno2004,TakokaSchweizer2014}",
    ),
    (
        "(Duffee 2002, Joslin, Singleton, and Zhu 2011)",
        r"\citep{Duffee2002,JoslinSingletonZhu2011}",
    ),
    (
        "(Davis and Hobson 2007,\nAcciaio et al.~2013)",
        r"\citep{DavisHobson2007,Acciaio2013}",
    ),
    (
        "(Davis and Hobson 2007, Acciaio et al.~2013)",
        r"\citep{DavisHobson2007,Acciaio2013}",
    ),
    (
        "Duffee 2002, Joslin,\nSingleton, and Zhu 2011",
        r"\citealt{Duffee2002,JoslinSingletonZhu2011}",
    ),
    (
        "Duffee 2002, Joslin, Singleton, and Zhu 2011",
        r"\citealt{Duffee2002,JoslinSingletonZhu2011}",
    ),

    # --- Inline with explicit year in parens: \citet ---
    ("Black and Scholes (1973)", r"\citet{BlackScholes1973}"),
    ("Merton (1973)",            r"\citet{Merton1973}"),
    ("Harrison and Kreps\n(1979)", r"\citet{HarrisonKreps1979}"),
    ("Harrison and Kreps (1979)", r"\citet{HarrisonKreps1979}"),
    ("Musiela and Rutkowski (1997)", r"\citet{MusielaRutkowski1997}"),
    ("Döberlein, Schweizer, and Stricker\n(2000)", r"\citet{DoberleinSchweizerStricker2000}"),
    ("Döberlein, Schweizer, and Stricker (2000)", r"\citet{DoberleinSchweizerStricker2000}"),
    ("Klein, Schmidt, and Teichmann (2016)", r"\citet{KleinSchmidtTeichmann2016}"),
    ("Herdegen (2017)", r"\citet{Herdegen2017}"),
    ("Cuchiero, Klein, and Teichmann (2016)", r"\citet{CuchieroKleinTeichmann2016}"),
    ("De Donno (2004)", r"\citet{DeDonno2004}"),
    ("Takaoka and Schweizer (2014)", r"\citet{TakokaSchweizer2014}"),
    ("Carmona and Tehranchi\n(2006)", r"\citet{CarmonaTehranchi2006}"),
    ("Carmona and Tehranchi (2006)", r"\citet{CarmonaTehranchi2006}"),
    ("Filipović (2001, 2009)", r"\citet{Filipovic2001,Filipovic2009}"),
    ("Filipović (2001)",       r"\citet{Filipovic2001}"),
    ("Filipović (2009)",       r"\citet{Filipovic2009}"),
    ("Henrard (2007)", r"\citet{Henrard2007}"),
    ("Morini (2009)",  r"\citet{Morini2009}"),
    ("Samuelson (1938)", r"\citet{Samuelson1938}"),
    ("Hobson\n(1998)", r"\citet{Hobson1998}"),
    ("Hobson (1998)",  r"\citet{Hobson1998}"),
    ("Balbás, Ibáñez, and López (2002)", r"\citet{BalbasIbanezLopez2002}"),
    ("Harrison-Pliska (1981)", r"\citet{HarrisonPliska1981}"),
    ("Gatheral, Jaisson, and Rosenbaum (2018)", r"\citet{GatheralJaissonRosenbaum2018}"),
    ("Vayanos and\nVila (2021)", r"\citet{VayanosVila2021}"),
    ("Vayanos and Vila (2021)", r"\citet{VayanosVila2021}"),

    # --- In-flow without year parens: \citealt ---
    ("cf.~Björk et al.~1997, Döberlein\nand Schweizer 2001",
     r"cf.~\citealt{Bjork1997}, \citealt{DoberleinSchweizer2001}"),
    ("cf.~Björk et al.~1997, Döberlein and Schweizer 2001",
     r"cf.~\citealt{Bjork1997}, \citealt{DoberleinSchweizer2001}"),
    ("cf.~Balbás et al. 2002 for\nthe general framework; Filipović 2001, 2009",
     r"cf.~\citealt{BalbasIbanezLopez2002} for the general framework; \citealt{Filipovic2001,Filipovic2009}"),
    ("cf.~Balbás et al. 2002 for the general framework; Filipović 2001, 2009",
     r"cf.~\citealt{BalbasIbanezLopez2002} for the general framework; \citealt{Filipovic2001,Filipovic2009}"),
    ("such as Balbás et\nal.~2002)", r"such as \citealt{BalbasIbanezLopez2002})"),
    ("such as Balbás et al.~2002)", r"such as \citealt{BalbasIbanezLopez2002})"),
    ("Balbás et al.~(2002)", r"\citealt{BalbasIbanezLopez2002}"),
    ("Balbás et al.~2002",   r"\citealt{BalbasIbanezLopez2002}"),
    ("Harrison-Pliska for", r"\citeauthor{HarrisonPliska1981} for"),
    ("Geman-El Karoui-Rochet 1995", r"\citealt{GemanElKarouiRochet1995}"),
    ("Harrison and Pliska 1981", r"\citealt{HarrisonPliska1981}"),
    ("(Geman, El Karoui, and Rochet 1995)", r"(\citealt{GemanElKarouiRochet1995})"),
    ("Heath, Jarrow, and Morton 1992", r"\citealt{HeathJarrowMorton1992}"),
    ("Pagan 1984", r"\citealt{Pagan1984}"),
    ("Litterman and Scheinkman 1991", r"\citealt{LittermanScheinkman1991}"),
    ("Filipović and Trolle\n2013", r"\citealt{FilipovicTrolle2013}"),
    ("Filipović and Trolle 2013",   r"\citealt{FilipovicTrolle2013}"),
    ("Crépey et al.~2015",  r"\citealt{Crepey2015}"),
    ("Grbac and Runggaldier 2015", r"\citealt{GrbacRunggaldier2015}"),
    ("Davis and Hobson 2007", r"\citealt{DavisHobson2007}"),
    ("Acciaio et al.~2013",   r"\citealt{Acciaio2013}"),
    ("Duffee 2002",  r"\citealt{Duffee2002}"),

    # --- Possessive / as-noun forms ---
    ("Klein-Schmidt-Teichmann's", r"\citeauthor{KleinSchmidtTeichmann2016}'s"),
    ("Klein-Schmidt-Teichmann,",  r"\citeauthor{KleinSchmidtTeichmann2016},"),
    ("Klein-Schmidt-Teichmann ",  r"\citeauthor{KleinSchmidtTeichmann2016} "),
    ("Herdegen's", r"\citeauthor{Herdegen2017}'s"),
    ("Filipović's", r"\citeauthor{Filipovic2001}'s"),

    # --- Remaining inline year forms ---
    ("(Herdegen 2017, Proposition 3.5)", r"(\citealt{Herdegen2017}, Proposition~3.5)"),
    ("Herdegen 2017, Proposition 3.5",   r"\citealt{Herdegen2017}, Proposition~3.5"),

    # --- Parenthetical see Bingham ---
    ("(for a\ncomprehensive treatment, see Bingham and Kiesel 2004)",
     r"\citep{BinghamKiesel2004}"),
    ("(for a comprehensive treatment, see Bingham and Kiesel 2004)",
     r"\citep{BinghamKiesel2004}"),
]

# ---------------------------------------------------------------------------
# Unicode fixes: characters used outside math mode
# ---------------------------------------------------------------------------
UNICODE_FIXES = [
    (r"\emph{nested sub-σ-algebras}",  r"\emph{nested sub-$\sigma$-algebras}"),
    (r"\emph{same} σ-algebra",          r"\emph{same} $\sigma$-algebra"),
    (r"(≥ 15Y)",                        r"($\geq$ 15Y)"),
    (r"(5Y vs ≥ 20Y)",                  r"(5Y vs $\geq$ 20Y)"),
]

# ---------------------------------------------------------------------------
# Corrupted includegraphics fix (artifact of pandoc re-run)
# ---------------------------------------------------------------------------
FIGURE_FIX = (
    r"\pandocbounded{\includegraphics[keepaspepandoc paper_revised.md -o paper.tex "
    r"--standalonectratio,alt={Market Price of Risk Gaps Over Time "
    r"(5Y vs 30Y)}]{./figures/test1_lambda_gap_timeseries.png}}",
    r"\pandocbounded{\includegraphics[keepaspectratio,alt={Market Price of Risk Gaps "
    r"Over Time (5Y vs 30Y)}]{./figures/test1_lambda_gap_timeseries.png}}",
)


def fix_tex(src: str) -> str:
    # 1. Add natbib after \usepackage{bookmark}
    src = src.replace(
        r"\usepackage{bookmark}",
        r"\usepackage{bookmark}" + "\n" + r"\usepackage[authoryear,round]{natbib}",
        1,
    )

    # 2. Unicode fixes
    for old, new in UNICODE_FIXES:
        src = src.replace(old, new)

    # 3. Corrupted figure line fix
    src = src.replace(FIGURE_FIX[0], FIGURE_FIX[1])

    # 4. Citation replacements
    for old, new in CITATIONS:
        src = src.replace(old, new)

    # 5. Replace inline References section with \bibliography
    # Matches \section{References}...\end{document} (including trailing newline)
    src = re.sub(
        r"\\section\{References\}.*?\\end\{document\}",
        "\n\\\\bibliographystyle{plainnat}\n\\\\bibliography{paper}\n\n\\\\end{document}\n",
        src,
        flags=re.DOTALL,
    )

    return src


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.tex> <output.tex>", file=sys.stderr)
        sys.exit(1)

    infile, outfile = sys.argv[1], sys.argv[2]
    with open(infile, encoding="utf-8") as f:
        src = f.read()

    result = fix_tex(src)

    with open(outfile, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"Written: {outfile}")


if __name__ == "__main__":
    main()
