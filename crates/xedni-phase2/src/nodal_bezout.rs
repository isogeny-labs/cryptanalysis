//! Escape 7B — Singular / nodal degree-`d >= 4` plane Bezout curves collapsing
//! geometric genus to `g = (d-1)(d-2)/2 - delta <= 2`:
//! exact parameter vs `3d` congruence audit, off-base `0 mod p` collapse,
//! on-base `[2]`-multiplicity reducible sublattice collapse (`L*C'`, `Q*C'`, `Sym^2`),
//! and exact genus-2 hyperelliptic node-projection + Mumford Jacobian kernel LLL
//! on the surviving irreducible Bezout cell `(d=4, delta=1, s=11 => g=2, r=12)`.

use std::collections::{HashMap, HashSet};

use num_bigint::BigInt;
use num_integer::Integer;
use num_rational::BigRational;
use num_traits::{One, ToPrimitive, Zero};
use serde::{Deserialize, Serialize};

use crate::field_ec::{
    find_prime_order_curve, mod_inv_u64, mod_mul_u64, solve_pollard_rho_single_target, EcPoint,
    PollardRhoReceipt, PrimeWeierstrass, SplitMix64,
};
use crate::linalg_lll::{
    dot_bigint, integer_kernel_basis, intersect_full_rank_lattices, lll_reduce_hp, max_vec_bits,
    mod_inv_bigint, primitivize_vec, rank_mod_prime, rank_over_q, row_hermite_basis,
    subspace_congruence_sublattice,
};
use crate::plane_cubic::{
    collinear_point_triples, jksst_projective_frame_mod_p, lift_projective_point_lll,
    PlaneCubicPoint, CUBIC_EXPONENTS,
};

const JAC_AUX_PRIMES: &[u64] = &[
    257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349, 353, 359, 367,
    373, 379, 383, 389, 397, 401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479,
    487, 491, 499, 503, 509, 521, 523, 541, 547, 557, 563, 569, 571, 577, 587, 593, 599, 601, 607,
    613, 617, 619, 631, 641, 643, 647, 653, 659, 661, 673, 677, 683, 691, 701,
];

/// Deterministic graded-lexicographic exponent list `(ex, ey, ez)` with `ex + ey + ez = d`.
pub fn degree_d_exponents(d: usize) -> Vec<(usize, usize, usize)> {
    let mut exps = Vec::with_capacity((d + 1) * (d + 2) / 2);
    for ex in (0..=d).rev() {
        for ey in (0..=(d - ex)).rev() {
            let ez = d - ex - ey;
            exps.push((ex, ey, ez));
        }
    }
    exps
}

pub fn monomial_count(d: usize) -> usize {
    (d + 1) * (d + 2) / 2
}

pub fn projective_param_count(d: usize) -> usize {
    d * (d + 3) / 2
}

pub fn smooth_plane_genus(d: usize) -> isize {
    ((d as isize - 1) * (d as isize - 2)) / 2
}

fn pow_bigint(base: &BigInt, exp: usize) -> BigInt {
    let mut acc = BigInt::one();
    for _ in 0..exp {
        acc *= base;
    }
    acc
}

pub fn incidence_row_deg_d(
    exps: &[(usize, usize, usize)],
    x: &BigInt,
    y: &BigInt,
    z: &BigInt,
) -> Vec<BigInt> {
    exps.iter()
        .map(|&(ex, ey, ez)| pow_bigint(x, ex) * pow_bigint(y, ey) * pow_bigint(z, ez))
        .collect()
}

/// Exact linear rows enforcing a singular point (node, multiplicity >= 2) at `(x : y : z)`:
/// `C(Q) = 0`, `d_X C(Q) = 0`, `d_Y C(Q) = 0`, `d_Z C(Q) = 0` (exact rank 3 over `Q` by Euler's identity).
pub fn node_constraint_rows_deg_d(
    exps: &[(usize, usize, usize)],
    x: &BigInt,
    y: &BigInt,
    z: &BigInt,
) -> [Vec<BigInt>; 4] {
    let c_row = incidence_row_deg_d(exps, x, y, z);
    let dx_row: Vec<BigInt> = exps
        .iter()
        .map(|&(ex, ey, ez)| {
            if ex == 0 {
                BigInt::zero()
            } else {
                BigInt::from(ex) * pow_bigint(x, ex - 1) * pow_bigint(y, ey) * pow_bigint(z, ez)
            }
        })
        .collect();
    let dy_row: Vec<BigInt> = exps
        .iter()
        .map(|&(ex, ey, ez)| {
            if ey == 0 {
                BigInt::zero()
            } else {
                BigInt::from(ey) * pow_bigint(x, ex) * pow_bigint(y, ey - 1) * pow_bigint(z, ez)
            }
        })
        .collect();
    let dz_row: Vec<BigInt> = exps
        .iter()
        .map(|&(ex, ey, ez)| {
            if ez == 0 {
                BigInt::zero()
            } else {
                BigInt::from(ez) * pow_bigint(x, ex) * pow_bigint(y, ey) * pow_bigint(z, ez - 1)
            }
        })
        .collect();
    [c_row, dx_row, dy_row, dz_row]
}

/// Convert a JKSST-ordered cubic (`PLANE_CUBIC_COEFFICIENTS`) to `degree_d_exponents(3)` order.
pub fn jksst_cubic_to_grlex(cubic_jksst: &[BigInt]) -> Vec<BigInt> {
    let exps3 = degree_d_exponents(3);
    let mut out = vec![BigInt::zero(); 10];
    for (coef, &exp_j) in cubic_jksst.iter().zip(CUBIC_EXPONENTS.iter()) {
        let pos = exps3.iter().position(|&e| e == exp_j).expect("deg-3 exp");
        out[pos] = coef.clone();
    }
    out
}

/// Multiply two homogeneous polynomials of degrees `d1` and `d2` (in `degree_d_exponents` order).
pub fn mul_homog_poly(d1: usize, p1: &[BigInt], d2: usize, p2: &[BigInt]) -> Vec<BigInt> {
    let exps1 = degree_d_exponents(d1);
    let exps2 = degree_d_exponents(d2);
    let exps_out = degree_d_exponents(d1 + d2);
    let mut idx_map: HashMap<(usize, usize, usize), usize> = HashMap::with_capacity(exps_out.len());
    for (idx, &e) in exps_out.iter().enumerate() {
        idx_map.insert(e, idx);
    }
    let mut out = vec![BigInt::zero(); exps_out.len()];
    for (c1, &(x1, y1, z1)) in p1.iter().zip(&exps1) {
        if c1.is_zero() {
            continue;
        }
        for (c2, &(x2, y2, z2)) in p2.iter().zip(&exps2) {
            if c2.is_zero() {
                continue;
            }
            let slot = idx_map[&(x1 + x2, y1 + y2, z1 + z2)];
            out[slot] += c1 * c2;
        }
    }
    out
}

/// Basis of `{E_grlex * m_k mod p : m_k in Mon_{d-3}}` spanning multiples of `E` in `F_p[X,Y,Z]_d`.
pub fn multiples_of_cubic_basis_mod_p(
    d: usize,
    cubic_grlex: &[BigInt],
    modulus: &BigInt,
) -> Vec<Vec<BigInt>> {
    assert!(d >= 3);
    let m_rem = monomial_count(d - 3);
    let mut basis = Vec::with_capacity(m_rem);
    for k in 0..m_rem {
        let mut unit = vec![BigInt::zero(); m_rem];
        unit[k] = BigInt::one();
        let prod = mul_homog_poly(3, cubic_grlex, d - 3, &unit);
        basis.push(prod.into_iter().map(|v| v.mod_floor(modulus)).collect());
    }
    basis
}

/// Constructively verify `E | (C mod p)` in `F_p[X, Y, Z]_d` by checking whether `C mod p`
/// lies in `span_{F_p}{E * m_k}` and `C != 0 mod p`.
pub fn is_divisible_by_cubic_mod_p(
    d: usize,
    c_poly: &[BigInt],
    cubic_grlex: &[BigInt],
    modulus: &BigInt,
) -> bool {
    if c_poly.iter().all(|v| v.mod_floor(modulus).is_zero()) {
        return false;
    }
    let mult_basis = multiples_of_cubic_basis_mod_p(d, cubic_grlex, modulus);
    let dim = monomial_count(d);
    let r_base = rank_mod_prime(&mult_basis, dim, modulus);
    let mut with_c = mult_basis;
    with_c.push(c_poly.iter().map(|v| v.mod_floor(modulus)).collect());
    let r_aug = rank_mod_prime(&with_c, dim, modulus);
    r_aug == r_base
}

