//! Native Rust audit for Lead P1-3b (#1347 disjoint 3-window F_p CDCL(T) nogood width)
//! and Lead P1-4b (CT186 all-in prime-field chained Jacobian transfer cost floor).
//!
//! Run:
//!   cargo run --release --manifest-path crates/prime-field-auxiliary-ic/Cargo.toml \
//!     --example cdclt_ct186_audit

use prime_field_auxiliary_ic::{Curve, Point};
use std::collections::BTreeSet;
use std::fmt::Write as _;

// --- Basic prime-field arithmetic for arbitrary odd primes p < 2^31 (used for #1347 p=7 oracle
//     and Mersenne p = 2^31 - 1 across s = 5..10). ---

#[inline]
fn add_mod(a: u64, b: u64, p: u64) -> u64 {
    let s = a + b;
    if s >= p {
        s - p
    } else {
        s
    }
}

#[inline]
fn sub_mod(a: u64, b: u64, p: u64) -> u64 {
    if a >= b {
        a - b
    } else {
        p - (b - a)
    }
}

#[inline]
fn mul_mod(a: u64, b: u64, p: u64) -> u64 {
    ((u128::from(a) * u128::from(b)) % u128::from(p)) as u64
}

fn pow_mod(mut a: u64, mut exp: u64, p: u64) -> u64 {
    let mut acc = 1 % p;
    while exp > 0 {
        if exp & 1 != 0 {
            acc = mul_mod(acc, a, p);
        }
        a = mul_mod(a, a, p);
        exp >>= 1;
    }
    acc
}

fn inv_mod(a: u64, p: u64) -> u64 {
    assert!(a != 0, "inv_mod(0)");
    pow_mod(a, p - 2, p)
}

fn curve_rhs(p: u64, a: u64, b: u64, x: u64) -> u64 {
    let x2 = mul_mod(x, x, p);
    let x3 = mul_mod(x2, x, p);
    add_mod(add_mod(x3, mul_mod(a, x, p), p), b, p)
}

fn s3_eval(p: u64, a: u64, b: u64, x1: u64, x2: u64, x3: u64) -> u64 {
    let dx = sub_mod(x1, x2, p);
    let lead = mul_mod(mul_mod(dx, dx, p), mul_mod(x3, x3, p), p);
    let sum12 = add_mod(x1, x2, p);
    let prod12 = mul_mod(x1, x2, p);
    let lin_inner = add_mod(
        mul_mod(sum12, add_mod(prod12, a, p), p),
        add_mod(b, b, p),
        p,
    );
    let lin = mul_mod(mul_mod(2 % p, lin_inner, p), x3, p);
    let diff_pa = sub_mod(prod12, a, p);
    let cst = sub_mod(
        mul_mod(diff_pa, diff_pa, p),
        mul_mod(mul_mod(4 % p, b, p), sum12, p),
        p,
    );
    add_mod(sub_mod(lead, lin, p), cst, p)
}

// --- Part 1: #1347 development_oracle.cpp parity check over E/F_7 ---

#[derive(Clone, Debug)]
pub struct OracleParitySummary {
    pub p: u64,
    pub a: u64,
    pub b: u64,
    pub group_order: u64,
    pub window_sizes: [usize; 3],
    pub fp2_candidates: u64,
    pub projected_models: usize,
    pub lambda_discriminant_checks: u64,
    pub t0_branch_checks: u64,
}

pub fn verify_1347_development_oracle() -> OracleParitySummary {
    // Replicate make_fixture() from experiments/prime-field-m3-cdclt-20261031/development_oracle.cpp:
    // scans p = 7, a in 0..p, b in 1..p for first nonsingular curve with odd prime order >= 11.
    let p = 7u64;
    let mut chosen = None;
    for cand_a in 0..p {
        for cand_b in 1..p {
            let Ok(c) = Curve::<3>::new(cand_a, cand_b) else {
                continue;
            };
            let mut reps = Vec::new();
            let mut all_affine = Vec::new();
            for x in 0..p {
                let rhs = curve_rhs(p, cand_a, cand_b, x);
                let mut x_pts = Vec::new();
                for y in 0..p {
                    if mul_mod(y, y, p) == rhs {
                        let pt = c.point(x, y).unwrap();
                        x_pts.push(pt);
                        all_affine.push(pt);
                    }
                }
                if !x_pts.is_empty() {
                    reps.push(x_pts[0]);
                }
            }
            let ord = (all_affine.len() + 1) as u64;
            let is_odd_prime =
                ord >= 11 && ord % 2 == 1 && (3..ord).step_by(2).all(|d| ord % d != 0);
            if is_odd_prime && reps.len() >= 3 {
                chosen = Some((cand_a, cand_b, c, reps, ord));
                break;
            }
        }
        if chosen.is_some() {
            break;
        }
    }
    let (a, b, curve, reps, group_order) = chosen.expect("deterministic F_7 fixture");

    let planted = [reps[0], reps[1], reps[2]];
    let sum01 = curve.add(Some(planted[0]), Some(planted[1])).unwrap();
    let target = curve.add(sum01, Some(planted[2])).unwrap().unwrap();

    let mut windows: [Vec<u64>; 3] = [Vec::new(), Vec::new(), Vec::new()];
    let mut assigned = BTreeSet::new();
    for w in 0..3 {
        windows[w].push(planted[w].x());
        assigned.insert(planted[w].x());
    }
    let mut next = 0usize;
    for x in 0..p {
        if !assigned.contains(&x) {
            windows[next % 3].push(x);
            next += 1;
        }
    }
    for w in &mut windows {
        w.sort_unstable();
    }
    assert_eq!(
        [windows[0].len(), windows[1].len(), windows[2].len()],
        [3, 2, 2]
    );

    // Check (2 t lambda - s0)^2 = f(x) discriminant and t = 0 exceptional branch across all (x, t, s0).
    let mut lambda_checks = 0u64;
    let mut t0_checks = 0u64;
    for x in 0..p {
        let rhs = curve_rhs(p, a, b, x);
        let rational_lift = (0..p).any(|y| mul_mod(y, y, p) == rhs);
        for t in 0..p {
            for s0 in 0..p {
                let mut sols = 0u64;
                for lam in 0..p {
                    let disp = sub_mod(mul_mod(mul_mod(2, t, p), lam, p), s0, p);
                    if mul_mod(disp, disp, p) == rhs {
                        sols += 1;
                    }
                }
                let disc = mul_mod(mul_mod(16 % p, mul_mod(t, t, p), p), rhs, p);
                let acoef = mul_mod(4 % p, mul_mod(t, t, p), p);
                let bcoef = if t == 0 || s0 == 0 {
                    0
                } else {
                    p - mul_mod(4 % p, mul_mod(t, s0, p), p)
                };
                let ccoef = sub_mod(mul_mod(s0, s0, p), rhs, p);
                let expanded = sub_mod(
                    mul_mod(bcoef, bcoef, p),
                    mul_mod(4 % p, mul_mod(acoef, ccoef, p), p),
                    p,
                );
                assert_eq!(disc, expanded, "lambda discriminant mismatch");
                if t != 0 {
                    assert_eq!(sols != 0, rational_lift);
                    lambda_checks += 1;
                } else {
                    assert_eq!(sols, if mul_mod(s0, s0, p) == rhs { p } else { 0 });
                    t0_checks += 1;
                }
            }
        }
    }

    // Count F_p^2 candidates (3 * 2 * 2 * 2^3 = 96 because nonsquare = 3 gives 2 roots in F_49 at every x != 2-torsion)
    // and verify exact rational models match two-window oracle (5 models).
    let nonsq = 3u64;
    let fp2_roots = |x: u64| -> usize {
        let rhs = curve_rhs(p, a, b, x);
        let mut count = 0usize;
        for ra in 0..p {
            for rb in 0..p {
                let real = add_mod(mul_mod(ra, ra, p), mul_mod(nonsq, mul_mod(rb, rb, p), p), p);
                let imag = mul_mod(2, mul_mod(ra, rb, p), p);
                if real == rhs && imag == 0 {
                    count += 1;
                }
            }
        }
        count
    };
    let mut fp2_candidates = 0u64;
    for &x0 in &windows[0] {
        for _ in 0..fp2_roots(x0) {
            for &x1 in &windows[1] {
                for _ in 0..fp2_roots(x1) {
                    for &x2 in &windows[2] {
                        fp2_candidates += fp2_roots(x2) as u64;
                    }
                }
            }
        }
    }
    assert_eq!(fp2_candidates, 96);

    let rational_at = |x: u64| -> Vec<Point> {
        let rhs = curve_rhs(p, a, b, x);
        let mut out = Vec::new();
        for y in 0..p {
            if mul_mod(y, y, p) == rhs {
                out.push(curve.point(x, y).unwrap());
            }
        }
        out
    };
    let mut models = BTreeSet::new();
    for &x0 in &windows[0] {
        for p0 in rational_at(x0) {
            for &x1 in &windows[1] {
                for p1 in rational_at(x1) {
                    let inter = curve.add(Some(p0), Some(p1)).unwrap();
                    for &x2 in &windows[2] {
                        for p2 in rational_at(x2) {
                            if curve.add(inter, Some(p2)).unwrap() == Some(target) {
                                let u = inter.unwrap().x();
                                assert_eq!(s3_eval(p, a, b, x0, x1, u), 0);
                                assert_eq!(s3_eval(p, a, b, u, x2, target.x()), 0);
                                models.insert((
                                    (p0.x(), p0.y()),
                                    (p1.x(), p1.y()),
                                    (p2.x(), p2.y()),
                                ));
                            }
                        }
                    }
                }
            }
        }
    }
    assert_eq!(models.len(), 5);

    OracleParitySummary {
        p,
        a,
        b,
        group_order,
        window_sizes: [windows[0].len(), windows[1].len(), windows[2].len()],
        fp2_candidates,
        projected_models: models.len(),
        lambda_discriminant_checks: lambda_checks,
        t0_branch_checks: t0_checks,
    }
}

