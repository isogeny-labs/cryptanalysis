"""Freeze 80 ascending W23 first-code variants with five source slots fixed."""
import hashlib
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
protocol = json.loads((HERE / "prepare_protocol.json").read_text())
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
assert sha(HERE / "prepare_sage.py") == protocol["preparer_sha256"]
prior = json.loads((ROOT / "n41_n131_sixpair_rr_root_span_20261016/frozen_panels.json").read_text())["n131"]
census = json.loads((ROOT / "n131_w23_sixpair_density_20261016/run_result.json").read_text())["worker_result"]
assert census["seed_mask"] == 898618 and prior["target"] == protocol["raw_target"]
assert prior["field_degree"] == 131

R = PolynomialRing(GF(2), "t")
t = R.gen()
F = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])

def dec(value):
    return F(R([(int(value) >> i) & 1 for i in range(131)]))

def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

def xy(point):
    return [enc(point[0]), enc(point[1])]

def halftrace(value):
    out = F.zero()
    term = value
    for _ in range(66):
        out += term
        term = term**4
    assert out**2 + out == value
    return out

point_cache = {}
key_cache = {}

def source(mask):
    if mask not in point_cache:
        value = dec(mask << 1)
        assert value and value.trace() == 0 and (1/value).trace() == 0
        x = 1 + 1/halftrace(value)
        points = E.lift_x(x, all=True)
        assert len(points) == 2
        point_cache[mask] = points[0]
    return point_cache[mask]

def orbit_key(mask):
    if mask not in key_cache:
        point = 4 * source(mask)
        assert point != E(0)
        x = point[0]
        smallest = None
        for _ in range(131):
            value = enc(x)
            smallest = value if smallest is None or value < smallest else smallest
            x = x**2
        key_cache[mask] = smallest
    return key_cache[mask]

def roots(a, b):
    left, right = source(a), source(b)
    groups = {}
    for p in (left, -left):
        for q in (right, -right):
            point = p + q
            if point == E(0):
                return None
            pair = xy(point)
            groups.setdefault(pair[0], set()).add(tuple(pair))
    if len(groups) != 2 or any(len(values) != 2 for values in groups.values()):
        return None
    return [[list(row) for row in sorted(groups[x])] for x in sorted(groups)]

fixed_edges = prior["edges"][1:]
fixed = [edge["roots"][0][0] for edge in fixed_edges]
fixed_x = {point[0] for point in fixed}
assert len(fixed) == len(fixed_x) == 5
fixed_keys = {orbit_key(mask) for edge in fixed_edges for mask in edge["masks"]}
assert len(fixed_keys) == 10

variants = []
scan_count = 0
for mask in range(1, protocol["max_mask_exclusive"]):
    scan_count += 1
    mate = mask ^ census["seed_mask"]
    if mask >= mate:
        continue
    w, z = dec(mask << 1), dec(mate << 1)
    if not w or not z or w.trace() != 0 or z.trace() != 0:
        continue
    if (1/w).trace() != 0 or (1/z).trace() != 0:
        continue
    keys = [orbit_key(mask), orbit_key(mate)]
    if keys[0] == keys[1] or any(key in fixed_keys for key in keys):
        continue
    pair_roots = roots(mask, mate)
    if pair_roots is None:
        continue
    xs = {root[0][0] for root in pair_roots}
    if len(xs) != 2 or xs & fixed_x or prior["target"][0] in xs:
        continue
    variants.append({"mask": mask, "mate": mate, "orbit_keys": keys,
                     "roots": pair_roots})
    if len(variants) == protocol["wanted_variants"]:
        break

assert len(variants) == protocol["wanted_variants"], (len(variants), scan_count)
assert [v["mask"] for v in variants] == sorted(v["mask"] for v in variants)
result = {"status": "FROZEN_N131_W23_ASCENDING_FIRST_CODE_PANEL",
          "candidate_id": None, "field_degree": 131,
          "field_modulus": (1 << 131) | (1 << 13) | 7,
          "target": prior["target"], "fixed_points": fixed,
          "fixed_orbit_keys": sorted(fixed_keys), "variants": variants,
          "masks_scanned": scan_count,
          "prepare_protocol_sha256": sha(HERE / "prepare_protocol.json")}
with (HERE / "panel.json").open("x") as output:
    json.dump(result, output, indent=2, sort_keys=True)
    output.write("\n")
print(json.dumps({"status": result["status"], "variants": len(variants),
                  "masks_scanned": scan_count,
                  "last_mask": variants[-1]["mask"]}, sort_keys=True))
