.PHONY: all clean

all: xedni_cross_field_20261101.pdf

xedni_domains.svg: xedni_domains.dot
	dot -Tsvg $< -o $@

xedni_domains.png: xedni_domains.svg
	python3 -m cairosvg $< --scale 1.5 --output $@

degree_bounds.svg: degree_bounds.dot degree_bounds.csv
	dot -Tsvg degree_bounds.dot -o $@

degree_bounds.png: degree_bounds.svg
	python3 -m cairosvg $< --scale 1.5 --output $@

xedni_cross_field_20261101.pdf: README.md xedni_domains.png degree_bounds.png
	pandoc README.md --from=markdown --pdf-engine=xelatex \
		--variable=mainfont:'Noto Sans CJK JP' \
		--variable=monofont:'Noto Sans Mono CJK JP' \
		--variable=geometry:margin=0.75in --variable=fontsize:10pt \
		--variable=colorlinks:true --variable=urlcolor:blue --output=$@

clean:
	rm -f xedni_domains.svg xedni_domains.png degree_bounds.svg degree_bounds.png \
		xedni_cross_field_20261101.pdf
