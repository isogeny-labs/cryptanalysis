//! Independent affine checks after generic triangular-basis recovery.
//! No target labels or generating tuples are inputs to these functions.
use crate::recovery::{Basis, Limits, Result};
use num_bigint::BigUint;
use std::collections::BTreeSet;
use torus_s4::{Curve, Point};
use torus_s4_tree::{TreeInput, TreeSystem};

#[derive(Debug, PartialEq, Eq)]
pub struct CheckedSum {
    pub us: Vec<BigUint>,
    pub negative: Vec<bool>,
}

/// Check membership in the union without evaluating the auxiliary circuit,
/// lift every coordinate, and enumerate at most 256 actual group sums.
pub fn verify_sum(input: &TreeInput, us: &[BigUint]) -> Result<CheckedSum> {
    // Validate the public card, including arity and beta/chart constraints.
    TreeSystem::compile(input)?;
    if us.len() != input.arity {
        return Err("sum arity mismatch".into());
    }
    let curve = Curve::from_case(&input.curve)?;
    let mut ordered = us.to_vec();
    ordered.sort();
    let mut points: Vec<Point> = vec![];
    for u in &ordered {
        if u >= &curve.f.p {
            return Err("noncanonical u".into());
        }
        let mut member = false;
        for beta in &input.betas {
            let mut c = input.curve.clone();
            c.beta = beta.clone();
            member |= curve.member(&c, u)?;
        }
        if !member {
            return Err("coordinate is not in any membership branch".into());
        }
        let v = curve
            .f
            .sqrt(&curve.rhs(u))?
            .ok_or("nonrational curve lift")?;
        points.push(Some((u.clone(), v)));
    }
    let target = input.curve.point()?;
    for mask in 0..(1usize << input.arity) {
        let mut sum = None;
        for (i, p) in points.iter().enumerate() {
            let (u, v) = p.as_ref().ok_or("unexpected identity leaf")?;
            let v = if mask >> i & 1 == 1 {
                curve.f.sub(&0u32.into(), v)
            } else {
                v.clone()
            };
            sum = curve.add(&sum, &Some((u.clone(), v)))?;
        }
        if sum == target {
            // This checks the complete raw relation; clearing cofactor on
            // both sides therefore also agrees with the public prime target.
            if curve.times(&sum, 8)? != curve.times(&target, 8)? {
                return Err("cofactor transport mismatch".into());
            }
            return Ok(CheckedSum {
                us: ordered,
                negative: (0..input.arity).map(|i| mask >> i & 1 != 0).collect(),
            });
        }
    }
    Err("no rational signed sum equals public target".into())
}

/// Positive certificates only. Empty output is never an absence certificate.
pub fn recover_sums(
    input: &TreeInput,
    tree: &TreeSystem,
    basis: &Basis,
    limits: &mut Limits,
) -> Result<(usize, Vec<CheckedSum>)> {
    if basis.variables != tree.system.variables.len() {
        return Err("basis/system variable mismatch".into());
    }
    let f = input.curve.field()?;
    let assignments = basis.assignments(&f, limits)?;
    let count = assignments.len();
    let mut seen = BTreeSet::new();
    let mut checked = vec![];
    for values in assignments {
        tree.system.check(&values)?;
        let mut us = vec![];
        for y in &values[..input.arity] {
            let den = f.sub(&1u32.into(), y);
            let Ok(inv) = f.inv(&den) else {
                break;
            };
            us.push(f.mul(&f.add(&1u32.into(), y), &inv));
        }
        if us.len() != input.arity {
            continue;
        }
        if let Ok(certificate) = verify_sum(input, &us) {
            if seen.insert(certificate.us.clone()) {
                checked.push(certificate);
            }
        }
    }
    Ok((count, checked))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::recovery::{parse_basis, Term};
    use torus_s4_tree::actual_four_control;

    #[test]
    fn actual_four_public_point_certificate_and_mutations() {
        let (_, input, _, points) = actual_four_control().unwrap();
        let us: Vec<_> = points
            .iter()
            .map(|p| p.as_ref().unwrap().0.clone())
            .collect();
        let cert = verify_sum(&input, &us).unwrap();
        assert_eq!(cert.us.len(), 4);
        let mut wrong = us.clone();
        wrong[0] = 0u32.into();
        assert!(verify_sum(&input, &wrong).is_err());
        assert!(verify_sum(&input, &us[..3]).is_err());
        let mut wrong_target = input.clone();
        let c = Curve::from_case(&input.curve).unwrap();
        let p = c
            .add(&input.curve.point().unwrap(), &points[0])
            .unwrap()
            .unwrap();
        wrong_target.curve.target = [
            p.0.to_string().parse().unwrap(),
            p.1.to_string().parse().unwrap(),
        ];
        assert!(verify_sum(&wrong_target, &us).is_err());
    }

    #[test]
    fn actual_four_known_assignment_exercises_recovery_without_solver_claim() {
        let (_, input, tree, points) = actual_four_control().unwrap();
        let values = tree.witness(&input, &points).unwrap();
        // A synthetic linear basis isolates a known assignment. This tests
        // root recovery at actual p and dimension; it is not a solver output.
        let n = values.len();
        let f = input.curve.field().unwrap();
        let basis = Basis {
            variables: n,
            engine_reported_unit: false,
            equations: values
                .iter()
                .enumerate()
                .map(|(i, v)| {
                    let mut exponents = vec![0; n];
                    exponents[i] = 1;
                    vec![
                        Term {
                            coefficient: 1u32.into(),
                            exponents,
                        },
                        Term {
                            coefficient: f.sub(&0u32.into(), v),
                            exponents: vec![0; n],
                        },
                    ]
                })
                .collect(),
        };
        let (count, certs) = recover_sums(&input, &tree, &basis, &mut Limits::default()).unwrap();
        assert_eq!(count, 1);
        assert_eq!(certs.len(), 1);
        assert_eq!(certs[0].us.len(), 4);
        let unit = parse_basis("ROOTS_UNIT\nROOTS_DONE\n", n, &f).unwrap();
        let (count, certs) = recover_sums(&input, &tree, &unit, &mut Limits::default()).unwrap();
        assert_eq!(count, 0);
        assert!(certs.is_empty());
        let mut invalid = basis;
        invalid.equations[0][1].coefficient =
            f.add(&invalid.equations[0][1].coefficient, &1u32.into());
        assert!(recover_sums(&input, &tree, &invalid, &mut Limits::default()).is_err());
    }
}
