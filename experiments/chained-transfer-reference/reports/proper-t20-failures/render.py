"""Render recorded attempt history; no research computation."""
from pathlib import Path
import subprocess
import typst
p=Path(__file__).resolve().parent
subprocess.run(["dot","-Tsvg",str(p/"flow.dot"),"-o",str(p/"flow.svg")],check=True)
f=p/"flow.svg";f.write_text("\n".join(x.rstrip() for x in f.read_text().splitlines()).rstrip()+"\n")
typst.compile(str(p/"report.typ"),output=str(p/"report.pdf"))
