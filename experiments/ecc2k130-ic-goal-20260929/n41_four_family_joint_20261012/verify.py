"""Receipt and independent-source consistency checks for four-family panel."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def verify_sources(protocol):
    assert all(sha(path) == value for path, value in protocol["sources"].items())


def main():
    protocol = load("protocol.json")
    verify_sources(protocol)
    source = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
    counts = [[0] * 256 for _ in range(4)]
    for line in source.read_text().splitlines()[1:]:
        parts = line.split()
        if parts[0] == "S":
            counts[int(parts[1])][int(parts[3]) ^ int(parts[4])] += 1
    tuples = [protocol["positive_seed_tuple"], *protocol["negative_seed_tuples"]]
    statuses = []
    for label, seeds in zip(("positive", "negative0", "negative1"), tuples):
        build, result = load(f"{label}_build.json"), load(f"{label}_result.json")
        assert build["seed_tuple"] == seeds
        assert [row["states"] for row in build["family_sizes"]] == [counts[i][s] for i, s in enumerate(seeds)]
        assert sha(HERE / f"{label}.xcnf") == build["formula_sha256"]
        assert result["protocol_sha256"] == sha(HERE / "protocol.json")
        assert result["build_sha256"] == sha(HERE / f"{label}_build.json")
        assert sha(HERE / f"{label}.stdout") == result["stdout_sha256"]
        assert sha(HERE / f"{label}.stderr") == result["stderr_sha256"]
        terminals = [x for x in (HERE / f"{label}.stdout").read_text().splitlines() if x.startswith("s ")]
        assert (terminals[-1] if terminals else None) == result["terminal"]
        assert result["status"] == "BOUNDED_UNKNOWN" and result["terminal"] == "s INDETERMINATE"
        statuses.append(result["status"])
    assert load("positive_build.json")["positive_assignment_check"] == {
        "cnf_clauses": load("positive_build.json")["clauses"],
        "native_xor_rows": load("positive_build.json")["xor_rows"]}
    branch, branch_result = load("branch_protocol.json"), load("positive_branch_result.json")
    verify_sources(branch)
    assert branch_result["protocol_sha256"] == sha(HERE / "branch_protocol.json")
    assert sha(HERE / "positive_branch.stdout") == branch_result["stdout_sha256"]
    assert sha(HERE / "positive_branch.stderr") == branch_result["stderr_sha256"]
    assert branch_result["status"] == "BOUNDED_UNKNOWN"
    join = load("join_protocol.json")
    assert all(sha(path) == value for path, value in join["source_hashes"].items())
    assert join["seed_tuples"] == tuples
    compile_receipt = load("compile_receipt.json")
    assert compile_receipt["status"] == "PASS_LOCAL_COMPILE"
    assert compile_receipt["join_protocol_sha256"] == sha(HERE / "join_protocol.json")
    assert compile_receipt["source_sha256"] == sha(HERE / "join.cpp")
    assert compile_receipt["binary_sha256"] == sha(HERE / "join")
    failure = load("failure_v1.json")
    assert failure["status"] == "PRE_SOLVER_IMPORT_ERROR"
    assert failure["original_protocol_sha256"] == sha(HERE / "protocol_failed_v1.json")
    summaries = []
    for index, seeds in enumerate(tuples):
        receipt = load(f"join_{index}_receipt.json")
        assert receipt["status"] == "PASS" and receipt["exit_code"] == 0
        assert receipt["protocol_sha256"] == sha(HERE / "join_protocol.json")
        assert receipt["stdout_sha256"] == sha(HERE / f"join_{index}.stdout")
        assert receipt["stderr_sha256"] == sha(HERE / f"join_{index}.stderr")
        lines = (HERE / f"join_{index}.stdout").read_text().splitlines()
        result = [int(v) if i < 10 else float(v) for i, v in enumerate(lines[-1].split()[1:])]
        assert lines[-1].startswith("RESULT ") and int(result[0]) == 123808
        assert list(map(int, result[1:5])) == [counts[i][s] for i, s in enumerate(seeds)]
        assert int(result[5]) == int(result[1] * result[2])
        assert int(result[7]) == int(result[3] * result[4])
        hits = [line for line in lines if line.startswith("HIT ")]
        assert int(result[9]) == len(hits)
        if index == 0:
            prior = json.loads((GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/audit_result.json").read_text())
            assert prior["status"] == "PASS_INDEPENDENT_N41_DIAGONAL_ALLSEED_FOURPAIR_RELATION"
            assert list(map(int, hits[0].split()[1:])) == [pair["state_id"] for pair in prior["pairs"]]
        else:
            assert not hits
        summaries.append({"seed_tuple": seeds, "states": list(map(int, result[1:5])),
                          "left_attempts": int(result[5]), "right_attempts": int(result[7]),
                          "hits": len(hits), "internal_seconds": result[10]})
    print(json.dumps({"status": "PASS_FROZEN_FOUR_FAMILY_PANEL",
                      "sat_statuses": statuses, "branch_status": branch_result["status"],
                      "join_summaries": summaries}, sort_keys=True))


if __name__ == "__main__":
    main()
