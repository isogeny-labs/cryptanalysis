"""Exact six-slot subgroup source screen for adding P + Frobenius(P)."""

import hashlib
import json
import resource
import time
from decimal import Decimal, getcontext
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def main():
    p = json.loads((HERE / "protocol.json").read_text())
    assert p["status"] == "FROZEN_BEFORE_SCREEN"
    assert sha(__file__) == p["source_sha256"]
    for key, value in p["input_sha256"].items():
        assert sha(p["inputs"][key]) == value
    geometry = json.loads(Path(p["inputs"]["geometry"]).read_text())
    candidate = json.loads(Path(p["inputs"]["candidate"]).read_text())
    record = candidate["candidate_record"]
    r = int(record["curve"]["subgroup_order_r"])
    lam = int(record["endomorphism"]["frobenius_eigenvalue_mod_r"])
    assert r == 549756390943 and geometry["curve_id"] == p["curve_id"]
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    zero = curve(0)
    start = time.monotonic()
    original_all = set()
    image_all = set()
    slot_stats = []
    output = []
    for rotation in p["rotations"]:
        rows = geometry["point_rows_by_unique_rotation"][str(rotation)]
        assert len(rows) == 64
        original = set()
        image = set()
        slot_out = []
        for index, row in enumerate(rows):
            x, y, column, mask, branch, sign = map(int, row)
            assert branch == 0 and sign in (0, 1)
            point = curve(field.from_integer(x), field.from_integer(y))
            assert r*point == zero
            tau = curve(point[0]**2, point[1]**2)
            mapped = point + tau
            assert mapped != zero and mapped == ((lam+1) % r)*point
            orig_key = (encode(point[0]), encode(point[1]))
            image_key = (encode(mapped[0]), encode(mapped[1]))
            assert orig_key == (x, y)
            original.add(orig_key)
            image.add(image_key)
            slot_out.append({"original": [x, y], "image": list(image_key),
                             "column": column, "mask": mask, "sign": sign,
                             "image_log_multiplier_mod_r": (lam+1) % r})
        assert len(original) == len(image) == 64
        original_all.update(original)
        image_all.update(image)
        slot_stats.append({"rotation": rotation,
                           "original_points": len(original),
                           "image_points": len(image),
                           "overlap": len(original & image),
                           "union_points": len(original | image)})
        output.append({"rotation": rotation, "rows": slot_out})
        assert time.monotonic() - start < p["wall_cap_seconds"]
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < p["rss_cap_bytes"]
    (HERE / "union_rows.json").write_text(json.dumps(output, separators=(",", ":")) + "\n")
    assert len(original_all) == 64 * len(p["rotations"])
    getcontext().prec = 35
    print(json.dumps({
        "kind": "n41_w6_adjacent_union_six_slot_screen",
        "status": "PASS_EXACT_GROUP_CENSUS",
        "protocol_sha256": sha(HERE / "protocol.json"),
        "curve_id": p["curve_id"],
        "rotations": p["rotations"],
        "slot_stats": slot_stats,
        "original_global_points": len(original_all),
        "image_global_points": len(image_all),
        "global_overlap": len(original_all & image_all),
        "global_union_points": len(original_all | image_all),
        "source_folded_columns": 26,
        "image_log_multiplier_mod_r": (lam+1) % r,
        "union_rows_sha256": sha(HERE / "union_rows.json"),
        "conditional_uniform_subgroup_mean_six_slots":
            str(Decimal(128)**6 / Decimal(r)),
        "elapsed_seconds": time.monotonic()-start,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
