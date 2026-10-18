"""Pin all inputs and the checked Sage runtime for the first arithmetic run."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
panel_p = json.loads((here / "panel_protocol.json").read_text())
assert not (here / "run_protocol.json").exists()
paths = [here / name for name in ("run_sage.py", "panel.json", "panel_protocol.json",
                                   "sage_runtime_info.json")]
paths += [Path(panel_p[key]) for key in ("states", "fixture", "w_table", "witness")]
record = {"wall_cap_seconds": 180,
          "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths},
          **{key: panel_p[key] for key in ("states", "fixture", "w_table")}}
(here / "run_protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
