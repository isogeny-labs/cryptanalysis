"""Incremental signed-triple index for exact six- and seven-source rows."""
import itertools
import time
from collections import Counter, defaultdict


def sparse(raw):
    return {int(j): int(v) for j, v in raw.items() if v}


class WideIndex:
    def __init__(self, points, neg, add, row_cap, wall_cap_seconds):
        self.points = points
        self.neg = neg
        self.add = add
        self.row_cap = row_cap
        self.wall_cap_ns = int(wall_cap_seconds*1e9)
        self.totals = []
        self.parts = []
        self.triples = defaultdict(list)
        self.six_rows = []
        self.seven_rows = []
        self.search_ns = 0

    def signed(self, point, sign):
        return point if sign == 1 else self.neg(point)

    def emit(self, sources, signs, target):
        row = Counter()
        for source, sign in zip(sources, signs):
            for column, coefficient in self.parts[source].items():
                row[column] += sign*coefficient
        row = {column: coefficient for column, coefficient in row.items() if coefficient}
        check = None
        for column, coefficient in row.items():
            for _ in range(abs(coefficient)):
                point = self.points[column] if coefficient > 0 else self.neg(self.points[column])
                check = self.add(check, point)
        if check is not None:
            raise ValueError("WIDE_ROW_GROUP_MISMATCH")
        item = {"sources": sources, "coefficients": signs,
                "row": {str(column): coefficient for column, coefficient in sorted(row.items())}}
        target.append(item)
        return item

    def append(self, entry):
        started = time.perf_counter_ns()
        k = len(self.totals)
        if entry["source"] != k or entry["status"] != "OUTSIDE_CLASS_TRACE":
            raise ValueError("SOURCE_ORDER_OR_STATUS")
        total = None
        for trace in entry["outside_traces"]:
            total = self.add(total, tuple(trace))
        part = sparse(entry["class_part"])
        check = total
        for column, coefficient in part.items():
            for _ in range(abs(coefficient)):
                point = self.points[column] if coefficient > 0 else self.neg(self.points[column])
                check = self.add(check, point)
        if check is not None:
            raise ValueError("SOURCE_GROUP_MISMATCH")
        self.totals.append(total)
        self.parts.append(part)
        six_new = []
        seven_new = []
        six_probes = seven_probes = six_matches = seven_matches = 0
        status = "COMPLETE"

        six_started = time.perf_counter_ns()
        for l, m in itertools.combinations(range(k), 2):
            if status != "COMPLETE":
                break
            for sl, sm, sk in itertools.product((-1, 1), repeat=3):
                total6 = self.add(self.signed(self.totals[l], sl),
                                  self.add(self.signed(self.totals[m], sm), self.signed(total, sk)))
                six_probes += 1
                for i, j, h, sj, sh in self.triples.get(self.neg(total6), ()):
                    if h >= l:
                        continue
                    six_matches += 1
                    item = self.emit((i, j, h, l, m, k), (1, sj, sh, sl, sm, sk), self.six_rows)
                    six_new.append(item)
                    if len(self.six_rows) + len(self.seven_rows) >= self.row_cap:
                        status = "CENSORED_ROW_CAP"
                        break
                if status != "COMPLETE":
                    break
            if self.search_ns + time.perf_counter_ns() - started >= self.wall_cap_ns:
                status = "CENSORED_WALL_CAP"
        six_ns = time.perf_counter_ns() - six_started

        seven_started = time.perf_counter_ns()
        if status == "COMPLETE":
            for l, m, n in itertools.combinations(range(k), 3):
                if status != "COMPLETE":
                    break
                for sl, sm, sn, sk in itertools.product((-1, 1), repeat=4):
                    total7 = self.add(self.signed(self.totals[l], sl),
                                      self.add(self.signed(self.totals[m], sm),
                                               self.add(self.signed(self.totals[n], sn),
                                                        self.signed(total, sk))))
                    seven_probes += 1
                    for i, j, h, sj, sh in self.triples.get(self.neg(total7), ()):
                        if h >= l:
                            continue
                        seven_matches += 1
                        item = self.emit((i, j, h, l, m, n, k),
                                         (1, sj, sh, sl, sm, sn, sk), self.seven_rows)
                        seven_new.append(item)
                        if len(self.six_rows) + len(self.seven_rows) >= self.row_cap:
                            status = "CENSORED_ROW_CAP"
                            break
                    if status != "COMPLETE":
                        break
                if self.search_ns + time.perf_counter_ns() - started >= self.wall_cap_ns:
                    status = "CENSORED_WALL_CAP"
        seven_ns = time.perf_counter_ns() - seven_started

        update_started = time.perf_counter_ns()
        triple_insertions = 0
        if status == "COMPLETE":
            for i, j in itertools.combinations(range(k), 2):
                for sj, sk in itertools.product((-1, 1), repeat=2):
                    key = self.add(self.totals[i],
                                   self.add(self.signed(self.totals[j], sj), self.signed(total, sk)))
                    self.triples[key].append((i, j, k, sj, sk))
                    triple_insertions += 1
        update_ns = time.perf_counter_ns() - update_started
        elapsed = time.perf_counter_ns() - started
        self.search_ns += elapsed
        if status == "COMPLETE" and self.search_ns >= self.wall_cap_ns:
            status = "CENSORED_WALL_CAP"
        return six_new, seven_new, {"status": status,
                                    "six_probes": six_probes, "seven_probes": seven_probes,
                                    "six_matches": six_matches, "seven_matches": seven_matches,
                                    "triple_insertions": triple_insertions,
                                    "six_wall_ns": six_ns, "seven_wall_ns": seven_ns,
                                    "triple_update_wall_ns": update_ns,
                                    "wide_setup_wall_ns": elapsed-six_ns-seven_ns-update_ns,
                                    "wide_wall_ns": elapsed}
