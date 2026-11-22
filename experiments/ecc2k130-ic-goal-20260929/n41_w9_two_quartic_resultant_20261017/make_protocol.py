"""Freeze source hashes before drawing the two-quartic control panel."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent
paths = {
    "freeze": here / "freeze.py",
    "states": root / "n41_n131_w29_rotation_alignment_20261017/aligned_states.json",
    "fixture": root / "n41_w9_implicit_fivepair_tower_20261017/fixture.json",
    "controls": root / "n41_w9_joint_residual_20261017/controls.json",
    "witness": root / "n41_w9_code_linear_tower_20261017/witness.json",
    "w_table": root / "n41_w9_target_w_bdd_20261017/w_table.json",
}
assert not (here / "panel_protocol.json").exists()
record = {
    "seed": 41019,
    "negative_count": 32,
    "source_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                      for name, path in paths.items()},
    "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths.values()},
    **{name: str(paths[name]) for name in ("states", "fixture", "controls", "witness", "w_table")},
}
(here / "panel_protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
