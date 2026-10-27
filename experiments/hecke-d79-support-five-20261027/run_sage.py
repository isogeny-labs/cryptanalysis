"""Enumerate exact signed five-source zero sums with a pair index."""
import hashlib
import importlib.util
import itertools
import json
import sys
import time
from collections import Counter, defaultdict
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


def save(path, obj):
    path.write_text(json.dumps(obj, separators=(",", ":"), sort_keys=True) + "\n")


def signed(point, sign, neg):
    return point if sign == 1 else neg(point)


def combine(parts, sources, signs):
    row = Counter()
    for i, sign in zip(sources, signs):
        for j, coefficient in parts[i].items():
            row[j] += sign * coefficient
    return {j: value for j, value in row.items() if value}


def main():
    selection = json.loads(pinned(PLAN["source_selection"]).read_text())
    previous = json.loads(pinned(PLAN["source_result"]).read_text())
    assert selection["status"] == "CLASSES_FROZEN" and previous["status"] == "COMPLETE"
    assert [x["p"] for x in selection["selected"]] == [x["p"] for x in PLAN["cases"]]
    R = module(PLAN["relation_helpers"], "five_group")
    I = module(PLAN["incremental_module"], "five_rank")
    Ref = module(PLAN["pair_index_reference"], "five_static_four")
    case_dir = HERE / "cases"
    case_dir.mkdir(exist_ok=True)
    output = {"schema": "hecke-d79-support-five-result-v1", "status": "RUNNING", "cases": [],
              "candidate_id": None, "target_online_ms": None}
    save(HERE / "result.json", output)
    for frozen, item, former in zip(selection["selected"], PLAN["cases"], previous["cases"]):
        p, q = frozen["p"], frozen["q"]
        assert (p, q) == (item["p"], former["q"])
        prior = json.loads(pinned(item).read_text())
        assert prior["p"] == p and len(prior["entries"]) == 40
        entries = prior["entries"]
        assert all(x["status"] == "OUTSIDE_CLASS_TRACE" for x in entries)
        neg, add = R.group_law(p)
        points = [tuple(x) for x in frozen["class"]["class_points"]]
        parts = [I.sparse(x["class_part"]) for x in entries]
        totals = []
        for entry in entries:
            total = None
            for trace in entry["outside_traces"]:
                total = add(total, tuple(trace))
            totals.append(total)
        baseline = [I.sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
        four, _ = Ref.hecke_rows_pair_index({i: x for i, x in enumerate(entries)}, points, neg, add)
        assert len(four) == prior["comparisons"]["original"]["verified_rows"]
        basis = I.RankBasis(q, baseline + [I.sparse(x["row"]) for x in four])
        assert basis.rank == former["orders"]["original"]["final_rank_mod_q"]
        baseline_rank = basis.rank
        pairs = defaultdict(list)
        pair_insertions = 0
        for l in range(40):
            for m in range(l + 1, 40):
                for sl, sm in itertools.product((-1, 1), repeat=2):
                    total = add(signed(totals[l], sl, neg), signed(totals[m], sm, neg))
                    pairs[total].append((l, m, sl, sm))
                    pair_insertions += 1
        rows = []
        triple_probes = pair_matches = 0
        status = "COMPLETE"
        started = time.perf_counter_ns()
        for i in range(40):
            if status != "COMPLETE":
                break
            for j in range(i + 1, 40):
                if status != "COMPLETE":
                    break
                for k in range(j + 1, 40):
                    if status != "COMPLETE":
                        break
                    for sj, sk in itertools.product((-1, 1), repeat=2):
                        triple = add(totals[i], add(signed(totals[j], sj, neg),
                                                     signed(totals[k], sk, neg)))
                        triple_probes += 1
                        for l, m, sl, sm in pairs.get(neg(triple), ()):
                            if l <= k:
                                continue
                            pair_matches += 1
                            sources = (i, j, k, l, m)
                            signs = (1, sj, sk, sl, sm)
                            row = combine(parts, sources, signs)
                            check = None
                            for source, coefficient in row.items():
                                for _ in range(abs(coefficient)):
                                    check = add(check, points[source] if coefficient > 0 else neg(points[source]))
                            assert check is None
                            novel = bool(basis.insert(row))
                            rows.append({"sources": sources, "coefficients": signs,
                                         "row": {str(index): value for index, value in sorted(row.items())},
                                         "novel": novel})
                            if len(rows) >= PLAN["row_cap_per_case"]:
                                status = "CENSORED_ROW_CAP"
                                break
                        if status != "COMPLETE":
                            break
                    if (time.perf_counter_ns() - started) / 1e9 >= PLAN["wall_cap_seconds_per_case"]:
                        status = "CENSORED_WALL_CAP"
                        break
        wall_ns = time.perf_counter_ns() - started
        if status == "COMPLETE":
            assert triple_probes == 4 * sum(1 for _ in itertools.combinations(range(40), 3))
        case = {"p": p, "q": q, "status": status, "baseline_rank_with_four": baseline_rank,
                "rank_with_five": basis.rank, "five_rows": len(rows),
                "novel_directions": basis.rank - baseline_rank,
                "pair_insertions": pair_insertions, "triple_probes": triple_probes,
                "pair_matches": pair_matches, "wall_ns": wall_ns,
                "rows": rows, "candidate_id": None, "target_online_ms": None}
        path = case_dir / f"p{p}.json"
        save(path, case)
        output["cases"].append({"p": p, "q": q, "path": path.relative_to(HERE).as_posix(),
                                "sha256": sha(path), "status": status,
                                "baseline_rank_with_four": baseline_rank,
                                "rank_with_five": basis.rank,
                                "five_rows": len(rows), "novel_directions": basis.rank - baseline_rank})
        save(HERE / "result.json", output)
        print(json.dumps(output["cases"][-1]), flush=True)
    output["status"] = "COMPLETE" if all(x["status"] == "COMPLETE" for x in output["cases"]) else "CENSORED"
    save(HERE / "result.json", output)


if __name__ == "__main__":
    main()
