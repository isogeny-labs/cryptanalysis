"""Freeze two-family Macaulay inputs before the N41 panel run."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = HERE / "protocol.json"
assert not path.exists()
sources = {
    "script": HERE / "run.py",
    "freeze": Path(__file__),
    "macaulay_field": ROOT / "n41_n131_macaulay_family_gate_20261019/macaulay.py",
    "resultant_input": ROOT / "n41_w11_freecode_resultant_20261018/resultant_input.tsv",
    "complete_census": ROOT / "n41_w11_freecode_resultant_20261018/census_result.json",
}
cfg = {"status": "FROZEN_BEFORE_N41_JOINT_MACAULAY",
       "candidate_id": None, "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
       "target_indexes": [0, 1], "positive_codes": [253, 63],
       "expansion_check_codes": [[253,63], [0,0], [511,255], [1023,1023], [42,19]],
       "degrees": [4, 5, 6], "wall_cap_seconds": 120,
       "rss_cap_bytes": 4294967296,
       "sources": {name: {"path": str(source), "sha256": sha(source)}
                   for name, source in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(path)}, sort_keys=True))
