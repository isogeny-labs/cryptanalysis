"""Check frozen inputs, generated rows, and independent quadratic-rank replay."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for protocol_name in ("five_protocol.json", "extended_protocol.json",
                      "extended_rank_protocol.json", "audit_protocol.json"):
    for name, source in read(protocol_name)["sources"].items():
        assert digest(source["path"]) == source["sha256"], (protocol_name, name)

source = read("extended_result.json")
rank = read("extended_rank_result.json")
audit = read("audit_result.json")
five = read("five_result.json")
assert source["status"] == "PASS_N131_W23_EXTENDED_TRIPLE_X"
assert rank["status"] == "PASS_N131_EXTENDED_QUADRATIC_RANK"
assert audit["status"] == "PASS_INDEPENDENT_N131_QUADRATIC_RANK_AUDIT"
assert five["status"] == "PASS_TRIPLE_X_QUADRATIC_FIVE"
assert all(record["candidate_id"] is None for record in (source, rank, audit, five))
assert source["first_five_replayed"] is True
assert source["family_count"] == rank["source_families"] == audit["families_checked"] == 280
assert rank["feature_width"] == 8646
assert rank["first_full_rank_prefix"] == audit["first_full_rank_prefix"] == 271
assert rank["last_rank"] == audit["last_rank"] == 8646
assert audit["target_checks"] == 840
assert source["sets_sha256"] == digest(HERE / "extended_sets.jsonl")
assert rank["rows_sha256"] == digest(HERE / "extended_rank_rows.jsonl")

sets = [json.loads(line) for line in (HERE / "extended_sets.jsonl").open()]
rows = [json.loads(line) for line in (HERE / "extended_rank_rows.jsonl").open()]
assert len(sets) == len(rows) == 280
all_x = set()
for index, (source_set, row) in enumerate(zip(sets, rows), 1):
    xs = source_set["x"]
    assert len(xs) == len(set(xs)) == 32, index
    assert all(0 <= x < 2**131 for x in xs), index
    all_x.update(xs)
    assert row["family_count"] == index
    assert row["last_masks"] == source_set["masks"]
    assert row["distinct_x"] == len(all_x) == 32 * index
    assert row["quadratic_codimension"] == 8646 - row["quadratic_rank"]
    assert row["quadratic_rank"] <= min(8646, 32 * index - 1)
    assert row["target_checks"]["constructed"]["exact_x_member"] is True
    assert row["target_checks"]["constructed"]["quadratic_hull_contains"] is True
    if index <= 270:
        assert row["target_checks"]["public"]["quadratic_hull_contains"] is False
        assert row["target_checks"]["panel_public"]["quadratic_hull_contains"] is False
    else:
        assert row["quadratic_rank"] == 8646
        assert row["target_checks"]["public"]["quadratic_hull_contains"] is True
        assert row["target_checks"]["panel_public"]["quadratic_hull_contains"] is True
    assert row["target_checks"]["public"]["exact_x_member"] is False
    assert row["target_checks"]["panel_public"]["exact_x_member"] is False

assert rows[269]["quadratic_rank"] == 8639
assert rows[270]["quadratic_rank"] == 8646
assert rows[-1]["quadratic_rank"] == 8646
print("PASS_FROZEN_N131_QUADRATIC_CAPACITY_RECORD")
