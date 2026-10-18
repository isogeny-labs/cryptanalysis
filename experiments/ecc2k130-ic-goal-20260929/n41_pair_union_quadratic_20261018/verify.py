"""Recheck frozen N41 quadratic ranks, source hashes and native census."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


lock = json.loads((HERE / "artifact_lock.json").read_text())
for name, digest in lock["local_sha256"].items():
    assert sha(HERE / name) == digest, name


sample_protocol = json.loads((HERE / "protocol.json").read_text())
full_protocol = json.loads((HERE / "full_protocol.json").read_text())
for relative, digest in sample_protocol["sources_sha256"].items():
    assert sha(ROOT / relative) == digest, relative
assert sha(HERE / "probe_sage.py") == sample_protocol["probe_sha256"]
assert sha(HERE / "sage_runtime_info.json") == sample_protocol["sage_runtime_sha256"]
for relative, digest in full_protocol["repo_sha256"].items():
    assert sha(ROOT / relative) == digest, relative
for local, digest in full_protocol["local_sha256"].items():
    assert sha(HERE / local) == digest, local

sample = json.loads((HERE / "result.json").read_text())
full = json.loads((HERE / "full_result.json").read_text())
assert sample["status"] == "COMPLETE_N41_QUADRATIC_PAIR_UNION_PANEL"
assert sample["protocol_sha256"] == sha(HERE / "protocol.json")
assert full["status"] == "COMPLETE_N41_QUADRATIC_PAIR_CENSUS"
assert full["protocol_sha256"] == sha(HERE / "full_protocol.json")
assert full["exit_code"] == 0 and full["stop_reason"] is None
assert not full["monitor_degraded"]
assert full["wall_ns"] < 180 * 10**9
assert full["sampled_peak_combined_rss_bytes"] < 4 * 1024**3
assert sha(HERE / "full_stdout.txt") == full["stdout_sha256"]
assert sha(HERE / "full_stderr.txt") == full["stderr_sha256"]
assert (HERE / "full_stderr.txt").read_text() == ""

summary = full["summary"]
assert len(summary) == 1
tokens = summary[0].split()
assert tokens[:5] == ["SUMMARY", "1554", "0", "46", "58596"]
assert full["rank_rows"] == ["RANK 862 1554"]
rows = {}
for line in full["pair_rows"]:
    cols = line.split()
    assert cols[0] == "PAIR"
    key = (int(cols[1]), int(cols[2]))
    assert key not in rows
    rows[key] = cols[3:]
assert len(rows) == 1600
assert set(rows) == {(a, b) for a in range(40) for b in range(40)}
assert sum(value == ["EMPTY"] for value in rows.values()) == 46
assert sum(value != ["EMPTY"] for value in rows.values()) == 1554
assert sum(int(value[0]) for value in rows.values() if value != ["EMPTY"]) == 58596
assert all(value[1] == "862" for value in rows.values() if value != ["EMPTY"])


def feature(x):
    out = 1
    for i in range(41):
        if x & (1 << i):
            out |= 1 << (1+i)
    index = 42
    for i in range(41):
        for j in range(i+1, 41):
            if (x & (1 << i)) and (x & (1 << j)):
                out |= 1 << index
            index += 1
    assert index == 862
    return out


def rank(values):
    pivots = {}
    for value in values:
        while value:
            bit = value.bit_length()-1
            if bit not in pivots:
                pivots[bit] = value
                break
            value ^= pivots[bit]
    return len(pivots)


prior = json.loads((ROOT / "n41_w8_three_code_pair_union_20261015" /
                    "audit_result.json").read_text())
prior_pairs = {tuple(row["codes"]): row for row in prior["pairs_checked"]}
for item in sample["results"]:
    pair = tuple(item["codes"])
    assert pair in prior_pairs
    assert item["valid_third_codes"] == prior_pairs[pair]["valid_third_codes"]
    assert item["distinct_union_x"] == prior_pairs[pair]["distinct_union_x"]
    assert len(item["x_values"]) == len(set(item["x_values"]))
    assert rank(map(feature, item["x_values"])) == item["quadratic_rank"] == 862
    assert item["quadratic_nullity"] == 0
    native = rows[pair]
    assert native[:2] == [str(item["valid_third_codes"]), "862"]
    first_full = next(x[0] for x in item["rank_after_each_third_code"] if x[2] == 862)
    assert int(native[2]) == first_full

print(json.dumps({"status": "VERIFIED", "full_rank_pairs": 1554,
                  "empty_pairs": 46, "independent_sage_sample_pairs": 3}, sort_keys=True))
