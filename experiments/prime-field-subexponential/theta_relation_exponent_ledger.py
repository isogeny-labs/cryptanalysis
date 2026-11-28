#!/usr/bin/env python3
"""Optimize the end-to-end exponent of free-residual theta relations."""

from fractions import Fraction
import json


def record(genus, theta_hit_exponent):
    sigma = Fraction(theta_hit_exponent)
    beta = (sigma + genus - 1) / genus
    if beta > 1:
        beta = Fraction(1)
    collection = sigma + genus - 1 - (genus - 2) * beta
    linear_algebra = 2 * beta
    total = max(collection, linear_algebra)
    return {
        "theta_hit_exponent": str(sigma),
        "optimal_factor_base_exponent": str(beta),
        "relation_collection_exponent": str(collection),
        "sparse_linear_algebra_exponent": str(linear_algebra),
        "total_exponent": str(total),
        "total_exponent_float": float(total),
    }


def main():
    rows = []
    for genus in range(2, 8):
        baseline = Fraction(1) if genus == 2 else Fraction(2 * genus - 2, genus)
        rows.append({
            "genus": genus,
            "best_proven_baseline_exponent": str(baseline),
            "random_theta_probe": record(genus, 1),
            "hypothetical_free_theta_hit": record(genus, 0),
        })
    result = {
        "model": {
            "factor_base_size": "p^beta",
            "theta_hit_cost": "p^sigma",
            "residual_degree": "g-1",
            "usable_residual_probability": "p^{-(g-1)(1-beta)}",
            "relations_required": "p^beta",
            "collection_exponent": "sigma+g-1-(g-2)beta",
            "linear_algebra_exponent": "2beta",
        },
        "rows": rows,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
