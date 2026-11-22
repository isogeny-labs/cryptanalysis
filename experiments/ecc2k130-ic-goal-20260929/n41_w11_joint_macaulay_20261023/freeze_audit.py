"""Freeze independent raw-code replay of the saved block certificates."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = HERE / "audit_protocol.json"
assert not path.exists()
sources = {
    "script": HERE / "audit_blocks.py",
    "freeze": Path(__file__),
    "block_protocol": HERE / "block_protocol.json",
    "block_result": HERE / "block_result.json",
    "macaulay_field": ROOT / "n41_n131_macaulay_family_gate_20261019/macaulay.py",
    "resultant_input": ROOT / "n41_w11_freecode_resultant_20261018/resultant_input.tsv",
}
cfg = {"status": "FROZEN_BEFORE_N41_BLOCK_CERTIFICATE_AUDIT",
       "candidate_id": None, "wall_cap_seconds": 120, "rss_cap_bytes": 4294967296,
       "sources": {name: {"path": str(source), "sha256": sha(source)}
                   for name, source in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(path)}, sort_keys=True))
