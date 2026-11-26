#!/usr/bin/env python3
"""Ledger for known-log effective-divisor atom degree tradeoffs."""

import json


def panel(genus, atom_degree):
    return {
        "genus": genus,
        "atom_degree": atom_degree,
        "known_scalar_sourcing_exponent": genus - atom_degree,
        "binary_slots_per_log2_p": genus,
        "section_variables_per_log2_p": atom_degree * genus,
        "semi_regular_explicit_quotient_exponent": atom_degree * genus,
        "orientation_space_exponent": genus,
        "generic_meet_in_middle_exponent": genus / 2,
        "degree_g_atoms_cover_every_jacobian_class": atom_degree == genus,
    }


def main():
    result = {
        "scope": (
            "Prime-field exponent ledger for binary orientations of "
            "known-log effective divisors of degrees one through the genus."
        ),
        "algorithm_claimed": False,
        "panels": [
            panel(genus, atom_degree)
            for genus in range(2, 8)
            for atom_degree in range(1, genus + 1)
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
