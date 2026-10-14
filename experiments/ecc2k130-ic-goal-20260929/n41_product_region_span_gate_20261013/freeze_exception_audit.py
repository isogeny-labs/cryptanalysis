import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sources = [HERE / name for name in ("audit_exception_sage.py",
                                     "exception_result.json", "exception_run_result.json",
                                     "exception_protocol.json", "audit_result.json",
                                     "sage_runtime_info.json")]
protocol = {"status": "FROZEN", "kind": "n41_four_family_exception_independent_sage_audit",
            "wall_cap_seconds": 120, "rss_cap_bytes": 4294967296,
            "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in sources}}
with (HERE / "exception_audit_protocol.json").open("x") as stream:
    json.dump(protocol, stream, indent=2, sort_keys=True)
    stream.write("\n")
