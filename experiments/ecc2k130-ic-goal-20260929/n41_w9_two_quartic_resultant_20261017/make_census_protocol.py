"""Freeze all-code-pair sparsity census inputs."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
base = json.loads((here / "panel_protocol.json").read_text())
paths = [here / name for name in ("census_sage.py", "panel_protocol.json",
                                   "symbolic_result.json", "sage_runtime_info.json")]
paths += [Path(base[key]) for key in ("states", "w_table")]
assert not (here / "census_protocol.json").exists()
record = {"wall_cap_seconds":120,
          "sources": {str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths},
          **{key:base[key] for key in ("states", "w_table")}}
(here / "census_protocol.json").write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
