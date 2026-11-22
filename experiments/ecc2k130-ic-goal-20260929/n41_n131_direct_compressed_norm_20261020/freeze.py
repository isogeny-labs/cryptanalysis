"""Freeze source-bound protocols before either checked Sage run."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent
prior = root / "n41_n131_symbolic_affine_block_norm_20261019"
common = [here/"run_sage.py", here/"sage_runtime_info.json"]
configs = {
    "n41": {
        "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
        "coefficients": root/"n41_w9_two_product_eliminant_20261017/result.json",
        "reference": prior/"compress_result.json",
        "variable_code_bit_indices": [2, 0, 1, 3],
        "tested_widths": [4],
        "sampled_prefixes_by_width": {"4": list(range(16))},
        "wall_cap_seconds": 120,
    },
    "n131": {
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "coefficients": root/"n131_w33_freecode_resultant_20261018/coefficients.json",
        "reference": prior/"n131_transfer_result.json",
        "variable_code_bit_indices": [0, 1, 2, 3, 4, 5],
        "tested_widths": [4, 5, 6],
        "sampled_prefixes_by_width": {"4": [0, 1], "5": [0, 1], "6": [0, 1]},
        "wall_cap_seconds": 300,
    },
}
for mode, cfg in configs.items():
    paths = common+[cfg["coefficients"], cfg["reference"]]
    protocol = {
        "status": f"FROZEN_BEFORE_{mode.upper()}_DIRECT_COMPRESSED_RECURRENCE",
        "candidate_id": None,
        "curve_id": cfg["curve_id"],
        "coefficients": str(cfg["coefficients"]),
        "reference": str(cfg["reference"]),
        "variable_code_bit_indices": cfg["variable_code_bit_indices"],
        "tested_widths": cfg["tested_widths"],
        "sampled_prefixes_by_width": cfg["sampled_prefixes_by_width"],
        "wall_cap_seconds": cfg["wall_cap_seconds"],
        "worker_count": 1,
        "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
        "test": "Direct compressed quadratic norm recurrence, exact explicit-block equality, full right-subspace modular GCD, frozen positive and comparison blocks",
    }
    out = here/f"{mode}_protocol.json"
    assert not out.exists()
    out.write_text(json.dumps(protocol, sort_keys=True, indent=2)+"\n")
    print(mode, hashlib.sha256(out.read_bytes()).hexdigest())
