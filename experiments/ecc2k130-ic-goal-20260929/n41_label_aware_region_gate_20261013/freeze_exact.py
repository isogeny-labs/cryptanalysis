"""Freeze exact comparison against the already frozen symbolic SAT pair."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sources = [HERE / name for name in ("build.py", "build_result.json", "exact_join.py",
                                     "run_exact.py",
                                     "protocol.json", "run_result.json")]
sources += [HERE.parent / "n41_joint_product_span_relaxation_20261013" / "RESULT.md"]
protocol = {"status": "FROZEN", "kind": "n41_exact_label_region_comparator",
            "worker_count": 1, "wall_cap_seconds": 120,
            "rss_cap_bytes": 4294967296,
            "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in sources}}
with (HERE / "exact_protocol.json").open("x") as stream:
    json.dump(protocol, stream, indent=2, sort_keys=True)
    stream.write("\n")
