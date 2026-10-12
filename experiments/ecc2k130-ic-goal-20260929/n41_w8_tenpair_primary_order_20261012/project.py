"""Exact one-hot source-size gate for transfer of the N41 selector encoding."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_w18_bucketed_public_20261012/projection_result.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


data = json.loads(SOURCE.read_text())
states = data["full_signed_pair_states_per_slot"]
slots = 10
bits = states * slots
bytes_min = (bits + 7) // 8
result = {
    "status": "FAIL_N131_LITERAL_ONEHOT_MEMORY_GATE",
    "candidate_id": None,
    "source_states_per_slot": states,
    "ten_independent_slots": slots,
    "selector_variables_min": bits,
    "one_bit_each_bytes_min": bytes_min,
    "rss_cap_bytes": 4 * 1024**3,
    "memory_ratio_decimal": f"{bytes_min / (4 * 1024**3):.9f}",
    "scope": "literal independent one-hot pair-state selectors only; compact Boolean source encodings are outside this gate",
    "source_path": str(SOURCE),
    "source_sha256": sha(SOURCE),
    "producer_sha256": sha(__file__),
}
assert bits == 344827929120 and bytes_min == 43103491140
assert bytes_min > result["rss_cap_bytes"]
with (HERE / "projection_result.json").open("x") as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write("\n")
