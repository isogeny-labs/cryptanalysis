"""Freeze the all-code-pair leading-coefficient census."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
base = json.loads((here / "panel_protocol.json").read_text())
paths = [here / name for name in ("leading_census_sage.py", "panel_protocol.json",
                                   "symbolic_result.json", "sage_runtime_info.json")]
paths += [Path(base[key]) for key in ("states", "w_table")]
assert not (here / "leading_protocol.json").exists()
record = {"wall_cap_seconds":60,
          "sources": {str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths},
          **{key:base[key] for key in ("states", "w_table")}}
(here / "leading_protocol.json").write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
