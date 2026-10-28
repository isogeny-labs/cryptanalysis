"""Independent Sage audit of live support-four through eight journals."""
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


class DenseRank:
    """Independent dense modular elimination for all journal prefixes."""

    def __init__(self, q, rows):
        self.q = q
        self.pivots = {}
        for row in rows:
            self.add(row)

    @property
    def rank(self):
        return len(self.pivots)

    def add(self, row):
        q = self.q
        value = [row.get(j, 0) % q for j in range(40)]
        for column in sorted(self.pivots):
            coefficient = value[column]
            if coefficient:
                pivot = self.pivots[column]
                value = [(x - coefficient * y) % q for x, y in zip(value, pivot)]
        column = next((j for j, x in enumerate(value) if x), None)
        if column is None:
            return False
        inverse = pow(value[column], -1, q)
        self.pivots[column] = [(x * inverse) % q for x in value]
        return True


def canonical(rows):
    keys = [(tuple(x["sources"]), tuple(x["coefficients"]),
             tuple(sorted(sparse(x["row"]).items()))) for x in rows]
    assert len(keys) == len(set(keys))
    return sorted(keys)


def signed_rows(entries, points, zero, first_count, last_count):
    """Independent Sage split: first sign fixed +, all others signed."""
    n = len(entries)
    totals = [sum((points[0].curve()(x, y) for x, y in entry["outside_traces"]), zero)
              for entry in entries]
    first = defaultdict(list)
    for indices in itertools.combinations(range(n), first_count):
        for signs_rest in itertools.product((-1, 1), repeat=first_count-1):
            signs = (1,) + signs_rest
            total = sum((sign*totals[i] for i, sign in zip(indices, signs)), zero)
            first[total].append((indices, signs))
    rows = []
    for later in itertools.combinations(range(n), last_count):
        for signs in itertools.product((-1, 1), repeat=last_count):
            need = -sum((sign*totals[i] for i, sign in zip(later, signs)), zero)
            for earlier, earlier_signs in first.get(need, ()):
                if earlier[-1] >= later[0]:
                    continue
                sources = earlier + later
                coefficients = earlier_signs + signs
                row = Counter()
                for source, sign in zip(sources, coefficients):
                    for column, value in sparse(entries[source]["class_part"]).items():
                        row[column] += sign*value
                row = {column: value for column, value in row.items() if value}
                assert sum((value*points[column] for column, value in row.items()), zero) == zero
                rows.append({"sources": sources, "coefficients": coefficients, "row": row})
    return rows


def independent_eight_rows(entries, encoded_points, neg, add):
    """Independent four-plus-four enumeration using the affine group law."""
    n = len(entries)
    totals = []
    for entry in entries:
        total = None
        for raw in entry["outside_traces"]:
            total = add(total, tuple(raw))
        totals.append(total)
    first = defaultdict(list)
    for ids in itertools.combinations(range(n), 4):
        for rest in itertools.product((-1, 1), repeat=3):
            signs = (1,) + rest
            total = None
            for i, sign in zip(ids, signs):
                total = add(total, totals[i] if sign == 1 else neg(totals[i]))
            first[total].append((ids, signs))
    rows = []
    for latter in itertools.combinations(range(n), 4):
        for latter_signs in itertools.product((-1, 1), repeat=4):
            total = None
            for i, sign in zip(latter, latter_signs):
                total = add(total, totals[i] if sign == 1 else neg(totals[i]))
            for earlier, earlier_signs in first.get(neg(total), ()):
                if earlier[-1] >= latter[0]:
                    continue
                sources = earlier + latter
                signs = earlier_signs + latter_signs
                row = Counter()
                for source, sign in zip(sources, signs):
                    for j, value in sparse(entries[source]["class_part"]).items():
                        row[j] += sign * value
                row = {j: value for j, value in row.items() if value}
                check = None
                for j, value in row.items():
                    for _ in range(abs(value)):
                        check = add(check, encoded_points[j] if value > 0 else neg(encoded_points[j]))
                assert check is None
                rows.append({"sources": sources, "coefficients": signs, "row": row})
    return rows


