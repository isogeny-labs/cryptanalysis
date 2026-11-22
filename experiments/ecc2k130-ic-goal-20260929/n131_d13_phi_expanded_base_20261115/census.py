"""Exact orbit census for adding P + Frobenius(P) to the d13 base."""

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CODEGEN = ROOT / "ecc2k130" / "codegen"
sys.path.insert(0, str(CODEGEN))

from indexcalc_e2e import AuditCurve, AuditField, Ledger  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def orbit_x(onb, value):
    for _ in range(131):
        yield onb.toCoords(value)
        value = onb.sqr(value)


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    source = Path(protocol["source_receipt"])
    assert sha(source) == protocol["source_receipt_sha256"]
    assert sha(__file__) == protocol["census_source_sha256"]
    receipt = json.loads(source.read_text())
    assert receipt["curve_id"] == protocol["curve_id"]
    assert receipt["effective_relation_matrix_columns"] == 4134
    assert receipt["actual_usable_points_before_sign_frobenius_folding"] == 1083108
    assert len(receipt["representatives"]) == 4134
    started = time.monotonic()
    ledger = Ledger()
    onb = AuditField(131, ledger)
    curve = AuditCurve(onb, ledger)
    one = onb.one()
    original_x = set()
    image_x = set()
    representative_image = []
    for index, (cx, cy) in enumerate(receipt["representatives"]):
        x, y = onb.fromCoords(int(cx)), onb.fromCoords(int(cy))
        assert x not in (0, one)
        p = (x, y)
        assert curve.onCurve(p)
        t = (onb.sqr(x), onb.sqr(y))
        q = curve.add(p, t)
        assert q is not None and curve.onCurve(q)
        image_coordinate = x ^ onb.inv(x)
        assert q[0] == image_coordinate
        original_x.update(orbit_x(onb, x))
        image_x.update(orbit_x(onb, image_coordinate))
        representative_image.append(onb.toCoords(image_coordinate))
        if (index & 63) == 0:
            assert time.monotonic() - started < protocol["wall_cap_seconds"]
            assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < protocol["rss_cap_bytes"]
    assert len(original_x) == len(image_x) == 4134 * 131
    overlap = original_x & image_x
    assert len(representative_image) == len(set(representative_image)) == 4134
    assert onb.frob(one, 131) == one
    result = {
        "kind": "n131_d13_adjacent_endomorphism_base_census",
        "status": "PASS_EXACT_ORBIT_CENSUS",
        "curve_id": protocol["curve_id"],
        "source_receipt_sha256": protocol["source_receipt_sha256"],
        "protocol_sha256": sha(HERE / "protocol.json"),
        "original_x_count": len(original_x),
        "image_x_count": len(image_x),
        "x_overlap_count": len(overlap),
        "original_point_count": 2 * len(original_x),
        "image_point_count": 2 * len(image_x),
        "union_point_count": 2 * (len(original_x) + len(image_x) - len(overlap)),
        "original_folded_columns": 4134,
        "union_independent_log_unknowns_upper_bound": 4134,
        "endomorphism_scalar_mod_r":
            (1 + int(protocol["frobenius_eigenvalue"])) % int(protocol["subgroup_order"]),
        "representative_image_x_sha256": hashlib.sha256(
            b"".join(x.to_bytes(17, "little") for x in representative_image)).hexdigest(),
        "original_x_set_sha256": hashlib.sha256(
            b"".join(x.to_bytes(17, "little") for x in sorted(original_x))).hexdigest(),
        "image_x_set_sha256": hashlib.sha256(
            b"".join(x.to_bytes(17, "little") for x in sorted(image_x))).hexdigest(),
        "wall_seconds": time.monotonic() - started,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "field_operation_counts": dict(ledger.counts),
    }
    assert result["endomorphism_scalar_mod_r"] != 0
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
