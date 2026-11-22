#!/usr/bin/env sage -python
"""Freeze a new one-point N131 public workload; keep the scalar outside solver inputs."""

import hashlib
import json
import secrets
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
R = 680564733841876926932320129493409985129
G = (1723937215198422920526670030259507407702,
     1738023298242148033288875399277548700785)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write("\n")


def main():
    base = PolynomialRing(GF(2), "t")
    t = base.gen()
    field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def decode(value):
        return field(base([(int(value) >> i) & 1 for i in range(131)]))

    def encode(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    generator = curve(decode(G[0]), decode(G[1]))
    assert R*generator == curve(0)
    seed = secrets.token_bytes(32)
    digest = hashlib.sha256(b"ecc2k130-w20-output-linear-v1" + seed).digest()
    scalar = int.from_bytes(digest, "big") % (R - 1) + 1
    target = scalar * generator
    assert target != curve(0) and R*target == curve(0)
    raw = pow(4, -1, R) * target
    assert raw != curve(0) and raw[0] not in (0, 1) and 4*raw == target
    reciprocal_x = 1/raw[0]
    public_point = [encode(target[0]), encode(target[1])]
    raw_point = [encode(raw[0]), encode(raw[1])]
    workload = {
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "field": "GF(2)[t]/(t^131+t^13+t^2+t+1)",
        "curve": "y^2+xy=x^3+1",
        "subgroup_order": R, "generator": list(G),
        "target_count": 1, "target_point": public_point,
        "target_generation_seed_sha256": hashlib.sha256(seed).hexdigest(),
        "target_generation_law": "sha256(domain||seed) mod (r-1) + 1",
        "raw_preimage_index": 0,
    }
    encoded = json.dumps(workload, sort_keys=True, separators=(",", ":")).encode()
    workload_id = hashlib.sha256(encoded).hexdigest()[:12]
    save("public_target.json", {"status": "FROZEN_FRESH_N131_ONE_POINT_TARGET",
                                "candidate_id": None, "workload_id": workload_id,
                                "workload": workload, "public_target": public_point,
                                "raw_preimage": raw_point,
                                "raw_standard_reciprocal_x": encode(reciprocal_x),
                                "target_generation_excluded_from_online": True,
                                "source_sha256": {"script": sha(__file__),
                                                  "sage_runtime": sha(HERE / "sage_runtime_info.json")}})
    save("private_fixture.json", {"status": "PRIVATE_REPLAY_FIXTURE",
                                  "workload_id": workload_id, "seed_hex": seed.hex(),
                                  "scalar": scalar, "public_target": public_point,
                                  "public_sha256": sha(HERE / "public_target.json")})
    print(json.dumps({"status": "FROZEN_FRESH_N131_ONE_POINT_TARGET",
                      "workload_id": workload_id, "public_target": public_point}))


if __name__ == "__main__":
    main()
