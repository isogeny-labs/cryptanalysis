"""Exact binary selection of four raw fibers and an n-cycle Frobenius orbit."""


def mux(circuit, flag, zero, one):
    """Return zero when flag is false and one when flag is true."""
    return circuit.xor((zero, circuit.and_(flag, circuit.xor((zero, one)))))


def build(circuit, reciprocals, n, square, frobenius):
    """Return bits for one of four n-long Frobenius orbits, with selector wires.

    `reciprocals[f*n+j]` must equal Frobenius^j of its fiber's first entry.
    Invalid binary rotation codes are explicitly excluded by CNF clauses.
    """
    assert n > 1 and len(reciprocals) == 4 * n
    base_values = [reciprocals[fiber * n] for fiber in range(4)]
    for fiber, value in enumerate(base_values):
        for rotation in range(n):
            assert value == reciprocals[fiber * n + rotation]
            value = square(value)
        assert value == base_values[fiber]
    fiber_bits = [circuit.variable() for _ in range(2)]
    rotation_bits = [circuit.variable() for _ in range((n - 1).bit_length())]
    bits = []
    for bit in range(n):
        values = [-1 if value >> bit & 1 else 0 for value in base_values]
        low = mux(circuit, fiber_bits[0], values[0], values[1])
        high = mux(circuit, fiber_bits[0], values[2], values[3])
        bits.append(mux(circuit, fiber_bits[1], low, high))
    for exponent_bit, flag in enumerate(rotation_bits):
        images = [frobenius(1 << bit, 1 << exponent_bit)
                  for bit in range(n)]
        transformed = circuit.linear_element(bits, images)
        bits = [mux(circuit, flag, old, new)
                for old, new in zip(bits, transformed)]
    for invalid in range(n, 1 << len(rotation_bits)):
        clause = [(-wire if invalid >> bit & 1 else wire)
                  for bit, wire in enumerate(rotation_bits)]
        circuit.clauses.append(" ".join(map(str, clause)) + " 0")
    return bits, fiber_bits, rotation_bits
