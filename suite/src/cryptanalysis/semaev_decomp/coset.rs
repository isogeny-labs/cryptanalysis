//! Pairs-and-solve `S₄` over a **coset** `V + c` of an `F₂`-subspace.
//!
//! A child module of [`super`] so that it can share the tuned private
//! kernels of [`super::SubspaceOracle`] (the quartic Frobenius table,
//! the Horner form of `L_V`, the unrolled quartic gcd) without widening
//! their visibility.
//!
//! # The one change
//!
//! `L_V(t) = Π_{v ∈ V}(t + v)` is additive, so
//!
//! ```text
//!   L_V(t) + L_V(c) = L_V(t + c) = Π_{v ∈ V}(t + c + v)
//! ```
//!
//! vanishes exactly on the coset `V + c` and is still square-free.  The
//! roots of a quartic `f` that lie in `V + c` are therefore those of
//! `gcd(f, (L_V mod f) + L_V(c))`: the constant `L_V(c)` is computed once
//! per oracle and added to the remainder before the gcd.  Nothing else
//! in the pair loop changes, so a pair still costs `O(l)` field
//! operations and the loop runs over the `2^l (2^l + 1) / 2` unordered
//! pairs of the coset.
//!
//! With `c = 0` the coset is `V`, the span and every remainder are the
//! ones [`super::SubspaceOracle`] computes, and
//! [`AffineSubspaceOracle::decompose`] returns its witness and pair
//! count bit for bit (pinned by a test below).

use super::{
    gcd_quartic, quartic_general_with, GeneralTargetPowers, Gf2, LvHorner, Poly, QuarticFrobenius,
    MAX_DEG,
};

/// The `S₄` decomposition oracle for an affine factor base
/// `V + c = { c + v : v ∈ V }`, for the curve `y² + xy = x³ + ax² + b`
/// with any `b ≠ 0`.
///
/// The span is indexed by the coordinate word: `span[w] = c + Σ_j
/// w_j·basis[j]`.  Pairs are visited as `(span[i], span[j])`, `i ≤ j`, in
/// that index order, which fixes the witness [`Self::decompose`]
/// returns.
#[derive(Clone, Debug)]
pub struct AffineSubspaceOracle {
    /// Dimension of `V`.
    pub l: u32,
    /// Curve constant.
    pub b: u64,
    /// The shift `c`, as given.
    pub shift: u64,
    /// Every element of the coset, indexed by its coordinate word.
    pub span: Vec<u64>,
    /// Coefficients of `L_V`.
    pub lv: Vec<u64>,
    /// `L_V(c)`, zero exactly when `c ∈ V`.
    pub lc: u64,
}

/// Evaluate the linearised polynomial `Σ aᵢ x^{2^i}`.
fn eval_linearised(lv: &[u64], x: u64, gf: &Gf2) -> u64 {
    lv.iter().enumerate().fold(0u64, |acc, (i, &ai)| {
        acc ^ gf.mul(ai, gf.sqr_k(x, i as u32))
    })
}

/// Horner evaluation of `g` at `t`.
#[inline]
fn eval_poly(g: &Poly, t: u64, gf: &Gf2) -> u64 {
    let mut v = 0u64;
    for j in (0..=MAX_DEG).rev() {
        v = gf.mul(v, t) ^ g.c[j];
    }
    v
}

impl AffineSubspaceOracle {
    /// The oracle for `span(basis) + shift` on the curve with constant
    /// `b`.  Panics, as [`super::SubspaceOracle::new`] does, on a
    /// dependent basis, `b = 0` or `l > 30`.
    pub fn new(basis: &[u64], shift: u64, b: u64, gf: &Gf2) -> Self {
        let linear = super::SubspaceOracle::new(basis, b, gf);
        let span = linear.span.iter().map(|&v| v ^ shift).collect();
        let lc = eval_linearised(&linear.lv, shift, gf);
        Self {
            l: linear.l,
            b,
            shift,
            span,
            lv: linear.lv,
            lc,
        }
    }

