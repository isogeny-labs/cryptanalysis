"""Rendering only; frozen prospective sources and identities."""
from pathlib import Path
import subprocess
import typst
p=Path(__file__).resolve().parent
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
