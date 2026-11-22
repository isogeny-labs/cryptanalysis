"""Freeze first-code block Macaulay widths and source snapshots."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = HERE / "block_protocol.json"
assert not path.exists()
sources = {
    "script": HERE / "run_blocks.py",
    "freeze": Path(__file__),
    "whole_protocol": HERE / "protocol.json",
    "whole_result": HERE / "result.json",
    "macaulay_field": ROOT / "n41_n131_macaulay_family_gate_20261019/macaulay.py",
    "resultant_input": ROOT / "n41_w11_freecode_resultant_20261018/resultant_input.tsv",
    "complete_census": ROOT / "n41_w11_freecode_resultant_20261018/census_result.json",
}
cfg = {"status": "FROZEN_BEFORE_N41_MACAULAY_BLOCK_PANEL",
       "candidate_id": None, "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
       "target_indexes": [0, 1], "positive_code": 253,
       "block_widths": [0, 1, 2, 3, 4], "degrees": [3, 4, 5, 6],
       "wall_cap_seconds": 120, "rss_cap_bytes": 4294967296,
       "sources": {name: {"path": str(source), "sha256": sha(source)}
                   for name, source in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(path)}, sort_keys=True))
