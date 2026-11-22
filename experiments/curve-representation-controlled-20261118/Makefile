.PHONY: test syntax

test: syntax
	python3 -m unittest -v test_systems.py

syntax:
	python3 -c "import ast,pathlib; [ast.parse(p.read_text(), filename=str(p)) for p in pathlib.Path('.').glob('*.py')]"
