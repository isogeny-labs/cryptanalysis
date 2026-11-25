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
//!   the search and again on the result;
//! * for general plane cubics over `F_p` (`JksstPlaneCubicProblem`), Steps 3--6
//!   normalize four general-position points via `PGL_3(F_p)` to the standard
//!   projective frame, lift the remaining `r - 4` points in `Z^3` via 3D LLL,
//!   detect curve-independent collinear triples (`collinear_point_triples`),
//!   and optimize the homogeneous projective-congruence sublattice.
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

/// A primitive integral representative of a rational projective point.
///
/// Rational projective points admit an integral representative after clearing
/// denominators.  Dividing by the coordinate gcd and fixing the sign makes
/// equality structural and keeps intermediate group-law coordinates smaller.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PlaneCubicPoint {
    pub coordinates: [BigInt; 3],
}

impl PlaneCubicPoint {
    pub fn new(mut coordinates: [BigInt; 3]) -> Result<Self, String> {
        if coordinates.iter().all(BigInt::is_zero) {
            return Err("projective point (0,0,0) is invalid".into());
        }
        let gcd = coordinates.iter().fold(BigInt::zero(), |gcd, x| gcd.gcd(x));
        for coordinate in &mut coordinates {
            *coordinate /= &gcd;
        }
        if coordinates
            .iter()
            .find(|coordinate| !coordinate.is_zero())
            .is_some_and(Signed::is_negative)
        {
            for coordinate in &mut coordinates {
                *coordinate = -&*coordinate;
            }
        }
        Ok(Self { coordinates })
    }
}

fn plane_cubic_value(c: &[BigInt], point: &PlaneCubicPoint) -> BigInt {
    let [x, y, z] = &point.coordinates;
    dot(&plane_cubic_incidence_row(x, y, z), c)
}

fn plane_cubic_gradient(c: &[BigInt], point: &PlaneCubicPoint) -> [BigInt; 3] {
    let [x, y, z] = &point.coordinates;
    let two = BigInt::from(2);
    let three = BigInt::from(3);
    [
        &three * &c[0] * x * x
            + &two * &c[1] * x * y
            + &c[2] * y * y
            + &two * &c[4] * x * z
            + &c[5] * y * z
            + &c[7] * z * z,
        &c[1] * x * x
            + &two * &c[2] * x * y
            + &three * &c[3] * y * y
            + &c[5] * x * z
            + &two * &c[6] * y * z
            + &c[8] * z * z,
        &c[4] * x * x
            + &c[5] * x * y
            + &c[6] * y * y
            + &two * &c[7] * x * z
            + &two * &c[8] * y * z
            + &three * &c[9] * z * z,
    ]
}

fn multiply_binary_forms(a: &[BigInt], b: &[BigInt]) -> Vec<BigInt> {
    let mut product = vec![BigInt::zero(); a.len() + b.len() - 1];
    for (i, x) in a.iter().enumerate() {
        for (j, y) in b.iter().enumerate() {
            product[i + j] += x * y;
        }
    }
    product
}

/// Restrict `F` to `s P + t Q`; index `i` is the coefficient of `s^(3-i)t^i`.
fn binary_cubic_restriction(c: &[BigInt], p: &PlaneCubicPoint, q: &PlaneCubicPoint) -> [BigInt; 4] {
    const EXPONENTS: [(usize, usize, usize); PLANE_CUBIC_COEFFICIENTS] = [
        (3, 0, 0),
        (2, 1, 0),
        (1, 2, 0),
        (0, 3, 0),
        (2, 0, 1),
        (1, 1, 1),
        (0, 2, 1),
        (1, 0, 2),
        (0, 1, 2),
        (0, 0, 3),
    ];
    let mut result = std::array::from_fn(|_| BigInt::zero());
    for (coefficient, (ex, ey, ez)) in c.iter().zip(EXPONENTS) {
        let mut term = vec![BigInt::from(1)];
        for (coordinate, exponent) in [0usize, 1, 2].into_iter().zip([ex, ey, ez]) {
            for _ in 0..exponent {
                term = multiply_binary_forms(
                    &term,
                    &[
                        p.coordinates[coordinate].clone(),
                        q.coordinates[coordinate].clone(),
                    ],
                );
            }
        }
        for (value, monomial) in result.iter_mut().zip(term) {
            *value += coefficient * monomial;
        }
    }
    result
}

fn combine_projective(
    a: &BigInt,
    p: &PlaneCubicPoint,
    b: &BigInt,
    q: &PlaneCubicPoint,
) -> Result<PlaneCubicPoint, String> {
    PlaneCubicPoint::new(std::array::from_fn(|i| {
        a * &p.coordinates[i] + b * &q.coordinates[i]
    }))
}

fn projective_cross_nonzero(p: &PlaneCubicPoint, q: &PlaneCubicPoint) -> bool {
    let [px, py, pz] = &p.coordinates;
    let [qx, qy, qz] = &q.coordinates;
    !(py * qz - pz * qy).is_zero()
        || !(pz * qx - px * qz).is_zero()
        || !(px * qy - py * qx).is_zero()
}

/// Exact group arithmetic on a smooth plane cubic with any rational origin.
///
/// For points `P,Q`, let their line have residual intersection `R`, then let
/// the line `R,O` have residual intersection `S`.  Hyperplane divisors give
/// `P+Q+R ~ H ~ R+O+S`, hence `[S-O]=[P-O]+[Q-O]`.  Unlike the familiar
/// one-line reflection formula, this two-line construction does not require
/// the chosen origin to be a flex.
#[derive(Clone, Debug)]
pub struct PlaneCubicGroup {
    coefficients: Vec<BigInt>,
    origin: PlaneCubicPoint,
}

impl PlaneCubicGroup {
    pub fn new(coefficients: Vec<BigInt>, origin: PlaneCubicPoint) -> Result<Self, String> {
        if coefficients.len() != PLANE_CUBIC_COEFFICIENTS {
            return Err(format!(
                "expected {PLANE_CUBIC_COEFFICIENTS} plane-cubic coefficients, got {}",
                coefficients.len()
            ));
        }
        if plane_cubic_discriminant(&coefficients)?.is_zero() {
            return Err("plane cubic is singular".into());
        }
        if !plane_cubic_value(&coefficients, &origin).is_zero() {
            return Err("chosen origin is not on the plane cubic".into());
        }
        Ok(Self {
            coefficients,
            origin,
        })
    }

    /// Choose a rational origin without consuming one of the relation points.
    ///
    /// The origin is the residual intersection of the chord through `p` and
    /// `q`.  If the cubic reduces to a Weierstrass model whose flex is the
    /// finite-field identity and `p,q` reduce to `m_p G,m_q G`, respectively,
    /// this origin reduces to `-(m_p+m_q)G`.  Thus its source-group scalar is
    /// known even when the lifted cubic has no rational flex.
    pub fn with_chord_origin(
        coefficients: Vec<BigInt>,
        p: &PlaneCubicPoint,
        q: &PlaneCubicPoint,
    ) -> Result<Self, String> {
        if !projective_cross_nonzero(p, q) {
            return Err("chord-origin construction requires distinct points".into());
        }
        let provisional = Self::new(coefficients, p.clone())?;
        let origin = provisional.third_intersection(p, q)?;
        Self::new(provisional.coefficients, origin)
    }

    pub fn origin(&self) -> &PlaneCubicPoint {
        &self.origin
    }

    pub fn is_on_curve(&self, point: &PlaneCubicPoint) -> bool {
        plane_cubic_value(&self.coefficients, point).is_zero()
    }

    fn tangent_auxiliary(&self, point: &PlaneCubicPoint) -> Result<PlaneCubicPoint, String> {
        let gradient = plane_cubic_gradient(&self.coefficients, point);
        if gradient.iter().all(BigInt::is_zero) {
            return Err("plane cubic point is singular".into());
        }
        let zero = BigInt::zero();
        let candidates = [
            [gradient[1].clone(), -&gradient[0], zero.clone()],
            [gradient[2].clone(), zero.clone(), -&gradient[0]],
            [zero, gradient[2].clone(), -&gradient[1]],
        ];
        for candidate in candidates {
            if candidate.iter().all(BigInt::is_zero) {
                continue;
            }
            let candidate = PlaneCubicPoint::new(candidate)?;
            if projective_cross_nonzero(point, &candidate) {
                return Ok(candidate);
            }
        }
        Err("failed to parameterize the tangent line".into())
    }

