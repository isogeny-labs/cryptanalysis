# Document rendering only; no cryptanalytic experiment is run.
# Dependencies: Python with CairoSVG (rendering only), Pandoc and XeLaTeX.
.PHONY: all clean
all: report.pdf

orbit-compression.png: orbit-compression.svg
	python3 -m cairosvg $< --scale 1.5 --output $@

report.pdf: README.md orbit-compression.png
	pandoc README.md --from=markdown --pdf-engine=xelatex --variable=geometry:margin=0.75in --variable=fontsize:10pt --variable=colorlinks:true --variable=urlcolor:blue --output=$@

clean:
	rm -f orbit-compression.png report.pdf