    /// Whether `x ∈ V + c`: `L_V(x) = L_V(c)`.
    pub fn contains(&self, x: u64, gf: &Gf2) -> bool {
        eval_linearised(&self.lv, x, gf) == self.lc
    }

    /// The coset roots of `q / lead(q)` (`deg q = d`, `lead_inv` its
    /// inverse leading coefficient), as a polynomial whose roots are
    /// exactly those roots.
    #[inline(always)]
    fn coset_roots_of(
        &self,
        q: &Poly,
        d: usize,
        lead_inv: u64,
        horner: &LvHorner,
        gf: &Gf2,
    ) -> Poly {
        if d == 0 {
            // A non-zero constant has no roots.
            let mut one = Poly::zero();
            one.c[0] = 1;
            return one;
        }
        if d == 4 {
            let f = [
                gf.mul(q.c[0], lead_inv),
                gf.mul(q.c[1], lead_inv),
                gf.mul(q.c[2], lead_inv),
                gf.mul(q.c[3], lead_inv),
            ];
            // `roots_in_subspace_quartic`, plus the constant `L_V(c)`.
            let frob = QuarticFrobenius::new(f, gf);
            let mut u = [
                gf.mul(horner.top, f[0]),
                gf.mul(horner.top, f[1]) ^ horner.lin[0],
                gf.mul(horner.top, f[2]) ^ horner.lin[1],
                gf.mul(horner.top, f[3]),
            ];
            for &b in &horner.steps {
                u = frob.sqr(u, gf);
                u[1] ^= b;
            }
            u[0] ^= self.lc;
            return gcd_quartic(f, u, gf);
        }
        // `roots_in_subspace`, plus the constant `L_V(c)`.
        let mut monic = *q;
        monic.scale_in_place(lead_inv, d, gf);
        let mut t = Poly::zero();
        t.c[1] = 1;
        let mut acc = Poly::zero();
        let mut pow = t.rem_monic(&monic, d, gf);
        for (i, &ai) in self.lv.iter().enumerate() {
            if ai != 0 {
                for j in 0..d {
                    acc.c[j] ^= gf.mul(pow.c[j], ai);
                }
            }
            if i + 1 < self.lv.len() {
                pow = pow.sqr_mod_monic(&monic, d, gf);
            }
        }
        acc.c[0] ^= self.lc;
        monic.gcd(&acc, gf)
    }

    /// **Does `x_R` decompose over the coset?**  A witness `(X₁, X₂, X₃)`
    /// with `S₄(X₁, X₂, X₃, x_R) = 0` and every `Xᵢ ∈ V + c`, together
    /// with the number of pairs processed — the first witness in pair
    /// order, exactly as [`super::SubspaceOracle::decompose`] reports one.
    pub fn decompose(&self, xr: u64, gf: &Gf2) -> (Option<[u64; 3]>, u64) {
        let mut found = None;
        let pairs = self.scan(xr, gf, &mut |w| {
            found = Some(w);
            false
        });
        (found, pairs)
    }

    /// **Every** coset triple `X₁ ≤ X₂ ≤ X₃` (as integers) with
    /// `S₄(X₁, X₂, X₃, x_R) = 0`, sorted and without repeats, and the
    /// number of pairs processed (always the full count).
    pub fn decompose_all(&self, xr: u64, gf: &Gf2) -> (Vec<[u64; 3]>, u64) {
        let mut all = std::collections::BTreeSet::new();
        let pairs = self.scan(xr, gf, &mut |mut w| {
            w.sort_unstable();
            all.insert(w);
            true
        });
        (all.into_iter().collect(), pairs)
    }

    /// The pair loop.  `sink` receives every `(X₁, X₂, X₃)` found and
    /// returns `false` to stop.  Order: row by row (`X₁ = span[i]`); within
    /// a row, first the pairs whose quartic vanishes identically (every
    /// non-zero coset element, in index order) as they are built, then
    /// each remaining pair's roots in pair order (the linear root, or the
    /// coset roots in index order) — the order in which
    /// [`super::SubspaceOracle`] meets its first witness.
    fn scan(&self, xr: u64, gf: &Gf2, sink: &mut dyn FnMut([u64; 3]) -> bool) -> u64 {
        #[cfg(target_arch = "x86_64")]
        if gf.has_clmul {
            // SAFETY: `has_clmul` records `is_x86_feature_detected!("pclmulqdq")`.
            return unsafe { self.scan_pclmulqdq(xr, gf, sink) };
        }
        self.scan_body(xr, gf, sink)
    }

