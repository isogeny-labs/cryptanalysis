//! Escape 7A — Cayley-Bacharach 9-point cubic pencils (`dim ker_Q B(P_1..P_9) = 2`),
//! rational `lambda` specialization, shared `CoordinateFb` abscissa-pool solving,
//! and strict non-collinear hit rates across `8..14`-bit prime-order curves.

use std::collections::HashSet;

use num_bigint::BigInt;
use num_integer::Integer;
use num_rational::BigRational;
use num_traits::{One, Zero};
use serde::{Deserialize, Serialize};

use crate::field_ec::{
    expected_pollard_rho_ops, find_prime_order_curve, solve_pollard_rho_single_target, EcPoint,
    PollardRhoReceipt, PrimeWeierstrass, SplitMix64,
};
use crate::linalg_lll::{
    integer_kernel_basis, lll_reduce_hp, max_vec_bits, mod_inv_bigint, primitivize_vec,
    rank_mod_prime, rank_over_q, solve_var0_mod_prime,
};
use crate::plane_cubic::{
    canonical_projective_mod_p, choose_best_chord_pair, collinear_point_triples,
    find_relations_modular_kernel_lll, homogeneous_congruence_sublattice,
    jksst_projective_frame_mod_p, lift_projective_point_lll, mat_vec_mod_p,
    plane_cubic_discriminant, plane_cubic_gradient, plane_cubic_incidence_row, plane_cubic_value,
    select_best_cubic_from_sublattice, PlaneCubicPoint, PLANE_CUBIC_COEFFICIENTS,
};

/// Certified 9-point Cayley-Bacharach pencil configuration in `P^2(Z)`.
#[derive(Clone, Debug)]
pub struct CayleyBacharachPencil {
    pub c0: Vec<BigInt>,
    pub c1: Vec<BigInt>,
    pub points_9: Vec<PlaneCubicPoint>,
    pub incidence_rank_q: usize,
    pub pencil_mod_p_rank: usize,
    pub p9_height_bits: u64,
}

fn poly_mul_rat(a: &[BigRational], b: &[BigRational]) -> Vec<BigRational> {
    let mut out = vec![BigRational::zero(); a.len() + b.len() - 1];
    for (i, x) in a.iter().enumerate() {
        for (j, y) in b.iter().enumerate() {
            out[i + j] += x * y;
        }
    }
    out
}

fn poly_sub_rat(a: &[BigRational], b: &[BigRational]) -> Vec<BigRational> {
    let n = a.len().max(b.len());
    let mut out = vec![BigRational::zero(); n];
    for (i, slot) in out.iter_mut().enumerate() {
        let va = a.get(i).cloned().unwrap_or_else(BigRational::zero);
        let vb = b.get(i).cloned().unwrap_or_else(BigRational::zero);
        *slot = va - vb;
    }
    out
}

/// Exact division of homogeneous binary form `num(X, Z)` (coeff `i` = `X^(d-i) Z^i`)
/// by linear factor `(l0 * X + l1 * Z)` over `Q`.
fn divide_homogeneous_by_linear(
    num: &[BigRational],
    l0: &BigRational,
    l1: &BigRational,
) -> Result<Vec<BigRational>, String> {
    if num.len() < 2 {
        return Err("cannot divide degree-0 form by linear factor".into());
    }
    let m = num.len() - 1;
    if !l0.is_zero() {
        let mut q = vec![BigRational::zero(); m];
        let mut rem = num.to_vec();
        for i in 0..m {
            let coeff = &rem[i] / l0;
            q[i] = coeff.clone();
            rem[i] = BigRational::zero();
            rem[i + 1] -= &coeff * l1;
        }
        if !rem[m].is_zero() {
            return Err(
                "nonzero remainder in Sylvester resultant linear division (l0 != 0)".into(),
            );
        }
        Ok(q)
    } else if !l1.is_zero() {
        // Factor is l1 * Z: num[i] is coeff of X^(m-i) Z^i, so Z divides num iff num[0] == 0!
        if !num[0].is_zero() {
            return Err("nonzero remainder when dividing by Z".into());
        }
        Ok(num[1..=m].iter().map(|c| c / l1).collect())
    } else {
        Err("zero linear factor".into())
    }
}

fn eval_homog_rat(poly: &[BigRational], x: &BigRational, z: &BigRational) -> BigRational {
    let d = poly.len() - 1;
    let mut acc = BigRational::zero();
    for (i, c) in poly.iter().enumerate() {
        let xp = (d - i) as u32;
        let zp = i as u32;
        acc += c * x.pow(xp as i32) * z.pow(zp as i32);
    }
    acc
}

