#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
evidence = json.loads((ROOT / "artifacts" / "evidence.json").read_text())
theta_diagnostic = json.loads((ROOT / "artifacts" / "complex_theta_diagnostic.json").read_text())
finite_theta = json.loads((ROOT / "artifacts" / "p224_finite_field_theta.json").read_text())
p256_theta = json.loads((ROOT / "artifacts" / "p256_finite_field_theta.json").read_text())
point_map = json.loads((ROOT / "artifacts" / "p224_point_map_status.json").read_text())
p256_status = json.loads((ROOT / "artifacts" / "p256_descent_status.json").read_text())


def assessment(label):
    curve = evidence["curves"][label]
    params = curve["parameters"]
    is_p224 = label == "P-224"
    return {
        "format": "correspondence-assessment-draft-v1",
        "assessment_state": "draft",
        "authority": "companion artifact; not a ledger record or independent certificate",
        "curve": label,
        "source": {
            "object_uid": f"nist-{label.lower()}-cube",
            "representation_uid": "short-weierstrass-product-with-explicit-3-torsion-basis",
            "equations": f"E: y^2=x^3+({params['a']})x+({params['b']}); source E^3",
            "field": f"F_p, p={params['p']}",
            "dimension": 3,
            "subgroup_order": params["n"],
        },
        "destination": {
            "object_uid": f"quotient-{label.lower()}-cube-by-lambda",
            "representation_uid": "p224-descended-plane-quartic-v1" if is_p224 else "p256-cubic-quartic-candidate-v1",
            "equations": "artifacts/p224_descended_quartic.json" if is_p224 else "artifacts/p256_finite_field_theta.json",
            "field": (f"F_p, p={params['p']}; direct Frobenius/Hilbert-90 descent verified" if is_p224 else f"F_(p^3) candidate, p={params['p']}; F_p descent unverified"),
            "dimension": 3,
            "ambient_group_order": None,
        },
        "transformation": {
            "kind": "principally-polarized quotient isogeny candidate",
            "family": "(3,3,3)-isogeny / Tian normal-Weil-set reconstruction",
            "degree": 27,
            "field_of_definition": ("kernel and descended plane quartic are F_p-rational" if is_p224 else "kernel is F_p-rational; candidate quartic is over F_(p^3); F_p descent unverified"),
            "formulas": None,
            "exceptional_cases": [
                "scalar diagonal subgroups of repeated E^3 are audited, but non-scalar End(E)-linear elliptic subvarieties remain",
                ("signed divisor-map twist compatibility remains unverified" if is_p224 else "Frobenius/Hilbert-90 descent and Serre twist remain unverified"),
                "point-map exceptional divisors not available before reconstruction",
            ],
            "normalization": "product principal polarization; standard symplectic E[3] basis",
        },
        "obligations": {
            "existence": {
                "state": "supported",
                "evidence": [
                    "artifacts/evidence.json: exact 27-element F_p-rational maximal isotropic kernel",
                    "factor intersections all have cardinality one",
                    "artifacts/complex_theta_diagnostic.json: 36 nonzero even theta constants on three sampled complex fibers",
                ],
                "scope": ("explicit nonsingular P-224 plane quartic closes the ppav-to-Jacobian existence/descent gate" if is_p224 else "an exact F_(p^3) plane quartic candidate exists; F_p descent remains open"),
            },
            "explicit_construction": {
                "state": "supported" if is_p224 else "partial",
                "evidence": ([
                    "artifacts/p224_finite_field_theta.json: corrected quartic with exact 28/36 theta pattern and seven bitangents",
                    "artifacts/tian_523_control_validation.txt: corrected implementation reproduces Tian's published control quartic",
                    "artifacts/p224_magma_validation.txt: Frobenius-rational moduli and direct Hilbert-90 descent pass",
                    "artifacts/p224_descended_quartic.json: explicit nonsingular 15-term F_p quartic",
                ] if is_p224 else [
                    "artifacts/p256_finite_field_theta.json: exact 28/36 theta pattern, 15-term quartic, and seven bitangent checks",
                    "artifacts/p256_descent_status.json: coefficients are exactly in F_(p^3), not fixed in the displayed coordinates by p-Frobenius",
                    "artifacts/p256_aronhold_frobenius.json: one fixed odd characteristic and nine 3-cycles; only one known Aronhold line stays in the selected system",
                    "handoff/p256_descent_diagnostic.m: preserved independent descent diagnostic",
                ]),
                "scope": ("P-224 quotient plane-quartic construction and descent; signed point map remains open" if is_p224 else "P-256 extension-field quotient candidate; F_p descent remains open"),
            },
            "map_correctness": {
                "state": "partial" if is_p224 else "unknown",
                "evidence": ([
                    "artifacts/p224_point_map_status.json: exact 64-coordinate Kummer map",
                    "all three kernel generators collapse and a transverse 3-torsion control is distinguished",
                ] if is_p224 else ["no executable P-256 source-to-Jacobian map exists"]),
                "scope": "signed divisor recovery, homomorphism, exceptional points, and dual composition remain untested",
            },
            "subgroup_preservation": {
                "state": "supported",
                "evidence": [
                    "gcd(n,3)=1",
                    "ker(pi)=Lambda is killed by 3",
                    "conditional polarized-dual certificate pi^dagger o pi=[3]",
                ],
                "scope": "theorem conditional on constructing the polarized quotient isogeny",
            },
            "computational_advantage": {
                "state": "refuted",
                "evidence": [
                    f"published Tian destination substitution is 2^{curve['cost_model']['destination_minus_rho_log2']:.6f} above the rho operation scale before polylogs and transfer costs"
                ],
                "scope": "only the published genus-3 index-calculus route with q=p; new relation mechanisms remain unknown",
            },
            "scaling_support": {
                "state": "supported",
                "evidence": [
                    "Tian: soft-O(q) for a source E(F_{q^3})",
                    "prime-field substitution q=p gives soft-O(p), versus rho O(sqrt(n)) with n approximately p",
                ],
                "scope": "modeled asymptotics, not measured end-to-end timings",
            },
        },
        "preservation_certificate": {
            "identity": "pi^dagger o pi = [3] for a polarized (3,3,3)-isogeny",
            "kernel_intersection": "Lambda intersect Delta(E[n]) is trivial because Lambda is 3-primary and gcd(n,3)=1",
            "recovery_map": "[3^{-1} mod n] o pi^dagger on the image subgroup",
            "scalar_multiplier": 3,
            "composed_diagonal_identity": "Sum o pi^dagger o pi o Delta = [9], since Sum o Delta=[3]",
            "composed_recovery_to_E": "[9^{-1} mod n] o Sum o pi^dagger",
            "composed_recovery_scalar": params["composed_diagonal_recovery_scalar_9_inverse_mod_n"],
            "proof_artifact": "report.md, Subgroup-preservation certificate",
        },
        "mechanism": {
            "proposed_benefit": "genus-3 factor-base/index-calculus geometry",
            "prediction": "the published Tian route does not beat rho after replacing a cubic-extension source by a prime-field NIST subgroup",
            "falsification_condition": "an explicit NIST transfer plus complete relation collection, linear algebra, descent, and recovery below the matched rho cost",
            "assumptions": [
                "the destination is a genus-3 Jacobian over F_p",
                "the published soft-O(p) relation machinery is the destination solver",
            ],
        },
        "cost_comparison": {
            "workload": "single discrete logarithm in the prime-order NIST subgroup",
            "baseline": curve["cost_model"]["baseline"],
            "units": "modeled log2 group/field scale; no wall-time equivalence claimed",
            "construction": "unmeasured",
            "transfer": "unmeasured",
            "destination": curve["cost_model"]["published_tian_destination_model"],
            "recovery": "unmeasured",
            "verification": ("kernel and normal-Weil identities measured; Tian source control, Frobenius moduli, cocycle, Hilbert-90 descent, smoothness, descended-moduli equality, and Kummer kernel-fiber checks pass" if is_p224 else "kernel and finite-field theta checks measured; extension-field quartic exists; base-field descent unverified"),
            "failed_attempts_and_duplicates": "see attempts.md",
            "memory_and_data": "unmeasured for quotient and destination solver",
            "setup_reuse": "not credited",
            "uncertainty": "soft-O factors and field/group-operation conversion omitted; omission favors the candidate",
            "evidence_label": "modeled",
        },
        "controls": [
            "P-192, P-384, and P-521 mod-3 profiles: zero admissible kernels",
            "exhaustive 1120-Lagrangian census",
            "27 distinct kernel elements and three trivial factor intersections",
            "OpenSSL recomputation of all five p,t mod-3 profiles",
            "complete 13-line scalar-diagonal incidence census for every admissible kernel",
            "three complex periods per kernel with all 36 even theta constants nonzero",
            "729 exact kernel and 4096 exact quotient normal-Weil multiplication identities",
            "Tian q=523 published-quartic source control (passes after unique two-sign correction)",
            "Magma 2.29 Dixmier-Ohno Frobenius-moduli control (P-224 passes)",
            "P-224 exact Kummer images for three kernel generators and one transverse control",
            "P-224 exact Kummer sign collision: the test point and its negative have identical 64-coordinate digests",
            "P-256 exact 28/36 theta pattern and seven Aronhold bitangents",
            "P-256 exact 28-bitangent Frobenius orbit audit (one fixed line, nine 3-cycles)",
            "Q1/Q2 symplectic-pair relabeling changes candidate moduli (failed invariance control)",
            "constant-free and displayed two-Weil-constant candidates have equal moduli (positive scaling control)",
            "all 64 squared theta nulls are invariant under Q1/Q2 relabeling after characteristic permutation",
        ],
        "protocol": {
            "parameter_scope": "NIST P-224 and P-256; ell=3; direct product E^3 over F_p",
            "sample_selection": "complete Lagrangian enumeration, not random sampling",
            "stopping_rules": "construction is complete only after a quartic, map, and dual-composition certificate exist",
            "invalidation_rules": "non-rational kernel, nontrivial factor intersection, singular/non-descending quartic, failed homomorphism, or lost subgroup invalidates the path",
            "hardware_manifest": evidence["environment"],
            "execution_route": "python src/nist_333.py --out artifacts/evidence.json; python src/complex_theta_diagnostic.py --out artifacts/complex_theta_diagnostic.json; python src/finite_field_theta.py --out artifacts/p224_finite_field_theta.json; python src/export_quartic_descent.py; python tests/test_nist_333.py -v; python tests/test_complex_theta_diagnostic.py -v; python tests/test_finite_field_theta.py -v",
        },
        "exploration_boundary": {
            "families": ["direct E^3 (3,3,3) gluing", "Tian normal-Weil-set reconstruction"],
            "parameters": "ell=3 on NIST P-224/P-256",
            "completed_scope": ("torsion fields, exact kernel, finite-field normal-Weil audits, explicit P-224 quartic/descent, Kummer point map, kernel-fiber controls, preservation proof, and asymptotic cost substitution" if is_p224 else "torsion fields, exact kernel, scalar-diagonal census, exact F_(p^3) quartic candidate, preservation proof, and asymptotic cost substitution"),
            "completeness_claim": ("P-224 plane-quartic construction/descent and Kummer map only; none for the signed divisor map or new destination solvers" if is_p224 else "P-256 extension-field quartic candidate only; none for F_p descent, signed point map, or new destination solvers"),
        },
        "composition": {
            "edge_ids": (["diagonal-embedding", "quotient-by-lambda", "p224-ppav-to-jacobian-descended", "source-to-kummer-map", "signed-divisor-map-unconstructed"] if is_p224 else ["diagonal-embedding", "quotient-by-lambda", "p256-cubic-quartic-candidate", "fp-descent-unverified"]),
            "junction_compatibility": ("P-224 quotient curve/descent and Kummer representation are explicit; signed divisor representation is missing" if is_p224 else "P-256 exact F_(p^3) quartic exists; F_p descent and point map are missing"),
            "weakest_open_obligation": ("signed source-to-Jacobian divisor map and executable dual composition" if is_p224 else "F_p descent followed by a signed source-to-Jacobian map"),
        },
        "sources": [
            "https://doi.org/10.1007/s00145-023-09474-2",
            "https://arxiv.org/abs/2012.07173",
            "https://csrc.nist.gov/pubs/fips/186-5/final",
            "https://www.secg.org/sec2-v2.pdf",
        ],
        "open_obligations": [
            ("preserve the accepted P-224 quartic/descent certificate" if is_p224 else "finish indecomposability testing against elliptic subvarieties defined by non-scalar elements of End(E)"),
            "recover and verify a signed source-to-Jacobian divisor map",
            "check pi^dagger o pi=[3] in the executable representation",
            "measure a complete destination workload only if a mechanism different from the already-refuted published substitution is proposed",
        ],
        "recommended_next_action": ("implement Tian's zeta/Groebner signed-divisor recovery, then verify pi^dagger o pi=[3]" if is_p224 else "run handoff/p256_descent_diagnostic.m in Magma and complete Hilbert-90 descent if the cocycle passes"),
        "official_status_change": "none",
    }


out = [assessment("P-224"), assessment("P-256")]
(ROOT / "artifacts" / "assessment.json").write_text(json.dumps(out, indent=2) + "\n")