    #[cfg(target_arch = "x86_64")]
    #[target_feature(enable = "pclmulqdq")]
    unsafe fn scan_pclmulqdq(
        &self,
        xr: u64,
        gf: &Gf2,
        sink: &mut dyn FnMut([u64; 3]) -> bool,
    ) -> u64 {
        self.scan_body(xr, gf, sink)
    }

    #[inline(always)]
    fn scan_body(&self, xr: u64, gf: &Gf2, sink: &mut dyn FnMut([u64; 3]) -> bool) -> u64 {
        let tp = GeneralTargetPowers::new(xr, self.b, gf);
        let horner = LvHorner::new(&self.lv, gf);
        let span = &self.span;
        let count = span.len();
        let mut pairs = 0u64;

        let mut qs: Vec<Poly> = Vec::with_capacity(count);
        let mut leads: Vec<u64> = Vec::with_capacity(count);
        let mut scratch: Vec<u64> = Vec::with_capacity(count);

        for i1 in 0..count {
            let x1 = span[i1];
            qs.clear();
            leads.clear();
            for &x2 in &span[i1..] {
                let q = quartic_general_with(x1, x2, &tp, gf);
                pairs += 1;
                match q.deg() {
                    // Every `t` is a root, reported where the linear
                    // oracle reports it (before the row's remainders):
                    // its witness is the first non-zero span element.
                    None => {
                        for &t in span.iter().filter(|&&v| v != 0) {
                            if !sink([x1, x2, t]) {
                                return pairs;
                            }
                        }
                        leads.push(0);
                    }
                    Some(d) => leads.push(q.c[d]),
                }
                qs.push(q);
            }
            gf.batch_inv(&mut leads, &mut scratch);

            for (i, q) in qs.iter().enumerate() {
                let x2 = span[i1 + i];
                let Some(d) = q.deg() else {
                    continue; // reported in the build loop
                };
                let g = self.coset_roots_of(q, d, leads[i], &horner, gf);
                match g.deg() {
                    None | Some(0) => continue,
                    Some(1) => {
                        if !sink([x1, x2, gf.mul(g.c[0], gf.inv(g.c[1]))]) {
                            return pairs;
                        }
                    }
                    Some(_) => {
                        for &t in span.iter() {
                            if eval_poly(&g, t, gf) == 0 && !sink([x1, x2, t]) {
                                return pairs;
                            }
                        }
                    }
                }
            }
        }
        pairs
    }
}

#[cfg(test)]
mod tests {
    use super::super::{eval_s4_general, SubspaceOracle};
    use super::*;
    use crate::cryptanalysis::koblitz_index_calculus::find_irreducible_sparse;

    fn xorshift(state: &mut u64) -> u64 {
        *state ^= *state >> 12;
        *state ^= *state << 25;
        *state ^= *state >> 27;
        state.wrapping_mul(0x2545_F491_4F6C_DD1D)
    }

    fn random_basis(l: u32, gf: &Gf2, s: &mut u64) -> Vec<u64> {
        loop {
            let basis: Vec<u64> = (0..l).map(|_| xorshift(s) & gf.mask).collect();
            let mut span: Vec<u64> = (0..1u64 << l)
                .map(|w| {
                    (0..l as usize)
                        .filter(|j| (w >> j) & 1 == 1)
                        .fold(0, |a, j| a ^ basis[j])
                })
                .collect();
            span.sort_unstable();
            span.dedup();
            if span.len() == 1 << l {
                return basis;
            }
        }
    }

