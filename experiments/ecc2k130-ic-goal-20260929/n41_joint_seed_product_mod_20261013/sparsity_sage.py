"""Measure exact coefficient support of the reusable N41 left polynomial."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

spec_path = Path(__file__).resolve()
HERE = spec_path.parent
GOAL = HERE.parent
PARENT = GOAL / "n41_symbolic_two_bucket_20261011/run.py"
spec = importlib.util.spec_from_file_location("two_bucket_parent_sparsity", PARENT)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "sparsity_protocol.json").read_text())
    files = {"script": HERE / "sparsity_sage.py", "parent": PARENT,
             "global_result": HERE / "global_result.json",
             "sage_runtime": HERE / "sage_runtime_info.json"}
    assert {key: sha(path) for key, path in files.items()} == p["sha256"]
    start = time.monotonic_ns()
    _field, _curve, ring, _geometry, _left, _right, left_polys = parent.setup()
    setup_ns = time.monotonic_ns() - start
    product = ring.one()
    for poly in left_polys.values():
        product *= poly
    product_ns = time.monotonic_ns() - start - setup_ns
    degree = int(product.degree())
    assert degree == json.loads((HERE / "global_result.json").read_text())["global_left_degree"]
    coefficients = [[i, parent.control.integer(product[i])]
                    for i in range(degree + 1) if product[i] != 0]
    assert coefficients[0][0] >= 0 and coefficients[-1][0] == degree
    result = {"status": "PASS_EXACT_N41_GLOBAL_PRODUCT_COEFFICIENT_CENSUS",
              "degree": degree, "coefficient_count": degree + 1,
              "nonzero_coefficients": len(coefficients),
              "zero_coefficients": degree + 1 - len(coefficients),
              "setup_ns": setup_ns, "product_ns": product_ns,
              "protocol_sha256": sha(HERE / "sparsity_protocol.json")}
    with (HERE / "sparsity_result.json").open("x") as out:
        out.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    with (HERE / "nonzero_coefficients.json").open("x") as out:
        out.write(json.dumps(coefficients, separators=(",", ":")) + "\n")
    print(result["status"], len(coefficients), degree + 1, flush=True)


if __name__ == "__main__":
    main()
