.PHONY: all clean

all: xedni_lift_optimizer_20261101.pdf

pipeline.svg: pipeline.dot
	dot -Tsvg $< -o $@

pipeline.png: pipeline.dot
	dot -Tpng -Gdpi=180 $< -o $@

nine_point_control.svg: nine_point_control.dot
	dot -Tsvg $< -o $@

nine_point_control.png: nine_point_control.dot
	dot -Tpng -Gdpi=180 $< -o $@

xedni_lift_optimizer_20261101.pdf: README.md pipeline.png nine_point_control.png
	pandoc README.md --from=markdown --pdf-engine=xelatex \
		--variable=mainfont:'DejaVu Sans' \
		--variable=monofont:'DejaVu Sans Mono' \
		--variable=geometry:margin=0.72in --variable=fontsize:9pt \
		--variable=colorlinks:true --variable=urlcolor:blue --output=$@

clean:
	rm -f pipeline.svg pipeline.png nine_point_control.svg nine_point_control.png xedni_lift_optimizer_20261101.pdf

