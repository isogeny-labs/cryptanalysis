#!/usr/bin/env python3
"""Aggregate the six requested follow-on workstreams without overclaiming."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def read(name):
    return json.loads((ROOT / "artifacts" / name).read_text())


point_map = read("p224_point_map_status.json")
prereq = read("p224_jacobian_prerequisites.json")
p256 = read("p256_descent_status.json")
frobenius = read("p224_frobenius_certificate.json")
complexity = json.loads(
    (ROOT.parent / "hecdlp-cover-reduction" / "artifacts" / "complexity_gate.json").read_text()
)
empirical = json.loads(
    (ROOT.parent / "hecdlp-cover-reduction" / "artifacts" / "empirical_benchmark.json").read_text()
)
end_to_end = json.loads(
    (ROOT.parent / "hecdlp-cover-reduction" / "artifacts" / "end_to_end_hecdlp.json").read_text()
)
signed_control = json.loads(
    (ROOT.parent / "hecdlp-cover-reduction" / "artifacts" / "signed_transfer_benchmark.json").read_text()
)

result = {
    "format": "nist-333-six-follow-ons-v1",
    "items": {
        "1_p224_source_to_jacobian_map": {
            "status": "partial",
            "completed": "exact 64-coordinate source-to-quotient Kummer map",
            "evidence": "artifacts/p224_point_map_status.json",
            "exact_sign_pair_collision": point_map["implemented_map"]["exact_sign_pair_collision"],
            "open": point_map["remaining_obstruction"]["missing_stage"],
        },
        "2_kernel_and_dual_composition": {
            "status": "partial",
            "completed": "all three selected kernel generators collapse exactly; a transverse 3-torsion control does not; theorem-level [3]/[9] recovery scalars are exact",
            "evidence": [
                "artifacts/p224_point_map_status.json",
                "../hecdlp-cover-reduction/artifacts/signed_transfer_benchmark.json",
            ],
            "signed_dual_analogue_checks_pass": signed_control["all_checks_pass"],
            "open": "signed divisor map and executable polarized dual are required for an end-to-end composition test",
        },
        "3_practical_jacobian_representation": {
            "status": "partial",
            "completed": "two rational smooth contact points, rational canonical divisor, and degree-zero/basepoint encoding",
            "evidence": "artifacts/p224_jacobian_prerequisites.json",
            "checks_pass": prereq["verification"]["all_checks_pass"],
            "open": prereq["scope_boundary"]["not_completed"],
        },
        "4_p256_reconstruction_and_descent": {
            "status": "partial_with_obstruction_certificate",
            "completed": "exact F_(p^3) quartic candidate with 28/36 theta pattern and seven bitangent checks",
            "evidence": [
                "artifacts/p256_finite_field_theta.json",
                "artifacts/p256_descent_status.json",
                "artifacts/p256_aronhold_frobenius.json",
                "handoff/p256_descent_diagnostic.m",
            ],
            "open": p256["obstruction_certificate"]["precise_missing_capability"],
            "obstruction_type": p256["obstruction_certificate"]["type"],
        },
        "5_complexity_changing_mechanisms": {
            "status": "complete_for_standard_cover_isogeny_routes",
            "completed": "prime-field subfield obstruction and same-field exponent comparison",
            "evidence": [
                "../hecdlp-cover-reduction/artifacts/complexity_gate.json",
                "../hecdlp-cover-reduction/artifacts/empirical_benchmark.json",
                "../hecdlp-cover-reduction/artifacts/end_to_end_hecdlp.json",
                "../hecdlp-cover-reduction/artifacts/signed_transfer_benchmark.json",
            ],
            "same_field_route_passes": all(
                row["complexity_changing_gate"]["same_field_cover_or_isogeny_passes"]
                for row in complexity["curves"].values()
            ),
            "conclusion": "no standard same-field cover/isogeny route changes the NIST ECDLP exponent; only the explicit pass conditions merit further search",
            "toy_measured_slopes": {
                "rho_group_multiplications_vs_order": empirical["rho"]["fitted_exponent_group_multiplications_vs_order"],
                "quartic_candidate_lines_vs_q": empirical["plane_quartic_relation_collection"]["fitted_exponent_candidate_lines_vs_q"],
                "scope": "measured primitives only; not an end-to-end NIST DLP solve",
            },
            "complete_toy_hecdlp": {
                "curves_solved": len(end_to_end["rows"]),
                "all_target_logs_recovered": all(
                    row["all_target_logs_recovered"] for row in end_to_end["rows"]
                ),
                "relation_candidates_vs_q_slope": end_to_end["fitted_slopes"]["relation_candidates_vs_q"],
                "rho_additions_vs_group_order_slope": end_to_end["fitted_slopes"]["rho_jacobian_additions_vs_group_order"],
                "scope": "complete toy genus-3 HECDLPs; not the unresolved P-224 signed transfer",
            },
        },
        "6_p224_frobenius_l_polynomial": {
            "status": "partial",
            "completed": "exact expected (1-t*T+p*T^2)^3 polynomial and functional-equation checks; one explicit rational bitangent",
            "evidence": "artifacts/p224_frobenius_certificate.json",
            "open": frobenius["certification_status"]["open_obligation"],
            "full_independent_certification": frobenius["certification_status"]["full_independent_certification"],
        },
    },
    "summary": {
        "fully_closed_items": [5],
        "materially_advanced_items": [1, 2, 3, 4, 6],
        "honest_terminal_state": "all six addressed; unavailable end-to-end stages carry executable reproducers or explicit obstruction certificates",
    },
}

(ROOT / "artifacts" / "follow_on_status.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n"
)
print(ROOT / "artifacts" / "follow_on_status.json")
