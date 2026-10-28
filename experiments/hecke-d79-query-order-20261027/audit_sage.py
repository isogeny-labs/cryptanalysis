"""Independent Sage audit of paired support-eight query orders."""
import hashlib
import importlib.util
import itertools
import json
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

from sage.all import EllipticCurve, GF, factor, is_prime, matrix, vector

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


def ordered_final_query_prefix(entries, neg, add, probe_limit, policy):
    """Rebuild the last source's ordered three-plus-five query prefix."""
    k = len(entries) - 1
    totals = []
    parts = []
    for entry in entries:
        total = None
        for raw in entry["outside_traces"]:
            total = add(total, tuple(raw))
        totals.append(total)
        parts.append(sparse(entry["class_part"]))
    triples = defaultdict(list)
    for h in range(2, k):
        for i, j in itertools.combinations(range(h), 2):
            for sj, sh in itertools.product((-1, 1), repeat=2):
                total = add(totals[i], add(totals[j] if sj == 1 else neg(totals[j]),
                                             totals[h] if sh == 1 else neg(totals[h])))
                triples[total].append(((i, j, h), (1, sj, sh)))
    rows = []
    probes = 0
    later_supports = itertools.combinations(range(k), 4)
    if policy == "reverse_lex":
        later_supports = reversed(list(later_supports))
    for later in later_supports:
        if probes == probe_limit:
            break
        for signs in itertools.product((-1, 1), repeat=5):
            probes += 1
            total = None
            for i, sign in zip(later + (k,), signs):
                total = add(total, totals[i] if sign == 1 else neg(totals[i]))
            for earlier, earlier_signs in triples.get(neg(total), ()):
                if earlier[-1] >= later[0]:
                    continue
                sources = earlier + later + (k,)
                coefficients = earlier_signs + signs
                row = Counter()
                for source, sign in zip(sources, coefficients):
                    for j, value in parts[source].items():
                        row[j] += sign * value
                rows.append({"sources": sources, "coefficients": coefficients,
                             "row": {j: value for j, value in row.items() if value}})
            if probes == probe_limit:
                break
    assert probes == probe_limit
    return rows


