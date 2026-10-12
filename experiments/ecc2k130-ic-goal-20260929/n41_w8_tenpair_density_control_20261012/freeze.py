"""Freeze the unpinned ten-pair public-point N41 control before execution."""

import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INPUT = ROOT / "n41_w8_sixpair_mitm_20261011/join_input.tsv"
PARENT = ROOT / "n41_w8_ninepair_join_control_20261012"
assert not (HERE / "protocol.json").exists()
assert json.loads((PARENT / "audit_result.json").read_text())["status"].startswith("PASS")
paths = {
    "source": HERE / "join10.cpp",
    "included_group_source": PARENT / "join9.cpp",
    "binary": HERE / "join10",
    "runner": HERE / "run.py",
    "input": INPUT,
    "ninepair_public_point_audit": PARENT / "audit_result.json",
}
protocol = {
    "status": "FROZEN_UNPINNED_N41_TENPAIR_PUBLIC_POINT_CONTROL",
    "candidate_id": None,
    "field": "GF(2)[t]/(t^41+t^3+1)",
    "curve": "y^2+xy=x^3+1",
    "target_law": "four_raw_preimages_of_one_frozen_public_point",
    "source_law": "ten_free_signed_W8_pairs_slots_0_1_2_3_4_5_0_1_2_3",
    "left_slots": [0, 1, 2, 3, 4],
    "right_slots": [5, 0, 1, 2, 3],
    "left_kept_cap": 5000000,
    "right_kept_cap": 5000000,
    "random_generator": "xorshift64star_seed_4d595df4d0f33173",
    "worker_count": 1,
    "total_wall_cap_seconds": 180,
    "combined_rss_cap_bytes": 4 * 1024**3,
    "compiler": subprocess.check_output(["clang++", "--version"], text=True).splitlines()[0],
    "sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
               for name, path in paths.items()},
}
(HERE / "protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
print(protocol["status"])
