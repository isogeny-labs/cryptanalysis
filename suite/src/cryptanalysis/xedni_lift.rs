//! Exact affine-lattice optimization for the coefficient-lifting stage of xedni.
//!
//! Steps 7--9 of the original algorithm search an affine lattice of cubic
//! coefficient vectors: every vector must pass through the selected rational
//! lifts and remain in a prescribed residue class.  The 2000 implementation
//! used HNF-derived short vectors and then varied them to reduce the curve
//! discriminant.  This module makes that seam explicit and certifiable:
//!
//! * LLL reduces a supplied basis of admissible coefficient changes;
//! * Babai nearest-plane finds a short representative of the affine coset;
//! * a bounded, deterministic neighborhood search minimizes the *exact*
//!   generalized-Weierstrass discriminant, with coefficient height as a
//!   tie-breaker;
//! * exact linear constraints and coefficient congruences are checked before
//!   the search and again on the result.
//!
//! This is a lift optimizer, not a discrete-log attack.  It can improve a
//! constant in the classic prime-field construction, but it does not evade the
//! conditional asymptotic obstruction proved by Jacobson--Koblitz--Silverman--
//! Stein--Teske.  Nor does it provide the degree-`m` number-field construction
//! needed over `F_{2^m}`.

use num_bigint::BigInt;
use num_traits::{ToPrimitive, Zero};
use serde::{Deserialize, Serialize};

use crate::cryptanalysis::lattice::lll_reduce_hp;

/// The signed coefficient order used by the xedni paper's `B` matrix:
/// `(a0, a1, a3, -a00, -a2, -a4, -a6)`.
pub const WEIERSTRASS_COEFFICIENTS: usize = 7;

/// One affine lattice of admissible curve coefficients.
#[derive(Clone, Debug)]
pub struct AffineLiftProblem {
    /// Any feasible coefficient vector.
    pub particular: Vec<BigInt>,
    /// Basis vectors that preserve every exact constraint and congruence.
    pub directions: Vec<Vec<BigInt>>,
    /// Rows `b` for which `b * coefficients` must equal the value at
    /// `particular`.  Xedni uses the point-incidence matrix here.
    pub exact_constraints: Vec<Vec<BigInt>>,
    /// If present, every result must be coefficientwise congruent to
    /// `particular` modulo this positive modulus.
    pub congruence_modulus: Option<BigInt>,
}

/// Decimal-string JSON form accepted by the CLI.  Strings avoid narrowing
/// the arbitrary-precision coefficients in JSON implementations.
#[derive(Clone, Debug, Deserialize)]
pub struct AffineLiftInput {
    pub particular: Vec<String>,
    pub directions: Vec<Vec<String>>,
    #[serde(default)]
    pub exact_constraints: Vec<Vec<String>>,
    pub congruence_modulus: Option<String>,
}

fn parse_decimal(value: &str, field: &str) -> Result<BigInt, String> {
    value
        .parse::<BigInt>()
        .map_err(|_| format!("{field} contains a non-decimal integer: {value:?}"))
}

impl TryFrom<AffineLiftInput> for AffineLiftProblem {
    type Error = String;

    fn try_from(value: AffineLiftInput) -> Result<Self, Self::Error> {
        let particular = value
            .particular
            .iter()
            .map(|x| parse_decimal(x, "particular"))
            .collect::<Result<_, _>>()?;
        let directions = value
            .directions
            .iter()
            .map(|row| row.iter().map(|x| parse_decimal(x, "directions")).collect())
            .collect::<Result<_, _>>()?;
        let exact_constraints = value
            .exact_constraints
            .iter()
            .map(|row| {
                row.iter()
                    .map(|x| parse_decimal(x, "exact_constraints"))
                    .collect()
            })
            .collect::<Result<_, _>>()?;
        let congruence_modulus = value
            .congruence_modulus
            .as_deref()
            .map(|x| parse_decimal(x, "congruence_modulus"))
            .transpose()?;
        Ok(Self {
            particular,
            directions,
            exact_constraints,
            congruence_modulus,
        })
    }
}

