"""Read-only replay of frozen global cross-span evidence."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rank(values):
    pivots = {}
    for value in values:
        while value:
            bit = value.bit_length() - 1
            if bit in pivots:
                value ^= pivots[bit]
            else:
                pivots[bit] = value
                break
    return len(pivots)


for name in ("protocol.json", "audit_protocol.json", "audit_run_protocol.json"):
    frozen = read(name)
    assert frozen["status"] == "FROZEN"
    for path, expected in frozen["sources"].items():
        assert sha(path) == expected, path

native = read("result.json")
run = read("run_result.json")
audit = read("audit_result.json")
audit_run = read("audit_run_result.json")
assert native["status"] == "PASS_COMPLETE_N41_GLOBAL_CROSS_SPAN"
assert native["product_families"] == 2048
assert native["coordinate_basis_vectors_examined"] == 12310
assert native["coordinate_union_rank"] == native["cross_span_rank"] == 40
assert native["trace_pairing_rank"] == 41
assert native["trace_failures"] == 0
assert rank([row[0] for row in native["union_basis"]]) == 40
assert rank([row[0] for row in native["cross_basis"]]) == 40
assert len(native["union_basis"]) == len(native["cross_basis"]) == 40
assert len({row[1] for row in native["union_basis"]}) == 9
assert all(row[1] in {entry[0] for entry in native["union_basis"]}
           and row[2] in {entry[0] for entry in native["union_basis"]}
           for row in native["cross_basis"])
assert run["status"] == "EXIT_0" and run["exit_code"] == 0
assert run["stop_reason"] is None and not run["monitor_degraded"]
assert run["wall_ns"] < 120_000_000_000
assert run["sampled_peak_combined_rss_bytes"] < 4 * 1024**3
assert run["protocol_sha256"] == sha(HERE / "protocol.json")
for name in ("result.json", "native.stdout", "native.stderr"):
    assert run["sha256"][name] == sha(HERE / name)
assert audit["status"] == "PASS_INDEPENDENT_N41_GLOBAL_CROSS_SPAN_REPLAY"
assert audit["witness_families_rebuilt"] == 9
assert audit["union_pivots_checked"] == audit["union_rank"] == 40
assert audit["cross_pivots_checked"] == audit["cross_rank"] == 40
assert audit["trace_pairing_rank"] == 41
assert audit["source_sha256"]["native_result"] == sha(HERE / "result.json")
assert audit["source_sha256"]["script"] == sha(HERE / "audit_sage.py")
assert audit_run["status"] == "EXIT_0" and audit_run["exit_code"] == 0
assert audit_run["stop_reason"] is None and not audit_run["monitor_degraded"]
assert audit_run["wall_ns"] < 120_000_000_000
assert audit_run["sampled_peak_combined_rss_bytes"] < 4 * 1024**3
assert audit_run["protocol_sha256"] == sha(HERE / "audit_run_protocol.json")
for name in ("audit_result.json", "audit.stdout", "audit.stderr"):
    assert audit_run["sha256"][name] == sha(HERE / name)

terminal = {
    "status": "PASS_N41_UNIVERSAL_CROSS_ANNIHILATOR_CENSUS",
    "candidate_id": None,
    "curve_id": "EC1N41Ckb1h023d9a38bbf7",
    "target_reciprocal": native["target_reciprocal"],
    "complete_product_families": native["product_families"],
    "coordinate_union_rank": 40,
    "cross_span_rank": 40,
    "field_dimension": 41,
    "universal_cross_annihilator_dimension": 1,
    "universal_cross_annihilator_basis": [1],
    "native_parent_wall_ns": run["wall_ns"],
    "audit_parent_wall_ns": audit_run["wall_ns"],
    "native_peak_sampled_combined_rss_bytes": run["sampled_peak_combined_rss_bytes"],
    "audit_peak_sampled_combined_rss_bytes": audit_run["sampled_peak_combined_rss_bytes"],
    "protocol_sha256": sha(HERE / "protocol.json"),
    "result_sha256": sha(HERE / "result.json"),
    "audit_result_sha256": sha(HERE / "audit_result.json"),
}
output = HERE / "terminal.json"
rendered = json.dumps(terminal, indent=2, sort_keys=True) + "\n"
if output.exists():
    assert output.read_text() == rendered
else:
    output.write_text(rendered)
print(terminal["status"], terminal["cross_span_rank"])
