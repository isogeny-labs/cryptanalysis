"""Incremental exact signed five-source relation index."""
import itertools
import time
from collections import Counter, defaultdict


def sparse(raw):
    return {int(j): int(v) for j, v in raw.items() if v}


class FiveIndex:
    def __init__(self, points, neg, add, row_cap, wall_cap_seconds):
        self.points = points
        self.neg = neg
        self.add = add
        self.row_cap = row_cap
        self.wall_cap_ns = int(wall_cap_seconds * 1e9)
        self.totals = []
        self.parts = []
        self.pairs = defaultdict(list)
        self.rows = []
        self.search_ns = 0

    def signed(self, point, sign):
        return point if sign == 1 else self.neg(point)

    def append(self, entry):
        k = len(self.totals)
        if entry["source"] != k or entry["status"] != "OUTSIDE_CLASS_TRACE":
            raise ValueError("SOURCE_ORDER_OR_STATUS")
        total = None
        for raw in entry["outside_traces"]:
            total = self.add(total, tuple(raw))
        part = sparse(entry["class_part"])
        check = total
        for j, coefficient in part.items():
            for _ in range(abs(coefficient)):
                point = self.points[j] if coefficient > 0 else self.neg(self.points[j])
                check = self.add(check, point)
        if check is not None:
            raise ValueError("SOURCE_GROUP_MISMATCH")
        self.totals.append(total)
        self.parts.append(part)
        new_rows = []
        probes = matches = 0
        start = time.perf_counter_ns()
        status = "COMPLETE"
        for l in range(k):
            if status != "COMPLETE":
                break
            for m in range(l + 1, k):
                if status != "COMPLETE":
                    break
                for sl, sm, sk in itertools.product((-1, 1), repeat=3):
                    triple = self.add(self.signed(self.totals[l], sl),
                                      self.add(self.signed(self.totals[m], sm), self.signed(total, sk)))
                    probes += 1
                    for i, j, sj in self.pairs.get(self.neg(triple), ()):
                        if j >= l:
                            continue
                        matches += 1
                        sources = (i, j, l, m, k)
                        signs = (1, sj, sl, sm, sk)
                        row = Counter()
                        for source, sign in zip(sources, signs):
                            for column, coefficient in self.parts[source].items():
                                row[column] += sign * coefficient
                        row = {column: coefficient for column, coefficient in row.items() if coefficient}
                        verify = None
                        for column, coefficient in row.items():
                            for _ in range(abs(coefficient)):
                                point = self.points[column] if coefficient > 0 else self.neg(self.points[column])
                                verify = self.add(verify, point)
                        if verify is not None:
                            raise ValueError("FIVE_ROW_GROUP_MISMATCH")
                        item = {"sources": sources, "coefficients": signs,
                                "row": {str(column): coefficient for column, coefficient in sorted(row.items())}}
                        self.rows.append(item)
                        new_rows.append(item)
                        if len(self.rows) >= self.row_cap:
                            status = "CENSORED_ROW_CAP"
                            break
                    if status != "COMPLETE":
                        break
                if self.search_ns + time.perf_counter_ns() - start >= self.wall_cap_ns:
                    status = "CENSORED_WALL_CAP"
                    break
        elapsed = time.perf_counter_ns() - start
        self.search_ns += elapsed
        pair_insertions = 0
        if status == "COMPLETE":
            for i in range(k):
                for sk in (-1, 1):
                    key = self.add(self.totals[i], self.signed(total, sk))
                    self.pairs[key].append((i, k, sk))
                    pair_insertions += 1
        return new_rows, {"status": status, "triple_probes": probes,
                          "pair_matches": matches, "pair_insertions": pair_insertions}
