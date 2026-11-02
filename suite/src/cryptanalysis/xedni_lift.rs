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
//!   discriminant, with coefficient height as a tie-breaker.  For a full
//!   plane cubic this is computed directly from the cubic and its Hessian,
//!   avoiding a potentially unavailable rational-flex conversion;
//! * exact linear constraints and coefficient congruences are checked before
//!   the search and again on the result.
//!
//! This is a lift optimizer, not a discrete-log attack.  It can improve a
//! constant in the classic prime-field construction, but it does not evade the
//! conditional asymptotic obstruction proved by Jacobson--Koblitz--Silverman--
//! Stein--Teske.  Nor does it provide the degree-`m` number-field construction
//! needed over `F_{2^m}`.

use num_bigint::BigInt;
use num_integer::Integer;
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use serde::{Deserialize, Serialize};

use crate::cryptanalysis::lattice::lll_reduce_hp;

/// The signed coefficient order used by the xedni paper's `B` matrix:
/// `(a0, a1, a3, -a00, -a2, -a4, -a6)`.
pub const WEIERSTRASS_COEFFICIENTS: usize = 7;

/// Coefficient count for a homogeneous plane cubic in the JKSST order
/// `(X^3, X^2Y, XY^2, Y^3, X^2Z, XYZ, Y^2Z, XZ^2, YZ^2, Z^3)`.
pub const PLANE_CUBIC_COEFFICIENTS: usize = 10;

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
    /// Optional projective points `(X,Y,Z)` for the ten-coefficient model.
    /// These are converted to exact JKSST incidence rows.  Supply this or
    /// `exact_constraints`, not both.
    #[serde(default)]
    pub projective_points: Vec<[String; 3]>,
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
        if !value.exact_constraints.is_empty() && !value.projective_points.is_empty() {
            return Err("supply exact_constraints or projective_points, not both".into());
        }
        let exact_constraints = if value.projective_points.is_empty() {
            value
                .exact_constraints
                .iter()
                .map(|row| {
                    row.iter()
                        .map(|x| parse_decimal(x, "exact_constraints"))
                        .collect()
                })
                .collect::<Result<_, _>>()?
        } else {
            value
                .projective_points
                .iter()
                .map(|point| {
                    let x = parse_decimal(&point[0], "projective_points")?;
                    let y = parse_decimal(&point[1], "projective_points")?;
                    let z = parse_decimal(&point[2], "projective_points")?;
                    if x.is_zero() && y.is_zero() && z.is_zero() {
                        return Err("projective point (0,0,0) is invalid".into());
                    }
                    Ok(plane_cubic_incidence_row(&x, &y, &z))
                })
                .collect::<Result<_, String>>()?
        };
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

/// Exact objective for a general ten-coefficient cubic.
///
/// The determinant is the direct ternary-cubic discriminant construction in
/// Fisher, *The invariants of a genus one curve*, Section 7.2: form the cubic
/// Hessian, put the coefficients of the three partial derivatives of each in
/// a 6-by-6 matrix, and take its determinant.  It is `+/- 1728 Delta`, hence
/// vanishes exactly on singular plane cubics over characteristic zero.
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct PlaneCubicLiftScore {
    pub nonsingular: bool,
    pub discriminant_bits: u64,
    pub coefficient_height_bits: u64,
    pub squared_l2_norm: String,
    pub discriminant: String,
}

/// Certified output for the general-cubic Step-7 optimizer.
#[derive(Clone, Debug, Serialize)]
pub struct PlaneCubicLiftOptimization {
    pub method: &'static str,
    pub coefficient_order: &'static str,
    pub baseline_coefficients: Vec<String>,
    pub babai_coefficients: Vec<String>,
    pub optimized_coefficients: Vec<String>,
    pub baseline_score: PlaneCubicLiftScore,
    pub babai_score: PlaneCubicLiftScore,
    pub optimized_score: PlaneCubicLiftScore,
    pub candidates_evaluated: usize,
    pub exact_constraints_preserved: bool,
    pub congruence_preserved: bool,
    pub discriminant_evaluated: bool,
}

