#!/usr/bin/env sage -python
"""Independently replay the fresh public point and raw preimage fixture."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
R = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    public = json.loads((HERE / "public_target.json").read_text())
    private = json.loads((HERE / "private_fixture.json").read_text())
    assert private["public_sha256"] == sha(HERE / "public_target.json")
    seed = bytes.fromhex(private["seed_hex"])
    assert hashlib.sha256(seed).hexdigest() == public["workload"]["target_generation_seed_sha256"]
    digest = hashlib.sha256(b"ecc2k130-w20-output-linear-v1" + seed).digest()
    scalar = int.from_bytes(digest, "big") % (R - 1) + 1
    assert scalar == private["scalar"]
    encoded = json.dumps(public["workload"], sort_keys=True,
                         separators=(",", ":")).encode()
    assert hashlib.sha256(encoded).hexdigest()[:12] == public["workload_id"]

    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def decode(number):
        return field(ring([(int(number) >> bit) & 1 for bit in range(131)]))

    def point(pair):
        return curve(decode(pair[0]), decode(pair[1]))

    generator = point(public["workload"]["generator"])
    target = point(public["public_target"])
    raw = point(public["raw_preimage"])
    assert generator != curve(0) and R*generator == curve(0)
    assert scalar*generator == target and R*target == curve(0)
    assert raw != curve(0) and 4*raw == target
    assert raw[0] != 0 and 1/raw[0] == decode(public["raw_standard_reciprocal_x"])
    result = {"status": "PASS_INDEPENDENT_FRESH_N131_TARGET_REPLAY",
              "workload_id": public["workload_id"],
              "public_target": public["public_target"],
              "generator_order_check": True, "scalar_point_replay": True,
              "raw_preimage_projection": True,
              "standard_reciprocal_check": True,
              "source_sha256": {"script": sha(__file__),
                                "public": sha(HERE / "public_target.json"),
                                "private": sha(HERE / "private_fixture.json"),
                                "runtime": sha(HERE / "sage_runtime_info.json")}}
    with (HERE / "target_replay_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print("PASS_INDEPENDENT_FRESH_N131_TARGET_REPLAY", public["workload_id"])


if __name__ == "__main__":
    main()