    pub fn third_intersection(
        &self,
        p: &PlaneCubicPoint,
        q: &PlaneCubicPoint,
    ) -> Result<PlaneCubicPoint, String> {
        if !self.is_on_curve(p) || !self.is_on_curve(q) {
            return Err("third intersection requires two points on the cubic".into());
        }
        if p != q {
            let restriction = binary_cubic_restriction(&self.coefficients, p, q);
            if !restriction[0].is_zero() || !restriction[3].is_zero() {
                return Err("internal error: chord endpoints do not vanish".into());
            }
            return combine_projective(&restriction[2], p, &(-&restriction[1]), q);
        }

        let auxiliary = self.tangent_auxiliary(p)?;
        let restriction = binary_cubic_restriction(&self.coefficients, p, &auxiliary);
        if !restriction[0].is_zero() || !restriction[1].is_zero() {
            return Err("internal error: tangent does not have double contact".into());
        }
        combine_projective(&restriction[3], p, &(-&restriction[2]), &auxiliary)
    }

    pub fn add(&self, p: &PlaneCubicPoint, q: &PlaneCubicPoint) -> Result<PlaneCubicPoint, String> {
        let residual = self.third_intersection(p, q)?;
        self.third_intersection(&residual, &self.origin)
    }

    pub fn negate(&self, point: &PlaneCubicPoint) -> Result<PlaneCubicPoint, String> {
        let tangent_residual = self.third_intersection(&self.origin, &self.origin)?;
        self.third_intersection(point, &tangent_residual)
    }

    pub fn scalar_mul(
        &self,
        scalar: &BigInt,
        point: &PlaneCubicPoint,
    ) -> Result<PlaneCubicPoint, String> {
        let mut scalar = scalar.clone();
        let mut addend = point.clone();
        if scalar.is_negative() {
            scalar = -scalar;
            addend = self.negate(&addend)?;
        }
        let mut result = self.origin.clone();
        while !scalar.is_zero() {
            if scalar.is_odd() {
                result = self.add(&result, &addend)?;
            }
            scalar >>= 1;
            if !scalar.is_zero() {
                addend = self.add(&addend, &addend)?;
            }
        }
        Ok(result)
    }

    pub fn relation_sum(
        &self,
        scalars: &[BigInt],
        points: &[PlaneCubicPoint],
    ) -> Result<PlaneCubicPoint, String> {
        if scalars.len() != points.len() {
            return Err("relation scalars and points must have the same length".into());
        }
        let mut sum = self.origin.clone();
        for (scalar, point) in scalars.iter().zip(points) {
            sum = self.add(&sum, &self.scalar_mul(scalar, point)?)?;
        }
        Ok(sum)
    }
}

/// Evaluate the finite-field scalar equation induced by a shifted origin.
///
/// If point `i` reduces to `m_i G` and the chosen lifted origin reduces to
/// `m_o G`, an exact lifted relation has source residue
/// `sum_i n_i (m_i-m_o)` modulo the source subgroup order.
pub fn shifted_source_relation_residue(
    scalars: &[BigInt],
    point_multipliers: &[BigInt],
    origin_multiplier: &BigInt,
    group_order: &BigInt,
) -> Result<BigInt, String> {
    if scalars.len() != point_multipliers.len() {
        return Err("relation scalars and source multipliers must have the same length".into());
    }
    if group_order <= &BigInt::zero() {
        return Err("source group order must be positive".into());
    }
    let residue: BigInt = scalars
        .iter()
        .zip(point_multipliers)
        .map(|(scalar, multiplier)| scalar * (multiplier - origin_multiplier))
        .sum();
    Ok(residue.mod_floor(group_order))
}

/// Recover the one unknown source multiplier in a certified shifted relation.
///
/// `known_multipliers` must contain exactly one `None`.  `Ok(None)` means the
/// unknown's relation coefficient is not invertible modulo `group_order`.
pub fn recover_shifted_source_discrete_log(
    scalars: &[BigInt],
    known_multipliers: &[Option<BigInt>],
    origin_multiplier: &BigInt,
    group_order: &BigInt,
) -> Result<Option<BigInt>, String> {
    if scalars.len() != known_multipliers.len() {
        return Err("relation scalars and source multipliers must have the same length".into());
    }
    if group_order <= &BigInt::zero() {
        return Err("source group order must be positive".into());
    }
    let unknowns: Vec<usize> = known_multipliers
        .iter()
        .enumerate()
        .filter_map(|(index, multiplier)| multiplier.is_none().then_some(index))
        .collect();
    if unknowns.len() != 1 {
        return Err("exactly one source multiplier must be unknown".into());
    }
    let unknown = unknowns[0];
    let coefficient = scalars[unknown].mod_floor(group_order);
    let inverse = coefficient.extended_gcd(group_order);
    if inverse.gcd != BigInt::from(1) {
        return Ok(None);
    }
    let known_sum: BigInt = scalars
        .iter()
        .zip(known_multipliers)
        .filter_map(|(scalar, multiplier)| {
            multiplier
                .as_ref()
                .map(|multiplier| scalar * (multiplier - origin_multiplier))
        })
        .sum();
    let rhs = &coefficient * origin_multiplier - known_sum;
    Ok(Some((rhs * inverse.x).mod_floor(group_order)))
}

/// Evaluate the source residue when the chord origin uses the unknown target.
///
/// If `target_index` reduces to `t G` and `chord_known_index` reduces to
/// `m_j G`, their residual chord point reduces to `-(t+m_j)G`. This helper is
/// for certificate generation, where the planted target multiplier is known.
pub fn target_chord_source_relation_residue(
    scalars: &[BigInt],
    point_multipliers: &[BigInt],
    target_index: usize,
    chord_known_index: usize,
    group_order: &BigInt,
) -> Result<BigInt, String> {
    if scalars.len() != point_multipliers.len() {
        return Err("relation scalars and source multipliers must have the same length".into());
    }
    if target_index >= point_multipliers.len() || chord_known_index >= point_multipliers.len() {
        return Err("target or chord-known index is out of range".into());
    }
    if target_index == chord_known_index {
        return Err("target and chord-known indices must be distinct".into());
    }
    let origin_multiplier =
        -(&point_multipliers[target_index] + &point_multipliers[chord_known_index]);
    shifted_source_relation_residue(scalars, point_multipliers, &origin_multiplier, group_order)
}

/// Recover an unknown target whose point participates in the chord origin.
///
/// Let `S=sum_i n_i`. With chord origin `O=-(t+m_j)G`, reduction of an exact
/// lifted relation gives
///
/// `(n_t + S)t + sum_{i != t} n_i m_i + S m_j = 0 (mod group_order)`.
///
/// Thus the origin supplies a target coefficient even when `n_t=0`.
/// `known_multipliers` must contain exactly one `None`, and the chord partner
/// must be a different point with a known source multiplier. `Ok(None)` means
/// the effective coefficient `n_t+S` is not invertible.
pub fn recover_target_chord_source_discrete_log(
    scalars: &[BigInt],
    known_multipliers: &[Option<BigInt>],
    chord_known_index: usize,
    group_order: &BigInt,
) -> Result<Option<BigInt>, String> {
    if scalars.len() != known_multipliers.len() {
        return Err("relation scalars and source multipliers must have the same length".into());
    }
    if group_order <= &BigInt::zero() {
        return Err("source group order must be positive".into());
    }
    let unknowns: Vec<usize> = known_multipliers
        .iter()
        .enumerate()
        .filter_map(|(index, multiplier)| multiplier.is_none().then_some(index))
        .collect();
    if unknowns.len() != 1 {
        return Err("exactly one source multiplier must be unknown".into());
    }
    let target_index = unknowns[0];
    if chord_known_index >= known_multipliers.len() {
        return Err("chord-known index is out of range".into());
    }
    if chord_known_index == target_index {
        return Err("chord partner must have a known source multiplier".into());
    }
    let chord_multiplier = known_multipliers[chord_known_index]
        .as_ref()
        .ok_or_else(|| "chord partner must have a known source multiplier".to_string())?;
    let coefficient_sum: BigInt = scalars.iter().sum();
    let effective_coefficient = (&scalars[target_index] + &coefficient_sum).mod_floor(group_order);
    let inverse = effective_coefficient.extended_gcd(group_order);
    if inverse.gcd != BigInt::from(1) {
        return Ok(None);
    }
    let known_sum: BigInt = scalars
        .iter()
        .zip(known_multipliers)
        .filter_map(|(scalar, multiplier)| {
            multiplier.as_ref().map(|multiplier| scalar * multiplier)
        })
        .sum::<BigInt>()
        + coefficient_sum * chord_multiplier;
    Ok(Some((-known_sum * inverse.x).mod_floor(group_order)))
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

/// Strategy used to lift non-frame projective points from `P^2(F_p)` to `Z^3`.
#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum JksstPointLiftMode {
    /// 3D-LLL shortest primitive preimage in `{v in Z^3 : v = t * P (mod p)}`,
    /// achieving `O(p^(2/3))` coordinates and `O(p^2)` cubic monomials.
    #[default]
    ProjectiveLll,
    /// Balanced affine lift `(bal(X/Z), bal(Y/Z), 1)` when `Z != 0 mod p`.
    AffineBalanced,
}