/// Build one row of the full ten-coefficient plane-cubic incidence matrix.
pub fn plane_cubic_incidence_row(x: &BigInt, y: &BigInt, z: &BigInt) -> Vec<BigInt> {
    let x2 = x * x;
    let y2 = y * y;
    let z2 = z * z;
    vec![
        &x2 * x,
        &x2 * y,
        x * &y2,
        &y2 * y,
        &x2 * z,
        x * y * z,
        &y2 * z,
        x * &z2,
        y * &z2,
        &z2 * z,
    ]
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

fn validate(problem: &AffineLiftProblem, expected_dimension: usize) -> Result<(), String> {
    let n = problem.particular.len();
    if n != expected_dimension {
        return Err(format!(
            "this optimizer requires {expected_dimension} coefficients, got {n}"
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

fn round_rational(value: &BigRational) -> BigInt {
    let (floor, remainder) = value.numer().div_mod_floor(value.denom());
    let twice_remainder = remainder << 1;
    if twice_remainder < *value.denom() {
        floor
    } else if twice_remainder > *value.denom() || value.is_positive() {
        floor + 1
    } else {
        // Exact negative half: match integer rounding away from zero.
        floor
    }
}

fn babai_coefficients(basis: &[Vec<BigInt>], target: &[BigInt]) -> Result<Vec<BigInt>, String> {
    let b: Vec<Vec<BigRational>> = basis
        .iter()
        .map(|row| row.iter().cloned().map(BigRational::from_integer).collect())
        .collect();
    let mut residual: Vec<BigRational> = target
        .iter()
        .cloned()
        .map(BigRational::from_integer)
        .collect();
    let rank = b.len();
    let dim = target.len();
    let mut star = vec![vec![BigRational::zero(); dim]; rank];
    let mut norms = vec![BigRational::zero(); rank];
    for i in 0..rank {
        star[i].clone_from(&b[i]);
        for j in 0..i {
            if norms[j].is_zero() {
                return Err("linearly dependent lattice directions".into());
            }
            let mu: BigRational = b[i]
                .iter()
                .zip(&star[j])
                .map(|(x, y)| x * y)
                .sum::<BigRational>()
                / &norms[j];
            for k in 0..dim {
                let correction = &mu * &star[j][k];
                star[i][k] -= correction;
            }
        }
        norms[i] = star[i].iter().map(|x| x * x).sum();
        if norms[i].is_zero() {
            return Err("linearly dependent lattice directions".into());
        }
    }

    let mut coefficients = vec![BigInt::zero(); rank];
    for i in (0..rank).rev() {
        let projection: BigRational = residual
            .iter()
            .zip(&star[i])
            .map(|(x, y)| x * y)
            .sum::<BigRational>()
            / &norms[i];
        let coefficient = round_rational(&projection);
        coefficients[i] = coefficient.clone();
        for k in 0..dim {
            residual[k] -= BigRational::from_integer(coefficient.clone()) * &b[i][k];
        }
    }
    Ok(coefficients)
}

fn affine_candidate(
    particular: &[BigInt],
    basis: &[Vec<BigInt>],
    coefficients: &[BigInt],
) -> Vec<BigInt> {
    let mut out = particular.to_vec();
    for (basis_vector, coefficient) in basis.iter().zip(coefficients) {
        for (x, delta) in out.iter_mut().zip(basis_vector) {
            *x += coefficient * delta;
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

struct SearchState<S> {
    best: Vec<BigInt>,
    score: S,
    evaluated: usize,
    limit: usize,
}

fn enumerate_neighborhood<S, Score, Better>(
    depth: usize,
    radius: i64,
    center: &[BigInt],
    coefficients: &mut [BigInt],
    particular: &[BigInt],
    basis: &[Vec<BigInt>],
    state: &mut SearchState<S>,
    score_candidate: &Score,
    better_score: &Better,
) -> Result<(), String>
where
    Score: Fn(&[BigInt]) -> Result<S, String>,
    Better: Fn(&S, &S) -> bool,
{
    if state.evaluated >= state.limit {
        return Ok(());
    }
    if depth == coefficients.len() {
        let candidate = affine_candidate(particular, basis, coefficients);
        let score = score_candidate(&candidate)?;
        state.evaluated += 1;
        if better_score(&score, &state.score) {
            state.best = candidate;
            state.score = score;
        }
        return Ok(());
    }
    for delta in -radius..=radius {
        coefficients[depth] = &center[depth] + delta;
        enumerate_neighborhood(
            depth + 1,
            radius,
            center,
            coefficients,
            particular,
            basis,
            state,
            score_candidate,
            better_score,
        )?;
        if state.evaluated >= state.limit {
            break;
        }
    }
    Ok(())
}

struct CoreOptimization<S> {
    baseline: Vec<BigInt>,
    babai: Vec<BigInt>,
    optimized: Vec<BigInt>,
    baseline_score: S,
    babai_score: S,
    optimized_score: S,
    candidates_evaluated: usize,
    exact_constraints_preserved: bool,
    congruence_preserved: bool,
}

fn optimize_affine_lift<S, Score, Better>(
    problem: &AffineLiftProblem,
    options: LiftSearchOptions,
    expected_dimension: usize,
    score_candidate: Score,
    better_score: Better,
) -> Result<CoreOptimization<S>, String>
where
    S: Clone,
    Score: Fn(&[BigInt]) -> Result<S, String>,
    Better: Fn(&S, &S) -> bool,
{
    validate(problem, expected_dimension)?;
    if options.neighborhood_radius < 0 || options.max_candidates == 0 {
        return Err("search radius must be nonnegative and candidate cap positive".into());
    }

    let baseline_score = score_candidate(&problem.particular)?;
    let mut basis = problem.directions.clone();
    lll_reduce_hp(&mut basis, 0.99).map_err(str::to_string)?;
    let target: Vec<BigInt> = problem.particular.iter().map(|x| -x).collect();
    let center = babai_coefficients(&basis, &target)?;
    let babai = affine_candidate(&problem.particular, &basis, &center);
    let babai_score = score_candidate(&babai)?;

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
        &score_candidate,
        &better_score,
    )?;
    let (exact_constraints_preserved, congruence_preserved) = certify(problem, &state.best);
    if !exact_constraints_preserved || !congruence_preserved {
        return Err("internal error: optimized lift left its certified affine coset".into());
    }

    Ok(CoreOptimization {
        baseline: problem.particular.clone(),
        babai,
        optimized: state.best,
        baseline_score,
        babai_score,
        optimized_score: state.score,
        candidates_evaluated: state.evaluated,
        exact_constraints_preserved,
        congruence_preserved,
    })
}

/// Optimize one certified seven-coefficient Weierstrass xedni coset.
pub fn optimize_weierstrass_lift(
    problem: &AffineLiftProblem,
    options: LiftSearchOptions,
) -> Result<LiftOptimization, String> {
    let result = optimize_affine_lift(
        problem,
        options,
        WEIERSTRASS_COEFFICIENTS,
        score_weierstrass_lift,
        better,
    )?;
    Ok(LiftOptimization {
        method: "LLL-HP + exact-rational Babai CVP + exact discriminant neighborhood",
        baseline_coefficients: result.baseline.iter().map(ToString::to_string).collect(),
        babai_coefficients: result.babai.iter().map(ToString::to_string).collect(),
        optimized_coefficients: result.optimized.iter().map(ToString::to_string).collect(),
        baseline_score: result.baseline_score,
        babai_score: result.babai_score,
        optimized_score: result.optimized_score,
        candidates_evaluated: result.candidates_evaluated,
        exact_constraints_preserved: result.exact_constraints_preserved,
        congruence_preserved: result.congruence_preserved,
    })
}

// Quadratic coefficient order used only by the direct discriminant:
// (X^2, Y^2, Z^2, XY, XZ, YZ).
fn multiply_linear_forms(a: &[BigInt], b: &[BigInt]) -> Vec<BigInt> {
    vec![
        &a[0] * &b[0],
        &a[1] * &b[1],
        &a[2] * &b[2],
        &a[0] * &b[1] + &a[1] * &b[0],
        &a[0] * &b[2] + &a[2] * &b[0],
        &a[1] * &b[2] + &a[2] * &b[1],
    ]
}

fn multiply_quadratic_linear(q: &[BigInt], linear: &[BigInt]) -> Vec<BigInt> {
    vec![
        &q[0] * &linear[0],
        &q[0] * &linear[1] + &q[3] * &linear[0],
        &q[1] * &linear[0] + &q[3] * &linear[1],
        &q[1] * &linear[1],
        &q[0] * &linear[2] + &q[4] * &linear[0],
        &q[3] * &linear[2] + &q[4] * &linear[1] + &q[5] * &linear[0],
        &q[1] * &linear[2] + &q[5] * &linear[1],
        &q[2] * &linear[0] + &q[4] * &linear[2],
        &q[2] * &linear[1] + &q[5] * &linear[2],
        &q[2] * &linear[2],
    ]
}

fn add_scaled_cubic(target: &mut [BigInt], source: &[BigInt], scale: i64) {
    let scale = BigInt::from(scale);
    for (coefficient, term) in target.iter_mut().zip(source) {
        *coefficient += &scale * term;
    }
}

/// Return Fisher's integral cubic Hessian `-det(second derivatives) / 2`.
fn plane_cubic_hessian(c: &[BigInt]) -> Result<Vec<BigInt>, String> {
    let linear = |x: i64, i: usize, y: i64, j: usize, z: i64, k: usize| {
        vec![x * &c[i], y * &c[j], z * &c[k]]
    };
    let f_xx = linear(6, 0, 2, 1, 2, 4);
    let f_xy = linear(2, 1, 2, 2, 1, 5);
    let f_xz = linear(2, 4, 1, 5, 2, 7);
    let f_yy = linear(2, 2, 6, 3, 2, 6);
    let f_yz = linear(1, 5, 2, 6, 2, 8);
    let f_zz = linear(2, 7, 2, 8, 6, 9);

    // det [[a,b,c],[b,d,e],[c,e,f]]
    //   = adf + 2bce - ae^2 - dc^2 - fb^2.
    let mut determinant = vec![BigInt::zero(); PLANE_CUBIC_COEFFICIENTS];
    add_scaled_cubic(
        &mut determinant,
        &multiply_quadratic_linear(&multiply_linear_forms(&f_xx, &f_yy), &f_zz),
        1,
    );
    add_scaled_cubic(
        &mut determinant,
        &multiply_quadratic_linear(&multiply_linear_forms(&f_xy, &f_xz), &f_yz),
        2,
    );
    add_scaled_cubic(
        &mut determinant,
        &multiply_quadratic_linear(&multiply_linear_forms(&f_yz, &f_yz), &f_xx),
        -1,
    );
    add_scaled_cubic(
        &mut determinant,
        &multiply_quadratic_linear(&multiply_linear_forms(&f_xz, &f_xz), &f_yy),
        -1,
    );
    add_scaled_cubic(
        &mut determinant,
        &multiply_quadratic_linear(&multiply_linear_forms(&f_xy, &f_xy), &f_zz),
        -1,
    );
    let two = BigInt::from(2);
    if determinant
        .iter()
        .any(|coefficient| !coefficient.is_multiple_of(&two))
    {
        return Err("internal error: nonintegral ternary-cubic Hessian".into());
    }
    Ok(determinant
        .into_iter()
        .map(|coefficient| -coefficient / &two)
        .collect())
}

fn plane_cubic_partials(c: &[BigInt]) -> [Vec<BigInt>; 3] {
    let two = BigInt::from(2);
    let three = BigInt::from(3);
    [
        vec![
            &three * &c[0],
            c[2].clone(),
            c[7].clone(),
            &two * &c[1],
            &two * &c[4],
            c[5].clone(),
        ],
        vec![
            c[1].clone(),
            &three * &c[3],
            c[8].clone(),
            &two * &c[2],
            c[5].clone(),
            &two * &c[6],
        ],
        vec![
            c[4].clone(),
            c[6].clone(),
            &three * &c[9],
            c[5].clone(),
            &two * &c[7],
            &two * &c[8],
        ],
    ]
}

/// Fraction-free determinant with exact divisions (Bareiss elimination).
fn determinant_bareiss(mut matrix: Vec<Vec<BigInt>>) -> Result<BigInt, String> {
    let n = matrix.len();
    if n == 0 || matrix.iter().any(|row| row.len() != n) {
        return Err("determinant requires a nonempty square matrix".into());
    }
    if n == 1 {
        return Ok(matrix[0][0].clone());
    }
    let mut sign = BigInt::from(1);
    let mut previous_pivot = BigInt::from(1);
    for pivot_column in 0..n - 1 {
        let Some(pivot_row) = (pivot_column..n).find(|&row| !matrix[row][pivot_column].is_zero())
        else {
            return Ok(BigInt::zero());
        };
        if pivot_row != pivot_column {
            matrix.swap(pivot_row, pivot_column);
            sign = -sign;
        }
        let pivot = matrix[pivot_column][pivot_column].clone();
        for row in pivot_column + 1..n {
            for column in pivot_column + 1..n {
                let numerator = &matrix[row][column] * &pivot
                    - &matrix[row][pivot_column] * &matrix[pivot_column][column];
                let (quotient, remainder) = numerator.div_rem(&previous_pivot);
                if !remainder.is_zero() {
                    return Err("internal error: inexact Bareiss division".into());
                }
                matrix[row][column] = quotient;
            }
            matrix[row][pivot_column] = BigInt::zero();
        }
        previous_pivot = pivot;
    }
    Ok(sign * &matrix[n - 1][n - 1])
}

/// Compute `+/- 1728 Delta` for an integral ternary cubic exactly.
pub fn plane_cubic_discriminant(c: &[BigInt]) -> Result<BigInt, String> {
    if c.len() != PLANE_CUBIC_COEFFICIENTS {
        return Err(format!(
            "expected {PLANE_CUBIC_COEFFICIENTS} plane-cubic coefficients, got {}",
            c.len()
        ));
    }
    let hessian = plane_cubic_hessian(c)?;
    let mut matrix = plane_cubic_partials(c).to_vec();
    matrix.extend(plane_cubic_partials(&hessian));
    determinant_bareiss(matrix)
}

fn score_plane_cubic_lift(c: &[BigInt]) -> Result<PlaneCubicLiftScore, String> {
    if c.len() != PLANE_CUBIC_COEFFICIENTS {
        return Err(format!(
            "expected {PLANE_CUBIC_COEFFICIENTS} plane-cubic coefficients, got {}",
            c.len()
        ));
    }
    let discriminant = plane_cubic_discriminant(c)?;
    let squared_l2: BigInt = c.iter().map(|x| x * x).sum();
    Ok(PlaneCubicLiftScore {
        nonsingular: !discriminant.is_zero(),
        discriminant_bits: abs_bits(&discriminant),
        coefficient_height_bits: c.iter().map(abs_bits).max().unwrap_or(0),
        squared_l2_norm: squared_l2.to_string(),
        discriminant: discriminant.to_string(),
    })
}

fn better_plane_cubic(a: &PlaneCubicLiftScore, b: &PlaneCubicLiftScore) -> bool {
    match (a.nonsingular, b.nonsingular) {
        (true, false) => return true,
        (false, true) => return false,
        _ => {}
    }
    let a_norm = a
        .squared_l2_norm
        .parse::<BigInt>()
        .expect("internally generated integer score");
    let b_norm = b
        .squared_l2_norm
        .parse::<BigInt>()
        .expect("internally generated integer score");
    (a.discriminant_bits, a.coefficient_height_bits, a_norm)
        < (b.discriminant_bits, b.coefficient_height_bits, b_norm)
}

/// Optimize the exact linear Step-7 coset for a full plane cubic.
///
/// This supports all `2 <= r <= 9` incidence rows from JKSST.  It does not
/// perform the Step-8 coordinate conversion: the Step-9 discriminant is
/// evaluated directly on the ternary cubic by the Hessian construction.
pub fn optimize_plane_cubic_lift(
    problem: &AffineLiftProblem,
    options: LiftSearchOptions,
) -> Result<PlaneCubicLiftOptimization, String> {
    if !(2..=9).contains(&problem.exact_constraints.len()) {
        return Err("JKSST plane-cubic mode requires 2 through 9 point-incidence rows".into());
    }
    let result = optimize_affine_lift(
        problem,
        options,
        PLANE_CUBIC_COEFFICIENTS,
        score_plane_cubic_lift,
        better_plane_cubic,
    )?;
    Ok(PlaneCubicLiftOptimization {
        method: "LLL-HP + exact-rational Babai CVP + exact ternary-discriminant neighborhood",
        coefficient_order: "X^3,X^2Y,XY^2,Y^3,X^2Z,XYZ,Y^2Z,XZ^2,YZ^2,Z^3",
        baseline_coefficients: result.baseline.iter().map(ToString::to_string).collect(),
        babai_coefficients: result.babai.iter().map(ToString::to_string).collect(),
        optimized_coefficients: result.optimized.iter().map(ToString::to_string).collect(),
        baseline_score: result.baseline_score,
        babai_score: result.babai_score,
        optimized_score: result.optimized_score,
        candidates_evaluated: result.candidates_evaluated,
        exact_constraints_preserved: result.exact_constraints_preserved,
        congruence_preserved: result.congruence_preserved,
        discriminant_evaluated: true,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn bi(values: &[i64]) -> Vec<BigInt> {
        values.iter().copied().map(BigInt::from).collect()
    }

    fn big(value: &str) -> BigInt {
        value.parse().expect("decimal test integer")
    }

    fn rational_rank(rows: &[Vec<BigInt>]) -> usize {
        let mut matrix: Vec<Vec<BigRational>> = rows
            .iter()
            .map(|row| row.iter().cloned().map(BigRational::from_integer).collect())
            .collect();
        let mut rank = 0;
        for column in 0..matrix.first().map_or(0, Vec::len) {
            let Some(pivot) = (rank..matrix.len()).find(|&row| !matrix[row][column].is_zero())
            else {
                continue;
            };
            matrix.swap(rank, pivot);
            let pivot_value = matrix[rank][column].clone();
            for entry in &mut matrix[rank][column..] {
                *entry /= &pivot_value;
            }
            let pivot_row = matrix[rank].clone();
            for (row_index, row) in matrix.iter_mut().enumerate() {
                if row_index == rank || row[column].is_zero() {
                    continue;
                }
                let factor = row[column].clone();
                for (entry, pivot_entry) in row[column..].iter_mut().zip(&pivot_row[column..]) {
                    *entry -= &factor * pivot_entry;
                }
            }
            rank += 1;
            if rank == matrix.len() {
                break;
            }
        }
        rank
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
    fn direct_plane_cubic_discriminant_matches_reference_models() {
        // Fisher Section 7.2 gives det(partials(U), partials(H(U))) =
        // +/- 1728 Delta.  These values independently pin the normalization.
        let fermat = bi(&[1, 0, 0, 1, 0, 0, 0, 0, 0, 1]);
        assert_eq!(
            plane_cubic_discriminant(&fermat).unwrap(),
            34_012_224.into()
        );

        // x^3+y^3+z^3-3xyz is the singular Hesse member k^3=1.
        let singular_hesse = bi(&[1, 0, 0, 1, 0, -3, 0, 0, 0, 1]);
        assert!(plane_cubic_discriminant(&singular_hesse).unwrap().is_zero());

        // y^2 z = x^3 - x z^2 has elliptic Delta=64.
        let weierstrass = bi(&[-1, 0, 0, 0, 0, 0, 1, 1, 0, 0]);
        assert_eq!(
            plane_cubic_discriminant(&weierstrass).unwrap(),
            (-110_592).into()
        );
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
    fn exact_babai_supports_coefficients_beyond_i64() {
        let short = bi(&[1, 0, 1, -1, 0, 1, 0]);
        let direction = bi(&[67, 0, 0, 0, 0, 0, 0]);
        let multiplier = big("10000000000000000000000000000000000000000");
        let mut particular = short.clone();
        particular[0] += &direction[0] * multiplier;
        let problem = AffineLiftProblem {
            particular,
            directions: vec![direction],
            exact_constraints: Vec::new(),
            congruence_modulus: Some(BigInt::from(67)),
        };
        let result = optimize_weierstrass_lift(
            &problem,
            LiftSearchOptions {
                neighborhood_radius: 0,
                max_candidates: 1,
            },
        )
        .unwrap();
        assert_eq!(
            result.optimized_coefficients,
            short.iter().map(ToString::to_string).collect::<Vec<_>>()
        );
    }

    #[test]
    fn full_plane_cubic_path_supports_nine_independent_point_rows() {
        // Nine multiples of (0,1) on y^2 = x^3 - x + 1, represented by
        // primitive-enough integral projective coordinates.  Their ten-term
        // incidence matrix has rank nine and its kernel is the curve vector.
        let points = [
            ("0", "1", "1"),
            ("2", "-7", "8"),
            ("56", "419", "1"),
            ("-6244", "24655", "21952"),
            ("5232472", "-8824453", "11089567"),
            ("8246188998", "30795303833", "588480472"),
            ("-51055373209680", "101098481076377", "85923747076383"),
            (
                "1796402375990961480",
                "-2098030206970736191",
                "2631958890650432000",
            ),
            (
                "160221897655974195623120",
                "396235626125845757178647",
                "25634128246348207648607",
            ),
        ];
        let constraints: Vec<Vec<BigInt>> = points
            .iter()
            .map(|(x, y, z)| plane_cubic_incidence_row(&big(x), &big(y), &big(z)))
            .collect();
        assert_eq!(rational_rank(&constraints), 9);
        let short = bi(&[1, 0, 0, 0, 0, 0, -1, -1, 0, 1]);
        assert!(constraints.iter().all(|row| dot(row, &short).is_zero()));

        let direction: Vec<BigInt> = short.iter().map(|x| x * 67).collect();
        let mut particular = short.clone();
        for (coefficient, delta) in particular.iter_mut().zip(&direction) {
            *coefficient += delta * 123;
        }
        let problem = AffineLiftProblem {
            particular,
            directions: vec![direction],
            exact_constraints: constraints,
            congruence_modulus: Some(BigInt::from(67)),
        };
        let result = optimize_plane_cubic_lift(
            &problem,
            LiftSearchOptions {
                neighborhood_radius: 0,
                max_candidates: 1,
            },
        )
        .unwrap();
        assert_eq!(
            result.optimized_coefficients,
            short.iter().map(ToString::to_string).collect::<Vec<_>>()
        );
        assert!(result.exact_constraints_preserved);
        assert!(result.congruence_preserved);
        assert!(result.discriminant_evaluated);
        assert!(result.optimized_score.nonsingular);
        // The planted model is y^2 = x^3 - x + 1, with Delta=-368.
        assert_eq!(result.optimized_score.discriminant, "635904");
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
