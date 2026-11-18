.PHONY: check report

check:
	python3 check_archive.py

report: check
	mkdir -p .build
	cp original/report.tex original/coverage.pdf original/equations.pdf original/field-structure.pdf .build/
	cd .build && pdflatex -interaction=nonstopmode -halt-on-error report.tex > build-first.txt
	cd .build && pdflatex -interaction=nonstopmode -halt-on-error report.tex > build.txt
	! rg 'Overfull|LaTeX Warning:.*(undefined|multiply defined)' .build/report.log
	pdftotext .build/report.pdf .build/report.txt