/// Source-faithful JKSST Steps 3--9 plane-cubic lifting problem over `F_p`.
#[derive(Clone, Debug)]
pub struct JksstPlaneCubicProblem {
    pub modulus: BigInt,
    pub source_coefficients: Vec<BigInt>,
    pub source_points: Vec<[BigInt; 3]>,
    pub frame_indices: Option<[usize; 4]>,
    pub point_lift_mode: JksstPointLiftMode,
    pub max_frames: usize,
    pub reject_collinear_lifts: bool,
}

/// Decimal-string JSON input for `ca-icx xedni-lift --model jksst-plane-cubic`.
#[derive(Clone, Debug, Deserialize)]
pub struct JksstPlaneCubicInput {
    pub modulus: String,
    pub source_coefficients: Vec<String>,
    pub source_points: Vec<[String; 3]>,
    #[serde(default)]
    pub frame_indices: Option<[usize; 4]>,
    #[serde(default)]
    pub point_lift_mode: JksstPointLiftMode,
    #[serde(default = "default_jksst_max_frames")]
    pub max_frames: usize,
    #[serde(default)]
    pub reject_collinear_lifts: bool,
}

fn default_jksst_max_frames() -> usize {
    126
}

impl TryFrom<JksstPlaneCubicInput> for JksstPlaneCubicProblem {
    type Error = String;

    fn try_from(value: JksstPlaneCubicInput) -> Result<Self, Self::Error> {
        let modulus = parse_decimal(&value.modulus, "modulus")?;
        let source_coefficients = value
            .source_coefficients
            .iter()
            .map(|x| parse_decimal(x, "source_coefficients"))
            .collect::<Result<_, _>>()?;
        let source_points = value
            .source_points
            .iter()
            .map(|pt| {
                Ok([
                    parse_decimal(&pt[0], "source_points")?,
                    parse_decimal(&pt[1], "source_points")?,
                    parse_decimal(&pt[2], "source_points")?,
                ])
            })
            .collect::<Result<_, String>>()?;
        Ok(Self {
            modulus,
            source_coefficients,
            source_points,
            frame_indices: value.frame_indices,
            point_lift_mode: value.point_lift_mode,
            max_frames: value.max_frames,
            reject_collinear_lifts: value.reject_collinear_lifts,
        })
    }
}

/// Certified `PGL_3(F_p)` frame sending `(1:0:0), (0:1:0), (0:0:1), (1:1:1)`
/// to four chosen general-position source points.
#[derive(Clone, Debug)]
pub struct JksstProjectiveFrame {
    pub modulus: BigInt,
    pub frame_indices: [usize; 4],
    pub matrix_to_source: [[BigInt; 3]; 3],
    pub matrix_from_source: [[BigInt; 3]; 3],
    pub transformed_source_cubic: Vec<BigInt>,
    pub transformed_points_mod_p: Vec<[BigInt; 3]>,
}

/// Certified output of JKSST projective-frame + homogeneous-congruence lifting.
#[derive(Clone, Debug, Serialize)]
pub struct JksstPlaneCubicOptimization {
    pub method: &'static str,
    pub coefficient_order: &'static str,
    pub point_lift_mode: JksstPointLiftMode,
    pub frame_indices: [usize; 4],
    pub matrix_to_source_mod_p: [[String; 3]; 3],
    pub matrix_from_source_mod_p: [[String; 3]; 3],
    pub transformed_source_cubic_mod_p: Vec<String>,
    pub lifted_points: Vec<[String; 3]>,
    pub max_point_coordinate_bits: u64,
    pub pre_lift_collinear_triples: Vec<[usize; 3]>,
    pub homogeneous_scale_mod_p: String,
    pub optimized_coefficients: Vec<String>,
    pub optimized_score: PlaneCubicLiftScore,
    pub frames_evaluated: usize,
    pub candidates_evaluated: usize,
    pub incidence_preserved: bool,
    pub projective_congruence_preserved: bool,
    pub discriminant_evaluated: bool,
}

fn projective_determinant_3x3(p: &[BigInt; 3], q: &[BigInt; 3], r: &[BigInt; 3]) -> BigInt {
    &p[0] * (&q[1] * &r[2] - &q[2] * &r[1]) - &p[1] * (&q[0] * &r[2] - &q[2] * &r[0])
        + &p[2] * (&q[0] * &r[1] - &q[1] * &r[0])
}

/// Return all index triples `(i < j < k)` whose lifted projective points are
/// collinear over `Q` (`det([P_i, P_j, P_k]) = 0`).
///
/// Any such triple cuts a curve-independent hyperplane divisor `P_i + P_j + P_k ~ H`
/// on every smooth plane cubic through the lifted points, producing a five-term
/// shifted relation `(P_i - O) + (P_j - O) + (P_k - O) - (P_u - O) - (P_v - O) = 0`
/// regardless of the Step-9 cubic optimizer.
pub fn collinear_point_triples(points: &[PlaneCubicPoint]) -> Vec<[usize; 3]> {
    let mut triples = Vec::new();
    for i in 0..points.len() {
        for j in (i + 1)..points.len() {
            for k in (j + 1)..points.len() {
                if projective_determinant_3x3(
                    &points[i].coordinates,
                    &points[j].coordinates,
                    &points[k].coordinates,
                )
                .is_zero()
                {
                    triples.push([i, j, k]);
                }
            }
        }
    }
    triples
}

fn mod_pos(value: &BigInt, modulus: &BigInt) -> BigInt {
    value.mod_floor(modulus)
}

fn mod_inv(value: &BigInt, modulus: &BigInt) -> Result<BigInt, String> {
    let reduced = mod_pos(value, modulus);
    let egcd = reduced.extended_gcd(modulus);
    if egcd.gcd != BigInt::from(1) {
        return Err(format!("{reduced} is not invertible modulo {modulus}"));
    }
    Ok(mod_pos(&egcd.x, modulus))
}

fn canonical_projective_mod_p(
    point: &[BigInt; 3],
    modulus: &BigInt,
) -> Result<[BigInt; 3], String> {
    let reduced: [BigInt; 3] = std::array::from_fn(|i| mod_pos(&point[i], modulus));
    let Some(pivot) = reduced.iter().position(|x| !x.is_zero()) else {
        return Err("projective point reduces to (0,0,0) mod p".into());
    };
    let inv = mod_inv(&reduced[pivot], modulus)?;
    Ok(std::array::from_fn(|i| {
        mod_pos(&(&reduced[i] * &inv), modulus)
    }))
}

fn invert_3x3_mod_p(matrix: &[[BigInt; 3]; 3], modulus: &BigInt) -> Option<[[BigInt; 3]; 3]> {
    let m = matrix;
    let det = &m[0][0] * (&m[1][1] * &m[2][2] - &m[1][2] * &m[2][1])
        - &m[0][1] * (&m[1][0] * &m[2][2] - &m[1][2] * &m[2][0])
        + &m[0][2] * (&m[1][0] * &m[2][1] - &m[1][1] * &m[2][0]);
    let det_mod = mod_pos(&det, modulus);
    let egcd = det_mod.extended_gcd(modulus);
    if egcd.gcd != BigInt::from(1) {
        return None;
    }
    let inv_det = mod_pos(&egcd.x, modulus);
    let adj = [
        [
            &m[1][1] * &m[2][2] - &m[1][2] * &m[2][1],
            &m[0][2] * &m[2][1] - &m[0][1] * &m[2][2],
            &m[0][1] * &m[1][2] - &m[0][2] * &m[1][1],
        ],
        [
            &m[1][2] * &m[2][0] - &m[1][0] * &m[2][2],
            &m[0][0] * &m[2][2] - &m[0][2] * &m[2][0],
            &m[0][2] * &m[1][0] - &m[0][0] * &m[1][2],
        ],
        [
            &m[1][0] * &m[2][1] - &m[1][1] * &m[2][0],
            &m[0][1] * &m[2][0] - &m[0][0] * &m[2][1],
            &m[0][0] * &m[1][1] - &m[0][1] * &m[1][0],
        ],
    ];
    Some(std::array::from_fn(|r| {
        std::array::from_fn(|c| mod_pos(&(&adj[r][c] * &inv_det), modulus))
    }))
}

fn mat_vec_mod_p(matrix: &[[BigInt; 3]; 3], v: &[BigInt; 3], modulus: &BigInt) -> [BigInt; 3] {
    std::array::from_fn(|r| {
        mod_pos(
            &(&matrix[r][0] * &v[0] + &matrix[r][1] * &v[1] + &matrix[r][2] * &v[2]),
            modulus,
        )
    })
}

