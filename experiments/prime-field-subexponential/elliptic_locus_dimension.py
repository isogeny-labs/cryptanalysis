#!/usr/bin/env python3
"""Dimension ledger for the elliptic-cover locus in hyperelliptic moduli."""

import json


def row(genus):
    degree = (genus + 2) // 2
    hyperelliptic_dimension = 2 * genus - 1
    if genus == 2:
        cover_locus_dimension_bound = 2
        reason = "extra-involution branch locus"
    else:
        cover_locus_dimension_bound = 2 * degree - 1
        reason = "elliptic modulus plus Rat_d/PGL2"
    codimension = hyperelliptic_dimension - cover_locus_dimension_bound
    assert codimension > 0
    return {
        "genus": genus,
        "cover_degree": degree,
        "hyperelliptic_moduli_dimension": hyperelliptic_dimension,
        "elliptic_cover_locus_dimension_upper_bound": (
            cover_locus_dimension_bound
        ),
        "codimension_lower_bound": codimension,
        "finite_field_density_upper_bound": f"O(p^-{codimension})",
        "dimension_bound_reason": reason,
    }


def main():
    result = {
        "scope": "fixed genus, sufficiently large odd prime fields",
        "rows": [row(genus) for genus in range(2, 8)],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
