"""Documentation renderer only; recognition and all algebraic checks are Rust."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "three-gluing-figures"
for suffix in ("svg", "pdf"):
    subprocess.run([
        "dot", f"-T{suffix}", str(FIG / "criterion.dot"),
        "-o", str(FIG / f"criterion.{suffix}"),
    ], check=True)
subprocess.run([
    "pandoc", str(ROOT / "THREE_GLUING.md"), "--from=markdown",
    "--pdf-engine=xelatex", "--resource-path=" + str(ROOT),
    "-o", str(ROOT / "THREE_GLUING.pdf"),
], cwd=ROOT, check=True)