/// Test exact divisibility `factor_k | poly_d` over `Q` (`factor_k != 0` of degree `k < d`).
pub fn divides_over_q(
    d: usize,
    poly_d: &[BigInt],
    k: usize,
    factor_k: &[BigInt],
) -> Result<bool, String> {
    if factor_k.iter().all(BigInt::is_zero) || k >= d {
        return Ok(false);
    }
    let m_q = monomial_count(d - k);
    let dim = monomial_count(d);
    // Columns 0..m_q are `factor_k * m_j`, last column is `poly_d`: check if kernel has last coord != 0!
    let mut cols: Vec<Vec<BigInt>> = Vec::with_capacity(m_q + 1);
    for j in 0..m_q {
        let mut unit = vec![BigInt::zero(); m_q];
        unit[j] = BigInt::one();
        cols.push(mul_homog_poly(k, factor_k, d - k, &unit));
    }
    cols.push(poly_d.to_vec());
    let mut rows = vec![vec![BigInt::zero(); m_q + 1]; dim];
    for r in 0..dim {
        for c in 0..=m_q {
            rows[r][c] = cols[c][r].clone();
        }
    }
    let kern = integer_kernel_basis(&rows, m_q + 1)?;
    Ok(kern.iter().any(|v| !v[m_q].is_zero()))
}

