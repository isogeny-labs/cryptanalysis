"""Independent checked-Sage replay of the unpinned residual-family hit."""
import hashlib
import importlib.util
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
EARLIER = GOAL / "n41_symbolic_two_bucket_20261011/audit.py"
GEOMETRY = GOAL / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"
PRIOR = GOAL / "n41_seed_sum_s3_bucket_norm_20261010/batch_result.json"
spec = importlib.util.spec_from_file_location("independent_two_bucket_audit", EARLIER)
independent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(independent)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "audit_protocol.json").read_text())
    paths = {"auditor": HERE / "audit_sage.py", "earlier_auditor": EARLIER,
             "search_protocol": HERE / "search_protocol.json",
             "search_result": HERE / "search_result.json", "geometry": GEOMETRY,
             "prior_witness": PRIOR, "sage_runtime": HERE / "sage_runtime_info.json"}
    assert {key: sha(path) for key, path in paths.items()} == p["sha256"]
    search = json.loads(paths["search_result"].read_text())
    protocol = json.loads(paths["search_protocol"].read_text())
    assert search["status"] == "ALGEBRAIC_HIT_PENDING_GROUP_REPLAY"
    hit = search["hit"]
    assert search["decisions"] == 4 * (hit["right_seed"] - 1) + hit["raw_option"] + 1
    binary = PolynomialRing(GF(2), "T")
    T = binary.gen()
    field = GF(2**41, "T", modulus=T**41 + T**3 + 1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    ring = PolynomialRing(field, "Z")
    geometry = json.loads(GEOMETRY.read_text())["n41"]
    projected = curve(*(independent.decode(field, v) for v in protocol["residual"]))
    torsion = curve(field.one(), field.zero())
    inv4 = pow(4, -1, geometry["subgroup_order"])
    raw = inv4 * projected + hit["raw_option"] * torsion
    assert 4 * raw == projected
    assert [independent.encode(raw[0]), independent.encode(raw[1])] == hit["raw_target"]
    target = 1 / (raw[0] + 1)
    witnesses = []
    for family in hit["left_families"]:
        left, _left_u2, _left_products = independent.bucket(
            field, ring, geometry["window_basis_halftrace"][2], family["left_seed"])
        right, right_u2, right_products = independent.bucket(
            field, ring, geometry["window_basis_halftrace"][3], hit["right_seed"])
        norm = independent.target_norm(ring, target, right_u2, right_products)
        common = left.gcd(norm)
        assert int(common.degree()) == hit["gcd_degree"]
        roots = [independent.encode(z) for z in common.roots(multiplicities=False)]
        assert sorted(roots) == sorted(family["roots"])
        for code in roots:
            z = independent.decode(field, code)
            C = (z*z + z) * (target*target + target)
            D = (z + target)**2
            right_outputs = [b for product in right_products
                             for b in independent.quadratic_roots(1 + product, product, right_u2)
                             if (1 + C)*b*b + C*b + D == 0]
            for b in right_outputs:
                L = curve.lift_x(1 + 1/z)
                R = curve.lift_x(1 + 1/b)
                for l in (L, -L):
                    for r in (R, -R):
                        if l + r == raw:
                            witnesses.append({"left_seed": family["left_seed"],
                                              "right_seed": hit["right_seed"],
                                              "left_reciprocal": code,
                                              "right_reciprocal": independent.encode(b),
                                              "left_point": [independent.encode(l[0]), independent.encode(l[1])],
                                              "right_point": [independent.encode(r[0]), independent.encode(r[1])]})
    assert witnesses
    prior = json.loads(PRIOR.read_text())["cases"][0]["first_group_witness"]
    witness = witnesses[0]
    l = curve(*(independent.decode(field, v) for v in witness["left_point"]))
    r = curve(*(independent.decode(field, v) for v in witness["right_point"]))
    assert 4 * l == curve(*(independent.decode(field, v) for v in prior["left_pair_point"]))
    assert 4 * r == curve(*(independent.decode(field, v) for v in prior["right_pair_point"]))
    result = {"status": "PASS_INDEPENDENT_GROUP_REPLAY_OF_UNPINNED_RESIDUAL_HIT",
              "candidate_id": None, "curve_id": protocol["curve_id"],
              "decisions": search["decisions"], "hit": hit,
              "group_witness": witness, "witness_count": len(witnesses),
              "projected_pair_witness_match": True,
              "protocol_sha256": sha(HERE / "audit_protocol.json")}
    with (HERE / "audit_result.json").open("x") as out:
        out.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(result["status"], result["witness_count"], flush=True)


if __name__ == "__main__":
    main()
