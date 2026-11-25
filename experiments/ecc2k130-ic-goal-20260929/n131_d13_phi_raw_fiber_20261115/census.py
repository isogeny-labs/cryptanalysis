"""Exact cofactor-class census for the d13 raw source and its 1+tau image."""

import hashlib
import json
import resource
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "ecc2k130" / "codegen"))
from indexcalc_e2e import AuditCurve, AuditField, Ledger  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(items):
    return hashlib.sha256(json.dumps(items, separators=(",", ":")).encode()).hexdigest()


def main():
    p = json.loads((HERE / "protocol_v2.json").read_text())
    assert p["status"] == "FROZEN_AMENDED_BEFORE_CENSUS"
    for name, value in p["input_sha256"].items():
        assert sha(p["inputs"][name]) == value
    assert sha(__file__) == p["source_sha256"]
    geometry = json.loads(Path(p["inputs"]["geometry"]).read_text())
    prior = json.loads(Path(p["inputs"]["expanded_census"]).read_text())
    assert geometry["curve_id"] == prior["curve_id"] == p["curve_id"]
    start = time.monotonic()
    onb = AuditField(131, Ledger())
    curve = AuditCurve(onb, Ledger())
    r = int(p["subgroup_order"])
    entries = geometry["official_single_target_cofactor_fiber"]["four_verified_lifts"]
    target = tuple(onb.fromCoords(int(x)) for x in entries[0]["target_coordinates"])
    torsion = [curve.add(tuple(onb.fromCoords(int(x)) for x in e["target_coordinates"]),
                         curve.neg(target)) for e in entries]
    assert torsion[0] is None and len(set(torsion)) == 4
    t4 = next(t for t in torsion if curve.dbl(t) is not None)
    group4 = [None, t4, curve.dbl(t4), curve.neg(t4)]
    assert set(group4) == set(torsion)
    assert all(curve.frob(t) == t for t in group4)
    assert r % 4 == 1

    basis = [int(s, 16) for s in geometry["domain"]["basis_coordinate_masks_hex"]]
    rows = []
    class_counts = Counter()
    image_class_counts = Counter()
    original_x = set()
    image_x = set()
    for code in range(1, 1 << len(basis)):
        mask = 0
        for j, b in enumerate(basis):
            if (code >> j) & 1:
                mask ^= b
        phi = onb.fromCoords(mask)
        x = onb.inv(phi) ^ onb.one()
        raw = curve.pointFromX(x)
        if raw is None:
            continue
        assert x not in (0, onb.one())
        source_class = group4.index(curve.mul(raw, r))
        raw_classes = sorted((source_class, (-source_class) % 4))
        image = curve.add(raw, curve.frob(raw))
        assert image is not None and curve.onCurve(image)
        assert image[0] == (x ^ onb.inv(x))
        image_classes = [2 * source_class % 4] * 2
        assert image_classes == sorted((2 * c) % 4 for c in raw_classes)
        if code in (1, 16, 64, 128, 256, 512, 1024, 2048, 4096, 8191):
            assert curve.mul(image, r) == group4[image_classes[0]]
        projected = curve.mul(raw, 4)
        assert curve.mul(group4[source_class], 4) is None
        image_projected = curve.mul(image, 4)
        assert image_projected == curve.add(projected, curve.frob(projected))
        assert image_projected is not None
        for c in raw_classes:
            class_counts[c] += 1
        for c in image_classes:
            image_class_counts[c] += 1
        rows.append([code, raw_classes, image_classes, onb.toCoords(image[0])])
        original_x.add(onb.toCoords(projected[0]))
        image_x.add(onb.toCoords(image_projected[0]))
        if (code & 63) == 0:
            assert time.monotonic() - start < p["wall_cap_seconds"]
            assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < p["rss_cap_bytes"]
    assert len(rows) == geometry["factor_base"]["distinct_nonidentity_signed_subgroup_options_per_position"]
    assert len(original_x) == len(image_x) == len(rows)
    assert not (original_x & image_x)
    assert sum(class_counts.values()) == sum(image_class_counts.values()) == 2 * len(rows)
    assert all(image_class_counts[c] == 0 for c in (1, 3))
    output = {
        "kind": "n131_d13_union_raw_cofactor_class_census",
        "status": "PASS_EXACT_POSITION_CENSUS",
        "protocol_sha256": sha(HERE / "protocol_v2.json"),
        "curve_id": p["curve_id"],
        "source_raw_x_per_position": len(rows),
        "source_raw_points_per_position": 2 * len(rows),
        "image_raw_x_per_position": len(image_x),
        "image_raw_points_per_position": 2 * len(rows),
        "union_raw_points_per_position": 4 * len(rows),
        "original_cofactor_classes_per_position": {str(i): class_counts[i] for i in range(4)},
        "image_cofactor_classes_per_position": {str(i): image_class_counts[i] for i in range(4)},
        "raw_image_x_digest": digest([row[3] for row in rows]),
        "ordered_class_pairs_digest": digest([row[:3] for row in rows]),
        "torsion_generator_coordinates": [onb.toCoords(v) for v in t4],
        "elapsed_seconds": time.monotonic() - start,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
