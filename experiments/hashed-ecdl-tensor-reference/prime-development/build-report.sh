#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
dot -Tsvg pipeline.dot -o pipeline.svg
dot -Tpdf pipeline.dot -o pipeline.pdf
pdflatex -interaction=nonstopmode -halt-on-error report.tex > build.log
pdflatex -interaction=nonstopmode -halt-on-error report.tex >> build.log
gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -dPDFSETTINGS=/screen \
  -dEmbedAllFonts=true -dSubsetFonts=true \
  -sOutputFile=.report-compact.pdf report.pdf
mv -- .report-compact.pdf report.pdf
