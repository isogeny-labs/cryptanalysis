"""Read-only receipt and byte replay for all linked N41 SAT attempts."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
FORMULAS = (
    "control.xcnf", "public.xcnf", "v2/control.xcnf",
    "v3/control.xcnf", "v3/public.xcnf",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def unpacked(path):
    digest, size = hashlib.sha256(), 0
    with gzip.open(path, "rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def main():
    archive_protocol = read(HERE / "archive_protocol.json")
    archive = read(HERE / "archive_result.json")
    assert archive_protocol["archive_source_sha256"] == sha(HERE / "archive.py")
    assert archive["status"] == "PASS_N41_LINKED_THREE_ATTEMPT_XCNF_ARCHIVE"
    assert archive["archive_protocol_sha256"] == sha(HERE / "archive_protocol.json")
    for name in FORMULAS:
        packed = HERE / (name + ".gz")
        receipt = archive["files"][name]
        assert sha(packed) == receipt["gzip_sha256"]
        digest, size = unpacked(packed)
        assert digest == receipt["raw_sha256"] == archive_protocol["raw_sha256"][name]
        assert size == receipt["raw_bytes"]

    first_protocol = read(HERE / "protocol.json")
    failure = read(HERE / "failure_audit_result.json")
    assert failure["status"] == "PRODUCER_FAILURE_XCNF_ZERO_LITERAL"
    assert failure["source_sha256"] == sha(HERE / "run.py")
    assert failure["protocol_sha256"] == sha(HERE / "protocol.json")
    assert first_protocol["sha256"]["runner"] == sha(HERE / "run.py")
    for label in ("control", "public"):
        receipt = read(HERE / f"{label}.json")
        profile = read(HERE / f"{label}.build.json")
        archived = archive["files"][f"{label}.xcnf"]
        assert receipt["status"] == "UNKNOWN" and receipt["exit_code"] == 255
        assert receipt["terminal_lines"] == [] and receipt["restart_rows"] == 0
        assert "PARSE ERROR" in (HERE / f"{label}.stderr").read_text()
        assert receipt["stderr_sha256"] == sha(HERE / f"{label}.stderr")
        assert receipt["stdout_sha256"] == sha(HERE / f"{label}.stdout")
        assert profile["sha256"] == archived["raw_sha256"]
        assert profile["bytes"] == archived["raw_bytes"]
        assert failure["attempts"][label]["formula_sha256"] == archived["raw_sha256"]
        assert failure["attempts"][label]["malformed_line"] == 112221
        assert failure["attempts"][label]["solver_search_started"] is False

    second_protocol = read(HERE / "v2/protocol.json")
    recover_protocol = read(HERE / "v2/recover_protocol.json")
    recovered = read(HERE / "v2/recover_result.json")
    assert second_protocol["sha256"]["runner"] == sha(HERE / "v2/run.py")
    assert second_protocol["sha256"]["first_failure_audit"] == sha(HERE / "failure_audit_result.json")
    assert recover_protocol["sha256"]["formula"] == archive["files"]["v2/control.xcnf"]["raw_sha256"]
    assert recover_protocol["sha256"]["source"] == sha(HERE / "v2/recover_control.py")
    assert recover_protocol["sha256"]["stdout"] == sha(HERE / "v2/control.stdout")
    assert recovered["status"] == "PASS_N41_V2_SAT_CONTROL_RECOVERED_AFTER_DECODER_ERROR"
    assert recovered["recover_protocol_sha256"] == sha(HERE / "v2/recover_protocol.json")
    linked = read(GOAL / "n41_n131_linked_frobenius_pair_20261012/audit_result.json")
    known_ids = [entry["state_id"] for entry in linked["source_pairs"]]
    assert recovered["selected_state_ids"] == known_ids
    assert recovered["raw_preimage_index"] == linked["raw_target_preimage_index"] == 3
    assert recovered["raw_sum"] == linked["raw_target_replayed"]

    final_protocol = read(HERE / "v3/protocol.json")
    assert final_protocol["sha256"]["runner"] == sha(HERE / "v3/run.py")
    assert final_protocol["sha256"]["v2_control_formula"] == archive["files"]["v2/control.xcnf"]["raw_sha256"]
    assert final_protocol["sha256"]["v2_control_stdout"] == sha(HERE / "v2/control.stdout")
    assert final_protocol["sha256"]["linked_audit"] == sha(GOAL / "n41_n131_linked_frobenius_pair_20261012/audit_result.json")
    assert final_protocol["control_cap_s"] == 30 and final_protocol["public_cap_s"] == 180
    assert final_protocol["combined_rss_cap_bytes"] == 4 * 1024**3
    control, public = read(HERE / "v3/control.json"), read(HERE / "v3/public.json")
    cp, pp = read(HERE / "v3/control.build.json"), read(HERE / "v3/public.build.json")
    for label, receipt, profile in (("control", control, cp), ("public", public, pp)):
        archived = archive["files"][f"v3/{label}.xcnf"]
        assert profile["sha256"] == archived["raw_sha256"]
        assert profile["bytes"] == archived["raw_bytes"]
        assert profile["positive_assignment_check"] == {
            "clauses": profile["cnf_clauses"],
            "native_xor_rows": profile["native_xor_rows"]}
        assert receipt["stdout_sha256"] == sha(HERE / f"v3/{label}.stdout")
        assert receipt["stderr_sha256"] == sha(HERE / f"v3/{label}.stderr")
        assert receipt["peak_combined_rss_bytes_sampled"] < 4 * 1024**3
    assert control["status"] == "SAT" and control["stop"] is None
    assert control["terminal_lines"] == ["s SATISFIABLE"]
    assert control["model_check"] == {
        "cnf_clauses_checked": cp["cnf_clauses"],
        "native_xor_rows_checked": cp["native_xor_rows"]}
    assert control["group_replay"]["selected_state_ids"] == known_ids
    assert control["group_replay"]["nine_distinct_edges"] is True
    assert control["group_replay"]["nine_links_checked"] == 9
    assert control["group_replay"]["raw_sum"] == linked["raw_target_replayed"]
    assert public["status"] == public["stop"] == "PARENT_TIME_CAP"
    assert public["terminal_lines"] == [] and public["model_check"] is None
    assert public["restart_rows"] > 0 and public["exit_code"] == -9
    print("PASS_N41_LINKED_FUNCTIONAL_FINAL_EVIDENCE_AUDIT", public["status"])


if __name__ == "__main__":
    main()