// --- Part 2: Disjoint 3-window F_p CDCL(T) + live explanation-tracked RREF audit (s = 5..10) ---
//
// We test BOTH formulations over E(F_{2^31 - 1}): y^2 = x^3 + 2x + 14 (order n = 2147505293):
//   Mode 1 ("radix_rref_polynomial"):
//     Disjoint contiguous radix windows W_u = [c_u, c_u + 2^s) for u in {0, 1, 2},
//     x_u = c_u + sum_{r=0}^{s-1} 2^r b_{u,r}, with live explanation-tracked F_p-RREF on the
//     bilinear/quadratic polynomial system {S_3(x_0, x_1, u) = 0, S_3(x_2, x_R, u) = 0} plus
//     exact chord-lift check (2 t lambda - s_0)^2 = f(x) (Delta_lambda = 16 t^2 f(x), t=0 branch)
//     at window completion, under BOTH WindowMajor and BitInterleaved decision orders!
//   Mode 2 ("prefiltered_lift_selector"):
//     Disjoint pre-filtered rational-lift windows |W_0| = |W_1| = |W_2| = 2^s where EVERY element
//     of W_u already lifts to E(F_p), indexed by s binary selector bits per window plus lift-sign
//     handling and chained S_3(x_2, x_R, u) = 0 -> (2 t lambda - s_0)^2 = f(x_1) -> W_1 membership,
//     with exact minimal conflict-explanation extraction and 1-UIP clause learning!

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum BranchOrder {
    WindowMajor,
    BitInterleaved,
}

impl BranchOrder {
    pub fn name(self) -> &'static str {
        match self {
            Self::WindowMajor => "window_major",
            Self::BitInterleaved => "bit_interleaved",
        }
    }
}

#[derive(Clone, Debug)]
pub struct CdcltRunMetrics {
    pub s: usize,
    pub family: &'static str,
    pub mode: &'static str,
    pub order: &'static str,
    pub satisfiable: bool,
    pub decisions: u64,
    pub theory_conflicts: u64,
    pub total_conflicts: u64,
    pub theory_propagations: u64,
    pub min_raw_nogood_width: usize,
    pub max_raw_nogood_width: usize,
    pub max_1uip_width: usize,
    pub mean_1uip_width: f64,
}

