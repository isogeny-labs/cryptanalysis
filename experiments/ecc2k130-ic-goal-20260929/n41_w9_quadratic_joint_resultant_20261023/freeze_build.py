"""Freeze the right-sum-free Boolean circuit against the archived source."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n41_w9_joint_right_s3_20261023"
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
path = HERE / "build_protocol.json"
assert not path.exists()
prior = json.loads((PRIOR / "compact_build_protocol.json").read_text())
assert prior["status"] == "FROZEN_BEFORE_COMPACT_JOINT_RIGHT_S3_BUILD"
for source, digest in prior["sources"].items():
    assert sha(source) == digest
preflight = json.loads((HERE / "preflight_result.json").read_text())
assert preflight["status"] == "PASS_N41_QUADRATIC_RESULTANT_PREFLIGHT"
sources = dict(prior["sources"])
for source in (HERE / "build_resultant.py", HERE / "freeze_build.py",
               HERE / "preflight_result.json", HERE / "protocol.json",
               PRIOR / "compact_build_protocol.json", PRIOR / "compact_build_result.json"):
    sources[str(source)] = sha(source)
cfg = {"status": "FROZEN_BEFORE_N41_QUADRATIC_RESULTANT_BUILD",
       "candidate_id": None, "curve_id": prior["curve_id"],
       "states": prior["states"], "fixture": prior["fixture"],
       "panel": prior["panel"], "join_rows": prior["join_rows"],
       "preflight_result": str(HERE / "preflight_result.json"),
       "method": "eliminate right-sum reciprocal with the characteristic-two two-quadratic resultant",
       "wall_cap_seconds": 300, "memory_envelope_bytes": 4294967296,
       "sources": sources}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(path)}, sort_keys=True))
