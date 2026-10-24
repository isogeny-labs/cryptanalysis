"""Build cubic bit-constancy certificates in GF(2^41)[z]/H, without roots."""
import hashlib
import importlib.util
import json
import resource
import signal
import struct
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


assert CFG["status"] == "FROZEN_BEFORE_N41_QUOTIENT_CUBIC"
for name, item in CFG["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
assert not (HERE / "result.json").exists()
signal.alarm(CFG["wall_cap_seconds"])
started = time.monotonic()
spec = importlib.util.spec_from_file_location("frozen_field", CFG["sources"]["field_arithmetic"]["path"])
field_source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(field_source)
F = field_source.Field(41, [0, 3])
mul = F.mul
square = lambda x: mul(x, x)
geom = json.loads(Path(CFG["sources"]["geometry"]["path"]).read_text())
terms = json.loads(Path(CFG["sources"]["root_polynomial"]["path"]).read_text())["terms"]
cases = [json.loads(line) for line in Path(CFG["sources"]["coordinate_audit"]["path"]).open()]
assert len(cases) == 1554 and len(terms) == 170
target_x = struct.unpack("<65Q", Path(CFG["sources"]["target_residuals"]["path"]).read_bytes())


def trace(x):
    acc = x
    for _ in range(40):
        x = square(x)
        acc ^= x
    assert acc in (0, 1)
    return acc


def trace_dual_basis():
    # Trace(t^j * t^k) depends only on j+k. The inverse matrix maps a bit
    # coordinate to the coefficient alpha of Tr(alpha*z).
    powers = [1]
    for _ in range(80):
        powers.append(mul(powers[-1], 2))
    traces = [trace(x) for x in powers]
    rows = [sum(traces[j + k] << k for k in range(41)) | (1 << (41 + j))
            for j in range(41)]
    for k in range(41):
        pivot = next(j for j in range(k, 41) if (rows[j] >> k) & 1)
        rows[k], rows[pivot] = rows[pivot], rows[k]
        for j in range(41):
            if j != k and (rows[j] >> k) & 1:
                rows[j] ^= rows[k]
    assert [row & ((1 << 41) - 1) for row in rows] == [1 << i for i in range(41)]
    dual = [sum(((rows[k] >> (41 + i)) & 1) << k for k in range(41))
            for i in range(41)]
    assert all(trace(mul(dual[i], 1 << j)) == (i == j)
               for i in range(41) for j in range(41))
    return dual


dual = trace_dual_basis()
setup_seconds = time.monotonic() - started


def product(block, mask):
    value = 0
    for i, basis in enumerate(block["product_basis"]):
        if (mask >> i) & 1:
            value ^= basis
    return value


def h_monic(left_code, right_code):
    blocks = geom["blocks"]
    masks = geom["permitted_canonical_a"]
    a, b = blocks[0]["s"], blocks[1]["s"]
    p = product(blocks[0], masks[left_code])
    q = product(blocks[1], masks[right_code])
    bases = [a, b, p, q]
    powers = [[1] for _ in range(4)]
    for axis in range(4):
        for _ in range(8):
            powers[axis].append(mul(powers[axis][-1], bases[axis]))
    h = [0] * 9
    for ea, eb, ep, eq, ez in terms:
        coefficient = 1
        for axis, exponent in enumerate((ea, eb, ep, eq)):
            coefficient = mul(coefficient, powers[axis][exponent])
        h[ez] ^= coefficient
    assert h[8]
    inv = F.inv(h[8])
    h = [mul(v, inv) for v in h]
    assert h[8] == 1
    return h


def reduce(poly, h):
    out = poly[:] + [0] * max(0, 8 - len(poly))
    for k in range(len(out) - 1, 7, -1):
        coefficient = out[k]
        if coefficient:
            for j in range(8):
                if h[j]:
                    out[k - 8 + j] ^= mul(coefficient, h[j])
    return out[:8]


def square_mod(poly, h):
    out = [0] * 15
    for i, v in enumerate(poly):
        out[2 * i] = square(v)
    return reduce(out, h)


def mul_mod(left, right, h):
    out = [0] * 15
    for i, a in enumerate(left):
        if a:
            for j, b in enumerate(right):
                if b:
                    out[i + j] ^= mul(a, b)
    return reduce(out, h)


def trace_residues(h):
    z_power = [[0, 1] + [0] * 6]
    for _ in range(40):
        z_power.append(square_mod(z_power[-1], h))
    output = []
    for alpha in dual:
        row = [0] * 8
        coefficient = alpha
        for power in z_power:
            for i, value in enumerate(power):
                if value:
                    row[i] ^= mul(coefficient, value)
            coefficient = square(coefficient)
        assert square_mod(row, h) == row
        output.append(row)
    return output


def classify(poly):
    if any(poly[1:]):
        return None
    assert poly[0] in (0, 1)
    return poly[0]


def feature(value):
    output = value & 1
    position = 1
    for i in range(1, 41):
        for j in range(i + 1, 41):
            output |= (((value >> i) & 1) & ((value >> j) & 1)) << position
            position += 1
    for i in range(1, 41):
        for j in range(i + 1, 41):
            for k in range(j + 1, 41):
                output |= (((value >> i) & 1) & ((value >> j) & 1) &
                           ((value >> k) & 1)) << position
                position += 1
    assert position == CFG["feature_width"]
    return output


def masks_from_residues(bits, h):
    zero = one = 0
    constant = classify(bits[0])
    if constant is not None:
        zero |= (constant == 0)
        one |= (constant == 1)
    position = 1
    for i in range(1, 41):
        for j in range(i + 1, 41):
            pair = mul_mod(bits[i], bits[j], h)
            constant = classify(pair)
            if constant is not None:
                zero |= (constant == 0) << position
                one |= (constant == 1) << position
            position += 1
    assert position == 781
    for i in range(1, 41):
        for j in range(i + 1, 41):
            pair = mul_mod(bits[i], bits[j], h)
            for k in range(j + 1, 41):
                triple = mul_mod(pair, bits[k], h)
                constant = classify(triple)
                if constant is not None:
                    zero |= (constant == 0) << position
                    one |= (constant == 1) << position
                position += 1
    assert position == CFG["feature_width"]
    assert zero & one == 0
    return zero, one


rows = []
target_features = [feature(F.inv(x)) for x in target_x]
for index in CFG["panel_indices"]:
    case = cases[index]
    tick = time.monotonic()
    h = h_monic(case["left_code"], case["right_code"])
    h_seconds = time.monotonic() - tick
    tick = time.monotonic()
    bits = trace_residues(h)
    trace_seconds = time.monotonic() - tick
    tick = time.monotonic()
    zero, one = masks_from_residues(bits, h)
    feature_seconds = time.monotonic() - tick
    rejected_targets = [panel for panel, value in enumerate(target_features)
                        if (zero & value) | (one & ~value)]
    rows.append({"index": index, "codes": [case["left_code"], case["right_code"]],
                 "h": h, "zero_mask_hex": hex(zero), "one_mask_hex": hex(one),
                 "constant_bits": (zero | one).bit_count(),
                 "rejected_target_indices": rejected_targets,
                 "phase_seconds": {"polynomial": h_seconds,
                                   "trace_residues": trace_seconds,
                                   "feature_products": feature_seconds}})
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < CFG["rss_cap_bytes"]

result = {"status": "PASS_N41_ROOT_FREE_QUOTIENT_CUBIC", "candidate_id": None,
          "curve_id": CFG["curve_id"], "families": len(rows),
          "feature_width": CFG["feature_width"],
          "setup_seconds": setup_seconds,
          "wall_seconds": time.monotonic() - started,
          "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "rows": rows, "protocol_sha256": sha(HERE / "protocol.json")}
(HERE / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
signal.alarm(0)
print(json.dumps({"status": result["status"], "families": len(rows),
                  "wall_seconds": result["wall_seconds"]}, sort_keys=True))