/// Deterministic bounded-search controls.
#[derive(Clone, Copy, Debug)]
pub struct LiftSearchOptions {
    /// Enumerate this distance on either side of each Babai coefficient.
    pub neighborhood_radius: i64,
    /// Hard cap on exact objective evaluations.
    pub max_candidates: usize,
}

impl Default for LiftSearchOptions {
    fn default() -> Self {
        Self {
            neighborhood_radius: 2,
            max_candidates: 50_000,
        }
    }
}

/// Exact objective values, serialized without narrowing big integers.
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct LiftScore {
    pub nonsingular: bool,
    pub discriminant_bits: u64,
    pub coefficient_height_bits: u64,
    pub squared_l2_norm: String,
    pub discriminant: String,
}

/// Certified output of the affine-CVP search.
#[derive(Clone, Debug, Serialize)]
pub struct LiftOptimization {
    pub method: &'static str,
    pub baseline_coefficients: Vec<String>,
    pub babai_coefficients: Vec<String>,
    pub optimized_coefficients: Vec<String>,
    pub baseline_score: LiftScore,
    pub babai_score: LiftScore,
    pub optimized_score: LiftScore,
    pub candidates_evaluated: usize,
    pub exact_constraints_preserved: bool,
    pub congruence_preserved: bool,
}

fn dot(a: &[BigInt], b: &[BigInt]) -> BigInt {
    a.iter().zip(b).map(|(x, y)| x * y).sum()
}

fn abs_bits(x: &BigInt) -> u64 {
    x.magnitude().bits()
}

fn signed_weierstrass_discriminant(c: &[BigInt]) -> Result<BigInt, String> {
    if c.len() != WEIERSTRASS_COEFFICIENTS {
        return Err(format!(
            "expected {WEIERSTRASS_COEFFICIENTS} signed Weierstrass coefficients, got {}",
            c.len()
        ));
    }
    let a0 = &c[0];
    let a1 = &c[1];
    let a3 = &c[2];
    let a00 = -&c[3];
    let a2 = -&c[4];
    let a4 = -&c[5];
    let a6 = -&c[6];

    // Completing the square gives
    // (2 a0 y + a1 x + a3)^2 = A x^3 + B x^2 + C x + D.
    // The cubic polynomial discriminant is 16 times the usual elliptic-curve
    // discriminant in the monic standard case.  The constant factor is
    // irrelevant to ordering, while this form remains integral for a0,a00 != 1.
    let four = BigInt::from(4);
    let two = BigInt::from(2);
    let a = &four * a0 * &a00;
    let b = &four * a0 * &a2 + a1 * a1;
    let cc = &four * a0 * &a4 + &two * a1 * a3;
    let d = &four * a0 * &a6 + a3 * a3;

    let term1 = BigInt::from(18) * &a * &b * &cc * &d;
    let term2 = BigInt::from(4) * &b * &b * &b * &d;
    let term3 = &b * &b * &cc * &cc;
    let term4 = BigInt::from(4) * &a * &cc * &cc * &cc;
    let term5 = BigInt::from(27) * &a * &a * &d * &d;
    Ok(term1 - term2 + term3 - term4 - term5)
}

/// Score a signed generalized-Weierstrass coefficient vector exactly.
pub fn score_weierstrass_lift(c: &[BigInt]) -> Result<LiftScore, String> {
    let discriminant = signed_weierstrass_discriminant(c)?;
    let squared_l2: BigInt = c.iter().map(|x| x * x).sum();
    Ok(LiftScore {
        nonsingular: !discriminant.is_zero(),
        discriminant_bits: abs_bits(&discriminant),
        coefficient_height_bits: c.iter().map(abs_bits).max().unwrap_or(0),
        squared_l2_norm: squared_l2.to_string(),
        discriminant: discriminant.to_string(),
    })
}

fn better(a: &LiftScore, b: &LiftScore) -> bool {
    match (a.nonsingular, b.nonsingular) {
        (true, false) => return true,
        (false, true) => return false,
        _ => {}
    }
    (
        a.discriminant_bits,
        a.coefficient_height_bits,
        a.squared_l2_norm.len(),
        &a.squared_l2_norm,
    ) < (
        b.discriminant_bits,
        b.coefficient_height_bits,
        b.squared_l2_norm.len(),
        &b.squared_l2_norm,
    )
}

