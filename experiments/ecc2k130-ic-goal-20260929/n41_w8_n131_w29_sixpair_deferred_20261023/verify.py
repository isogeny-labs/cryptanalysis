"""Replay immutable-source and result receipts for the two N41 controls."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
read = lambda name: json.loads((HERE / name).read_text())

for stem in ("build", "query", "relaxed_build", "relaxed_query"):
    protocol = read(f"{stem}_protocol.json")
    result = read(f"{stem}_result.json")
    assert result["protocol_sha256"] == sha(HERE / f"{stem}_protocol.json")
    for name, item in protocol["sources"].items():
        assert sha(item["path"]) == item["sha256"], (stem, name)
    assert result["candidate_id"] is None
    assert result["curve_id"] == "EC1N41Ckb1h7d5e80d3c4d0"

for build, formula in (("build", "n41_public_deferred.xcnf"),
                       ("relaxed_build", "n41_public_all_deferred.xcnf")):
    result = read(f"{build}_result.json")
    assert result["formula_sha256"] == sha(HERE / formula)
    assert result["formula_bytes"] == (HERE / formula).stat().st_size
    counts = result["counts"]
    assert result["positive_assignment_check"] == {
        "clauses": counts["clauses"],
        "native_xor_rows": counts["native_xor_rows"],
    }
    assert result["constructed_codes"] == [121, 100, 93, 2, 108, 28]

point = [344545435656, 924092594889]
assert read("build_result.json")["target_point"] == point
for name in ("query_result.json", "relaxed_build_result.json",
             "relaxed_query_result.json"):
    assert read(name)["public_point"] == point

for stem, cap in (("query", 180), ("relaxed_query", 120)):
    result = read(f"{stem}_result.json")
    protocol = read(f"{stem}_protocol.json")
    assert protocol["worker_count"] == 1
    assert protocol["parent_wall_cap_seconds"] == cap
    assert protocol["rss_cap_bytes"] == 4294967296
    assert result["status"] == "BOUNDED_UNKNOWN"
    assert result["stop_reason"] == "WALL_CAP"
    assert not any(result[f"solver_terminal_{x}"] for x in
                   ("sat", "unsat", "indeterminate"))
    assert result["solver_stdout_sha256"] == sha(HERE / f"{stem}.stdout")
    assert result["solver_stderr_sha256"] == sha(HERE / f"{stem}.stderr")

print("PASS_TWO_FROZEN_N41_CONTROLS")
