import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sources = [HERE / name for name in ("audit_info_sage.py", "info_cases.jsonl",
                                     "info_protocol.json", "info_run_result.json",
                                     "sage_runtime_info.json")]
protocol = {"status": "FROZEN", "kind": "n41_informative_row_kernel_sage_audit",
            "audited_case_indices": [0, 1, 2, 10], "wall_cap_seconds": 120,
            "rss_cap_bytes": 4294967296,
            "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in sources}}
with (HERE / "audit_info_protocol.json").open("x") as stream:
    json.dump(protocol, stream, indent=2, sort_keys=True)
    stream.write("\n")
