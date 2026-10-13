"""Read-only verifier for the frozen four-fiber N41 portfolio."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
NAMES = ("base.xcnf", *(f"fiber{i}.xcnf" for i in range(4)))


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
    protocol, result = read(HERE / "protocol.json"), read(HERE / "result.json")
    audit_protocol, audit = read(HERE / "audit_protocol.json"), read(HERE / "audit_result.json")
    archive_protocol, archive = read(HERE / "archive_protocol.json"), read(HERE / "archive_result.json")
    parent = GOAL / "n41_linked_functional_fullpoint_20261012"
    paths = {"runner": HERE / "run.py", "v3_runner": parent / "v3/run.py",
             "v3_protocol": parent / "v3/protocol.json",
             "v3_public_receipt": parent / "v3/public.json",
             "v3_public_build": parent / "v3/public.build.json",
             "v3_archive": parent / "archive_result.json",
             "source_input": GOAL / "n41_w8_sixpair_mitm_20261011/join_input.tsv",
             "solver": Path("/opt/homebrew/bin/cryptominisat5")}
    assert protocol["sha256"] == {name: sha(path) for name, path in paths.items()}
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["status"] == audit["portfolio_status"] == "BOUNDED_UNKNOWN"
    assert result["fiber_order"] == [0, 1, 2, 3]
    assert result["worker_count"] == 1
    assert result["total_target_dependent_ns"] < protocol["total_cap_seconds"] * 10**9
    assert audit_protocol["sha256"] == {
        "audit_source": sha(HERE / "audit.py"),
        "runner": sha(HERE / "run.py"),
        "protocol": sha(HERE / "protocol.json"),
        "result": sha(HERE / "result.json"),
        "v3_runner": sha(parent / "v3/run.py"),
    }
    assert audit["status"] == "PASS_N41_LINKED_FOUR_FIBER_TERMINAL_AUDIT"
    assert audit["audit_protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert audit["all_four_formulas_rebuilt_byte_for_byte"] is True
    assert audit["known_witness_fiber"] == 3
    assert sum(audit["phase_ns"].values()) == result["total_target_dependent_ns"]
    assert archive_protocol["archive_source_sha256"] == sha(HERE / "archive.py")
    assert archive_protocol["audit_result_sha256"] == sha(HERE / "audit_result.json")
    assert archive["status"] == "PASS_N41_LINKED_FIBER_XCNF_ARCHIVE"
    assert archive["archive_protocol_sha256"] == sha(HERE / "archive_protocol.json")
    for name in NAMES:
        packed = HERE / (name + ".gz")
        receipt = archive["files"][name]
        assert sha(packed) == receipt["gzip_sha256"]
        digest, size = unpacked(packed)
        assert digest == receipt["raw_sha256"] == archive_protocol["raw_sha256"][name]
        assert size == receipt["raw_bytes"]
    assert archive["files"]["base.xcnf"]["raw_sha256"] == result["base_formula_sha256"]
    restarts = 0
    for row in result["slices"]:
        index = row["fiber"]
        assert row["formula_sha256"] == archive["files"][f"fiber{index}.xcnf"]["raw_sha256"]
        assert row["formula_bytes"] == archive["files"][f"fiber{index}.xcnf"]["raw_bytes"]
        receipt = read(HERE / f"fiber{index}.json")
        assert row["receipt_sha256"] == sha(HERE / f"fiber{index}.json")
        assert row["status"] == receipt["status"] == receipt["stop"] == "PARENT_TIME_CAP"
        assert receipt["terminal_lines"] == [] and receipt["model_check"] is None
        assert receipt["stdout_sha256"] == sha(HERE / f"fiber{index}.stdout")
        assert receipt["stderr_sha256"] == sha(HERE / f"fiber{index}.stderr")
        assert receipt["exit_code"] == -9 and receipt["restart_rows"] > 0
        assert receipt["peak_combined_rss_bytes_sampled"] < protocol["combined_rss_cap_bytes"]
        restarts += receipt["restart_rows"]
    assert restarts == audit["total_restarts"]
    print("PASS_N41_LINKED_FOUR_FIBER_FINAL_EVIDENCE_AUDIT", result["status"])


if __name__ == "__main__":
    main()