fn pullback_plane_cubic_mod_p(
    c: &[BigInt],
    matrix: &[[BigInt; 3]; 3],
    modulus: &BigInt,
) -> Result<Vec<BigInt>, String> {
    const EXPONENTS: [(usize, usize, usize); PLANE_CUBIC_COEFFICIENTS] = [
        (3, 0, 0),
        (2, 1, 0),
        (1, 2, 0),
        (0, 3, 0),
        (2, 0, 1),
        (1, 1, 1),
        (0, 2, 1),
        (1, 0, 2),
        (0, 1, 2),
        (0, 0, 3),
    ];
    let rows: [Vec<BigInt>; 3] = std::array::from_fn(|r| matrix[r].to_vec());
    let mut out = vec![BigInt::zero(); PLANE_CUBIC_COEFFICIENTS];
    for (coeff, (ex, ey, ez)) in c.iter().zip(EXPONENTS) {
        if mod_pos(coeff, modulus).is_zero() {
            continue;
        }
        let mut factors: Vec<&[BigInt]> = Vec::with_capacity(3);
        for _ in 0..ex {
            factors.push(&rows[0]);
        }
        for _ in 0..ey {
            factors.push(&rows[1]);
        }
        for _ in 0..ez {
            factors.push(&rows[2]);
        }
        let quad = multiply_linear_forms(factors[0], factors[1]);
        let cubic = multiply_quadratic_linear(&quad, factors[2]);
        for (slot, term) in out.iter_mut().zip(cubic) {
            *slot = mod_pos(&(&*slot + coeff * term), modulus);
        }
    }
    let Some(first) = out.iter().position(|x| !x.is_zero()) else {
        return Err("pulled-back source cubic vanishes modulo p".into());
    };
    let inv = mod_inv(&out[first], modulus)?;
    Ok(out
        .into_iter()
        .map(|x| mod_pos(&(x * &inv), modulus))
        .collect())
}

/// Construct JKSST's `PGL_3(F_p)` frame normalization sending `(1:0:0)`,
/// `(0:1:0)`, `(0:0:1)`, `(1:1:1)` to `source_points[frame_indices[0..4]]`.
pub fn jksst_projective_frame_mod_p(
    modulus: &BigInt,
    source_coefficients: &[BigInt],
    source_points: &[[BigInt; 3]],
    frame_indices: [usize; 4],
) -> Result<JksstProjectiveFrame, String> {
    if modulus <= &BigInt::from(3) {
        return Err("JKSST projective frame requires prime modulus p > 3".into());
    }
    if source_coefficients.len() != PLANE_CUBIC_COEFFICIENTS {
        return Err(format!(
            "expected {PLANE_CUBIC_COEFFICIENTS} source cubic coefficients, got {}",
            source_coefficients.len()
        ));
    }
    for (a_idx, &i) in frame_indices.iter().enumerate() {
        if i >= source_points.len() {
            return Err("frame index out of bounds".into());
        }
        if frame_indices[..a_idx].contains(&i) {
            return Err("frame indices must be distinct".into());
        }
    }
    let canonical_pts: Vec<[BigInt; 3]> = source_points
        .iter()
        .map(|pt| canonical_projective_mod_p(pt, modulus))
        .collect::<Result<_, _>>()?;
    for pt in &canonical_pts {
        let val = dot(
            &plane_cubic_incidence_row(&pt[0], &pt[1], &pt[2]),
            source_coefficients,
        );
        if !mod_pos(&val, modulus).is_zero() {
            return Err("a supplied source point is not on the source cubic modulo p".into());
        }
    }

    let base_cols: [[BigInt; 3]; 3] = std::array::from_fn(|r| {
        std::array::from_fn(|c| canonical_pts[frame_indices[c]][r].clone())
    });
    let Some(base_inv) = invert_3x3_mod_p(&base_cols, modulus) else {
        return Err("first three frame points are collinear modulo p".into());
    };
    let fourth = &canonical_pts[frame_indices[3]];
    let scales = mat_vec_mod_p(&base_inv, fourth, modulus);
    if scales
        .iter()
        .any(|s| s.extended_gcd(modulus).gcd != BigInt::from(1))
    {
        return Err("fourth frame point is collinear with two frame vertices modulo p".into());
    }
    let matrix_to_source: [[BigInt; 3]; 3] = std::array::from_fn(|r| {
        std::array::from_fn(|c| mod_pos(&(&base_cols[r][c] * &scales[c]), modulus))
    });
    let Some(matrix_from_source) = invert_3x3_mod_p(&matrix_to_source, modulus) else {
        return Err("projective frame matrix is not invertible modulo p".into());
    };
    let transformed_points_mod_p: Vec<[BigInt; 3]> = canonical_pts
        .iter()
        .map(|pt| {
            let mapped = mat_vec_mod_p(&matrix_from_source, pt, modulus);
            canonical_projective_mod_p(&mapped, modulus)
        })
        .collect::<Result<_, _>>()?;
    let transformed_source_cubic =
        pullback_plane_cubic_mod_p(source_coefficients, &matrix_to_source, modulus)?;

    // Certify exact standard-frame image and cubic incidence mod p.
    let expected_frame = [
        [BigInt::from(1), BigInt::zero(), BigInt::zero()],
        [BigInt::zero(), BigInt::from(1), BigInt::zero()],
        [BigInt::zero(), BigInt::zero(), BigInt::from(1)],
        [BigInt::from(1), BigInt::from(1), BigInt::from(1)],
    ];
    for (slot, expected) in frame_indices.iter().zip(&expected_frame) {
        if &transformed_points_mod_p[*slot] != expected {
            return Err("internal error: frame normalization missed a standard vertex".into());
        }
    }
    for pt in &transformed_points_mod_p {
        let val = dot(
            &plane_cubic_incidence_row(&pt[0], &pt[1], &pt[2]),
            &transformed_source_cubic,
        );
        if !mod_pos(&val, modulus).is_zero() {
            return Err("internal error: transformed point left pulled-back source cubic".into());
        }
    }
    Ok(JksstProjectiveFrame {
        modulus: modulus.clone(),
        frame_indices,
        matrix_to_source,
        matrix_from_source,
        transformed_source_cubic,
        transformed_points_mod_p,
    })
}

fn balanced_residue(value: &BigInt, modulus: &BigInt) -> BigInt {
    let r = mod_pos(value, modulus);
    let half = modulus >> 1;
    if r > half {
        r - modulus
    } else {
        r
    }
}

/// Lift one projective point from `P^2(F_p)` to a short primitive integer vector
/// in `{v in Z^3 : v in <point_mod_p> + p Z^3}` via 3D LLL (`O(p^(2/3))` norm).
pub fn lift_projective_point_lll(
    point_mod_p: &[BigInt; 3],
    modulus: &BigInt,
) -> Result<PlaneCubicPoint, String> {
    if modulus <= &BigInt::from(3) {
        return Err("modulus must exceed 3".into());
    }
    let canon = canonical_projective_mod_p(point_mod_p, modulus)?;
    let pivot = canon
        .iter()
        .position(|x| x == &BigInt::from(1))
        .ok_or_else(|| "canonical projective point lacks unit pivot".to_string())?;
    let mut basis = Vec::with_capacity(3);
    basis.push(vec![
        balanced_residue(&canon[0], modulus),
        balanced_residue(&canon[1], modulus),
        balanced_residue(&canon[2], modulus),
    ]);
    for j in 0..3 {
        if j != pivot {
            let mut row = vec![BigInt::zero(); 3];
            row[j] = modulus.clone();
            basis.push(row);
        }
    }
    lll_reduce_hp(&mut basis, 0.99).map_err(str::to_string)?;

    let mut best: Option<(BigInt, [BigInt; 3])> = None;
    for c0 in -1i64..=1 {
        for c1 in -1i64..=1 {
            for c2 in -1i64..=1 {
                if c0 == 0 && c1 == 0 && c2 == 0 {
                    continue;
                }
                let candidate: [BigInt; 3] = std::array::from_fn(|k| {
                    &basis[0][k] * c0 + &basis[1][k] * c1 + &basis[2][k] * c2
                });
                if candidate.iter().all(|x| mod_pos(x, modulus).is_zero()) {
                    continue;
                }
                let prim = PlaneCubicPoint::new(candidate)?;
                let norm2: BigInt = prim.coordinates.iter().map(|x| x * x).sum();
                let replace = match &best {
                    None => true,
                    Some((best_norm, best_coords)) => {
                        (&norm2, &prim.coordinates) < (best_norm, best_coords)
                    }
                };
                if replace {
                    best = Some((norm2, prim.coordinates));
                }
            }
        }
    }
    let (_, chosen) = best.ok_or_else(|| "no valid projective LLL preimage found".to_string())?;
    if canonical_projective_mod_p(&chosen, modulus)? != canon {
        return Err("internal error: 3D-LLL point lift changed projective class mod p".into());
    }
    PlaneCubicPoint::new(chosen)
}

