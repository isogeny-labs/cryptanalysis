"""Charge direct N41 signed screening against odd-trace certificates on code boxes."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text())


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CountedField:
    def __init__(self, underlying):
        self.f = underlying
        self.n = underlying.n
        self.mul_count = 0
    def mul(self, a, b):
        self.mul_count += 1
        return self.f.mul(a, b)


def roots(states, mask):
    chosen = [s for s in states if s["a"] == mask]
    assert len(chosen) == 4
    by_x = {}
    for state in chosen:
        x, y = state["raw_sum"]
        by_x.setdefault(x, set()).add(y)
    assert len(by_x) == 2 and all(len(ys) == 2 for ys in by_x.values())
    return [[x, min(by_x[x])] for x in sorted(by_x)]


def insert(basis, word, label):
    while word:
        pivot = word.bit_length() - 1
        if pivot in basis:
            old_word, old_label = basis[pivot]
            word ^= old_word
            label ^= old_label
        else:
            basis[pivot] = (word, label)
            return False
    return bool(label)


def rank_prefix(rows, count, n):
    basis = {}
    failed = False
    for features, label in rows:
        word = sum(value << (j*n) for j, value in enumerate(features[:count]))
        if insert(basis, word, label):
            failed = True
    return len(basis), len(basis) + int(failed)


def evaluate_all(coefficients):
    values = []
    xors = 0
    for signs in range(64):
        value = 0
        for mask, c in enumerate(coefficients):
            if mask & signs == mask and c:
                value ^= c
                xors += 1
        values.append(value)
    return values, xors


def anf(values):
    result = values[:]
    for bit in range(6):
        for mask in range(64):
            if mask >> bit & 1:
                result[mask] ^= result[mask ^ (1 << bit)]
    return result


def chart(a, b, fixed, target, rr, field):
    points = [a, b] + fixed
    start = time.monotonic_ns()
    before = field.mul_count
    coefficients = rr.coefficients([p[0] for p in points],
                                   [p[1] for p in points], target, field)
    coefficient_ns = time.monotonic_ns() - start
    if coefficients is None:
        return {"status": "DUPLICATE_X_EXCEPTION"}
    coefficient_mul = field.mul_count - before
    start = time.monotonic_ns()
    values, xors = evaluate_all(coefficients)
    direct_ns = time.monotonic_ns() - start
    return {"status": "VALID_CHART", "values": values,
            "coefficient_sha256": hashlib.sha256(json.dumps(coefficients).encode()).hexdigest(),
            "zero_sign_masks": [i for i, value in enumerate(values) if value == 0],
            "coefficient_ns": coefficient_ns, "coefficient_mul": coefficient_mul,
            "direct_ns": direct_ns, "direct_xors": xors}


def trace_screen(charts, max_power_count, field):
    assert all(chart["status"] == "VALID_CHART" for chart in charts)
    start = time.monotonic_ns()
    before = field.mul_count
    feature_rows = []
    for chart_data in charts:
        values = chart_data["values"]
        powers = []
        current = values[:]
        square = [field.mul(value, value) for value in values]
        for j in range(max_power_count):
            powers.append(anf(current))
            if j + 1 < max_power_count:
                current = [field.mul(a, b) for a, b in zip(current, square)]
        feature_rows.extend((tuple(power[mask] for power in powers), int(mask == 0))
                            for mask in range(64))
    features_ns = time.monotonic_ns() - start
    features_mul = field.mul_count - before
    ranks = []
    rank_ns = 0
    for count in range(1, max_power_count + 1):
        start = time.monotonic_ns()
        rank, augmented = rank_prefix(feature_rows, count, field.n)
        rank_ns += time.monotonic_ns() - start
        ranks.append({"odd_power_count": count, "feature_rank": rank,
                      "augmented_rank": augmented,
                      "certificate_exists": rank == augmented})
    return {"rows": len(feature_rows), "feature_ns": features_ns,
            "feature_mul": features_mul, "rank_ns": rank_ns,
            "first_certificate_power_count": next((r["odd_power_count"] for r in ranks
                                                    if r["certificate_exists"]), None),
            "ranks": ranks}


def main():
    protocol = read(D / "protocol.json")
    assert sha(D / "run.py") == protocol["runner_sha256"]
    assert sha(D / "sage_runtime_info.json") == protocol["runtime_info_sha256"]
    for path, digest in protocol["sources"].items():
        assert sha(ROOT / path) == digest, path
    rr = load("rr_two_code_field", ROOT / "n41_n131_sixpair_rr_root_span_20261016/run.py")
    geometry = read(ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json")
    hit = read(ROOT / "n41_sixpair_shared_target_20261017/join_audit_result.json")
    fixed = []
    for slot in range(2, 6):
        witness = hit["pair_rows"][slot]
        root = roots(geometry["blocks"][slot]["states"], witness["masks"][0])
        matching = [point for point in root if point[0] == witness["raw_sum"][0]]
        assert len(matching) == 1
        fixed.append(matching[0])
    field = CountedField(rr.Field(41, (1 << 41) | (1 << 3) | 1))
    boxes = [("lexical_2x2", [(a, b) for a in (2, 3) for b in (5, 6)], 25),
             ("witness_pair", [(hit["pair_rows"][0]["masks"][0],
                                 hit["pair_rows"][1]["masks"][0])], 8)]
    assert protocol["target"] == hit["raw_target"]
    assert protocol["lexical_box"] == [list(pair) for pair in boxes[0][1]]
    assert protocol["witness_pair"] == list(boxes[1][1][0])
    results = []
    for name, pairs, max_count in boxes:
        charts = []
        for a, b in pairs:
            states_a = [s for s in geometry["blocks"][0]["states"] if s["a"] == a]
            states_b = [s for s in geometry["blocks"][1]["states"] if s["a"] == b]
            assert set(states_a[0]["columns"]).isdisjoint(states_b[0]["columns"])
            for point_a in roots(geometry["blocks"][0]["states"], a):
                for point_b in roots(geometry["blocks"][1]["states"], b):
                    chart_data = chart(point_a, point_b, fixed, hit["raw_target"], rr, field)
                    chart_data.update({"code_a": a, "code_b": b,
                                       "point_a": point_a, "point_b": point_b})
                    charts.append(chart_data)
        valid = [item for item in charts if item["status"] == "VALID_CHART"]
        trace = trace_screen(valid, max_count, field) if len(valid) == len(charts) else None
        results.append({"name": name, "code_pairs": pairs, "charts": charts,
                        "valid_charts": len(valid),
                        "zero_count": sum(len(c["zero_sign_masks"]) for c in valid),
                        "direct_coefficient_ns": sum(c["coefficient_ns"] for c in valid),
                        "direct_coefficient_mul": sum(c["coefficient_mul"] for c in valid),
                        "direct_sign_ns": sum(c["direct_ns"] for c in valid),
                        "direct_sign_xors": sum(c["direct_xors"] for c in valid),
                        "trace": trace})
    result = {"status": "COMPLETE_TWO_CODE_TRACE_BOX_SCREEN", "candidate_id": None,
              "protocol_sha256": sha(D / "protocol.json"),
              "fixed_slot_count": 4, "free_slot_count": 2,
              "target": hit["raw_target"], "boxes": results}
    (D / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps([{"name": b["name"], "valid_charts": b["valid_charts"],
                       "zero_count": b["zero_count"],
                       "first_certificate_power_count": b["trace"]["first_certificate_power_count"]
                       if b["trace"] else None} for b in results]))


if __name__ == "__main__":
    main()
