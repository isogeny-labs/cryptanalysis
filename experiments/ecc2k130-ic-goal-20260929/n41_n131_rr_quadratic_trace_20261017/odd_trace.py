"""Incrementally test odd-power trace feature dimension on frozen N131 charts."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
RR = ROOT / "n41_n131_sixpair_rr_root_span_20261016/run.py"
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()


def anf(values):
    result = values[:]
    for bit in range(6):
        for mask in range(64):
            if mask >> bit & 1:
                result[mask] ^= result[mask ^ (1 << bit)]
    return result


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


def main():
    protocol = json.loads((D / "odd_protocol.json").read_text())
    assert protocol["runner_sha256"] == sha(D / "odd_trace.py")
    for path, digest in protocol["sources"].items():
        assert sha(ROOT / path) == digest
    spec = importlib.util.spec_from_file_location("rr_odd_field", RR)
    rr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rr)
    panel = json.loads((ROOT / "n41_n131_rr_code_family_span_20261017/panel_n131_v2.json").read_text())
    field = rr.Field(panel["field_degree"], panel["field_modulus"])
    features = []
    start = time.monotonic_ns()
    for variant in panel["variants"]:
        family = []
        for root in variant["roots"]:
            points = [root[0]] + panel["fixed_points"]
            c = rr.coefficients([p[0] for p in points], [p[1] for p in points],
                                panel["target"], field)
            assert c is not None
            values = [rr.evaluate(c, mask) for mask in range(64)]
            odd = []
            for exponent in (1, 3, 5, 7):
                powered = []
                for value in values:
                    power = 1
                    for _ in range(exponent):
                        power = field.mul(power, value)
                    powered.append(power)
                odd.append(anf(powered))
            family.extend((tuple(coef[mask] for coef in odd), int(mask == 0))
                          for mask in range(64))
        features.append(family)
    screens = []
    for count in (1, 2, 3, 4):
        basis, failed = {}, None
        records = []
        for variant, family in zip(panel["variants"], features):
            for coeffs, label in family:
                word = sum(value << (i * field.n) for i, value in enumerate(coeffs[:count]))
                if insert(basis, word, label) and failed is None:
                    failed = variant["masks"][0]
            records.append({"code": variant["masks"][0], "feature_rank": len(basis),
                            "augmented_rank": len(basis) + int(failed is not None),
                            "shared_certificate_exists": failed is None})
        screens.append({"odd_powers": [1, 3, 5, 7][:count],
                        "feature_dimension": count * field.n,
                        "first_failed_code": failed, "records": records})
    out = {"status": "COMPLETE_ODD_TRACE_DIMENSION_SCREEN", "candidate_id": None,
           "protocol_sha256": sha(D / "odd_protocol.json"),
           "elapsed_ns": time.monotonic_ns() - start, "screens": screens,
           "chart_count": 8, "sign_states_per_chart": 64}
    (D / "odd_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
    print(json.dumps([{"powers": s["odd_powers"], "first_failed_code": s["first_failed_code"],
                       "ranks": [r["feature_rank"] for r in s["records"]]} for s in screens]))


if __name__ == "__main__":
    main()
