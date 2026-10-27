"""Independent Sage audit of live support-five journals and rank stops."""
import hashlib
import importlib.util
import itertools
import json
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

from sage.all import EllipticCurve, GF, factor, is_prime, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())
POST_SELECTION = json.loads((HERE / "post-selection.json").read_text())
PRE = json.loads((HERE / "pre-run.json").read_text())
POST = json.loads((HERE / "post-run.json").read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned(item, name=None):
    path = ROOT / item["path"]
    assert sha(path) == item["sha256"]
    if name is None:
        return path
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def sparse(raw):
    return {int(j): int(v) for j, v in raw.items() if v}


def rank(rows, q):
    F = GF(q)
    return int(matrix(F, len(rows), 40, lambda i, j: rows[i].get(j, 0)).rank())


def canonical(rows):
    keys = [(tuple(x["sources"]), tuple(x["coefficients"]),
             tuple(sorted(sparse(x["row"]).items()))) for x in rows]
    assert len(keys) == len(set(keys))
    return sorted(keys)


def five_rows(entries, points, zero):
    totals = [sum((points[0].curve()(x, y) for x, y in entry["outside_traces"]), zero)
              for entry in entries]
    triples = defaultdict(list)
    for i, j, k in itertools.combinations(range(len(entries)), 3):
        for sj, sk in itertools.product((-1, 1), repeat=2):
            triples[totals[i] + sj*totals[j] + sk*totals[k]].append((i, j, k, sj, sk))
    out = []
    for l, m in itertools.combinations(range(len(entries)), 2):
        for sl, sm in itertools.product((-1, 1), repeat=2):
            need = -(sl*totals[l] + sm*totals[m])
            for i, j, k, sj, sk in triples.get(need, ()):
                if k >= l:
                    continue
                sources = (i, j, k, l, m)
                signs = (1, sj, sk, sl, sm)
                row = Counter()
                for source, sign in zip(sources, signs):
                    for column, coefficient in sparse(entries[source]["class_part"]).items():
                        row[column] += sign*coefficient
                row = {column: coefficient for column, coefficient in row.items() if coefficient}
                assert sum((coefficient*points[column] for column, coefficient in row.items()), zero) == zero
                out.append({"sources": sources, "coefficients": signs, "row": row})
    return out


def main():
    for path, digest in (("selection.json", POST_SELECTION["selection_sha256"]),
                         ("inputs.json", POST_SELECTION["inputs_sha256"]),
                         ("select_sage.py", POST_SELECTION["selector_sha256"]),
                         ("post-selection.json", PRE["post_selection_sha256"]),
                         ("preflight.json", PRE["preflight_sha256"]),
                         ("preflight_sage.py", PRE["preflight_source_sha256"]),
                         ("live_index.py", PRE["live_index_sha256"]),
                         ("run_sage.py", PRE["runner_sha256"]),
                         ("PROTOCOL.md", PRE["protocol_sha256"]),
                         ("sage-runtime-info.txt", PRE["sage_runtime_info_sha256"]),
                         ("pre-run.json", POST["pre_run_sha256"]),
                         ("index.json", POST["index_sha256"]),
                         ("run-stdout.jsonl", POST["stdout_sha256"]),
                         ("run-stderr.txt", POST["stderr_sha256"])):
        assert sha(HERE / path) == digest, path
    selection = json.loads((HERE / "selection.json").read_text())
    index = json.loads((HERE / "index.json").read_text())
    assert selection["status"] == "CLASSES_FROZEN" and index["status"] == "COMPLETE"
    found = []
    for v in range(PLAN["v_start"], selection["selected"][-1]["class"]["v"] + 1, 2):
        p = v*v + 316
        if not is_prime(p):
            continue
        E = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
        n = int(E.cardinality())
        q = int(max(prime for prime, _ in factor(n)))
        if n % 5 == 0 and (p-1) % 5 != 0 and q >= 53:
            found.append(p)
    assert found == [x["p"] for x in selection["checked_eligible_cases"]]
    assert found == [x["p"] for x in selection["selected"]]
    gate = json.loads(pinned(PLAN["control_gate_result"]).read_text())
    control = next(x for x in gate["selected"] if x["p"] == PLAN["control_p"])
    cases = [("known_control", control)] + [("fresh", x) for x in selection["selected"]]
    assert len(cases) == len(index["cases"]) == 9
    ref = pinned(PLAN["pair_index_reference"], "live_five_audit_four")
    helper = pinned(PLAN["frozen"]["relation_helpers"], "live_five_audit_group")
    direct_info = json.loads((HERE.parent / "hecke-d79-compact-checkpoints-20261027" / "post-run.json").read_text())
    direct = pinned(direct_info["direct_audit_module"], "live_five_audit_direct")
    audited = []
    for (cohort, frozen), item in zip(cases, index["cases"]):
        p, q = frozen["p"], frozen["q"]
        assert (item["cohort"], item["p"], item["q"]) == (cohort, p, q)
        journal_path = HERE / item["journal"]
        summary_path = HERE / item["summary"]
        assert sha(journal_path) == item["journal_sha256"]
        assert sha(summary_path) == item["summary_sha256"]
        records = [json.loads(line) for line in journal_path.read_text().splitlines()]
        summary = json.loads(summary_path.read_text())
        assert len(records) == summary["source_count"] == item["source_count"]
        E = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
        assert int(E.cardinality()) == frozen["class"]["curve_order"]
        points = [E(x, y) for x, y in frozen["class"]["class_points"]]
        point_tuples = [tuple(x) for x in frozen["class"]["class_points"]]
        zero = E(0)
        baseline = [sparse(x["row"]) for x in frozen["class"]["base_rows"]]
        for row in baseline:
            assert sum((v*points[j] for j, v in row.items()), zero) == zero
        direct_set = direct.zero_relations(points)
        assert set(direct_set) == {(tuple(x["indices"]), tuple(x["coefficients"]))
                                   for x in frozen["direct_candidates"]}
        baseline += [{j: v for j, v in zip(indices, signs)} for indices, signs in direct_set]
        prior_rank = rank(baseline, q)
        assert prior_rank == frozen["baseline_rank_mod_q"] == summary["baseline_rank_mod_q"]
        entries = []
        for k, record in enumerate(records):
            entry = record["entry"]
            assert record["source"] == entry["source"] == k
            assert entry["status"] == record["step_status"] == "OUTSIDE_CLASS_TRACE" or (
                entry["status"] == "OUTSIDE_CLASS_TRACE" and record["step_status"] == "COMPLETE")
            assert record["step_status"] == "COMPLETE"
            outside = sum((E(x, y) for x, y in entry["outside_traces"]), zero)
            part = sum((v*points[j] for j, v in sparse(entry["class_part"]).items()), zero)
            assert outside + part == zero
            entries.append(entry)
        neg, add = helper.group_law(p)
        static_four, _ = ref.hecke_rows_pair_index({i: entry for i, entry in enumerate(entries)},
                                                    point_tuples, neg, add)
        static_five = five_rows(entries, points, zero)
        assert canonical(static_four) == canonical([row for r in records for row in r["four_rows"]])
        assert canonical(static_five) == canonical([row for r in records for row in r["five_rows"]])
        four_prefix = five_prefix = []
        total_four = total_five = 0
        for k, record in enumerate(records):
            new_four = [x for x in static_four if max(x["sources"]) == k]
            new_five = [x for x in static_five if max(x["sources"]) == k]
            assert canonical(new_four) == canonical(record["four_rows"])
            assert canonical(new_five) == canonical(record["five_rows"])
            assert record["four_metrics"]["new_verified_rows"] == len(new_four)
            assert record["four_metrics"]["pair_insertions"] == 2*k
            assert record["five_metrics"]["pair_matches"] == len(new_five)
            assert record["five_metrics"]["pair_insertions"] == 2*k
            assert record["five_metrics"]["triple_probes"] == 8*comb(k, 2)
            after_four = rank(baseline + four_prefix + five_prefix + [sparse(x["row"]) for x in new_four], q)
            after_five = rank(baseline + four_prefix + five_prefix +
                              [sparse(x["row"]) for x in new_four + new_five], q)
            assert record["novel_four"] == after_four - prior_rank
            assert record["novel_five"] == after_five - after_four
            assert record["rank_mod_q"] == after_five
            prior_rank = after_five
            four_prefix = four_prefix + [sparse(x["row"]) for x in new_four]
            five_prefix = five_prefix + [sparse(x["row"]) for x in new_five]
            total_four += len(new_four)
            total_five += len(new_five)
        assert prior_rank == summary["final_rank_mod_q"] == item["final_rank_mod_q"]
        assert total_four == summary["four_rows"] and total_five == summary["five_rows"]
        assert summary["novel_four"] == sum(x["novel_four"] for x in records)
        assert summary["novel_five"] == sum(x["novel_five"] for x in records)
        phases = summary["checkpoint_phase_times"]
        assert [x["source"] for x in phases] == list(range(len(records)))
        for name, field in (("lift_sum_ns", "lift_wall_ns"), ("four_sum_ns", "four_wall_ns"),
                            ("five_sum_ns", "five_wall_ns"), ("rank_sum_ns", "rank_wall_ns")):
            assert summary[name] == sum(x[field] for x in records)
        assert summary["checkpoint_sum_ns"] == sum(x["checkpoint_wall_ns"] for x in phases)
        assert summary["loop_overhead_ns"] >= 0
        assert summary["collector_wall_ns"] == sum(summary[x] for x in
            ("lift_sum_ns", "four_sum_ns", "five_sum_ns", "rank_sum_ns",
             "checkpoint_sum_ns", "loop_overhead_ns"))
        if summary["status"] == "RANK_GOAL_REACHED":
            assert prior_rank == PLAN["rank_goal"] and all(x["rank_mod_q"] < prior_rank for x in records[:-1])
            projected = [(frozen["class"]["curve_order"] // q) * point for point in points]
            T = projected[summary["anchor_index"]]
            assert int(T.order()) == q
            assert [int(T[0]), int(T[1])] == summary["anchor_point"]
            assert all(log*T == point for log, point in zip(summary["anchored_logs"], projected))
            assert summary["anchored_log_replay"] == "PASS"
        else:
            assert summary["status"] == "FULL_POOL_BELOW_RANK_GOAL"
            assert len(records) == 40 and prior_rank < PLAN["rank_goal"]
        audited.append({"cohort": cohort, "p": p, "q": q, "source_equations": len(entries),
                        "four_rows": total_four, "five_rows": total_five,
                        "final_rank": prior_rank, "status": "PASS"})
        print(json.dumps(audited[-1]), flush=True)
    (HERE / "audit.json").write_text(json.dumps({"schema": "hecke-d79-live-five-audit-v1",
                                                 "status": "PASS", "cases": audited},
                                                indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
