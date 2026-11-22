"""Freeze monitored checked-Sage execution of the resultant circuit builder."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
path = HERE / "build_run_protocol.json"
assert not path.exists()
build = json.loads((HERE / "build_protocol.json").read_text())
assert build["status"] == "FROZEN_BEFORE_N41_QUADRATIC_RESULTANT_BUILD"
sources = {"script": HERE / "build_resultant.py",
           "supervisor": HERE / "supervise_build.py",
           "freeze_script": Path(__file__),
           "builder_protocol": HERE / "build_protocol.json",
           "runtime": HERE / "sage_runtime_info.json",
           "prior_failure": HERE / "build_attempt1.json"}
cfg = {"status": "FROZEN_BEFORE_N41_RESULTANT_CIRCUIT_RUN",
       "curve_id": build["curve_id"], "candidate_id": None,
       "sage_launcher": "/Volumes/SSD990/cryptanalysis/sage",
       "worker_count": 1, "wall_cap_seconds": 330,
       "rss_cap_bytes": 4294967296,
       "sources": {name: {"path": str(source), "sha256": sha(source)}
                   for name, source in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(path)}, sort_keys=True))
