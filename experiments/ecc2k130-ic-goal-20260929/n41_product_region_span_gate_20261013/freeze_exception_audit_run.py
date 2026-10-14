import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sources = [HERE / name for name in ("audit_exception_sage.py",
                                     "exception_audit_protocol.json",
                                     "run_exception_audit.py", "sage_runtime_info.json")]
protocol = {"status": "FROZEN", "kind": "n41_four_family_exception_sage_replay",
            "wall_cap_seconds": 120, "rss_cap_bytes": 4294967296,
            "worker_count": 1,
            "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in sources}}
with (HERE / "exception_audit_run_protocol.json").open("x") as stream:
    json.dump(protocol, stream, indent=2, sort_keys=True)
    stream.write("\n")