/// Audit whether `poly_d` over `Z` degenerates into a reducible curve over `Q`
/// (`L_{ij} * C_{d-1}`, `Q_{1..5} * C_{d-2}`, or `Sym^2` pencil of cubics at `d=6, delta=8`).
pub fn is_reducible_over_node_loci(
    d: usize,
    poly_d: &[BigInt],
    nodes: &[PlaneCubicPoint],
) -> Result<(bool, &'static str), String> {
    if poly_d.iter().all(BigInt::is_zero) {
        return Ok((true, "zero-polynomial"));
    }
    // 1. Check divisibility by every secant line L_{ij} = P_i x P_j between pairs of nodes.
    let exps1 = degree_d_exponents(1); // [(1,0,0), (0,1,0), (0,0,1)]
    let _ = exps1;
    for i in 0..nodes.len() {
        for j in (i + 1)..nodes.len() {
            let a = &nodes[i].coordinates;
            let b = &nodes[j].coordinates;
            let line = primitivize_vec(vec![
                &a[1] * &b[2] - &a[2] * &b[1],
                &a[2] * &b[0] - &a[0] * &b[2],
                &a[0] * &b[1] - &a[1] * &b[0],
            ]);
            if line.iter().any(|v| !v.is_zero()) && divides_over_q(d, poly_d, 1, &line)? {
                return Ok((true, "secant-line-times-residual (L * C')"));
            }
        }
    }
    // 2. If nodes.len() >= 5 and d >= 4, check divisibility by any conic through 5 nodes.
    if nodes.len() >= 5 && d >= 4 {
        let exps2 = degree_d_exponents(2);
        let rows2: Vec<Vec<BigInt>> = nodes[..5]
            .iter()
            .map(|pt| {
                let [x, y, z] = &pt.coordinates;
                incidence_row_deg_d(&exps2, x, y, z)
            })
            .collect();
        let k2 = integer_kernel_basis(&rows2, 6)?;
        for conic in k2 {
            let prim_q = primitivize_vec(conic);
            if divides_over_q(d, poly_d, 2, &prim_q)? {
                return Ok((true, "node-conic-times-residual (Q_2 * C')"));
            }
        }
    }
    // 3. If d == 6 and nodes.len() >= 8, check whether poly_6 lies in Sym^2(ker_Q B_3(nodes[..8]))
    // (quadratic binary form a C_0^2 + b C_0 C_1 + c C_1^2, which factors into two cubics!).
    if d == 6 && nodes.len() >= 8 {
        let exps3 = degree_d_exponents(3);
        let rows3: Vec<Vec<BigInt>> = nodes[..8]
            .iter()
            .map(|pt| {
                let [x, y, z] = &pt.coordinates;
                incidence_row_deg_d(&exps3, x, y, z)
            })
            .collect();
        let k3 = integer_kernel_basis(&rows3, 10)?;
        if k3.len() == 2 {
            let c00 = mul_homog_poly(3, &k3[0], 3, &k3[0]);
            let c01 = mul_homog_poly(3, &k3[0], 3, &k3[1]);
            let c11 = mul_homog_poly(3, &k3[1], 3, &k3[1]);
            let r_sym = rank_over_q(&[c00.clone(), c01.clone(), c11.clone()], 28)?;
            let r_aug = rank_over_q(&[c00, c01, c11, poly_d.to_vec()], 28)?;
            if r_aug == r_sym {
                return Ok((true, "halphen-cubic-pencil-product (Sym^2 ker B_3)"));
            }
        }
    }
    Ok((false, "irreducible"))
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct NodalCellAuditRow {
    pub degree_d: usize,
    pub nodes_delta: usize,
    pub simple_points_s: usize,
    pub total_source_points: usize,
    pub target_geometric_genus: isize,
    pub placement: String,
    pub projective_params_nd: usize,
    pub node_linear_conditions: usize,
    pub free_projective_params_after_nodes: isize,
    pub general_mod_p_congruence_conditions_3d: usize,
    pub trials: usize,
    pub int_kernel_dim: usize,
    pub nonzero_mod_p_lifts: usize,
    pub zero_mod_p_degeneracies: usize,
    pub e_divides_c_mod_p_count: usize,
    pub lll_shortest_reducible_count: usize,
    pub lll_shortest_irreducible_valid_count: usize,
    pub dominant_outcome: String,
    pub median_shortest_valid_coef_bits: Option<u64>,
}

/// Audit one `(d, delta, s, placement)` configuration across `trials` on `F_p`.
#[allow(clippy::too_many_arguments)]
pub fn audit_nodal_bezout_configuration(
    p: u64,
    d: usize,
    delta: usize,
    simple_s: usize,
    on_base_nodes: bool,
    enforce_explicit_mod_p: bool,
    trials: usize,
    seed: u64,
) -> Result<NodalCellAuditRow, String> {
    let inst = find_prime_order_curve(p)?;
    let p_big = BigInt::from(inst.p);
    let n_big = BigInt::from(inst.order);
    let curve = PrimeWeierstrass::new(p_big.clone(), BigInt::from(inst.a), BigInt::from(inst.b))?;
    let gen = EcPoint::Affine(
        BigInt::from(inst.generator[0]),
        BigInt::from(inst.generator[1]),
    );
    let source_cubic_jksst = curve.source_cubic_coefficients();
    let exps_d = degree_d_exponents(d);
    let m_d = monomial_count(d);

    let mut rng = SplitMix64::new(seed ^ ((d as u64) << 16) ^ ((delta as u64) << 8) ^ p);
    let mut ops = 0u64;

    let mut last_kern_dim = 0usize;
    let mut nonzero_mod_p = 0usize;
    let mut zero_mod_p = 0usize;
    let mut e_div_count = 0usize;
    let mut reducible_count = 0usize;
    let mut irreducible_valid_count = 0usize;
    let mut valid_bits: Vec<u64> = Vec::new();
    let mut last_reason: &'static str = "none";

    for _t in 0..trials {
        let needed_curve_pts = if on_base_nodes {
            (delta + simple_s).max(4)
        } else {
            simple_s.max(4)
        };
        let mut src_pts: Vec<[BigInt; 3]> = Vec::with_capacity(needed_curve_pts);
        let mut seen_x: HashSet<BigInt> = HashSet::new();
        let cur_k = BigInt::one() + rng.uniform_below(&(&n_big - 1u64));
        let mut cur_pt = curve.scalar_mul(&cur_k, &gen, &mut ops)?;
        let stride = BigInt::from(7u64 + (rng.next_u64() % 29));
        let step_pt = curve.scalar_mul(&stride, &gen, &mut ops)?;

        let mut guard = 0usize;
        while src_pts.len() < needed_curve_pts && guard < needed_curve_pts * 8 {
            guard += 1;
            cur_pt = curve.add(&cur_pt, &step_pt, &mut ops)?;
            if let EcPoint::Affine(px, py) = &cur_pt {
                if seen_x.insert(px.clone()) {
                    src_pts.push([px.clone(), py.clone(), BigInt::one()]);
                }
            }
        }
        if src_pts.len() < needed_curve_pts {
            continue;
        }
        let Ok(frame) =
            jksst_projective_frame_mod_p(&p_big, &source_cubic_jksst, &src_pts, [0, 1, 2, 3])
        else {
            continue;
        };
        let cubic_grlex = jksst_cubic_to_grlex(&frame.transformed_source_cubic);

        // Lift curve points in frame.
        let mut lifted_curve_pts: Vec<PlaneCubicPoint> = Vec::with_capacity(needed_curve_pts);
        for (idx, pt_m) in frame.transformed_points_mod_p.iter().enumerate() {
            let lpt = if idx < 4 {
                PlaneCubicPoint::new(pt_m.clone())?
            } else {
                lift_projective_point_lll(pt_m, &p_big)?
            };
            lifted_curve_pts.push(lpt);
        }

        // Construct nodes (either on-base lifted_curve_pts[0..delta] or off-base points not on E'_src mod p).
        let mut node_pts: Vec<PlaneCubicPoint> = Vec::with_capacity(delta);
        if on_base_nodes {
            for pt in lifted_curve_pts.iter().take(delta) {
                node_pts.push(pt.clone());
            }
        } else {
            let exps3 = degree_d_exponents(3);
            let mut cand_seed = 2i64 + (_t as i64) * 3;
            while node_pts.len() < delta {
                let qx = BigInt::from(cand_seed);
                let qy = BigInt::from(cand_seed * 2 + 1);
                let qz = BigInt::from(1 + (cand_seed % 5));
                cand_seed += 1;
                let Ok(qpt) = PlaneCubicPoint::new([qx, qy, qz]) else {
                    continue;
                };
                if node_pts.contains(&qpt) {
                    continue;
                }
                let val_e = dot_bigint(
                    &incidence_row_deg_d(
                        &exps3,
                        &qpt.coordinates[0],
                        &qpt.coordinates[1],
                        &qpt.coordinates[2],
                    ),
                    &cubic_grlex,
                )
                .mod_floor(&p_big);
                if !val_e.is_zero() {
                    node_pts.push(qpt);
                }
            }
        }

        let simple_pts: Vec<PlaneCubicPoint> = if on_base_nodes {
            lifted_curve_pts[delta..(delta + simple_s)].to_vec()
        } else {
            lifted_curve_pts[..simple_s].to_vec()
        };

        let mut constraint_rows: Vec<Vec<BigInt>> = Vec::new();
        for npt in &node_pts {
            let [x, y, z] = &npt.coordinates;
            constraint_rows.extend(node_constraint_rows_deg_d(&exps_d, x, y, z));
        }
        for spt in &simple_pts {
            let [x, y, z] = &spt.coordinates;
            constraint_rows.push(incidence_row_deg_d(&exps_d, x, y, z));
        }

        let kern = integer_kernel_basis(&constraint_rows, m_d)?;
        last_kern_dim = kern.len();
        if kern.is_empty() {
            last_reason = "empty-Z-kernel (overconstrained)";
            continue;
        }

        let (mut sublattice, has_nz_mod_p) = if enforce_explicit_mod_p {
            let target_mults = multiples_of_cubic_basis_mod_p(d, &cubic_grlex, &p_big);
            subspace_congruence_sublattice(&kern, &target_mults, &p_big)?
        } else {
            (kern, true)
        };

        if !has_nz_mod_p {
            zero_mod_p += 1;
            last_reason = "all congruent lifts satisfy C == 0 mod p";
            continue;
        }

        lll_reduce_hp(&mut sublattice, 0.99).map_err(str::to_string)?;
        let shortest = primitivize_vec(sublattice[0].clone());
        if shortest.iter().all(|v| v.mod_floor(&p_big).is_zero()) {
            zero_mod_p += 1;
            last_reason = "shortest LLL vector is 0 mod p";
            continue;
        }
        nonzero_mod_p += 1;

        let e_div = is_divisible_by_cubic_mod_p(d, &shortest, &cubic_grlex, &p_big);
        if e_div {
            e_div_count += 1;
        }
        let (is_red, reason) = is_reducible_over_node_loci(d, &shortest, &node_pts)?;
        last_reason = reason;
        if is_red {
            reducible_count += 1;
        } else if e_div {
            irreducible_valid_count += 1;
            valid_bits.push(max_vec_bits(&shortest));
        }
    }

    valid_bits.sort_unstable();
    let med_bits = if valid_bits.is_empty() {
        None
    } else {
        Some(valid_bits[valid_bits.len() / 2])
    };

    Ok(NodalCellAuditRow {
        degree_d: d,
        nodes_delta: delta,
        simple_points_s: simple_s,
        total_source_points: if on_base_nodes {
            delta + simple_s
        } else {
            simple_s
        },
        target_geometric_genus: smooth_plane_genus(d) - (delta as isize),
        placement: if on_base_nodes {
            format!(
                "on-base [2]-multiplicity ({})",
                if enforce_explicit_mod_p {
                    "explicit E|C mod p"
                } else {
                    "pure Bezout >3d"
                }
            )
        } else {
            "off-base nodes (explicit E|C mod p)".into()
        },
        projective_params_nd: projective_param_count(d),
        node_linear_conditions: 3 * delta,
        free_projective_params_after_nodes: projective_param_count(d) as isize
            - (3 * delta) as isize,
        general_mod_p_congruence_conditions_3d: 3 * d,
        trials,
        int_kernel_dim: last_kern_dim,
        nonzero_mod_p_lifts: nonzero_mod_p,
        zero_mod_p_degeneracies: zero_mod_p,
        e_divides_c_mod_p_count: e_div_count,
        lll_shortest_reducible_count: reducible_count,
        lll_shortest_irreducible_valid_count: irreducible_valid_count,
        dominant_outcome: last_reason.into(),
        median_shortest_valid_coef_bits: med_bits,
    })
}

// ============================================================================
// Surviving Irreducible Nodal Bezout Cell `(d=4, delta=1, s=11 => g=2, r=12)`:
// Birational projection from node `P_1 = (1:0:0)` to `W^2 = F_6(t)`,
// odd-degree Cantor Mumford Jacobian arithmetic over `F_q`, multi-prime
// subgroup-kernel LLL, and exact `Q[t]` norm principal-divisor certification!
// ============================================================================

/// Genus-2 hyperelliptic curve `W^2 = sum_{m=0}^6 f[m] * t^m` projected from a 1-nodal quartic.
#[derive(Clone, Debug)]
pub struct NodalQuarticGenus2Projection {
    /// Coefficients `[f_0, f_1, ..., f_6]` of `F_6(t)` (`t = Y / Z`).
    pub f_coeffs: [BigInt; 7],
    /// Tangent-cone discriminant `a_11^2 - 4 a_20 a_02` at node `(1:0:0)` (`!= 0` => ordinary node).
    pub node_tangent_disc: BigInt,
    /// Projected rational points `(t_i, w_i)` on `W^2 = F_6(t)` for `P_3..P_12` (`Z_i != 0`).
    pub affine_points: Vec<(BigRational, BigRational)>,
    /// Indices in the 12-point tuple corresponding to `affine_points` (`2..12`).
    pub source_point_indices: Vec<usize>,
}

/// Project a quartic `C(X, Y, Z)` (in `degree_d_exponents(4)` order) with a node at `P_0 = (1:0:0)`
/// to `W^2 = B_3(t, 1)^2 - 4 A_2(t, 1) D_4(t, 1)`.
pub fn project_1nodal_quartic_to_genus2(
    quartic_grlex: &[BigInt],
    lifted_points: &[PlaneCubicPoint],
) -> Result<NodalQuarticGenus2Projection, String> {
    let exps4 = degree_d_exponents(4);
    let idx_of = |ex: usize, ey: usize, ez: usize| -> usize {
        exps4.iter().position(|&e| e == (ex, ey, ez)).unwrap()
    };
    // Verify node at (1:0:0): X^4, X^3 Y, X^3 Z must be 0!
    if !quartic_grlex[idx_of(4, 0, 0)].is_zero()
        || !quartic_grlex[idx_of(3, 1, 0)].is_zero()
        || !quartic_grlex[idx_of(3, 0, 1)].is_zero()
    {
        return Err("quartic does not have a node at (1:0:0)".into());
    }
    // A_2(t) = a0 + a1 t + a2 t^2 (where t = Y / Z)
    let a = [
        quartic_grlex[idx_of(2, 0, 2)].clone(),
        quartic_grlex[idx_of(2, 1, 1)].clone(),
        quartic_grlex[idx_of(2, 2, 0)].clone(),
    ];
    let b = [
        quartic_grlex[idx_of(1, 0, 3)].clone(),
        quartic_grlex[idx_of(1, 1, 2)].clone(),
        quartic_grlex[idx_of(1, 2, 1)].clone(),
        quartic_grlex[idx_of(1, 3, 0)].clone(),
    ];
    let d = [
        quartic_grlex[idx_of(0, 0, 4)].clone(),
        quartic_grlex[idx_of(0, 1, 3)].clone(),
        quartic_grlex[idx_of(0, 2, 2)].clone(),
        quartic_grlex[idx_of(0, 3, 1)].clone(),
        quartic_grlex[idx_of(0, 4, 0)].clone(),
    ];

    let node_tangent_disc = &a[1] * &a[1] - BigInt::from(4) * &a[2] * &a[0];
    if node_tangent_disc.is_zero() {
        return Err("cuspidal/degenerate tangent cone at (1:0:0)".into());
    }

    let mut f_coeffs: [BigInt; 7] = std::array::from_fn(|_| BigInt::zero());
    for i in 0..4 {
        for j in 0..4 {
            f_coeffs[i + j] += &b[i] * &b[j];
        }
    }
    for i in 0..3 {
        for j in 0..5 {
            f_coeffs[i + j] -= BigInt::from(4) * &a[i] * &d[j];
        }
    }

    let mut affine_points = Vec::new();
    let mut source_point_indices = Vec::new();
    for (idx, pt) in lifted_points.iter().enumerate() {
        if idx == 0 {
            continue; // Node (1:0:0)
        }
        let [x, y, z] = &pt.coordinates;
        if z.is_zero() {
            continue; // Skip Z = 0 points such as (0:1:0) at infinity
        }
        let t = BigRational::new(y.clone(), z.clone());
        let xr = BigRational::new(x.clone(), z.clone());
        let eval_poly = |cfs: &[BigInt], tr: &BigRational| -> BigRational {
            let mut acc = BigRational::zero();
            for (pow, cf) in cfs.iter().enumerate() {
                acc += BigRational::from_integer(cf.clone()) * tr.pow(pow as i32);
            }
            acc
        };
        let a_val = eval_poly(&a, &t);
        let b_val = eval_poly(&b, &t);
        let w = BigRational::from_integer(BigInt::from(2)) * a_val * xr + b_val;
        let f_val = eval_poly(&f_coeffs, &t);
        if &w * &w != f_val {
            return Err("internal error: projected genus-2 point failed W^2 == F_6(t)".into());
        }
        affine_points.push((t, w));
        source_point_indices.push(idx);
    }

    Ok(NodalQuarticGenus2Projection {
        f_coeffs,
        node_tangent_disc,
        affine_points,
        source_point_indices,
    })
}

// --- Polynomial helpers over `F_q` (`u64`) for odd-degree genus-2 Cantor Mumford arithmetic ---

fn trim_u64(mut p: Vec<u64>, q: u64) -> Vec<u64> {
    for c in &mut p {
        *c %= q;
    }
    while p.last().is_some_and(|&c| c == 0) {
        p.pop();
    }
    p
}

fn poly_add_mod(a: &[u64], b: &[u64], q: u64) -> Vec<u64> {
    let n = a.len().max(b.len());
    let mut out = vec![0u64; n];
    for (i, slot) in out.iter_mut().enumerate() {
        let va = a.get(i).copied().unwrap_or(0);
        let vb = b.get(i).copied().unwrap_or(0);
        *slot = (va + vb) % q;
    }
    trim_u64(out, q)
}

fn poly_sub_mod(a: &[u64], b: &[u64], q: u64) -> Vec<u64> {
    let n = a.len().max(b.len());
    let mut out = vec![0u64; n];
    for (i, slot) in out.iter_mut().enumerate() {
        let va = a.get(i).copied().unwrap_or(0);
        let vb = b.get(i).copied().unwrap_or(0);
        *slot = (va + q - (vb % q)) % q;
    }
    trim_u64(out, q)
}

fn poly_mul_mod(a: &[u64], b: &[u64], q: u64) -> Vec<u64> {
    if a.is_empty() || b.is_empty() {
        return Vec::new();
    }
    let mut out = vec![0u64; a.len() + b.len() - 1];
    for (i, &va) in a.iter().enumerate() {
        for (j, &vb) in b.iter().enumerate() {
            out[i + j] = (out[i + j] + mod_mul_u64(va, vb, q)) % q;
        }
    }
    trim_u64(out, q)
}

fn poly_div_rem_mod(num: &[u64], den: &[u64], q: u64) -> Option<(Vec<u64>, Vec<u64>)> {
    let den = trim_u64(den.to_vec(), q);
    if den.is_empty() {
        return None;
    }
    let mut rem = trim_u64(num.to_vec(), q);
    if rem.len() < den.len() {
        return Some((Vec::new(), rem));
    }
    let deg_d = den.len() - 1;
    let lead_inv = mod_inv_u64(den[deg_d], q)?;
    let mut quot = vec![0u64; rem.len() - den.len() + 1];
    while rem.len() >= den.len() && !rem.is_empty() {
        let deg_r = rem.len() - 1;
        let shift = deg_r - deg_d;
        let coeff = mod_mul_u64(rem[deg_r], lead_inv, q);
        quot[shift] = coeff;
        for (i, &dv) in den.iter().enumerate() {
            let sub = mod_mul_u64(coeff, dv, q);
            rem[shift + i] = (rem[shift + i] + q - sub) % q;
        }
        rem = trim_u64(rem, q);
    }
    Some((trim_u64(quot, q), rem))
}

fn poly_make_monic(mut p: Vec<u64>, q: u64) -> Option<Vec<u64>> {
    p = trim_u64(p, q);
    if p.is_empty() {
        return None;
    }
    let inv = mod_inv_u64(*p.last().unwrap(), q)?;
    for c in &mut p {
        *c = mod_mul_u64(*c, inv, q);
    }
    Some(p)
}

/// Extended polynomial GCD over `F_q`: returns `(monic_gcd, s, t)` with `s * a + t * b = monic_gcd`.
fn poly_xgcd_mod(a: &[u64], b: &[u64], q: u64) -> Option<(Vec<u64>, Vec<u64>, Vec<u64>)> {
    let mut r0 = trim_u64(a.to_vec(), q);
    let mut r1 = trim_u64(b.to_vec(), q);
    let mut s0 = vec![1u64];
    let mut s1: Vec<u64> = Vec::new();
    let mut t0: Vec<u64> = Vec::new();
    let mut t1 = vec![1u64];

    while !r1.is_empty() {
        let (quot, rem) = poly_div_rem_mod(&r0, &r1, q)?;
        let s2 = poly_sub_mod(&s0, &poly_mul_mod(&quot, &s1, q), q);
        let t2 = poly_sub_mod(&t0, &poly_mul_mod(&quot, &t1, q), q);
        r0 = r1;
        r1 = rem;
        s0 = s1;
        s1 = s2;
        t0 = t1;
        t1 = t2;
    }
    if r0.is_empty() {
        return None;
    }
    let inv = mod_inv_u64(*r0.last().unwrap(), q)?;
    let scale = |v: Vec<u64>| -> Vec<u64> {
        trim_u64(v.into_iter().map(|c| mod_mul_u64(c, inv, q)).collect(), q)
    };
    Some((scale(r0), scale(s0), scale(t0)))
}

/// Mumford divisor `(u(x), v(x))` (`u` monic of degree `<= 2`, `deg v < deg u`, `u | (v^2 - f)`)
/// on a smooth monic odd-degree genus-2 curve `y^2 = f(x)` (`deg f = 5`) over `F_q`.
#[derive(Clone, Debug, Eq, PartialEq, Hash)]
struct MumfordDivisor {
    u: Vec<u64>,
    v: Vec<u64>,
}

impl MumfordDivisor {
    fn identity() -> Self {
        Self {
            u: vec![1],
            v: Vec::new(),
        }
    }

    fn from_point(x: u64, y: u64, q: u64) -> Self {
        Self {
            u: vec![(q - (x % q)) % q, 1],
            v: trim_u64(vec![y % q], q),
        }
    }

    fn negate(&self, q: u64) -> Self {
        Self {
            u: self.u.clone(),
            v: trim_u64(self.v.iter().map(|&c| (q - (c % q)) % q).collect(), q),
        }
    }
}

/// Cantor composition + reduction on `y^2 = f_quintic(x)` (`deg = 5`, monic) over `F_q`.
fn cantor_add_genus2(
    d1: &MumfordDivisor,
    d2: &MumfordDivisor,
    f_quintic: &[u64],
    q: u64,
) -> Option<MumfordDivisor> {
    let (g1, e1, e2) = poly_xgcd_mod(&d1.u, &d2.u, q)?;
    let v_sum = poly_add_mod(&d1.v, &d2.v, q);
    let (d, c1, c2) = poly_xgcd_mod(&g1, &v_sum, q)?;
    let s1 = poly_mul_mod(&c1, &e1, q);
    let s2 = poly_mul_mod(&c1, &e2, q);
    let s3 = c2;

    let (u1_div_d, _) = poly_div_rem_mod(&d1.u, &d, q)?;
    let (u2_div_d, _) = poly_div_rem_mod(&d2.u, &d, q)?;
    let mut u = poly_mul_mod(&u1_div_d, &u2_div_d, q);
    u = poly_make_monic(u, q)?;

    let term1 = poly_mul_mod(&poly_mul_mod(&s1, &d1.u, q), &d2.v, q);
    let term2 = poly_mul_mod(&poly_mul_mod(&s2, &d2.u, q), &d1.v, q);
    let v1v2_f = poly_add_mod(&poly_mul_mod(&d1.v, &d2.v, q), f_quintic, q);
    let term3 = poly_mul_mod(&s3, &v1v2_f, q);
    let num_v = poly_add_mod(&poly_add_mod(&term1, &term2, q), &term3, q);
    let (v_div_d, _) = poly_div_rem_mod(&num_v, &d, q)?;
    let (_, mut v) = poly_div_rem_mod(&v_div_d, &u, q)?;

    // Reduction loop while deg(u) > 2 (since genus = 2).
    while u.len() > 3 {
        let f_minus_v2 = poly_sub_mod(f_quintic, &poly_mul_mod(&v, &v, q), q);
        let (u_next_raw, rem_check) = poly_div_rem_mod(&f_minus_v2, &u, q)?;
        if !rem_check.is_empty() {
            return None;
        }
        u = poly_make_monic(u_next_raw, q)?;
        let neg_v = trim_u64(v.iter().map(|&c| (q - (c % q)) % q).collect(), q);
        let (_, v_next) = poly_div_rem_mod(&neg_v, &u, q)?;
        v = v_next;
    }

    Some(MumfordDivisor { u, v })
}

fn eval_poly_u64(cfs: &[u64], x: u64, q: u64) -> u64 {
    let mut acc = 0u64;
    let mut xp = 1u64;
    for &c in cfs {
        acc = (acc + mod_mul_u64(c, xp, q)) % q;
        xp = mod_mul_u64(xp, x, q);
    }
    acc
}

/// Reduce `W^2 = F_6(t)` modulo a prime `q` where `F_6` is squarefree of degree 6 and has a root `alpha in F_q`,
/// transforming `(t, W)` into `(x, y)` on a smooth monic quintic `y^2 = f_5(x)` over `F_q`.
fn build_mod_q_quintic_jacobian_points(
    proj: &NodalQuarticGenus2Projection,
    q: u64,
) -> Option<(Vec<u64>, Vec<MumfordDivisor>)> {
    let qb = BigInt::from(q);
    if proj.node_tangent_disc.mod_floor(&qb).is_zero() {
        return None;
    }
    let mut f6 = [0u64; 7];
    for (slot, c) in f6.iter_mut().zip(&proj.f_coeffs) {
        *slot = c.mod_floor(&qb).to_u64()?;
    }
    if f6[6] == 0 {
        return None;
    }
    // Check squarefreeness of F_6 mod q: gcd(F_6, F_6') == 1!
    let mut df6 = [0u64; 6];
    for i in 1..=6 {
        df6[i - 1] = mod_mul_u64(i as u64, f6[i], q);
    }
    let (gcd_f, _, _) = poly_xgcd_mod(&f6, &df6, q)?;
    if gcd_f.len() != 1 {
        return None;
    }

    // Find a root alpha in F_q of F_6(alpha) == 0 mod q, avoiding all projected t_i mod q.
    let mut pts_mod: Vec<(u64, u64)> = Vec::with_capacity(proj.affine_points.len());
    for (tr, wr) in &proj.affine_points {
        let t_den = tr.denom().mod_floor(&qb).to_u64()?;
        let w_den = wr.denom().mod_floor(&qb).to_u64()?;
        let ti = mod_mul_u64(
            tr.numer().mod_floor(&qb).to_u64()?,
            mod_inv_u64(t_den, q)?,
            q,
        );
        let wi = mod_mul_u64(
            wr.numer().mod_floor(&qb).to_u64()?,
            mod_inv_u64(w_den, q)?,
            q,
        );
        pts_mod.push((ti, wi));
    }

    let alpha = (0..q)
        .find(|&a| eval_poly_u64(&f6, a, q) == 0 && pts_mod.iter().all(|&(ti, _)| ti != a))?;

    // Taylor shift F_6(alpha + s) = sum_{k=1}^6 taylor[k] * s^k (taylor[0] == 0).
    // Compute via Horner shift!
    let mut shifted = f6.to_vec();
    for step in 0..6 {
        for i in (step..6).rev() {
            shifted[i] = (shifted[i] + mod_mul_u64(alpha, shifted[i + 1], q)) % q;
        }
    }
    if shifted[0] != 0 || shifted[1] == 0 {
        return None;
    }
    // u = 1 / (t - alpha), w_tilde = u^3 * W => w_tilde^2 = sum_{k=1}^6 shifted[k] * u^(6 - k)
    // = c5 u^5 + c4 u^4 + c3 u^3 + c2 u^2 + c1 u + c0 where c_{6-k} = shifted[k]!
    let c5 = shifted[1];
    let c4 = shifted[2];
    let c3 = shifted[3];
    let c2 = shifted[4];
    let c1 = shifted[5];
    let c0 = shifted[6];

    let c5_2 = mod_mul_u64(c5, c5, q);
    let c5_3 = mod_mul_u64(c5_2, c5, q);
    let c5_4 = mod_mul_u64(c5_2, c5_2, q);
    // x = c5 * u, y = c5^2 * w_tilde => y^2 = x^5 + c4 x^4 + (c3 c5) x^3 + (c2 c5^2) x^2 + (c1 c5^3) x + (c0 c5^4).
    let f_quintic = vec![
        mod_mul_u64(c0, c5_4, q),
        mod_mul_u64(c1, c5_3, q),
        mod_mul_u64(c2, c5_2, q),
        mod_mul_u64(c3, c5, q),
        c4,
        1u64,
    ];

    let mut point_divs: Vec<MumfordDivisor> = Vec::with_capacity(pts_mod.len());
    for &(ti, wi) in &pts_mod {
        let u = mod_inv_u64((ti + q - alpha) % q, q)?;
        let u3 = mod_mul_u64(mod_mul_u64(u, u, q), u, q);
        let w_tilde = mod_mul_u64(u3, wi, q);
        let x = mod_mul_u64(c5, u, q);
        let y = mod_mul_u64(c5_2, w_tilde, q);
        if mod_mul_u64(y, y, q) != eval_poly_u64(&f_quintic, x, q) {
            return None;
        }
        point_divs.push(MumfordDivisor::from_point(x, y, q));
    }

    // Return difference divisors D_j = [P_{j} - P_0] for j = 1..pts_mod.len()!
    let base_neg = point_divs[0].negate(q);
    let mut diffs = Vec::with_capacity(point_divs.len() - 1);
    for pd in &point_divs[1..] {
        diffs.push(cantor_add_genus2(pd, &base_neg, &f_quintic, q)?);
    }
    Some((f_quintic, diffs))
}

/// Upper bound `(ceil(sqrt q) + 1)^4 + 16` on `#Jac(C)(F_q)` for genus 2, computed in exact
/// integer arithmetic and saturating at `u64::MAX` (the f64 form saturated and then wrapped).
fn hasse_weil_cap_genus2(q: u64) -> u64 {
    let r = crate::field_ec::isqrt_ceil_u128(q as u128) + 1;
    let cap = r.saturating_pow(4).saturating_add(16);
    u64::try_from(cap).unwrap_or(u64::MAX)
}

fn jacobian_relation_kernel_mod_q(
    f_quintic: &[u64],
    diffs: &[MumfordDivisor],
    q: u64,
    ops: &mut u64,
) -> Option<Vec<Vec<BigInt>>> {
    let r = diffs.len();
    // Hasse-Weil bound on #Jac(C)(F_q) for g = 2: (sqrt(q) + 1)^4.
    let hw_cap = hasse_weil_cap_genus2(q);
    let id = MumfordDivisor::identity();
    let mut subgroup: Vec<MumfordDivisor> = vec![id.clone()];
    let mut coords_of: HashMap<MumfordDivisor, Vec<BigInt>> = HashMap::new();
    coords_of.insert(id.clone(), vec![BigInt::zero(); r]);
    let mut kernel_rows: Vec<Vec<BigInt>> = Vec::with_capacity(r);

    for (k, dk) in diffs.iter().enumerate() {
        let mut cur = dk.clone();
        let mut m = 1u64;
        let mut multiples: Vec<MumfordDivisor> = vec![id.clone()];
        while !coords_of.contains_key(&cur) {
            multiples.push(cur.clone());
            cur = cantor_add_genus2(&cur, dk, f_quintic, q)?;
            *ops += 1;
            m += 1;
            if m > hw_cap || subgroup.len() as u64 > 250_000 {
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
            // Only expand full subgroup table if total size stays small; for g=2 #J(F_q) ~ q^2 ~ 70_000 at q=257,
            // which fits easily in < 10 MB! Cap at 120_000 elements for instant execution.
            if (subgroup.len() as u64) * m > 120_000 {
                return None;
            }
            let prev = subgroup.clone();
            for (t, t_div) in multiples.iter().enumerate().take(m as usize).skip(1) {
                let t_big = BigInt::from(t);
                for base_div in &prev {
                    let sum_div = if base_div == &id {
                        t_div.clone()
                    } else {
                        *ops += 1;
                        cantor_add_genus2(base_div, t_div, f_quintic, q)?
                    };
                    if !coords_of.contains_key(&sum_div) {
                        let mut rep = coords_of[base_div].clone();
                        rep[k] = t_big.clone();
                        coords_of.insert(sum_div.clone(), rep);
                        subgroup.push(sum_div);
                    }
                }
            }
        }
    }
    Some(kernel_rows)
}

/// Exact rational function-field principal-divisor certificate on `W^2 = F_6(t)`:
/// checks whether the zero-sum divisor `sum_j m_j [(t_j, w_j)]` (`sum m_j = 0`, distinct `t_j`,
/// `m_j` supported with `|m_j| <= 2`) is principal over `Q` by solving the exact `BigRational`
/// interpolation system for `p(t) + q(t) W` (`deg p <= M_+`, `deg q <= M_+ - 3`) and verifying
/// the polynomial norm identity `p(t)^2 - q(t)^2 F_6(t) == c * U_-(t) * U_+(t)` (`c != 0`)!
pub fn certify_genus2_zero_sum_relation_over_q(
    proj: &NodalQuarticGenus2Projection,
    m_weights: &[i64],
) -> bool {
    if m_weights.len() != proj.affine_points.len() {
        return false;
    }
    let sum_m: i64 = m_weights.iter().sum();
    if sum_m != 0 || m_weights.iter().all(|&x| x == 0) {
        return false;
    }
    let m_pos: usize = m_weights
        .iter()
        .filter(|&&x| x > 0)
        .map(|&x| x as usize)
        .sum();
    if !(3..=14).contains(&m_pos) {
        return false;
    }

    // Unknowns: p_0 .. p_{m_pos} (m_pos + 1 coeffs) and q_0 .. q_{m_pos - 3} (m_pos - 2 coeffs).
    let np = m_pos + 1;
    let nq = m_pos - 2;
    let nvars = np + nq;
    let f_rat: [BigRational; 7] =
        std::array::from_fn(|i| BigRational::from_integer(proj.f_coeffs[i].clone()));

    // Build exact linear equations over Q for multiplicity |m_j| at (t_j, +w_j) (if m_j > 0)
    // and at (t_j, -w_j) (if m_j < 0, so p(t) + q(t) W is divisible by U_-(t) in O(C)!).
    let mut eqs: Vec<Vec<BigRational>> = Vec::new();
    for (idx, &mj) in m_weights.iter().enumerate() {
        if mj == 0 {
            continue;
        }
        let mult = mj.unsigned_abs() as usize;
        let (tj, wj_raw) = &proj.affine_points[idx];
        let w0 = if mj > 0 {
            wj_raw.clone()
        } else {
            -wj_raw.clone()
        };
        if w0.is_zero() && mult > 1 {
            return false;
        }

        // Compute Taylor jet w(s) = w0 + w1 s + ... up to order `mult - 1` around t = tj + s
        // from w(s)^2 = F_6(tj + s)!
        let mut f_jet = vec![BigRational::zero(); mult];
        for (k, f_jet_slot) in f_jet.iter_mut().enumerate() {
            // k-th Taylor coeff of F_6 at tj:
            let mut ck = BigRational::zero();
            for (deg, f_coeff) in f_rat.iter().enumerate().skip(k) {
                // binom(deg, k) * f_rat[deg] * tj^(deg - k)
                let mut binom = 1u64;
                for r in 0..k {
                    binom = binom * ((deg - r) as u64) / ((r + 1) as u64);
                }
                ck += f_coeff
                    * BigRational::from_integer(BigInt::from(binom))
                    * tj.pow((deg - k) as i32);
            }
            *f_jet_slot = ck;
        }
        let mut w_jet = vec![BigRational::zero(); mult];
        w_jet[0] = w0.clone();
        for k in 1..mult {
            let mut conv = BigRational::zero();
            for a in 1..k {
                conv += &w_jet[a] * &w_jet[k - a];
            }
            w_jet[k] = (&f_jet[k] - conv) / (BigRational::from_integer(BigInt::from(2)) * &w0);
        }

        // Order `ord` condition (0 <= ord < mult) on p(tj + s) + q(tj + s) * w(s) = 0:
        for ord in 0..mult {
            let mut row = vec![BigRational::zero(); nvars];
            for (i, row_slot) in row.iter_mut().enumerate().take(np).skip(ord) {
                let mut binom = 1u64;
                for r in 0..ord {
                    binom = binom * ((i - r) as u64) / ((r + 1) as u64);
                }
                *row_slot =
                    BigRational::from_integer(BigInt::from(binom)) * tj.pow((i - ord) as i32);
            }
            for j in 0..nq {
                let mut acc = BigRational::zero();
                for u in 0..=ord.min(j) {
                    let mut binom = 1u64;
                    for r in 0..u {
                        binom = binom * ((j - r) as u64) / ((r + 1) as u64);
                    }
                    acc += BigRational::from_integer(BigInt::from(binom))
                        * tj.pow((j - u) as i32)
                        * &w_jet[ord - u];
                }
                row[np + j] = acc;
            }
            eqs.push(row);
        }
    }

    // RREF over BigRational to extract nullspace of `eqs`.
    let nrows = eqs.len();
    let mut piv_cols = Vec::new();
    let mut r_idx = 0usize;
    for col in 0..nvars {
        let Some(piv) = (r_idx..nrows).find(|&r| !eqs[r][col].is_zero()) else {
            continue;
        };
        eqs.swap(r_idx, piv);
        let inv = BigRational::one() / &eqs[r_idx][col];
        for v in &mut eqs[r_idx][col..nvars] {
            *v *= &inv;
        }
        let piv_row = eqs[r_idx].clone();
        for (r, eq_row) in eqs.iter_mut().enumerate() {
            if r == r_idx || eq_row[col].is_zero() {
                continue;
            }
            let fac = eq_row[col].clone();
            for (slot, pv) in eq_row[col..nvars].iter_mut().zip(&piv_row[col..nvars]) {
                let sub = &fac * pv;
                *slot -= sub;
            }
        }
        piv_cols.push(col);
        r_idx += 1;
        if r_idx == nrows {
            break;
        }
    }

    let free_cols: Vec<usize> = (0..nvars).filter(|c| !piv_cols.contains(c)).collect();
    if free_cols.is_empty() {
        return false;
    }

    // Construct U_-(t) * U_+(t) = prod_j (t - t_j)^|m_j| of degree 2 * m_pos.
    let poly_mul_r = |a: &[BigRational], b: &[BigRational]| -> Vec<BigRational> {
        if a.is_empty() || b.is_empty() {
            return Vec::new();
        }
        let mut out = vec![BigRational::zero(); a.len() + b.len() - 1];
        for (i, va) in a.iter().enumerate() {
            for (j, vb) in b.iter().enumerate() {
                out[i + j] += va * vb;
            }
        }
        out
    };
    let mut u_prod = vec![BigRational::one()];
    for (idx, &mj) in m_weights.iter().enumerate() {
        let mult = mj.unsigned_abs() as usize;
        let lin = vec![-proj.affine_points[idx].0.clone(), BigRational::one()];
        for _ in 0..mult {
            u_prod = poly_mul_r(&u_prod, &lin);
        }
    }

    // Test every nullspace basis vector (generically dim 1 when principal!).
    for &fc in &free_cols {
        let mut sol = vec![BigRational::zero(); nvars];
        sol[fc] = BigRational::one();
        for (row_pos, &pc) in piv_cols.iter().enumerate() {
            sol[pc] = -eqs[row_pos][fc].clone();
        }
        let p_poly = &sol[..np];
        let q_poly = &sol[np..];
        let p2 = poly_mul_r(p_poly, p_poly);
        let q2 = poly_mul_r(q_poly, q_poly);
        let q2f = poly_mul_r(&q2, &f_rat);
        let max_len = p2.len().max(q2f.len());
        let mut norm_poly = vec![BigRational::zero(); max_len];
        for (i, slot) in norm_poly.iter_mut().enumerate() {
            let vp = p2.get(i).cloned().unwrap_or_else(BigRational::zero);
            let vq = q2f.get(i).cloned().unwrap_or_else(BigRational::zero);
            *slot = vp - vq;
        }
        while norm_poly.last().is_some_and(BigRational::is_zero) {
            norm_poly.pop();
        }
        if norm_poly.len() == u_prod.len() {
            let lead_c = norm_poly.last().unwrap().clone(); // u_prod is monic!
            if !lead_c.is_zero()
                && norm_poly
                    .iter()
                    .zip(&u_prod)
                    .all(|(nv, uv)| nv == &(&lead_c * uv))
            {
                return true;
            }
        }
    }
    false
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Genus2NodalYieldRow {
    pub p: u64,
    pub bits: f64,
    pub group_order: u64,
    pub trials: usize,
    pub irreducible_bezout_lifts: usize,
    pub e_divides_c_mod_p_verified: usize,
    pub genus2_projections_built: usize,
    pub median_quartic_coef_bits: u64,
    pub median_sextic_f6_bits: u64,
    pub jacobian_kernel_trials_completed: usize,
    pub certified_genus2_relations: usize,
    pub solved_and_verified: bool,
    pub pollard_rho: PollardRhoReceipt,
}

/// Benchmark the surviving irreducible `(d=4, delta=1, s=11 => g=2, r=12)` nodal Bezout family
/// end-to-end on `E(F_p)`.
pub fn run_1nodal_quartic_genus2_yield(
    p: u64,
    trials: usize,
    seed: u64,
) -> Result<Genus2NodalYieldRow, String> {
    let inst = find_prime_order_curve(p)?;
    let p_big = BigInt::from(inst.p);
    let n_big = BigInt::from(inst.order);
    let curve = PrimeWeierstrass::new(p_big.clone(), BigInt::from(inst.a), BigInt::from(inst.b))?;
    let gen = EcPoint::Affine(
        BigInt::from(inst.generator[0]),
        BigInt::from(inst.generator[1]),
    );
    let secret_x = BigInt::from((inst.order * 29 + 11) % (inst.order - 2) + 2);
    let mut ops = 0u64;
    let target_q = curve.scalar_mul(&secret_x, &gen, &mut ops)?;
    let rho = solve_pollard_rho_single_target(&curve, &gen, &n_big, &target_q, seed ^ 0x7B7B)?;

    let source_cubic = curve.source_cubic_coefficients();
    let exps4 = degree_d_exponents(4);
    let mut rng = SplitMix64::new(seed ^ 0x4112 ^ p);

    let mut irred_lifts = 0usize;
    let mut ediv_ok = 0usize;
    let mut g2_built = 0usize;
    let mut jac_completed = 0usize;
    let mut cert_rels = 0usize;
    let mut solved = false;
    let mut q_bits_vec = Vec::new();
    let mut f6_bits_vec = Vec::new();

    for _t in 0..trials {
        // Draw 12 distinct fresh-masked points in <G>.
        let mut pts_src: Vec<[BigInt; 3]> = Vec::with_capacity(12);
        let mut u_vec: Vec<BigInt> = Vec::with_capacity(12);
        let mut v_vec: Vec<BigInt> = Vec::with_capacity(12);
        let mut seen_x: HashSet<BigInt> = HashSet::new();

        let mut guard = 0usize;
        while pts_src.len() < 12 && guard < 128 {
            guard += 1;
            let u = BigInt::one() + rng.uniform_below(&(&n_big - 1u64));
            let v = rng.uniform_below(&n_big);
            let pt = curve.add(
                &curve.scalar_mul(&u, &gen, &mut ops)?,
                &curve.scalar_mul(&v, &target_q, &mut ops)?,
                &mut ops,
            )?;
            if let EcPoint::Affine(px, py) = pt {
                if seen_x.insert(px.clone()) {
                    pts_src.push([px, py, BigInt::one()]);
                    u_vec.push(u);
                    v_vec.push(v);
                }
            }
        }
        if pts_src.len() < 12 {
            continue;
        }
        let Ok(frame) = jksst_projective_frame_mod_p(&p_big, &source_cubic, &pts_src, [0, 1, 2, 3])
        else {
            continue;
        };
        let mut lifted: Vec<PlaneCubicPoint> = Vec::with_capacity(12);
        for (idx, pm) in frame.transformed_points_mod_p.iter().enumerate() {
            let lpt = if idx < 4 {
                PlaneCubicPoint::new(pm.clone())?
            } else {
                lift_projective_point_lll(pm, &p_big)?
            };
            lifted.push(lpt);
        }
        if !collinear_point_triples(&lifted).is_empty() {
            continue;
        }

        // Node at lifted[0] = (1:0:0), simple points at lifted[1..12] (11 simple points => 3 + 11 = 14 eqs in 15 vars!).
        let mut rows: Vec<Vec<BigInt>> = Vec::with_capacity(15);
        rows.extend(node_constraint_rows_deg_d(
            &exps4,
            &lifted[0].coordinates[0],
            &lifted[0].coordinates[1],
            &lifted[0].coordinates[2],
        ));
        for pt in &lifted[1..] {
            rows.push(incidence_row_deg_d(
                &exps4,
                &pt.coordinates[0],
                &pt.coordinates[1],
                &pt.coordinates[2],
            ));
        }
        let kern = integer_kernel_basis(&rows, 15)?;
        if kern.len() != 1 {
            continue;
        }
        let quartic = primitivize_vec(kern[0].clone());
        let cubic_grlex = jksst_cubic_to_grlex(&frame.transformed_source_cubic);
        let e_div = is_divisible_by_cubic_mod_p(4, &quartic, &cubic_grlex, &p_big);
        if e_div {
            ediv_ok += 1;
        }
        let (is_red, _) = is_reducible_over_node_loci(4, &quartic, &[lifted[0].clone()])?;
        if is_red || !e_div {
            continue;
        }
        irred_lifts += 1;
        q_bits_vec.push(max_vec_bits(&quartic));

        let Ok(proj) = project_1nodal_quartic_to_genus2(&quartic, &lifted) else {
            continue;
        };
        if proj.affine_points.len() < 6 {
            continue;
        }
        g2_built += 1;
        f6_bits_vec.push(max_vec_bits(&proj.f_coeffs));

        // Multi-prime genus-2 Jacobian kernel intersection + LLL across 4 good primes with F_q root!
        let r_jac = proj.affine_points.len() - 1;
        let mut lattice: Option<Vec<Vec<BigInt>>> = None;
        let mut used_q = 0usize;
        let mut jac_ops = 0u64;
        for &q_aux in JAC_AUX_PRIMES {
            if used_q >= 4 {
                break;
            }
            if q_aux == p {
                continue;
            }
            let Some((f_quintic, diffs)) = build_mod_q_quintic_jacobian_points(&proj, q_aux) else {
                continue;
            };
            let Some(kern_q) =
                jacobian_relation_kernel_mod_q(&f_quintic, &diffs, q_aux, &mut jac_ops)
            else {
                continue;
            };
            lattice = Some(match lattice {
                None => row_hermite_basis(kern_q, r_jac),
                Some(prev) => intersect_full_rank_lattices(&prev, &kern_q, r_jac)?,
            });
            used_q += 1;
        }
        let Some(mut basis) = lattice else {
            continue;
        };
        if used_q < 3 {
            continue;
        }
        jac_completed += 1;
        lll_reduce_hp(&mut basis, 0.99).map_err(str::to_string)?;

        for row in &basis {
            let Some(rel_diffs): Option<Vec<i64>> = row.iter().map(ToPrimitive::to_i64).collect()
            else {
                continue;
            };
            if rel_diffs.iter().all(|&x| x == 0) || rel_diffs.iter().any(|&x| x.abs() > 2) {
                continue;
            }
            let s_diff: i64 = rel_diffs.iter().sum();
            if s_diff.abs() > 2 {
                continue;
            }
            let mut m_weights = Vec::with_capacity(r_jac + 1);
            m_weights.push(-s_diff);
            m_weights.extend_from_slice(&rel_diffs);
            if certify_genus2_zero_sum_relation_over_q(&proj, &m_weights) {
                cert_rels += 1;
                // Specialize zero-sum relation sum_k m_weights[k] * P_{source_idx[k]} = O_E!
                let mut cu = BigInt::zero();
                let mut cv = BigInt::zero();
                for (mw, &sidx) in m_weights.iter().zip(&proj.source_point_indices) {
                    cu = (&cu + BigInt::from(*mw) * &u_vec[sidx]).mod_floor(&n_big);
                    cv = (&cv + BigInt::from(*mw) * &v_vec[sidx]).mod_floor(&n_big);
                }
                if !cv.is_zero() {
                    if let Ok(inv) = mod_inv_bigint(&cv, &n_big) {
                        let cand_x = ((-cu) * inv).mod_floor(&n_big);
                        let mut vops = 0u64;
                        if curve.scalar_mul(&cand_x, &gen, &mut vops)? == target_q {
                            solved = true;
                        }
                    }
                }
            }
        }
    }

    q_bits_vec.sort_unstable();
    f6_bits_vec.sort_unstable();

    Ok(Genus2NodalYieldRow {
        p,
        bits: (p as f64).log2(),
        group_order: inst.order,
        trials,
        irreducible_bezout_lifts: irred_lifts,
        e_divides_c_mod_p_verified: ediv_ok,
        genus2_projections_built: g2_built,
        median_quartic_coef_bits: q_bits_vec.get(q_bits_vec.len() / 2).copied().unwrap_or(0),
        median_sextic_f6_bits: f6_bits_vec.get(f6_bits_vec.len() / 2).copied().unwrap_or(0),
        jacobian_kernel_trials_completed: jac_completed,
        certified_genus2_relations: cert_rels,
        solved_and_verified: solved,
        pollard_rho: rho,
    })
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Escape7bSummary {
    pub parameter_and_degeneracy_table: Vec<NodalCellAuditRow>,
    pub genus2_1nodal_quartic_yield: Vec<Genus2NodalYieldRow>,
}

pub fn run_escape_7b_suite(seed: u64) -> Result<Escape7bSummary, String> {
    let p_audit = 1021u64;
    let trials_audit = 25usize;
    let cells = vec![
        // (d=4, delta=2 => g=1): off-base vs on-base (s=0 and s=6)
        audit_nodal_bezout_configuration(p_audit, 4, 2, 0, false, true, trials_audit, seed)?,
        audit_nodal_bezout_configuration(p_audit, 4, 2, 6, true, true, trials_audit, seed)?,
        // (d=4, delta=1 => g=2): off-base vs on-base pure Bezout (s=11, r_total=12)
        audit_nodal_bezout_configuration(p_audit, 4, 1, 0, false, true, trials_audit, seed)?,
        audit_nodal_bezout_configuration(p_audit, 4, 1, 11, true, false, trials_audit, seed)?,
        // (d=5, delta=5 => g=1): off-base vs on-base (s=4, r_total=9) and (s=5, r_total=10)
        audit_nodal_bezout_configuration(p_audit, 5, 5, 0, false, true, trials_audit, seed)?,
        audit_nodal_bezout_configuration(p_audit, 5, 5, 4, true, true, trials_audit, seed)?,
        audit_nodal_bezout_configuration(p_audit, 5, 5, 5, true, true, trials_audit, seed)?,
        // (d=6, delta=8 => g=2): off-base vs on-base (s=0, r_total=8)
        audit_nodal_bezout_configuration(p_audit, 6, 8, 0, false, true, trials_audit, seed)?,
        audit_nodal_bezout_configuration(p_audit, 6, 8, 0, true, true, trials_audit, seed)?,
    ];

    let mut g2_rows = Vec::new();
    for &p in &[251u64, 509, 1021, 2039] {
        g2_rows.push(run_1nodal_quartic_genus2_yield(p, 20, seed)?);
    }

    Ok(Escape7bSummary {
        parameter_and_degeneracy_table: cells,
        genus2_1nodal_quartic_yield: g2_rows,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hasse_weil_cap_does_not_wrap_for_large_q() {
        assert_eq!(hasse_weil_cap_genus2(1021), 33u64.pow(4) + 16);
        for q in [1u64 << 40, (1u64 << 53) + 5, 1u64 << 62, u64::MAX] {
            let cap = hasse_weil_cap_genus2(q);
            assert!(cap >= 1 << 60, "q={q} cap={cap}");
        }
        assert_eq!(hasse_weil_cap_genus2(u64::MAX), u64::MAX);
    }

    #[test]
    fn off_base_nodes_force_zero_mod_p_while_on_base_1nodal_quartic_is_irreducible_bezout() {
        let off_d4_del2 =
            audit_nodal_bezout_configuration(1021, 4, 2, 0, false, true, 5, 2026_1119).unwrap();
        assert_eq!(off_d4_del2.zero_mod_p_degeneracies, 5);
        assert_eq!(off_d4_del2.nonzero_mod_p_lifts, 0);

        let on_d4_del1 =
            audit_nodal_bezout_configuration(1021, 4, 1, 11, true, false, 5, 2026_1119).unwrap();
        assert_eq!(on_d4_del1.e_divides_c_mod_p_count, 5);
        assert_eq!(on_d4_del1.lll_shortest_irreducible_valid_count, 5);
    }

    #[test]
    fn planted_principal_divisor_on_genus2_sextic_passes_exact_norm_certificate() {
        // Construct W^2 = F_6(t) = (1 + t + t^3)^2 - (t - 1)(t - 2)(t - 3)(t + 1)(t + 2)(t + 3)
        // where p(t) - W = (1 + t + t^3) - W vanishes at the 6 points t in {-3,-2,-1,1,2,3}
        // with w(t) = +(1 + t + t^3)!
        // Equivalently, (1 + t + t^3 - W) / ((t - 1)(t - 2)(t - 3)) has divisor
        // (-3, +w(-3)) + (-2, +w(-2)) + (-1, +w(-1)) - (1, -w(1)) - (2, -w(2)) - (3, -w(3))!
        let poly_mul_i = |a: &[i64], b: &[i64]| -> Vec<i64> {
            let mut out = vec![0i64; a.len() + b.len() - 1];
            for (i, &va) in a.iter().enumerate() {
                for (j, &vb) in b.iter().enumerate() {
                    out[i + j] += va * vb;
                }
            }
            out
        };
        let mut u6 = vec![1i64];
        for r in [-3i64, -2, -1, 1, 2, 3] {
            u6 = poly_mul_i(&u6, &[-r, 1]);
        }
        let p3 = vec![1i64, 1, 0, 1];
        let p3_sq = poly_mul_i(&p3, &p3);
        let f_coeffs: [BigInt; 7] = std::array::from_fn(|i| BigInt::from(p3_sq[i] - u6[i]));

        let w_at =
            |t: i64| -> BigRational { BigRational::from_integer(BigInt::from(1 + t + t * t * t)) };
        let pts = vec![
            (BigRational::from_integer(BigInt::from(-3)), w_at(-3)),
            (BigRational::from_integer(BigInt::from(-2)), w_at(-2)),
            (BigRational::from_integer(BigInt::from(-1)), w_at(-1)),
            (BigRational::from_integer(BigInt::from(1)), -w_at(1)),
            (BigRational::from_integer(BigInt::from(2)), -w_at(2)),
            (BigRational::from_integer(BigInt::from(3)), -w_at(3)),
        ];
        let proj = NodalQuarticGenus2Projection {
            f_coeffs,
            node_tangent_disc: BigInt::one(),
            affine_points: pts,
            source_point_indices: vec![2, 3, 4, 5, 6, 7],
        };
        assert!(certify_genus2_zero_sum_relation_over_q(
            &proj,
            &[1, 1, 1, -1, -1, -1]
        ));
        assert!(!certify_genus2_zero_sum_relation_over_q(
            &proj,
            &[1, 1, -1, -1, 0, 0]
        ));
    }
}
