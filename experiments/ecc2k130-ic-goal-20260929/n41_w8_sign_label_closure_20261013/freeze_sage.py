"""Freeze complete checked-Sage reconstruction of all seven pair tables."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n41_w8_fixed_sum_table_20261009"
paths = [HERE / "audit_sage.py", HERE / "run_sage.py", HERE / "result.json",
         HERE / "sage_runtime_info.json", BASE / "geometry.json", BASE / "audit.py",
         BASE / "audit.json", ROOT / "n41_lowpower_w8_s6/basis8.json",
         ROOT / "n41_lowpower_w8_s6/native_input.txt"]
record = {
    "status": "FROZEN", "kind": "n41_w8_sevenpair_all_state_checked_sage_replay",
    "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
    "worker_count": 1, "wall_cap_seconds": 600, "rss_cap_bytes": 4 * 1024**3,
    "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
}
with (HERE / "sage_protocol.json").open("x") as stream:
    json.dump(record, stream, indent=2, sort_keys=True)
    stream.write("\n")
print("FROZEN_N41_SEVENPAIR_ALL_STATE_SAGE_REPLAY")
