"""Freeze symbolic polynomial inputs before the degree/sparsity run."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
base = json.loads((here / "panel_protocol.json").read_text())
paths = [here / name for name in ("symbolic_sage.py", "panel.json", "panel_protocol.json",
                                   "run_result.json", "sage_runtime_info.json")]
paths += [Path(base[key]) for key in ("states", "fixture", "w_table")]
assert not (here / "symbolic_protocol.json").exists()
record = {"wall_cap_seconds": 180,
          "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths},
          **{key: base[key] for key in ("states", "fixture", "w_table")}}
(here / "symbolic_protocol.json").write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