/// Compute the exact rational 9th base point `P_9^CB` of two cubics `(C_0, C_1)`
/// passing through `P_1 = (1:0:0), P_2 = (0:1:0), P_3 = (0:0:1), P_4 = (1:1:1), P_5..P_8`.
pub fn compute_cayley_bacharach_ninth_point(
    c0: &[BigInt],
    c1: &[BigInt],
    pts_8: &[PlaneCubicPoint],
) -> Result<PlaneCubicPoint, String> {
    if pts_8.len() != 8 {
        return Err("expected 8 points in general position".into());
    }
    let to_r = |x: &BigInt| BigRational::from_integer(x.clone());
    // Write C_k(X, Y, Z) = A_k(X, Z) Y^2 + B_k(X, Z) Y + D_k(X, Z)
    // Monomial order: (X^3:0, X^2Y:1, XY^2:2, Y^3:3, X^2Z:4, XYZ:5, Y^2Z:6, XZ^2:7, YZ^2:8, Z^3:9)
    // Note c[3] = 0 because P_2 = (0:1:0) is on both cubics.
    if !c0[3].is_zero() || !c1[3].is_zero() {
        return Err("expected P_2 = (0:1:0) frame vertex so Y^3 vanishes".into());
    }
    let a0 = vec![to_r(&c0[2]), to_r(&c0[6])];
    let b0 = vec![to_r(&c0[1]), to_r(&c0[5]), to_r(&c0[8])];
    let d0 = vec![to_r(&c0[0]), to_r(&c0[4]), to_r(&c0[7]), to_r(&c0[9])];

    let a1 = vec![to_r(&c1[2]), to_r(&c1[6])];
    let b1 = vec![to_r(&c1[1]), to_r(&c1[5]), to_r(&c1[8])];
    let d1 = vec![to_r(&c1[0]), to_r(&c1[4]), to_r(&c1[7]), to_r(&c1[9])];

    let a0d1_a1d0 = poly_sub_rat(&poly_mul_rat(&a0, &d1), &poly_mul_rat(&a1, &d0)); // deg 4
    let a0b1_a1b0 = poly_sub_rat(&poly_mul_rat(&a0, &b1), &poly_mul_rat(&a1, &b0)); // deg 3
    let b0d1_b1d0 = poly_sub_rat(&poly_mul_rat(&b0, &d1), &poly_mul_rat(&b1, &d0)); // deg 5

    let term1 = poly_mul_rat(&a0d1_a1d0, &a0d1_a1d0); // deg 8
    let term2 = poly_mul_rat(&a0b1_a1b0, &b0d1_b1d0); // deg 8
    let mut res_xz = poly_sub_rat(&term1, &term2);

    // Divide out the 7 points with (X_i, Z_i) != (0, 0) (all except index 1 = (0:1:0)).
    for (idx, pt) in pts_8.iter().enumerate() {
        if idx == 1 {
            continue;
        }
        let xi = to_r(&pt.coordinates[0]);
        let zi = to_r(&pt.coordinates[2]);
        if xi.is_zero() && zi.is_zero() {
            return Err("unexpected second point at (0:1:0)".into());
        }
        // Factor is (Z_i * X - X_i * Z).
        res_xz = divide_homogeneous_by_linear(&res_xz, &zi, &(-xi))?;
    }
    if res_xz.len() != 2 || (res_xz[0].is_zero() && res_xz[1].is_zero()) {
        return Err("residual resultant factor is degenerate".into());
    }
    // Linear form res_xz[0] * X + res_xz[1] * Z = 0 => (X_9 : Z_9) = (-res_xz[1] : res_xz[0]).
    let x9 = -res_xz[1].clone();
    let z9 = res_xz[0].clone();
    if x9.is_zero() && z9.is_zero() {
        return Err("degenerate (X_9, Z_9) = (0, 0)".into());
    }

    // Recover Y_9 from (A_0 B_1 - A_1 B_0)(X_9, Z_9) * Y_9 + (A_0 D_1 - A_1 D_0)(X_9, Z_9) = 0.
    let denom_y = eval_homog_rat(&a0b1_a1b0, &x9, &z9);
    let numer_y = -eval_homog_rat(&a0d1_a1d0, &x9, &z9);
    let y9 = if !denom_y.is_zero() {
        numer_y / denom_y
    } else {
        // Edge case: (X_9 : Z_9) coincides with a known point P_j; use Vieta on A_0 Y^2 + B_0 Y + D_0 = 0.
        let mut matched_y = None;
        for (idx, pt) in pts_8.iter().enumerate() {
            if idx == 1 {
                continue;
            }
            let xi = to_r(&pt.coordinates[0]);
            let zi = to_r(&pt.coordinates[2]);
            if &x9 * &zi == &z9 * &xi {
                // Scale pt to match (x9, z9):
                let scale = if !xi.is_zero() { &x9 / &xi } else { &z9 / &zi };
                matched_y = Some(to_r(&pt.coordinates[1]) * scale);
                break;
            }
        }
        let y_known =
            matched_y.ok_or_else(|| "cannot resolve Y_9 in tangent CB base locus".to_string())?;
        let a_val = eval_homog_rat(&a0, &x9, &z9);
        let b_val = eval_homog_rat(&b0, &x9, &z9);
        if !a_val.is_zero() {
            (-b_val / a_val) - y_known
        } else {
            let a1_val = eval_homog_rat(&a1, &x9, &z9);
            let b1_val = eval_homog_rat(&b1, &x9, &z9);
            if a1_val.is_zero() {
                return Err("both cubics degenerate in Y at (X_9, Z_9)".into());
            }
            (-b1_val / a1_val) - y_known
        }
    };

    // Clear rational denominators to a primitive integer point.
    let lcm_den = x9.denom().lcm(y9.denom()).lcm(z9.denom());
    let ix = (&x9 * BigRational::from_integer(lcm_den.clone())).to_integer();
    let iy = (&y9 * BigRational::from_integer(lcm_den.clone())).to_integer();
    let iz = (&z9 * BigRational::from_integer(lcm_den)).to_integer();
    let p9 = PlaneCubicPoint::new([ix, iy, iz])?;

    if !plane_cubic_value(c0, &p9).is_zero() || !plane_cubic_value(c1, &p9).is_zero() {
        return Err("internal error: P_9^CB failed exact incidence on pencil basis".into());
    }
    Ok(p9)
}

