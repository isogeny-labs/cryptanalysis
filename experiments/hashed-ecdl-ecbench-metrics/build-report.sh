#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
dot -Tsvg pipeline.dot -o pipeline.svg
dot -Tpdf pipeline.dot -o pipeline.pdf
pdflatex -interaction=nonstopmode -halt-on-error report.tex >/dev/null
compact=$(mktemp)
trap 'rm -f -- "$compact"' EXIT
gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook \
  -dDetectDuplicateImages=true -dCompressFonts=true -sOutputFile="$compact" report.pdf
mv -- "$compact" report.pdf
rm -f report.aux report.log report.out
