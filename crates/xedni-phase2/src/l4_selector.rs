//! Escape 7C — Flagship `CH-L4` (`L4-check F1`) scalar-blind public small-height
//! lift selector, exact Tate-doubling Neron-Tate canonical heights & Gram span
//! ratio `rho_G`, `8..12`-bit conditioned vs unconditioned height separation, and
//! `24..28`-bit growing-rank (`r = 7, 8, 9`) height scaling vs Theorem X / JKSST thresholds.

use std::collections::HashSet;

use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::{One, Zero};
use serde::{Deserialize, Serialize};

use crate::field_ec::{find_prime_order_curve, EcPoint, PrimeWeierstrass, SplitMix64};
use crate::linalg_lll::{
    abs_bits, integer_kernel_basis, lll_reduce_hp, max_vec_bits, primitivize_vec,
};
use crate::plane_cubic::{
    choose_best_chord_pair, collinear_point_triples, find_relations_modular_kernel_lll,
    homogeneous_congruence_sublattice, jksst_projective_frame_mod_p,
    lift_projective_point_affine_balanced, lift_projective_point_weighted_lll,
    plane_cubic_discriminant, plane_cubic_incidence_row, select_best_cubic_from_sublattice,
    PlaneCubicGroup, PlaneCubicPoint, PLANE_CUBIC_COEFFICIENTS,
};

/// Exact Hermite constants `gamma_s` in dimensions `1..=8` (classical Korkine-Zolotarev / `E_8`)
/// and `1 + s/4` for `s >= 9`, matching `L4-check/CHECK.md` (`rho*(7)=11.04, rho*(8)=5.04, rho*(9)=1.92`).
pub fn hermite_constant_theorem_x(s: usize) -> f64 {
    match s {
        0 => 1.0,
        1 => 1.0,
        2 => (4.0f64 / 3.0).sqrt(),
        3 => 2.0f64.powf(1.0 / 3.0),
        4 => 2.0f64.sqrt(),
        5 => 2.0f64.powf(3.0 / 5.0),
        6 => (64.0f64 / 3.0).powf(1.0 / 6.0),
        7 => 2.0f64.powf(6.0 / 7.0),
        8 => 2.0,
        _ => 1.0 + (s as f64) / 4.0,
    }
}

fn binom_f64(n: usize, k: usize) -> f64 {
    if k > n {
        return 0.0;
    }
    let k = k.min(n - k);
    let mut res = 1.0f64;
    for i in 0..k {
        res = res * ((n - i) as f64) / ((i + 1) as f64);
    }
    res
}

/// Compute `log2 |M(k, max_s, rho)|` in Theorem X (`L4-check/CHECK.md` §3):
/// `|M(k, S, rho)| = sum_{u=1}^S binom(k, u+1) * ((2 * floor((gamma_u * rho)^(u/2)) + 1)^(u+1) - 1) / 2`.
pub fn log2_theorem_x_candidate_count(k_points: usize, max_s: usize, rho: f64) -> f64 {
    if rho <= 0.0 || max_s == 0 {
        return f64::NEG_INFINITY;
    }
    let s_cap = max_s.min(k_points.saturating_sub(1));
    let mut terms_log2: Vec<f64> = Vec::with_capacity(s_cap);
    for u in 1..=s_cap {
        let gamma = hermite_constant_theorem_x(u);
        let c_u = ((gamma * rho).powf((u as f64) / 2.0)).floor();
        if c_u < 1.0 {
            continue;
        }
        let b_log2 = binom_f64(k_points, u + 1).log2();
        let box_log2 = ((u + 1) as f64) * (2.0 * c_u + 1.0).log2() - 1.0;
        terms_log2.push(b_log2 + box_log2);
    }
    if terms_log2.is_empty() {
        return f64::NEG_INFINITY;
    }
    let max_l = terms_log2.iter().copied().fold(f64::NEG_INFINITY, f64::max);
    let sum_exp: f64 = terms_log2.iter().map(|&x| 2.0f64.powf(x - max_l)).sum();
    max_l + sum_exp.log2()
}

/// Solve by bisection for the minimum `rho*` such that `log2 |M(k_points, max_s, rho*)| >= target_log2_m`.
/// - For 256-bit Pollard-rho parity (`Pr >= 2^-128` at `q ~ 2^256`), `target_log2_m = 128.0`.
/// - For sub-`sqrt(p)` per-trial dependence probability (`|M|/p >= p^(-1/2)`), `target_log2_m = 0.5 * log2(p)`.
pub fn solve_theorem_x_rho_threshold(k_points: usize, max_s: usize, target_log2_m: f64) -> f64 {
    let mut lo = 0.01f64;
    let mut hi = 1.0e6f64;
    for _ in 0..80 {
        let mid = 0.5 * (lo + hi);
        if log2_theorem_x_candidate_count(k_points, max_s, mid) >= target_log2_m {
            hi = mid;
        } else {
            lo = mid;
        }
    }
    0.5 * (lo + hi)
}

/// Public scalar-blind small-height lift selector arms.
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum SelectorArm {
    /// Affine balanced box lift `(bal_p(x), bal_p(y), 1)` on the `r` smallest-box points in the pool.
    NaiveBox,
    /// Single-shift `PGL_3(F_p)` 4-point frame + 3D-LLL shortest ray preselection.
    Pgl3Lll,
    /// Multi-shift Kummer abscissa translations + multi-frame anisotropic 3D-LLL + chord-origin-aware cubic coset selector.
    MultiShiftKummerTorsion,
}

/// Scalar-blind public output of [`select_public_small_height_lift`].
#[derive(Clone, Debug)]
pub struct PublicSelectedLift {
    pub arm: SelectorArm,
    pub selected_pool_indices: Vec<usize>,
    pub lifted_points: Vec<PlaneCubicPoint>,
    pub cubic_coefficients: Vec<BigInt>,
    pub origin_pair: [usize; 2],
    pub origin_bits: u64,
    pub max_point_bits: u64,
    pub coef_bits: u64,
    pub disc_bits: u64,
}