fn lift_projective_point_affine_balanced(
    point_mod_p: &[BigInt; 3],
    modulus: &BigInt,
) -> Result<PlaneCubicPoint, String> {
    let canon = canonical_projective_mod_p(point_mod_p, modulus)?;
    if canon[2].is_zero() {
        return lift_projective_point_lll(&canon, modulus);
    }
    let z_inv = mod_inv(&canon[2], modulus)?;
    let x = balanced_residue(&(&canon[0] * &z_inv), modulus);
    let y = balanced_residue(&(&canon[1] * &z_inv), modulus);
    PlaneCubicPoint::new([x, y, BigInt::from(1)])
}

/// Compute a saturated integer basis of `{c in Z^ncols : rows * c = 0}` using
/// unimodular column reduction.
pub fn integer_kernel_basis(
    rows: &[Vec<BigInt>],
    ncols: usize,
) -> Result<Vec<Vec<BigInt>>, String> {
    let nrows = rows.len();
    if rows.iter().any(|r| r.len() != ncols) {
        return Err("matrix row length mismatch".into());
    }
    let mut h: Vec<Vec<BigInt>> = rows.to_vec();
    let mut u: Vec<Vec<BigInt>> = (0..ncols)
        .map(|i| (0..ncols).map(|j| BigInt::from(i == j)).collect())
        .collect();
    let mut col = 0usize;
    for r in 0..nrows {
        if col >= ncols {
            break;
        }
        loop {
            let nonzero: Vec<usize> = (col..ncols).filter(|&j| !h[r][j].is_zero()).collect();
            if nonzero.len() <= 1 {
                break;
            }
            let pivot_col = *nonzero
                .iter()
                .min_by(|&&a, &&b| h[r][a].magnitude().cmp(h[r][b].magnitude()))
                .expect("nonempty");
            for &j in &nonzero {
                if j == pivot_col {
                    continue;
                }
                let q = h[r][j].div_floor(&h[r][pivot_col]);
                let q = if q.is_zero() {
                    if h[r][j].sign() == h[r][pivot_col].sign() {
                        BigInt::from(1)
                    } else {
                        BigInt::from(-1)
                    }
                } else {
                    q
                };
                for row_h in h.iter_mut().take(nrows) {
                    let delta = &q * &row_h[pivot_col];
                    row_h[j] -= delta;
                }
                for row_u in u.iter_mut().take(ncols) {
                    let delta = &q * &row_u[pivot_col];
                    row_u[j] -= delta;
                }
            }
        }
        let Some(pivot_col) = (col..ncols).find(|&j| !h[r][j].is_zero()) else {
            continue;
        };
        if pivot_col != col {
            for row_h in h.iter_mut().take(nrows) {
                row_h.swap(col, pivot_col);
            }
            for row_u in u.iter_mut().take(ncols) {
                row_u.swap(col, pivot_col);
            }
        }
        col += 1;
    }
    let mut basis = Vec::with_capacity(ncols.saturating_sub(col));
    for j in col..ncols {
        let vec: Vec<BigInt> = (0..ncols).map(|i| u[i][j].clone()).collect();
        if vec.iter().all(BigInt::is_zero) {
            return Err("internal error: zero unimodular kernel column".into());
        }
        if rows.iter().any(|row| !dot(row, &vec).is_zero()) {
            return Err("internal error: kernel column violates incidence constraint".into());
        }
        basis.push(vec);
    }
    Ok(basis)
}

fn row_hermite_basis(mut rows: Vec<Vec<BigInt>>, ncols: usize) -> Vec<Vec<BigInt>> {
    let mut rank = 0usize;
    for col in 0..ncols {
        loop {
            let active: Vec<usize> = (rank..rows.len())
                .filter(|&i| !rows[i][col].is_zero())
                .collect();
            if active.len() <= 1 {
                break;
            }
            let piv = *active
                .iter()
                .min_by(|&&a, &&b| rows[a][col].magnitude().cmp(rows[b][col].magnitude()))
                .expect("nonempty");
            for &i in &active {
                if i == piv {
                    continue;
                }
                let q = rows[i][col].div_floor(&rows[piv][col]);
                let piv_row = rows[piv].clone();
                for (entry, p_val) in rows[i].iter_mut().zip(&piv_row) {
                    *entry -= &q * p_val;
                }
            }
        }
        let Some(piv) = (rank..rows.len()).find(|&i| !rows[i][col].is_zero()) else {
            continue;
        };
        rows.swap(rank, piv);
        if rows[rank][col].is_negative() {
            for entry in &mut rows[rank] {
                *entry = -&*entry;
            }
        }
        for i in 0..rank {
            let q = rows[i][col].div_floor(&rows[rank][col]);
            if !q.is_zero() {
                let rank_row = rows[rank].clone();
                for (entry, r_val) in rows[i].iter_mut().zip(&rank_row) {
                    *entry -= &q * r_val;
                }
            }
        }
        rank += 1;
        if rank == ncols {
            break;
        }
    }
    rows.truncate(rank);
    rows
}

fn homogeneous_scale_factor_mod_p(
    candidate: &[BigInt],
    target_mod_p: &[BigInt],
    modulus: &BigInt,
) -> Option<BigInt> {
    let pivot = target_mod_p
        .iter()
        .position(|x| !mod_pos(x, modulus).is_zero())?;
    let t_inv = mod_inv(&target_mod_p[pivot], modulus).ok()?;
    let scale = mod_pos(&(&candidate[pivot] * t_inv), modulus);
    if scale.is_zero() || scale.extended_gcd(modulus).gcd != BigInt::from(1) {
        return None;
    }
    let ok = candidate
        .iter()
        .zip(target_mod_p)
        .all(|(c, t)| mod_pos(&(c - &scale * t), modulus).is_zero());
    ok.then_some(scale)
}

/// Construct an exact integer basis of the homogeneous congruence sublattice
/// `{c in ker_Z(B) : exists mu in Z, c = mu * target_cubic (mod p)}`.
pub fn homogeneous_congruence_sublattice(
    kernel_basis: &[Vec<BigInt>],
    target_cubic_mod_p: &[BigInt],
    modulus: &BigInt,
) -> Result<Vec<Vec<BigInt>>, String> {
    let d = kernel_basis.len();
    if d == 0 {
        return Err("empty incidence kernel".into());
    }
    let nvars = d + 1;
    let mut mat = vec![vec![BigInt::zero(); nvars]; PLANE_CUBIC_COEFFICIENTS];
    for row in 0..PLANE_CUBIC_COEFFICIENTS {
        for (col, kvec) in kernel_basis.iter().enumerate() {
            mat[row][col] = mod_pos(&kvec[row], modulus);
        }
        mat[row][d] = mod_pos(&(-&target_cubic_mod_p[row]), modulus);
    }

    // Modular RREF over F_p.
    let mut pivot_cols = Vec::new();
    let mut rank = 0usize;
    for col in 0..nvars {
        let Some(piv) = (rank..PLANE_CUBIC_COEFFICIENTS)
            .find(|&r| mat[r][col].extended_gcd(modulus).gcd == BigInt::from(1))
        else {
            continue;
        };
        mat.swap(rank, piv);
        let inv = mod_inv(&mat[rank][col], modulus)?;
        for entry in &mut mat[rank][col..] {
            *entry = mod_pos(&(&*entry * &inv), modulus);
        }
        let piv_row = mat[rank].clone();
        for (r_idx, row_vec) in mat.iter_mut().enumerate() {
            if r_idx == rank || row_vec[col].is_zero() {
                continue;
            }
            let factor = row_vec[col].clone();
            for c_idx in col..nvars {
                row_vec[c_idx] = mod_pos(&(&row_vec[c_idx] - &factor * &piv_row[c_idx]), modulus);
            }
        }
        pivot_cols.push(col);
        rank += 1;
        if rank == PLANE_CUBIC_COEFFICIENTS {
            break;
        }
    }

    let free_cols: Vec<usize> = (0..nvars).filter(|c| !pivot_cols.contains(c)).collect();
    let mut null_vectors = Vec::new();
    let mut has_nonzero_mu = false;
    for &free in &free_cols {
        let mut v = vec![BigInt::zero(); nvars];
        v[free] = BigInt::from(1);
        for (row_idx, &pcol) in pivot_cols.iter().enumerate() {
            v[pcol] = mod_pos(&(-&mat[row_idx][free]), modulus);
        }
        if !v[d].is_zero() {
            has_nonzero_mu = true;
        }
        null_vectors.push(v);
    }
    if !has_nonzero_mu {
        return Err("kernel contains no projective preimage of the source cubic modulo p".into());
    }

    let mut alpha_generators: Vec<Vec<BigInt>> = null_vectors
        .into_iter()
        .map(|v| v[..d].to_vec())
        .filter(|alpha| alpha.iter().any(|x| !x.is_zero()))
        .collect();
    for i in 0..d {
        let mut p_row = vec![BigInt::zero(); d];
        p_row[i] = modulus.clone();
        alpha_generators.push(p_row);
    }
    let alpha_basis = row_hermite_basis(alpha_generators, d);
    if alpha_basis.len() != d {
        return Err("internal error: homogeneous sublattice lost rank".into());
    }
    let mut sublattice = Vec::with_capacity(d);
    for alpha in alpha_basis {
        let mut vec = vec![BigInt::zero(); PLANE_CUBIC_COEFFICIENTS];
        for (coeff, kvec) in alpha.iter().zip(kernel_basis) {
            for (slot, val) in vec.iter_mut().zip(kvec) {
                *slot += coeff * val;
            }
        }
        sublattice.push(vec);
    }
    Ok(sublattice)
}