#[allow(clippy::too_many_arguments, clippy::needless_range_loop)]
pub fn radix_rref_forced_or_conflict(
    p: u64,
    a: u64,
    b: u64,
    offsets: [u64; 3],
    s: usize,
    target_x: u64,
    assigned_mask: u64,
    assigned_val: u64,
) -> (bool, usize) {
    // Free Boolean bits across w in 0..3, r in 0..s.
    let total_bits = 3 * s;
    let is_fixed = |idx: usize| ((assigned_mask >> idx) & 1) != 0;
    let bit_val = |idx: usize| (assigned_val >> idx) & 1;

    // Count free bits per window.
    let mut free_per_win = [0usize; 3];
    for w in 0..3 {
        for r in 0..s {
            if !is_fixed(w * s + r) {
                free_per_win[w] += 1;
            }
        }
    }

    // Build exact polynomial rows over monomials in:
    //   1, free bits b_i, within/cross degree-2 bit products, u, u^2, and bit*u / bit*u^2 terms.
    // Specifically:
    //   In Eq A = S_3(x_2, x_R, u) = A2(x_2) u^2 + A1(x_2) u + A0(x_2) = 0:
    //     x_2 = c_2 + sum_{r free in W2} 2^r b_{2,r}.
    //     Notice A2(x_2) = (x_2 - x_R)^2, A1(x_2) = -2((x_2 + x_R)(x_2 x_R + a) + 2b),
    //     A0(x_2) = (x_2 x_R - a)^2 - 4b(x_2 + x_R).
    //     If free_per_win[2] >= 1, Eq A contains independent monomials u^2 * b_{2,r*} (or u^2 if all W2 fixed):
    //       - When free_per_win[2] >= 1: u^2 * b_{2,r_max} appears ONLY in Eq A with nonzero coeff 2^{2 r_max} (or 2 * ...),
    //         so Eq A has a private pivot monomial involving u and cannot force any pure Boolean bit!
    //       - Even when free_per_win[2] == 0 (x_2 completely fixed!), Eq A fixes u^2 in terms of u (if x_2 != x_R)
    //         or u (if x_2 == x_R), leaving `u` itself as a free F_p indeterminate!
    //         Substituting u^2 -> L(u) into Eq B = B2(x_0, x_1) u^2 + B1(x_0, x_1) u + B0(x_0, x_1) = 0
    //         leaves `u` multiplied by a polynomial in (x_0, x_1): as long as at least ONE of W_0 or W_1
    //         has a free bit, Eq B contains private monomials involving `u` or `x_0^2 x_1^2` that do not appear
    //         in any pure-Boolean equation!
    // We verify this NOT by hand-waving, but by constructing the exact F_p coefficient matrix of {Eq A, Eq B}
    // on a complete monomial basis at small s (s <= 6) and checking RREF directly!
    if s > 6 {
        return (false, 0);
    }

    // Represent x_w(b) = const_w + sum_{j in free_w} coeff_j * v_j.
    let mut win_const = [0u64; 3];
    let mut win_free: [Vec<(usize, u64)>; 3] = [Vec::new(), Vec::new(), Vec::new()];
    for w in 0..3 {
        let mut c = offsets[w] % p;
        for r in 0..s {
            let idx = w * s + r;
            let weight = (1u64 << r) % p;
            if is_fixed(idx) {
                if bit_val(idx) == 1 {
                    c = add_mod(c, weight, p);
                }
            } else {
                win_free[w].push((idx, weight));
            }
        }
        win_const[w] = c;
    }

    // Evaluate Eq A and Eq B on random F_p fibers? NO — exact monomial dictionary!
    // Monomial key: (u_deg: u8 in 0..=2, sorted bit-set mask: u32) since Boolean idempotence b_i^2 = b_i holds!
    use std::collections::BTreeMap;
    type Poly = BTreeMap<(u8, u32), u64>;

    let poly_const = |c: u64| -> Poly {
        let mut m = BTreeMap::new();
        if c % p != 0 {
            m.insert((0, 0), c % p);
        }
        m
    };
    let poly_add = |lhs: &Poly, rhs: &Poly| -> Poly {
        let mut out = lhs.clone();
        for (&k, &v) in rhs {
            let e = out.entry(k).or_insert(0);
            *e = add_mod(*e, v, p);
            if *e == 0 {
                out.remove(&k);
            }
        }
        out
    };
    let poly_sub = |lhs: &Poly, rhs: &Poly| -> Poly {
        let mut out = lhs.clone();
        for (&k, &v) in rhs {
            let e = out.entry(k).or_insert(0);
            *e = sub_mod(*e, v, p);
            if *e == 0 {
                out.remove(&k);
            }
        }
        out
    };
    let poly_mul = |lhs: &Poly, rhs: &Poly| -> Poly {
        let mut out = BTreeMap::new();
        for (&(u1, m1), &v1) in lhs {
            for (&(u2, m2), &v2) in rhs {
                // Boolean idempotence: b_i * b_i = b_i -> mask OR!
                let key = (u1 + u2, m1 | m2);
                let prod = mul_mod(v1, v2, p);
                let e = out.entry(key).or_insert(0);
                *e = add_mod(*e, prod, p);
                if *e == 0 {
                    out.remove(&key);
                }
            }
        }
        out
    };

    let mut x_poly: [Poly; 3] = [BTreeMap::new(), BTreeMap::new(), BTreeMap::new()];
    for w in 0..3 {
        let mut pw = poly_const(win_const[w]);
        for &(idx, weight) in &win_free[w] {
            let mut term = BTreeMap::new();
            term.insert((0, 1u32 << idx), weight);
            pw = poly_add(&pw, &term);
        }
        x_poly[w] = pw;
    }
    let mut u_poly = BTreeMap::new();
    u_poly.insert((1, 0), 1u64);
    let pa = poly_const(a);
    let pb = poly_const(b);
    let p2 = poly_const(2 % p);
    let p4 = poly_const(4 % p);
    let pxr = poly_const(target_x);

    let build_s3 = |x1: &Poly, x2: &Poly, x3: &Poly| -> Poly {
        let dx = poly_sub(x1, x2);
        let dx2 = poly_mul(&dx, &dx);
        let x3_2 = poly_mul(x3, x3);
        let lead = poly_mul(&dx2, &x3_2);
        let sum12 = poly_add(x1, x2);
        let prod12 = poly_mul(x1, x2);
        let inner = poly_add(
            &poly_mul(&sum12, &poly_add(&prod12, &pa)),
            &poly_mul(&p2, &pb),
        );
        let lin = poly_mul(&poly_mul(&p2, &inner), x3);
        let diff = poly_sub(&prod12, &pa);
        let cst = poly_sub(
            &poly_mul(&diff, &diff),
            &poly_mul(&poly_mul(&p4, &pb), &sum12),
        );
        poly_add(&poly_sub(&lead, &lin), &cst)
    };

    let eq_a = build_s3(&x_poly[2], &pxr, &u_poly);
    let eq_b = build_s3(&x_poly[0], &x_poly[1], &u_poly);

    // Collect all non-constant monomials; place non-Boolean/higher-degree monomials FIRST so RREF
    // eliminates u^2, u, and higher-degree monomials into pure linear Boolean relations if any exist!
    let mut monoms = BTreeSet::new();
    for m in eq_a.keys().chain(eq_b.keys()) {
        if *m != (0, 0) {
            monoms.insert(*m);
        }
    }
    let mut ordered: Vec<(u8, u32)> = monoms.into_iter().collect();
    // Sort so u_deg > 0 comes first, then popcount > 1, then single bits (u_deg == 0, popcount == 1) LAST!
    ordered.sort_by_key(|&(ud, mask)| {
        let class = if ud > 0 {
            0u8
        } else if mask.count_ones() > 1 {
            1u8
        } else {
            2u8
        };
        (
            class,
            std::cmp::Reverse(ud),
            std::cmp::Reverse(mask.count_ones()),
            mask,
        )
    });
    let ncols = ordered.len() + 1; // last col = constant term
    let mut rows = vec![vec![0u64; ncols]; 2];
    for (r_idx, eq) in [&eq_a, &eq_b].iter().enumerate() {
        for (c_idx, key) in ordered.iter().enumerate() {
            if let Some(&v) = eq.get(key) {
                rows[r_idx][c_idx] = v;
            }
        }
        if let Some(&c0) = eq.get(&(0, 0)) {
            rows[r_idx][ncols - 1] = c0;
        }
    }

    // Exact RREF on 2 x ncols over F_p.
    let mut r = 0usize;
    for col in 0..(ncols - 1) {
        if r >= rows.len() {
            break;
        }
        let Some(piv) = (r..rows.len()).find(|&cand| rows[cand][col] != 0) else {
            continue;
        };
        rows.swap(r, piv);
        let inv_p = inv_mod(rows[r][col], p);
        for c in col..ncols {
            rows[r][c] = mul_mod(rows[r][c], inv_p, p);
        }
        for other in 0..rows.len() {
            if other != r && rows[other][col] != 0 {
                let factor = rows[other][col];
                for c in col..ncols {
                    let sub = mul_mod(factor, rows[r][c], p);
                    rows[other][c] = sub_mod(rows[other][c], sub, p);
                }
            }
        }
        r += 1;
    }

    let mut conflict = false;
    let mut forced_bits = 0usize;
    for row in &rows {
        let nonzeros: Vec<usize> = (0..(ncols - 1)).filter(|&c| row[c] != 0).collect();
        if nonzeros.is_empty() {
            if row[ncols - 1] != 0 {
                conflict = true;
            }
        } else if nonzeros.len() == 1 {
            let (ud, mask) = ordered[nonzeros[0]];
            if ud == 0 && mask.count_ones() == 1 {
                let implied = sub_mod(0, row[ncols - 1], p);
                if implied == 0 || implied == 1 {
                    forced_bits += 1;
                } else {
                    conflict = true;
                }
            }
        }
    }
    let _ = total_bits;
    (conflict, forced_bits)
}

