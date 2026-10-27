"""Exact signed support-at-most-four D79 relation enumeration by pair lookup."""
import itertools
from collections import Counter, defaultdict


def sparse(raw):
    return {int(k): int(v) for k, v in raw.items() if v}


def hecke_rows_pair_index(entries, points, neg, add):
    ids = sorted(entries)
    totals = {}
    for i in ids:
        entry = entries[i]
        total = None
        for raw in entry["outside_traces"]:
            total = add(total, tuple(raw))
        class_total = None
        for j, coeff in sparse(entry["class_part"]).items():
            for _ in range(abs(coeff)):
                class_total = add(class_total, points[j] if coeff > 0 else neg(points[j]))
        if add(total, class_total) is not None:
            raise ValueError("SOURCE_GROUP_MISMATCH:" + str(i))
        totals[i] = total

    signed = {(i, 1): totals[i] for i in ids}
    signed.update({(i, -1): neg(totals[i]) for i in ids})
    singles = defaultdict(list)
    for i in ids:
        for sign in (-1, 1):
            singles[signed[i, sign]].append((i, sign))
    pairs = defaultdict(list)
    for i, j in itertools.combinations(ids, 2):
        for si, sj in itertools.product((-1, 1), repeat=2):
            pairs[add(signed[i, si], signed[j, sj])].append((i, si, j, sj))

    out = []
    probes = 0

    def emit(terms):
        row = Counter()
        for i, sign in terms:
            for j, coeff in sparse(entries[i]["class_part"]).items():
                row[j] += sign * coeff
        row = {j: x for j, x in row.items() if x}
        check = None
        for j, coeff in row.items():
            for _ in range(abs(coeff)):
                check = add(check, points[j] if coeff > 0 else neg(points[j]))
        if check is not None:
            raise ValueError("HECKE_ROW_GROUP_MISMATCH")
        out.append({"sources": [i for i, _ in terms],
                    "coefficients": [sign for _, sign in terms],
                    "row": {str(j): x for j, x in sorted(row.items())}})

    for i in ids:
        if totals[i] is None:
            emit(((i, 1),))
    for i, j in itertools.combinations(ids, 2):
        for sj in (-1, 1):
            left = add(totals[i], signed[j, sj])
            if left is None:
                emit(((i, 1), (j, sj)))
            complement = neg(left)
            probes += 2
            for k, sk in singles.get(complement, ()):
                if k > j:
                    emit(((i, 1), (j, sj), (k, sk)))
            for k, sk, l, sl in pairs.get(complement, ()):
                if k > j:
                    emit(((i, 1), (j, sj), (k, sk), (l, sl)))
    metrics = {"signed_singleton_insertions": 2 * len(ids),
               "signed_pair_insertions": 4 * (len(ids) * (len(ids) - 1) // 2),
               "complement_bucket_probes": probes,
               "verified_candidate_count": len(out)}
    return out, metrics