fn primitivize_cubic(mut c: Vec<BigInt>) -> Vec<BigInt> {
    let g = c.iter().fold(BigInt::zero(), |acc, x| acc.gcd(x));
    if g > BigInt::from(1) {
        for x in &mut c {
            *x /= &g;
        }
    }
    if c.iter()
        .find(|x| !x.is_zero())
        .is_some_and(Signed::is_negative)
    {
        for x in &mut c {
            *x = -&*x;
        }
    }
    c
}

fn enumerate_homogeneous_lattice(
    depth: usize,
    radius: i64,
    coeffs: &mut [i64],
    basis: &[Vec<BigInt>],
    target_mod_p: &[BigInt],
    modulus: &BigInt,
    evaluated: &mut usize,
    limit: usize,
    best: &mut Option<(Vec<BigInt>, PlaneCubicLiftScore, BigInt)>,
) -> Result<(), String> {
    if *evaluated >= limit {
        return Ok(());
    }
    if depth == coeffs.len() {
        let Some(&first_nz) = coeffs.iter().find(|&&x| x != 0) else {
            return Ok(());
        };
        if first_nz < 0 {
            return Ok(());
        }
        let mut raw = vec![BigInt::zero(); PLANE_CUBIC_COEFFICIENTS];
        for (&mult, bvec) in coeffs.iter().zip(basis) {
            if mult != 0 {
                for (slot, val) in raw.iter_mut().zip(bvec) {
                    *slot += val * mult;
                }
            }
        }
        let candidate = primitivize_cubic(raw);
        let Some(scale) = homogeneous_scale_factor_mod_p(&candidate, target_mod_p, modulus) else {
            return Ok(());
        };
        let score = score_plane_cubic_lift(&candidate)?;
        *evaluated += 1;
        let replace = match best {
            None => true,
            Some((_, best_score, _)) => better_plane_cubic(&score, best_score),
        };
        if replace {
            *best = Some((candidate, score, scale));
        }
        return Ok(());
    }
    for val in -radius..=radius {
        coeffs[depth] = val;
        enumerate_homogeneous_lattice(
            depth + 1,
            radius,
            coeffs,
            basis,
            target_mod_p,
            modulus,
            evaluated,
            limit,
            best,
        )?;
        if *evaluated >= limit {
            break;
        }
    }
    Ok(())
}