    /// Brute force over every sorted coset triple: the reference.
    fn all_triples(o: &AffineSubspaceOracle, xr: u64, gf: &Gf2) -> Vec<[u64; 3]> {
        let mut v = o.span.clone();
        v.sort_unstable();
        let mut out = Vec::new();
        for i in 0..v.len() {
            for j in i..v.len() {
                for k in j..v.len() {
                    if eval_s4_general(v[i], v[j], v[k], xr, o.b, gf) == 0 {
                        out.push([v[i], v[j], v[k]]);
                    }
                }
            }
        }
        out
    }

    /// Every coset triple the oracle reports, and only those, over random
    /// fields, curves, subspaces, shifts and targets, including shifts
    /// inside `V` (the coset is then `V` itself) and the targets `0`
    /// and `c`.
    #[test]
    fn coset_oracle_finds_exactly_the_brute_force_triples() {
        let mut s = 0xAFF1_0E5E_7C05_E7A1u64;
        for (n, l) in [
            (5u32, 2u32),
            (7, 2),
            (8, 3),
            (11, 3),
            (13, 3),
            (16, 2),
            (19, 3),
        ] {
            let gf = Gf2::new(&find_irreducible_sparse(n).unwrap());
            for round in 0..6 {
                let basis = random_basis(l, &gf, &mut s);
                let shift = match round {
                    0 => 0,
                    1 => basis[0] ^ basis[l as usize - 1],
                    _ => xorshift(&mut s) & gf.mask,
                };
                let b = (xorshift(&mut s) & gf.mask).max(1);
                let o = AffineSubspaceOracle::new(&basis, shift, b, &gf);
                for xr in [
                    0,
                    shift,
                    1,
                    xorshift(&mut s) & gf.mask,
                    xorshift(&mut s) & gf.mask,
                ] {
                    let (all, pairs) = o.decompose_all(xr, &gf);
                    let want = all_triples(&o, xr, &gf);
                    assert_eq!(all, want, "n={n} l={l} c={shift:#x} b={b:#x} xr={xr:#x}");
                    let full = (1u64 << l) * ((1u64 << l) + 1) / 2;
                    assert_eq!(pairs, full);
                    let (first, _) = o.decompose(xr, &gf);
                    match first {
                        None => assert!(want.is_empty()),
                        Some(mut w) => {
                            assert!(w.iter().all(|&x| o.contains(x, &gf)));
                            assert_eq!(eval_s4_general(w[0], w[1], w[2], xr, b, &gf), 0);
                            w.sort_unstable();
                            assert!(want.contains(&w));
                        }
                    }
                }
            }
        }
    }

    /// With `c = 0` the coset oracle is the linear one: the same witness
    /// and the same pair count on every target.
    #[test]
    fn zero_shift_is_the_subspace_oracle_bit_for_bit() {
        let mut s = 0x5EED_0000_0000_0042u64;
        for (n, l) in [(11u32, 3u32), (17, 4), (24, 5), (31, 4)] {
            let gf = Gf2::new(&find_irreducible_sparse(n).unwrap());
            let basis = random_basis(l, &gf, &mut s);
            let b = (xorshift(&mut s) & gf.mask).max(1);
            let lin = SubspaceOracle::new(&basis, b, &gf);
            let aff = AffineSubspaceOracle::new(&basis, 0, b, &gf);
            assert_eq!(aff.lc, 0);
            for _ in 0..40 {
                let xr = xorshift(&mut s) & gf.mask;
                assert_eq!(
                    aff.decompose(xr, &gf),
                    lin.decompose(xr, &gf),
                    "n={n} xr={xr:#x}"
                );
            }
        }
    }

    /// Membership agrees with the explicit span.
    #[test]
    fn coset_membership_is_exact() {
        let mut s = 0x0C05_E700_0000_0001u64;
        let gf = Gf2::new(&find_irreducible_sparse(10).unwrap());
        let basis = random_basis(4, &gf, &mut s);
        let shift = xorshift(&mut s) & gf.mask;
        let o = AffineSubspaceOracle::new(&basis, shift, 1, &gf);
        let set: std::collections::HashSet<u64> = o.span.iter().copied().collect();
        for x in 0..(1u64 << 10) {
            assert_eq!(o.contains(x, &gf), set.contains(&x), "x={x:#x}");
        }
    }
}
