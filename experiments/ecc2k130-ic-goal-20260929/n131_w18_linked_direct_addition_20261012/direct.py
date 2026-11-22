"""Direct x-only linked-pair addition gate for the frozen N131 ten-pair circuit."""

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n131_w18_tenpair_linked_frob_20261012"
sys.path.insert(0, str(PRIOR))
import ten as prior  # noqa: E402

base = prior.base
pair = prior.pair
ORIGINAL_BUILD = prior.build
ORIGINAL_SOURCES = prior.sources
ROTATION = 16


def halftrace_linear(value):
    """Halftrace as an F2-linear map, including inputs of trace one."""
    result = 0
    for _ in range((pair.N + 1) // 2):
        result ^= value
        value = pair.gf_square(pair.gf_square(value))
    return result


def build(target_reciprocals, bdd_root, bdd_nodes):
    circuit, wires = ORIGINAL_BUILD(target_reciprocals, bdd_root, bdd_nodes)
    algebra = base.Algebra(circuit, base.Field(), dense_and_threshold=3000)
    a = algebra.from_bits(wires["outputs"][0])
    u = algebra.from_bits(wires["intermediates"][0])
    x_bits = [circuit.variable() for _ in range(pair.N)]
    x = algebra.from_bits(x_bits)
    circuit.require_zero(algebra.add(algebra.mul(a, x), algebra.one).bits())

    rhs = algebra.add(x, algebra.square(a))
    ht_basis = [halftrace_linear(1 << bit) for bit in range(pair.N)]
    h = algebra.from_bits(circuit.linear_element(rhs.bits(), ht_basis))
    circuit.require_zero(algebra.add(algebra.square(h), h, rhs).bits())
    y = algebra.mul(x, h)
    frob_basis = [pair.gf_frobenius(1 << bit, ROTATION)
                  for bit in range(pair.N)]
    X = algebra.from_bits(circuit.linear_element(x.bits(), frob_basis))
    Y = algebra.from_bits(circuit.linear_element(y.bits(), frob_basis))
    d = algebra.add(x, X)
    s = algebra.add(y, Y)
    d2 = algebra.square(d)
    numerator = algebra.add(algebra.mul(d2, d), algebra.square(s),
                            algebra.mul(s, d))
    circuit.require_zero(algebra.add(algebra.mul(u, numerator), d2).bits())
    circuit.clauses.append(" ".join(map(str, d.bits())) + " 0")
    wires["linked_x_inverse"] = x_bits
    return circuit, wires


def sources():
    result = ORIGINAL_SOURCES()
    result["balanced_runner"] = Path(__file__)
    result["linked_direct_addition"] = Path(__file__)
    return result


prior.HERE = HERE
prior.orbit9.HERE = HERE
prior.build = build
prior.orbit9.build = build
prior.sources = sources
prior.orbit9.sources = sources


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "control", "query"))
    choice = parser.parse_args().mode
    {"freeze": prior.freeze, "control": prior.control,
     "query": prior.query}[choice]()
