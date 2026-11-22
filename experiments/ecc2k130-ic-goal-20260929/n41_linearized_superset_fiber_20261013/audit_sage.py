"""Independent pair-quadratic replay of valid and excluded product outputs."""

import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
protocol = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
invalid = json.loads((HERE / "invalid_control.json").read_text())
fiber = json.loads((GOAL / "n41_symbolic_seed_fiber_20261012/panel.json").read_text())
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
assert invalid["status"] == "PASS_INVALID_SUPERSET_ROOT_REJECTED"
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**41, name="t", modulus=t**41+t**3+1)
ring = PolynomialRing(field, "c")


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(41)]))


seeds = [decode(seed << 1)**(1 << rotation)
         for seed, rotation in zip(fiber["seeds"], fiber["rotations"])]
products = [[(decode(x << 1)*decode(y << 1))**(1 << fiber["rotations"][slot])
             for x, y in fiber["ordered_masks"][slot]]
            for slot in range(2)]


def pair_roots(seed, product):
    equation = ring([seed*seed, product, 1+product*product])
    assert equation != 0
    return [root for root, _ in equation.roots()]


left = [pair_roots(seeds[0], p) for p in products[0]]
right = [pair_roots(seeds[1], q) for q in products[1]]
assert all(len(roots) == 2 for roots in left+right)


def matches(value, right_roots=right):
    return sum((1+(c*d)**2)*value**2+c*d*value+(c+d)**2 == 0
               for left_roots in left for right_list in right_roots
               for c in left_roots for d in right_list)


positive_v = decode(result["cases"][0]["hits"][0]["right_reciprocal"])
invalid_v = decode(invalid["control"]["four_atom_reciprocal"])
bad_q = decode(invalid["control"]["invalid_product"])
assert bad_q not in products[1]
positive_matches = matches(positive_v)
invalid_valid_matches = matches(invalid_v)
invalid_bad_matches = matches(invalid_v, [pair_roots(seeds[1], bad_q)])
assert positive_matches > 0
assert invalid_valid_matches == 0
assert invalid_bad_matches > 0
output = {
    "status": "PASS_INDEPENDENT_PAIR_EQUATION_SOURCE_FILTER_AUDIT",
    "positive_valid_pair_equation_matches": positive_matches,
    "invalid_valid_pair_equation_matches": invalid_valid_matches,
    "invalid_excluded_pair_equation_matches": invalid_bad_matches,
    "valid_pair_product_counts": [len(p) for p in products],
    "invalid_product": invalid["control"]["invalid_product"],
    "source_sha256": {
        "protocol": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
        "query_result": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest(),
        "invalid_control": hashlib.sha256((HERE / "invalid_control.json").read_bytes()).hexdigest(),
        "auditor": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    },
}
with (HERE / "audit.json").open("x") as stream:
    json.dump(output, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(output["status"], positive_matches, invalid_bad_matches, flush=True)