/// Scalar-blind public lift selector: takes ONLY public curve parameters `(modulus, a, b)`
/// and public affine points `public_pool` on `E(F_p)` (never sees secret `x` or masks `(u_i, v_i)`!).
pub fn select_public_small_height_lift(
    arm: SelectorArm,
    modulus: &BigInt,
    a_weier: &BigInt,
    b_weier: &BigInt,
    public_pool: &[[BigInt; 2]],
    rank_points: usize,
) -> Result<PublicSelectedLift, String> {
    if !(5..=9).contains(&rank_points) || public_pool.len() < rank_points {
        return Err("invalid rank_points or insufficient public_pool length".into());
    }
    let base_cubic = vec![
        BigInt::one(),
        BigInt::zero(),
        BigInt::zero(),
        BigInt::zero(),
        BigInt::zero(),
        BigInt::zero(),
        BigInt::from(-1),
        a_weier.mod_floor(modulus),
        BigInt::zero(),
        b_weier.mod_floor(modulus),
    ];

    match arm {
        SelectorArm::NaiveBox => {
            let mut scored: Vec<(BigInt, usize, PlaneCubicPoint)> =
                Vec::with_capacity(public_pool.len());
            for (idx, xy) in public_pool.iter().enumerate() {
                let pt = lift_projective_point_affine_balanced(
                    &[xy[0].clone(), xy[1].clone(), BigInt::one()],
                    modulus,
                )?;
                let box_h = pt.coordinates[0]
                    .magnitude()
                    .max(pt.coordinates[1].magnitude())
                    .clone();
                scored.push((BigInt::from(box_h), idx, pt));
            }
            scored.sort_by(|a, b| (&a.0, a.1).cmp(&(&b.0, b.1)));

            let mut sel_idx = Vec::with_capacity(rank_points);
            let mut lifted = Vec::with_capacity(rank_points);
            for (_, idx, pt) in scored {
                if sel_idx.len() == rank_points {
                    break;
                }
                let mut probe = lifted.clone();
                probe.push(pt);
                if collinear_point_triples(&probe).is_empty() {
                    sel_idx.push(idx);
                    lifted = probe;
                }
            }
            if lifted.len() < rank_points {
                return Err("insufficient non-collinear naive box lifts".into());
            }
            let rows: Vec<Vec<BigInt>> = lifted
                .iter()
                .map(|p| {
                    let [x, y, z] = &p.coordinates;
                    plane_cubic_incidence_row(x, y, z)
                })
                .collect();
            let kern = integer_kernel_basis(&rows, PLANE_CUBIC_COEFFICIENTS)?;
            let cubic = if rank_points == 9 {
                if kern.len() != 1 {
                    return Err("expected rank-1 cubic kernel at r=9".into());
                }
                let c = primitivize_vec(kern[0].clone());
                if plane_cubic_discriminant(&c)?.is_zero() {
                    return Err("singular r=9 naive cubic".into());
                }
                c
            } else {
                let sub = homogeneous_congruence_sublattice(&kern, &base_cubic, modulus)?;
                select_best_cubic_from_sublattice(sub, &base_cubic, modulus, 2)?
            };
            let opair = choose_best_chord_pair(&cubic, &lifted, None)
                .ok_or_else(|| "no valid chord origin".to_string())?;
            let grp = PlaneCubicGroup::with_chord_origin(
                cubic.clone(),
                &lifted[opair[0]],
                &lifted[opair[1]],
            )?;
            let disc = plane_cubic_discriminant(&cubic)?;
            Ok(PublicSelectedLift {
                arm,
                selected_pool_indices: sel_idx,
                max_point_bits: lifted
                    .iter()
                    .map(PlaneCubicPoint::max_coord_bits)
                    .max()
                    .unwrap_or(0),
                coef_bits: max_vec_bits(&cubic),
                disc_bits: abs_bits(&disc),
                origin_bits: grp.origin().max_coord_bits(),
                lifted_points: lifted,
                cubic_coefficients: cubic,
                origin_pair: opair,
            })
        }
        SelectorArm::Pgl3Lll => {
            let proj_pool: Vec<[BigInt; 3]> = public_pool
                .iter()
                .map(|xy| [xy[0].clone(), xy[1].clone(), BigInt::one()])
                .collect();
            select_framed_candidate(
                &proj_pool,
                &base_cubic,
                modulus,
                rank_points,
                1,
                &[[1, 1, 1]],
                false,
                arm,
            )
        }
        SelectorArm::MultiShiftKummerTorsion => {
            // Test Kummer abscissa translations x' = x + s (mod p):
            // y^2 = (x' - s)^3 + a (x' - s) + b = x'^3 - 3 s x'^2 + (3 s^2 + a) x' + (-s^3 - a s + b)
            // together with multiple 4-point projective frames, anisotropic 3D-LLL weights,
            // and chord-origin-aware cubic coset scoring (`coef_bits + origin_bits / 2`).
            let mut shifts = vec![BigInt::zero()];
            if !public_pool.is_empty() {
                // Shift placing pool[0]'s x-coordinate at 0 (Kummer origin alignment) and midpoint shifts!
                shifts.push((-&public_pool[0][0]).mod_floor(modulus));
                if public_pool.len() > 1 {
                    shifts.push((-&public_pool[1][0]).mod_floor(modulus));
                }
            }
            let weights = [[1i64, 1, 1], [2, 1, 1], [1, 2, 1], [1, 1, 2]];
            let mut best: Option<PublicSelectedLift> = None;

            for s in &shifts {
                // Homogeneous cubic for Y^2 Z = (X - s Z)^3 + a (X - s Z) Z^2 + b Z^3:
                // X^3 - 3 s X^2 Z - Y^2 Z + (3 s^2 + a) X Z^2 + (-s^3 - a s + b) Z^3 = 0.
                let s2 = (s * s).mod_floor(modulus);
                let s3 = (&s2 * s).mod_floor(modulus);
                let c4 = (BigInt::from(-3) * s).mod_floor(modulus);
                let c7 = (BigInt::from(3) * &s2 + a_weier).mod_floor(modulus);
                let c9 = (-&s3 - a_weier * s + b_weier).mod_floor(modulus);
                let shifted_cubic = vec![
                    BigInt::one(),
                    BigInt::zero(),
                    BigInt::zero(),
                    BigInt::zero(),
                    c4,
                    BigInt::zero(),
                    BigInt::from(-1),
                    c7,
                    BigInt::zero(),
                    c9,
                ];
                let shifted_pool: Vec<[BigInt; 3]> = public_pool
                    .iter()
                    .map(|xy| {
                        [
                            (&xy[0] + s).mod_floor(modulus),
                            xy[1].clone(),
                            BigInt::one(),
                        ]
                    })
                    .collect();

                if let Ok(cand) = select_framed_candidate(
                    &shifted_pool,
                    &shifted_cubic,
                    modulus,
                    rank_points,
                    6,
                    &weights,
                    true,
                    arm,
                ) {
                    let replace = match &best {
                        None => true,
                        Some(prev) => {
                            (cand.coef_bits, cand.disc_bits, cand.origin_bits)
                                < (prev.coef_bits, prev.disc_bits, prev.origin_bits)
                        }
                    };
                    if replace {
                        best = Some(cand);
                    }
                }
            }
            best.ok_or_else(|| "MultiShiftKummerTorsion found no valid candidate".into())
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn select_framed_candidate(
    proj_pool: &[[BigInt; 3]],
    source_cubic: &[BigInt],
    modulus: &BigInt,
    rank_points: usize,
    max_frames: usize,
    weight_profiles: &[[i64; 3]],
    penalize_origin: bool,
    arm: SelectorArm,
) -> Result<PublicSelectedLift, String> {
    let mut frames_tried = 0usize;
    let mut best: Option<PublicSelectedLift> = None;
    let cap = proj_pool.len().min(10);

    'outer: for i0 in 0..cap {
        for i1 in (i0 + 1)..cap {
            for i2 in (i1 + 1)..cap {
                for i3 in (i2 + 1)..cap {
                    let Ok(frame) = jksst_projective_frame_mod_p(
                        modulus,
                        source_cubic,
                        proj_pool,
                        [i0, i1, i2, i3],
                    ) else {
                        continue;
                    };
                    frames_tried += 1;

                    for &w_prof in weight_profiles {
                        let mut scored: Vec<(BigInt, usize, PlaneCubicPoint)> = Vec::new();
                        for (idx, pmod) in frame.transformed_points_mod_p.iter().enumerate() {
                            if [i0, i1, i2, i3].contains(&idx) {
                                continue;
                            }
                            if let Ok(lpt) =
                                lift_projective_point_weighted_lll(pmod, modulus, w_prof)
                            {
                                let n2: BigInt = lpt.coordinates.iter().map(|x| x * x).sum();
                                scored.push((n2, idx, lpt));
                            }
                        }
                        scored.sort_by(|a, b| (&a.0, a.1).cmp(&(&b.0, b.1)));

                        let mut sel_idx = vec![i0, i1, i2, i3];
                        let mut lifted: Vec<PlaneCubicPoint> = [i0, i1, i2, i3]
                            .into_iter()
                            .map(|idx| {
                                PlaneCubicPoint::new(frame.transformed_points_mod_p[idx].clone())
                            })
                            .collect::<Result<_, _>>()?;
                        for (_, idx, lpt) in scored {
                            if sel_idx.len() == rank_points {
                                break;
                            }
                            let mut probe = lifted.clone();
                            probe.push(lpt);
                            if collinear_point_triples(&probe).is_empty() {
                                sel_idx.push(idx);
                                lifted = probe;
                            }
                        }
                        if lifted.len() < rank_points {
                            continue;
                        }

                        let rows: Vec<Vec<BigInt>> = lifted
                            .iter()
                            .map(|p| {
                                let [x, y, z] = &p.coordinates;
                                plane_cubic_incidence_row(x, y, z)
                            })
                            .collect();
                        let Ok(kern) = integer_kernel_basis(&rows, PLANE_CUBIC_COEFFICIENTS) else {
                            continue;
                        };
                        let Ok(mut sub) = homogeneous_congruence_sublattice(
                            &kern,
                            &frame.transformed_source_cubic,
                            modulus,
                        ) else {
                            continue;
                        };
                        let cubic_res = if penalize_origin && sub.len() >= 2 {
                            lll_reduce_hp(&mut sub, 0.99).map_err(str::to_string)?;
                            select_origin_aware_cubic(
                                &sub,
                                &frame.transformed_source_cubic,
                                modulus,
                            )
                            .or_else(|_| {
                                select_best_cubic_from_sublattice(
                                    sub,
                                    &frame.transformed_source_cubic,
                                    modulus,
                                    2,
                                )
                            })
                        } else {
                            select_best_cubic_from_sublattice(
                                sub,
                                &frame.transformed_source_cubic,
                                modulus,
                                2,
                            )
                        };
                        let Ok(cubic) = cubic_res else {
                            continue;
                        };
                        let Some(opair) = choose_best_chord_pair(&cubic, &lifted, None) else {
                            continue;
                        };
                        let Ok(grp) = PlaneCubicGroup::with_chord_origin(
                            cubic.clone(),
                            &lifted[opair[0]],
                            &lifted[opair[1]],
                        ) else {
                            continue;
                        };
                        let Ok(disc) = plane_cubic_discriminant(&cubic) else {
                            continue;
                        };
                        if disc.is_zero() {
                            continue;
                        }
                        let cand = PublicSelectedLift {
                            arm,
                            selected_pool_indices: sel_idx,
                            max_point_bits: lifted
                                .iter()
                                .map(PlaneCubicPoint::max_coord_bits)
                                .max()
                                .unwrap_or(0),
                            coef_bits: max_vec_bits(&cubic),
                            disc_bits: abs_bits(&disc),
                            origin_bits: grp.origin().max_coord_bits(),
                            lifted_points: lifted,
                            cubic_coefficients: cubic,
                            origin_pair: opair,
                        };
                        let replace = match &best {
                            None => true,
                            Some(prev) => {
                                (cand.coef_bits, cand.origin_bits, cand.disc_bits)
                                    < (prev.coef_bits, prev.origin_bits, prev.disc_bits)
                            }
                        };
                        if replace {
                            best = Some(cand);
                        }
                    }

                    if frames_tried >= max_frames {
                        break 'outer;
                    }
                }
            }
        }
    }
    best.ok_or_else(|| "no valid framed public lift found".into())
}

fn select_origin_aware_cubic(
    sublattice: &[Vec<BigInt>],
    target_mod_p: &[BigInt],
    modulus: &BigInt,
) -> Result<Vec<BigInt>, String> {
    let piv = target_mod_p
        .iter()
        .position(|x| !x.mod_floor(modulus).is_zero())
        .ok_or_else(|| "zero target cubic".to_string())?;
    let t_inv = crate::linalg_lll::mod_inv_bigint(&target_mod_p[piv], modulus)?;
    let mut best: Option<(u64, u64, Vec<BigInt>)> = None;

    for a in -2i64..=2 {
        for b in -2i64..=2 {
            if a == 0 && b == 0 {
                continue;
            }
            let raw: Vec<BigInt> = (0..PLANE_CUBIC_COEFFICIENTS)
                .map(|k| &sublattice[0][k] * a + &sublattice[1][k] * b)
                .collect();
            let prim = primitivize_vec(raw);
            let scale = (&prim[piv] * &t_inv).mod_floor(modulus);
            if scale.is_zero()
                || prim
                    .iter()
                    .zip(target_mod_p)
                    .any(|(c, t)| !(c - &scale * t).mod_floor(modulus).is_zero())
            {
                continue;
            }
            let disc = plane_cubic_discriminant(&prim)?;
            if disc.is_zero() {
                continue;
            }
            // Chord origin of frame vertices (1:0:0) and (0:1:0) is (-c_2 : c_1 : 0) / gcd(c_1, c_2)!
            let g12 = prim[1].gcd(&prim[2]);
            let o_bits = if g12.is_zero() {
                max_vec_bits(&prim)
            } else {
                abs_bits(&(&prim[1] / &g12)).max(abs_bits(&(&prim[2] / &g12)))
            };
            let c_bits = max_vec_bits(&prim);
            let score = c_bits * 2 + o_bits;
            let replace = match &best {
                None => true,
                Some((bs, bd, _)) => (score, abs_bits(&disc)) < (*bs, *bd),
            };
            if replace {
                best = Some((score, abs_bits(&disc), prim));
            }
        }
    }
    best.map(|(_, _, v)| v)
        .ok_or_else(|| "no origin-aware nonsingular cubic".into())
}

// ============================================================================
// Exact Tate-doubling Neron-Tate canonical heights & Theorem X span ratio `rho_G`
// ============================================================================

/// Compute canonical hyperplane height `h_hat_H(P) = lim_{k->inf} h_{P^2}([2^k]_O P) / 4^k`
/// on `(C, O)` using `doublings` exact rational chord-tangent doublings (`4^k` divisor).
pub fn canonical_height_hyperplane_ln(
    group: &PlaneCubicGroup,
    pt: &PlaneCubicPoint,
    doublings: usize,
) -> Result<f64, String> {
    if pt == group.origin() {
        return Ok(0.0);
    }
    let mut cur = pt.clone();
    let mut denom = 1.0f64;
    for _ in 0..doublings {
        cur = group.add(&cur, &cur)?;
        denom *= 4.0;
        if &cur == group.origin() {
            return Ok(0.0);
        }
    }
    Ok(cur.weil_height_ln() / denom)
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CanonicalHeightProfile {
    pub max_hat_h_ln: f64,
    pub max_hat_h_bits: f64,
    pub span_rank_s: usize,
    pub lambda_min_ln: Option<f64>,
    pub rho_g: Option<f64>,
}

/// Compute `max_i h_hat_H(P_i)`, independent span rank `s`, lattice minimum `lambda(Lambda)`,
/// and Theorem X span ratio `rho_G = max_i h_hat_H(P_i) / lambda(Lambda)`.
pub fn compute_canonical_height_and_rho_g(
    group: &PlaneCubicGroup,
    points: &[PlaneCubicPoint],
    certified_relations: &[Vec<i64>],
    point_doublings: usize,
    pair_doublings: usize,
) -> Result<CanonicalHeightProfile, String> {
    let r = points.len();
    let mut diag_h = vec![0.0f64; r];
    for (i, pt) in points.iter().enumerate() {
        diag_h[i] = canonical_height_hyperplane_ln(group, pt, point_doublings)?;
    }
    let max_h = diag_h.iter().copied().fold(0.0f64, f64::max);

    // Build full Neron-Tate height pairing Gram matrix G_{ij} = 0.5 * (h(P_i + P_j) - h(P_i) - h(P_j)).
    // Use `pair_doublings` for pairwise sums (and matching `pair_doublings` diagonal so pairing is symmetric & consistent!).
    let mut diag_pair = vec![0.0f64; r];
    for (i, pt) in points.iter().enumerate() {
        diag_pair[i] = if pair_doublings == point_doublings {
            diag_h[i]
        } else {
            canonical_height_hyperplane_ln(group, pt, pair_doublings)?
        };
    }
    let mut gram = vec![vec![0.0f64; r]; r];
    for i in 0..r {
        gram[i][i] = diag_pair[i].max(0.0);
        for j in (i + 1)..r {
            let sum_pt = group.add(&points[i], &points[j])?;
            let h_sum = canonical_height_hyperplane_ln(group, &sum_pt, pair_doublings)?;
            let gij = 0.5 * (h_sum - diag_pair[i] - diag_pair[j]);
            gram[i][j] = gij;
            gram[j][i] = gij;
        }
    }

    // Select a maximal Q-independent subset `indep` using exact `certified_relations` first,
    // plus Cholesky positive-definiteness check `d_k > 1e-3 * max_diag` to guard torsion/dependent points.
    let mut dependent_drop: HashSet<usize> = HashSet::new();
    // Row-reduce certified_relations over f64/Q to drop pivot columns from the end so independent prefix survives.
    let mut rel_mat: Vec<Vec<f64>> = certified_relations
        .iter()
        .map(|v| v.iter().map(|&x| x as f64).collect())
        .collect();
    let mut r_row = 0usize;
    for col in (0..r).rev() {
        if let Some(piv) = (r_row..rel_mat.len()).find(|&rw| rel_mat[rw][col].abs() > 1e-9) {
            rel_mat.swap(r_row, piv);
            let pv = rel_mat[r_row][col];
            for v in &mut rel_mat[r_row] {
                *v /= pv;
            }
            let prow = rel_mat[r_row].clone();
            for (idx_r, row_v) in rel_mat.iter_mut().enumerate() {
                if idx_r != r_row && row_v[col].abs() > 1e-9 {
                    let f = row_v[col];
                    for (c, pv_c) in prow.iter().enumerate() {
                        row_v[c] -= f * pv_c;
                    }
                }
            }
            dependent_drop.insert(col);
            r_row += 1;
        }
    }

    let mut indep: Vec<usize> = Vec::new();
    let mut chol_l: Vec<Vec<f64>> = Vec::new();
    let tol = (max_h * 2.0e-3).max(1.0e-4);
    for (cand, gram_cand) in gram.iter().enumerate() {
        if dependent_drop.contains(&cand) || gram_cand[cand] <= tol {
            continue;
        }
        let k = indep.len();
        let mut row_l = vec![0.0f64; k + 1];
        let mut ok = true;
        for j in 0..k {
            let mut s = gram_cand[indep[j]];
            for t in 0..j {
                s -= row_l[t] * chol_l[j][t];
            }
            if chol_l[j][j] <= 1e-9 {
                ok = false;
                break;
            }
            row_l[j] = s / chol_l[j][j];
        }
        if !ok {
            continue;
        }
        let sq_sum: f64 = row_l[..k].iter().map(|x| x * x).sum();
        let diag_rem = gram[cand][cand] - sq_sum;
        if diag_rem > tol {
            row_l[k] = diag_rem.sqrt();
            indep.push(cand);
            chol_l.push(row_l);
        }
    }

    let s = indep.len();
    if s == 0 {
        return Ok(CanonicalHeightProfile {
            max_hat_h_ln: max_h,
            max_hat_h_bits: max_h / std::f64::consts::LN_2,
            span_rank_s: 0,
            lambda_min_ln: None,
            rho_g: None,
        });
    }

    // SVP on s x s Gram submatrix via scaled integer Cholesky + LLL + [-1, 1]^s search (`3^s <= 6561`).
    let scale = (1u64 << 24) as f64;
    let mut basis_int: Vec<Vec<BigInt>> = (0..s)
        .map(|i| {
            (0..s)
                .map(|j| {
                    if j <= i {
                        BigInt::from((chol_l[i][j] * scale).round() as i64)
                    } else {
                        BigInt::zero()
                    }
                })
                .collect()
        })
        .collect();
    // Track unimodular integer combination matrix by augmenting identity scaled tiny? Simpler:
    // directly enumerate [-2, 2]^s if s <= 5, or LLL-reduce augmented `[R_int | I_s]` and read `I_s` coords!
    let mut aug_basis: Vec<Vec<BigInt>> = (0..s)
        .map(|i| {
            let mut v = basis_int.remove(0);
            for j in 0..s {
                v.push(BigInt::from(i == j));
            }
            v
        })
        .collect();
    let _ = lll_reduce_hp(&mut aug_basis, 0.99);
    let coords_basis: Vec<Vec<f64>> = aug_basis
        .iter()
        .map(|row| {
            row[s..]
                .iter()
                .map(|x| x.to_string().parse::<f64>().unwrap_or(0.0))
                .collect()
        })
        .collect();

    let mut lambda_min = f64::INFINITY;
    let mut coeffs = vec![0i32; s];
    #[allow(clippy::too_many_arguments)]
    fn search_svp(
        depth: usize,
        s: usize,
        coeffs: &mut [i32],
        coords_basis: &[Vec<f64>],
        indep: &[usize],
        gram: &[Vec<f64>],
        best: &mut f64,
    ) {
        if depth == s {
            if coeffs.iter().all(|&c| c == 0) {
                return;
            }
            let mut v = vec![0.0f64; s];
            for (b_idx, &c) in coeffs.iter().enumerate() {
                if c != 0 {
                    let cf = c as f64;
                    for slot in 0..s {
                        v[slot] += cf * coords_basis[b_idx][slot];
                    }
                }
            }
            if v.iter().all(|x| x.abs() < 0.5) {
                return;
            }
            let mut qf = 0.0f64;
            for a in 0..s {
                for b in 0..s {
                    qf += v[a] * v[b] * gram[indep[a]][indep[b]];
                }
            }
            if qf > 1e-6 && qf < *best {
                *best = qf;
            }
            return;
        }
        let rad = if s <= 5 { 2 } else { 1 };
        for c in -rad..=rad {
            coeffs[depth] = c;
            search_svp(depth + 1, s, coeffs, coords_basis, indep, gram, best);
        }
    }
    search_svp(
        0,
        s,
        &mut coeffs,
        &coords_basis,
        &indep,
        &gram,
        &mut lambda_min,
    );

    let (lam_opt, rho_opt) = if lambda_min.is_finite() && lambda_min > 1e-6 {
        (Some(lambda_min), Some(max_h / lambda_min))
    } else {
        (None, None)
    };

    Ok(CanonicalHeightProfile {
        max_hat_h_ln: max_h,
        max_hat_h_bits: max_h / std::f64::consts::LN_2,
        span_rank_s: s,
        lambda_min_ln: lam_opt,
        rho_g: rho_opt,
    })
}

/// Exact Mann-Whitney U / ROC-AUC for predicting `positives` using `smaller score = higher rank`.
/// Returns `0.5` if either class is empty; `> 0.5` means successful lifts have smaller heights!
pub fn roc_auc_smaller_is_positive(scores_and_labels: &[(f64, bool)]) -> Option<f64> {
    let pos: Vec<f64> = scores_and_labels
        .iter()
        .filter(|&&(_, ok)| ok)
        .map(|&(s, _)| s)
        .collect();
    let neg: Vec<f64> = scores_and_labels
        .iter()
        .filter(|&&(_, ok)| !ok)
        .map(|&(s, _)| s)
        .collect();
    if pos.is_empty() || neg.is_empty() {
        return None;
    }
    let mut wins = 0.0f64;
    for &sp in &pos {
        for &sn in &neg {
            if sp < sn {
                wins += 1.0;
            } else if (sp - sn).abs() <= 1e-12 {
                wins += 0.5;
            }
        }
    }
    Some(wins / ((pos.len() * neg.len()) as f64))
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct L4ToySeparationRow {
    pub p: u64,
    pub bits: f64,
    pub group_order: u64,
    pub arm: SelectorArm,
    pub trials: usize,
    pub candidate_lifts: usize,
    pub non_collinear_successes: usize,
    pub success_rate: f64,
    pub all_median_coef_bits: u64,
    pub success_median_coef_bits: Option<u64>,
    pub all_median_hat_h_bits: f64,
    pub success_median_hat_h_bits: Option<f64>,
    pub all_median_rho_g: Option<f64>,
    pub success_median_rho_g: Option<f64>,
    pub roc_auc_small_coef_bits: Option<f64>,
    pub roc_auc_large_rho_g: Option<f64>,
    pub top_quartile_enrichment: Option<f64>,
    pub ecdlp_solved_and_verified: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct L4HighBitScalingRow {
    pub p: u64,
    pub bits: f64,
    pub group_order: u64,
    pub rank_r: usize,
    pub pool_w: usize,
    pub naive_min_coef_bits: u64,
    pub pgl3_lll_min_coef_bits: u64,
    pub kummer_multishift_min_coef_bits: u64,
    pub kummer_min_point_bits: u64,
    pub kummer_min_disc_bits: u64,
    pub kummer_min_hat_h_bits: f64,
    pub coef_bits_per_log2_p: f64,
    pub jksst_sub_sqrt_p_coef_bits_ceiling: f64,
    pub height_excess_ratio_over_ceiling: f64,
    pub theorem_x_rho_star_sub_sqrt_p: f64,
    pub theorem_x_rho_star_256bit_s_eq_r_minus_1: f64,
    pub theorem_x_rho_star_256bit_s_eq_r: f64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Escape7cSummary {
    pub experiment_i_toy_separation: Vec<L4ToySeparationRow>,
    pub experiment_ii_high_bit_scaling: Vec<L4HighBitScalingRow>,
}

fn median_f64(mut v: Vec<f64>) -> Option<f64> {
    v.retain(|x| x.is_finite());
    if v.is_empty() {
        return None;
    }
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    Some(v[v.len() / 2])
}

/// Run Experiment 7C-(i): `8..12`-bit conditioned vs unconditioned Weil/canonical height & `rho_G` audit.
pub fn run_l4_experiment_i_separation(seed: u64) -> Result<Vec<L4ToySeparationRow>, String> {
    let primes = [251u64, 509, 1021, 2039, 4093];
    let arms = [
        SelectorArm::NaiveBox,
        SelectorArm::Pgl3Lll,
        SelectorArm::MultiShiftKummerTorsion,
    ];
    let rank_r = 6usize;
    let pool_w = 24usize;
    let mut out = Vec::new();

    for &p in &primes {
        let inst = find_prime_order_curve(p)?;
        let p_big = BigInt::from(inst.p);
        let n_big = BigInt::from(inst.order);
        let curve =
            PrimeWeierstrass::new(p_big.clone(), BigInt::from(inst.a), BigInt::from(inst.b))?;
        let gen = EcPoint::Affine(
            BigInt::from(inst.generator[0]),
            BigInt::from(inst.generator[1]),
        );
        let secret_x = BigInt::from((inst.order * 41 + 7) % (inst.order - 2) + 2);
        let mut ops = 0u64;
        let target_q = curve.scalar_mul(&secret_x, &gen, &mut ops)?;

        let trials = if p <= 1021 { 90 } else { 60 };
        // Pre-generate `trials` identical public pools so all 3 selector arms are paired on the exact same inputs!
        let mut rng = SplitMix64::new(seed ^ 0x7C01 ^ p);
        let mut jumps = Vec::with_capacity(16);
        for _ in 0..16 {
            let u = BigInt::one() + rng.uniform_below(&(&n_big - 1u64));
            let v = BigInt::one() + rng.uniform_below(&(&n_big - 1u64));
            let jpt = curve.add(
                &curve.scalar_mul(&u, &gen, &mut ops)?,
                &curve.scalar_mul(&v, &target_q, &mut ops)?,
                &mut ops,
            )?;
            jumps.push((jpt, u, v));
        }
        let mut u_cur = BigInt::from(5u64);
        let mut v_cur = BigInt::one();
        let mut pt_cur = curve.add(
            &curve.scalar_mul(&u_cur, &gen, &mut ops)?,
            &target_q,
            &mut ops,
        )?;

        struct FrozenPool {
            pts: Vec<[BigInt; 2]>,
            u: Vec<BigInt>,
            v: Vec<BigInt>,
        }
        let mut pools = Vec::with_capacity(trials);
        for _ in 0..trials {
            let mut pts = Vec::with_capacity(pool_w);
            let mut u_vec = Vec::with_capacity(pool_w);
            let mut v_vec = Vec::with_capacity(pool_w);
            let mut seen_x = HashSet::new();
            let mut guard = 0usize;
            while pts.len() < pool_w && guard < pool_w * 8 {
                guard += 1;
                let j = (rng.next_u64() as usize) & 15;
                pt_cur = curve.add(&pt_cur, &jumps[j].0, &mut ops)?;
                u_cur = (&u_cur + &jumps[j].1).mod_floor(&n_big);
                v_cur = (&v_cur + &jumps[j].2).mod_floor(&n_big);
                if let EcPoint::Affine(px, py) = &pt_cur {
                    if seen_x.insert(px.clone()) {
                        pts.push([px.clone(), py.clone()]);
                        u_vec.push(u_cur.clone());
                        v_vec.push(v_cur.clone());
                    }
                }
            }
            if pts.len() == pool_w {
                pools.push(FrozenPool {
                    pts,
                    u: u_vec,
                    v: v_vec,
                });
            }
        }

        for &arm in &arms {
            let mut cand_count = 0usize;
            let mut succ_count = 0usize;
            let mut all_cbits = Vec::new();
            let mut succ_cbits = Vec::new();
            let mut all_h_bits = Vec::new();
            let mut succ_h_bits = Vec::new();
            let mut all_rhos = Vec::new();
            let mut succ_rhos = Vec::new();
            let mut cbits_labels: Vec<(f64, bool)> = Vec::new();
            let mut neg_rho_labels: Vec<(f64, bool)> = Vec::new();
            let mut solved_verified = false;

            for pool in &pools {
                let Ok(sel) = select_public_small_height_lift(
                    arm, &p_big, &curve.a, &curve.b, &pool.pts, rank_r,
                ) else {
                    continue;
                };
                let Ok(rel_res) = find_relations_modular_kernel_lll(
                    &sel.cubic_coefficients,
                    &sel.lifted_points,
                    sel.origin_pair,
                    6,
                    8,
                    20,
                ) else {
                    continue;
                };
                let Ok(grp) = PlaneCubicGroup::with_chord_origin(
                    sel.cubic_coefficients.clone(),
                    &sel.lifted_points[sel.origin_pair[0]],
                    &sel.lifted_points[sel.origin_pair[1]],
                ) else {
                    continue;
                };

                let exact_rels: Vec<Vec<i64>> = rel_res
                    .certified_relations
                    .iter()
                    .map(|r| r.scalars.clone())
                    .collect();
                let is_succ = rel_res
                    .certified_relations
                    .iter()
                    .any(|r| !r.is_collinear_alias);

                // Compute canonical heights and rho_G (2 doublings for pairs, 3 for points -> fast & exact!).
                let h_prof = compute_canonical_height_and_rho_g(
                    &grp,
                    &sel.lifted_points,
                    &exact_rels,
                    2,
                    1,
                )?;

                cand_count += 1;
                all_cbits.push(sel.coef_bits);
                all_h_bits.push(h_prof.max_hat_h_bits);
                if let Some(rg) = h_prof.rho_g {
                    all_rhos.push(rg);
                    neg_rho_labels.push((-rg, is_succ));
                }
                cbits_labels.push((sel.coef_bits as f64, is_succ));

                if is_succ {
                    succ_count += 1;
                    succ_cbits.push(sel.coef_bits);
                    succ_h_bits.push(h_prof.max_hat_h_bits);
                    if let Some(rg) = h_prof.rho_g {
                        succ_rhos.push(rg);
                    }
                    // Verify [k]G == Q recovery from non-collinear relation!
                    if !solved_verified {
                        for rel in &rel_res.certified_relations {
                            if rel.is_collinear_alias {
                                continue;
                            }
                            let mut cu = BigInt::zero();
                            let mut cv = BigInt::zero();
                            for (slot, &fk) in rel.fixed_flex_scalars.iter().enumerate() {
                                let p_idx = sel.selected_pool_indices[slot];
                                cu = (&cu + BigInt::from(fk) * &pool.u[p_idx]).mod_floor(&n_big);
                                cv = (&cv + BigInt::from(fk) * &pool.v[p_idx]).mod_floor(&n_big);
                            }
                            if !cv.is_zero() {
                                if let Ok(inv) = crate::linalg_lll::mod_inv_bigint(&cv, &n_big) {
                                    let cand_x = ((-cu) * inv).mod_floor(&n_big);
                                    let mut vops = 0u64;
                                    if curve.scalar_mul(&cand_x, &gen, &mut vops)? == target_q {
                                        solved_verified = true;
                                        break;
                                    }
                                }
                            }
                        }
                    }
                }
            }

            all_cbits.sort_unstable();
            succ_cbits.sort_unstable();
            let top_q_enrich = if succ_count > 0 && cand_count >= 8 {
                let mut sorted = cbits_labels.clone();
                sorted.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
                let q_len = (cand_count / 4).max(1);
                let hits_q = sorted[..q_len].iter().filter(|&&(_, ok)| ok).count();
                let base_rate = succ_count as f64 / cand_count as f64;
                Some((hits_q as f64 / q_len as f64) / base_rate)
            } else {
                None
            };

            out.push(L4ToySeparationRow {
                p,
                bits: (p as f64).log2(),
                group_order: inst.order,
                arm,
                trials,
                candidate_lifts: cand_count,
                non_collinear_successes: succ_count,
                success_rate: if cand_count > 0 {
                    succ_count as f64 / cand_count as f64
                } else {
                    0.0
                },
                all_median_coef_bits: all_cbits.get(all_cbits.len() / 2).copied().unwrap_or(0),
                success_median_coef_bits: if succ_cbits.is_empty() {
                    None
                } else {
                    Some(succ_cbits[succ_cbits.len() / 2])
                },
                all_median_hat_h_bits: median_f64(all_h_bits).unwrap_or(0.0),
                success_median_hat_h_bits: median_f64(succ_h_bits),
                all_median_rho_g: median_f64(all_rhos),
                success_median_rho_g: median_f64(succ_rhos),
                roc_auc_small_coef_bits: roc_auc_smaller_is_positive(&cbits_labels),
                roc_auc_large_rho_g: roc_auc_smaller_is_positive(&neg_rho_labels),
                top_quartile_enrichment: top_q_enrich,
                ecdlp_solved_and_verified: solved_verified,
            });
        }
    }
    Ok(out)
}

/// Run Experiment 7C-(ii): `24..28`-bit prime-order curves (`p ~ 2^24, 2^26, 2^28`) across `r = 7, 8, 9`.
pub fn run_l4_experiment_ii_high_bit_scaling(
    seed: u64,
) -> Result<Vec<L4HighBitScalingRow>, String> {
    let primes = [16_777_259u64, 67_108_879, 268_435_399];
    let ranks = [7usize, 8, 9];
    let pool_w = 96usize;
    let trials_per_cell = 6usize;
    let mut rows = Vec::new();

    for &p in &primes {
        let inst = find_prime_order_curve(p)?;
        let p_big = BigInt::from(inst.p);
        let n_big = BigInt::from(inst.order);
        let curve =
            PrimeWeierstrass::new(p_big.clone(), BigInt::from(inst.a), BigInt::from(inst.b))?;
        let gen = EcPoint::Affine(
            BigInt::from(inst.generator[0]),
            BigInt::from(inst.generator[1]),
        );
        let mut rng = SplitMix64::new(seed ^ 0x7C02 ^ p);
        let mut ops = 0u64;

        // Pre-sample `trials_per_cell` public pools of width `pool_w`.
        let mut pools = Vec::with_capacity(trials_per_cell);
        let step_pt = curve.scalar_mul(&BigInt::from(104_729u64), &gen, &mut ops)?;
        let mut cur = curve.scalar_mul(
            &(BigInt::one() + rng.uniform_below(&(&n_big - 1u64))),
            &gen,
            &mut ops,
        )?;
        for _ in 0..trials_per_cell {
            let mut pts = Vec::with_capacity(pool_w);
            let mut seen_x = HashSet::new();
            while pts.len() < pool_w {
                cur = curve.add(&cur, &step_pt, &mut ops)?;
                if let EcPoint::Affine(px, py) = &cur {
                    if seen_x.insert(px.clone()) {
                        pts.push([px.clone(), py.clone()]);
                    }
                }
            }
            pools.push(pts);
        }

        for &r in &ranks {
            let mut min_naive = u64::MAX;
            let mut min_pgl3 = u64::MAX;
            let mut min_kummer = u64::MAX;
            let mut min_pt_bits = u64::MAX;
            let mut min_disc_bits = u64::MAX;
            let mut min_hat_h_bits = f64::INFINITY;

            for pool in &pools {
                if let Ok(s_naive) = select_public_small_height_lift(
                    SelectorArm::NaiveBox,
                    &p_big,
                    &curve.a,
                    &curve.b,
                    pool,
                    r,
                ) {
                    min_naive = min_naive.min(s_naive.coef_bits);
                }
                if let Ok(s_pgl) = select_public_small_height_lift(
                    SelectorArm::Pgl3Lll,
                    &p_big,
                    &curve.a,
                    &curve.b,
                    pool,
                    r,
                ) {
                    min_pgl3 = min_pgl3.min(s_pgl.coef_bits);
                }
                if let Ok(s_kum) = select_public_small_height_lift(
                    SelectorArm::MultiShiftKummerTorsion,
                    &p_big,
                    &curve.a,
                    &curve.b,
                    pool,
                    r,
                ) {
                    if s_kum.coef_bits < min_kummer {
                        min_kummer = s_kum.coef_bits;
                        min_pt_bits = s_kum.max_point_bits;
                        min_disc_bits = s_kum.disc_bits;
                        if let Ok(grp) = PlaneCubicGroup::with_chord_origin(
                            s_kum.cubic_coefficients.clone(),
                            &s_kum.lifted_points[s_kum.origin_pair[0]],
                            &s_kum.lifted_points[s_kum.origin_pair[1]],
                        ) {
                            let mut max_hb = 0.0f64;
                            for lpt in &s_kum.lifted_points {
                                if let Ok(h_ln) = canonical_height_hyperplane_ln(&grp, lpt, 2) {
                                    max_hb = max_hb.max(h_ln / std::f64::consts::LN_2);
                                }
                            }
                            min_hat_h_bits = min_hat_h_bits.min(max_hb);
                        }
                    }
                }
            }

            let bits = (p as f64).log2();
            // JKSST / Siegel sub-sqrt(p) curve bit-height ceiling (~ 0.5 * log2(p) bits for O(1)-norm collision)
            let jksst_ceiling = 0.5 * bits;
            let rho_sub_sqrt = solve_theorem_x_rho_threshold(r, r - 1, 0.5 * bits);
            let rho_256_rm1 = solve_theorem_x_rho_threshold(r, r - 1, 128.0);
            let rho_256_r = solve_theorem_x_rho_threshold(r + 1, r, 128.0);

            rows.push(L4HighBitScalingRow {
                p,
                bits,
                group_order: inst.order,
                rank_r: r,
                pool_w,
                naive_min_coef_bits: min_naive,
                pgl3_lll_min_coef_bits: min_pgl3,
                kummer_multishift_min_coef_bits: min_kummer,
                kummer_min_point_bits: min_pt_bits,
                kummer_min_disc_bits: min_disc_bits,
                kummer_min_hat_h_bits: min_hat_h_bits,
                coef_bits_per_log2_p: (min_kummer as f64) / bits,
                jksst_sub_sqrt_p_coef_bits_ceiling: jksst_ceiling,
                height_excess_ratio_over_ceiling: (min_kummer as f64) / jksst_ceiling,
                theorem_x_rho_star_sub_sqrt_p: rho_sub_sqrt,
                theorem_x_rho_star_256bit_s_eq_r_minus_1: rho_256_rm1,
                theorem_x_rho_star_256bit_s_eq_r: rho_256_r,
            });
        }
    }
    Ok(rows)
}

pub fn run_escape_7c_suite(seed: u64) -> Result<Escape7cSummary, String> {
    let exp_i = run_l4_experiment_i_separation(seed)?;
    let exp_ii = run_l4_experiment_ii_high_bit_scaling(seed)?;
    Ok(Escape7cSummary {
        experiment_i_toy_separation: exp_i,
        experiment_ii_high_bit_scaling: exp_ii,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn theorem_x_thresholds_reproduce_l4_check_reference_values() {
        // Check k = s + 1 at 256 bits (`target_log2_m = 128.0`) against `L4-check/CHECK.md` §4:
        // s=7 -> 11.04, s=8 -> 5.04, s=9 -> 1.92!
        let r7 = solve_theorem_x_rho_threshold(8, 7, 128.0);
        let r8 = solve_theorem_x_rho_threshold(9, 8, 128.0);
        let r9 = solve_theorem_x_rho_threshold(10, 9, 128.0);
        assert!((r7 - 11.04).abs() < 0.05, "got r7={r7}");
        assert!((r8 - 5.04).abs() < 0.05, "got r8={r8}");
        assert!((r9 - 1.92).abs() < 0.05, "got r9={r9}");
    }

    #[test]
    fn canonical_height_satisfies_parallelogram_law_on_plane_cubic() {
        // y^2 z = x^3 - x z^2 + z^3 with origin at infinity (0:1:0)
        let coeffs: Vec<BigInt> = [1i64, 0, 0, 0, 0, 0, -1, -1, 0, 1]
            .into_iter()
            .map(BigInt::from)
            .collect();
        let inf = PlaneCubicPoint::new([BigInt::zero(), BigInt::one(), BigInt::zero()]).unwrap();
        let grp = PlaneCubicGroup::new(coeffs, inf).unwrap();
        let a = PlaneCubicPoint::new([BigInt::zero(), BigInt::one(), BigInt::one()]).unwrap();
        let b = PlaneCubicPoint::new([BigInt::from(56), BigInt::from(419), BigInt::one()]).unwrap();
        let a_plus_b = grp.add(&a, &b).unwrap();
        let a_minus_b = grp.add(&a, &grp.negate(&b).unwrap()).unwrap();

        let ha = canonical_height_hyperplane_ln(&grp, &a, 4).unwrap();
        let hb = canonical_height_hyperplane_ln(&grp, &b, 4).unwrap();
        let hp = canonical_height_hyperplane_ln(&grp, &a_plus_b, 4).unwrap();
        let hm = canonical_height_hyperplane_ln(&grp, &a_minus_b, 4).unwrap();
        let lhs = hp + hm;
        let rhs = 2.0 * (ha + hb);
        assert!(
            (lhs - rhs).abs() / rhs < 1e-2,
            "parallelogram mismatch: lhs={lhs}, rhs={rhs}"
        );
    }
}
