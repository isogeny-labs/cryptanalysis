"""Independent XOR-convolution replay of every W18 seed-bucket count."""
import hashlib
import json
import struct
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
COUNTS = GOAL / "n131_w16_w18_offset_gate_20261011/signed_w18.i64le"
SUPPORT = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def walsh(values):
    step = 1
    size = len(values)
    while step < size:
        for base in range(0, size, step * 2):
            for i in range(base, base + step):
                a, b = values[i], values[i + step]
                values[i], values[i + step] = a + b, a - b
        step *= 2


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert all(sha(path) == value for path, value in protocol["sources"].items())
    result = json.loads((HERE / "result.json").read_text())
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    start = time.monotonic_ns()
    indicator = [0] * 262144
    columns = defaultdict(list)
    for line in SUPPORT.read_text().splitlines():
        mask, column = map(int, line.split())
        assert 0 < mask < 262144 and indicator[mask] == 0
        indicator[mask] = 1
        columns[column].append(mask)
    assert sum(indicator) == 131307 and len(columns) == 131068
    walsh(indicator)
    indicator = [v * v for v in indicator]
    walsh(indicator)
    assert all(v % 262144 == 0 for v in indicator)
    same_column_ordered = [0] * 262144
    same_column_ordered[0] = 131307
    for masks in columns.values():
        for i, a in enumerate(masks):
            for b in masks[i + 1:]:
                same_column_ordered[a ^ b] += 2
    reconstructed = [2 * (v // 262144 - same_column_ordered[i])
                     for i, v in enumerate(indicator)]
    archived = struct.unpack("<262144q", COUNTS.read_bytes())
    assert tuple(reconstructed) == archived
    best = max(range(1, len(reconstructed)), key=lambda i: (reconstructed[i], -i))
    assert best == result["best_seed"]
    assert reconstructed[best] == result["maximum_signed_states_per_seed"]
    assert sum(reconstructed) == result["total_signed_pair_states_per_slot"]
    c = reconstructed[best]
    r = int(result["subgroup_order"])
    q = result["half_coverage_minimum_fixed_seed_tuples"]
    assert (q - 1) * (2 * c**4) < r <= q * (2 * c**4)
    out = {"status": "PASS_INDEPENDENT_FULL_W18_SEED_COUNT_REPLAY",
           "checked_seed_counts": len(reconstructed), "source_masks": 131307,
           "folded_columns": len(columns), "best_seed": best,
           "maximum_signed_states_per_seed": c,
           "wall_ns": time.monotonic_ns() - start,
           "result_sha256": sha(HERE / "result.json"),
           "protocol_sha256": sha(HERE / "protocol.json")}
    with (HERE / "audit.json").open("x") as stream:
        json.dump(out, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(out["status"], out["checked_seed_counts"], out["wall_ns"] / 1e9)


if __name__ == "__main__":
    main()
