"""Enumerate canonical signed six-source zero sums with triple buckets."""
import hashlib
import importlib.util
import itertools
import json
import time
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

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


def main():
    selected = json.loads(pinned(PLAN["source_selection"]).read_text())
    old = json.loads(pinned(PLAN["source_index"]).read_text())
    assert selected["status"] == "CLASSES_FROZEN" and old["status"] == "COMPLETE"
    assert [x["p"] for x in selected["selected"]] == [x["p"] for x in PLAN["cases"]]
    R = module(PLAN["relation_helpers"], "six_group")
    I = module(PLAN["incremental_module"], "six_rank")
    case_dir = HERE / "cases"
    case_dir.mkdir(exist_ok=False)
    output = {"schema": "hecke-d79-support-six-result-v1", "status": "RUNNING",
              "candidate_id": None, "target_online_ms": None, "cases": []}
    save(HERE / "result.json", output)
    for frozen, item in zip(selected["selected"], PLAN["cases"]):
        p, q = frozen["p"], frozen["q"]
        assert p == item["p"]
        prior = [json.loads(line) for line in pinned(item["journal"]).read_text().splitlines()]
        summary = json.loads(pinned(item["summary"]).read_text())
        assert len(prior) == summary["source_count"] == 40
        assert (summary["p"], summary["q"]) == (p, q)
        entries = [x["entry"] for x in prior]
        assert all(x["source"] == i and x["status"] == "OUTSIDE_CLASS_TRACE"
                   for i, x in enumerate(entries))
        neg, add = R.group_law(p)
        points = [tuple(x) for x in frozen["class"]["class_points"]]
        parts = [I.sparse(x["class_part"]) for x in entries]
        totals = []
        for entry in entries:
            total = None
            for trace in entry["outside_traces"]:
                total = add(total, tuple(trace))
            totals.append(total)
        baseline = [I.sparse(x["row"]) for x in frozen["class"]["base_rows"] +
                    frozen["direct_candidates"]]
        baseline += [I.sparse(row["row"]) for record in prior
                     for row in record["four_rows"] + record["five_rows"]]
        basis = I.RankBasis(q, baseline)
        assert basis.rank == summary["final_rank_mod_q"]
        start_rank = basis.rank
        build_started = time.perf_counter_ns()
        triples = defaultdict(list)
        triple_insertions = 0
        for i, j, k in itertools.combinations(range(40), 3):
            for sj, sk in itertools.product((-1, 1), repeat=2):
                total = add(totals[i], add(signed(totals[j], sj, neg),
                                           signed(totals[k], sk, neg)))
                triples[total].append((i, j, k, sj, sk))
                triple_insertions += 1
        build_wall_ns = time.perf_counter_ns() - build_started
        rows = []
        probes = matches = 0
        status = "COMPLETE"
        started = time.perf_counter_ns()
        for l, m, n in itertools.combinations(range(40), 3):
            if status != "COMPLETE":
                break
            for sl, sm, sn in itertools.product((-1, 1), repeat=3):
                total = add(signed(totals[l], sl, neg),
                            add(signed(totals[m], sm, neg), signed(totals[n], sn, neg)))
                probes += 1
                for i, j, k, sj, sk in triples.get(neg(total), ()):
                    if k >= l:
                        continue
                    matches += 1
                    sources = (i, j, k, l, m, n)
                    signs = (1, sj, sk, sl, sm, sn)
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
            assert probes == 8*comb(40, 3)
        result = {"p": p, "q": q, "status": status, "baseline_rank_with_five": start_rank,
                  "rank_with_six": basis.rank, "six_rows": len(rows),
                  "novel_directions": basis.rank - start_rank,
                  "triple_insertions": triple_insertions, "triple_probes": probes,
                  "matched_zero_sums": matches, "build_wall_ns": build_wall_ns,
                  "query_wall_ns": query_wall_ns,
                  "search_wall_ns": build_wall_ns + query_wall_ns,
                  "rows": rows, "candidate_id": None, "target_online_ms": None}
        path = case_dir / f"p{p}.json"
        save(path, result)
        output["cases"].append({"p": p, "q": q, "path": path.relative_to(HERE).as_posix(),
                                "sha256": sha(path), "status": status,
                                "baseline_rank_with_five": start_rank,
                                "rank_with_six": basis.rank, "six_rows": len(rows),
                                "novel_directions": basis.rank - start_rank})
        save(HERE / "result.json", output)
        print(json.dumps(output["cases"][-1]), flush=True)
    output["status"] = "COMPLETE" if all(x["status"] == "COMPLETE" for x in output["cases"]) else "CENSORED"
    save(HERE / "result.json", output)


if __name__ == "__main__":
    main()
