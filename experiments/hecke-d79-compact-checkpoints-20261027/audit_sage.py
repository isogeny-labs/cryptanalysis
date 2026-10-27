"""Independent Sage audit of append-only case journals and charged accounting."""
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
    index = sealed(HERE / "index.json", POST_RUN["index_sha256"])
    gate = sealed(ROOT / PLAN["control_gate_result"]["path"], PLAN["control_gate_result"]["sha256"])
    control = next(x for x in gate["selected"] if x["p"] == PLAN["control_p"])
    pair_index = module(PLAN["pair_index_reference"], "compact_audit_pair")
    direct_index = module(POST_RUN["direct_audit_module"], "compact_audit_direct")
    helper = module(PLAN["frozen"]["relation_helpers"], "compact_audit_group")
    assert selection["status"] == "CLASSES_FROZEN" and index["status"] == "COMPLETE"
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
    assert len(cases) == len(index["cases"]) == 1 + PLAN["target_ready_classes"]
    audited = []
    for (cohort, frozen), item in zip(cases, index["cases"]):
        p, q = frozen["p"], frozen["q"]
        assert (item["cohort"], item["p"], item["q"]) == (cohort, p, q)
        assert item["journal"] == f"cases/p{p}.jsonl"
        assert item["summary"] == f"cases/p{p}-summary.json"
        journal_path, summary_path = HERE / item["journal"], HERE / item["summary"]
        assert hashlib.sha256(journal_path.read_bytes()).hexdigest() == item["journal_sha256"]
        summary = sealed(summary_path, item["summary_sha256"])
        records = [json.loads(line) for line in journal_path.read_text().splitlines() if line]
        assert (summary["cohort"], summary["p"], summary["q"]) == (cohort, p, q)
        assert len(records) == summary["source_count"] == item["source_count"]
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
        assert base_rank == summary["baseline_rank_mod_q"] == frozen["baseline_rank_mod_q"]
        entries, emitted = [], []
        prior_rank = base_rank
        for k, record in enumerate(records):
            assert record["source"] == record["entry"]["source"] == k
            assert record["entry"]["status"] == "OUTSIDE_CLASS_TRACE"
            entries.append(record["entry"])
            assert record["lift_wall_ns"] == record["entry"]["lift_wall_ns"]
            assert record["new_verified_rows"] == len(record["new_rows"])
            assert all(max(row["sources"]) == k for row in record["new_rows"])
            emitted.extend(record["new_rows"])
            for row in record["new_rows"]:
                assert sum((v * sage_points[j] for j, v in sparse(row["row"]).items()), zero) == zero
            current = rank(baseline + [sparse(row["row"]) for row in emitted], field)
            assert record["rank_mod_q"] == current
            assert record["novel_rows"] == current - prior_rank
            assert record["pair_insertions"] == 2*k
            assert record["bucket_probes"] == 2+4*k
            prior_rank = current
        neg, add = helper.group_law(p)
        static, _ = pair_index.hecke_rows_pair_index({x["source"]: x for x in entries}, points, neg, add)
        assert canonical(static) == canonical(emitted)
        assert len(emitted) == summary["verified_relation_count"]
        assert prior_rank == summary["final_rank_mod_q"]
        phase_times = summary["checkpoint_phase_times"]
        assert [x["source"] for x in phase_times] == list(range(len(records)))
        assert summary["lift_sum_ns"] == sum(x["lift_wall_ns"] for x in records)
        assert summary["index_sum_ns"] == sum(x["index_wall_ns"] for x in records)
        assert summary["rank_sum_ns"] == sum(x["rank_wall_ns"] for x in records)
        assert summary["checkpoint_sum_ns"] == sum(x["checkpoint_wall_ns"] for x in phase_times)
        assert summary["loop_overhead_ns"] >= 0
        assert summary["collector_wall_ns"] == (summary["lift_sum_ns"] + summary["index_sum_ns"] +
                                                  summary["rank_sum_ns"] + summary["checkpoint_sum_ns"] +
                                                  summary["loop_overhead_ns"])
        if summary["rank_goal_status"] == "ACHIEVED":
            assert summary["status"] == "RANK_GOAL_REACHED" and prior_rank == PLAN["rank_goal"]
            assert all(x["rank_mod_q"] < PLAN["rank_goal"] for x in records[:-1])
            projected = [(frozen["class"]["curve_order"] // q) * point for point in sage_points]
            anchor = summary["anchor_index"]
            T = projected[anchor]
            assert [int(T[0]), int(T[1])] == summary["anchor_point"]
            assert int(T.order()) == q and summary["anchored_log_replay"] == "PASS"
            assert len(summary["anchored_logs"]) == 40
            assert all(log*T == point for log, point in zip(summary["anchored_logs"], projected))
        else:
            assert summary["status"] == "FULL_POOL_BELOW_RANK_GOAL"
            assert summary["rank_goal_status"] == "BOUNDED_BELOW_GOAL"
            assert len(records) == 40 and prior_rank < PLAN["rank_goal"]
        cell = {"cohort": cohort, "p": p, "q": q, "status": "PASS",
                "source_equations_verified": len(entries), "relation_rows_verified": len(emitted),
                "baseline_rank_mod_q": base_rank, "final_rank_mod_q": prior_rank,
                "rank_goal_status": summary["rank_goal_status"],
                "source_count": len(entries), "collector_wall_ns": summary["collector_wall_ns"],
                "checkpoint_sum_ns": summary["checkpoint_sum_ns"],
                "loop_overhead_ns": summary["loop_overhead_ns"]}
        audited.append(cell)
        print(json.dumps(cell), flush=True)
    out = {"schema": "hecke-d79-compact-checkpoints-audit-v1", "status": "PASS", "cases": audited}
    (HERE / "audit.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
