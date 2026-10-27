"""Enumerate canonical signed seven-source zero sums with a 3+4 index."""
import hashlib
import importlib.util
import itertools
import json
import resource
import time
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

from sage.all import EllipticCurve, GF, matrix, vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned(item):
    path = ROOT / item["path"]
    assert sha(path) == item["sha256"], str(path)
    return path


def module(item, name):
    spec = importlib.util.spec_from_file_location(name, pinned(item))
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def signed(point, sign, neg):
    return point if sign == 1 else neg(point)


def anchor_logs(p, q, n, encoded_points, rows):
    E = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
    points = [E(x, y) for x, y in encoded_points]
    projected = [(n // q)*point for point in points]
    zero = E(0)
    anchor = next(j for j, point in enumerate(projected) if point != zero)
    T = projected[anchor]
    assert int(T.order()) == q
    F = GF(q)
    A = matrix(F, len(rows), 40, lambda i, j: rows[i].get(j, 0))
    assert int(A.rank()) == 39
    augmented = A.stack(matrix(F, 1, 40, lambda _, j: int(j == anchor)))
    assert int(augmented.rank()) == 40
    logs = [int(x) for x in augmented.solve_right(vector(F, [0]*len(rows) + [1]))]
    assert all(log*T == point for log, point in zip(logs, projected))
    return {"anchor_index": anchor, "anchor_point": [int(T[0]), int(T[1])],
            "anchored_logs": logs, "anchored_log_replay": "PASS"}


def main():
    selection = json.loads(pinned(PLAN["source_selection"]).read_text())
    prior_index = json.loads(pinned(PLAN["source_index"]).read_text())
    prior_six = json.loads(pinned(PLAN["six_result"]).read_text())
    assert selection["status"] == "CLASSES_FROZEN"
    assert prior_index["status"] == prior_six["status"] == "COMPLETE"
    assert [x["p"] for x in selection["selected"]] == [x["p"] for x in PLAN["cases"]]
    R = module(PLAN["relation_helpers"], "seven_group")
    I = module(PLAN["incremental_module"], "seven_rank")
    case_dir = HERE / "cases"
    case_dir.mkdir(exist_ok=False)
    output = {"schema": "hecke-d79-support-seven-result-v1", "status": "RUNNING",
              "candidate_id": None, "target_online_ms": None, "cases": []}
    save(HERE / "result.json", output)
    for frozen, item in zip(selection["selected"], PLAN["cases"]):
        p, q = frozen["p"], frozen["q"]
        assert p == item["p"]
        prior = [json.loads(line) for line in pinned(item["journal"]).read_text().splitlines()]
        summary = json.loads(pinned(item["summary"]).read_text())
        six = json.loads(pinned(item["six_case"]).read_text())
        assert len(prior) == summary["source_count"] == 40
        assert (summary["p"], summary["q"], six["p"], six["q"]) == (p, q, p, q)
        assert six["status"] == "COMPLETE"
        entries = [record["entry"] for record in prior]
        assert all(entry["source"] == i and entry["status"] == "OUTSIDE_CLASS_TRACE"
                   for i, entry in enumerate(entries))
        neg, add = R.group_law(p)
        points = [tuple(x) for x in frozen["class"]["class_points"]]
        parts = [I.sparse(entry["class_part"]) for entry in entries]
        totals = []
        for entry in entries:
            total = None
            for trace in entry["outside_traces"]:
                total = add(total, tuple(trace))
            totals.append(total)
        baseline = [I.sparse(row["row"]) for row in frozen["class"]["base_rows"] +
                    frozen["direct_candidates"]]
        baseline += [I.sparse(row["row"]) for record in prior
                     for row in record["four_rows"] + record["five_rows"]]
        baseline += [I.sparse(row["row"]) for row in six["rows"]]
        basis = I.RankBasis(q, baseline)
        assert basis.rank == six["rank_with_six"]
        base_rank = basis.rank
        build_started = time.perf_counter_ns()
        triples = defaultdict(list)
        triple_insertions = 0
        for i, j, k in itertools.combinations(range(40), 3):
            for sj, sk in itertools.product((-1, 1), repeat=2):
                total = add(totals[i], add(signed(totals[j], sj, neg), signed(totals[k], sk, neg)))
                triples[total].append((i, j, k, sj, sk))
                triple_insertions += 1
        build_wall_ns = time.perf_counter_ns() - build_started
        rows = []
        probes = matches = 0
        status = "COMPLETE"
        started = time.perf_counter_ns()
        for l, m, n, o in itertools.combinations(range(40), 4):
            if status != "COMPLETE":
                break
            for sl, sm, sn, so in itertools.product((-1, 1), repeat=4):
                total = add(signed(totals[l], sl, neg),
                            add(signed(totals[m], sm, neg),
                                add(signed(totals[n], sn, neg), signed(totals[o], so, neg))))
                probes += 1
                for i, j, k, sj, sk in triples.get(neg(total), ()):
                    if k >= l:
                        continue
                    matches += 1
                    sources = (i, j, k, l, m, n, o)
                    signs = (1, sj, sk, sl, sm, sn, so)
                    row = Counter()
                    for source, sign in zip(sources, signs):
                        for column, coefficient in parts[source].items():
                            row[column] += sign*coefficient
                    row = {column: coefficient for column, coefficient in row.items() if coefficient}
                    check = None
                    for column, coefficient in row.items():
                        for _ in range(abs(coefficient)):
                            point = points[column] if coefficient > 0 else neg(points[column])
                            check = add(check, point)
                    assert check is None
                    novel = bool(basis.insert(row))
                    rows.append({"sources": sources, "coefficients": signs,
                                 "row": {str(column): coefficient for column, coefficient in sorted(row.items())},
                                 "novel": novel})
                    if len(rows) >= PLAN["row_cap_per_case"]:
                        status = "CENSORED_ROW_CAP"
                        break
                if status != "COMPLETE":
                    break
            if (build_wall_ns + time.perf_counter_ns() - started) / 1e9 >= PLAN["wall_cap_seconds_per_case"]:
                status = "CENSORED_WALL_CAP"
        query_wall_ns = time.perf_counter_ns() - started
        if status == "COMPLETE":
            assert triple_insertions == 4*comb(40, 3)
            assert probes == 16*comb(40, 4)
        case = {"p": p, "q": q, "status": status, "baseline_rank_with_six": base_rank,
                "rank_with_seven": basis.rank, "seven_rows": len(rows),
                "novel_directions": basis.rank - base_rank,
                "triple_insertions": triple_insertions, "quadruple_probes": probes,
                "matched_zero_sums": matches, "build_wall_ns": build_wall_ns,
                "query_wall_ns": query_wall_ns, "search_wall_ns": build_wall_ns + query_wall_ns,
                "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "rows": rows, "candidate_id": None, "target_online_ms": None}
        if status == "COMPLETE" and basis.rank == PLAN["rank_goal"]:
            case["anchor"] = anchor_logs(p, q, frozen["class"]["curve_order"], points,
                                          baseline + [I.sparse(row["row"]) for row in rows])
        path = case_dir / f"p{p}.json"
        save(path, case)
        output["cases"].append({"p": p, "q": q, "path": path.relative_to(HERE).as_posix(),
                                "sha256": sha(path), "status": status,
                                "baseline_rank_with_six": base_rank,
                                "rank_with_seven": basis.rank, "seven_rows": len(rows),
                                "novel_directions": basis.rank - base_rank,
                                "anchor_replay": case.get("anchor", {}).get("anchored_log_replay")})
        save(HERE / "result.json", output)
        print(json.dumps(output["cases"][-1]), flush=True)
    output["status"] = "COMPLETE" if all(x["status"] == "COMPLETE" for x in output["cases"]) else "CENSORED"
    save(HERE / "result.json", output)


if __name__ == "__main__":
    main()
