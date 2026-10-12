"""Independent score replay with the known constant coordinate removed."""

import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "verification_protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_NEAR_CHARACTER_VERIFICATION"
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
vectors = json.loads((HERE / "vectors.json").read_text())
producer = json.loads((HERE / "result.json").read_text())
assert producer["vectors_sha256"] == hashlib.sha256((HERE / "vectors.json").read_bytes()).hexdigest()
assert {k: len(v) for k, v in vectors.items()} == {"train": 4096, "holdout": 8192, "uniform": 8192}


def signed(rows, coord, mask):
    return sum(1 if (row[coord] & mask).bit_count() % 2 == 0 else -1 for row in rows)


output = {"status": "PASS_INDEPENDENT_NEAR_CHARACTER_SCORE_AUDIT", "candidate_id": None,
          "total_vectors": sum(map(len, vectors.values())), "coordinates": {}}
for coord, name in ((2, "x"), (3, "inverse_x")):
    assert all((row[coord] & 1) == 0 for rows in vectors.values() for row in rows)
    all_masks = [1 << i for i in range(1, 41)]
    all_masks += [(1 << i) | (1 << j) for i in range(1, 41) for j in range(i + 1, 41)]
    assert len(all_masks) == 820
    original = {row["mask"]: row["signed_count"]
                for row in producer["selection"][name]["train_signed_counts"]}
    scored = [(mask, signed(vectors["train"], coord, mask)) for mask in all_masks]
    assert all(original[mask] == value for mask, value in scored)
    scored.sort(key=lambda pair: (-abs(pair[1]), pair[0]))
    top = []
    for mask, train_count in scored[:10]:
        top.append({"mask": mask, "train_signed_count": train_count,
                    "holdout_signed_count": signed(vectors["holdout"], coord, mask),
                    "uniform_signed_count": signed(vectors["uniform"], coord, mask)})
    output["coordinates"][name] = {
        "constant_bit_zero": 0, "nonconstant_masks": len(all_masks), "top_ten": top,
        "max_abs_holdout_top_ten": max(abs(row["holdout_signed_count"]) for row in top) / 8192,
        "top_one_holdout_95pct_normal_halfwidth": 1.96 / math.sqrt(8192),
        "top_one_source_minus_uniform_95pct_normal_halfwidth": 1.96 * math.sqrt(2 / 8192)}
    print(name, top[0], flush=True)

with (HERE / "analysis.json").open("x") as stream:
    json.dump(output, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(output["status"], flush=True)