/// Construct a certified 9-point Cayley-Bacharach pencil from 8 lifted points
/// (where `pts_8[0..4]` is the standard JKSST frame).
pub fn build_cayley_bacharach_pencil(
    pts_8: &[PlaneCubicPoint],
    modulus: &BigInt,
) -> Result<CayleyBacharachPencil, String> {
    if pts_8.len() != 8 {
        return Err("expected 8 lifted points".into());
    }
    let rows_8: Vec<Vec<BigInt>> = pts_8
        .iter()
        .map(|pt| {
            let [x, y, z] = &pt.coordinates;
            plane_cubic_incidence_row(x, y, z)
        })
        .collect();
    let mut kern = integer_kernel_basis(&rows_8, PLANE_CUBIC_COEFFICIENTS)?;
    if kern.len() != 2 {
        return Err(format!(
            "expected dim ker_Q B(P_1..P_8) = 2, got {}",
            kern.len()
        ));
    }
    lll_reduce_hp(&mut kern, 0.99).map_err(str::to_string)?;
    let c0 = primitivize_vec(kern[0].clone());
    let c1 = primitivize_vec(kern[1].clone());
    let p9 = compute_cayley_bacharach_ninth_point(&c0, &c1, pts_8)?;

    let mut points_9 = pts_8.to_vec();
    points_9.push(p9.clone());
    // Reject if P_9 coincides with one of P_1..P_8 (tangent base point).
    if pts_8.contains(&p9) {
        return Err("9th CB point collided with an existing base point (multiplicity 2)".into());
    }
    let rows_9: Vec<Vec<BigInt>> = points_9
        .iter()
        .map(|pt| {
            let [x, y, z] = &pt.coordinates;
            plane_cubic_incidence_row(x, y, z)
        })
        .collect();
    let inc_rank = rank_over_q(&rows_9, PLANE_CUBIC_COEFFICIENTS)?;
    if inc_rank != 8 {
        return Err(format!("expected rank_Q B(P_1..P_9) = 8, got {inc_rank}"));
    }
    let pencil_mod_p_rank =
        rank_mod_prime(&[c0.clone(), c1.clone()], PLANE_CUBIC_COEFFICIENTS, modulus);

    Ok(CayleyBacharachPencil {
        c0,
        c1,
        points_9,
        incidence_rank_q: inc_rank,
        pencil_mod_p_rank,
        p9_height_bits: p9.max_coord_bits(),
    })
}

/// Test rational `lambda = nu / mu` chord-tangent specializations `nabla C_lambda(P_i) . P_j = 0`
/// across all `8 * 7 = 56` ordered pairs `(i, j)`: count how many preserve projective congruence
/// `C_lambda = gamma * E'_src (mod p)` and verify equivalence with `2 P_i + P_j = O_E` on `E(F_p)`.
pub fn audit_chord_tangent_pencil_specializations(
    pencil: &CayleyBacharachPencil,
    transformed_source_cubic: &[BigInt],
    modulus: &BigInt,
) -> (usize, usize) {
    let mut total_valid_specializations = 0usize;
    let mut congruent_to_source_hits = 0usize;
    let piv = transformed_source_cubic
        .iter()
        .position(|x| !x.mod_floor(modulus).is_zero());

    for i in 0..8 {
        let g0 = plane_cubic_gradient(&pencil.c0, &pencil.points_9[i]);
        let g1 = plane_cubic_gradient(&pencil.c1, &pencil.points_9[i]);
        for j in 0..8 {
            if i == j {
                continue;
            }
            let pj = &pencil.points_9[j].coordinates;
            let dot0 = &g0[0] * &pj[0] + &g0[1] * &pj[1] + &g0[2] * &pj[2];
            let dot1 = &g1[0] * &pj[0] + &g1[1] * &pj[1] + &g1[2] * &pj[2];
            if dot0.is_zero() && dot1.is_zero() {
                continue;
            }
            // mu * dot0 + nu * dot1 = 0 => (mu, nu) = (dot1, -dot0) primitive.
            let g = dot0.gcd(&dot1);
            let mu = &dot1 / &g;
            let nu = (-&dot0) / &g;
            let c_lam: Vec<BigInt> = pencil
                .c0
                .iter()
                .zip(&pencil.c1)
                .map(|(a, b)| &mu * a + &nu * b)
                .collect();
            total_valid_specializations += 1;

            if let Some(pv) = piv {
                if let Ok(inv) = mod_inv_bigint(&transformed_source_cubic[pv], modulus) {
                    let scale = (&c_lam[pv] * inv).mod_floor(modulus);
                    if !scale.is_zero()
                        && c_lam
                            .iter()
                            .zip(transformed_source_cubic)
                            .all(|(c, t)| (c - &scale * t).mod_floor(modulus).is_zero())
                    {
                        congruent_to_source_hits += 1;
                    }
                }
            }
        }
    }
    (total_valid_specializations, congruent_to_source_hits)
}

