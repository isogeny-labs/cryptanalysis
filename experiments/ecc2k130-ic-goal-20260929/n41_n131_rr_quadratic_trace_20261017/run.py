"""Symbolic sign elimination for target-conditioned D and D-cubed traces."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
SPAN = ROOT / "n41_n131_rr_code_family_span_20261017"
RR_PATH = ROOT / "n41_n131_sixpair_rr_root_span_20261016/run.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def load_rr():
    spec = importlib.util.spec_from_file_location("rr_quadratic_field", RR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def insert(basis, word, label, provenance):
    while word:
        pivot = word.bit_length() - 1
        if pivot in basis:
            old_word, old_label, old_provenance = basis[pivot]
            word ^= old_word
            label ^= old_label
            provenance ^= old_provenance
        else:
            basis[pivot] = (word, label, provenance)
            return None
    return provenance if label else None


def solve(basis):
    functional = 0
    for pivot in sorted(basis):
        word, label, _ = basis[pivot]
        low = word ^ (1 << pivot)
        bit = label ^ ((functional & low).bit_count() & 1)
        functional |= bit << pivot
    return functional


def cube_anf(coefficients, field):
    # In the Boolean quotient, s_i^2=s_i; in characteristic two,
    # D(s)^2=sum_S c_S^2 s^S. The product D^2 D uses mask union.
    square = [field.mul(value, value) for value in coefficients]
    cube = [0] * 64
    for left, a in enumerate(square):
        if not a:
            continue
        for right, b in enumerate(coefficients):
            if b:
                cube[left | right] ^= field.mul(a, b)
    return cube


def trace_mask(field):
    out = 0
    for bit in range(field.n):
        value, acc = 1 << bit, 0
        for _ in range(field.n):
            acc ^= value
            value = field.mul(value, value)
        assert acc in (0, 1)
        out |= acc << bit
    return out


def trace_dual(field):
    mask = trace_mask(field)
    basis = {}
    for a in range(field.n):
        row = 0
        for bit in range(field.n):
            product = field.mul(1 << a, 1 << bit)
            row |= ((product & mask).bit_count() & 1) << bit
        assert insert(basis, row, 0, 1 << a) is None
    assert len(basis) == field.n
    return basis


def trace_coefficient(dual, mask):
    coefficient = 0
    while mask:
        pivot = mask.bit_length() - 1
        row, _, source = dual[pivot]
        mask ^= row
        coefficient ^= source
    return coefficient


def n41_families(geometry, hit):
    used = {column for row in hit["pair_rows"][1:] for column in row["columns"]}
    fixed = []
    for slot in range(1, 6):
        witness = hit["pair_rows"][slot]["raw_sum"]
        states = geometry["blocks"][slot]["states"]
        fixed.append(min((state["raw_sum"] for state in states
                          if state["raw_sum"][0] == witness[0]), key=lambda p: p[1]))
    families = []
    for mask in geometry["permitted_canonical_a"]:
        states = [state for state in geometry["blocks"][0]["states"] if state["a"] == mask]
        assert len(states) == 4
        if not used.isdisjoint(states[0]["columns"]):
            continue
        roots = []
        for x in sorted({state["raw_sum"][0] for state in states}):
            points = [state["raw_sum"] for state in states if state["raw_sum"][0] == x]
            assert len(points) == 2
            roots.append(sorted(points)[0])
        assert len(roots) == 2
        families.append({"code": mask, "roots": roots})
    assert len(families) == 35
    return fixed, families


def run_panel(name, field, target, fixed, families, rr):
    start = time.monotonic_ns()
    basis, rows, records = {}, [], []
    first_failure = None
    dual = None
    for family in families:
        root_records = []
        for root_index, first in enumerate(family["roots"]):
            points = [first] + fixed
            coefficients = rr.coefficients([p[0] for p in points],
                                           [p[1] for p in points], target, field)
            if coefficients is None:
                root_records.append({"root_index": root_index,
                                     "status": "DUPLICATE_X_EXCEPTION"})
                continue
            cube = cube_anf(coefficients, field)
            assert all(rr.evaluate(cube, signs) == field.mul(
                field.mul(rr.evaluate(coefficients, signs),
                          rr.evaluate(coefficients, signs)),
                rr.evaluate(coefficients, signs)) for signs in range(64))
            zeros = [signs for signs in range(64) if rr.evaluate(coefficients, signs) == 0]
            for mask in range(64):
                feature = coefficients[mask] | (cube[mask] << field.n)
                label = int(mask == 0)
                index = len(rows)
                rows.append((feature, label))
                contradiction = insert(basis, feature, label, 1 << index)
                if contradiction is not None and first_failure is None:
                    first_failure = {"code": family["code"],
                                     "root_index": root_index,
                                     "row_index": index,
                                     "xor_row_indices": [i for i in range(index + 1)
                                                         if contradiction >> i & 1]}
            root_records.append({"root_index": root_index, "status": "VALID_CHART",
                                 "zero_sign_masks": zeros,
                                 "coefficient_sha256": hashlib.sha256(json.dumps(coefficients).encode()).hexdigest(),
                                 "cube_coefficient_sha256": hashlib.sha256(json.dumps(cube).encode()).hexdigest()})
        consistent = first_failure is None
        certificate = None
        if consistent:
            functional = solve(basis)
            assert all(((functional & word).bit_count() & 1) == label
                       for word, label in rows)
            if dual is None:
                dual = trace_dual(field)
            low = functional & ((1 << field.n) - 1)
            high = functional >> field.n
            a, b = trace_coefficient(dual, low), trace_coefficient(dual, high)
            certificate = {"coordinate_functional": functional,
                           "trace_a": a, "trace_b": b}
        records.append({"code": family["code"], "roots": root_records,
                        "feature_rank": len(basis),
                        "augmented_rank": len(basis) + int(not consistent),
                        "shared_certificate_exists": consistent,
                        "certificate": certificate})
    return {"status": "COMPLETE_QUADRATIC_TRACE_PANEL",
            "field_degree": field.n, "code_families": len(families),
            "charts": sum(len(item["roots"]) for item in records),
            "first_failed_code_prefix": next((i + 1 for i, item in enumerate(records)
                                              if not item["shared_certificate_exists"]), None),
            "first_failure": first_failure,
            "records": records, "row_count": len(rows),
            "elapsed_ns": time.monotonic_ns() - start}


def main():
    protocol = read(D / "protocol.json")
    assert sha(D / "run.py") == protocol["runner_sha256"]
    for relative, digest in protocol["sources"].items():
        assert sha(ROOT / relative) == digest, relative
    rr = load_rr()
    geometry = read(ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json")
    hit = read(ROOT / "n41_sixpair_shared_target_20261017/join_audit_result.json")
    fixed41, families41 = n41_families(geometry, hit)
    field41 = rr.Field(41, (1 << 41) | (1 << 3) | 1)
    result41 = run_panel("n41", field41, hit["raw_target"], fixed41, families41, rr)
    assert any(item["code"] == 6 and any(root.get("zero_sign_masks")
               for root in item["roots"]) for item in result41["records"])
    panel = read(SPAN / "panel_n131_v2.json")
    assert panel["status"] == "FROZEN_N131_FOUR_FIRST_CODE_VARIANTS"
    families131 = [{"code": variant["masks"][0],
                    "roots": [root[0] for root in variant["roots"]]}
                   for variant in panel["variants"]]
    field131 = rr.Field(panel["field_degree"], panel["field_modulus"])
    result131 = run_panel("n131", field131, panel["target"], panel["fixed_points"],
                          families131, rr)
    output = {"status": "COMPLETE_SYMBOLIC_QUADRATIC_TRACE_SCREEN",
              "candidate_id": None,
              "protocol_sha256": sha(D / "protocol.json"),
              "n41": result41, "n131": result131}
    (D / "result.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(json.dumps({name: {key: output[name][key] for key in (
        "code_families", "charts", "first_failed_code_prefix", "row_count", "elapsed_ns")}
        for name in ("n41", "n131")}, sort_keys=True))


if __name__ == "__main__":
    main()
