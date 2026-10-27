"""Independent Sage audit of stopped collector rows, ranks, and anchored logs."""
import hashlib
import importlib.util
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, factor, is_prime, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())
POST_SELECTION = json.loads((HERE / "post-selection.json").read_text())
POST_RUN = json.loads((HERE / "post-run.json").read_text())


def sealed(path, digest):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest, str(path)
    return json.loads(raw)


def module(item, name):
    path = ROOT / item["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def sparse(raw):
    return {int(k): int(v) for k, v in raw.items() if v}


def rank(rows, field):
    return int(matrix(field, len(rows), 40, lambda i, j: rows[i].get(j, 0)).rank())


def canonical(rows):
    keys = [(tuple(x["sources"]), tuple(x["coefficients"]),
             tuple(sorted((int(j), int(v)) for j, v in x["row"].items()))) for x in rows]
    assert len(keys) == len(set(keys))
    return sorted(keys)


def main():
    selection = sealed(HERE / "selection.json", POST_SELECTION["selection_sha256"])
    result = sealed(HERE / "result.json", POST_RUN["result_sha256"])
    gate = sealed(ROOT / PLAN["control_gate_result"]["path"], PLAN["control_gate_result"]["sha256"])
    control = next(x for x in gate["selected"] if x["p"] == PLAN["control_p"])
    pair_index = module(PLAN["pair_index_reference"], "stopped_audit_pair")
    direct_index = module(POST_RUN["direct_audit_module"], "stopped_audit_direct")
    helper = module(PLAN["frozen"]["relation_helpers"], "stopped_audit_group")
    assert selection["status"] == "CLASSES_FROZEN" and result["status"] == "COMPLETE"
    found = []
    for v in range(PLAN["v_start"], selection["selected"][-1]["class"]["v"] + 1, 2):
        p = v*v + 316
        if not is_prime(p):
            continue
        curve = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
        n = int(curve.cardinality())
        q = int(max(prime for prime, _ in factor(n)))
        if n % 5 == 0 and (p-1) % 5 != 0 and q >= 53:
            found.append(p)
    assert found == [x["p"] for x in selection["checked_eligible_cases"]]
    assert found == [x["p"] for x in selection["selected"]]
    cases = [("known_success_control", control)] + [("fresh_panel", x) for x in selection["selected"]]
    assert len(cases) == len(result["cases"]) == 1 + PLAN["target_ready_classes"]
    audited = []
    for (cohort, frozen), produced in zip(cases, result["cases"]):
        p, q = frozen["p"], frozen["q"]
        assert (produced["cohort"], produced["p"], produced["q"]) == (cohort, p, q)
        curve = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
        assert int(curve.cardinality()) == frozen["class"]["curve_order"]
        sage_points = [curve(x, y) for x, y in frozen["class"]["class_points"]]
        points = [tuple(x) for x in frozen["class"]["class_points"]]
        assert len(points) == 40
        zero = curve(0)
        for row in frozen["class"]["base_rows"]:
            assert sum((v * sage_points[i] for i, v in sparse(row["row"]).items()), zero) == zero
        direct = direct_index.zero_relations(sage_points)
        assert set(direct) == {(tuple(x["indices"]), tuple(x["coefficients"]))
                               for x in frozen["direct_candidates"]}
        baseline = [sparse(x["row"]) for x in frozen["class"]["base_rows"]]
        baseline += [{i: s for i, s in zip(indices, signs)} for indices, signs in direct]
        field = GF(q)
        base_rank = rank(baseline, field)
        assert base_rank == frozen["baseline_rank_mod_q"] == produced["baseline_rank_mod_q"]
        entries = produced["source_entries"]
        count = produced["stop_source_count"]
        assert len(entries) == len(produced["source_steps"]) == count
        assert [x["source"] for x in entries] == list(range(count))
        assert all(x["status"] == "OUTSIDE_CLASS_TRACE" for x in entries)
        neg, add = helper.group_law(p)
        static, _ = pair_index.hecke_rows_pair_index({x["source"]: x for x in entries}, points, neg, add)
        assert canonical(static) == canonical(produced["relation_rows"])
        assert len(static) == produced["verified_relation_count"]
        for row in produced["relation_rows"]:
            assert sum((v * sage_points[j] for j, v in sparse(row["row"]).items()), zero) == zero
        prior_rank = base_rank
        for k, step in enumerate(produced["source_steps"]):
            assert step["source"] == k and step["source_count"] == k + 1
            prefix = [sparse(row["row"]) for row in produced["relation_rows"] if max(row["sources"]) <= k]
            current = rank(baseline + prefix, field)
            assert current == step["rank_mod_q"]
            assert step["novel_rows"] == current - prior_rank
            assert step["new_rows"] == sum(max(row["sources"]) == k for row in produced["relation_rows"])
            prior_rank = current
        assert prior_rank == produced["final_rank_mod_q"]
        assert produced["lift_sum_ns"] == sum(x["lift_wall_ns"] for x in produced["source_steps"])
        assert produced["index_sum_ns"] == sum(x["index_wall_ns"] for x in produced["source_steps"])
        assert produced["rank_sum_ns"] == sum(x["rank_wall_ns"] for x in produced["source_steps"])
        assert produced["collector_wall_ns"] >= produced["lift_sum_ns"] + produced["index_sum_ns"] + produced["rank_sum_ns"]
        overhead_ns = (produced["collector_wall_ns"] - produced["lift_sum_ns"]
                       - produced["index_sum_ns"] - produced["rank_sum_ns"])
        if produced["rank_goal_status"] == "ACHIEVED":
            assert produced["status"] == "RANK_GOAL_REACHED" and prior_rank == PLAN["rank_goal"]
            assert all(step["rank_mod_q"] < PLAN["rank_goal"] for step in produced["source_steps"][:-1])
            projected = [(frozen["class"]["curve_order"] // q) * point for point in sage_points]
            anchor = produced["anchor_index"]
            T = projected[anchor]
            assert [int(T[0]), int(T[1])] == produced["anchor_point"]
            assert int(T.order()) == q and produced["anchored_log_replay"] == "PASS"
            assert len(produced["anchored_logs"]) == 40
            assert all(log * T == point for log, point in zip(produced["anchored_logs"], projected))
        else:
            assert produced["status"] == "FULL_POOL_BELOW_RANK_GOAL"
            assert produced["rank_goal_status"] == "BOUNDED_BELOW_GOAL" and count == 40
            assert prior_rank < PLAN["rank_goal"]
        cell = {"cohort": cohort, "p": p, "q": q, "status": "PASS", "source_count": count,
                "source_equations_verified": count, "relation_rows_verified": len(static),
                "baseline_rank_mod_q": base_rank, "final_rank_mod_q": prior_rank,
                "rank_goal_status": produced["rank_goal_status"],
                "record_io_and_overhead_ns": overhead_ns,
                "collector_wall_ns": produced["collector_wall_ns"]}
        audited.append(cell)
        print(json.dumps(cell), flush=True)
    out = {"schema": "hecke-d79-rank-stopped-audit-v1", "status": "PASS", "cases": audited}
    (HERE / "audit.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