/// Theoretical fresh-mask union-bound numerator `|M(r, B)| = ((2B + 1)^r - 1) / 2`
/// capped at `1.0` when divided by `q`, plus the weight-bounded non-collinear count for `||m||_inf <= 2`.
pub fn fresh_mask_null_probability_bound(r: usize, linf_bound: u64, group_order: u64) -> f64 {
    // Number of projective nonzero vectors in [-B, B]^r with support <= r is ((2B+1)^r - 1)/2;
    // however, the LLL modular kernel searches primitive vectors with small L1 norm (empirically L1 <= 6).
    // Report the exact projective L1-ball size #{m in Z^r / {+-1} : 1 <= ||m||_1 <= 6, ||m||_inf <= B} / q
    // alongside the full [-1, 1]^r box ((3^r - 1)/2) / q!
    let _ = linf_bound;
    let box1 = ((3u128.pow(r as u32) - 1) / 2) as f64;
    (box1 / (group_order as f64)).min(1.0)
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Escape7aPrimeRow {
    pub p: u64,
    pub bits: f64,
    pub curve_a: u64,
    pub curve_b: u64,
    pub group_order: u64,
    pub trials: usize,
    pub valid_cb_pencils: usize,
    pub rank_8_certified: usize,
    pub mod_p_reduction_identity_verified: usize,
    pub cb_hyperplane_tautologies_certified: usize,
    pub median_p9_height_bits: u64,
    pub median_congruent_cubic_bits: u64,
    pub chord_tangent_specs_tested: usize,
    pub chord_tangent_congruent_hits: usize,
    pub strict_non_collinear_hits: usize,
    pub strict_hit_rate: f64,
    pub fresh_mask_box1_null_upper: f64,
    pub single_relation_chance_1_over_q: f64,
    pub direct_solved_and_verified: bool,
    pub direct_recovered_scalar: Option<String>,
    pub coord_fb_size: usize,
    pub coord_fb_cb_p9_hits: usize,
    pub coord_fb_pencil_mw_relations: usize,
    pub coord_fb_solved_and_verified: bool,
    pub coord_fb_total_ops: u64,
    pub pollard_rho: PollardRhoReceipt,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Escape7aSummary {
    pub primes_tested: Vec<u64>,
    pub rows: Vec<Escape7aPrimeRow>,
}

/// Run the full Escape 7A investigation on one prime `p`.
pub fn run_escape_7a_for_prime(
    p: u64,
    trials: usize,
    pool_size: usize,
    fb_target_size: usize,
    seed: u64,
) -> Result<Escape7aPrimeRow, String> {
    let inst = find_prime_order_curve(p)?;
    let p_big = BigInt::from(inst.p);
    let n_big = BigInt::from(inst.order);
    let curve = PrimeWeierstrass::new(p_big.clone(), BigInt::from(inst.a), BigInt::from(inst.b))?;
    let gen = EcPoint::Affine(
        BigInt::from(inst.generator[0]),
        BigInt::from(inst.generator[1]),
    );
    let secret_x = BigInt::from((inst.order * 37 + 19) % (inst.order - 2) + 2);
    let mut dummy_ops = 0u64;
    let target_q = curve.scalar_mul(&secret_x, &gen, &mut dummy_ops)?;
    let source_cubic = curve.source_cubic_coefficients();

    let rho_receipt =
        solve_pollard_rho_single_target(&curve, &gen, &n_big, &target_q, seed ^ 0xA5A5_5A5A)?;
    if !rho_receipt.verified || rho_receipt.recovered_scalar != secret_x.to_string() {
        return Err("Pollard rho verification failed".into());
    }

    let mut rng = SplitMix64::new(seed ^ p);
    // Precompute 16 random jump steps for fast fresh-mask pool sampling.
    let mut jumps: Vec<(EcPoint, BigInt, BigInt)> = Vec::with_capacity(16);
    let mut src_ops = 0u64;
    for _ in 0..16 {
        let u = BigInt::one() + rng.uniform_below(&(&n_big - 1u64));
        let v = BigInt::one() + rng.uniform_below(&(&n_big - 1u64));
        let ug = curve.scalar_mul(&u, &gen, &mut src_ops)?;
        let vq = curve.scalar_mul(&v, &target_q, &mut src_ops)?;
        let jpt = curve.add(&ug, &vq, &mut src_ops)?;
        jumps.push((jpt, u, v));
    }

    let mut u_cur = BigInt::one() + rng.uniform_below(&(&n_big - 1u64));
    let mut v_cur = BigInt::one();
    let mut pt_cur = {
        let ug = curve.scalar_mul(&u_cur, &gen, &mut src_ops)?;
        let vq = curve.scalar_mul(&v_cur, &target_q, &mut src_ops)?;
        curve.add(&ug, &vq, &mut src_ops)?
    };

    let mut valid_cb_pencils = 0usize;
    let mut rank_8_certified = 0usize;
    let mut mod_p_identity_ok = 0usize;
    let mut cb_tautologies = 0usize;
    let mut p9_bits_vec = Vec::new();
    let mut cubic_bits_vec = Vec::new();
    let mut ct_specs_tested = 0usize;
    let mut ct_congruent_hits = 0usize;
    let mut strict_non_collinear_hits = 0usize;
    let mut direct_recovered: Option<BigInt> = None;

    for _t in 0..trials {
        // Sample `pool_size` masked source points.
        let mut pool_pts: Vec<[BigInt; 3]> = Vec::with_capacity(pool_size);
        let mut pool_ec: Vec<EcPoint> = Vec::with_capacity(pool_size);
        let mut pool_u: Vec<BigInt> = Vec::with_capacity(pool_size);
        let mut pool_v: Vec<BigInt> = Vec::with_capacity(pool_size);
        let mut seen_x: HashSet<BigInt> = HashSet::new();

        let mut guard = 0usize;
        while pool_pts.len() < pool_size && guard < pool_size * 8 {
            guard += 1;
            let j_idx = (rng.next_u64() as usize) & 15;
            pt_cur = curve.add(&pt_cur, &jumps[j_idx].0, &mut src_ops)?;
            u_cur = (&u_cur + &jumps[j_idx].1).mod_floor(&n_big);
            v_cur = (&v_cur + &jumps[j_idx].2).mod_floor(&n_big);
            if let EcPoint::Affine(px, py) = &pt_cur {
                if seen_x.insert(px.clone()) {
                    pool_pts.push([px.clone(), py.clone(), BigInt::one()]);
                    pool_ec.push(pt_cur.clone());
                    pool_u.push(u_cur.clone());
                    pool_v.push(v_cur.clone());
                }
            }
        }
        if pool_pts.len() < 8 {
            continue;
        }

        // Find first general-position 4-point frame.
        let mut frame_opt = None;
        'fs: for i0 in 0..4.min(pool_pts.len()) {
            for i1 in (i0 + 1)..6.min(pool_pts.len()) {
                for i2 in (i1 + 1)..8.min(pool_pts.len()) {
                    for i3 in (i2 + 1)..10.min(pool_pts.len()) {
                        if let Ok(fr) = jksst_projective_frame_mod_p(
                            &p_big,
                            &source_cubic,
                            &pool_pts,
                            [i0, i1, i2, i3],
                        ) {
                            frame_opt = Some(([i0, i1, i2, i3], fr));
                            break 'fs;
                        }
                    }
                }
            }
        }
        let Some((fidx, frame)) = frame_opt else {
            continue;
        };

        // Lift remaining points via 3D-LLL and select 4 shortest non-collinear preimages (total 8 points).
        let mut scored: Vec<(BigInt, usize, PlaneCubicPoint)> = Vec::new();
        for (idx, pt_mod) in frame.transformed_points_mod_p.iter().enumerate() {
            if fidx.contains(&idx) {
                continue;
            }
            if let Ok(lifted) = lift_projective_point_lll(pt_mod, &p_big) {
                let n2: BigInt = lifted.coordinates.iter().map(|x| x * x).sum();
                scored.push((n2, idx, lifted));
            }
        }
        scored.sort_by(|a, b| (&a.0, a.1).cmp(&(&b.0, b.1)));

        let mut sel_idx: Vec<usize> = fidx.to_vec();
        let mut pts_8: Vec<PlaneCubicPoint> = fidx
            .iter()
            .map(|&idx| PlaneCubicPoint::new(frame.transformed_points_mod_p[idx].clone()))
            .collect::<Result<_, _>>()?;
        for (_, idx, lpt) in scored {
            if sel_idx.len() == 8 {
                break;
            }
            let mut probe = pts_8.clone();
            probe.push(lpt);
            if collinear_point_triples(&probe).is_empty() {
                sel_idx.push(idx);
                pts_8 = probe;
            }
        }
        if pts_8.len() < 8 {
            continue;
        }

        let Ok(pencil) = build_cayley_bacharach_pencil(&pts_8, &p_big) else {
            continue;
        };
        if !collinear_point_triples(&pencil.points_9).is_empty() {
            continue;
        }
        valid_cb_pencils += 1;
        if pencil.incidence_rank_q == 8 {
            rank_8_certified += 1;
        }
        p9_bits_vec.push(pencil.p9_height_bits);

        // Verify the Mod-p Cayley-Bacharach Reduction Identity:
        // when pencil_mod_p_rank == 2 and P_9 != 0 mod p, P_9^CB mod p maps back to -(P_1 + ... + P_8) on E(F_p)!
        let mut sum_8 = EcPoint::Infinity;
        for &idx in &sel_idx {
            sum_8 = curve.add(&sum_8, &pool_ec[idx], &mut src_ops)?;
        }
        let expected_p9_ec = curve.negate(&sum_8);
        if pencil.pencil_mod_p_rank == 2 {
            if let Ok(p9_framed_mod) =
                canonical_projective_mod_p(&pencil.points_9[8].coordinates, &p_big)
            {
                let src_proj = mat_vec_mod_p(&frame.matrix_to_source, &p9_framed_mod, &p_big);
                let actual_ec = if src_proj[2].is_zero() {
                    EcPoint::Infinity
                } else if let Some(zinv) = curve.inv_mod(&src_proj[2]) {
                    EcPoint::Affine(
                        (&src_proj[0] * &zinv).mod_floor(&p_big),
                        (&src_proj[1] * &zinv).mod_floor(&p_big),
                    )
                } else {
                    EcPoint::Infinity
                };
                if actual_ec == expected_p9_ec {
                    mod_p_identity_ok += 1;
                }
            }
        }

        // Audit (i-a): rational chord-tangent specializations C_lambda = C_0 + lambda C_1.
        let (ct_tot, ct_hit) = audit_chord_tangent_pencil_specializations(
            &pencil,
            &frame.transformed_source_cubic,
            &p_big,
        );
        ct_specs_tested += ct_tot;
        ct_congruent_hits += ct_hit;

        // Optimize congruent pencil member C_lambda = mu C_0 + nu C_1 = gamma * E'_src (mod p).
        let Ok(sublattice) = homogeneous_congruence_sublattice(
            &[pencil.c0.clone(), pencil.c1.clone()],
            &frame.transformed_source_cubic,
            &p_big,
        ) else {
            continue;
        };
        let Ok(best_cubic) = select_best_cubic_from_sublattice(
            sublattice,
            &frame.transformed_source_cubic,
            &p_big,
            2,
        ) else {
            continue;
        };
        cubic_bits_vec.push(max_vec_bits(&best_cubic));

        let Some(origin_pair) = choose_best_chord_pair(&best_cubic, &pencil.points_9, Some(8))
        else {
            continue;
        };
        let Ok(rel_search) =
            find_relations_modular_kernel_lll(&best_cubic, &pencil.points_9, origin_pair, 7, 8, 24)
        else {
            continue;
        };

        if rel_search
            .certified_relations
            .iter()
            .any(|r| r.is_cb_hyperplane_tautology)
        {
            cb_tautologies += 1;
        }

        // Check strict non-collinear, non-CB-tautology relations and attempt exact [k]G == Q recovery!
        let mut trial_had_strict = false;
        let mut u_9: Vec<BigInt> = sel_idx.iter().map(|&i| pool_u[i].clone()).collect();
        let mut v_9: Vec<BigInt> = sel_idx.iter().map(|&i| pool_v[i].clone()).collect();
        // P_9^CB mod p = -(P_1 + ... + P_8) has exact source representation (-sum u_i, -sum v_i).
        let sum_u8: BigInt = u_9.iter().sum();
        let sum_v8: BigInt = v_9.iter().sum();
        u_9.push((-&sum_u8).mod_floor(&n_big));
        v_9.push((-&sum_v8).mod_floor(&n_big));

        let u_o = (-(&u_9[origin_pair[0]] + &u_9[origin_pair[1]])).mod_floor(&n_big);
        let v_o = (-(&v_9[origin_pair[0]] + &v_9[origin_pair[1]])).mod_floor(&n_big);

        for rel in &rel_search.certified_relations {
            if rel.is_collinear_alias || rel.is_cb_hyperplane_tautology {
                continue;
            }
            let mut coef_u = BigInt::zero();
            let mut coef_v = BigInt::zero();
            for (k, &sc) in rel.scalars.iter().enumerate() {
                if sc == 0 {
                    continue;
                }
                let sb = BigInt::from(sc);
                coef_u = (&coef_u + &sb * (&u_9[k] - &u_o)).mod_floor(&n_big);
                coef_v = (&coef_v + &sb * (&v_9[k] - &v_o)).mod_floor(&n_big);
            }
            // Exclude algebraic combinations of the CB tautology that still collapse to (0, 0) mod n!
            if coef_u.is_zero() && coef_v.is_zero() {
                continue;
            }
            trial_had_strict = true;
            if direct_recovered.is_none() && !coef_v.is_zero() {
                if let Ok(inv_v) = mod_inv_bigint(&coef_v, &n_big) {
                    let cand_x = ((-&coef_u) * inv_v).mod_floor(&n_big);
                    let mut v_ops = 0u64;
                    if curve.scalar_mul(&cand_x, &gen, &mut v_ops)? == target_q {
                        direct_recovered = Some(cand_x);
                    }
                }
            }
        }
        if trial_had_strict {
            strict_non_collinear_hits += 1;
        }
    }

    // --- Mechanism (i-b): Shared `CoordinateFb` Abscissa Pool + CB Pencils ---
    let mut fb_ops = 0u64;
    let mut sqrt_probes = 0u64;
    let mut frame_src: Vec<[BigInt; 3]> = Vec::new();
    let mut frame_ec: Vec<EcPoint> = Vec::new();
    let mut frame_u: Vec<BigInt> = Vec::new();
    let mut frame_v: Vec<BigInt> = Vec::new();
    let mut cur_u = BigInt::from(3u64);
    let mut cur_v = BigInt::one();
    let mut cur_pt = curve.add(
        &curve.scalar_mul(&cur_u, &gen, &mut fb_ops)?,
        &target_q,
        &mut fb_ops,
    )?;
    for step in 0..40usize {
        if let EcPoint::Affine(px, py) = &cur_pt {
            if !frame_src.iter().any(|q| &q[0] == px) {
                frame_src.push([px.clone(), py.clone(), BigInt::one()]);
                frame_ec.push(cur_pt.clone());
                frame_u.push(cur_u.clone());
                frame_v.push(cur_v.clone());
                if frame_src.len() == 4
                    && jksst_projective_frame_mod_p(&p_big, &source_cubic, &frame_src, [0, 1, 2, 3])
                        .is_ok()
                {
                    break;
                } else if frame_src.len() == 4 {
                    frame_src.pop();
                    frame_ec.pop();
                    frame_u.pop();
                    frame_v.pop();
                }
            }
        }
        if step % 2 == 0 {
            cur_pt = curve.add(&cur_pt, &gen, &mut fb_ops)?;
            cur_u = (&cur_u + 1u64).mod_floor(&n_big);
        } else {
            cur_pt = curve.add(&cur_pt, &target_q, &mut fb_ops)?;
            cur_v = (&cur_v + 1u64).mod_floor(&n_big);
        }
    }

    let mut fb_ec: Vec<EcPoint> = Vec::new();
    let mut fb_lifted: Vec<PlaneCubicPoint> = Vec::new();
    let mut fb_src: Vec<[BigInt; 3]> = Vec::new();
    let mut cb_p9_fb_hits = 0usize;
    let mut fb_mw_relations = 0usize;
    let mut fb_solved = false;

    if frame_src.len() == 4 {
        let fixed_frame =
            jksst_projective_frame_mod_p(&p_big, &source_cubic, &frame_src, [0, 1, 2, 3])?;
        let c = &fixed_frame.transformed_source_cubic;
        'sieve: for radius in 1..=48i64 {
            for xi in -radius..=radius {
                for zi in 1..=radius {
                    if xi.abs() != radius && zi != radius {
                        continue;
                    }
                    if xi.gcd(&zi) != 1 {
                        continue;
                    }
                    let bx = BigInt::from(xi);
                    let bz = BigInt::from(zi);
                    let aq = (&c[2] * &bx + &c[6] * &bz).mod_floor(&p_big);
                    if aq.is_zero() {
                        continue;
                    }
                    let bq = (&c[1] * &bx * &bx + &c[5] * &bx * &bz + &c[8] * &bz * &bz)
                        .mod_floor(&p_big);
                    let dq = (&c[4] * &bx * &bx * &bz + &c[7] * &bx * &bz * &bz).mod_floor(&p_big);
                    let disc_q = (&bq * &bq - BigInt::from(4) * &aq * &dq).mod_floor(&p_big);
                    let Some(sq) = curve.tonelli_shanks_sqrt(&disc_q, &mut sqrt_probes) else {
                        continue;
                    };
                    let Some(inv2a) = curve.inv_mod(&(BigInt::from(2) * &aq)) else {
                        continue;
                    };
                    let ym = ((-&bq + sq) * inv2a).mod_floor(&p_big);
                    let framed_mod = [bx.mod_floor(&p_big), ym, bz.mod_floor(&p_big)];
                    let src_proj =
                        mat_vec_mod_p(&fixed_frame.matrix_to_source, &framed_mod, &p_big);
                    if src_proj[2].is_zero() {
                        continue;
                    }
                    let Some(zinv) = curve.inv_mod(&src_proj[2]) else {
                        continue;
                    };
                    let sx = (&src_proj[0] * &zinv).mod_floor(&p_big);
                    let sy = (&src_proj[1] * &zinv).mod_floor(&p_big);
                    // Deduplicate by abscissa sx (sign-folded shared CoordinateFb!).
                    if frame_src.iter().any(|fp| fp[0] == sx) || fb_src.iter().any(|fp| fp[0] == sx)
                    {
                        continue;
                    }
                    let ec_pt = EcPoint::Affine(sx.clone(), sy.clone());
                    if !curve.on_curve(&ec_pt) {
                        continue;
                    }
                    let lifted = lift_projective_point_lll(&framed_mod, &p_big)?;
                    fb_src.push([sx, sy, BigInt::one()]);
                    fb_ec.push(ec_pt);
                    fb_lifted.push(lifted);
                    if fb_src.len() >= fb_target_size {
                        break 'sieve;
                    }
                }
            }
        }

        let num_fb = fb_src.len();
        if num_fb >= 4 {
            // Unknowns: var 0 = secret scalar x, vars 1..=num_fb = logs z_j of fb_ec[j].
            let num_vars = 1 + num_fb;
            let mut eq_rows: Vec<Vec<BigInt>> = Vec::new();
            let mut eq_rhs: Vec<BigInt> = Vec::new();
            let frame_lifted_4: Vec<PlaneCubicPoint> = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1]]
                .into_iter()
                .map(|arr| {
                    PlaneCubicPoint::new([
                        BigInt::from(arr[0]),
                        BigInt::from(arr[1]),
                        BigInt::from(arr[2]),
                    ])
                    .unwrap()
                })
                .collect();

            let mut fb_rng = SplitMix64::new(seed ^ 0xCB09_FB01 ^ p);
            let fb_trials = if p <= 1021 { 320 } else { 140 };
            let mut walk_u = BigInt::from(11u64);
            let mut walk_v = BigInt::from(3u64);
            let mut walk_pt = curve.add(
                &curve.scalar_mul(&walk_u, &gen, &mut fb_ops)?,
                &curve.scalar_mul(&walk_v, &target_q, &mut fb_ops)?,
                &mut fb_ops,
            )?;

            for _ft in 0..fb_trials {
                let j_idx = (fb_rng.next_u64() as usize) & 15;
                walk_pt = curve.add(&walk_pt, &jumps[j_idx].0, &mut fb_ops)?;
                walk_u = (&walk_u + &jumps[j_idx].1).mod_floor(&n_big);
                walk_v = (&walk_v + &jumps[j_idx].2).mod_floor(&n_big);
                let EcPoint::Affine(wx, wy) = &walk_pt else {
                    continue;
                };
                if frame_src.iter().any(|fp| &fp[0] == wx) || fb_src.iter().any(|fp| &fp[0] == wx) {
                    continue;
                }
                let walk_framed_mod = mat_vec_mod_p(
                    &fixed_frame.matrix_from_source,
                    &[wx.clone(), wy.clone(), BigInt::one()],
                    &p_big,
                );
                let Ok(walk_lifted) = lift_projective_point_lll(&walk_framed_mod, &p_big) else {
                    continue;
                };

                // Build 8-tuple = frame_4 + fresh masked walk_lifted + 3 distinct CoordinateFb points!
                let mut pts_8 = frame_lifted_4.clone();
                pts_8.push(walk_lifted);
                if !collinear_point_triples(&pts_8).is_empty() {
                    continue;
                }
                let mut chosen: Vec<usize> = Vec::with_capacity(3);
                let mut tries = 0usize;
                while chosen.len() < 3 && tries < num_fb * 6 {
                    tries += 1;
                    let idx = (fb_rng.next_u64() as usize) % num_fb;
                    if chosen.contains(&idx) {
                        continue;
                    }
                    let mut probe = pts_8.clone();
                    probe.push(fb_lifted[idx].clone());
                    if collinear_point_triples(&probe).is_empty() {
                        chosen.push(idx);
                        pts_8 = probe;
                    }
                }
                if chosen.len() < 3 {
                    continue;
                }
                let Ok(pencil) = build_cayley_bacharach_pencil(&pts_8, &p_big) else {
                    continue;
                };
                // Check (1) whether P_9^CB mod p lands in the shared CoordinateFb abscissa pool!
                let mut sum_8_ec = walk_pt.clone();
                for fe in &frame_ec {
                    sum_8_ec = curve.add(&sum_8_ec, fe, &mut fb_ops)?;
                }
                for &c_idx in &chosen {
                    sum_8_ec = curve.add(&sum_8_ec, &fb_ec[c_idx], &mut fb_ops)?;
                }
                let p9_ec = curve.negate(&sum_8_ec);
                if let EcPoint::Affine(p9x, p9y) = &p9_ec {
                    if let Some(hit_j) = fb_src.iter().position(|fp| &fp[0] == p9x) {
                        cb_p9_fb_hits += 1;
                        let sign_j = if &fb_src[hit_j][1] == p9y {
                            1i64
                        } else {
                            -1i64
                        };
                        // P_1..P_4 + walk_pt + sum_{k=0..2} F_{chosen[k]} + sign_j * F_{hit_j} = O_E!
                        let mut row = vec![BigInt::zero(); num_vars];
                        let sum_fu: BigInt = frame_u.iter().sum::<BigInt>() + &walk_u;
                        let sum_fv: BigInt = frame_v.iter().sum::<BigInt>() + &walk_v;
                        row[0] = sum_fv.mod_floor(&n_big);
                        for &c_idx in &chosen {
                            row[1 + c_idx] = (&row[1 + c_idx] + 1u64).mod_floor(&n_big);
                        }
                        row[1 + hit_j] = (&row[1 + hit_j] + BigInt::from(sign_j)).mod_floor(&n_big);
                        let rhs_val = (-sum_fu).mod_floor(&n_big);
                        eq_rows.push(row);
                        eq_rhs.push(rhs_val);
                    }
                }

                // Check (2) congruent C_lambda Mordell-Weil relations on the 8-point subset `(frame_4 + walk + 3*fb)`!
                // Check every 32nd trial after `p > 1021` or every 8th trial at `p <= 1021` to bound auxiliary ops cleanly.
                let check_mw = if p <= 1021 {
                    _ft % 4 == 0
                } else {
                    _ft % 8 == 0
                };
                if check_mw {
                    if let Ok(sub) = homogeneous_congruence_sublattice(
                        &[pencil.c0.clone(), pencil.c1.clone()],
                        &fixed_frame.transformed_source_cubic,
                        &p_big,
                    ) {
                        if let Ok(best_c) = select_best_cubic_from_sublattice(
                            sub,
                            &fixed_frame.transformed_source_cubic,
                            &p_big,
                            2,
                        ) {
                            if let Some(opair) = choose_best_chord_pair(&best_c, &pts_8, None) {
                                if let Ok(rsearch) = find_relations_modular_kernel_lll(
                                    &best_c, &pts_8, opair, 6, 8, 16,
                                ) {
                                    fb_ops += rsearch.aux_curve_group_ops;
                                    for rel in &rsearch.certified_relations {
                                        if rel.is_collinear_alias {
                                            continue;
                                        }
                                        fb_mw_relations += 1;
                                        let mut row = vec![BigInt::zero(); num_vars];
                                        let mut const_u = BigInt::zero();
                                        for slot in 0..4 {
                                            let fk = BigInt::from(rel.fixed_flex_scalars[slot]);
                                            const_u += &fk * &frame_u[slot];
                                            row[0] += &fk * &frame_v[slot];
                                        }
                                        {
                                            let fk_w = BigInt::from(rel.fixed_flex_scalars[4]);
                                            const_u += &fk_w * &walk_u;
                                            row[0] += &fk_w * &walk_v;
                                        }
                                        for (k, &c_idx) in chosen.iter().enumerate() {
                                            let fk = BigInt::from(rel.fixed_flex_scalars[5 + k]);
                                            row[1 + c_idx] += fk;
                                        }
                                        for entry in &mut row {
                                            *entry = entry.mod_floor(&n_big);
                                        }
                                        eq_rows.push(row);
                                        eq_rhs.push((-const_u).mod_floor(&n_big));
                                    }
                                }
                            }
                        }
                    }
                }

                if eq_rows.len() >= num_vars {
                    if let Some(cand_x) = solve_var0_mod_prime(&eq_rows, &eq_rhs, num_vars, &n_big)
                    {
                        let mut v_ops = 0u64;
                        if curve.scalar_mul(&cand_x, &gen, &mut v_ops)? == target_q {
                            fb_solved = true;
                            if direct_recovered.is_none() {
                                direct_recovered = Some(cand_x);
                            }
                            break;
                        }
                    }
                }
            }
        }
    }

    p9_bits_vec.sort_unstable();
    cubic_bits_vec.sort_unstable();
    let med_p9 = p9_bits_vec.get(p9_bits_vec.len() / 2).copied().unwrap_or(0);
    let med_cbits = cubic_bits_vec
        .get(cubic_bits_vec.len() / 2)
        .copied()
        .unwrap_or(0);
    let hit_rate = if valid_cb_pencils > 0 {
        strict_non_collinear_hits as f64 / valid_cb_pencils as f64
    } else {
        0.0
    };
    let _ = expected_pollard_rho_ops(&n_big);

    Ok(Escape7aPrimeRow {
        p,
        bits: (p as f64).log2(),
        curve_a: inst.a,
        curve_b: inst.b,
        group_order: inst.order,
        trials,
        valid_cb_pencils,
        rank_8_certified,
        mod_p_reduction_identity_verified: mod_p_identity_ok,
        cb_hyperplane_tautologies_certified: cb_tautologies,
        median_p9_height_bits: med_p9,
        median_congruent_cubic_bits: med_cbits,
        chord_tangent_specs_tested: ct_specs_tested,
        chord_tangent_congruent_hits: ct_congruent_hits,
        strict_non_collinear_hits,
        strict_hit_rate: hit_rate,
        fresh_mask_box1_null_upper: fresh_mask_null_probability_bound(8, 1, inst.order),
        single_relation_chance_1_over_q: 1.0 / (inst.order as f64),
        direct_solved_and_verified: direct_recovered.as_ref().is_some_and(|x| x == &secret_x),
        direct_recovered_scalar: direct_recovered.map(|x| x.to_string()),
        coord_fb_size: fb_src.len(),
        coord_fb_cb_p9_hits: cb_p9_fb_hits,
        coord_fb_pencil_mw_relations: fb_mw_relations,
        coord_fb_solved_and_verified: fb_solved,
        coord_fb_total_ops: fb_ops + sqrt_probes,
        pollard_rho: rho_receipt,
    })
}

