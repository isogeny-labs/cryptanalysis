"""Independent polynomial-field replay of every union phi-chart branch.

The earlier independent Sage raw-fiber audit establishes the adjacent group
map on all 4,134 selectors. This pass checks the chart conversion and digest.
"""

import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import GF, Matrix, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(values):
    return hashlib.sha256(b"".join(int(v).to_bytes(17, "little")
                                for v in values)).hexdigest()


def main():
    p = json.loads((HERE / "audit_sage_protocol_v3.json").read_text())
    assert p["status"] == "FROZEN_FIELD_CHART_REPLAY"
    assert p["source_sha256"] == sha(__file__)
    for name, value in p["input_sha256"].items():
        assert sha(p["inputs"][name]) == value
    geometry = json.loads(Path(p["inputs"]["geometry"]).read_text())
    prior = json.loads(Path(p["inputs"]["audit_result"]).read_text())
    valid_codes = json.loads(Path(p["inputs"]["valid_codes"]).read_text())
    raw_replay = json.loads(Path(p["inputs"]["raw_sage_result"]).read_text())
    assert raw_replay["status"] == "PASS_ALL_VALID_SELECTORS"
    assert raw_replay["valid_selectors"] == len(valid_codes) == 4134
    started = time.monotonic()
    n = 131
    bitpoly = (1 << 131) | (1 << 13) | (1 << 2) | (1 << 1) | 1
    ring = PolynomialRing(GF(2), "z")
    modulus = ring([bitpoly >> i & 1 for i in range(n+1)])
    field = GF(2**n, name="z", modulus=modulus)
    zeta = field.multiplicative_generator() ** ((2**n-1)//263)
    basis = [zeta**i + zeta**(263-i) for i in range(1, n+1)]
    inverse = Matrix(GF(2), [b.list() for b in basis]).transpose().inverse()
    dual = [sum(int(bit) << j for j, bit in enumerate(row)) for row in inverse.rows()]

    def decode(mask):
        value = field(0)
        bits = int(mask)
        while bits:
            low = bits & -bits
            value += basis[low.bit_length()-1]
            bits ^= low
        return value

    def encode(value):
        polybits = sum(int(bit) << i for i, bit in enumerate(value.list()))
        return sum(((polybits & row).bit_count() & 1) << i for i, row in enumerate(dual))

    assert sum(basis, field(0)) == 1
    masks = [int(x, 16) for x in geometry["domain"]["basis_coordinate_masks_hex"]]
    image_phis, source_phis = [], []
    for code, mask in valid_codes:
        expected_mask = 0
        for j, value in enumerate(masks):
            if code >> j & 1:
                expected_mask ^= value
        assert mask == expected_mask
        phi = decode(mask)
        assert phi != 0
        y = phi**2 + phi
        assert y not in (0, 1)
        image_x = 1/y
        out = 1/(image_x+1)
        assert (1+y)*out == phi+phi**2
        assert out == y/(1+y)
        source_phis.append(mask)
        image_phis.append(encode(out))
        if (code & 63) == 0:
            assert time.monotonic()-started < p["wall_cap_seconds"]
            assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < p["rss_cap_bytes"]
    assert digest(image_phis) == prior["image_phi_digest"]
    assert digest(source_phis) == prior["source_phi_digest"]
    print(json.dumps({
        "kind": "n131_d13_union_phi_branch_independent_field_chart_audit",
        "status": "PASS_ALL_VALID_SELECTORS",
        "protocol_sha256": sha(HERE / "audit_sage_protocol_v3.json"),
        "valid_selectors": len(image_phis),
        "image_phi_digest": digest(image_phis),
        "source_phi_digest": digest(source_phis),
        "elapsed_seconds": time.monotonic()-started,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
