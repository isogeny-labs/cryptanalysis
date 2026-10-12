"""Exact GF(2) rank receipt for the frozen W20 pair-product basis."""

import hashlib
import json
from pathlib import Path

import linear

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    seed, bits = linear.seven.seed_and_bits()
    basis = linear.seven.product_basis(seed, bits)
    assert len(basis) == len(bits) == 19
    pivots = {}
    for vector in basis:
        reduced = vector
        while reduced:
            pivot = reduced.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = reduced
                break
            reduced ^= pivots[pivot]
        assert reduced != 0
    rank = len(pivots)
    assert rank == 19
    result = {"status": "PASS_W20_PAIR_PRODUCT_BASIS_RANK",
              "field_degree": linear.seven.N, "fixed_seed_mask": seed,
              "source_selector_bits": bits, "product_basis": basis,
              "pivot_coordinates": sorted(pivots), "rank": rank,
              "left_nullity": linear.seven.N-rank,
              "source_sha256": {"script": sha(__file__),
                                "sevenpair": sha(linear.W20 / "sevenpair_circuit.py"),
                                "protocol": sha(HERE / "protocol.json")}}
    with (HERE / "basis_rank_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print("PASS_W20_PAIR_PRODUCT_BASIS_RANK", rank, linear.seven.N-rank)


if __name__ == "__main__":
    main()
