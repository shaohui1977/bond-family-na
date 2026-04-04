CONDA_RUN = conda run --no-capture-output -n bondna
PANDOC    = $(CONDA_RUN) pandoc
TECTONIC  = $(CONDA_RUN) tectonic
PYTHON    = $(CONDA_RUN) python
SRC       = paper.md
OUT       = bond_family_na.pdf
ARXIV_OUT = paper.pdf
RAW_TEX   = paper_raw.tex
FIXED_TEX = paper.tex

PANDOC_FLAGS = \
	--pdf-engine=tectonic \
	--include-in-header=pandoc-header.tex \
	--variable geometry:margin=1in \
	--variable fontsize=11pt \
	--variable linestretch=1.15 \
	--variable colorlinks=true \
	--variable linkcolor=blue \
	--variable urlcolor=blue \
	--number-sections \
	--standalone

.PHONY: pdf arxiv clean

pdf:
	$(PANDOC) $(PANDOC_FLAGS) -o $(OUT) $(SRC)

# arXiv build: paper.md → paper_raw.tex (pandoc) → paper.tex (fix_tex.py) → paper.pdf (tectonic)
# Rebuilds whenever paper.md or fix_tex.py changes.
arxiv: $(SRC) fix_tex.py paper.bib
	@echo "--- Step 1: pandoc paper.md → paper_raw.tex"
	$(PANDOC) --standalone -o $(RAW_TEX) $(SRC)
	@echo "--- Step 2: apply arXiv fixes → paper.tex"
	$(PYTHON) fix_tex.py $(RAW_TEX) $(FIXED_TEX)
	@echo "--- Step 3: tectonic paper.tex → paper.pdf"
	$(TECTONIC) $(FIXED_TEX)

clean:
	rm -f $(OUT) $(ARXIV_OUT) $(RAW_TEX)
