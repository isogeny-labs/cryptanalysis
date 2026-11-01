//! Structural applicability audit for xedni-style ECDLP lifting.
//!
//! Silverman's original algorithm lifts points of `E(F_p)` to rational
//! points and reduces them modulo the rational prime `p`. That construction
//! does not transfer verbatim to `F_{2^m}`: the residue field of `Q` at 2 is
//! only `F_2`. A global lift whose residue field contains `F_{2^m}` must use
//! a number field `K` with a prime of residue degree `m`, and therefore
//! `[K:Q] >= m` because every residue degree is at most the field degree.
//!
//! This module records that exact domain boundary. It does not implement a
//! discrete-log attack and it does not extrapolate the prime-field failure
//! theorem to number fields. In particular, Kogure's 2002 characteristic-two
//! xedni report is a primary-source gate for binary and Koblitz variants.

use serde::Serialize;

use crate::cryptanalysis::curve_catalog::{CatalogCurve, CurveObject, Family};

/// Machine-readable result of checking one catalog curve against the lift
/// domain of the original xedni algorithm.
#[derive(Clone, Debug, Serialize)]
pub struct XedniAssessment {
    pub curve: &'static str,
    pub family: &'static str,
    pub field: String,
    pub residue_characteristic: String,
    pub residue_degree: u32,
    pub minimum_global_field_degree: u32,
    pub original_rational_lift: bool,
    pub applicability: &'static str,
    pub evidence_status: &'static str,
    pub obstruction_or_gate: String,
    pub next_check: &'static str,
    pub sources: Vec<&'static str>,
}

/// Assess one exact catalog curve without running an experiment.
pub fn assess(curve: &CatalogCurve) -> XedniAssessment {
    let (characteristic, residue_degree) = match &curve.object {
        CurveObject::Prime(c) => (c.p.to_string(), 1),
        CurveObject::Binary(c) => ("2".to_string(), c.m),
        CurveObject::Char3(c) => ("3".to_string(), c.m),
    };
    let field = curve.field().label;

    match curve.family {
        Family::Prime => XedniAssessment {
            curve: curve.name,
            family: curve.family.tag(),
            field,
            residue_characteristic: characteristic,
            residue_degree,
            minimum_global_field_degree: 1,
            original_rational_lift: true,
            applicability: "original-domain-analyzed-negative",
            evidence_status: "conditional-theorem-plus-experiments",
            obstruction_or_gate: "JKSST Theorem 4.1 proves success probability < C0/p under Lang's canonical-height conjecture and the stated discriminant/height assumption; their experiments found only tiny lift relations and prohibitively low useful-lift rates.".to_string(),
            next_check: "No repeat of the classic lift is indicated; a variant must state which JKSST assumption or coefficient bound it changes.",
            sources: vec![
                "Silverman 2000, DCC 20(1):5-40, doi:10.1023/A:1008319518035",
                "Jacobson-Koblitz-Silverman-Stein-Teske 2000, DCC 20(1):41-64, doi:10.1023/A:1008312401197",
            ],
        },
        Family::BinaryRandom | Family::Koblitz => {
            let family_note = if curve.family == Family::Koblitz {
                "The Koblitz curve equation descends to F_2, but the ECDLP points live in E(F_{2^m}); lifting those coordinates still requires residue degree m."
            } else {
                "Both the curve coefficients and ECDLP point coordinates live over F_{2^m}."
            };
            XedniAssessment {
                curve: curve.name,
                family: curve.family.tag(),
                field,
                residue_characteristic: characteristic,
                residue_degree,
                minimum_global_field_degree: residue_degree,
                original_rational_lift: false,
                applicability: "degree-m-number-field-generalization-required",
                evidence_status: "primary-source-gated",
                obstruction_or_gate: format!(
                    "Q has residue field F_2 at 2, not F_{{2^{residue_degree}}}. Any number field K with a prime of residue degree {residue_degree} satisfies [K:Q] >= {residue_degree}. {family_note} Kogure's characteristic-two/Koblitz xedni report is identified bibliographically but its primary text has not yet been obtained."
                ),
                next_check: "Obtain and read Kogure ISEC2002-10 before specifying a characteristic-two lift, dependence test, or experiment.",
                sources: vec![
                    "Kogure 2002, xedni calculus method (characteristic 2), IEICE Technical Report ISEC2002-10, pp.57-60, NDL 6188214",
                    "Jacobson-Koblitz-Silverman-Stein-Teske 2000, DCC 20(1):41-64, doi:10.1023/A:1008312401197",
                ],
            }
        }
        Family::Extension | Family::Char3 => XedniAssessment {
            curve: curve.name,
            family: curve.family.tag(),
            field,
            residue_characteristic: characteristic,
            residue_degree,
            minimum_global_field_degree: residue_degree,
            original_rational_lift: false,
            applicability: "extension-field-generalization-required",
            evidence_status: "outside-reviewed-source-domain",
            obstruction_or_gate: format!(
                "The original rational lift covers prime fields. A global field realizing residue degree {residue_degree} must have degree at least {residue_degree}; no reviewed source in this audit supplies the required extension-field dependence analysis."
            ),
            next_check: "Identify and read a primary source for this characteristic and extension degree before designing a lift.",
            sources: vec![
                "Jacobson-Koblitz-Silverman-Stein-Teske 2000, DCC 20(1):41-64, doi:10.1023/A:1008312401197",
            ],
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::curve_catalog::by_name;

    #[test]
    fn prime_field_is_the_original_domain_with_conditional_negative_analysis() {
        let curve = by_name("p256").expect("P-256");
        let row = assess(&curve);
        assert!(row.original_rational_lift);
        assert_eq!(row.residue_degree, 1);
        assert_eq!(row.minimum_global_field_degree, 1);
        assert_eq!(row.applicability, "original-domain-analyzed-negative");
        assert!(row.obstruction_or_gate.contains("Theorem 4.1"));
        assert!(row.obstruction_or_gate.contains("under Lang's"));
    }

    #[test]
    fn random_binary_lift_requires_degree_at_least_m() {
        let curve = by_name("sect163r1").expect("B-163");
        let row = assess(&curve);
        assert_eq!(row.family, "binary");
        assert!(!row.original_rational_lift);
        assert_eq!(row.residue_characteristic, "2");
        assert_eq!(row.residue_degree, 163);
        assert_eq!(row.minimum_global_field_degree, 163);
        assert!(row.obstruction_or_gate.contains("[K:Q] >= 163"));
    }

    #[test]
    fn koblitz_curve_coefficients_do_not_remove_the_point_lift_degree() {
        let curve = by_name("sect163k1").expect("K-163");
        let row = assess(&curve);
        assert_eq!(row.family, "koblitz");
        assert_eq!(row.minimum_global_field_degree, 163);
        assert!(row.obstruction_or_gate.contains("equation descends to F_2"));
        assert!(row
            .obstruction_or_gate
            .contains("points live in E(F_{2^m})"));
        assert_eq!(row.evidence_status, "primary-source-gated");
    }
}
