"""Generate 280 exact N131 W23 triple-sum x families with one Sage worker."""
import functools
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg = json.loads((HERE / "extended_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N131_W23_EXTENDED_TRIPLE_X"
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
prior = json.loads(Path(cfg["sources"]["prior_result"]["path"]).read_text())
prior_sets = json.loads(Path(cfg["sources"]["prior_sets"]["path"]).read_text())["n131"]
panel = json.loads(Path(cfg["sources"]["sixpair_panel"]["path"]).read_text())["n131"]
assert prior["n131"]["first_masks"] == cfg["first_five"]
signal.alarm(cfg["wall_cap_seconds"])
started = time.monotonic()
R = PolynomialRing(GF(2), "t")
t = R.gen()
F = GF(2**131, name="t", modulus=t**131 + t**13 + t**2 + t + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
seed = 898618


def dec(value):
    return F(R([(int(value) >> i) & 1 for i in range(131)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def point(row):
    return E(dec(row[0]), dec(row[1]))


def halftrace(value):
    term, out = value, F.zero()
    for _ in range(66):
        out += term
        term = term**4
    assert out**2 + out == value
    return out


@functools.lru_cache(maxsize=None)
def source(mask):
    w = dec(mask << 1)
    assert w and w.trace() == 0 and (1 / w).trace() == 0
    x = 1 + 1 / halftrace(w)
    points = E.lift_x(x, all=True)
    assert len(points) == 2
    return points[0]


@functools.lru_cache(maxsize=None)
def orbit_key(mask):
    p = 4 * source(mask)
    assert p != E(0)
    x, smallest = p[0], None
    for _ in range(131):
        value = enc(x)
        smallest = value if smallest is None else min(smallest, value)
        x = x**2
    return smallest


fixed_keys = {orbit_key(mask) for slot in cfg["exclude_folded_columns_of_edges"]
              for mask in panel["edges"][slot]["masks"]}
assert len(fixed_keys) == 10
fixed1, fixed2 = [
    [point(row) for root in panel["edges"][slot]["roots"] for row in root]
    for slot in cfg["fixed_edges"]]
assert len(fixed1) == len(fixed2) == 4


def eligible(mask):
    mate = mask ^ seed
    a, b = dec(mask << 1), dec(mate << 1)
    if not a or not b or a.trace() or b.trace():
        return False
    if (1 / a).trace() or (1 / b).trace():
        return False
    keys = (orbit_key(mask), orbit_key(mate))
    return keys[0] != keys[1] and not (set(keys) & fixed_keys)


def triple_x(mask):
    mate = mask ^ seed
    left, right = source(mask), source(mate)
    family = [p + q for p in (left, -left) for q in (right, -right)]
    assert all(p != E(0) for p in family)
    groups = {}
    for p in family:
        groups.setdefault(enc(p[0]), []).append(p)
    assert len(groups) == 2 and all(len(v) == 2 for v in groups.values())
    values = set()
    for a in family:
        for b in fixed1:
            ab = a + b
            for c in fixed2:
                total = ab + c
                assert total != E(0)
                values.add(enc(total[0]))
    assert len(values) == 32
    return sorted(values)


selected = []
sets_path = HERE / "extended_sets.jsonl"
assert not sets_path.exists()
with sets_path.open("x") as out:
    for index, (mask, mate) in enumerate(cfg["first_five"]):
        assert mate == mask ^ seed and eligible(mask)
        values = triple_x(mask)
        assert values == prior_sets[index]
        selected.append([mask, mate])
        out.write(json.dumps({"masks": [mask, mate], "x": values},
                             sort_keys=True, separators=(",", ":")) + "\n")
        out.flush()
    next_mask = cfg["scan_after_mask"] + 1
    while len(selected) < cfg["family_count"]:
        assert next_mask < 1 << 22
        mask = next_mask
        next_mask += 1
        if not eligible(mask):
            continue
        mate = mask ^ seed
        values = triple_x(mask)
        selected.append([mask, mate])
        out.write(json.dumps({"masks": [mask, mate], "x": values},
                             sort_keys=True, separators=(",", ":")) + "\n")
        out.flush()
result = {"status": "PASS_N131_W23_EXTENDED_TRIPLE_X",
          "candidate_id": None, "curve_id": cfg["curve_id"],
          "family_count": len(selected), "last_scan_mask_exclusive": next_mask,
          "first_five_replayed": True,
          "last_masks": selected[-1],
          "source_cache_entries": source.cache_info().currsize,
          "sets_sha256": sha(sets_path),
          "wall_seconds": time.monotonic() - started,
          "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256": sha(HERE / "extended_protocol.json")}
(HERE / "extended_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
signal.alarm(0)
print(json.dumps({k: result[k] for k in ("status", "family_count",
                                             "last_scan_mask_exclusive",
                                             "wall_seconds", "self_maxrss_raw")}, sort_keys=True))
