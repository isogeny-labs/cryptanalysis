#!/usr/bin/env sage -python
"""Independent Sage replay of all N131 raw-fiber/Frobenius target choices."""

import hashlib
import json
import sys
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
TARGET = ROOT / "n131_fixed_seed_eight_pair_circuit_20261010" / "target_preimages.json"
sys.path.insert(0, str(HERE))
import orbit9  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    runtime = json.loads((HERE / "sage_runtime_info.json").read_text())
    assert runtime["status"] == "verified"
    frozen = json.loads((HERE / "protocol.json").read_text())
    control = json.loads((HERE / "control_result.json").read_text())
    target = json.loads(TARGET.read_text())
    fixture = json.loads((BASE / "control_fixture.json").read_text())
    assert frozen["source_sha256"]["runner"] == sha(HERE / "orbit9.py")
    assert frozen["source_sha256"]["target"] == sha(TARGET)
    assert control["formula"]["xcnf_sha256"] == sha(HERE / "control.xcnf")
    assert control["status"] == "PASS_FULL_N131_NINEPAIR_ORBIT_CONSTRUCTED_WITNESS"
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    zero = curve(0)
    r = 680564733841876926932320129493409985129

    def dec(value):
        return field(ring([(int(value) >> i) & 1 for i in range(131)]))

    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    def xy(point):
        return [enc(point[0]), enc(point[1])]

    challenge_public = curve(*map(dec, target["public_target"]))
    assert challenge_public != zero and r * challenge_public == zero
    cases = [
        ("challenge", [row["point"] for row in target["preimages"]],
         target["public_target"]),
        ("constructed", [list(point) for point in
                         orbit9.constructed_preimages(fixture["raw_target"])],
         control["constructed_public_target"]),
    ]
    audits = {}
    for name, preimages, public_xy in cases:
        native_rows = orbit9.orbit_rows(preimages)
        public = curve(*map(dec, public_xy))
        assert public != zero and r * public == zero
        assert len(native_rows) == 524
        checked = []
        for fiber, raw_xy in enumerate(preimages):
            point = curve(*map(dec, raw_xy))
            assert 4 * point == public
            public_rotated = public
            for rotation in range(131):
                row = native_rows[fiber * 131 + rotation]
                assert row["raw_preimage_index"] == fiber
                assert row["target_rotation"] == rotation
                assert xy(point) == row["point"]
                assert 4 * point == public_rotated
                assert point[0] not in (field(0), field(1))
                reciprocal = 1 / point[0]
                assert enc(reciprocal) == row["standard_reciprocal"]
                checked.append([fiber, rotation, *xy(point), enc(reciprocal)])
                point = curve(point[0]**2, point[1]**2)
                public_rotated = curve(public_rotated[0]**2, public_rotated[1]**2)
            assert xy(point) == raw_xy
            assert public_rotated == public
        assert len(checked) == len({(row[2], row[3]) for row in checked}) == 524
        digest = hashlib.sha256(json.dumps(checked, separators=(",", ":")).encode()).hexdigest()
        audits[name] = {"public_target": public_xy,
                        "raw_preimages": preimages,
                        "choices_checked": len(checked),
                        "distinct_points": 524,
                        "row_digest_sha256": digest}
    assert audits["constructed"]["raw_preimages"] == control["raw_preimages"]
    assert native_rows[0]["standard_reciprocal"] == orbit9.base.standard_reciprocal(
        fixture["raw_target_z"])
    result = {"status": "PASS_SAGE_ALL_524_N131_ORBIT_FIBER_CHOICES",
              "candidate_id": None, "curve_id": frozen["curve_id"],
              "challenge": audits["challenge"],
              "constructed": audits["constructed"],
              "sha256": {"audit_script": sha(Path(__file__)),
                         "runner": sha(HERE / "orbit9.py"),
                         "protocol": sha(HERE / "protocol.json"),
                         "control": sha(HERE / "control_result.json"),
                         "target": sha(TARGET),
                         "fixture": sha(BASE / "control_fixture.json"),
                         "sage_runtime": sha(HERE / "sage_runtime_info.json")}}
    with (HERE / "sage_audit_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], flush=True)


if __name__ == "__main__":
    main()
