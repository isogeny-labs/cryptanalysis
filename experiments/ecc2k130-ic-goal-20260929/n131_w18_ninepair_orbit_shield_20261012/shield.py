"""Exact distinct-folded-column shield for the nine-pair orbit SAT circuit.

The underlying nine-pair source and target choice stay unchanged. For every
slot pair, forbid equal pair codes and the 65 unequal code pairs that share a
folded column in the frozen W18 source table.
"""

import argparse
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_ninepair_orbit_20261012"
sys.path.insert(0, str(PARENT))
import orbit9  # noqa: E402

ORIGINAL_BUILD = orbit9.build
ORIGINAL_SOURCES = orbit9.sources
SLOTS = 9
SOURCE_CODES = 33191
CONFLICT_CODE_PAIRS = 65


def source_conflicts():
    columns = {int(mask): int(column) for mask, column in
               (line.split() for line in orbit9.base.SUPPORT.read_text().splitlines())}
    codes, _, _ = orbit9.base.source_domain()
    assert len(codes) == SOURCE_CODES
    incident = defaultdict(list)
    for code in sorted(codes):
        a = orbit9.base.pair.mask_from_code(code)
        b = a ^ orbit9.base.pair.SEED
        assert a in columns and b in columns and columns[a] != columns[b]
        incident[columns[a]].append(code)
        incident[columns[b]].append(code)
    conflicts = {tuple(sorted((left, right)))
                 for codes_at_column in incident.values()
                 for left, right in combinations(codes_at_column, 2)
                 if left != right}
    assert len(conflicts) == CONFLICT_CODE_PAIRS
    return sorted(conflicts)


def mismatch_literals(bits, code):
    """One literal is true exactly when a selected bit differs from code."""
    return [(-wire if code >> bit & 1 else wire)
            for bit, wire in enumerate(bits)]


def shielded_build(target_reciprocals, bdd_root, bdd_nodes):
    circuit, wires = ORIGINAL_BUILD(target_reciprocals, bdd_root, bdd_nodes)
    assert len(wires["selectors"]) == SLOTS
    conflicts = source_conflicts()
    for left_slot, right_slot in combinations(range(SLOTS), 2):
        left_bits, right_bits = (wires["selectors"][left_slot],
                                 wires["selectors"][right_slot])
        assert len(left_bits) == len(right_bits) == 17
        differences = [circuit.xor((left, right))
                       for left, right in zip(left_bits, right_bits)]
        circuit.clauses.append(" ".join(map(str, differences)) + " 0")
        for first_code, second_code in conflicts:
            for a, b in ((first_code, second_code), (second_code, first_code)):
                literals = mismatch_literals(left_bits, a)
                literals += mismatch_literals(right_bits, b)
                circuit.clauses.append(" ".join(map(str, literals)) + " 0")
    return circuit, wires


def sources():
    return {**ORIGINAL_SOURCES(), "source_shield": Path(__file__)}


orbit9.HERE = HERE
orbit9.build = shielded_build
orbit9.sources = sources


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "control", "query"))
    {"freeze": orbit9.freeze, "control": orbit9.control,
     "query": orbit9.query}[parser.parse_args().mode]()
