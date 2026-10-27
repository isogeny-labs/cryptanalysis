"""Bounded exact three-plus-five support-eight search on a sealed D79 residual."""
import hashlib
import importlib.util
import itertools
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, matrix, vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCE = ROOT / "experiments/hecke-d79-live-seven-20261027"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def sparse(row):
    return {int(k): int(v) for k, v in row.items() if v}


def main():
    seal = json.loads((HERE / "pre-run.json").read_text())
    for path, digest in seal["inputs"].items():
        assert sha(ROOT / path) == digest, path
    assert sha(HERE / "PROTOCOL.md") == seal["protocol_sha256"]
    assert sha(HERE / "run_sage.py") == seal["runner_sha256"]
    selection = json.loads((SOURCE / "selection.json").read_text())
    frozen = next(x for x in selection["selected"] if x["p"] == 1825517)
    plan = json.loads((SOURCE / "inputs.json").read_text())
    records = [json.loads(line) for line in (SOURCE / "cases/p1825517.jsonl").read_text().splitlines()]
    assert len(records) == 40 and frozen["q"] == 6091
    Incremental = module(ROOT / plan["incremental_module"]["path"], "residual_incremental")
    Group = module(ROOT / plan["frozen"]["relation_helpers"]["path"], "residual_group")
    neg, add = Group.group_law(1825517)
    points = [tuple(x) for x in frozen["class"]["class_points"]]
    sage_curve = EllipticCurve(GF(1825517), [0, -1, 1, -10, -20])
    sage_points = [sage_curve(x, y) for x, y in points]
    zero = sage_curve(0)
    start = time.perf_counter_ns()
    rows = [sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
    for rec in records:
        for family in ("four", "five", "six", "seven"):
            rows.extend(sparse(x["row"]) for x in rec["rows"][family])
    basis = Incremental.RankBasis(6091, rows)
    assert basis.rank == 38
    totals = []
    parts = []
    for k, rec in enumerate(records):
        entry = rec["entry"]
        assert entry["source"] == k and entry["status"] == "OUTSIDE_CLASS_TRACE"
        total = None
        for raw in entry["outside_traces"]:
            total = add(total, tuple(raw))
        part = sparse(entry["class_part"])
        check = total
        for j, value in part.items():
            for _ in range(abs(value)):
                check = add(check, points[j] if value > 0 else neg(points[j]))
        assert check is None
        totals.append(total)
        parts.append(part)
    setup_ns = time.perf_counter_ns() - start
    start = time.perf_counter_ns()
    triples = defaultdict(list)
    for i, j, k in itertools.combinations(range(40), 3):
        for sj, sk in itertools.product((-1, 1), repeat=2):
            key = add(totals[i], add(totals[j] if sj == 1 else neg(totals[j]),
                                     totals[k] if sk == 1 else neg(totals[k])))
            triples[key].append(((i, j, k), (1, sj, sk)))
    index_ns = time.perf_counter_ns() - start
    start = time.perf_counter_ns()
    probes = matches = verified = 0
    found = None
    status = "EXHAUSTED"
    for later in itertools.combinations(range(40), 5):
        if found is not None or status != "EXHAUSTED":
            break
        for signs in itertools.product((-1, 1), repeat=5):
            probes += 1
            total = None
            for index, sign in zip(later, signs):
                total = add(total, totals[index] if sign == 1 else neg(totals[index]))
            for earlier, early_signs in triples.get(neg(total), ()):
                if earlier[-1] >= later[0]:
                    continue
                matches += 1
                sources = earlier + later
                coefficients = early_signs + signs
                row = Counter()
                for source, sign in zip(sources, coefficients):
                    for j, value in parts[source].items():
                        row[j] += sign * value
                row = {j: value for j, value in row.items() if value}
                assert sum((value * sage_points[j] for j, value in row.items()), zero) == zero
                verified += 1
                if basis.insert(row):
                    found = {"sources": sources, "coefficients": coefficients,
                             "row": {str(j): value for j, value in sorted(row.items())}}
                    status = "RANK_39_FOUND"
                    rows.append(row)
                    break
            if found is not None:
                break
            if probes >= 12_000_000:
                status = "CENSORED_PROBE_CAP"
                break
            if time.perf_counter_ns() - start >= 120_000_000_000:
                status = "CENSORED_WALL_CAP"
                break
    search_ns = time.perf_counter_ns() - start
    out = {"schema": "hecke-d79-support-eight-residual-v1", "status": status,
           "p": 1825517, "q": 6091, "source_count": 40, "rank_before": 38,
           "rank_after": basis.rank, "triple_entries": sum(map(len, triples.values())),
           "quintuple_sign_probes": probes, "matches": matches, "verified_rows": verified,
           "selected_row": found, "setup_wall_ns": setup_ns, "triple_index_wall_ns": index_ns,
           "search_wall_ns": search_ns, "candidate_id": None, "target_online_ms": None}
    if found is not None:
        t0 = time.perf_counter_ns()
        q = 6091
        projected = [(frozen["class"]["curve_order"] // q) * point for point in sage_points]
        anchor = next(i for i, point in enumerate(projected) if point != zero)
        T = projected[anchor]
        assert int(T.order()) == q
        A = matrix(GF(q), len(rows), 40, lambda i, j: rows[i].get(j, 0))
        assert int(A.rank()) == 39
        augmented = A.stack(matrix(GF(q), 1, 40, lambda _, j: int(j == anchor)))
        logs = [int(x) for x in augmented.solve_right(vector(GF(q), [0] * len(rows) + [1]))]
        assert all(log * T == point for log, point in zip(logs, projected))
        out.update({"anchor_index": anchor, "anchored_logs": logs,
                    "anchored_log_replay": "PASS", "replay_wall_ns": time.perf_counter_ns() - t0})
    (HERE / "result.json").write_text(json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("anchored_logs", "selected_row")}), flush=True)


if __name__ == "__main__":
    main()
