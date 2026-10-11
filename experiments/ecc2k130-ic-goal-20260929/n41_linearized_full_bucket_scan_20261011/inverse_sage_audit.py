"""Independently replay every inverse-join row, solving S3 from right to left."""

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
GEOMETRY = BASE / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def element(field, word):
    return sum((field.gen()**i for i in range(41) if word >> i & 1), field.zero())


def word(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial()))


def selected(values, mask):
    return sum((value for i, value in enumerate(values) if mask >> i & 1),
               values[0].parent().zero())


def quadratic_roots(a, b, c):
    if a == 0:
        assert b != 0
        return [c/b]
    if b == 0:
        return [(c/a)**(1 << 40)]
    v = a*c/(b*b)
    if v.trace() != 0:
        return []
    h = c.parent().zero()
    x = v
    for _ in range(21):
        h += x
        x = x**4
    ratio = b/a
    result = [ratio*h, ratio*(h+1)]
    assert all(a*x*x+b*x+c == 0 for x in result)
    return result


def family_map(basis):
    field = basis[0].parent()
    w_basis = [u*u+u for u in basis]
    output = {}
    count = 0
    for seed in range(1, 64):
        u_s = selected(basis, seed)
        w_s = selected(w_basis, seed)
        products = {selected(w_basis, a)**2+w_s*selected(w_basis, a)
                    for a in range(64)}
        assert len(products) == 32
        for p in products:
            assert 1+p != 0
            for z in quadratic_roots(1+p, p, u_s*u_s):
                output.setdefault(word(z), set()).add(seed)
                count += 1
    return output, count


def main():
    protocol = json.loads((HERE / "inverse_sage_protocol.json").read_text())
    paths = {"source": Path(__file__), "geometry": GEOMETRY,
             "targets": HERE / "targets.json", "inverse_result": HERE / "inverse_result.json",
             "runtime": HERE / "inverse_sage_runtime_info.json"}
    assert protocol["sha256"] == {name: sha(path) for name, path in paths.items()}
    start = time.monotonic_ns()
    binary = PolynomialRing(GF(2), "t")
    t = binary.gen()
    field = GF(2**41, "t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    geometry = json.loads(GEOMETRY.read_text())["n41"]
    left_basis = [element(field, x) for x in geometry["window_basis_halftrace"][2]]
    right_basis = [element(field, x) for x in geometry["window_basis_halftrace"][3]]
    left, left_factor_roots = family_map(left_basis)
    right, right_factor_roots = family_map(right_basis)
    setup_ns = time.monotonic_ns()-start
    assert len(left) == len(right) == 1984
    targets = json.loads((HERE / "targets.json").read_text())["rows"]
    previous = json.loads((HERE / "inverse_result.json").read_text())["rows"]
    rows = []
    for target, expected in zip(targets, previous):
        assert (target["kind"], target["option"]) == (expected["kind"], expected["option"])
        raw = curve(*(element(field, v) for v in target["raw_xy"]))
        q = 1/(raw[0]+1)
        assert word(q) == target["target_z"]
        query_start = time.monotonic_ns()
        hits = set()
        roots_examined = 0
        for b_word, right_seeds in right.items():
            b = element(field, b_word)
            C = (b*b+b)*(q*q+q)
            D = (b+q)**2
            for a in quadratic_roots(1+C, C, D):
                roots_examined += 1
                a_word = word(a)
                for left_seed in left.get(a_word, ()):
                    for right_seed in right_seeds:
                        hits.add((left_seed, right_seed, a_word, b_word))
        found = sorted(hits)
        expected_hits = sorted((h["left_seed"], h["right_seed"],
                                h["left_z"], h["right_z"]) for h in expected["hits"])
        assert found == expected_hits and expected["status"] == "COMPLETE"
        rows.append({"kind": target["kind"], "option": target["option"],
                     "roots_examined": roots_examined, "hits": [list(x) for x in found],
                     "query_ns": time.monotonic_ns()-query_start})
        print(json.dumps({"kind": target["kind"], "option": target["option"],
                          "roots_examined": roots_examined, "hits": len(found)}), flush=True)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak = peak if sys.platform == "darwin" else peak*1024
    result = {"status": "PASS_COMPLETE_OPPOSITE_ORIENTATION", "candidate_id": None,
              "left_distinct_coordinates": len(left), "right_distinct_coordinates": len(right),
              "left_factor_roots": left_factor_roots,
              "right_factor_roots": right_factor_roots,
              "setup_ns": setup_ns, "rows": rows, "peak_rss_bytes": peak,
              "source_sha256": sha(Path(__file__)),
              "protocol_sha256": sha(HERE / "inverse_sage_protocol.json")}
    (HERE / "inverse_sage_audit.json").write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"status": result["status"], "rows": len(rows)}))


if __name__ == "__main__":
    main()
