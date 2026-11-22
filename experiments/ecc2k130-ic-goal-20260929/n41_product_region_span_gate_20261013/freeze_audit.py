import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sources = [HERE / name for name in ("audit.py", "result.json", "run_result.json",
                                     "protocol.json")]
protocol = {"status": "FROZEN", "kind": "n41_complete_product_region_rank_replay",
            "wall_cap_seconds": 120, "rss_cap_bytes": 4294967296,
            "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in sources}}
with (HERE / "audit_protocol.json").open("x") as stream:
    json.dump(protocol, stream, indent=2, sort_keys=True)
    stream.write("\n")