fn validate(problem: &AffineLiftProblem) -> Result<(), String> {
    let n = problem.particular.len();
    if n != WEIERSTRASS_COEFFICIENTS {
        return Err(format!(
            "this optimizer currently requires {WEIERSTRASS_COEFFICIENTS} signed Weierstrass coefficients"
        ));
    }
    if problem.directions.is_empty() {
        return Err("at least one affine-lattice direction is required".into());
    }
    if problem
        .directions
        .iter()
        .any(|v| v.len() != n || v.iter().all(BigInt::is_zero))
    {
        return Err("directions must be nonzero vectors of coefficient dimension".into());
    }
    if problem.exact_constraints.iter().any(|row| row.len() != n) {
        return Err("constraint rows must match the coefficient dimension".into());
    }
    for row in &problem.exact_constraints {
        for direction in &problem.directions {
            if !dot(row, direction).is_zero() {
                return Err("a supplied direction changes an exact constraint".into());
            }
        }
    }
    if let Some(q) = &problem.congruence_modulus {
        if q <= &BigInt::zero() {
            return Err("congruence modulus must be positive".into());
        }
        for direction in &problem.directions {
            if direction.iter().any(|x| (x % q) != BigInt::zero()) {
                return Err("a supplied direction changes the coefficient residue class".into());
            }
        }
    }
    Ok(())
}

fn approximate_vector(v: &[BigInt], shift: usize) -> Result<Vec<f64>, String> {
    v.iter()
        .map(|x| {
            let scaled = if shift == 0 { x.clone() } else { x >> shift };
            scaled
                .to_f64()
                .ok_or_else(|| "coefficient does not fit the scaled floating-point CVP view".into())
        })
        .collect()
}

fn babai_coefficients(basis: &[Vec<BigInt>], target: &[BigInt]) -> Result<Vec<i64>, String> {
    let max_bits = basis
        .iter()
        .flatten()
        .chain(target)
        .map(abs_bits)
        .max()
        .unwrap_or(0);
    let shift = max_bits.saturating_sub(500) as usize;
    let b: Vec<Vec<f64>> = basis
        .iter()
        .map(|v| approximate_vector(v, shift))
        .collect::<Result<_, _>>()?;
    let mut residual = approximate_vector(target, shift)?;
    let rank = b.len();
    let dim = target.len();
    let mut star = vec![vec![0.0; dim]; rank];
    let mut norms = vec![0.0; rank];
    for i in 0..rank {
        star[i].clone_from(&b[i]);
        for j in 0..i {
            if norms[j] == 0.0 {
                return Err("linearly dependent lattice directions".into());
            }
            let mu = b[i].iter().zip(&star[j]).map(|(x, y)| x * y).sum::<f64>() / norms[j];
            for k in 0..dim {
                star[i][k] -= mu * star[j][k];
            }
        }
        norms[i] = star[i].iter().map(|x| x * x).sum();
        if !norms[i].is_finite() || norms[i] <= f64::EPSILON {
            return Err("unstable or dependent lattice directions in Babai reduction".into());
        }
    }

    let mut coefficients = vec![0i64; rank];
    for i in (0..rank).rev() {
        let projection = residual
            .iter()
            .zip(&star[i])
            .map(|(x, y)| x * y)
            .sum::<f64>()
            / norms[i];
        let rounded = projection.round();
        if !rounded.is_finite() || rounded < i64::MIN as f64 || rounded > i64::MAX as f64 {
            return Err(
                "Babai coefficient exceeds the supported deterministic search range".into(),
            );
        }
        let coefficient = rounded as i64;
        coefficients[i] = coefficient;
        for k in 0..dim {
            residual[k] -= rounded * b[i][k];
        }
    }
    Ok(coefficients)
}

