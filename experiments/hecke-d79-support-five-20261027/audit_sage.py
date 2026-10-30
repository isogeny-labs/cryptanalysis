"""Independently enumerate five-source zero sums with Sage triple buckets."""
import hashlib
import importlib.util
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
    assert sha(path) == item["sha256"]
    return path


def module(item, name):
    spec = importlib.util.spec_from_file_location(name, pinned(item))
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def sparse(raw):
    return {int(j): int(v) for j, v in raw.items() if v}


def rank(rows, q):
    F = GF(q)
    return int(matrix(F, len(rows), 40, lambda i, j: rows[i].get(j, 0)).rank())


def canonical(row):
    return tuple(sorted(sparse(row).items()))


def main():
    for path, digest in (("inputs.json", PRE["inputs_sha256"]),
                         ("PROTOCOL.md", PRE["protocol_sha256"]),
                         ("run_sage.py", PRE["runner_sha256"]),
                         ("sage-runtime-info.txt", PRE["sage_runtime_info_sha256"]),
                         ("pre-run.json", POST["pre_run_sha256"]),
                         ("result.json", POST["result_sha256"]),
                         ("run-stdout.jsonl", POST["stdout_sha256"]),
                         ("run-stderr.txt", POST["stderr_sha256"])):
        assert sha(HERE / path) == digest, path
    frozen = json.loads(pinned(PLAN["source_selection"]).read_text())
    previous = json.loads(pinned(PLAN["source_result"]).read_text())
    output = json.loads((HERE / "result.json").read_text())
    assert frozen["status"] == "CLASSES_FROZEN"
    assert previous["status"] == output["status"] == "COMPLETE"
    assert len(frozen["selected"]) == len(output["cases"]) == len(PLAN["cases"]) == 8
    helper = module(PLAN["relation_helpers"], "five_audit_group")
    ref = module(PLAN["pair_index_reference"], "five_audit_four")
    audits = []
    for selected, input_case, prior, item in zip(frozen["selected"], PLAN["cases"], previous["cases"], output["cases"]):
        p, q = selected["p"], selected["q"]
        assert p == input_case["p"] == prior["p"] == item["p"]
        earlier = json.loads(pinned(input_case).read_text())
        path = HERE / item["path"]
        assert sha(path) == item["sha256"]
        case = json.loads(path.read_text())
        assert case["p"] == p and case["q"] == q and case["status"] == "COMPLETE"
        E = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
        assert int(E.cardinality()) == selected["class"]["curve_order"]
        zero = E(0)
        points = [E(x, y) for x, y in selected["class"]["class_points"]]
        outside = []
        entries = earlier["entries"]
        assert len(entries) == 40
        for i, entry in enumerate(entries):
            assert entry["source"] == i and entry["status"] == "OUTSIDE_CLASS_TRACE"
            total = sum((E(x, y) for x, y in entry["outside_traces"]), zero)
            part = sum((v * points[j] for j, v in sparse(entry["class_part"]).items()), zero)
            assert total + part == zero
            outside.append(total)
        baseline = [sparse(x["row"]) for x in selected["class"]["base_rows"] + selected["direct_candidates"]]
        assert rank(baseline, q) == selected["baseline_rank_mod_q"]
        for row in baseline:
            assert sum((v * points[j] for j, v in row.items()), zero) == zero
        neg, add = helper.group_law(p)
        four, _ = ref.hecke_rows_pair_index({i: x for i, x in enumerate(entries)},
                                              [tuple(x) for x in selected["class"]["class_points"]], neg, add)
        four_rows = [sparse(x["row"]) for x in four]
        for row in four_rows:
            assert sum((v * points[j] for j, v in row.items()), zero) == zero
        four_rank = rank(baseline + four_rows, q)
        assert four_rank == prior["orders"]["original"]["final_rank_mod_q"] == case["baseline_rank_with_four"]
        triples = defaultdict(list)
        for i, j, k in itertools.combinations(range(40), 3):
            for sj, sk in itertools.product((-1, 1), repeat=2):
                total = outside[i] + sj * outside[j] + sk * outside[k]
                triples[total].append((i, j, k, sj, sk))
        expected = {}
        for l, m in itertools.combinations(range(40), 2):
            for sl, sm in itertools.product((-1, 1), repeat=2):
                need = -(sl * outside[l] + sm * outside[m])
                for i, j, k, sj, sk in triples.get(need, ()):
                    if k >= l:
                        continue
                    sources = (i, j, k, l, m)
                    signs = (1, sj, sk, sl, sm)
                    row = Counter()
                    for source, sign in zip(sources, signs):
                        row.update({j: sign*v for j, v in sparse(entries[source]["class_part"]).items()})
                    row = {j: v for j, v in row.items() if v}
                    assert sum((v * points[j] for j, v in row.items()), zero) == zero
                    key = (sources, signs)
                    assert key not in expected
                    expected[key] = canonical(row)
        actual = {}
        for record in case["rows"]:
            key = (tuple(record["sources"]), tuple(record["coefficients"]))
            assert key not in actual
            actual[key] = canonical(record["row"])
        assert actual == expected
        assert len(expected) == case["five_rows"] == case["pair_matches"] == item["five_rows"]
        assert case["pair_insertions"] == 4*comb(40, 2)
        assert case["triple_probes"] == 4*comb(40, 3)
        final_rank = rank(baseline + four_rows + [dict(row) for row in expected.values()], q)
        assert final_rank == case["rank_with_five"] == item["rank_with_five"]
        assert final_rank - four_rank == case["novel_directions"] == item["novel_directions"]
        assert sum(bool(record["novel"]) for record in case["rows"]) == case["novel_directions"]
        audits.append({"p": p, "q": q, "source_equations": 40, "four_rank": four_rank,
                       "five_rows": len(expected), "five_rank": final_rank,
                       "novel_directions": final_rank - four_rank, "status": "PASS"})
        print(json.dumps(audits[-1]), flush=True)
    (HERE / "audit.json").write_text(json.dumps({"schema": "hecke-d79-support-five-audit-v1",
                                                 "status": "PASS", "cases": audits},
                                                indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
