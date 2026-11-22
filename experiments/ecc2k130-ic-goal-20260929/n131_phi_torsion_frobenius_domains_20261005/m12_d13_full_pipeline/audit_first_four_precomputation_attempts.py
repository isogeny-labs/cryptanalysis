"""Independently replay the four archived d13/m12 preparation-query receipts."""

import gzip
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "first_four_precomputation_attempts_20261115.jsonl"
LAUNCH = HERE / "local_launch_corrected_20261115.json"
PROTOCOL = HERE / "d13_m12_single_target_protocol_v1.json"
OUTPUT = HERE / "first_four_precomputation_audit_20261115.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    protocol = json.loads(PROTOCOL.read_text())
    launch = json.loads(LAUNCH.read_text())
    store = Path(launch["output_directory"]).resolve()
    run_dir = store / launch["run_id"]
    assert run_dir.is_dir() and launch["run_id"].startswith(protocol["candidate_id"] + "W")
    assert launch["run_id"].endswith("W" + protocol["workload_id"] + "R1")

    frozen_lines = SNAPSHOT.read_bytes().splitlines(keepends=True)
    live_lines = (run_dir / "precomputation_attempts.jsonl").read_bytes().splitlines(keepends=True)
    assert len(frozen_lines) == 4 and live_lines[:4] == frozen_lines
    rows = [json.loads(line) for line in frozen_lines]
    assert [row["relation_index"] for row in rows] == [1, 2, 3, 4]
    assert len({row["target_scalar"] for row in rows}) == 4

    audit_rows = []
    for row, line in zip(rows, frozen_lines):
        assert row["status"] == "timeout" and row["verified_relation_count"] == 0
        assert row["target_count"] == 1 and row["batch"] is False
        details = row["query_details"]
        assert details["formula_counts"] == {
            "vars": 232244, "clauses": 228629, "xors": 171278}
        assert details["target_scalar_known_to_solver"] is False
        assert details["rss_gate_passed"] is True
        assert details["conservative_combined_peak_rss_bytes"] <= 4 * 1024**3
        assert details["verified_relation_count"] == 0
        attempts = details["attempts"]
        assert len(attempts) == 1
        assert attempts[0]["solver_stop_reason"] == "parent_timeout"
        assert attempts[0]["solver_status"] == "indeterminate"
        assert attempts[0]["solver_exit_code"] == -15

        archived = []
        for artifact in row["archived_solver_artifacts"]:
            assert artifact["stored"] is True
            path = Path(artifact["path"])
            assert path.is_file() and path.resolve().is_relative_to(store)
            zipped = path.read_bytes()
            raw = gzip.decompress(zipped)
            assert sha(zipped) == artifact["compressed_sha256"]
            assert len(raw) == artifact["uncompressed_bytes"]
            assert sha(raw) == artifact["uncompressed_sha256"]
            archived.append(path.name)
            if path.name == "query.xcnf.gz":
                lines = raw.splitlines()
                assert lines[0] == b"p cnf 232244 399907"
                assert len(lines) == 399908
                assert sum(line.startswith(b"x") for line in lines[1:]) == 171278
                assert sha(raw) == details["target_formula_sha256"]
            if path.name == "cryptominisat.stdout.txt.gz":
                assert b"s SATISFIABLE" not in raw
                assert b"s UNSATISFIABLE" not in raw
        assert sorted(archived) == ["cryptominisat.stderr.txt.gz",
                                    "cryptominisat.stdout.txt.gz", "query.xcnf.gz"]
        audit_rows.append({
            "relation_index": row["relation_index"],
            "status": row["status"],
            "verified_relations": row["verified_relation_count"],
            "charged_query_wall_ns": details["query_wall_ns"],
            "solver_wall_ns": details["solver_wall_ns"],
            "conservative_combined_peak_rss_bytes":
                details["conservative_combined_peak_rss_bytes"],
            "row_sha256": sha(line),
            "archived_artifacts": sorted(archived),
        })

    receipt = {
        "kind": "d13_m12_first_four_precomputation_independent_audit_v1",
        "status": "PASS_FOUR_TIMEOUT_ROWS_AND_ARCHIVES",
        "candidate_id": protocol["candidate_id"],
        "workload_id": protocol["workload_id"],
        "run_id": launch["run_id"],
        "verified_relations": 0,
        "attempts_completed": 4,
        "total_charged_query_wall_ns": sum(
            row["charged_query_wall_ns"] for row in audit_rows),
        "rows": audit_rows,
        "source_sha256": sha(Path(__file__).read_bytes()),
        "snapshot_sha256": sha(SNAPSHOT.read_bytes()),
        "protocol_sha256": sha(PROTOCOL.read_bytes()),
        "launch_sha256": sha(LAUNCH.read_bytes()),
    }
    with OUTPUT.open("x") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(receipt["status"], receipt["total_charged_query_wall_ns"])


if __name__ == "__main__":
    main()