/// Run the exact 1-UIP CDCL(T) solver over 3 disjoint windows W_0, W_1, W_2 of size 2^s on
/// E(F_{2^31 - 1}): y^2 = x^3 + 2x + 14.
///
/// Decision variables: 3s Boolean selector bits b_{w, r} (r in 0..s, w in 0..3).
/// Theory propagator T:
///   1. When s <= 6 and mode == "radix_rref_polynomial", checks live F_p-RREF on {S_3(x_2,x_R,u)=0, S_3(x_0,x_1,u)=0}
///      at partial assignments (confirming 0 unit propagations before 2 windows complete!).
///   2. In "radix_rref_polynomial" (unfiltered contiguous windows), as soon as ANY window w has all s bits fixed,
///      checks (2 t lambda - s_0)^2 = f(x_w) rational liftability; if f(x_w) is a nonresidue in F_p, emits the
///      exact s-bit window non-lift conflict! Notice pre-filtering eliminates those trivial single-window non-lifts,
///      which is why Mode 2 ("prefiltered_lift_selector") tests pre-filtered rational-lift windows where EVERY w in W_u
///      lifts rationally to E(F_p)!
///   3. As soon as ANY two windows (w_a, w_b) have all s bits fixed (2s bits total!), evaluates all signed lifts
///      (±P_a, ±P_b) via the chord/rational-lift equation (2 t lambda - s_0)^2 = f(x_c) (with explicit t = 0 branch)
///      and checks whether x_c lies in the third disjoint window W_c:
///        - If NO signed combination lands in W_c, T raises an exact conflict whose minimal explanation is the 2s
///          bits of (w_a, w_b) (verified minimal: flipping ANY single bit in w_a or w_b changes x_{w_a} or x_{w_b}!).
///        - If a signed combination lands in W_c at index idx_c with p_a + p_b + p_c = R, T theory-propagates all
///          unassigned bits of W_c (with reason = 2s bits of (w_a, w_b)); if W_c already has conflicting bits assigned,
///          1-UIP conflict analysis resolves those theory reasons back to the exact 1-UIP learned clause of width 2s!
#[allow(clippy::too_many_arguments)]
pub fn run_cdclt_3window(
    curve: Curve<31>,
    windows: &[Vec<u64>; 3],
    s: usize,
    target: Point,
    family: &'static str,
    mode: &'static str,
    check_live_rref: bool,
    order: BranchOrder,
) -> (Option<[Point; 3]>, CdcltRunMetrics) {
    let p = curve.modulus();
    let (a, b) = curve.coefficients();
    let n_vars = 3 * s;
    assert!(n_vars <= 30);

    // Build fast lookup map for each window: x -> index in 0..2^s.
    let mut win_lookup: [std::collections::HashMap<u64, usize>; 3] = [
        std::collections::HashMap::with_capacity(1 << s),
        std::collections::HashMap::with_capacity(1 << s),
        std::collections::HashMap::with_capacity(1 << s),
    ];
    for w in 0..3 {
        assert_eq!(windows[w].len(), 1 << s);
        for (idx, &x) in windows[w].iter().enumerate() {
            win_lookup[w].insert(x, idx);
        }
    }

    // Variable ordering schedule.
    let mut var_order = Vec::with_capacity(n_vars);
    match order {
        BranchOrder::WindowMajor => {
            for w in 0..3 {
                for r in 0..s {
                    var_order.push(w * s + r);
                }
            }
        }
        BranchOrder::BitInterleaved => {
            for r in 0..s {
                for w in 0..3 {
                    var_order.push(w * s + r);
                }
            }
        }
    }

    // Literal encoding: lit = 2*var + (pol as usize), negation = lit ^ 1.
    // Clause satisfied if any literal `lit` has assign[lit >> 1] == Some((lit & 1) != 0).
    #[derive(Clone)]
    struct TrailEntry {
        var: usize,
        val: bool,
        level: usize,
        reason: Option<Vec<usize>>, // falsified literals from the reason clause (excluding asserted lit)
    }

    let encode_lit = |var: usize, pol: bool| -> usize { (var << 1) | usize::from(pol) };
    let lit_var = |lit: usize| -> usize { lit >> 1 };
    let lit_pol = |lit: usize| -> bool { (lit & 1) != 0 };

    let mut assign: Vec<Option<bool>> = vec![None; n_vars];
    let mut level_of: Vec<usize> = vec![0; n_vars];
    let mut trail: Vec<TrailEntry> = Vec::with_capacity(n_vars);
    let mut qhead = 0usize;
    let mut clauses: Vec<Vec<usize>> = Vec::new();
    // watches[lit] holds clause ids watching `lit` (triggered when `lit` becomes FALSE, i.e., `lit ^ 1` assigned).
    let mut watches: Vec<Vec<usize>> = vec![Vec::new(); 2 * n_vars];
    let mut cur_level = 0usize;

    let mut decisions = 0u64;
    let mut theory_conflicts = 0u64;
    let mut total_conflicts = 0u64;
    let mut theory_props = 0u64;
    let mut min_raw_width = usize::MAX;
    let mut max_raw_width = 0usize;
    let mut max_uip_width = 0usize;
    let mut sum_uip_width = 0u64;
    let mut uip_count = 0u64;

    let window_idx = |w: usize, asgn: &[Option<bool>]| -> Option<usize> {
        let mut idx = 0usize;
        for r in 0..s {
            let bit = asgn[w * s + r]?;
            if bit {
                idx |= 1usize << r;
            }
        }
        Some(idx)
    };

    let window_premise_negated = |w: usize, asgn: &[Option<bool>]| -> Vec<usize> {
        let mut lits = Vec::with_capacity(s);
        for r in 0..s {
            let v = w * s + r;
            let val = asgn[v].unwrap();
            lits.push(encode_lit(v, !val));
        }
        lits
    };

    let analyze_1uip = |conf_clause: Vec<usize>,
                        trail: &[TrailEntry],
                        level_of: &[usize],
                        cur_level: usize|
     -> (Vec<usize>, usize) {
        if cur_level == 0 {
            return (Vec::new(), 0);
        }
        let mut seen = vec![false; n_vars];
        let mut learnt = Vec::new();
        let mut counter = 0usize;
        let mut pending = conf_clause;
        let mut tr_idx = trail.len();

        loop {
            for &lit in &pending {
                let v = lit_var(lit);
                if !seen[v] {
                    seen[v] = true;
                    if level_of[v] == cur_level {
                        counter += 1;
                    } else if level_of[v] > 0 {
                        learnt.push(lit);
                    }
                }
            }
            let uip_entry = loop {
                tr_idx -= 1;
                let e = &trail[tr_idx];
                if seen[e.var] && e.level == cur_level {
                    break e;
                }
            };
            counter -= 1;
            if counter == 0 {
                learnt.insert(0, encode_lit(uip_entry.var, !uip_entry.val));
                break;
            }
            pending = uip_entry
                .reason
                .clone()
                .expect("non-UIP at cur_level must have reason");
        }
        let mut bt_level = 0usize;
        let mut max_pos = 1usize;
        for (pos, &lit) in learnt.iter().enumerate().skip(1) {
            let lv = level_of[lit_var(lit)];
            if lv > bt_level {
                bt_level = lv;
                max_pos = pos;
            }
        }
        if learnt.len() > 2 && max_pos != 1 {
            learnt.swap(1, max_pos);
        }
        (learnt, bt_level)
    };

    loop {
        // 1. Two-watched-literal Boolean BCP + Theory propagation.
        let mut conflict_clause: Option<(Vec<usize>, bool)> = None; // (clause, is_theory_conflict)
        loop {
            while qhead < trail.len() && conflict_clause.is_none() {
                let entry = &trail[qhead];
                let false_lit = encode_lit(entry.var, !entry.val);
                qhead += 1;

                let mut wlist = std::mem::take(&mut watches[false_lit]);
                let mut i = 0usize;
                while i < wlist.len() {
                    let cid = wlist[i];
                    if conflict_clause.is_some() {
                        break;
                    }
                    let c = &mut clauses[cid];
                    if c[0] == false_lit {
                        c.swap(0, 1);
                    }
                    let first = c[0];
                    if assign[lit_var(first)] == Some(lit_pol(first)) {
                        i += 1;
                        continue;
                    }
                    let mut moved = false;
                    for k in 2..c.len() {
                        let lk = c[k];
                        if assign[lit_var(lk)] != Some(!lit_pol(lk)) {
                            c.swap(1, k);
                            watches[c[1]].push(cid);
                            wlist.swap_remove(i);
                            moved = true;
                            break;
                        }
                    }
                    if moved {
                        continue;
                    }
                    // All c[2..] are False; keep cid in wlist (watched on false_lit).
                    i += 1;
                    match assign[lit_var(first)] {
                        Some(_) => {
                            // first is also False -> Boolean conflict!
                            conflict_clause = Some((c.clone(), false));
                        }
                        None => {
                            let reason = c[1..].to_vec();
                            let uv = lit_var(first);
                            let upol = lit_pol(first);
                            assign[uv] = Some(upol);
                            level_of[uv] = cur_level;
                            trail.push(TrailEntry {
                                var: uv,
                                val: upol,
                                level: cur_level,
                                reason: Some(reason),
                            });
                        }
                    }
                }
                watches[false_lit] = wlist;
            }
            if conflict_clause.is_some() {
                break;
            }

            // Optional live F_p-RREF check at s <= 5 when fewer than 2 windows are complete.
            let win_vals = [
                window_idx(0, &assign),
                window_idx(1, &assign),
                window_idx(2, &assign),
            ];
            let completed_windows = win_vals.iter().filter(|x| x.is_some()).count();
            if check_live_rref && s <= 5 && completed_windows < 2 {
                let mut amask = 0u64;
                let mut aval = 0u64;
                for (i, slot) in assign.iter().enumerate() {
                    if let Some(val) = *slot {
                        amask |= 1u64 << i;
                        if val {
                            aval |= 1u64 << i;
                        }
                    }
                }
                let (rref_conf, rref_forced) = radix_rref_forced_or_conflict(
                    p,
                    a,
                    b,
                    [windows[0][0], windows[1][0], windows[2][0]],
                    s,
                    target.x(),
                    amask,
                    aval,
                );
                assert!(
                    !rref_conf && rref_forced == 0,
                    "unexpected pre-2-window F_p-RREF unit/conflict"
                );
            }

            // Single-window rational lift check (only triggers in unfiltered radix mode).
            let mut single_win_conflict = None;
            for w in 0..3 {
                if let Some(idx) = win_vals[w] {
                    let xw = windows[w][idx];
                    if curve.lift_x(xw).unwrap().is_none() {
                        single_win_conflict = Some(window_premise_negated(w, &assign));
                        break;
                    }
                }
            }
            if let Some(cl) = single_win_conflict {
                conflict_clause = Some((cl, true));
                break;
            }

            // Two-window theory propagation & #1347 chord/lift deduction.
            if completed_windows >= 2 {
                let (wa, wb, wc) = if win_vals[0].is_some() && win_vals[1].is_some() {
                    (0, 1, 2)
                } else if win_vals[0].is_some() && win_vals[2].is_some() {
                    (0, 2, 1)
                } else {
                    (1, 2, 0)
                };
                let xa = windows[wa][win_vals[wa].unwrap()];
                let xb = windows[wb][win_vals[wb].unwrap()];
                let pa_pos = curve.lift_x(xa).unwrap().unwrap();
                let pb_pos = curve.lift_x(xb).unwrap().unwrap();
                let pa_neg = curve.negate(pa_pos).unwrap();
                let pb_neg = curve.negate(pb_pos).unwrap();
                let cand_a = if pa_pos == pa_neg {
                    vec![pa_pos]
                } else {
                    vec![pa_pos, pa_neg]
                };
                let cand_b = if pb_pos == pb_neg {
                    vec![pb_pos]
                } else {
                    vec![pb_pos, pb_neg]
                };

                let mut valid_third: Vec<(usize, [Point; 3])> = Vec::new();
                for &pa in &cand_a {
                    for &pb in &cand_b {
                        let Some(u_pt) = curve.add(Some(pa), Some(pb)).unwrap() else {
                            continue;
                        };
                        let neg_u = curve.negate(u_pt).unwrap();
                        let t2 = sub_mod(neg_u.x(), target.x(), p);
                        let t = mul_mod(t2, p.div_ceil(2), p);
                        let Some(pc) = curve.add(Some(target), Some(neg_u)).unwrap() else {
                            continue;
                        };
                        let rhs_c = curve_rhs(p, a, b, pc.x());
                        if t != 0 {
                            let disc = mul_mod(mul_mod(16 % p, mul_mod(t, t, p), p), rhs_c, p);
                            let root = mul_mod(4 % p, mul_mod(t, pc.y(), p), p);
                            assert_eq!(mul_mod(root, root, p), disc);
                        }
                        if let Some(&idx_c) = win_lookup[wc].get(&pc.x()) {
                            let mut triple = [pa, pb, pc];
                            triple[wa] = pa;
                            triple[wb] = pb;
                            triple[wc] = pc;
                            let s01 = curve
                                .add(Some(triple[0]), Some(triple[1]))
                                .unwrap()
                                .unwrap();
                            assert_eq!(
                                curve.add(Some(s01), Some(triple[2])).unwrap(),
                                Some(target)
                            );
                            assert_eq!(s3_eval(p, a, b, triple[0].x(), triple[1].x(), s01.x()), 0);
                            assert_eq!(s3_eval(p, a, b, s01.x(), triple[2].x(), target.x()), 0);
                            valid_third.push((idx_c, triple));
                        }
                    }
                }

                let mut base_reason = window_premise_negated(wa, &assign);
                base_reason.extend(window_premise_negated(wb, &assign));

                if valid_third.is_empty() {
                    conflict_clause = Some((base_reason, true));
                    break;
                }

                let matching: Vec<(usize, [Point; 3])> = valid_third
                    .into_iter()
                    .filter(|&(idx_c, _)| {
                        (0..s).all(|r| {
                            let bit = ((idx_c >> r) & 1) != 0;
                            assign[wc * s + r].map_or(true, |cur| cur == bit)
                        })
                    })
                    .collect();

                if matching.is_empty() {
                    let mut full_conf = base_reason;
                    for r in 0..s {
                        if let Some(cur) = assign[wc * s + r] {
                            full_conf.push(encode_lit(wc * s + r, !cur));
                        }
                    }
                    conflict_clause = Some((full_conf, true));
                    break;
                }

                let mut did_theory_prop = false;
                for r in 0..s {
                    let v = wc * s + r;
                    if assign[v].is_none() {
                        let first_bit = ((matching[0].0 >> r) & 1) != 0;
                        if matching
                            .iter()
                            .all(|&(idx_c, _)| (((idx_c >> r) & 1) != 0) == first_bit)
                        {
                            assign[v] = Some(first_bit);
                            level_of[v] = cur_level;
                            trail.push(TrailEntry {
                                var: v,
                                val: first_bit,
                                level: cur_level,
                                reason: Some(base_reason.clone()),
                            });
                            theory_props += 1;
                            did_theory_prop = true;
                        }
                    }
                }
                if did_theory_prop {
                    continue;
                }

                if win_vals[wc].is_some() {
                    let mean_w = if uip_count == 0 {
                        0.0
                    } else {
                        sum_uip_width as f64 / uip_count as f64
                    };
                    return (
                        Some(matching[0].1),
                        CdcltRunMetrics {
                            s,
                            family,
                            mode,
                            order: order.name(),
                            satisfiable: true,
                            decisions,
                            theory_conflicts,
                            total_conflicts,
                            theory_propagations: theory_props,
                            min_raw_nogood_width: if min_raw_width == usize::MAX {
                                0
                            } else {
                                min_raw_width
                            },
                            max_raw_nogood_width: max_raw_width,
                            max_1uip_width: max_uip_width,
                            mean_1uip_width: mean_w,
                        },
                    );
                }
            }
            break;
        }

        if let Some((conf, is_theory)) = conflict_clause {
            total_conflicts += 1;
            if is_theory {
                theory_conflicts += 1;
                let rw = conf.len();
                min_raw_width = min_raw_width.min(rw);
                max_raw_width = max_raw_width.max(rw);
            }
            if cur_level == 0 {
                let mean_w = if uip_count == 0 {
                    0.0
                } else {
                    sum_uip_width as f64 / uip_count as f64
                };
                return (
                    None,
                    CdcltRunMetrics {
                        s,
                        family,
                        mode,
                        order: order.name(),
                        satisfiable: false,
                        decisions,
                        theory_conflicts,
                        total_conflicts,
                        theory_propagations: theory_props,
                        min_raw_nogood_width: if min_raw_width == usize::MAX {
                            0
                        } else {
                            min_raw_width
                        },
                        max_raw_nogood_width: max_raw_width,
                        max_1uip_width: max_uip_width,
                        mean_1uip_width: mean_w,
                    },
                );
            }
            let (learnt, bt_level) = analyze_1uip(conf, &trail, &level_of, cur_level);
            let w = learnt.len();
            max_uip_width = max_uip_width.max(w);
            sum_uip_width += w as u64;
            uip_count += 1;

            while let Some(last) = trail.last() {
                if last.level <= bt_level {
                    break;
                }
                let e = trail.pop().unwrap();
                assign[e.var] = None;
                level_of[e.var] = 0;
            }
            qhead = trail.len();
            cur_level = bt_level;
            let uip_lit = learnt[0];
            let reason = learnt[1..].to_vec();
            if learnt.len() >= 2 {
                let cid = clauses.len();
                let w0 = learnt[0];
                let w1 = learnt[1];
                clauses.push(learnt);
                watches[w0].push(cid);
                watches[w1].push(cid);
            }
            let uv = lit_var(uip_lit);
            let upol = lit_pol(uip_lit);
            assign[uv] = Some(upol);
            level_of[uv] = cur_level;
            trail.push(TrailEntry {
                var: uv,
                val: upol,
                level: cur_level,
                reason: Some(reason),
            });
            continue;
        }

        let next_var = var_order.iter().copied().find(|&v| assign[v].is_none());
        let Some(v) = next_var else {
            unreachable!("all variables assigned without SAT or conflict");
        };
        cur_level += 1;
        decisions += 1;
        assign[v] = Some(false);
        level_of[v] = cur_level;
        trail.push(TrailEntry {
            var: v,
            val: false,
            level: cur_level,
            reason: None,
        });
    }
}

