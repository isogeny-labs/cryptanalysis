//! Exact JKSST plane-cubic geometry, Fisher ternary discriminant, rational
//! chord-origin group law, `PGL_3(F_p)` frame normalization, 3D-LLL point
//! lifting, collinearity filtering, and multi-prime modular relation-kernel LLL.

use std::collections::{HashMap, HashSet};

use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::{One, Signed, ToPrimitive, Zero};
use serde::{Deserialize, Serialize};

use crate::field_ec::{mod_inv_u64, mod_mul_u64};
use crate::linalg_lll::{
    abs_bits, determinant_bareiss, dot_bigint, intersect_full_rank_lattices, lll_reduce_hp,
    mod_inv_bigint, primitivize_vec, row_hermite_basis, subspace_congruence_sublattice,
};

/// Homogeneous plane cubic monomial count in JKSST order:
/// `(X^3, X^2Y, XY^2, Y^3, X^2Z, XYZ, Y^2Z, XZ^2, YZ^2, Z^3)`.
pub const PLANE_CUBIC_COEFFICIENTS: usize = 10;

pub const CUBIC_EXPONENTS: [(usize, usize, usize); PLANE_CUBIC_COEFFICIENTS] = [
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

const AUX_PRIMES: &[u64] = &[
    257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349, 353, 359, 367,
    373, 379, 383, 389, 397, 401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479,
    487, 491, 499, 503, 509, 521, 523, 541,
];

const SCREEN_PRIMES: &[u64] = &[547, 557, 563, 569, 571, 577, 587, 593, 599, 601, 607, 613];

/// Primitive integer projective point in `P^2(Q)`.
#[derive(Clone, Debug, Eq, PartialEq, Hash)]
pub struct PlaneCubicPoint {
    pub coordinates: [BigInt; 3],
}

impl PlaneCubicPoint {
    pub fn new(mut coordinates: [BigInt; 3]) -> Result<Self, String> {
        if coordinates.iter().all(BigInt::is_zero) {
            return Err("projective point (0,0,0) is invalid".into());
        }
        let g = coordinates.iter().fold(BigInt::zero(), |acc, x| acc.gcd(x));
        for c in &mut coordinates {
            *c /= &g;
        }
        if coordinates
            .iter()
            .find(|c| !c.is_zero())
            .is_some_and(Signed::is_negative)
        {
            for c in &mut coordinates {
                *c = -&*c;
            }
        }
        Ok(Self { coordinates })
    }

    pub fn max_coord_bits(&self) -> u64 {
        self.coordinates.iter().map(abs_bits).max().unwrap_or(0)
    }

    pub fn weil_height_ln(&self) -> f64 {
        let max_mag = self
            .coordinates
            .iter()
            .map(|c| c.magnitude())
            .max()
            .unwrap();
        bigint_ln(max_mag)
    }
}

/// Natural logarithm of a positive `BigUint`/`BigInt` magnitude accurate to `f64` precision.
pub fn bigint_ln(x: &num_bigint::BigUint) -> f64 {
    if x.is_zero() {
        return f64::NEG_INFINITY;
    }
    let bits = x.bits();
    if bits <= 53 {
        return (x.to_u64().unwrap_or(1) as f64).ln();
    }
    let shift = bits - 53;
    let top = (x >> shift).to_u64().unwrap_or(1u64 << 52) as f64;
    top.ln() + (shift as f64) * std::f64::consts::LN_2
}

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

pub fn plane_cubic_value(c: &[BigInt], point: &PlaneCubicPoint) -> BigInt {
    let [x, y, z] = &point.coordinates;
    dot_bigint(&plane_cubic_incidence_row(x, y, z), c)
}

pub fn plane_cubic_gradient(c: &[BigInt], point: &PlaneCubicPoint) -> [BigInt; 3] {
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
    if determinant.iter().any(|coef| !coef.is_multiple_of(&two)) {
        return Err("internal error: nonintegral ternary-cubic Hessian".into());
    }
    Ok(determinant.into_iter().map(|coef| -coef / &two).collect())
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

/// Exact Fisher ternary-cubic discriminant (`+/- 1728 Delta`).
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

fn multiply_binary_forms(a: &[BigInt], b: &[BigInt]) -> Vec<BigInt> {
    let mut product = vec![BigInt::zero(); a.len() + b.len() - 1];
    for (i, x) in a.iter().enumerate() {
        for (j, y) in b.iter().enumerate() {
            product[i + j] += x * y;
        }
    }
    product
}

pub fn binary_cubic_restriction(
    c: &[BigInt],
    p: &PlaneCubicPoint,
    q: &PlaneCubicPoint,
) -> [BigInt; 4] {
    let mut result = std::array::from_fn(|_| BigInt::zero());
    for (coefficient, (ex, ey, ez)) in c.iter().zip(CUBIC_EXPONENTS) {
        let mut term = vec![BigInt::one()];
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

pub fn projective_cross_nonzero(p: &PlaneCubicPoint, q: &PlaneCubicPoint) -> bool {
    let [px, py, pz] = &p.coordinates;
    let [qx, qy, qz] = &q.coordinates;
    !(py * qz - pz * qy).is_zero()
        || !(pz * qx - px * qz).is_zero()
        || !(px * qy - py * qx).is_zero()
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

/// Exact group law on a smooth plane cubic over `Q` with any rational origin.
#[derive(Clone, Debug)]
pub struct PlaneCubicGroup {
    coefficients: Vec<BigInt>,
    origin: PlaneCubicPoint,
}

impl PlaneCubicGroup {
    pub fn new(coefficients: Vec<BigInt>, origin: PlaneCubicPoint) -> Result<Self, String> {
        if coefficients.len() != PLANE_CUBIC_COEFFICIENTS {
            return Err("invalid cubic length".into());
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

    pub fn coefficients(&self) -> &[BigInt] {
        &self.coefficients
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
        Err("failed to parameterize tangent line".into())
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
            return combine_projective(&restriction[2], p, &(-&restriction[1]), q);
        }
        let auxiliary = self.tangent_auxiliary(p)?;
        let restriction = binary_cubic_restriction(&self.coefficients, p, &auxiliary);
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
        let mut s = scalar.clone();
        let mut addend = point.clone();
        if s.is_negative() {
            s = -s;
            addend = self.negate(&addend)?;
        }
        let mut result = self.origin.clone();
        while !s.is_zero() {
            if s.is_odd() {
                result = self.add(&result, &addend)?;
            }
            s >>= 1;
            if !s.is_zero() {
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
            return Err("relation scalars and points length mismatch".into());
        }
        let mut sum = self.origin.clone();
        for (scalar, point) in scalars.iter().zip(points) {
            if scalar.is_zero() {
                continue;
            }
            sum = self.add(&sum, &self.scalar_mul(scalar, point)?)?;
        }
        Ok(sum)
    }
}

pub fn det3_coords(a: &[BigInt; 3], b: &[BigInt; 3], c: &[BigInt; 3]) -> BigInt {
    &a[0] * (&b[1] * &c[2] - &b[2] * &c[1]) - &a[1] * (&b[0] * &c[2] - &b[2] * &c[0])
        + &a[2] * (&b[0] * &c[1] - &b[1] * &c[0])
}

pub fn collinear_point_triples(points: &[PlaneCubicPoint]) -> Vec<[usize; 3]> {
    let mut triples = Vec::new();
    for i in 0..points.len() {
        for j in (i + 1)..points.len() {
            for k in (j + 1)..points.len() {
                if det3_coords(
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

pub fn canonical_projective_mod_p(
    point: &[BigInt; 3],
    modulus: &BigInt,
) -> Result<[BigInt; 3], String> {
    let reduced: [BigInt; 3] = std::array::from_fn(|i| point[i].mod_floor(modulus));
    let Some(pivot) = reduced.iter().position(|x| !x.is_zero()) else {
        return Err("projective point reduces to (0,0,0) mod p".into());
    };
    let inv = mod_inv_bigint(&reduced[pivot], modulus)?;
    Ok(std::array::from_fn(|i| {
        (&reduced[i] * &inv).mod_floor(modulus)
    }))
}

pub fn mat_vec_mod_p(mat: &[[BigInt; 3]; 3], vec: &[BigInt; 3], modulus: &BigInt) -> [BigInt; 3] {
    std::array::from_fn(|r| {
        (&mat[r][0] * &vec[0] + &mat[r][1] * &vec[1] + &mat[r][2] * &vec[2]).mod_floor(modulus)
    })
}

pub fn invert_3x3_mod_p(mat: &[[BigInt; 3]; 3], modulus: &BigInt) -> Option<[[BigInt; 3]; 3]> {
    let det = det3_coords(&mat[0], &mat[1], &mat[2]).mod_floor(modulus);
    let det_inv = mod_inv_bigint(&det, modulus).ok()?;
    let cofactor = |r: usize, c: usize| -> BigInt {
        let r1 = (r + 1) % 3;
        let r2 = (r + 2) % 3;
        let c1 = (c + 1) % 3;
        let c2 = (c + 2) % 3;
        (&mat[r1][c1] * &mat[r2][c2] - &mat[r1][c2] * &mat[r2][c1]).mod_floor(modulus)
    };
    Some(std::array::from_fn(|r| {
        std::array::from_fn(|c| (cofactor(c, r) * &det_inv).mod_floor(modulus))
    }))
}

pub fn pullback_plane_cubic_mod_p(
    source_cubic: &[BigInt],
    matrix_to_source: &[[BigInt; 3]; 3],
    modulus: &BigInt,
) -> Result<Vec<BigInt>, String> {
    if source_cubic.len() != PLANE_CUBIC_COEFFICIENTS {
        return Err("expected 10 cubic coefficients".into());
    }
    // Expand (M * [X, Y, Z]^T) into ternary cubic monomials via exact 3-way linear-form products.
    let lin: [Vec<BigInt>; 3] = std::array::from_fn(|r| {
        vec![
            matrix_to_source[r][0].clone(),
            matrix_to_source[r][1].clone(),
            matrix_to_source[r][2].clone(),
        ]
    });
    let mut out = vec![BigInt::zero(); PLANE_CUBIC_COEFFICIENTS];
    for (coef, (ex, ey, ez)) in source_cubic.iter().zip(CUBIC_EXPONENTS) {
        if coef.mod_floor(modulus).is_zero() {
            continue;
        }
        let mut factors: Vec<&[BigInt]> = Vec::with_capacity(3);
        for _ in 0..ex {
            factors.push(&lin[0]);
        }
        for _ in 0..ey {
            factors.push(&lin[1]);
        }
        for _ in 0..ez {
            factors.push(&lin[2]);
        }
        let quad = multiply_linear_forms(factors[0], factors[1]);
        let cub = multiply_quadratic_linear(&quad, factors[2]);
        for (slot, term) in out.iter_mut().zip(cub) {
            *slot = (&*slot + coef * term).mod_floor(modulus);
        }
    }
    Ok(out)
}

/// Certified `PGL_3(F_p)` frame mapping `(1:0:0), (0:1:0), (0:0:1), (1:1:1)`
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

pub fn jksst_projective_frame_mod_p(
    modulus: &BigInt,
    source_coefficients: &[BigInt],
    source_points: &[[BigInt; 3]],
    frame_indices: [usize; 4],
) -> Result<JksstProjectiveFrame, String> {
    if source_points.len() < 4 {
        return Err("need at least 4 source points for a projective frame".into());
    }
    let canonical_pts: Vec<[BigInt; 3]> = source_points
        .iter()
        .map(|pt| canonical_projective_mod_p(pt, modulus))
        .collect::<Result<_, _>>()?;
    for pt in &canonical_pts {
        let val = dot_bigint(
            &plane_cubic_incidence_row(&pt[0], &pt[1], &pt[2]),
            source_coefficients,
        );
        if !val.mod_floor(modulus).is_zero() {
            return Err("source point is not on the source cubic modulo p".into());
        }
    }
    let base_cols: [[BigInt; 3]; 3] = std::array::from_fn(|r| {
        std::array::from_fn(|c| canonical_pts[frame_indices[c]][r].clone())
    });
    let Some(base_inv) = invert_3x3_mod_p(&base_cols, modulus) else {
        return Err("first three frame points are collinear modulo p".into());
    };
    let scales = mat_vec_mod_p(&base_inv, &canonical_pts[frame_indices[3]], modulus);
    if scales.iter().any(|s| s.is_zero()) {
        return Err("fourth frame point is collinear with two frame vertices modulo p".into());
    }
    let matrix_to_source: [[BigInt; 3]; 3] = std::array::from_fn(|r| {
        std::array::from_fn(|c| (&base_cols[r][c] * &scales[c]).mod_floor(modulus))
    });
    let Some(matrix_from_source) = invert_3x3_mod_p(&matrix_to_source, modulus) else {
        return Err("frame matrix not invertible modulo p".into());
    };
    let transformed_points_mod_p: Vec<[BigInt; 3]> = canonical_pts
        .iter()
        .map(|pt| {
            canonical_projective_mod_p(&mat_vec_mod_p(&matrix_from_source, pt, modulus), modulus)
        })
        .collect::<Result<_, _>>()?;
    let transformed_source_cubic =
        pullback_plane_cubic_mod_p(source_coefficients, &matrix_to_source, modulus)?;

    Ok(JksstProjectiveFrame {
        modulus: modulus.clone(),
        frame_indices,
        matrix_to_source,
        matrix_from_source,
        transformed_source_cubic,
        transformed_points_mod_p,
    })
}

pub fn balanced_residue(value: &BigInt, modulus: &BigInt) -> BigInt {
    let r = value.mod_floor(modulus);
    let half = modulus >> 1;
    if r > half {
        r - modulus
    } else {
        r
    }
}

/// 3D-LLL shortest primitive projective ray lift (`O(p^(2/3))` coordinates).
pub fn lift_projective_point_lll(
    point_mod_p: &[BigInt; 3],
    modulus: &BigInt,
) -> Result<PlaneCubicPoint, String> {
    lift_projective_point_weighted_lll(point_mod_p, modulus, [1, 1, 1])
}

/// Weighted 3D-LLL projective ray lift minimizing `sum_k (w_k v_k)^2` on the ray lattice.
pub fn lift_projective_point_weighted_lll(
    point_mod_p: &[BigInt; 3],
    modulus: &BigInt,
    weights: [i64; 3],
) -> Result<PlaneCubicPoint, String> {
    let canon = canonical_projective_mod_p(point_mod_p, modulus)?;
    let pivot = canon
        .iter()
        .position(|x| x == &BigInt::one())
        .ok_or_else(|| "canonical projective point lacks unit pivot".to_string())?;
    let mut basis = Vec::with_capacity(3);
    basis.push(vec![
        balanced_residue(&canon[0], modulus) * weights[0],
        balanced_residue(&canon[1], modulus) * weights[1],
        balanced_residue(&canon[2], modulus) * weights[2],
    ]);
    for j in 0..3 {
        if j != pivot {
            let mut row = vec![BigInt::zero(); 3];
            row[j] = modulus * weights[j];
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
                let scaled: [BigInt; 3] = std::array::from_fn(|k| {
                    &basis[0][k] * c0 + &basis[1][k] * c1 + &basis[2][k] * c2
                });
                let unscaled: [BigInt; 3] =
                    std::array::from_fn(|k| &scaled[k] / BigInt::from(weights[k]));
                if unscaled.iter().all(|x| x.mod_floor(modulus).is_zero()) {
                    continue;
                }
                let prim = PlaneCubicPoint::new(unscaled)?;
                let norm2: BigInt = prim.coordinates.iter().map(|x| x * x).sum();
                let replace = match &best {
                    None => true,
                    Some((bn, bc)) => (&norm2, &prim.coordinates) < (bn, bc),
                };
                if replace {
                    best = Some((norm2, prim.coordinates));
                }
            }
        }
    }
    let (_, chosen) = best.ok_or_else(|| "no valid 3D-LLL preimage found".to_string())?;
    if canonical_projective_mod_p(&chosen, modulus)? != canon {
        return Err("internal error: 3D-LLL lift altered projective class mod p".into());
    }
    PlaneCubicPoint::new(chosen)
}

pub fn lift_projective_point_affine_balanced(
    point_mod_p: &[BigInt; 3],
    modulus: &BigInt,
) -> Result<PlaneCubicPoint, String> {
    let canon = canonical_projective_mod_p(point_mod_p, modulus)?;
    if canon[2].is_zero() {
        return lift_projective_point_lll(&canon, modulus);
    }
    let z_inv = mod_inv_bigint(&canon[2], modulus)?;
    let x = balanced_residue(&(&canon[0] * &z_inv), modulus);
    let y = balanced_residue(&(&canon[1] * &z_inv), modulus);
    PlaneCubicPoint::new([x, y, BigInt::one()])
}

/// Homogeneous congruence sublattice `{c in span_Z(kernel_basis) : exists mu, c = mu * target (mod p)}`.
pub fn homogeneous_congruence_sublattice(
    kernel_basis: &[Vec<BigInt>],
    target_cubic_mod_p: &[BigInt],
    modulus: &BigInt,
) -> Result<Vec<Vec<BigInt>>, String> {
    let (sub, has_nz) =
        subspace_congruence_sublattice(kernel_basis, &[target_cubic_mod_p.to_vec()], modulus)?;
    if !has_nz {
        return Err("kernel contains no projective preimage of source cubic mod p".into());
    }
    Ok(sub)
}

/// Select the shortest nonsingular congruent cubic from an LLL-reduced congruence lattice.
pub fn select_best_cubic_from_sublattice(
    mut sublattice: Vec<Vec<BigInt>>,
    target_cubic_mod_p: &[BigInt],
    modulus: &BigInt,
    radius: i64,
) -> Result<Vec<BigInt>, String> {
    lll_reduce_hp(&mut sublattice, 0.99).map_err(str::to_string)?;
    let d = sublattice.len();
    let mut best: Option<(u64, u64, BigInt, Vec<BigInt>)> = None;

    let mut eval_cand = |raw: Vec<BigInt>| -> Result<(), String> {
        let prim = primitivize_vec(raw);
        if prim.iter().all(|x| x.mod_floor(modulus).is_zero()) {
            return Ok(());
        }
        // Check projective proportionality to target_cubic_mod_p.
        let Some(piv) = target_cubic_mod_p
            .iter()
            .position(|x| !x.mod_floor(modulus).is_zero())
        else {
            return Ok(());
        };
        let Ok(t_inv) = mod_inv_bigint(&target_cubic_mod_p[piv], modulus) else {
            return Ok(());
        };
        let scale = (&prim[piv] * t_inv).mod_floor(modulus);
        if scale.is_zero()
            || prim
                .iter()
                .zip(target_cubic_mod_p)
                .any(|(c, t)| !(c - &scale * t).mod_floor(modulus).is_zero())
        {
            return Ok(());
        }
        let disc = plane_cubic_discriminant(&prim)?;
        if disc.is_zero() {
            return Ok(());
        }
        let dbits = abs_bits(&disc);
        let cbits = prim.iter().map(abs_bits).max().unwrap_or(0);
        let l2: BigInt = prim.iter().map(|x| x * x).sum();
        let replace = match &best {
            None => true,
            Some((bd, bc, bl2, _)) => (&dbits, &cbits, &l2) < (bd, bc, bl2),
        };
        if replace {
            best = Some((dbits, cbits, l2, prim));
        }
        Ok(())
    };

    for row in &sublattice {
        eval_cand(row.clone())?;
    }
    if d >= 2 {
        for a in -radius..=radius {
            for b in -radius..=radius {
                if a == 0 && b == 0 {
                    continue;
                }
                let mut v = vec![BigInt::zero(); PLANE_CUBIC_COEFFICIENTS];
                for k in 0..PLANE_CUBIC_COEFFICIENTS {
                    v[k] = &sublattice[0][k] * a + &sublattice[1][k] * b;
                }
                eval_cand(v)?;
                if d >= 3 && a.abs() <= 1 && b.abs() <= 1 {
                    for c in [-1i64, 1] {
                        let mut v3 = vec![BigInt::zero(); PLANE_CUBIC_COEFFICIENTS];
                        for k in 0..PLANE_CUBIC_COEFFICIENTS {
                            v3[k] = &sublattice[0][k] * a
                                + &sublattice[1][k] * b
                                + &sublattice[2][k] * c;
                        }
                        eval_cand(v3)?;
                    }
                }
            }
        }
    }

    best.map(|(_, _, _, v)| v)
        .ok_or_else(|| "no nonsingular congruent plane cubic found in sublattice".into())
}

pub fn transport_to_fixed_flex(scalars: &[i64], origin_pair: [usize; 2]) -> Vec<i64> {
    let s: i64 = scalars.iter().sum();
    let mut fixed = scalars.to_vec();
    fixed[origin_pair[0]] += s;
    fixed[origin_pair[1]] += s;
    fixed
}

pub fn is_collinear_relation_alias(
    scalars: &[i64],
    origin_pair: [usize; 2],
    points: &[PlaneCubicPoint],
) -> bool {
    let fixed = transport_to_fixed_flex(scalars, origin_pair);
    let supp: Vec<usize> = fixed
        .iter()
        .enumerate()
        .filter_map(|(idx, &v)| (v != 0).then_some(idx))
        .collect();
    if supp.len() != 3 {
        return false;
    }
    let v0 = fixed[supp[0]];
    if v0.abs() != 1 || fixed[supp[1]] != v0 || fixed[supp[2]] != v0 {
        return false;
    }
    det3_coords(
        &points[supp[0]].coordinates,
        &points[supp[1]].coordinates,
        &points[supp[2]].coordinates,
    )
    .is_zero()
}

/// Detect whether a relation on a 9-point Cayley-Bacharach tuple is the
/// automatic hyperplane-section relation `P_1 + ... + P_9 ~ 3H ~ 3(P_u + P_v + O)`,
/// whose fixed-flex divisor vector `fixed = n + (sum n)(e_u + e_v)` is `+/- (1,1,1,1,1,1,1,1,1)`
/// modulo adding multiples of collinear triples (specifically `fixed == [1; 9]` or `[-1; 9]`).
pub fn is_cayley_bacharach_hyperplane_tautology(scalars: &[i64], origin_pair: [usize; 2]) -> bool {
    if scalars.len() != 9 {
        return false;
    }
    let fixed = transport_to_fixed_flex(scalars, origin_pair);
    fixed.iter().all(|&x| x == 1) || fixed.iter().all(|&x| x == -1)
}

/// Choose the chord pair `(i, j)` avoiding `avoid` that minimizes `||O||_2^2`.
pub fn choose_best_chord_pair(
    coeffs: &[BigInt],
    pts: &[PlaneCubicPoint],
    avoid: Option<usize>,
) -> Option<[usize; 2]> {
    let mut best: Option<(BigInt, [usize; 2])> = None;
    for i in 0..pts.len() {
        if avoid == Some(i) {
            continue;
        }
        for j in (i + 1)..pts.len() {
            if avoid == Some(j) {
                continue;
            }
            if let Ok(grp) = PlaneCubicGroup::with_chord_origin(coeffs.to_vec(), &pts[i], &pts[j]) {
                let norm2: BigInt = grp.origin().coordinates.iter().map(|x| x * x).sum();
                let replace = match &best {
                    None => true,
                    Some((bn, _)) => &norm2 < bn,
                };
                if replace {
                    best = Some((norm2, [i, j]));
                }
            }
        }
    }
    best.map(|(_, pair)| pair)
}

#[derive(Clone, Debug)]
struct ModPlaneCubic {
    q: u64,
    c: [u64; PLANE_CUBIC_COEFFICIENTS],
    origin: [u64; 3],
}

#[inline]
fn mod_pos_u64(v: i128, q: u64) -> u64 {
    v.rem_euclid(q as i128) as u64
}

impl ModPlaneCubic {
    fn from_global(coefficients: &[BigInt], origin: &PlaneCubicPoint, q: u64) -> Option<Self> {
        let q_big = BigInt::from(q);
        let mut c = [0u64; PLANE_CUBIC_COEFFICIENTS];
        for (slot, val) in c.iter_mut().zip(coefficients) {
            *slot = val.mod_floor(&q_big).to_u64()?;
        }
        let origin_mod = Self::canon_point_big(&origin.coordinates, q)?;
        let model = Self {
            q,
            c,
            origin: origin_mod,
        };
        if !model.is_nonsingular_point(origin_mod) {
            return None;
        }
        Some(model)
    }

    fn canon_point_big(coords: &[BigInt; 3], q: u64) -> Option<[u64; 3]> {
        let q_big = BigInt::from(q);
        let raw = [
            coords[0].mod_floor(&q_big).to_u64()?,
            coords[1].mod_floor(&q_big).to_u64()?,
            coords[2].mod_floor(&q_big).to_u64()?,
        ];
        Self::canon_point(raw, q)
    }

    fn canon_point(raw: [u64; 3], q: u64) -> Option<[u64; 3]> {
        let r = [raw[0] % q, raw[1] % q, raw[2] % q];
        let piv = r.iter().position(|&x| x != 0)?;
        let inv = mod_inv_u64(r[piv], q)?;
        Some([
            mod_mul_u64(r[0], inv, q),
            mod_mul_u64(r[1], inv, q),
            mod_mul_u64(r[2], inv, q),
        ])
    }

    fn eval(&self, p: [u64; 3]) -> u64 {
        let q128 = self.q as u128;
        let c = &self.c;
        let (x, y, z) = (p[0] as u128, p[1] as u128, p[2] as u128);
        let x2 = (x * x) % q128;
        let y2 = (y * y) % q128;
        let z2 = (z * z) % q128;
        let terms = [
            (x2 * x) % q128,
            (x2 * y) % q128,
            (x * y2) % q128,
            (y2 * y) % q128,
            (x2 * z) % q128,
            (((x * y) % q128) * z) % q128,
            (y2 * z) % q128,
            (x * z2) % q128,
            (y * z2) % q128,
            (z2 * z) % q128,
        ];
        let mut sum = 0u128;
        for (&ci, &ti) in c.iter().zip(&terms) {
            sum = (sum + (ci as u128) * ti) % q128;
        }
        sum as u64
    }

    fn gradient(&self, p: [u64; 3]) -> [u64; 3] {
        let (q128, c) = (self.q as u128, &self.c);
        let (x, y, z) = (p[0] as u128, p[1] as u128, p[2] as u128);
        let x2 = (x * x) % q128;
        let y2 = (y * y) % q128;
        let z2 = (z * z) % q128;
        let xy = (x * y) % q128;
        let xz = (x * z) % q128;
        let yz = (y * z) % q128;
        let gx = (3 * (c[0] as u128) * x2
            + 2 * (c[1] as u128) * xy
            + (c[2] as u128) * y2
            + 2 * (c[4] as u128) * xz
            + (c[5] as u128) * yz
            + (c[7] as u128) * z2)
            % q128;
        let gy = ((c[1] as u128) * x2
            + 2 * (c[2] as u128) * xy
            + 3 * (c[3] as u128) * y2
            + (c[5] as u128) * xz
            + 2 * (c[6] as u128) * yz
            + (c[8] as u128) * z2)
            % q128;
        let gz = ((c[4] as u128) * x2
            + (c[5] as u128) * xy
            + (c[6] as u128) * y2
            + 2 * (c[7] as u128) * xz
            + 2 * (c[8] as u128) * yz
            + 3 * (c[9] as u128) * z2)
            % q128;
        [gx as u64, gy as u64, gz as u64]
    }

    fn is_nonsingular_point(&self, p: [u64; 3]) -> bool {
        self.eval(p) == 0 && self.gradient(p) != [0, 0, 0]
    }

    fn b1(&self, p: [u64; 3], r: [u64; 3]) -> u64 {
        let q128 = self.q as u128;
        let c = &self.c;
        let (px, py, pz) = (p[0] as u128, p[1] as u128, p[2] as u128);
        let (rx, ry, rz) = (r[0] as u128, r[1] as u128, r[2] as u128);
        let px2 = (px * px) % q128;
        let py2 = (py * py) % q128;
        let pz2 = (pz * pz) % q128;
        let terms = [
            (3 * px2 % q128) * rx % q128,
            (2 * ((px * rx) % q128) * py + px2 * ry) % q128,
            (rx * py2 + 2 * ((px * py) % q128) * ry) % q128,
            (3 * py2 % q128) * ry % q128,
            (2 * ((px * rx) % q128) * pz + px2 * rz) % q128,
            (((rx * py) % q128) * pz + ((px * ry) % q128) * pz + ((px * py) % q128) * rz) % q128,
            (2 * ((py * ry) % q128) * pz + py2 * rz) % q128,
            (rx * pz2 + 2 * ((px * pz) % q128) * rz) % q128,
            (ry * pz2 + 2 * ((py * pz) % q128) * rz) % q128,
            (3 * pz2 % q128) * rz % q128,
        ];
        let mut sum = 0u128;
        for (&ci, &ti) in c.iter().zip(&terms) {
            sum = (sum + (ci as u128) * ti) % q128;
        }
        sum as u64
    }

    fn cross_nonzero(&self, a: [u64; 3], b: [u64; 3]) -> bool {
        let q = self.q as i128;
        let c0 = (a[1] as i128 * b[2] as i128 - a[2] as i128 * b[1] as i128).rem_euclid(q);
        let c1 = (a[2] as i128 * b[0] as i128 - a[0] as i128 * b[2] as i128).rem_euclid(q);
        let c2 = (a[0] as i128 * b[1] as i128 - a[1] as i128 * b[0] as i128).rem_euclid(q);
        c0 != 0 || c1 != 0 || c2 != 0
    }

    fn third_intersection(&self, p: [u64; 3], r: [u64; 3]) -> Option<[u64; 3]> {
        let q = self.q;
        if p != r {
            let b1_val = self.b1(p, r) as i128;
            let b2_val = self.b1(r, p) as i128;
            let raw = [
                mod_pos_u64(b2_val * p[0] as i128 - b1_val * r[0] as i128, q),
                mod_pos_u64(b2_val * p[1] as i128 - b1_val * r[1] as i128, q),
                mod_pos_u64(b2_val * p[2] as i128 - b1_val * r[2] as i128, q),
            ];
            return Self::canon_point(raw, q);
        }
        let g = self.gradient(p);
        let cands = [
            [g[1], (q - g[0]) % q, 0],
            [g[2], 0, (q - g[0]) % q],
            [0, g[2], (q - g[1]) % q],
        ];
        for raw_aux in cands {
            if let Some(aux) = Self::canon_point(raw_aux, q) {
                if self.cross_nonzero(p, aux) {
                    let b2_val = self.b1(aux, p) as i128;
                    let b3_val = self.eval(aux) as i128;
                    let raw = [
                        mod_pos_u64(b3_val * p[0] as i128 - b2_val * aux[0] as i128, q),
                        mod_pos_u64(b3_val * p[1] as i128 - b2_val * aux[1] as i128, q),
                        mod_pos_u64(b3_val * p[2] as i128 - b2_val * aux[2] as i128, q),
                    ];
                    return Self::canon_point(raw, q);
                }
            }
        }
        None
    }

    fn add(&self, p: [u64; 3], r: [u64; 3]) -> Option<[u64; 3]> {
        let res = self.third_intersection(p, r)?;
        self.third_intersection(res, self.origin)
    }

    fn neg(&self, p: [u64; 3]) -> Option<[u64; 3]> {
        let tan_o = self.third_intersection(self.origin, self.origin)?;
        self.third_intersection(p, tan_o)
    }

    fn scalar_mul(&self, scalar: i64, p: [u64; 3], ops: &mut u64) -> Option<[u64; 3]> {
        if scalar == 0 {
            return Some(self.origin);
        }
        let mut addend = if scalar < 0 {
            *ops += 1;
            self.neg(p)?
        } else {
            p
        };
        let mut k = scalar.unsigned_abs();
        let mut acc = self.origin;
        while k > 0 {
            if k & 1 == 1 {
                acc = if acc == self.origin {
                    addend
                } else {
                    *ops += 1;
                    self.add(acc, addend)?
                };
            }
            k >>= 1;
            if k > 0 {
                *ops += 1;
                addend = self.add(addend, addend)?;
            }
        }
        Some(acc)
    }

    fn relation_is_origin(&self, scalars: &[i64], pts: &[[u64; 3]], ops: &mut u64) -> Option<bool> {
        let mut acc = self.origin;
        for (&s, &pt) in scalars.iter().zip(pts) {
            if s == 0 {
                continue;
            }
            let term = self.scalar_mul(s, pt, ops)?;
            acc = if acc == self.origin {
                term
            } else {
                *ops += 1;
                self.add(acc, term)?
            };
        }
        Some(acc == self.origin)
    }
}

fn single_prime_relation_kernel(
    curve: &ModPlaneCubic,
    points_mod_q: &[[u64; 3]],
    ops_counter: &mut u64,
) -> Option<(Vec<Vec<BigInt>>, u64)> {
    let r = points_mod_q.len();
    let max_order = curve.q + 1 + 2 * ((curve.q as f64).sqrt().ceil() as u64) + 4;
    let mut subgroup: Vec<[u64; 3]> = vec![curve.origin];
    let mut coords_of: HashMap<[u64; 3], Vec<BigInt>> = HashMap::new();
    coords_of.insert(curve.origin, vec![BigInt::zero(); r]);
    let mut kernel_rows: Vec<Vec<BigInt>> = Vec::with_capacity(r);

    for (k, &qk) in points_mod_q.iter().enumerate() {
        if !curve.is_nonsingular_point(qk) {
            return None;
        }
        let mut cur = qk;
        let mut m = 1u64;
        let mut multiples: Vec<[u64; 3]> = vec![curve.origin];
        while !coords_of.contains_key(&cur) {
            multiples.push(cur);
            cur = curve.add(cur, qk)?;
            *ops_counter += 1;
            m += 1;
            if m > max_order {
                return None;
            }
        }
        let c_vec = coords_of.get(&cur)?.clone();
        let mut rel = vec![BigInt::zero(); r];
        for i in 0..k {
            rel[i] = -&c_vec[i];
        }
        rel[k] = BigInt::from(m);
        kernel_rows.push(rel);

        if m > 1 {
            let prev_elements = subgroup.clone();
            for (t, &t_pt) in multiples.iter().enumerate().take(m as usize).skip(1) {
                let t_big = BigInt::from(t);
                for &base_pt in &prev_elements {
                    let sum_pt = if base_pt == curve.origin {
                        t_pt
                    } else {
                        *ops_counter += 1;
                        curve.add(base_pt, t_pt)?
                    };
                    if !coords_of.contains_key(&sum_pt) {
                        let mut rep = coords_of[&base_pt].clone();
                        rep[k] = t_big.clone();
                        coords_of.insert(sum_pt, rep);
                        subgroup.push(sum_pt);
                    }
                }
            }
        }
    }
    Some((kernel_rows, subgroup.len() as u64))
}

fn canonicalize_relation_sign(mut v: Vec<i64>) -> Option<Vec<i64>> {
    let mut g = 0i64;
    for &x in &v {
        g = g.gcd(&x.abs());
    }
    if g == 0 {
        return None;
    }
    if g > 1 {
        for x in &mut v {
            *x /= g;
        }
    }
    let first_nz = *v.iter().find(|&&x| x != 0)?;
    if first_nz < 0 {
        for x in &mut v {
            *x = -*x;
        }
    }
    Some(v)
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct CertifiedPlaneCubicRelation {
    pub scalars: Vec<i64>,
    pub fixed_flex_scalars: Vec<i64>,
    pub is_collinear_alias: bool,
    pub is_cb_hyperplane_tautology: bool,
    pub l1_norm: u64,
    pub linf_norm: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ModularKernelRelationSearch {
    pub aux_primes_used: Vec<u64>,
    pub aux_curve_group_ops: u64,
    pub rational_cert_checks: u64,
    pub certified_relations: Vec<CertifiedPlaneCubicRelation>,
}

/// Extract exact global Mordell-Weil relations on `(C, O)` via multi-prime
/// subgroup-kernel HNF intersection + LLL + 4-prime screen + exact `Q` check.
pub fn find_relations_modular_kernel_lll(
    coefficients: &[BigInt],
    points: &[PlaneCubicPoint],
    origin_pair: [usize; 2],
    num_aux_primes: usize,
    max_coeff_abs: i64,
    max_exact_checks: usize,
) -> Result<ModularKernelRelationSearch, String> {
    let r = points.len();
    if r < 2 {
        return Err("need at least 2 points for relation search".into());
    }
    let disc = plane_cubic_discriminant(coefficients)?;
    if disc.is_zero() {
        return Err("plane cubic is singular".into());
    }
    let group = PlaneCubicGroup::with_chord_origin(
        coefficients.to_vec(),
        &points[origin_pair[0]],
        &points[origin_pair[1]],
    )?;

    let mut used_primes = Vec::with_capacity(num_aux_primes);
    let mut aux_ops = 0u64;
    let mut lattice: Option<Vec<Vec<BigInt>>> = None;

    for &q in AUX_PRIMES {
        if used_primes.len() >= num_aux_primes {
            break;
        }
        if disc.mod_floor(&BigInt::from(q)).is_zero() {
            continue;
        }
        let Some(mod_cubic) = ModPlaneCubic::from_global(coefficients, group.origin(), q) else {
            continue;
        };
        let Some(pts_q): Option<Vec<[u64; 3]>> = points
            .iter()
            .map(|pt| ModPlaneCubic::canon_point_big(&pt.coordinates, q))
            .collect()
        else {
            continue;
        };
        let Some((kern_q, _)) = single_prime_relation_kernel(&mod_cubic, &pts_q, &mut aux_ops)
        else {
            continue;
        };
        lattice = Some(match lattice {
            None => row_hermite_basis(kern_q, r),
            Some(prev) => intersect_full_rank_lattices(&prev, &kern_q, r)?,
        });
        used_primes.push(q);
    }

    let Some(mut basis) = lattice else {
        return Err("failed to find good auxiliary primes".into());
    };
    lll_reduce_hp(&mut basis, 0.99).map_err(str::to_string)?;

    let mut candidates: Vec<Vec<i64>> = Vec::new();
    let mut seen: HashSet<Vec<i64>> = HashSet::new();
    let mut push_cand = |raw: Vec<BigInt>| {
        if let Some(i64_vec) = raw
            .iter()
            .map(ToPrimitive::to_i64)
            .collect::<Option<Vec<_>>>()
        {
            if let Some(canon) = canonicalize_relation_sign(i64_vec) {
                if canon.iter().all(|&x| x.abs() <= max_coeff_abs) && seen.insert(canon.clone()) {
                    candidates.push(canon);
                }
            }
        }
    };

    for row in &basis {
        push_cand(row.clone());
    }
    for i in 0..basis.len() {
        for j in (i + 1)..basis.len() {
            let sum: Vec<BigInt> = basis[i].iter().zip(&basis[j]).map(|(a, b)| a + b).collect();
            let diff: Vec<BigInt> = basis[i].iter().zip(&basis[j]).map(|(a, b)| a - b).collect();
            push_cand(sum);
            push_cand(diff);
        }
    }

    candidates.sort_by_key(|cand| {
        let cb_taut = usize::from(is_cayley_bacharach_hyperplane_tautology(cand, origin_pair));
        let col = usize::from(is_collinear_relation_alias(cand, origin_pair, points));
        let l1: u64 = cand.iter().map(|x| x.unsigned_abs()).sum();
        (cb_taut, col, l1, cand.clone())
    });

    let mut screens: Vec<(ModPlaneCubic, Vec<[u64; 3]>)> = Vec::with_capacity(4);
    for &q_scr in SCREEN_PRIMES {
        if screens.len() >= 4 {
            break;
        }
        if disc.mod_floor(&BigInt::from(q_scr)).is_zero() {
            continue;
        }
        let Some(mc) = ModPlaneCubic::from_global(coefficients, group.origin(), q_scr) else {
            continue;
        };
        let Some(pq): Option<Vec<[u64; 3]>> = points
            .iter()
            .map(|pt| ModPlaneCubic::canon_point_big(&pt.coordinates, q_scr))
            .collect()
        else {
            continue;
        };
        if pq.iter().all(|&pt| mc.is_nonsingular_point(pt)) {
            screens.push((mc, pq));
        }
    }

    let mut exact_checks = 0u64;
    let mut certified = Vec::new();
    for cand in candidates {
        if exact_checks as usize >= max_exact_checks {
            break;
        }
        if screens
            .iter()
            .any(|(mc, pq)| mc.relation_is_origin(&cand, pq, &mut aux_ops) != Some(true))
        {
            continue;
        }
        exact_checks += 1;
        let big_scalars: Vec<BigInt> = cand.iter().map(|&x| BigInt::from(x)).collect();
        if group.relation_sum(&big_scalars, points)? == *group.origin() {
            let fixed = transport_to_fixed_flex(&cand, origin_pair);
            let is_col = is_collinear_relation_alias(&cand, origin_pair, points);
            let is_cb = is_cayley_bacharach_hyperplane_tautology(&cand, origin_pair);
            let l1_norm = cand.iter().map(|x| x.unsigned_abs()).sum();
            let linf_norm = cand.iter().map(|x| x.unsigned_abs()).max().unwrap_or(0);
            certified.push(CertifiedPlaneCubicRelation {
                scalars: cand,
                fixed_flex_scalars: fixed,
                is_collinear_alias: is_col,
                is_cb_hyperplane_tautology: is_cb,
                l1_norm,
                linf_norm,
            });
        }
    }

    Ok(ModularKernelRelationSearch {
        aux_primes_used: used_primes,
        aux_curve_group_ops: aux_ops,
        rational_cert_checks: exact_checks,
        certified_relations: certified,
    })
}
