#!/usr/bin/env sage -python
"""Independently replay a SAT model as an exact N131 elliptic-curve relation."""

import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
R = 680564733841876926932320129493409985129
ROTATIONS = [0, 18, 36, 54, 72, 90, 108]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write("\n")


def main():
    model = json.loads((HERE / "model_audit_result.json").read_text())
    target = json.loads((HERE / "public_target.json").read_text())
    private = json.loads((HERE / "private_fixture.json").read_text())
    assert model["status"] == "PASS_W20_OUTPUT_LINEAR_XCNF_MODEL"
    assert model["workload_id"] == target["workload_id"] == private["workload_id"]
    assert private["public_sha256"] == sha(HERE / "public_target.json")

    poly = PolynomialRing(GF(2), "t")
    t = poly.gen()
    field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def decode(value):
        return field(poly([(int(value) >> bit) & 1 for bit in range(131)]))

    def encode(value):
        return sum(int(bit) << index for index, bit in
                   enumerate(value.polynomial().list()))

    def point(pair):
        return curve(decode(pair[0]), decode(pair[1]))

    def source_x(mask):
        return sum((field(t**(bit+1)) for bit in range(20) if mask >> bit & 1),
                   field.zero())

    def halftrace(value):
        acc, term = field.zero(), value
        for _ in range(66):
            acc += term
            term = term**4
        assert acc**2 + acc == value
        return acc

    def standard_reciprocal(raw):
        if raw == curve(0) or raw[0] == 0:
            return None
        return 1/raw[0]

    options = []
    for slot, masks in enumerate(model["source_mask_pairs"]):
        points = []
        for mask in masks:
            w = source_x(mask)
            assert w.trace() == 0 and (1/w).trace() == 0
            u = halftrace(w)
            assert u != 0
            x = 1 + 1/u
            lifts = curve.lift_x(x, all=True)
            assert len(lifts) == 2
            points.append(lifts)
        a = decode(model["unrotated_pair_standard_reciprocals"][slot])
        b = decode(model["output_inverse_witnesses"][slot])
        assert a*b == 1
        slot_options = {}
        for left, right in itertools.product(*points):
            raw = left + right
            if standard_reciprocal(raw) != a:
                continue
            rotation = ROTATIONS[slot]
            rotated = curve(raw[0]**(1 << rotation), raw[1]**(1 << rotation))
            slot_options[(encode(rotated[0]), encode(rotated[1]))] = rotated
        assert len(slot_options) == 2
        options.append(list(slot_options.values()))

    raw_target = point(target["raw_preimage"])
    public_q = point(target["public_target"])
    generator = point(target["workload"]["generator"])
    assert 4*raw_target == public_q and R*public_q == curve(0)
    assert private["scalar"]*generator == public_q
    target_a = decode(model["target_standard_reciprocal"])
    assert standard_reciprocal(raw_target) == target_a
    matches = []
    for choice in itertools.product(range(2), repeat=7):
        running = options[0][choice[0]]
        valid = True
        for slot in range(1, 7):
            running += options[slot][choice[slot]]
            if slot < 6 and standard_reciprocal(running) != decode(
                    model["intermediate_standard_reciprocals"][slot-1]):
                valid = False
                break
        if not valid or standard_reciprocal(running) != target_a:
            continue
        matches.append({"choice": list(choice),
                        "raw_point": [encode(running[0]), encode(running[1])],
                        "equals_selected_raw_preimage": running == raw_target,
                        "projects_to_public_target": 4*running == public_q})
    status = ("PASS_FRESH_N131_FACTOR_BASE_DECOMPOSITION" if
              any(item["projects_to_public_target"] for item in matches) else
              "NO_PUBLIC_RELATION_FROM_SAT_MODEL")
    save("model_replay_result.json", {
        "status": status, "workload_id": target["workload_id"],
        "model_matches": matches,
        "all_source_columns_distinct": model["all_source_columns_distinct"],
        "scalar_fixture_replayed": True,
        "source_sha256": {"script": sha(__file__),
                          "model_audit": sha(HERE / "model_audit_result.json"),
                          "public_target": sha(HERE / "public_target.json"),
                          "private_fixture": sha(HERE / "private_fixture.json"),
                          "sage_runtime": sha(HERE / "sage_runtime_info.json")}})
    print(status, len(matches), flush=True)


if __name__ == "__main__":
    main()
