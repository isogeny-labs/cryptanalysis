"""Independent byte, solver-log, and N41 positive-chain audit."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
INPUT = GOAL / "n41_w8_sixpair_mitm_20261011/join_input.tsv"
POSITIVE = GOAL / "n41_w8_tenpair_density_control_20261012/audit_result.json"
N = 41
MOD = (1 << N) | (1 << 3) | 1
SLOTS = (0, 1, 2, 3, 4, 5, 0, 1, 2, 3)
TREE = ((0, 1), (2, 3), (4, 5), (6, 7), (10, 11),
        (12, 13), (14, 15), (16, 8), (17, 9))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mul(a, b):
    product = 0
    for i in range(N):
        if b >> i & 1:
            product ^= a << i
    for i in range(2 * N - 2, N - 1, -1):
        if product >> i & 1:
            product ^= MOD << (i - N)
    return product


def power(a, exponent):
    result = 1
    while exponent:
        if exponent & 1:
            result = mul(result, a)
        a = mul(a, a)
        exponent >>= 1
    return result


def add(p, q):
    if p is None:
        return q
    if q is None:
        return p
    x1, y1 = p
    x2, y2 = q
    assert x1 != x2
    slope = mul(y1 ^ y2, power(x1 ^ x2, (1 << N) - 2))
    x3 = mul(slope, slope) ^ slope ^ x1 ^ x2
    y3 = mul(slope, x1 ^ x3) ^ x3 ^ y1
    return x3, y3


def source():
    rows = [[None] * 140 for _ in range(6)]
    targets = [None] * 4
    with INPUT.open() as stream:
        assert stream.readline().split() == ["ECC2K41", "6", "140", "4"]
        for line in stream:
            words = line.split()
            if words[0] == "S":
                slot, sid, edge, a, b, sa, sb, x, y = map(int, words[1:])
                assert edge == sid // 4 and a < b and a ^ b == 184
                rows[slot][sid] = (edge, (x, y))
            elif words[0] == "T":
                index, x, y = map(int, words[1:])
                targets[index] = (x, y)
            else:
                assert words[0] == "C"
    assert all(all(row is not None for row in block) for block in rows)
    assert all(point is not None for point in targets)
    return rows, targets


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    hashes = protocol["sha256"]
    assert sha(HERE / "run.py") == hashes["runner"]
    assert sha(INPUT) == hashes["input"]
    assert sha(POSITIVE) == hashes["positive"]
    assert sha(GOAL / "n41_w8_tenpair_functional_20261012/build.py") == hashes["old_builder"]
    assert sha("/opt/homebrew/bin/cryptominisat5") == hashes["solver"]
    rows, targets = source()
    audit = json.loads(POSITIVE.read_text())
    ids = [row["state_id"] for row in audit["source_pairs"]]
    assert len(ids) == 10
    edges = [rows[slot][sid][0] for slot, sid in zip(SLOTS, ids)]
    assert len(set(edges)) == 10
    nodes = [rows[slot][sid][1] for slot, sid in zip(SLOTS, ids)]
    for left, right in TREE:
        nodes.append(add(nodes[left], nodes[right]))
    assert nodes[-1] == targets[audit["raw_target_preimage_index"]]
    profiles = {}
    for label, cap in (("control", 30), ("public", 180)):
        build = json.loads((HERE / f"{label}.build.json").read_text())
        result = json.loads((HERE / f"{label}.json").read_text())
        formula = HERE / f"{label}.xcnf"
        assert sha(formula) == build["sha256"] and formula.stat().st_size == build["bytes"]
        lines = formula.read_text().splitlines()
        assert lines[0] == f'p cnf {build["variables"]} {build["cnf_clauses"] + build["native_xor_rows"]}'
        assert sum(line.startswith("x ") for line in lines[1:]) == build["native_xor_rows"]
        assert len(lines) - 1 - build["native_xor_rows"] == build["cnf_clauses"]
        assert build["positive_assignment_check"] == {
            "clauses": build["cnf_clauses"], "native_xor_rows": build["native_xor_rows"]}
        assert sha(HERE / f"{label}.stdout") == result["stdout_sha256"]
        assert sha(HERE / f"{label}.stderr") == result["stderr_sha256"]
        log = (HERE / f"{label}.stdout").read_text(errors="replace")
        assert [line for line in log.splitlines() if line.startswith("s ")] == result["terminal_lines"] == []
        assert sum(line.startswith("c rst") for line in log.splitlines()) == result["restart_rows"]
        assert result["status"] == result["stop"] == "PARENT_TIME_CAP"
        assert result["exit_code"] == -9 and result["model_check"] is None
        assert cap <= result["wall_ns_exploratory"] / 1e9 < cap + 1
        assert result["peak_combined_rss_bytes_sampled"] < protocol["combined_rss_cap_bytes"]
        profiles[label] = {"variables": build["variables"],
                           "cnf_clauses": build["cnf_clauses"],
                           "native_xor_rows": build["native_xor_rows"],
                           "restart_rows": result["restart_rows"]}
    control = (HERE / "control.xcnf").read_text().splitlines()
    public = (HERE / "public.xcnf").read_text().splitlines()
    public_clauses = profiles["public"]["cnf_clauses"]
    assert control[1:1 + public_clauses] == public[1:1 + public_clauses]
    units = control[1 + public_clauses:1 + public_clauses + 11]
    assert len(units) == 11 and all(len(line.split()) == 2 for line in units)
    assert control[1 + public_clauses + 11:] == public[1 + public_clauses:]
    output = {"status": "PASS_N41_FULLPOINT_BALANCED_ARCHIVE_AUDIT",
              "positive_raw_preimage_index": audit["raw_target_preimage_index"],
              "positive_group_links_replayed": 9,
              "ten_distinct_edges": True,
              "formula_and_terminal_profiles": profiles,
              "source_sha256": sha(HERE / "verify.py")}
    archive = HERE / "audit.json"
    if archive.exists():
        previous = json.loads(archive.read_text())
        assert previous["source_sha256"] == "0fdb1f488c5f2ce6f210333926d38b212511dc861057698fa9ee54c5154eaabf"
        # The first write-once verifier produced the immutable receipt. This
        # replay addition changes only the verifier hash, so compare all
        # measured and mathematical fields without modifying that receipt.
        assert {k: v for k, v in previous.items() if k != "source_sha256"} == {
            k: v for k, v in output.items() if k != "source_sha256"}
    else:
        with archive.open("x") as stream:
            json.dump(output, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(output["status"])


if __name__ == "__main__":
    main()
