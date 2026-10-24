"""Freeze N41 first, then promote the checked block-norm method to N131."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CASE = sys.argv[1]
assert CASE in ("n41", "n131")
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
path = HERE / f"protocol_{CASE}.json"
assert not path.exists()
runtime = HERE / "sage_runtime_info.json"
assert runtime.exists()
sources = {"script": HERE / "blocknorm_sage.py", "supervisor": HERE / "supervise.py",
           "freeze_script": Path(__file__), "runtime": runtime}
if CASE == "n41":
    sources["n41_input"] = ROOT / "n41_w11_freecode_resultant_20261018/resultant_input.tsv"
    codes = list(range(240, 256))
    curve_id = "EC1N41Ckb1h7d5e80d3c4d0"
    cap = 120
else:
    prior = json.loads((HERE / "n41_result.json").read_text())
    assert prior["status"] == "PASS_N41_BLOCK_NORM_GATE"
    supervisor = json.loads((HERE / "n41_supervisor.json").read_text())
    assert supervisor["status"] == "PASS_N41_BLOCK_NORM_GATE"
    sources.update({
        "n41_result": HERE / "n41_result.json",
        "n41_supervisor": HERE / "n41_supervisor.json",
        "n131_coefficients": ROOT / "n131_w33_freecode_resultant_20261018/coefficients.json",
        "n131_reference": ROOT / "resultant_nonzero_branch_20261019/w33_gcd_result.json",
    })
    codes = list(range(16))
    curve_id = "EC1N131Ckb1heb5f1998f20b"
    cap = 590
cfg = {"status": f"FROZEN_BEFORE_{CASE.upper()}_BLOCK_NORM",
       "case": CASE, "candidate_id": None, "curve_id": curve_id,
       "first_codes": codes, "target_indexes": [0, 1],
       "sage_launcher": "/Volumes/SSD990/cryptanalysis/sage",
       "worker_count": 1, "wall_cap_seconds": cap,
       "rss_cap_bytes": 4294967296,
       "sources": {name: {"path": str(source), "sha256": sha(source)}
                   for name, source in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(path)}, sort_keys=True))
