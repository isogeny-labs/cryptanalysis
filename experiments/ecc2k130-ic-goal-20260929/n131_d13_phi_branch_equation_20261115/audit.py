"""Exact d13 audit of the original/image phi-chart branch equation."""

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "ecc2k130" / "codegen"))
from indexcalc_e2e import AuditCurve, AuditField, Ledger  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(values):
    return hashlib.sha256(b"".join(int(v).to_bytes(17, "little")
                                for v in values)).hexdigest()


def main():
    p = json.loads((HERE / "protocol.json").read_text())
    assert p["status"] == "FROZEN_BEFORE_AUDIT"
    assert sha(__file__) == p["audit_source_sha256"]
    for name, value in p["input_sha256"].items():
        assert sha(p["inputs"][name]) == value
    geometry = json.loads(Path(p["inputs"]["geometry"]).read_text())
    assert geometry["curve_id"] == p["curve_id"]
    onb = AuditField(131, Ledger())
    curve = AuditCurve(onb, Ledger())
    one = onb.one()
    basis = [int(v, 16) for v in geometry["domain"]["basis_coordinate_masks_hex"]]
    start = time.monotonic()
    valid = 0
    image_phis = []
    source_phis = []
    for code in range(1, 1 << len(basis)):
        mask = 0
        for j, value in enumerate(basis):
            if code >> j & 1:
                mask ^= value
        phi = onb.fromCoords(mask)
        x = onb.inv(phi) ^ one
        raw = curve.pointFromX(x)
        if raw is None:
            continue
        assert x not in (0, one)
        y = onb.sqr(phi) ^ phi
        assert y not in (0, one)
        image = curve.add(raw, curve.frob(raw))
        assert image is not None and curve.onCurve(image)
        assert image[0] == onb.inv(y)
        out_original = onb.inv(x ^ one)
        out_image = onb.inv(image[0] ^ one)
        assert out_original == phi
        assert out_image == onb.mul(y, onb.inv(one ^ y))
        for b, out in ((0, out_original), (1, out_image)):
            lhs = onb.mul(one ^ (y if b else 0), out)
            rhs = phi ^ (onb.sqr(phi) if b else 0)
            assert lhs == rhs
        source_phis.append(mask)
        image_phis.append(onb.toCoords(out_image))
        valid += 1
        if (code & 63) == 0:
            assert time.monotonic()-start < p["wall_cap_seconds"]
            assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < p["rss_cap_bytes"]
    assert valid == 4134
    assert len(set(image_phis)) == len(set(source_phis)) == valid
    print(json.dumps({
        "kind": "n131_d13_adjacent_union_phi_branch_exact_audit",
        "status": "PASS_ALL_VALID_SELECTORS_BOTH_BRANCHES",
        "protocol_sha256": sha(HERE / "protocol.json"),
        "curve_id": p["curve_id"],
        "valid_selectors": valid,
        "branch_equations_checked": 2*valid,
        "image_phi_digest": digest(image_phis),
        "source_phi_digest": digest(source_phis),
        "image_phi_unique_per_position": len(set(image_phis)),
        "elapsed_seconds": time.monotonic()-start,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
