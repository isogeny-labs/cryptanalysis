#!/usr/bin/env python3
"""Exact exponent ledger for fixed-genus prime-field DLP strategies.

The factor-base row uses the elementary degree-one smoothness model:

    B = p^beta,
    Pr[g points all lie in B] = p^{-g(1-beta)+o(1)},
    relation collection = p^{g-(g-1)beta+o(1)},
    sparse linear algebra = p^{2 beta+o(1)}.

Balancing the two terms gives beta=g/(g+1) and total exponent 2g/(g+1).

The proved double-large-prime (DLP) variant uses a degree-one factor base
of exponent 1-1/g and has expected time exponent 2-2/g.  Diem's rigorous
general-curve analysis also bounds its large-prime tree storage exponent by
1-1/g+1/g^2.  These bounds require a bounded-degree plane model and a cyclic
degree-zero class group, or known class-group structure.  They do not imply a
subexponential algorithm for fixed genus.
"""

from fractions import Fraction
import json


def encoded(value: Fraction) -> dict[str, object]:
    return {
        "fraction": f"{value.numerator}/{value.denominator}",
        "decimal": float(value),
    }


def row(g: int) -> dict[str, object]:
    rho = Fraction(g, 2)
    beta = Fraction(g, g + 1)
    collection = Fraction(g, 1) - Fraction(g - 1, 1) * beta
    linear_algebra = 2 * beta
    factor_base = max(collection, linear_algebra)

    # Output-sensitive coefficient-lattice route from
    # coefficient_lattice_enumeration.md.
    coefficient_lattice = Fraction(g * g + 2, g + 2)

    # Gaudry--Thome--Theriault--Diem for imaginary hyperelliptic models,
    # and Diem for bounded-degree plane models of general curves.
    double_large_prime_beta = Fraction(g - 1, g)
    double_large_prime = 2 * double_large_prime_beta
    double_large_prime_tree_storage = (
        double_large_prime_beta + Fraction(1, g * g)
    )

    best = min(rho, factor_base, double_large_prime)
    if rho < double_large_prime:
        recommendation = "pollard-rho"
    elif double_large_prime < rho:
        recommendation = "proved-double-large-prime-index-calculus"
    else:
        # In genus two, rho and the DLP variant have the same exponent, while
        # rho avoids graph construction and sparse linear algebra.
        recommendation = "tie; pollard-rho is the conservative default"

    return {
        "genus": g,
        "rho_exponent": encoded(rho),
        "balanced_factor_base_beta": encoded(beta),
        "factor_base_relation_exponent": encoded(collection),
        "factor_base_linear_algebra_exponent": encoded(linear_algebra),
        "factor_base_total_exponent": encoded(factor_base),
        "pencil_coset_single_relation_exponent": encoded(beta),
        "pencil_coset_collection_exponent": encoded(2 * beta),
        "coefficient_lattice_prefix_exponent": encoded(coefficient_lattice),
        "double_large_prime_factor_base_beta": encoded(double_large_prime_beta),
        "double_large_prime_time_exponent": encoded(double_large_prime),
        "double_large_prime_tree_storage_exponent": encoded(
            double_large_prime_tree_storage
        ),
        "best_accounted_baseline_exponent": encoded(best),
        "recommendation": recommendation,
    }


def main() -> None:
    result = {
        "model": "generic fixed genus over growing prime fields",
        "scope": [2, 7],
        "double_large_prime_scope": {
            "curve_representation": "bounded-degree plane model",
            "group": "cyclic degree-zero class group or known group structure",
            "status": "proved expected-time bound",
        },
        "rows": [row(g) for g in range(2, 8)],
        "subexponential_achieved": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
