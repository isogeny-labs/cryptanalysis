"""Independent Sage and static-pair audit of the prospective priority panel."""
import hashlib
import importlib.util
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, factor, is_prime, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())
POST = json.loads((HERE / "post-selection.json").read_text())
RUN = json.loads((HERE / "post-run.json").read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned(item, name):
    path = ROOT / item["path"]
    assert sha(path) == item["sha256"]
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def sparse(raw):
    return {int(k): int(v) for k, v in raw.items() if v}


def rank(rows, q):
    F = GF(q)
    return int(matrix(F, len(rows), 40, lambda i, j: rows[i].get(j, 0)).rank())


def main():
    pre = json.loads((HERE / "pre-run.json").read_text())
    assert sha(HERE / "post-selection.json") == pre["post_selection_sha256"]
    assert sha(HERE / "run_sage.py") == pre["runner_sha256"]
    assert sha(HERE / "PROTOCOL.md") == pre["protocol_sha256"]
    assert sha(HERE / "inputs.json") == POST["inputs_sha256"]
    assert sha(HERE / "select_sage.py") == POST["selector_sha256"]
    assert sha(HERE / "selection.json") == POST["selection_sha256"]
    assert sha(HERE / "result.json") == RUN["result_sha256"]
    assert sha(HERE / "pre-run.json") == RUN["pre_run_sha256"]
    assert sha(HERE / "run-stdout.jsonl") == RUN["stdout_sha256"]
    assert sha(HERE / "run-stderr.txt") == RUN["stderr_sha256"]
    selection = json.loads((HERE / "selection.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert selection["status"] == "CLASSES_FROZEN" and result["status"] == "COMPLETE"
    assert len(selection["selected"]) == len(result["cases"]) == PLAN["target_ready_classes"]
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
    ref = pinned(PLAN["pair_index_reference"], "priority_audit_static_pair")
    helper = pinned(PLAN["frozen"]["relation_helpers"], "priority_audit_group")
    direct_info = json.loads((HERE.parent / "hecke-d79-compact-checkpoints-20261027" / "post-run.json").read_text())
    direct = pinned(direct_info["direct_audit_module"], "priority_audit_direct")
    audited = []
    for frozen, item in zip(selection["selected"], result["cases"]):
        p, q = frozen["p"], frozen["q"]
        assert (item["p"], item["q"]) == (p, q)
        case_path = HERE / item["path"]
        assert sha(case_path) == item["sha256"]
        case = json.loads(case_path.read_text())
        assert (case["p"], case["q"]) == (p, q)
        E = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
        assert int(E.cardinality()) == frozen["class"]["curve_order"]
        sage_points = [E(x, y) for x, y in frozen["class"]["class_points"]]
        points = [tuple(x) for x in frozen["class"]["class_points"]]
        zero = E(0)
        baseline = [sparse(x["row"]) for x in frozen["class"]["base_rows"]]
        for row in baseline:
            assert sum((v * sage_points[j] for j, v in row.items()), zero) == zero
        direct_set = direct.zero_relations(sage_points)
        assert set(direct_set) == {(tuple(x["indices"]), tuple(x["coefficients"]))
                                   for x in frozen["direct_candidates"]}
        baseline += [{j: v for j, v in zip(indices, signs)} for indices, signs in direct_set]
        assert rank(baseline, q) == frozen["baseline_rank_mod_q"] == case["baseline_rank"]
        incidence = [0] * 40
        for row in frozen["class"]["base_rows"] + frozen["direct_candidates"]:
            for j, v in row["row"].items():
                if v:
                    incidence[int(j)] += 1
        assert incidence == frozen["baseline_incidence"]
        expected_orders = {"original": list(range(40)),
                           "low_incidence": sorted(range(40), key=lambda j: (incidence[j], j))}
        assert case["source_orders"] == frozen["source_orders"] == expected_orders
        entries = case["entries"]
        assert len(entries) == 40
        for i, entry in enumerate(entries):
            assert entry["source"] == i and entry["status"] == "OUTSIDE_CLASS_TRACE"
            outside = sum((E(x, y) for x, y in entry["outside_traces"]), zero)
            class_part = sum((v * sage_points[j] for j, v in sparse(entry["class_part"]).items()), zero)
            assert outside + class_part == zero
        neg, add = helper.group_law(p)
        comparisons = {}
        for name, order in expected_orders.items():
            produced = case["comparisons"][name]
            count = produced["stop_prefix"]
            assert count == len(produced["steps"])
            ordered = {k: {**entries[source], "source": k} for k, source in enumerate(order[:count])}
            rows, _ = ref.hecke_rows_pair_index(ordered, points, neg, add)
            assert len(rows) == produced["verified_rows"]
            for row in rows:
                assert sum((v * sage_points[j] for j, v in sparse(row["row"]).items()), zero) == zero
            prior = rank(baseline, q)
            for k, step in enumerate(produced["steps"]):
                prefix_rows = [sparse(x["row"]) for x in rows if max(x["sources"]) <= k]
                current = rank(baseline + prefix_rows, q)
                new_count = sum(max(x["sources"]) == k for x in rows)
                assert step["prefix"] == k + 1 and step["original_source"] == order[k]
                assert step["new_rows"] == step["new_verified_rows"] == new_count
                assert step["novel_rows"] == current - prior
                assert step["rank_mod_q"] == current
                assert step["pair_insertions"] == 2*k and step["bucket_probes"] == 2+4*k
                prior = current
            assert prior == produced["final_rank_mod_q"]
            assert prior - frozen["baseline_rank_mod_q"] == produced["novel_rows"]
            assert item["orders"][name] == {"status": produced["status"], "stop_prefix": count,
                                             "final_rank_mod_q": prior}
            if produced["status"] == "RANK_GOAL_REACHED":
                assert prior == PLAN["rank_goal"] and all(x["rank_mod_q"] < prior for x in produced["steps"][:-1])
                anchor = produced["anchor"]
                projected = [(frozen["class"]["curve_order"] // q) * point for point in sage_points]
                T = projected[anchor["anchor_index"]]
                assert int(T.order()) == q and anchor["replay"] == "PASS"
                assert all(log*T == point for log, point in zip(anchor["anchored_logs"], projected))
            else:
                assert produced["status"] == "FULL_POOL_BELOW_RANK_GOAL"
                assert count == 40 and prior < PLAN["rank_goal"]
            comparisons[name] = {"status": produced["status"], "final_rank": prior,
                                 "verified_rows": len(rows), "first_rank_gain_prefix": next(
                                     (x["prefix"] for x in produced["steps"] if x["novel_rows"]), None)}
        audited.append({"p": p, "q": q, "source_equations": len(entries),
                        "baseline_rank": frozen["baseline_rank_mod_q"], "orders": comparisons})
        print(json.dumps(audited[-1]), flush=True)
    (HERE / "audit.json").write_text(json.dumps({"schema": "hecke-d79-source-priority-audit-v1",
                                                 "status": "PASS", "cases": audited},
                                                indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