def main():
    for name, digest in (("selection.json", POST_SELECTION["selection_sha256"]),
                         ("inputs.json", POST_SELECTION["inputs_sha256"]),
                         ("select_sage.py", POST_SELECTION["selector_sha256"]),
                         ("preflight.json", PRE["preflight_sha256"]),
                         ("wide_index.py", PRE["wide_index_sha256"]),
                         ("ordered_index.py", PRE["ordered_index_sha256"]),
                         ("run_sage.py", PRE["runner_sha256"]),
                         ("HOLDOUT_PROTOCOL.md", PRE["protocol_sha256"]),
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
    ref = pinned(PLAN["pair_index_reference"], "order_audit_four")
    helper = pinned(PLAN["frozen"]["relation_helpers"], "order_audit_group")
    direct_info = json.loads((HERE.parent / "hecke-d79-compact-checkpoints-20261027" / "post-run.json").read_text())
    direct = pinned(direct_info["direct_audit_module"], "order_audit_direct")
    audited = []
    for (cohort, frozen), item in zip(cases, index["cases"]):
        p, q = frozen["p"], frozen["q"]
        assert (item["cohort"], item["p"], item["q"]) == (cohort, p, q)
        jp, sp = HERE / item["journal"], HERE / item["summary"]
        assert sha(jp) == item["journal_sha256"] and sha(sp) == item["summary_sha256"]
        records = [json.loads(line) for line in jp.read_text().splitlines()]
        summary = json.loads(sp.read_text())
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
        assert rank(baseline, q) == frozen["baseline_rank_mod_q"] == summary["baseline_rank_mod_q"]
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
        for policy in ("lex", "reverse_lex"):
            stop_n = summary["first_eight_source_count"][policy] or len(entries)
            full = independent_eight_rows(entries[:stop_n], encoded, neg, add)
            if summary["first_eight_source_count"][policy] is None:
                expected[policy + "_eight"] = full
            else:
                last = records[stop_n - 1]
                metrics = last["eight_metrics"][policy]
                prior = [row for row in full if max(row["sources"]) < stop_n - 1]
                produced = last["rows"][policy + "_eight"]
                assert set(canonical(produced)).issubset(set(canonical(full)))
                if metrics["status"] == "RANK_GOAL_REACHED":
                    ordered = ordered_final_query_prefix(entries[:stop_n], neg, add,
                        metrics["step_probes"], policy)
                    def key(row):
                        return (tuple(row["sources"]), tuple(row["coefficients"]),
                                tuple(sorted(sparse(row["row"]).items())))
                    assert [key(row) for row in ordered[:len(produced)]] == [key(row) for row in produced]
                    expected[policy + "_eight"] = prior + ordered[:len(produced)]
                else:
                    assert metrics["status"] == "SKIPPED_LOWER_RANK_GOAL"
                    assert produced == [] and metrics["step_probes"] == 0
                    expected[policy + "_eight"] = prior
        for name, rows in expected.items():
            assert canonical(rows) == canonical([row for record in records for row in record["rows"][name]])
        bases = {name: DenseRank(q, baseline) for name in ("seven", "lex", "reverse_lex")}
        acc = {name: list(baseline) for name in bases}
        first = {name: None for name in bases}
        counts = {name: 0 for name in expected}
        probes = {policy: 0 for policy in ("lex", "reverse_lex")}
        for k, record in enumerate(records):
            for name in ("four", "five", "six", "seven"):
                new = [row for row in expected[name] if max(row["sources"]) == k]
                assert canonical(new) == canonical(record["rows"][name])
                novelty = 0
                for relation in new:
                    row = sparse(relation["row"])
                    novelty += bool(bases["seven"].add(row))
                    acc["seven"].append(row)
                    for policy in ("lex", "reverse_lex"):
                        bases[policy].add(row)
                        acc[policy].append(row)
                assert novelty == record["novel"][name]
                counts[name] += len(new)
            for policy in ("lex", "reverse_lex"):
                name = policy + "_eight"
                new = [row for row in expected[name] if max(row["sources"]) == k]
                assert canonical(new) == canonical(record["rows"][name])
                novelty = 0
                for relation in new:
                    row = sparse(relation["row"])
                    if first[policy] is None and k + 1 == summary["first_eight_source_count"][policy]:
                        assert bases[policy].rank < 39
                    novelty += bool(bases[policy].add(row))
                    acc[policy].append(row)
                assert novelty == record["novel_eight"][policy]
                counts[name] += len(new)
                metrics = record["eight_metrics"][policy]
                probes[policy] += metrics["step_probes"]
                if first[policy] is None:
                    if bases[policy].rank == 39:
                        first[policy] = k + 1
                        assert metrics["status"] in ("RANK_GOAL_REACHED", "SKIPPED_LOWER_RANK_GOAL")
                    else:
                        assert metrics["status"] == "COMPLETE"
                        assert metrics["step_probes"] == 32*comb(k, 4)
                else:
                    assert metrics["status"] == "SKIPPED_RANK_GOAL"
                    assert metrics["step_probes"] == 0
                assert record["rank_eight_mod_q"][policy] == bases[policy].rank
                assert record["eight_wall_ns"][policy] >= 0
            if first["seven"] is None and bases["seven"].rank == 39:
                first["seven"] = k + 1
            assert record["rank_mod_q"] == bases["seven"].rank
            assert record["four_metrics"]["pair_insertions"] == 2*k
            assert record["five_metrics"]["pair_insertions"] == 2*k
            assert record["five_metrics"]["triple_probes"] == 8*comb(k, 2)
            wide = record["wide_metrics"]
            assert wide["status"] == "COMPLETE"
            assert wide["six_probes"] == 8*comb(k, 2)
            assert wide["seven_probes"] == 16*comb(k, 3)
            assert wide["triple_insertions"] == 4*comb(k, 2)
        assert counts == summary["row_counts"]
        assert first["seven"] == summary["first_seven_source_count"]
        assert {x: first[x] for x in probes} == summary["first_eight_source_count"]
        assert probes == summary["actual_eight_probes"] == item["actual_eight_probes"]
        assert summary["paired_horizon_eight_probes"] == 32*comb(len(records), 5)
        assert summary["paired_probe_ratio"] == item["paired_probe_ratio"]
        assert summary["paired_probe_difference"] == (probes["lex"] - probes["reverse_lex"]
            if all(first[p] is not None for p in probes) else None)
        for name in bases:
            assert rank(acc[name], q) == bases[name].rank
        assert bases["seven"].rank == summary["final_rank_mod_q"] == item["final_rank_mod_q"]
        assert {p: bases[p].rank for p in probes} == summary["final_rank_eight_mod_q"] == item["final_rank_eight_mod_q"]
        assert summary["collector_wall_ns"] == sum(summary[x] for x in
            ("lift_sum_ns", "four_sum_ns", "five_sum_ns", "wide_sum_ns", "rank_sum_ns", "checkpoint_sum_ns", "loop_overhead_ns")) + sum(summary["eight_sum_ns"].values())
        projected = [(frozen["class"]["curve_order"] // q)*point for point in points]
        for policy in probes:
            if bases[policy].rank == 39:
                replay = summary["eight_replay"][policy]
                T = projected[replay["anchor_index"]]
                assert int(T.order()) == q and replay["anchored_log_replay"] == "PASS"
                assert [int(T[0]), int(T[1])] == replay["anchor_point"]
                prefix = list(baseline)
                stop_n = first[policy]
                for name in ("four", "five", "six", "seven", policy + "_eight"):
                    prefix.extend(sparse(row["row"]) for row in expected[name]
                                  if max(row["sources"]) < stop_n)
                assert rank(prefix, q) == 39
                F = GF(q)
                A = matrix(F, len(prefix), 40, lambda i, j: prefix[i].get(j, 0))
                aug = A.stack(matrix(F, 1, 40, lambda _, j: int(j == replay["anchor_index"])))
                logs = [int(x) for x in aug.solve_right(vector(F, [0]*len(prefix) + [1]))]
                assert logs == replay["anchored_logs"]
                assert all(log*T == point for log, point in zip(logs, projected))
        audited.append({"cohort": cohort, "p": p, "q": q,
            "source_equations": len(entries), "row_counts": counts,
            "first_source_count": first, "probes": probes, "status": "PASS"})
        print(json.dumps(audited[-1], sort_keys=True), flush=True)
    (HERE / "audit.json").write_text(json.dumps({"schema": "hecke-d79-query-order-audit-v1",
        "status": "PASS", "cases": audited}, sort_keys=True, indent=2) + "\n")

if __name__ == "__main__":
    main()
