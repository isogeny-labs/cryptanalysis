import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sources = [HERE / name for name in
           ("audit_sage.py", "run_audit.py", "result.json", "run_result.json",
            "protocol.json", "sage_runtime_info.json")]
sources += [HERE.parent / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"]
protocol = {"status": "FROZEN", "kind": "n41_w8_quadratic_partial_independent_sage_audit",
            "case_indexes": [0, 1, 2, 4, 68, 70],
            "worker_count": 1, "wall_cap_seconds": 120,
            "rss_cap_bytes": 4294967296,
            "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in sources}}
with (HERE / "audit_protocol.json").open("x") as stream:
    json.dump(protocol, stream, indent=2, sort_keys=True)
    stream.write("\n")