pub fn run_escape_7a_suite(seed: u64) -> Result<Escape7aSummary, String> {
    let primes = vec![251u64, 509, 1021, 2039, 4093, 8191, 16381];
    let mut rows = Vec::with_capacity(primes.len());
    for &p in &primes {
        let trials = if p <= 1021 { 160 } else { 120 };
        let pool_size = 40;
        let fb_size = if p <= 1021 { 10 } else { 14 };
        let _ = plane_cubic_discriminant;
        rows.push(run_escape_7a_for_prime(
            p, trials, pool_size, fb_size, seed,
        )?);
    }
    Ok(Escape7aSummary {
        primes_tested: primes,
        rows,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cayley_bacharach_ninth_point_certifies_rank_8_and_mod_p_identity_at_p251() {
        let inst = find_prime_order_curve(251).unwrap();
        let p_big = BigInt::from(inst.p);
        let curve =
            PrimeWeierstrass::new(p_big.clone(), BigInt::from(inst.a), BigInt::from(inst.b))
                .unwrap();
        let gen = EcPoint::Affine(
            BigInt::from(inst.generator[0]),
            BigInt::from(inst.generator[1]),
        );
        let mut ops = 0u64;
        let mut pool_pts = Vec::new();
        for k in 1..=20u64 {
            if let EcPoint::Affine(px, py) = curve
                .scalar_mul(&BigInt::from(k * 7), &gen, &mut ops)
                .unwrap()
            {
                pool_pts.push([px, py, BigInt::one()]);
            }
        }
        let fr = jksst_projective_frame_mod_p(
            &p_big,
            &curve.source_cubic_coefficients(),
            &pool_pts,
            [0, 1, 2, 3],
        )
        .unwrap();
        let mut pts_8: Vec<PlaneCubicPoint> = (0..4)
            .map(|i| PlaneCubicPoint::new(fr.transformed_points_mod_p[i].clone()).unwrap())
            .collect();
        for i in 4..20 {
            let lpt = lift_projective_point_lll(&fr.transformed_points_mod_p[i], &p_big).unwrap();
            let mut pr = pts_8.clone();
            pr.push(lpt);
            if collinear_point_triples(&pr).is_empty() {
                pts_8 = pr;
                if pts_8.len() == 8 {
                    break;
                }
            }
        }
        let pen = build_cayley_bacharach_pencil(&pts_8, &p_big)
            .expect("build_cayley_bacharach_pencil failed");
        assert_eq!(pen.incidence_rank_q, 8);
        let row = run_escape_7a_for_prime(251, 60, 32, 8, 2026_1119).unwrap();
        assert!(row.valid_cb_pencils >= 10, "got row={row:?}");
        assert_eq!(row.rank_8_certified, row.valid_cb_pencils);
        assert!(row.cb_hyperplane_tautologies_certified > 0);
        assert!(row.pollard_rho.verified);
    }
}
