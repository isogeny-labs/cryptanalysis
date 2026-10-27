"""Independent Sage reverse-triple audit of exact six-source relations."""
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
    prior_index = json.loads(pinned(PLAN["source_index"]).read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert selection["status"] == "CLASSES_FROZEN"
    assert prior_index["status"] == result["status"] == "COMPLETE"
    assert len(selection["selected"]) == len(result["cases"]) == len(PLAN["cases"]) == 8
    audits = []
    for frozen, item, result_item in zip(selection["selected"], PLAN["cases"], result["cases"]):
        p, q = frozen["p"], frozen["q"]
        assert p == item["p"] == result_item["p"]
        prior = [json.loads(line) for line in pinned(item["journal"]).read_text().splitlines()]
        summary = json.loads(pinned(item["summary"]).read_text())
        output_path = HERE / result_item["path"]
        assert sha(output_path) == result_item["sha256"]
        output = json.loads(output_path.read_text())
        assert len(prior) == 40 and output["status"] == "COMPLETE"
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
        for row in baseline:
            assert sum((v*points[j] for j, v in row.items()), zero) == zero
        base_rank = rank(baseline, q)
        assert base_rank == summary["final_rank_mod_q"] == output["baseline_rank_with_five"]
        latter = defaultdict(list)
        for l, m, n in itertools.combinations(range(40), 3):
            for sl, sm, sn in itertools.product((-1, 1), repeat=3):
                latter[sl*outside[l] + sm*outside[m] + sn*outside[n]].append((l, m, n, sl, sm, sn))
        expected = {}
        for i, j, k in itertools.combinations(range(40), 3):
            for sj, sk in itertools.product((-1, 1), repeat=2):
                need = -(outside[i] + sj*outside[j] + sk*outside[k])
                for l, m, n, sl, sm, sn in latter.get(need, ()):
                    if k >= l:
                        continue
                    sources = (i, j, k, l, m, n)
                    signs = (1, sj, sk, sl, sm, sn)
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
        assert len(expected) == output["six_rows"] == output["matched_zero_sums"] == result_item["six_rows"]
        assert output["triple_insertions"] == 4*comb(40, 3)
        assert output["triple_probes"] == 8*comb(40, 3)
        assert output["search_wall_ns"] == output["build_wall_ns"] + output["query_wall_ns"]
        assert output["search_wall_ns"] < PLAN["wall_cap_seconds_per_case"] * 1e9
        assert len(expected) < PLAN["row_cap_per_case"]
        final_rank = rank(baseline + [dict(row) for row in expected.values()], q)
        assert final_rank == output["rank_with_six"] == result_item["rank_with_six"]
        assert final_rank - base_rank == output["novel_directions"] == result_item["novel_directions"]
        assert sum(bool(row["novel"]) for row in output["rows"]) == output["novel_directions"]
        audits.append({"p": p, "q": q, "source_equations": 40,
                       "six_rows": len(expected), "baseline_rank_with_five": base_rank,
                       "rank_with_six": final_rank, "novel_directions": final_rank-base_rank,
                       "status": "PASS"})
        print(json.dumps(audits[-1]), flush=True)
    (HERE / "audit.json").write_text(json.dumps({"schema": "hecke-d79-support-six-audit-v1",
                                                 "status": "PASS", "cases": audits},
                                                indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
