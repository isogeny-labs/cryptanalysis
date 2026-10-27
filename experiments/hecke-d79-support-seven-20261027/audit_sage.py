"""Independent Sage 4+3 audit of canonical seven-source relations."""
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

from sage.all import EllipticCurve, GF, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())
PRE = json.loads((HERE / "pre-run.json").read_text())
POST = json.loads((HERE / "post-run.json").read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned(item):
    path = ROOT / item["path"]
    assert sha(path) == item["sha256"], str(path)
    return path


def sparse(raw):
    return {int(j): int(v) for j, v in raw.items() if v}


def rank(rows, q):
    F = GF(q)
    return int(matrix(F, len(rows), 40, lambda i, j: rows[i].get(j, 0)).rank())


def canonical(row):
    return tuple(sorted(sparse(row).items()))


def main():
    for name, digest in (("inputs.json", PRE["inputs_sha256"]),
                         ("PROTOCOL.md", PRE["protocol_sha256"]),
                         ("run_sage.py", PRE["runner_sha256"]),
                         ("sage-runtime-info.txt", PRE["sage_runtime_info_sha256"]),
                         ("pre-run.json", POST["pre_run_sha256"]),
                         ("result.json", POST["result_sha256"]),
                         ("run-stdout.jsonl", POST["stdout_sha256"]),
                         ("run-stderr.txt", POST["stderr_sha256"])):
        assert sha(HERE / name) == digest, name
    selection = json.loads(pinned(PLAN["source_selection"]).read_text())
    old_index = json.loads(pinned(PLAN["source_index"]).read_text())
    six_index = json.loads(pinned(PLAN["six_result"]).read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert selection["status"] == "CLASSES_FROZEN"
    assert old_index["status"] == six_index["status"] == result["status"] == "COMPLETE"
    assert len(selection["selected"]) == len(result["cases"]) == len(PLAN["cases"]) == 8
    audits = []
    for frozen, item, result_item in zip(selection["selected"], PLAN["cases"], result["cases"]):
        p, q = frozen["p"], frozen["q"]
        assert p == item["p"] == result_item["p"]
        prior = [json.loads(line) for line in pinned(item["journal"]).read_text().splitlines()]
        summary = json.loads(pinned(item["summary"]).read_text())
        six = json.loads(pinned(item["six_case"]).read_text())
        output_path = HERE / result_item["path"]
        assert sha(output_path) == result_item["sha256"]
        output = json.loads(output_path.read_text())
        assert len(prior) == 40 and six["status"] == output["status"] == "COMPLETE"
        E = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
        assert int(E.cardinality()) == frozen["class"]["curve_order"]
        zero = E(0)
        points = [E(x, y) for x, y in frozen["class"]["class_points"]]
        entries = [record["entry"] for record in prior]
        outside = []
        for i, entry in enumerate(entries):
            assert entry["source"] == i and entry["status"] == "OUTSIDE_CLASS_TRACE"
            total = sum((E(x, y) for x, y in entry["outside_traces"]), zero)
            part = sum((v*points[j] for j, v in sparse(entry["class_part"]).items()), zero)
            assert total + part == zero
            outside.append(total)
        baseline = [sparse(row["row"]) for row in frozen["class"]["base_rows"] +
                    frozen["direct_candidates"]]
        baseline += [sparse(row["row"]) for record in prior
                     for row in record["four_rows"] + record["five_rows"]]
        baseline += [sparse(row["row"]) for row in six["rows"]]
        for row in baseline:
            assert sum((v*points[j] for j, v in row.items()), zero) == zero
        base_rank = rank(baseline, q)
        assert base_rank == six["rank_with_six"] == output["baseline_rank_with_six"]
        first_four = defaultdict(list)
        for i, j, k, l in itertools.combinations(range(40), 4):
            for sj, sk, sl in itertools.product((-1, 1), repeat=3):
                total = outside[i] + sj*outside[j] + sk*outside[k] + sl*outside[l]
                first_four[total].append((i, j, k, l, sj, sk, sl))
        expected = {}
        for m, n, o in itertools.combinations(range(40), 3):
            for sm, sn, so in itertools.product((-1, 1), repeat=3):
                need = -(sm*outside[m] + sn*outside[n] + so*outside[o])
                for i, j, k, l, sj, sk, sl in first_four.get(need, ()):
                    if l >= m:
                        continue
                    sources = (i, j, k, l, m, n, o)
                    signs = (1, sj, sk, sl, sm, sn, so)
                    row = Counter()
                    for source, sign in zip(sources, signs):
                        for column, coefficient in sparse(entries[source]["class_part"]).items():
                            row[column] += sign*coefficient
                    row = {column: coefficient for column, coefficient in row.items() if coefficient}
                    assert sum((v*points[column] for column, v in row.items()), zero) == zero
                    key = (sources, signs)
                    assert key not in expected
                    expected[key] = canonical(row)
        actual = {}
        for row in output["rows"]:
            key = (tuple(row["sources"]), tuple(row["coefficients"]))
            assert key not in actual
            actual[key] = canonical(row["row"])
        assert actual == expected
        assert len(expected) == output["seven_rows"] == output["matched_zero_sums"] == result_item["seven_rows"]
        assert output["triple_insertions"] == 4*comb(40, 3)
        assert output["quadruple_probes"] == 16*comb(40, 4)
        assert output["search_wall_ns"] == output["build_wall_ns"] + output["query_wall_ns"]
        assert output["search_wall_ns"] < PLAN["wall_cap_seconds_per_case"] * 1e9
        assert len(expected) < PLAN["row_cap_per_case"]
        final_rank = rank(baseline + [dict(row) for row in expected.values()], q)
        assert final_rank == output["rank_with_seven"] == result_item["rank_with_seven"]
        assert final_rank - base_rank == output["novel_directions"] == result_item["novel_directions"]
        assert sum(bool(row["novel"]) for row in output["rows"]) == output["novel_directions"]
        if final_rank == PLAN["rank_goal"]:
            anchor = output["anchor"]
            projected = [(frozen["class"]["curve_order"] // q)*point for point in points]
            T = projected[anchor["anchor_index"]]
            assert int(T.order()) == q and anchor["anchored_log_replay"] == "PASS"
            assert [int(T[0]), int(T[1])] == anchor["anchor_point"]
            assert len(anchor["anchored_logs"]) == 40
            assert all(log*T == point for log, point in zip(anchor["anchored_logs"], projected))
            assert rank(baseline + [dict(row) for row in expected.values()] +
                        [{anchor["anchor_index"]: 1}], q) == 40
        audits.append({"p": p, "q": q, "source_equations": 40,
                       "seven_rows": len(expected), "baseline_rank_with_six": base_rank,
                       "rank_with_seven": final_rank, "novel_directions": final_rank-base_rank,
                       "anchor_replay": output.get("anchor", {}).get("anchored_log_replay"),
                       "status": "PASS"})
        print(json.dumps(audits[-1]), flush=True)
    (HERE / "audit.json").write_text(json.dumps({"schema": "hecke-d79-support-seven-audit-v1",
                                                 "status": "PASS", "cases": audits},
                                                indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
