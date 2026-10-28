"""Incremental canonical signed three-plus-five support-eight index."""
import itertools
import time
from collections import Counter, defaultdict
from math import comb


def sparse(raw):
    return {int(j): int(v) for j, v in raw.items() if v}


class EightIndex:
    def __init__(self, points, neg, add, row_cap, wall_cap_seconds, probe_cap):
        self.points, self.neg, self.add = points, neg, add
        self.row_cap = row_cap
        self.wall_cap_ns = int(wall_cap_seconds * 1e9)
        self.probe_cap = probe_cap
        self.totals, self.parts = [], []
        self.triples = defaultdict(list)
        self.rows = []
        self.search_ns = 0
        self.probes = 0

    def signed(self, point, sign):
        return point if sign == 1 else self.neg(point)

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
                check = self.add(check, self.points[column] if coefficient > 0 else self.neg(self.points[column]))
        if check is not None:
            raise ValueError("SOURCE_GROUP_MISMATCH")
        self.totals.append(total)
        self.parts.append(part)
        new_rows = []
        matches = 0
        status = "COMPLETE"
        query_started = time.perf_counter_ns()
        for later in itertools.combinations(range(k), 4):
            if status != "COMPLETE":
                break
            for signs in itertools.product((-1, 1), repeat=5):
                self.probes += 1
                later_total = None
                for index, sign in zip(later + (k,), signs):
                    later_total = self.add(later_total, self.signed(self.totals[index], sign))
                for earlier, earlier_signs in self.triples.get(self.neg(later_total), ()):
                    if earlier[-1] >= later[0]:
                        continue
                    matches += 1
                    sources = earlier + later + (k,)
                    coefficients = earlier_signs + signs
                    row = Counter()
                    for source, sign in zip(sources, coefficients):
                        for column, value in self.parts[source].items():
                            row[column] += sign * value
                    row = {column: value for column, value in row.items() if value}
                    check = None
                    for column, value in row.items():
                        for _ in range(abs(value)):
                            check = self.add(check, self.points[column] if value > 0 else self.neg(self.points[column]))
                    if check is not None:
                        raise ValueError("EIGHT_ROW_GROUP_MISMATCH")
                    item = {"sources": sources, "coefficients": coefficients,
                            "row": {str(column): value for column, value in sorted(row.items())}}
                    self.rows.append(item)
                    new_rows.append(item)
                    if len(self.rows) >= self.row_cap:
                        status = "CENSORED_ROW_CAP"
                        break
                if status != "COMPLETE":
                    break
                if self.probes >= self.probe_cap:
                    status = "CENSORED_PROBE_CAP"
                    break
                if self.search_ns + time.perf_counter_ns() - started >= self.wall_cap_ns:
                    status = "CENSORED_WALL_CAP"
                    break
        query_ns = time.perf_counter_ns() - query_started
        update_started = time.perf_counter_ns()
        insertions = 0
        if status == "COMPLETE":
            for i, j in itertools.combinations(range(k), 2):
                for sj, sk in itertools.product((-1, 1), repeat=2):
                    key = self.add(self.totals[i], self.add(self.signed(self.totals[j], sj), self.signed(total, sk)))
                    self.triples[key].append(((i, j, k), (1, sj, sk)))
                    insertions += 1
        update_ns = time.perf_counter_ns() - update_started
        elapsed = time.perf_counter_ns() - started
        self.search_ns += elapsed
        if status == "COMPLETE" and self.search_ns >= self.wall_cap_ns:
            status = "CENSORED_WALL_CAP"
        return new_rows, {"status": status, "quintuple_sign_probes": self.probes,
                          "step_probes": 32 * comb(k, 4) if status == "COMPLETE" else None,
                          "matches": matches, "triple_insertions": insertions,
                          "query_wall_ns": query_ns, "triple_update_wall_ns": update_ns,
                          "overhead_wall_ns": elapsed - query_ns - update_ns,
                          "eight_wall_ns": elapsed}
