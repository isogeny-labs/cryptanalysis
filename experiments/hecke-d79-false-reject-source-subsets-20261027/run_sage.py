"""Independent pair-index replay and rank certificates from sealed source traces."""
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())
SOURCE = ROOT / PLAN["source_dir"]


def sealed(name, digest):
    data = (SOURCE / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest, name
    return json.loads(data)


def sparse(row):
    return {int(k): int(v) for k, v in row.items() if v}


def rank(rows, field):
    return int(matrix(field, len(rows), 40, lambda i, j: rows[i].get(j, 0)).rank())


def independent_rows(entries, points):
    """Enumerate signed cancellations via pair lookup, independent of producer scans."""
    zero = points[0].curve()(0)
    total = {}
    for entry in entries:
        i = entry["source"]
        assert entry["status"] == "OUTSIDE_CLASS_TRACE"
        outside = sum((points[0].curve()(x, y) for x, y in entry["outside_traces"]), zero)
        class_part = sum((v * points[j] for j, v in sparse(entry["class_part"]).items()), zero)
        assert outside + class_part == zero
        total[i] = outside
    signed = {(i, s): s * point for i, point in total.items() for s in (-1, 1)}
    singles = {}
    for i in sorted(total):
        for s in (-1, 1):
            singles.setdefault(signed[i, s], []).append((i, s))
    pairs = {}
    for i, j in itertools.combinations(sorted(total), 2):
        for si, sj in itertools.product((-1, 1), repeat=2):
            pairs.setdefault(signed[i, si] + signed[j, sj], []).append((i, si, j, sj))
    relations = []

    def add(terms):
        support = tuple(i for i, _ in terms)
        row = Counter()
        for i, s in terms:
            for j, v in sparse(entries[i]["class_part"]).items():
                row[j] += s * v
        row = {j: v for j, v in row.items() if v}
        assert sum((v * points[j] for j, v in row.items()), zero) == zero
        relations.append((support, row))

    for i in sorted(total):
        if total[i] == zero:
            add(((i, 1),))
    for i, j in itertools.combinations(sorted(total), 2):
        for sj in (-1, 1):
            left = total[i] + signed[j, sj]
            if left == zero:
                add(((i, 1), (j, sj)))
            for k, sk in singles.get(-left, ()):
                if k > j:
                    add(((i, 1), (j, sj), (k, sk)))
            for k, sk, l, sl in pairs.get(-left, ()):
                if k > j:
                    add(((i, 1), (j, sj), (k, sk), (l, sl)))
    return relations


def main():
    gate = sealed("gate-result.json", PLAN["gate_sha256"])
    challenge = sealed("challenge-result.json", PLAN["challenge_sha256"])
    audit = sealed("audit.json", PLAN["audit_sha256"])
    target = PLAN["target_p"]
    frozen = next(x for x in gate["selected"] if x["p"] == target)
    produced = next(x for x in challenge["cases"] if x["p"] == target)
    audited = next(x for x in audit["cases"] if x["p"] == target)
    assert produced["gate_validation"] == "FALSE_REJECT"
    q = frozen["q"]
    curve = EllipticCurve(GF(target), [0, -1, 1, -10, -20])
    points = [curve(x, y) for x, y in frozen["class"]["class_points"]]
    entries = produced["source_entries"]
    assert [e["source"] for e in entries] == list(range(40))
    baseline = [sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
    field = GF(q)
    baseline_rank = rank(baseline, field)
    assert baseline_rank == audited["baseline_rank_mod_q"] == 35
    relations = independent_rows(entries, points)
    assert len(relations) == audited["hecke_candidate_count"]

    def stats(source_ids):
        ids = set(source_ids)
        rows = [row for support, row in relations if set(support) <= ids]
        return rank(baseline + rows, field), len(rows)

    prefix = []
    for count in range(41):
        r, n = stats(range(count))
        prefix.append({"source_count": count, "rank_mod_q": r, "hecke_rows": n})
    assert prefix[-1]["rank_mod_q"] == audited["full_pool_rank_mod_q"] == 39
    first = next(x["source_count"] for x in prefix if x["rank_mod_q"] >= PLAN["target_rank"])
    kept = set(range(40))
    deletions = []
    passes = 0
    while True:
        passes += 1
        removed = 0
        for i in range(39, -1, -1):
            if i not in kept:
                continue
            trial = kept - {i}
            if stats(trial)[0] >= PLAN["target_rank"]:
                kept = trial
                deletions.append(i)
                removed += 1
        if not removed:
            break
    cert_rank, cert_rows = stats(kept)
    assert cert_rank == 39
    assert all(stats(kept - {i})[0] < 39 for i in kept)
    selected_relations = [
        {"source_ids": list(support), "row": {str(j): v for j, v in sorted(row.items())}}
        for support, row in relations if set(support) <= kept
    ]
    assert len(selected_relations) == cert_rows
    assert rank(baseline + [sparse(x["row"]) for x in selected_relations], field) == 39
    output = {
        "schema": "hecke-d79-false-reject-source-subsets-v1",
        "status": "PASS", "p": target, "q": q,
        "baseline_rank_mod_q": baseline_rank,
        "full_hecke_row_count": len(relations),
        "full_rank_mod_q": prefix[-1]["rank_mod_q"],
        "ascending_prefix": prefix,
        "first_rank39_prefix_count": first,
        "deletion_passes": passes,
        "deletion_order": deletions,
        "inclusion_minimal_source_ids": sorted(kept),
        "inclusion_minimal_source_count": len(kept),
        "inclusion_minimal_rank_mod_q": cert_rank,
        "inclusion_minimal_hecke_row_count": cert_rows,
        "inclusion_minimal_hecke_rows": selected_relations,
        "inclusion_minimal_lift_sum_ns": sum(entries[i]["lift_wall_ns"] for i in kept),
        "full_lift_sum_ns": sum(e["lift_wall_ns"] for e in entries),
        "candidate_id": None,
        "target_online_ms": None,
    }
    (HERE / "result.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: output[k] for k in ("status", "first_rank39_prefix_count", "inclusion_minimal_source_count", "inclusion_minimal_source_ids", "inclusion_minimal_hecke_row_count")}))


if __name__ == "__main__":
    main()
