from pathlib import Path
import typst,hashlib,json
r=Path("/workspace/cryptanalysis");p=r/"experiments/chained-transfer-public-target/reports/paired-fourth-result-01";typst.compile(str(p/"report.typ"),output=str(p/"report.pdf"),root=str(p));print("PDF bytes",(p/"report.pdf").stat().st_size)
(p/"render-inputs.json").write_text(json.dumps({f.name:{"bytes":f.stat().st_size,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()}for f in [p/"report.typ",p/"report.pdf"]},indent=2)+"\n")
