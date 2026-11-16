from pathlib import Path
import typst
p=Path("/workspace/cryptanalysis/experiments/chained-transfer-public-target/reports/paired-fourth-edge-proposal-01");typst.compile(str(p/"report.typ"),output=str(p/"report.pdf"),root=str(p));print("PDF bytes",(p/"report.pdf").stat().st_size)