def main():
    for name, digest in (("selection.json", POST_SELECTION["selection_sha256"]),
                         ("inputs.json", POST_SELECTION["inputs_sha256"]),
                         ("select_sage.py", POST_SELECTION["selector_sha256"]),
                         ("post-selection.json", PRE["post_selection_sha256"]),
                         ("preflight.json", PRE["preflight_sha256"]),
                         ("preflight_sage.py", PRE["preflight_source_sha256"]),
                         ("wide_index.py", PRE["wide_index_sha256"]),
                         ("eight_index.py", PRE["eight_index_sha256"]),
                         ("run_sage.py", PRE["runner_sha256"]),
                         ("PROTOCOL.md", PRE["protocol_sha256"]),
                         ("sage-runtime-info.txt", PRE["sage_runtime_info_sha256"]),
                         ("pre-run.json", POST["pre_run_sha256"]),
                         ("index.json", POST["index_sha256"]),
                         ("run-stdout.jsonl", POST["stdout_sha256"]),
                         ("run-stderr.txt", POST["stderr_sha256"])):
        assert sha(HERE / name) == digest, name
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
    prior_selection = json.loads(pinned(PLAN["preflight_support_eight_selection"]).read_text())
    control = next(x for x in prior_selection["selected"] if x["p"] == PLAN["control_p"])
    cases = [("known_control", control)] + [("fresh", x) for x in selection["selected"]]
    assert len(cases) == len(index["cases"]) == 9
    ref = pinned(PLAN["pair_index_reference"], "live_seven_audit_four")
    helper = pinned(PLAN["frozen"]["relation_helpers"], "live_seven_audit_group")
    direct_info = json.loads((HERE.parent / "hecke-d79-compact-checkpoints-20261027" / "post-run.json").read_text())
    direct = pinned(direct_info["direct_audit_module"], "live_seven_audit_direct")
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
        encoded = [tuple(x) for x in frozen["class"]["class_points"]]
        zero = E(0)
        baseline = [sparse(x["row"]) for x in frozen["class"]["base_rows"]]
        assert all(sum((v*points[j] for j, v in row.items()), zero) == zero for row in baseline)
        direct_set = direct.zero_relations(points)
        assert set(direct_set) == {(tuple(x["indices"]), tuple(x["coefficients"]))
                                   for x in frozen["direct_candidates"]}
        baseline += [{j: v for j, v in zip(indices, signs)} for indices, signs in direct_set]
        current_rank = rank(baseline, q)
        assert current_rank == frozen["baseline_rank_mod_q"] == summary["baseline_rank_mod_q"]
        entries = []
        for k, record in enumerate(records):
            entry = record["entry"]
            assert record["source"] == entry["source"] == k
            assert entry["status"] == "OUTSIDE_CLASS_TRACE" and record["step_status"] == "COMPLETE"
            outside = sum((E(x, y) for x, y in entry["outside_traces"]), zero)
            part = sum((v*points[j] for j, v in sparse(entry["class_part"]).items()), zero)
            assert outside + part == zero
            entries.append(entry)
        neg, add = helper.group_law(p)
        expected = {}
        expected["four"], _ = ref.hecke_rows_pair_index({i: x for i, x in enumerate(entries)}, encoded, neg, add)
        expected["five"] = signed_rows(entries, points, zero, 3, 2)
        expected["six"] = signed_rows(entries, points, zero, 4, 2)
        expected["seven"] = signed_rows(entries, points, zero, 4, 3)
        expected["eight"] = independent_eight_rows(entries, encoded, neg, add)
        for name in ("four", "five", "six", "seven", "eight"):
            assert canonical(expected[name]) == canonical([row for record in records for row in record["rows"][name]])
        accumulated = list(baseline)
        accumulated_eight = list(baseline)
        basis_seven = DenseRank(q, baseline)
        basis_eight = DenseRank(q, baseline)
        assert basis_seven.rank == basis_eight.rank == current_rank
        first_seven = first_eight = None
        count = {name: 0 for name in expected}
        for k, record in enumerate(records):
            for name in ("four", "five", "six", "seven"):
                new_rows = [row for row in expected[name] if max(row["sources"]) == k]
                assert canonical(new_rows) == canonical(record["rows"][name])
                novel = 0
                for relation in new_rows:
                    row = sparse(relation["row"])
                    novel += bool(basis_seven.add(row))
                    basis_eight.add(row)
                    accumulated.append(row)
                    accumulated_eight.append(row)
                assert record["novel"][name] == novel
                count[name] += len(new_rows)
            new_eight = [row for row in expected["eight"] if max(row["sources"]) == k]
            assert canonical(new_eight) == canonical(record["rows"]["eight"])
            novel_eight = 0
            for relation in new_eight:
                row = sparse(relation["row"])
                novel_eight += bool(basis_eight.add(row))
                accumulated_eight.append(row)
            assert record["novel_eight"] == novel_eight
            count["eight"] += len(new_eight)
            assert record["rank_mod_q"] == basis_seven.rank
            assert record["rank_eight_mod_q"] == basis_eight.rank
            if basis_seven.rank == 39 and first_seven is None:
                first_seven = k + 1
            if basis_eight.rank == 39 and first_eight is None:
                first_eight = k + 1
            assert record["four_metrics"]["pair_insertions"] == 2*k
            assert record["five_metrics"]["pair_insertions"] == 2*k
            assert record["five_metrics"]["triple_probes"] == 8*comb(k, 2)
            wide = record["wide_metrics"]
            assert wide["status"] == "COMPLETE"
            assert wide["six_probes"] == 8*comb(k, 2)
            assert wide["seven_probes"] == 16*comb(k, 3)
            assert wide["triple_insertions"] == 4*comb(k, 2)
            assert wide["six_matches"] == len(record["rows"]["six"])
            assert wide["seven_matches"] == len(record["rows"]["seven"])
            assert record["wide_wall_ns"] >= sum(wide[x] for x in
                ("six_wall_ns", "seven_wall_ns", "triple_update_wall_ns"))
            eight = record["eight_metrics"]
            assert eight["status"] == "COMPLETE"
            assert eight["step_probes"] == 32*comb(k, 4)
            assert eight["matches"] == len(record["rows"]["eight"])
            assert eight["triple_insertions"] == 4*comb(k, 2)
            assert record["eight_wall_ns"] >= sum(eight[x] for x in
                ("query_wall_ns", "triple_update_wall_ns"))
        current_rank = rank(accumulated, q)
        current_eight = rank(accumulated_eight, q)
        assert current_rank == basis_seven.rank == summary["final_rank_mod_q"] == item["final_rank_mod_q"]
        assert current_eight == basis_eight.rank == summary["final_rank_eight_mod_q"] == item["final_rank_eight_mod_q"]
        assert first_seven == summary["first_seven_source_count"] == item["first_seven_source_count"]
        assert first_eight == summary["first_eight_source_count"] == item["first_eight_source_count"]
        assert count == summary["row_counts"]
        directions = {name: sum(r["novel"][name] for r in records)
                      for name in ("four", "five", "six", "seven")}
        directions["eight"] = sum(r["novel_eight"] for r in records)
        assert summary["novel_directions"] == directions
        for name, field in (("lift_sum_ns", "lift_wall_ns"), ("four_sum_ns", "four_wall_ns"),
                            ("five_sum_ns", "five_wall_ns"), ("wide_sum_ns", "wide_wall_ns"),
                            ("eight_sum_ns", "eight_wall_ns"), ("rank_sum_ns", "rank_wall_ns")):
            assert summary[name] == sum(r[field] for r in records)
        assert summary["six_sum_ns"] == sum(r["wide_metrics"]["six_wall_ns"] for r in records)
        assert summary["seven_sum_ns"] == sum(r["wide_metrics"]["seven_wall_ns"] for r in records)
        assert summary["triple_update_sum_ns"] == sum(r["wide_metrics"]["triple_update_wall_ns"] for r in records)
        assert summary["wide_setup_sum_ns"] == summary["wide_sum_ns"] - sum(summary[x] for x in
            ("six_sum_ns", "seven_sum_ns", "triple_update_sum_ns"))
        phases = summary["checkpoint_phase_times"]
        assert [x["source"] for x in phases] == list(range(len(records)))
        assert summary["checkpoint_sum_ns"] == sum(x["checkpoint_wall_ns"] for x in phases)
        assert summary["loop_overhead_ns"] >= 0
        assert summary["collector_wall_ns"] == sum(summary[x] for x in
            ("lift_sum_ns", "four_sum_ns", "five_sum_ns", "wide_sum_ns", "eight_sum_ns",
             "rank_sum_ns", "checkpoint_sum_ns", "loop_overhead_ns"))
        if summary["status"] == "RANK_GOAL_REACHED":
            assert current_rank == PLAN["rank_goal"]
            assert all(r["rank_mod_q"] < current_rank for r in records[:-1])
            projected = [(frozen["class"]["curve_order"] // q)*point for point in points]
            T = projected[summary["anchor_index"]]
            assert int(T.order()) == q and summary["anchored_log_replay"] == "PASS"
            assert [int(T[0]), int(T[1])] == summary["anchor_point"]
            assert all(log*T == point for log, point in zip(summary["anchored_logs"], projected))
        else:
            assert summary["status"] == "FULL_POOL_BELOW_RANK_GOAL"
            assert len(records) == 40 and current_rank < PLAN["rank_goal"]
        if current_eight == 39:
            projected = [(frozen["class"]["curve_order"] // q)*point for point in points]
            replay = summary["eight_replay"]
            T = projected[replay["anchor_index"]]
            assert int(T.order()) == q and replay["anchored_log_replay"] == "PASS"
            assert all(log*T == point for log, point in zip(replay["anchored_logs"], projected))
        audited.append({"cohort": cohort, "p": p, "q": q, "source_equations": len(entries),
                        "row_counts": count, "final_seven_rank": current_rank,
                        "final_eight_rank": current_eight,
                        "first_seven_source_count": first_seven,
                        "first_eight_source_count": first_eight,
                        "eight_anchor_replay": summary.get("eight_replay", {}).get("anchored_log_replay"),
                        "status": "PASS"})
        print(json.dumps(audited[-1]), flush=True)
    (HERE / "audit.json").write_text(json.dumps({"schema": "hecke-d79-live-eight-audit-v1",
                                                 "status": "PASS", "cases": audited},
                                                indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
