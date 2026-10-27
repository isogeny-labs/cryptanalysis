"""Independent Sage replay of fresh-class selection, rows, and frozen order ranks."""
import hashlib
import importlib.util
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, factor, is_prime, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())
POST_SELECTION = json.loads((HERE / "post-selection.json").read_text())
POST_CHALLENGE = json.loads((HERE / "post-challenge.json").read_text())


def sealed(path, digest):
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest, str(path)
    return data


def module(item, name):
    path = ROOT / item["path"]
    sealed(path, item["sha256"])
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def sparse(row):
    return {int(k): int(v) for k, v in row.items() if v}


def rank(rows, field):
    return int(matrix(field, len(rows), 40, lambda i, j: rows[i].get(j, 0)).rank())


def main():
    selection = json.loads(sealed(HERE / "selection.json", POST_SELECTION["selection_sha256"]))
    challenge = json.loads(sealed(HERE / "challenge.json", POST_CHALLENGE["challenge_sha256"]))
    cert = json.loads(sealed(ROOT / PLAN["prior_certificate_result"]["path"],
                             PLAN["prior_certificate_result"]["sha256"]))
    independent = module(POST_CHALLENGE["independent_pair_index"], "transfer_independent_pairs")
    direct_index = module(POST_CHALLENGE["independent_direct_index"], "transfer_independent_direct")
    assert selection["status"] == "ORDERS_FROZEN" and challenge["status"] == "COMPLETE"
    assert len(selection["selected"]) == len(challenge["cases"]) == 2
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
    audited = []
    for frozen, produced in zip(selection["selected"], challenge["cases"]):
        p, q = frozen["p"], frozen["q"]
        assert produced["p"] == p and produced["q"] == q and produced["status"] == "COMPLETE"
        curve = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
        assert int(curve.cardinality()) == frozen["class"]["curve_order"]
        points = [curve(x, y) for x, y in frozen["class"]["class_points"]]
        assert len(points) == 40
        for item in frozen["class"]["base_rows"]:
            assert sum((v*points[i] for i, v in sparse(item["row"]).items()), curve(0)) == curve(0)
        direct = direct_index.zero_relations(points)
        assert set(direct) == {(tuple(x["indices"]), tuple(x["coefficients"]))
                               for x in frozen["direct_candidates"]}
        baseline = [sparse(x["row"]) for x in frozen["class"]["base_rows"]]
        baseline += [{i: s for i, s in zip(indices, signs)} for indices, signs in direct]
        field = GF(q)
        base_rank = rank(baseline, field)
        assert base_rank == frozen["baseline_rank_mod_q"] == produced["baseline_rank_mod_q"]
        entries = produced["source_entries"]
        assert len(entries) == 40 and [x["source"] for x in entries] == list(range(40))
        assert all(x["status"] == "OUTSIDE_CLASS_TRACE" for x in entries)
        rows = independent.independent_rows(entries, points)
        assert len(rows) == produced["hecke_candidate_count"]
        full_rank = rank(baseline + [row for _, row in rows], field)
        assert full_rank == produced["full_pool_rank_mod_q"]
        priority = cert["inclusion_minimal_source_ids"]
        expected = {
            "ascending": list(range(40)),
            "certificate_first": priority + [i for i in range(40) if i not in priority],
            "sha": sorted(range(40), key=lambda i: (hashlib.sha256(f"d79-order-transfer-v1:{p}:{i}".encode()).hexdigest(), i)),
        }
        assert frozen["source_orders"] == expected
        first_by_order = {}
        rank_sums = {}
        for name, order in expected.items():
            reported = produced["order_results"][name]
            prefixes = reported["prefixes"]
            assert len(prefixes) == 41
            for count in range(41):
                seen = set(order[:count])
                subset = [row for support, row in rows if set(support) <= seen]
                assert prefixes[count]["source_count"] == count
                assert prefixes[count]["hecke_rows"] == len(subset)
                assert prefixes[count]["rank_mod_q"] == rank(baseline + subset, field)
                assert prefixes[count]["lift_sum_ns"] == sum(entries[i]["lift_wall_ns"] for i in seen)
            first = next((x["source_count"] for x in prefixes if x["rank_mod_q"] >= PLAN["rank_goal"]), None)
            assert first == reported["first_rank_goal_source_count"]
            first_by_order[name] = first
            rank_sums[name] = sum(x["rank_mod_q"] - base_rank for x in prefixes[1:])
        audited.append({"p": p, "q": q, "status": "PASS", "source_equations_verified": 40,
                        "hecke_rows_verified": len(rows), "baseline_rank_mod_q": base_rank,
                        "full_pool_rank_mod_q": full_rank, "first_rank39_source_count": first_by_order,
                        "rank_gain_prefix_sum": rank_sums})
        print(json.dumps({"p": p, "status": "PASS", "full_rank": full_rank,
                          "rank_gain_prefix_sum": rank_sums}), flush=True)
    out = {"schema": "hecke-d79-source-order-transfer-audit-v1", "status": "PASS",
           "cases": audited}
    (HERE / "audit.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
