"""Verified append-only signed-pair index and incremental F_q row basis."""
from collections import Counter, defaultdict


def sparse(raw):
    return {int(k): int(v) for k, v in raw.items() if v}


class RankBasis:
    def __init__(self, modulus, rows=()):
        self.modulus = int(modulus)
        self.pivots = {}
        for row in rows:
            self.insert(row)

    @property
    def rank(self):
        return len(self.pivots)

    def insert(self, row):
        q = self.modulus
        value = {int(i): int(x) % q for i, x in row.items() if int(x) % q}
        while value:
            i = min(value)
            if i not in self.pivots:
                inverse = pow(value[i], -1, q)
                self.pivots[i] = {j: x * inverse % q for j, x in value.items()}
                return True
            coefficient = value[i]
            for j, x in self.pivots[i].items():
                residual = (value.get(j, 0) - coefficient * x) % q
                if residual:
                    value[j] = residual
                else:
                    value.pop(j, None)
        return False


class PairIndex:
    def __init__(self, points, neg, add):
        self.points = points
        self.neg = neg
        self.add = add
        self.totals = {}
        self.parts = {}
        self.pairs = defaultdict(list)
        self.rows = []

    def append(self, entry):
        k = entry["source"]
        if k != len(self.totals) or entry["status"] != "OUTSIDE_CLASS_TRACE":
            raise ValueError("SOURCE_ORDER_OR_STATUS")
        neg, add = self.neg, self.add
        total = None
        for raw in entry["outside_traces"]:
            total = add(total, tuple(raw))
        part = sparse(entry["class_part"])
        class_total = None
        for j, coefficient in part.items():
            for _ in range(abs(coefficient)):
                class_total = add(class_total, self.points[j] if coefficient > 0 else neg(self.points[j]))
        if add(total, class_total) is not None:
            raise ValueError("SOURCE_GROUP_MISMATCH:" + str(k))
        self.totals[k] = total
        self.parts[k] = part
        new_rows = []

        def emit(terms):
            row = Counter()
            for i, sign in terms:
                for j, coefficient in self.parts[i].items():
                    row[j] += sign * coefficient
            row = {j: x for j, x in row.items() if x}
            check = None
            for j, coefficient in row.items():
                for _ in range(abs(coefficient)):
                    check = add(check, self.points[j] if coefficient > 0 else neg(self.points[j]))
            if check is not None:
                raise ValueError("HECKE_ROW_GROUP_MISMATCH")
            item = {"sources": [i for i, _ in terms],
                    "coefficients": [sign for _, sign in terms],
                    "row": {str(j): x for j, x in sorted(row.items())}}
            self.rows.append(item)
            new_rows.append(item)

        if total is None:
            emit(((k, 1),))
        for i in range(k):
            for sk in (-1, 1):
                signed = total if sk == 1 else neg(total)
                if add(self.totals[i], signed) is None:
                    emit(((i, 1), (k, sk)))
        for sk in (-1, 1):
            signed = total if sk == 1 else neg(total)
            for i, j, sj in self.pairs.get(neg(signed), ()):
                emit(((i, 1), (j, sj), (k, sk)))
        for l in range(k):
            for sl in (-1, 1):
                for sk in (-1, 1):
                    left = self.totals[l] if sl == 1 else neg(self.totals[l])
                    right = total if sk == 1 else neg(total)
                    complement = neg(add(left, right))
                    for i, j, sj in self.pairs.get(complement, ()):
                        if j < l:
                            emit(((i, 1), (j, sj), (l, sl), (k, sk)))
        for i in range(k):
            for sk in (-1, 1):
                signed = total if sk == 1 else neg(total)
                self.pairs[add(self.totals[i], signed)].append((i, k, sk))
        return new_rows, {"pair_insertions": 2*k, "bucket_probes": 2+4*k,
                          "new_verified_rows": len(new_rows)}
