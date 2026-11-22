"""Independent Sage replay of the half-fixed twelve-leaf witness."""

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, Matrix, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CODEGEN = ROOT / "ecc2k130" / "codegen"
sys.path.insert(0, str(CODEGEN))
import curves as native_curves
import field as native_field


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "sage_protocol.json").read_text())
    assert p["status"] == "FROZEN_BEFORE_INDEPENDENT_REPLAY"
    assert p["source_sha256"] == sha(__file__)
    for name, digest in p["input_sha256"].items():
        assert sha(p["inputs"][name]) == digest
    planted = json.loads(Path(p["inputs"]["planted_result"]).read_text())
    assert planted["fixed_original_positions"] == [0, 2, 4, 6, 8, 10]
    assert all(planted["leaf_branch_bits"][position] == 0
               for position in planted["fixed_original_positions"])
    geometry = json.loads(Path(p["inputs"]["geometry"]).read_text())
    started = time.monotonic()
    n = 131
    bitpoly = (1 << n) | (1 << 13) | (1 << 2) | (1 << 1) | 1
    ring = PolynomialRing(GF(2), "z")
    modulus = ring([bitpoly >> i & 1 for i in range(n+1)])
    k = GF(2**n, name="z", modulus=modulus)
    zeta = k.multiplicative_generator() ** ((2**n-1)//263)
    basis = [zeta**i + zeta**(263-i) for i in range(1, n+1)]
    inverse = Matrix(GF(2), [b.list() for b in basis]).transpose().inverse()
    dual = [sum(int(bit) << j for j, bit in enumerate(row)) for row in inverse.rows()]

    def decode(mask):
        result = k(0)
        bits = int(mask)
        while bits:
            low = bits & -bits
            result += basis[low.bit_length()-1]
            bits ^= low
        return result

    def encode(value):
        polybits = sum(int(bit) << i for i, bit in enumerate(value.list()))
        return sum(((polybits & row).bit_count() & 1) << i for i, row in enumerate(dual))

    assert sum(basis, k(0)) == 1
    sage_curve = EllipticCurve(k, [1, 0, 0, 0, 1])
    native_onb = native_field.Onb(n)
    native_curve = native_curves.Curve(native_onb)
    masks = [int(x, 16) for x in geometry["domain"]["basis_coordinate_masks_hex"]]
    valid = {int(code): int(mask) for code, mask in json.loads(
        Path(p["inputs"]["valid_codes"]).read_text())}
    running = sage_curve(0)
    for position, (code, branch, sign, phi_mask) in enumerate(zip(
            planted["leaf_codes"], planted["leaf_branch_bits"],
            planted["leaf_sign_bits"], planted["leaf_phi_masks"])):
        assert code in valid
        mask = 0
        for bit, base_mask in enumerate(masks):
            if code >> bit & 1:
                mask ^= base_mask
        assert mask == valid[code]
        phi = decode(mask)**(2**position)
        x = 1/phi+1
        native_phi = native_onb.frob(native_onb.fromCoords(mask), position)
        native_x = native_onb.add(native_onb.inv(native_phi), native_onb.one())
        native_source = native_curve.pointFromX(native_x)
        assert native_source is not None
        source = sage_curve(decode(native_onb.toCoords(native_source[0])),
                            decode(native_onb.toCoords(native_source[1])))
        assert source[0] == x
        if branch:
            point = source + sage_curve(source[0]**2, source[1]**2)
        else:
            point = source
        assert point != sage_curve(0)
        assert encode(1/(point[0]+1)) == phi_mask
        running += -point if sign else point
        if 1 <= position < len(planted["leaf_codes"])-1:
            assert encode(1/(running[0]+1)) == planted["partial_phi_masks"][position-1]
        assert time.monotonic()-started < p["wall_cap_seconds"]
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < p["rss_cap_bytes"]
    assert [encode(running[0]), encode(running[1])] == planted["synthetic_target_coordinates"]
    official = geometry["official_single_target_cofactor_fiber"]["four_verified_lifts"]
    official_points = [sage_curve(decode(int(item["target_coordinates"][0])),
                                  decode(int(item["target_coordinates"][1])))
                       for item in official]
    for index, old_target in enumerate(official_points):
        endpoint = running + old_target - official_points[0]
        assert encode(1/(endpoint[0]+1)) == planted["target_phi_masks"][index]
    print(json.dumps({"kind": "n131_d13_halfbranch_m12_independent_sage_planted_audit",
                      "status": "PASS_ALL_TWELVE_LEAVES_AND_TARGET_FIBER",
                      "protocol_sha256": sha(HERE / "sage_protocol.json"),
                      "checked_leaves": 12, "checked_partial_sums": 10,
                      "checked_target_fiber_endpoints": 4,
                      "elapsed_seconds": time.monotonic()-started,
                      "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
                     sort_keys=True))


if __name__ == "__main__":
    main()
