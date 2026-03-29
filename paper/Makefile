CONDA_RUN = conda run -n bondna
PANDOC    = $(CONDA_RUN) pandoc
SRC       = paper.md
OUT       = bond_family_na.pdf

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

.PHONY: pdf clean

pdf: $(OUT)

$(OUT): $(SRC)
	$(PANDOC) $(PANDOC_FLAGS) -o $@ $<

clean:
	rm -f $(OUT)