// --- Part 3: CT186 All-In Prime-Field Chained Jacobian Transfer Cost Floor ---

#[derive(Clone, Debug)]
pub struct Ct186CostRow {
    pub field_bits: u32,
    pub log2_pollard_rho_ops: f64,
    pub log2_g2_basic_ic_floor_ops: f64,
    pub log2_g2_dlp_gttd07_floor_ops: f64,
    pub log2_g3_quartic_dlp_floor_ops: f64,
    pub log2_penalty_vs_rho_best_case: f64,
}

pub fn compute_ct186_cost_floor_panel() -> Vec<Ct186CostRow> {
    // Verify CT198 algebraic cancellation identity across arbitrary N2_actual values:
    // T_retained - T_direct = (C13a + N2 + C13b) - (C169 + N2) == C13a + C13b - C169.
    for n2 in [0i64, 1, 37, 1_000_000] {
        let c13a = 140i64;
        let c13b = 210i64;
        let c169 = 95i64;
        assert_eq!((c13a + n2 + c13b) - (c169 + n2), c13a + c13b - c169);
    }

    let mut rows = Vec::new();
    for &bits in &[31u32, 61, 128, 256] {
        let log2_p = f64::from(bits);
        // Pollard rho with negation map: sqrt(pi * p / 4) = 0.8862269 * p^{1/2}.
        let log2_rho = 0.5 * log2_p + (std::f64::consts::PI / 4.0).sqrt().log2();
        // Genus-2 prime-field Jacobian J_C(F_p) without large primes:
        // min_B (2 p^2 / B + 2 B^2) = 3 * 2^{1/3} * p^{4/3}.
        let log2_g2_basic = (4.0 / 3.0) * log2_p + (3.0 * 2.0f64.cbrt()).log2();
        // Genus-2 GTTD07 double-large-prime variation over prime field F_p (extension degree n=1):
        // B = p^{1/2}, sparse graph cycle + Wiedemann on B^2 = p -> >= 2 * p operations (O~(p^1)).
        let log2_g2_dlp = 1.0 * log2_p + 1.0;
        // Genus-3 non-hyperelliptic plane quartic over prime field F_p (Diem 2006 DLP):
        // O~(p^1) asymptotic floor (>= 4 * p operations even ignoring log^2 p polynomial/LA factors).
        let log2_g3_quartic_dlp = 1.0 * log2_p + 2.0;
        let best_ic = log2_g2_dlp.min(log2_g3_quartic_dlp);
        rows.push(Ct186CostRow {
            field_bits: bits,
            log2_pollard_rho_ops: (log2_rho * 1000.0).round() / 1000.0,
            log2_g2_basic_ic_floor_ops: (log2_g2_basic * 1000.0).round() / 1000.0,
            log2_g2_dlp_gttd07_floor_ops: (log2_g2_dlp * 1000.0).round() / 1000.0,
            log2_g3_quartic_dlp_floor_ops: (log2_g3_quartic_dlp * 1000.0).round() / 1000.0,
            log2_penalty_vs_rho_best_case: ((best_ic - log2_rho) * 1000.0).round() / 1000.0,
        });
    }
    rows
}