/// Execute JKSST Steps 3--9 for `4 <= r <= 9` source points:
/// normalize four points to `(1:0:0), (0:1:0), (0:0:1), (1:1:1)` via `PGL_3(F_p)`,
/// lift the remaining `r - 4` points projectively by 3D LLL (`O(p^(2/3))`),
/// and optimize the homogeneous projective-congruence plane-cubic sublattice.
pub fn optimize_jksst_plane_cubic_lift(
    problem: &JksstPlaneCubicProblem,
    options: LiftSearchOptions,
) -> Result<JksstPlaneCubicOptimization, String> {
    let r = problem.source_points.len();
    if !(4..=9).contains(&r) {
        return Err("JKSST projective-frame plane-cubic mode requires 4 through 9 points".into());
    }
    if options.neighborhood_radius < 0 || options.max_candidates == 0 {
        return Err("search radius must be nonnegative and candidate cap positive".into());
    }
    if problem.max_frames == 0 {
        return Err("max_frames must be positive".into());
    }

    let mut candidate_frames: Vec<[usize; 4]> = Vec::new();
    if let Some(explicit) = problem.frame_indices {
        candidate_frames.push(explicit);
    } else {
        for i0 in 0..r {
            for i1 in (i0 + 1)..r {
                for i2 in (i1 + 1)..r {
                    for i3 in (i2 + 1)..r {
                        candidate_frames.push([i0, i1, i2, i3]);
                    }
                }
            }
        }
    }

    let mut frames_evaluated = 0usize;
    let mut total_candidates = 0usize;
    let mut best_bundle: Option<(
        JksstProjectiveFrame,
        Vec<PlaneCubicPoint>,
        Vec<[usize; 3]>,
        Vec<BigInt>,
        PlaneCubicLiftScore,
        BigInt,
    )> = None;

    for frame_indices in candidate_frames {
        if frames_evaluated >= problem.max_frames {
            break;
        }
        let Ok(frame) = jksst_projective_frame_mod_p(
            &problem.modulus,
            &problem.source_coefficients,
            &problem.source_points,
            frame_indices,
        ) else {
            continue;
        };
        frames_evaluated += 1;

        let mut lifted_points = Vec::with_capacity(r);
        for (idx, pt_mod_p) in frame.transformed_points_mod_p.iter().enumerate() {
            let pt = if frame_indices.contains(&idx) {
                PlaneCubicPoint::new(pt_mod_p.clone())?
            } else {
                match problem.point_lift_mode {
                    JksstPointLiftMode::ProjectiveLll => {
                        lift_projective_point_lll(pt_mod_p, &problem.modulus)?
                    }
                    JksstPointLiftMode::AffineBalanced => {
                        lift_projective_point_affine_balanced(pt_mod_p, &problem.modulus)?
                    }
                }
            };
            lifted_points.push(pt);
        }
        let collinear = collinear_point_triples(&lifted_points);
        if problem.reject_collinear_lifts && !collinear.is_empty() {
            continue;
        }

        let incidence_rows: Vec<Vec<BigInt>> = lifted_points
            .iter()
            .map(|pt| {
                let [x, y, z] = &pt.coordinates;
                plane_cubic_incidence_row(x, y, z)
            })
            .collect();
        let kernel = integer_kernel_basis(&incidence_rows, PLANE_CUBIC_COEFFICIENTS)?;
        if kernel.is_empty() {
            continue;
        }
        let Ok(mut sublattice) = homogeneous_congruence_sublattice(
            &kernel,
            &frame.transformed_source_cubic,
            &problem.modulus,
        ) else {
            continue;
        };
        if sublattice.len() > 1 {
            lll_reduce_hp(&mut sublattice, 0.99).map_err(str::to_string)?;
        }

        let mut frame_best: Option<(Vec<BigInt>, PlaneCubicLiftScore, BigInt)> = None;
        let mut evaluated = 0usize;
        for bvec in &sublattice {
            if evaluated >= options.max_candidates {
                break;
            }
            let cand = primitivize_cubic(bvec.clone());
            if let Some(scale) = homogeneous_scale_factor_mod_p(
                &cand,
                &frame.transformed_source_cubic,
                &problem.modulus,
            ) {
                let score = score_plane_cubic_lift(&cand)?;
                evaluated += 1;
                let replace = match &frame_best {
                    None => true,
                    Some((_, best_s, _)) => better_plane_cubic(&score, best_s),
                };
                if replace {
                    frame_best = Some((cand, score, scale));
                }
            }
        }
        if sublattice.len() > 1
            && options.neighborhood_radius > 0
            && evaluated < options.max_candidates
        {
            let mut coeffs = vec![0i64; sublattice.len()];
            enumerate_homogeneous_lattice(
                0,
                options.neighborhood_radius,
                &mut coeffs,
                &sublattice,
                &frame.transformed_source_cubic,
                &problem.modulus,
                &mut evaluated,
                options.max_candidates,
                &mut frame_best,
            )?;
        }
        total_candidates += evaluated;

        let Some((cand, score, scale)) = frame_best else {
            continue;
        };
        let replace = match &best_bundle {
            None => true,
            Some((_, _, _, _, best_score, _)) => better_plane_cubic(&score, best_score),
        };
        if replace {
            best_bundle = Some((frame, lifted_points, collinear, cand, score, scale));
        }
    }

    let Some((frame, lifted_points, collinear, optimized, score, scale)) = best_bundle else {
        return Err("no admissible JKSST projective-frame lift found".into());
    };

    let incidence_preserved = lifted_points
        .iter()
        .all(|pt| plane_cubic_value(&optimized, pt).is_zero());
    let projective_congruence_preserved = homogeneous_scale_factor_mod_p(
        &optimized,
        &frame.transformed_source_cubic,
        &problem.modulus,
    ) == Some(scale.clone());
    if !incidence_preserved || !projective_congruence_preserved {
        return Err("internal error: JKSST plane-cubic lift failed output certification".into());
    }
    let max_point_coordinate_bits = lifted_points
        .iter()
        .flat_map(|pt| pt.coordinates.iter())
        .map(abs_bits)
        .max()
        .unwrap_or(0);

    Ok(JksstPlaneCubicOptimization {
        method: "PGL3(F_p) 4-point frame + 3D-LLL projective point lift + homogeneous-congruence plane-cubic LLL",
        coefficient_order: "X^3,X^2Y,XY^2,Y^3,X^2Z,XYZ,Y^2Z,XZ^2,YZ^2,Z^3",
        point_lift_mode: problem.point_lift_mode,
        frame_indices: frame.frame_indices,
        matrix_to_source_mod_p: frame
            .matrix_to_source
            .map(|row| row.map(|v| v.to_string())),
        matrix_from_source_mod_p: frame
            .matrix_from_source
            .map(|row| row.map(|v| v.to_string())),
        transformed_source_cubic_mod_p: frame
            .transformed_source_cubic
            .iter()
            .map(ToString::to_string)
            .collect(),
        lifted_points: lifted_points
            .iter()
            .map(|pt| pt.coordinates.clone().map(|v| v.to_string()))
            .collect(),
        max_point_coordinate_bits,
        pre_lift_collinear_triples: collinear,
        homogeneous_scale_mod_p: scale.to_string(),
        optimized_coefficients: optimized.iter().map(ToString::to_string).collect(),
        optimized_score: score,
        frames_evaluated,
        candidates_evaluated: total_candidates,
        incidence_preserved,
        projective_congruence_preserved,
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

        // Close the formerly missing r=9 seam: use a chord-derived origin,
        // certify a relation involving the ninth point, and recover its
        // source multiplier from that shifted relation.
        let optimized = result
            .optimized_coefficients
            .iter()
            .map(|value| big(value))
            .collect();
        let multiples = plane_cubic_test_multiples();
        let group =
            PlaneCubicGroup::with_chord_origin(optimized, &multiples[0], &multiples[1]).unwrap();
        let relation_scalars = bi(&[2, -1]);
        let relation = group
            .relation_sum(
                &relation_scalars,
                &[multiples[2].clone(), multiples[8].clone()],
            )
            .unwrap();
        assert_eq!(&relation, group.origin());
        assert_eq!(
            recover_shifted_source_discrete_log(
                &relation_scalars,
                &[Some(BigInt::from(3)), None],
                &BigInt::from(-3),
                &BigInt::from(73),
            )
            .unwrap(),
            Some(BigInt::from(9))
        );
    }

    fn plane_cubic_test_point(x: &str, y: &str, z: &str) -> PlaneCubicPoint {
        PlaneCubicPoint::new([big(x), big(y), big(z)]).unwrap()
    }

    fn plane_cubic_test_multiples() -> Vec<PlaneCubicPoint> {
        [
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
        ]
        .into_iter()
        .map(|(x, y, z)| plane_cubic_test_point(x, y, z))
        .collect()
    }

    #[test]
    fn exact_plane_cubic_group_recovers_nine_known_multiples() {
        // y^2 z = x^3 - x z^2 + z^3 with its flex at infinity as origin.
        let coefficients = bi(&[1, 0, 0, 0, 0, 0, -1, -1, 0, 1]);
        let infinity = plane_cubic_test_point("0", "1", "0");
        let group = PlaneCubicGroup::new(coefficients, infinity).unwrap();
        let multiples = plane_cubic_test_multiples();
        let generator = &multiples[0];
        for (index, expected) in multiples.iter().enumerate() {
            let actual = group
                .scalar_mul(&BigInt::from(index + 1), generator)
                .unwrap();
            assert_eq!(&actual, expected, "incorrect multiple {}", index + 1);
        }
    }

    #[test]
    fn exact_plane_cubic_group_accepts_nonflex_origin() {
        let coefficients = bi(&[1, 0, 0, 0, 0, 0, -1, -1, 0, 1]);
        let multiples = plane_cubic_test_multiples();
        let standard_infinity = plane_cubic_test_point("0", "1", "0");
        let group = PlaneCubicGroup::new(coefficients, multiples[0].clone()).unwrap();

        // With O=G, the shifted law is P (+)_O Q = P+Q-G in the standard law.
        assert_eq!(
            group.add(&multiples[0], &multiples[3]).unwrap(),
            multiples[3]
        );
        assert_eq!(
            group.add(&multiples[1], &multiples[2]).unwrap(),
            multiples[3]
        );
        assert_eq!(group.negate(&multiples[1]).unwrap(), standard_infinity);

        let left = group
            .add(
                &group.add(&multiples[1], &multiples[2]).unwrap(),
                &multiples[3],
            )
            .unwrap();
        let right = group
            .add(
                &multiples[1],
                &group.add(&multiples[2], &multiples[3]).unwrap(),
            )
            .unwrap();
        assert_eq!(left, right);
    }

    #[test]
    fn chord_origin_preserves_all_relation_points_and_known_source_shift() {
        let coefficients = bi(&[1, 0, 0, 0, 0, 0, -1, -1, 0, 1]);
        let multiples = plane_cubic_test_multiples();
        let standard_infinity = plane_cubic_test_point("0", "1", "0");
        let standard_group = PlaneCubicGroup::new(coefficients.clone(), standard_infinity).unwrap();
        let group =
            PlaneCubicGroup::with_chord_origin(coefficients, &multiples[0], &multiples[1]).unwrap();

        // The residual chord point through G and 2G is -3G in the source law.
        let expected_origin = standard_group
            .scalar_mul(&BigInt::from(-3), &multiples[0])
            .unwrap();
        assert_eq!(group.origin(), &expected_origin);

        // Relative to that origin, G + 2G - 6G is zero:
        // 1 + 2 - 6 - (1 + 1 - 1)(-3) = 0 in source scalar coordinates.
        let relation = group
            .relation_sum(
                &bi(&[1, 1, -1]),
                &[
                    multiples[0].clone(),
                    multiples[1].clone(),
                    multiples[5].clone(),
                ],
            )
            .unwrap();
        assert_eq!(&relation, group.origin());

        let relation_scalars = bi(&[1, 1, -1]);
        let source_multipliers = bi(&[1, 2, 6]);
        let source_order = BigInt::from(73);
        assert!(shifted_source_relation_residue(
            &relation_scalars,
            &source_multipliers,
            &BigInt::from(-3),
            &source_order,
        )
        .unwrap()
        .is_zero());
        assert_eq!(
            recover_shifted_source_discrete_log(
                &relation_scalars,
                &[Some(BigInt::from(1)), Some(BigInt::from(2)), None],
                &BigInt::from(-3),
                &source_order,
            )
            .unwrap(),
            Some(BigInt::from(6))
        );
    }

    #[test]
    fn target_chord_origin_recovers_zero_explicit_target_coefficient() {
        let coefficients = bi(&[1, 0, 0, 0, 0, 0, -1, -1, 0, 1]);
        let multiples = plane_cubic_test_multiples();
        let standard_infinity = plane_cubic_test_point("0", "1", "0");
        let standard_group = PlaneCubicGroup::new(coefficients.clone(), standard_infinity).unwrap();
        let group =
            PlaneCubicGroup::with_chord_origin(coefficients, &multiples[8], &multiples[0]).unwrap();

        // The residual chord point through target 9G and known G is -10G.
        let expected_origin = standard_group
            .scalar_mul(&BigInt::from(-10), &multiples[0])
            .unwrap();
        assert_eq!(group.origin(), &expected_origin);

        // Relative to -10G, -2(G-O) -(2G-O) +2(7G-O)=0. The explicit
        // coefficient of target 9G is zero, but the coefficient sum is -1,
        // so the target enters through O=-(9G+G).
        let relation_scalars = bi(&[-2, -1, 0, 0, 0, 0, 2, 0, 0]);
        assert!(relation_scalars[8].is_zero());
        assert_eq!(relation_scalars.iter().sum::<BigInt>(), BigInt::from(-1));
        let relation = group.relation_sum(&relation_scalars, &multiples).unwrap();
        assert_eq!(&relation, group.origin());

        let source_multipliers = bi(&[1, 2, 3, 4, 5, 6, 7, 8, 9]);
        let source_order = BigInt::from(73);
        assert!(target_chord_source_relation_residue(
            &relation_scalars,
            &source_multipliers,
            8,
            0,
            &source_order,
        )
        .unwrap()
        .is_zero());
        assert_eq!(
            recover_target_chord_source_discrete_log(
                &relation_scalars,
                &[
                    Some(BigInt::from(1)),
                    Some(BigInt::from(2)),
                    Some(BigInt::from(3)),
                    Some(BigInt::from(4)),
                    Some(BigInt::from(5)),
                    Some(BigInt::from(6)),
                    Some(BigInt::from(7)),
                    Some(BigInt::from(8)),
                    None,
                ],
                0,
                &source_order,
            )
            .unwrap(),
            Some(BigInt::from(9))
        );

        let mut mutated = relation_scalars;
        mutated[6] += 1;
        assert_ne!(
            group.relation_sum(&mutated, &multiples).unwrap(),
            *group.origin()
        );
    }

    #[test]
    fn exact_plane_cubic_group_certifies_integer_relations() {
        let coefficients = bi(&[1, 0, 0, 0, 0, 0, -1, -1, 0, 1]);
        let infinity = plane_cubic_test_point("0", "1", "0");
        let group = PlaneCubicGroup::new(coefficients, infinity.clone()).unwrap();
        let multiples = plane_cubic_test_multiples();
        let relation = group
            .relation_sum(
                &bi(&[1, 1, -1]),
                &[
                    multiples[1].clone(),
                    multiples[2].clone(),
                    multiples[4].clone(),
                ],
            )
            .unwrap();
        assert_eq!(relation, infinity);
    }

    #[test]
    fn exact_plane_cubic_group_rejects_invalid_models_and_points() {
        let origin = plane_cubic_test_point("0", "1", "0");
        let singular = bi(&[1, 0, 0, 1, 0, -3, 0, 0, 0, 1]);
        assert!(PlaneCubicGroup::new(singular, origin.clone())
            .unwrap_err()
            .contains("singular"));

        let coefficients = bi(&[1, 0, 0, 0, 0, 0, -1, -1, 0, 1]);
        let off_curve = plane_cubic_test_point("1", "0", "1");
        assert!(PlaneCubicGroup::new(coefficients, off_curve)
            .unwrap_err()
            .contains("not on"));
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

    #[test]
    fn collinear_point_detector_separates_line_aliases_from_cubic_relations() {
        let multiples = plane_cubic_test_multiples();
        // Positive multiples G..9G of an infinite-order point have m_a+m_b+m_c >= 3 > 0,
        // so none are collinear over Q.
        assert!(collinear_point_triples(&multiples).is_empty());

        let with_line = vec![
            plane_cubic_test_point("0", "1", "1"),
            plane_cubic_test_point("3", "7", "1"),
            plane_cubic_test_point("6", "13", "1"),
            plane_cubic_test_point("2", "9", "1"),
        ];
        assert_eq!(collinear_point_triples(&with_line), vec![[0, 1, 2]]);
    }

    #[test]
    fn jksst_projective_frame_pulls_back_cubic_and_preserves_chord_origin() {
        // y^2 = x^3 - x + 1 over F_67, where G = (0, 1) has prime order 73.
        let p = BigInt::from(67);
        let source_cubic = bi(&[1, 0, 0, 0, 0, 0, -1, -1, 0, 1]);
        let multiples_q = plane_cubic_test_multiples();
        let source_pts: Vec<[BigInt; 3]> = multiples_q
            .iter()
            .map(|pt| canonical_projective_mod_p(&pt.coordinates, &p).unwrap())
            .collect();

        let frame =
            jksst_projective_frame_mod_p(&p, &source_cubic, &source_pts, [0, 1, 2, 3]).unwrap();
        // Standard vertices (1:0:0), (0:1:0), (0:0:1) force c0 = c3 = c9 = 0 mod p.
        assert!(frame.transformed_source_cubic[0].is_zero());
        assert!(frame.transformed_source_cubic[3].is_zero());
        assert!(frame.transformed_source_cubic[9].is_zero());

        // Check GL_3(F_p) equivariance of the binary-cubic chord formula mod p:
        // chordRaw(c', Q0, Q1) mapped by M equals chordRaw(c, P0, P1) in P^2(F_67).
        let p0 = PlaneCubicPoint::new(source_pts[0].clone()).unwrap();
        let p1 = PlaneCubicPoint::new(source_pts[1].clone()).unwrap();
        let res_src = binary_cubic_restriction(&source_cubic, &p0, &p1);
        let chord_src: [BigInt; 3] = std::array::from_fn(|i| {
            &res_src[2] * &p0.coordinates[i] - &res_src[1] * &p1.coordinates[i]
        });
        let chord_src_mod = canonical_projective_mod_p(&chord_src, &p).unwrap();

        let q0 = PlaneCubicPoint::new(frame.transformed_points_mod_p[0].clone()).unwrap();
        let q1 = PlaneCubicPoint::new(frame.transformed_points_mod_p[1].clone()).unwrap();
        let res_framed = binary_cubic_restriction(&frame.transformed_source_cubic, &q0, &q1);
        let chord_framed: [BigInt; 3] = std::array::from_fn(|i| {
            &res_framed[2] * &q0.coordinates[i] - &res_framed[1] * &q1.coordinates[i]
        });
        let mapped_back = mat_vec_mod_p(&frame.matrix_to_source, &chord_framed, &p);
        assert_eq!(
            canonical_projective_mod_p(&mapped_back, &p).unwrap(),
            chord_src_mod
        );
    }

    #[test]
    fn jksst_projective_lll_point_lift_reduces_coordinate_height_to_two_thirds_exponent() {
        let p = BigInt::from(268_435_399i64); // 28-bit prime (p = 3 mod 4)
        let pt = [
            BigInt::from(193_847_261i64),
            BigInt::from(118_273_645i64),
            BigInt::from(1),
        ];
        let lifted = lift_projective_point_lll(&pt, &p).unwrap();
        assert_eq!(
            canonical_projective_mod_p(&lifted.coordinates, &p).unwrap(),
            canonical_projective_mod_p(&pt, &p).unwrap()
        );
        let max_bits = lifted.coordinates.iter().map(abs_bits).max().unwrap();
        // Minkowski on covolume p^2 in Z^3 bounds the shortest vector near p^(2/3) (~19 bits),
        // well below the 27-bit affine balanced coordinate floor.
        assert!(
            max_bits <= 20,
            "expected <= 20-bit coordinates, got {max_bits}"
        );
    }

    #[test]
    fn jksst_frame_and_homogeneous_congruence_halves_r9_cubic_height() {
        // Deterministic 9-point set on y^2 = x^3 + 3x + 5 over F_65519 (p = 3 mod 4).
        let p = BigInt::from(65_519i64);
        let exp = (&p + 1i64) >> 2;
        let mut pts = Vec::new();
        let mut x = 14_231i64;
        while pts.len() < 9 {
            let bx = BigInt::from(x);
            let rhs = mod_pos(&(&bx * &bx * &bx + 3i64 * &bx + 5i64), &p);
            let y = rhs.modpow(&exp, &p);
            if mod_pos(&(&y * &y), &p) == rhs && !y.is_zero() {
                pts.push([bx, y, BigInt::from(1)]);
            }
            x = (x + 29_989) % 65_519;
        }
        let source_cubic = bi(&[1, 0, 0, 0, 0, 0, -1, 3, 0, 5]);

        // Naive Z=1 balanced r=9 kernel representative.
        let naive_rows: Vec<Vec<BigInt>> = pts
            .iter()
            .map(|pt| {
                let bx = balanced_residue(&pt[0], &p);
                let by = balanced_residue(&pt[1], &p);
                plane_cubic_incidence_row(&bx, &by, &BigInt::from(1))
            })
            .collect();
        let naive_kernel = integer_kernel_basis(&naive_rows, PLANE_CUBIC_COEFFICIENTS).unwrap();
        assert_eq!(naive_kernel.len(), 1);
        let naive_score =
            score_plane_cubic_lift(&primitivize_cubic(naive_kernel[0].clone())).unwrap();

        let problem = JksstPlaneCubicProblem {
            modulus: p.clone(),
            source_coefficients: source_cubic,
            source_points: pts,
            frame_indices: None,
            point_lift_mode: JksstPointLiftMode::ProjectiveLll,
            max_frames: 32,
            reject_collinear_lifts: true,
        };
        let jksst = optimize_jksst_plane_cubic_lift(
            &problem,
            LiftSearchOptions {
                neighborhood_radius: 1,
                max_candidates: 64,
            },
        )
        .unwrap();
        assert!(jksst.incidence_preserved);
        assert!(jksst.projective_congruence_preserved);
        assert!(jksst.optimized_score.nonsingular);
        assert!(jksst.pre_lift_collinear_triples.is_empty());
        assert!(
            jksst.optimized_score.coefficient_height_bits * 2 < naive_score.coefficient_height_bits,
            "expected >2x bit reduction: jksst={} vs naive={}",
            jksst.optimized_score.coefficient_height_bits,
            naive_score.coefficient_height_bits
        );
    }
}