fn affine_candidate(
    particular: &[BigInt],
    basis: &[Vec<BigInt>],
    coefficients: &[i64],
) -> Vec<BigInt> {
    let mut out = particular.to_vec();
    for (basis_vector, coefficient) in basis.iter().zip(coefficients) {
        let coefficient = BigInt::from(*coefficient);
        for (x, delta) in out.iter_mut().zip(basis_vector) {
            *x += &coefficient * delta;
        }
    }
    out
}

fn certify(problem: &AffineLiftProblem, candidate: &[BigInt]) -> (bool, bool) {
    let exact = problem
        .exact_constraints
        .iter()
        .all(|row| dot(row, candidate) == dot(row, &problem.particular));
    let congruent = problem.congruence_modulus.as_ref().is_none_or(|q| {
        candidate
            .iter()
            .zip(&problem.particular)
            .all(|(a, b)| ((a - b) % q).is_zero())
    });
    (exact, congruent)
}

struct SearchState {
    best: Vec<BigInt>,
    score: LiftScore,
    evaluated: usize,
    limit: usize,
}

fn enumerate_neighborhood(
    depth: usize,
    radius: i64,
    center: &[i64],
    coefficients: &mut [i64],
    particular: &[BigInt],
    basis: &[Vec<BigInt>],
    state: &mut SearchState,
) -> Result<(), String> {
    if state.evaluated >= state.limit {
        return Ok(());
    }
    if depth == coefficients.len() {
        let candidate = affine_candidate(particular, basis, coefficients);
        let score = score_weierstrass_lift(&candidate)?;
        state.evaluated += 1;
        if better(&score, &state.score) {
            state.best = candidate;
            state.score = score;
        }
        return Ok(());
    }
    for delta in -radius..=radius {
        coefficients[depth] = center[depth]
            .checked_add(delta)
            .ok_or("neighborhood coefficient overflow")?;
        enumerate_neighborhood(
            depth + 1,
            radius,
            center,
            coefficients,
            particular,
            basis,
            state,
        )?;
        if state.evaluated >= state.limit {
            break;
        }
    }
    Ok(())
}

