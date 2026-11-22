"""Select cubic-feature mismatch bits on 32 rectangles, then inspect 100 holdouts."""
import hashlib
import json
import resource
import struct
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "selection_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for name, item in CFG["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
assert CFG["status"] == "FROZEN_N41_CUBIC_BIT_SELECTION"
assert not (HERE / "selection_result.json").exists()
started = time.monotonic()
sys.path.insert(0, str(Path(CFG["sources"]["feature_source"]["path"]).parent))
from cubic_screen import FULL, WIDTH, feature  # noqa: E402
from reciprocal_cubic import inverse  # noqa: E402

rectangles = json.loads(Path(CFG["sources"]["rectangle_protocol"]["path"]).read_text())["rectangles"]
cases = [json.loads(line) for line in Path(CFG["sources"]["coordinate_audit"]["path"]).open()]
target_x = struct.unpack("<65Q", Path(CFG["sources"]["target_residuals"]["path"]).read_bytes())[0]
target_bits = feature(inverse(target_x))
assert WIDTH == 10661 and len(rectangles) == 132
training = rectangles[:CFG["train_rectangles"]]
holdout = rectangles[CFG["train_rectangles"]:]
assert len(holdout) == CFG["holdout_rectangles"]


def wrong_bits(rectangle):
    zero = one = FULL
    for index in rectangle["case_indices"]:
        for z in cases[index]["reciprocal_coordinates"]:
            lifted = feature(z)
            zero &= FULL ^ lifted
            one &= lifted
    return (zero & target_bits) | (one & (FULL ^ target_bits))


train_wrong = [wrong_bits(row) for row in training]
remaining = set(i for i, bits in enumerate(train_wrong) if bits)
order = []
training_coverage = []
for _ in range(CFG["max_bits"]):
    if not remaining:
        break
    counts = [sum((train_wrong[i] >> bit) & 1 for i in remaining)
              for bit in range(WIDTH)]
    best = max(range(WIDTH), key=lambda bit: (counts[bit], -bit))
    if counts[best] == 0:
        break
    order.append(best)
    covered = {i for i in remaining if train_wrong[i] >> best & 1}
    training_coverage.append(len(covered))
    remaining -= covered

# The bit order is fixed before any holdout root coordinates are accessed.
holdout_wrong = [wrong_bits(row) for row in holdout]
assert time.monotonic() - started < CFG["wall_cap_seconds"]
assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < CFG["rss_cap_bytes"]
selected_mask = sum(1 << bit for bit in order)
result = {"status": "PASS_N41_DISJOINT_CUBIC_BIT_SELECTION",
          "candidate_id": None, "feature_width": WIDTH,
          "training_rectangles": len(training),
          "holdout_rectangles": len(holdout),
          "bit_order": order,
          "training_newly_covered": training_coverage,
          "training_full_feature_rejected": sum(bool(bits) for bits in train_wrong),
          "training_selected_rejected": sum(bool(bits & selected_mask) for bits in train_wrong),
          "holdout_full_feature_rejected": sum(bool(bits) for bits in holdout_wrong),
          "holdout_selected_rejected": sum(bool(bits & selected_mask) for bits in holdout_wrong),
          "holdout_witness_present": any(966 in row["case_indices"] for row in holdout),
          "holdout_witness_selected_rejected": any(
              966 in row["case_indices"] and bool(bits & selected_mask)
              for row, bits in zip(holdout, holdout_wrong)),
          "wall_seconds": time.monotonic() - started,
          "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256": sha(HERE / "selection_protocol.json")}
assert result["holdout_witness_present"] is True
assert result["holdout_witness_selected_rejected"] is False
(HERE / "selection_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({key: result[key] for key in (
    "bit_order", "training_full_feature_rejected", "holdout_full_feature_rejected",
    "holdout_selected_rejected", "wall_seconds")}, sort_keys=True))