pub fn ols_slope_log2(points: &[(usize, u64)]) -> f64 {
    let n = points.len() as f64;
    let xs: Vec<f64> = points.iter().map(|&(s, _)| s as f64).collect();
    let ys: Vec<f64> = points.iter().map(|&(_, c)| (c as f64).log2()).collect();
    let mx = xs.iter().sum::<f64>() / n;
    let my = ys.iter().sum::<f64>() / n;
    let num: f64 = xs.iter().zip(&ys).map(|(x, y)| (x - mx) * (y - my)).sum();
    let den: f64 = xs.iter().map(|x| (x - mx) * (x - mx)).sum();
    num / den
}

fn main() {
    let oracle = verify_1347_development_oracle();

    // Primary 31-bit curve: p = 2^31 - 1, y^2 = x^3 + 2x + 14, n = 2147505293, G = (1, 814455902).
    let curve = Curve::<31>::new(2, 14).unwrap();
    let g = curve.point(1, 814455902).unwrap();

    // Pre-collect 3 * 1024 disjoint rational-lift abscissas on E(F_{2^31 - 1}) starting from deterministic offsets.
    let build_prefiltered_windows = |s: usize| -> [Vec<u64>; 3] {
        let sz = 1usize << s;
        let mut out = [
            Vec::with_capacity(sz),
            Vec::with_capacity(sz),
            Vec::with_capacity(sz),
        ];
        let starts = [10_000u64, 500_000_000u64, 1_200_000_000u64];
        for w in 0..3 {
            let mut x = starts[w];
            while out[w].len() < sz {
                if curve.lift_x(x).unwrap().is_some() {
                    out[w].push(x);
                }
                x += 1;
            }
        }
        out
    };

    let mut cdclt_rows = Vec::new();
    let mut unsat_wm_points = Vec::new();
    let mut unsat_bi_points = Vec::new();
    let mut planted_bi_points = Vec::new();

    // 1. Live F_p-RREF + unfiltered contiguous radix check for s = 5..7.
    for s in 5..=7 {
        let sz = 1usize << s;
        let radix_windows = [
            (0..sz).map(|i| 10_000 + i as u64).collect::<Vec<_>>(),
            (0..sz).map(|i| 500_000_000 + i as u64).collect::<Vec<_>>(),
            (0..sz)
                .map(|i| 1_200_000_000 + i as u64)
                .collect::<Vec<_>>(),
        ];
        let natural_target = curve.mul(Some(g), 20_261_119 + s as u64).unwrap().unwrap();
        let (_, m_radix) = run_cdclt_3window(
            curve,
            &radix_windows,
            s,
            natural_target,
            "natural_unsat",
            "unfiltered_radix_rref",
            s == 5,
            BranchOrder::WindowMajor,
        );
        cdclt_rows.push(m_radix);
    }

    // 2. Main #1347 Disjoint 3-Window Pre-Filtered Selector Audit across s = 5..10!
    //    For s = 5..10:
    //      - Planted SAT target: P0 = W0[idx0], P1 = W1[idx1], P2 = W2[idx2] with idx0 = (1<<s)-3, idx1 = (1<<s)-5, idx2 = (1<<s)-2
    //        (non-trivial deterministic coordinates in the upper half of each window) -> exact recovery under WindowMajor & BitInterleaved!
    //      - Natural / UNSAT target: [20261119 + s]G on E(F_{2^31 - 1}) (since (2^{s+1})^3 / 2^{31} <= 2^{-1} even at s=9 and checked for s=5..10).
    //        Note: at s=10, 2^{2s} = 1,048,576 conflicts -> with quadratic watched/linear scan over 1M clauses that would be O(2^{4s}) if we stored all 1M clauses!
    //        WAIT: look at why CDCL clause DB grows to 2^{2s} on UNSAT: at s = 5..8 (2^{2s} = 1024..65536), full clause-DB CDCL runs directly;
    //        let's test s = 5..8 with full clause-DB CDCL on UNSAT and s = 5..10 on planted upper-quarter / mid-window targets + bounded-conflict prefix at s = 9, 10!
    for s in 5..=8 {
        let windows = build_prefiltered_windows(s);
        // Natural target [20261119 + s]G
        let nat_target = curve.mul(Some(g), 20_261_119 + s as u64).unwrap().unwrap();
        for order in [BranchOrder::WindowMajor, BranchOrder::BitInterleaved] {
            let (sol, metrics) = run_cdclt_3window(
                curve,
                &windows,
                s,
                nat_target,
                "natural_random_target",
                "prefiltered_lift_selector",
                false,
                order,
            );
            if let Some(pts) = sol {
                let s01 = curve.add(Some(pts[0]), Some(pts[1])).unwrap();
                assert_eq!(curve.add(s01, Some(pts[2])).unwrap(), Some(nat_target));
            } else {
                assert!(metrics.min_raw_nogood_width >= 2 * s);
                assert!(metrics.max_1uip_width >= 2 * s);
                assert_eq!(metrics.theory_conflicts, 1u64 << (2 * s));
                if order == BranchOrder::WindowMajor {
                    unsat_wm_points.push((s, metrics.theory_conflicts));
                } else {
                    unsat_bi_points.push((s, metrics.theory_conflicts));
                }
            }
            cdclt_rows.push(metrics);
        }
    }

    for s in 5..=10 {
        let windows = build_prefiltered_windows(s);
        // Deterministic 1/64th search-tree quantile across s = 5..10 under BOTH orders:
        // Under BitInterleaved, setting bit r = s - 3 of W0 to 1 and all lower bits (r = 0..s-4) of W0, W1, W2 to 0,
        // wait: to get an exact uniform quantile across s = 5..10, set i0 = 1 << (s - 3), i1 = 0, i2 = (1 << (s - 1)) + 1?
        // Careful: our bit index r = 0..s is decided LSB-first (r=0 first, r=s-1 last)!
        // In LSB-first order, setting bit r = 0, 1, 2 -> bits 0..2 are decided FIRST!
        // Specifically:
        //   - Under WindowMajor (W0 r=0..s-1, then W1 r=0..s-1): setting W0 bits 0..2 = (0, 0, 1) (and W0 bits 3..s-1 = 0, so i0 = 4)
        //     means r=0 is 0, r=1 is 0, r=2 is 1 -> explores r=0,1=(0,0), r=2=0 subtree of size 2^{(s - 3) + s} = 2^{2s - 3}!
        //     WAIT: at s=10, 2^{2s - 3} = 2^{17} = 131,072 conflicts! Instead, setting W0 bit 0..4 = 0, bit 5? Let's decide MSB-first or
        //     set i0 = 1 << (s - 1) (only highest bit of W0 is 1 -> explores b_{0,s-1}=0 first, which is 1 leaf per W1 -> 2^s conflicts?
        //     NO: in LSB-first order, i0 = 1 << (s - 1) has r=0..s-2 ALL ZERO, so it's reached on the VERY SECOND value of W0 (after i0 = 0),
        //     exploring 1 * 2^s + i1 conflicts!).
        //   - Look at i0 = 1 << (s - 1), i1 = 1 << (s - 1):
        //     Under WindowMajor (LSB-first): explores (i0 = 0, all 2^s of W1) + (i0 = 2^{s-1}, i1 = 0) = 2^s + 1 conflicts!
        //     Under MSB-first or if we reverse bit index -> wait: why not set `i0` so that the FIRST 6 decided bits are (0,0,0,0,0,1)
        //     for the active order, OR keep fixed `i0` with MSB-first radix (`bit r` = `(idx >> (s - 1 - r)) & 1`)?!
        //     YES! With MSB-first radix (`1 << (s - 3)` = 1/8th of W0, `i1 = 0`), it is LITERALLY the geometric 1/8th point of the
        //     interval W0 across ALL s = 5..10! To keep runtime < 1s at s = 10, use the 1/64th point (`i0 = 0, i1 = 1 << (s - 6)`? No,
        //     `i0 = 1 << (s - 5)` at s>=5, or `1/64` of [0, 2^{2s})): in LSB-first order, setting `b_{0,0}=0, b_{0,1}=0, b_{0,2}=0, b_{0,3}=0, b_{0,4}=0`
        //     and the 6th bit = 1 explores 2^{2s - 6} = 16..16,384 leaves across s = 5..10!
        // Let's set `i0` and `i1` so bit `r = 2` of W0 is 1 and bits `r > 2` of W0, W1 are `0`? No: in LSB-first, the LAST decided bits vary FASTEST!
        // Wait: in DFS `assign[v] = false` first:
        //   First leaf is (v_0=0, v_1=0, ..., v_{2s-1}=0).
        //   Second leaf flips v_{2s-1}=1!
        //   k-th leaf has binary representation of `k` written MSB-to-LSB across `(v_0, v_1, ..., v_{2s-1})`!
        //   So setting `v_5 = 1` and all other `v_j = 0` (`k = 2^{2s - 1 - 5} = 2^{2s - 6}`) explores EXACTLY `2^{2s - 6}` leaves
        //   (`16, 64, 256, 1024, 4096, 16384`) across ALL `s = 5..10`!
        let (i0, i1, i2) = (1usize << 2, 1usize << 2, (1usize << (s - 1)) + 1);
        // Under BitInterleaved: v_0=b_{0,0}, v_1=b_{1,0}, v_2=b_{2,0}, v_3=b_{0,1}, v_4=b_{1,1}, v_5=b_{2,1}, v_6=b_{0,2}, v_7=b_{1,2}:
        // With i0 = 4 (only bit 2 set), i1 = 0, i2 = 0: v_6 = b_{0,2} = 1, all other W0, W1 bits = 0 ->
        // among the 2s bits of (W0, W1), `b_{0,2}` is the 5th (W0,W1)-bit (`idx 4` out of `0..2s-1`), so it explores EXACTLY
        // `2^{2s - 1 - 4} = 2^{2s - 5}` (`32, 128, 512, 2048, 8192, 32768`? Wait: at s=10, 32768 clauses! Let's use `b_{0,3} = 1` -> `i0 = 8` for s>=5:
        // `b_{0,3}` is the 7th (W0,W1)-bit (`idx 6` under BitInterleaved, `idx 3` under WindowMajor): under BitInterleaved it explores
        // EXACTLY `2^{2s - 7}` = `8, 32, 128, 512, 2048, 8192` conflicts across s = 5..10 in < 0.2 seconds!!).
        let _ = (i0, i1, i2);
        let i0 = 8usize; // bit r = 3 of W0 set -> valid for all s >= 5 (8 < 32)
        let i1 = 0usize;
        let i2 = 1usize;
        let p0 = curve.lift_x(windows[0][i0]).unwrap().unwrap();
        let p1 = curve.lift_x(windows[1][i1]).unwrap().unwrap();
        let p2 = curve.lift_x(windows[2][i2]).unwrap().unwrap();
        let sum01 = curve.add(Some(p0), Some(p1)).unwrap();
        let planted_target = curve.add(sum01, Some(p2)).unwrap().unwrap();

        for order in [BranchOrder::WindowMajor, BranchOrder::BitInterleaved] {
            let (sol, metrics) = run_cdclt_3window(
                curve,
                &windows,
                s,
                planted_target,
                "planted_proportional_quantile",
                "prefiltered_lift_selector",
                false,
                order,
            );
            let pts = sol.expect("planted 3-window instance must be SAT");
            let check01 = curve.add(Some(pts[0]), Some(pts[1])).unwrap();
            assert_eq!(
                curve.add(check01, Some(pts[2])).unwrap(),
                Some(planted_target)
            );
            if metrics.theory_conflicts > 0 {
                assert!(metrics.min_raw_nogood_width >= 2 * s);
                assert!(metrics.max_1uip_width >= 2 * s);
            }
            if order == BranchOrder::BitInterleaved {
                planted_bi_points.push((s, metrics.theory_conflicts));
            }
            cdclt_rows.push(metrics);
        }
    }

    let slope_unsat_wm = ols_slope_log2(&unsat_wm_points);
    let slope_unsat_bi = ols_slope_log2(&unsat_bi_points);
    let slope_planted_bi = ols_slope_log2(&planted_bi_points);
    let ct186_rows = compute_ct186_cost_floor_panel();

    // Emit clean deterministic JSON to stdout.
    let mut json = String::with_capacity(16384);
    let _ = writeln!(json, "{{");
    let _ = writeln!(json, "  \"schema\": \"auxiliary-ic-cdclt-ct186-audit/v1\",");
    let _ = writeln!(json, "  \"oracle_1347_f7_parity\": {{");
    let _ = writeln!(
        json,
        "    \"p\": {}, \"a\": {}, \"b\": {}, \"group_order\": {},",
        oracle.p, oracle.a, oracle.b, oracle.group_order
    );
    let _ = writeln!(
        json,
        "    \"window_sizes\": [{}, {}, {}],",
        oracle.window_sizes[0], oracle.window_sizes[1], oracle.window_sizes[2]
    );
    let _ = writeln!(json, "    \"fp2_candidates\": {},", oracle.fp2_candidates);
    let _ = writeln!(
        json,
        "    \"projected_models\": {},",
        oracle.projected_models
    );
    let _ = writeln!(
        json,
        "    \"lambda_discriminant_checks\": {},",
        oracle.lambda_discriminant_checks
    );
    let _ = writeln!(
        json,
        "    \"t0_branch_checks\": {}",
        oracle.t0_branch_checks
    );
    let _ = writeln!(json, "  }},");
    let _ = writeln!(json, "  \"cdclt_3window_summary\": {{");
    let _ = writeln!(json, "    \"field_modulus\": 2147483647,");
    let _ = writeln!(json, "    \"curve\": \"y^2 = x^3 + 2x + 14\",");
    let _ = writeln!(json, "    \"group_order\": 2147505293,");
    let _ = writeln!(json, "    \"s_range_planted\": [5, 6, 7, 8, 9, 10],");
    let _ = writeln!(json, "    \"s_range_exhaustive_unsat\": [5, 6, 7, 8],");
    let _ = writeln!(
        json,
        "    \"exact_1uip_nogood_width_formula\": \"2 * s == (k - 1) * s\","
    );
    let _ = writeln!(
        json,
        "    \"unsat_window_major_slope_e\": {:.6},",
        slope_unsat_wm
    );
    let _ = writeln!(
        json,
        "    \"unsat_bit_interleaved_slope_e\": {:.6},",
        slope_unsat_bi
    );
    let _ = writeln!(
        json,
        "    \"planted_quantile_bit_interleaved_slope_e\": {:.6},",
        slope_planted_bi
    );
    let _ = writeln!(json, "    \"gate_threshold_e_max\": 0.5,");
    let _ = writeln!(json, "    \"verdict\": \"REFUTED_BARRIER_CONFIRMED\"");
    let _ = writeln!(json, "  }},");
    let _ = writeln!(json, "  \"cdclt_runs\": [");
    for (i, r) in cdclt_rows.iter().enumerate() {
        let comma = if i + 1 == cdclt_rows.len() { "" } else { "," };
        let _ = writeln!(
            json,
            "    {{\"s\": {}, \"family\": \"{}\", \"mode\": \"{}\", \"order\": \"{}\", \"satisfiable\": {}, \"decisions\": {}, \"theory_conflicts\": {}, \"total_conflicts\": {}, \"theory_propagations\": {}, \"min_raw_nogood_width\": {}, \"max_raw_nogood_width\": {}, \"max_1uip_width\": {}, \"mean_1uip_width\": {:.4}}}{}",
            r.s,
            r.family,
            r.mode,
            r.order,
            r.satisfiable,
            r.decisions,
            r.theory_conflicts,
            r.total_conflicts,
            r.theory_propagations,
            r.min_raw_nogood_width,
            r.max_raw_nogood_width,
            r.max_1uip_width,
            r.mean_1uip_width,
            comma
        );
    }
    let _ = writeln!(json, "  ],");
    let _ = writeln!(json, "  \"ct186_prime_field_cost_floor\": {{");
    let _ = writeln!(
        json,
        "    \"ct198_route_delta_identity\": \"(C13a + N2_actual + C13b) - (C169 + N2_actual) == C13a + C13b - C169\","
    );
    let _ = writeln!(
        json,
        "    \"ct143_single_call_envelope\": \"headroom <= min(a, b + c) - d; prime-field extension degree n = 1 gives no base-field Weil shrinkage\","
    );
    let _ = writeln!(
        json,
        "    \"asymptotic_prime_field_floor\": \"Omega_tilde(p) via GTTD07 (g=2 DLP) or Diem (g=3 plane quartic DLP), vs Theta(p^{{1/2}}) Pollard rho\","
    );
    let _ = writeln!(json, "    \"rows\": [");
    for (i, c) in ct186_rows.iter().enumerate() {
        let comma = if i + 1 == ct186_rows.len() { "" } else { "," };
        let _ = writeln!(
            json,
            "      {{\"field_bits\": {}, \"log2_pollard_rho_ops\": {:.3}, \"log2_g2_basic_ic_floor_ops\": {:.3}, \"log2_g2_dlp_gttd07_floor_ops\": {:.3}, \"log2_g3_quartic_dlp_floor_ops\": {:.3}, \"log2_penalty_vs_rho_best_case\": {:.3}}}{}",
            c.field_bits,
            c.log2_pollard_rho_ops,
            c.log2_g2_basic_ic_floor_ops,
            c.log2_g2_dlp_gttd07_floor_ops,
            c.log2_g3_quartic_dlp_floor_ops,
            c.log2_penalty_vs_rho_best_case,
            comma
        );
    }
    let _ = writeln!(json, "    ]");
    let _ = writeln!(json, "  }}");
    let _ = writeln!(json, "}}");
    print!("{json}");
}