/// Optimize one certified xedni coefficient coset.
pub fn optimize_weierstrass_lift(
    problem: &AffineLiftProblem,
    options: LiftSearchOptions,
) -> Result<LiftOptimization, String> {
    validate(problem)?;
    if options.neighborhood_radius < 0 || options.max_candidates == 0 {
        return Err("search radius must be nonnegative and candidate cap positive".into());
    }

    let baseline_score = score_weierstrass_lift(&problem.particular)?;
    let mut basis = problem.directions.clone();
    lll_reduce_hp(&mut basis, 0.99).map_err(str::to_string)?;
    let target: Vec<BigInt> = problem.particular.iter().map(|x| -x).collect();
    let center = babai_coefficients(&basis, &target)?;
    let babai = affine_candidate(&problem.particular, &basis, &center);
    let babai_score = score_weierstrass_lift(&babai)?;

    // Starting from the feasible input makes the result monotonically no
    // worse even when the bounded neighborhood misses the global optimum.
    let mut state = SearchState {
        best: problem.particular.clone(),
        score: baseline_score.clone(),
        evaluated: 0,
        limit: options.max_candidates,
    };
    let mut coefficients = center.clone();
    enumerate_neighborhood(
        0,
        options.neighborhood_radius,
        &center,
        &mut coefficients,
        &problem.particular,
        &basis,
        &mut state,
    )?;
    let (exact_constraints_preserved, congruence_preserved) = certify(problem, &state.best);
    if !exact_constraints_preserved || !congruence_preserved {
        return Err("internal error: optimized lift left its certified affine coset".into());
    }

    Ok(LiftOptimization {
        method: "LLL-HP + Babai CVP + exact discriminant neighborhood",
        baseline_coefficients: problem.particular.iter().map(ToString::to_string).collect(),
        babai_coefficients: babai.iter().map(ToString::to_string).collect(),
        optimized_coefficients: state.best.iter().map(ToString::to_string).collect(),
        baseline_score,
        babai_score,
        optimized_score: state.score,
        candidates_evaluated: state.evaluated,
        exact_constraints_preserved,
        congruence_preserved,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn bi(values: &[i64]) -> Vec<BigInt> {
        values.iter().copied().map(BigInt::from).collect()
    }

    #[test]
    fn standard_discriminant_matches_sixteen_times_delta() {
        // y^2 = x^3 - x has elliptic discriminant 64; the completed-square
        // cubic 4x^3-4x has polynomial discriminant 1024.
        let coefficients = bi(&[1, 0, 0, -1, 0, 1, 0]);
        let score = score_weierstrass_lift(&coefficients).unwrap();
        assert_eq!(score.discriminant, "1024");
        assert!(score.nonsingular);
    }

    #[test]
    fn optimizer_preserves_points_and_modulus_while_recovering_short_lift() {
        // Four rational points on y^2+y=x^3-x.  Rows use the paper's signed
        // coefficient convention `(a0,a1,a3,-a00,-a2,-a4,-a6)`.
        let constraints = vec![
            bi(&[0, 0, 0, 0, 0, 0, 1]),
            bi(&[0, 0, 0, 1, 1, 1, 1]),
            bi(&[1, 1, -1, -1, 1, -1, 1]),
            bi(&[9, -6, -3, 8, 4, 2, 1]),
        ];
        let q = 67i64;
        let kernel = [
            bi(&[3, 2, 5, 0, 0, 0, 0]),
            bi(&[-8, -22, 0, -15, 15, 0, 0]),
            bi(&[2, -2, 0, -5, 0, 5, 0]),
        ];
        let directions: Vec<Vec<BigInt>> = kernel
            .iter()
            .map(|v| v.iter().map(|x| x * q).collect())
            .collect();
        let short = bi(&[1, 0, 1, -1, 0, 1, 0]);
        let mut particular = short.clone();
        for (v, multiplier) in directions.iter().zip([19i64, -13, 11]) {
            for (x, delta) in particular.iter_mut().zip(v) {
                *x += delta * multiplier;
            }
        }
        let problem = AffineLiftProblem {
            particular,
            directions,
            exact_constraints: constraints,
            congruence_modulus: Some(BigInt::from(q)),
        };
        let result = optimize_weierstrass_lift(
            &problem,
            LiftSearchOptions {
                neighborhood_radius: 1,
                max_candidates: 100,
            },
        )
        .unwrap();
        assert!(result.exact_constraints_preserved);
        assert!(result.congruence_preserved);
        assert!(result.optimized_score.nonsingular);
        assert!(result.optimized_score.discriminant_bits < result.baseline_score.discriminant_bits);
        assert_eq!(
            result.optimized_coefficients,
            short.iter().map(ToString::to_string).collect::<Vec<_>>()
        );
    }

    #[test]
    fn invalid_direction_is_rejected_before_search() {
        let problem = AffineLiftProblem {
            particular: bi(&[1, 0, 0, -1, 0, 1, 0]),
            directions: vec![bi(&[1, 0, 0, 0, 0, 0, 0])],
            exact_constraints: vec![bi(&[1, 0, 0, 0, 0, 0, 0])],
            congruence_modulus: Some(BigInt::from(67)),
        };
        let error = optimize_weierstrass_lift(&problem, LiftSearchOptions::default()).unwrap_err();
        assert!(error.contains("exact constraint"));
    }

    #[test]
    fn noncongruent_kernel_direction_is_rejected_before_search() {
        let problem = AffineLiftProblem {
            particular: bi(&[1, 0, 1, -1, 0, 1, 0]),
            // This is a genuine kernel direction for the four-point toy
            // incidence matrix, but it is not coefficientwise zero mod 67.
            directions: vec![bi(&[3, 2, 5, 0, 0, 0, 0])],
            exact_constraints: vec![
                bi(&[0, 0, 0, 0, 0, 0, 1]),
                bi(&[0, 0, 0, 1, 1, 1, 1]),
                bi(&[1, 1, -1, -1, 1, -1, 1]),
                bi(&[9, -6, -3, 8, 4, 2, 1]),
            ],
            congruence_modulus: Some(BigInt::from(67)),
        };
        let error = optimize_weierstrass_lift(&problem, LiftSearchOptions::default()).unwrap_err();
        assert!(error.contains("residue class"));
    }
}
