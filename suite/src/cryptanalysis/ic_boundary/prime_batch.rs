//! Batched prime-field preparation and probes for the pair-table oracle.
//!
//! The scalar pair table costs one affine addition per entry, and an
//! affine addition on a word prime is one modular inversion plus three
//! multiplications; the inversion is three quarters of it.  Two things
//! cut that:
//!
//! * **One inversion per abscissa pair.**  `x(P + Q)` and `x(P − Q)`
//!   share the denominator `x_Q − x_P`: with `λ± = (±y_Q − y_P)/(x_Q − x_P)`
//!   both abscissae come out of one inverse, and the pair table keys on
//!   the abscissa alone (`S` and `−S` share an entry), so the whole
//!   negation-folded table is `a(a − 1)/2` inversions plus `a` doublings
//!   for `a` abscissae, against `a(a + 1)` affine additions.
//! * **Montgomery's simultaneous inversion.**  A chunk of `k` denominators
//!   is inverted with one inversion and `3(k − 1)` multiplications.
//!
//! The same two ideas give the three-summand probe: every `R ± P_i` over
//! the base's abscissae from one batched inversion, in the scalar loop's
//! index order so the first witness is the one the scalar loop finds.
//!
//! The work is charged the way the binary `mitm-batched` oracle charges
//! its preparation: the complete native time in nanoseconds, with the
//! additions a scalar build would have counted kept as a diagnostic, or,
//! when a caller asks for counted pricing, exactly those additions.
//! Nothing here changes which entries the table holds: the witness map is
//! identical to `PairTable::build` / `build_negation_folded`, and the
//! tests check that entry by entry.

use super::{invmod, FactorBase, GroupOps, PairTable, PairWitnessMap, PrimeCurve, PrimePoint};
use std::time::Instant;

/// Montgomery arithmetic modulo one odd word prime `p < 2^63`.
///
/// Elements are kept as `a·R mod p` with `R = 2^64`.  The inverse goes
/// through the extended Euclidean algorithm on the representative rather
/// than Fermat's `p − 2` power: a few dozen word divisions against about
/// ninety multiplications, which matters when a batch is short.
#[derive(Clone, Copy, Debug)]
pub struct PrimeMont {
    p: u64,
    n0inv: u64,
    r: u64,
    r2: u64,
    r3: u64,
}

impl PrimeMont {
    pub fn new(p: u64) -> Option<Self> {
        if p < 3 || p.is_multiple_of(2) || p >= 1u64 << 63 {
            return None;
        }
        // Newton iteration for p^{-1} mod 2^64: each step doubles the
        // correct bits, six steps from the odd seed `1` give 64.
        let mut inv = 1u64;
        for _ in 0..6 {
            inv = inv.wrapping_mul(2u64.wrapping_sub(p.wrapping_mul(inv)));
        }
        debug_assert_eq!(p.wrapping_mul(inv), 1);
        let r = ((1u128 << 64) % p as u128) as u64;
        let r2 = ((r as u128 * r as u128) % p as u128) as u64;
        let mut this = Self {
            p,
            n0inv: inv.wrapping_neg(),
            r,
            r2,
            r3: 0,
        };
        this.r3 = this.mul(r2, r2);
        Some(this)
    }

    #[inline(always)]
    pub fn modulus(&self) -> u64 {
        self.p
    }

    #[inline(always)]
    pub fn one(&self) -> u64 {
        self.r
    }

    /// Montgomery product `a·b/R mod p`.
    #[inline(always)]
    pub fn mul(&self, a: u64, b: u64) -> u64 {
        let t = a as u128 * b as u128;
        let u = (t as u64).wrapping_mul(self.n0inv);
        let hi = (t >> 64) as u64;
        let product_hi = ((u as u128 * self.p as u128) >> 64) as u64;
        // t + u·p is divisible by 2^64; its high word is hi + product_hi
        // plus the carry out of the low words, and that carry is 1 unless
        // the low word of t was 0.
        let carry = u64::from((t as u64) != 0);
        let s = hi + product_hi + carry;
        if s >= self.p {
            s - self.p
        } else {
            s
        }
    }

    #[inline(always)]
    pub fn sqr(&self, a: u64) -> u64 {
        self.mul(a, a)
    }

    #[inline(always)]
    pub fn add(&self, a: u64, b: u64) -> u64 {
        let s = a + b;
        if s >= self.p {
            s - self.p
        } else {
            s
        }
    }

    #[inline(always)]
    pub fn sub(&self, a: u64, b: u64) -> u64 {
        if a >= b {
            a - b
        } else {
            a + (self.p - b)
        }
    }

    #[inline(always)]
    pub fn neg(&self, a: u64) -> u64 {
        if a == 0 {
            0
        } else {
            self.p - a
        }
    }

    #[inline(always)]
    pub fn to_mont(&self, x: u64) -> u64 {
        self.mul(x % self.p, self.r2)
    }

    #[inline(always)]
    pub fn from_mont(&self, x: u64) -> u64 {
        self.mul(x, 1)
    }

    /// `a^{-1}` in Montgomery form, by the extended Euclidean algorithm on
    /// the representative: `(aR)^{-1}·R^3/R = a^{-1}R`.  `inv(0) = 0`.
    pub fn inv(&self, a: u64) -> u64 {
        match invmod(a, self.p) {
            Some(v) => self.mul(v, self.r3),
            None => 0,
        }
    }

    /// Montgomery's simultaneous inversion of every element of `xs`, in
    /// place: one inversion and `3(k − 1)` multiplications.  No element
    /// may be zero; `scratch` is resized as needed.
    pub fn batch_inv(&self, xs: &mut [u64], scratch: &mut Vec<u64>) {
        let k = xs.len();
        if k == 0 {
            return;
        }
        scratch.clear();
        scratch.resize(k, 0);
        scratch[0] = xs[0];
        for i in 1..k {
            scratch[i] = self.mul(scratch[i - 1], xs[i]);
        }
        let mut acc = self.inv(scratch[k - 1]);
        for i in (1..k).rev() {
            let xi = self.mul(acc, scratch[i - 1]);
            acc = self.mul(acc, xs[i]);
            xs[i] = xi;
        }
        xs[0] = acc;
    }
}

/// The base's affine points in Montgomery form, converted once.
pub struct MontBase {
    pub field: PrimeMont,
    pub a: u64,
    pub xs: Vec<u64>,
    pub ys: Vec<u64>,
}

impl MontBase {
    pub fn new(curve: &PrimeCurve, points: &[PrimePoint]) -> Option<Self> {
        let field = PrimeMont::new(curve.p)?;
        if points.iter().any(|p| p.infinity) {
            return None;
        }
        Some(Self {
            field,
            a: field.to_mont(curve.a),
            xs: points.iter().map(|p| field.to_mont(p.x)).collect(),
            ys: points.iter().map(|p| field.to_mont(p.y)).collect(),
        })
    }
}

/// Reusable buffers for the batched routines.
#[derive(Default)]
pub struct PrimeBatchScratch {
    dens: Vec<u64>,
    prefix: Vec<u64>,
    pending: Vec<Pending>,
    abscissae: Vec<Option<u64>>,
    witnesses: Vec<(u32, u32)>,
}

/// One queued evaluation: a sum-and-difference of two base points, or a
/// doubling.  `i`, `j` are point indices; a doubling has `j == None`.
#[derive(Clone, Copy)]
struct Pending {
    i: u32,
    j: Option<u32>,
    /// Witness index for the sum (`P_i + P_j`), `u32::MAX` for none.
    w_plus: u32,
    /// Witness index for the difference (`P_i − P_j`), `u32::MAX` for none.
    w_minus: u32,
}

/// Does the compact `u32 → u32` storage hold every key and witness?
fn compact_prime_shape(p: u64, points: usize) -> bool {
    // Keys are `x + 1 ≤ p`; witnesses pack two 16-bit indices.
    p < u64::from(u32::MAX) && points <= usize::from(u16::MAX) + 1
}

impl PairTable {
    /// **The pair table of a prime-field base, prepared in batches.**
    ///
    /// The same entries and first witnesses as [`PairTable::build`] and
    /// [`PairTable::build_negation_folded`] (those two already agree:
    /// the full build's extra rows only re-insert keys the folded rows
    /// put there first), from `a(a − 1)/2` batched inversions and `a`
    /// doublings.  `build_ops.adds` carries the additions the scalar
    /// build would have counted — the folded count, or the full count
    /// when `folded` is false — so a caller can charge them or report
    /// them; nothing is charged here.  Fails only when the field is not
    /// a word prime the Montgomery arithmetic handles.
    pub fn build_prime_batched(
        curve: &PrimeCurve,
        fb: &FactorBase<PrimePoint>,
        folded: bool,
        chunk: usize,
    ) -> Result<Self, &'static str> {
        if !(1..=1 << 20).contains(&chunk) {
            return Err("prime batch chunk must be in 1..=1048576");
        }
        let start = Instant::now();
        let base = MontBase::new(curve, &fb.points)
            .ok_or("prime batched preparation needs an odd word prime below 2^63 and affine points")?;
        let groups: Vec<&Vec<usize>> = fb
            .abscissa_list
            .iter()
            .map(|x| fb.x_index.get(x).expect("every listed abscissa is indexed"))
            .collect();
        let a = groups.len();
        let n = fb.points.len();
        let compact = compact_prime_shape(curve.p, n);
        let mut map = PairWitnessMap::new(a * a + 1, compact);
        let mut scratch = PrimeBatchScratch::default();
        // The scalar builds call `add` before the identity check, so the
        // identity pair of each abscissa is in their count too.
        let scalar_adds: u64 = if folded {
            (0..a)
                .map(|ai| groups[ai..].iter().map(|g| g.len() as u64).sum::<u64>())
                .sum()
        } else {
            (n as u64) * (n as u64 + 1) / 2
        };
        for (ai, group) in groups.iter().enumerate() {
            let i = group[0] as u32;
            // Own abscissa: `2P_i` (skipped when `y = 0`, where `2P = O`,
            // exactly as the scalar build skips the identity sum).
            if fb.points[i as usize].y != 0 {
                scratch.pending.push(Pending {
                    i,
                    j: None,
                    w_plus: i,
                    w_minus: u32::MAX,
                });
            }
            for later in groups.iter().skip(ai + 1) {
                let j0 = later[0] as u32;
                scratch.pending.push(Pending {
                    i,
                    j: Some(j0),
                    w_plus: j0,
                    w_minus: if later.len() > 1 {
                        later[1] as u32
                    } else {
                        u32::MAX
                    },
                });
                if scratch.pending.len() >= chunk {
                    flush_pairs(&base, &mut scratch, &mut map);
                }
            }
        }
        if !scratch.pending.is_empty() {
            flush_pairs(&base, &mut scratch, &mut map);
        }
        let build_ops = GroupOps {
            adds: scalar_adds,
            ..Default::default()
        };
        Ok(Self {
            kind: if folded {
                "negation_folded_prime_batch_xonly"
            } else {
                "full_prime_batch_xonly"
            },
            entries: map.len() as u64,
            map,
            build_ops,
            build_wall_ns: start.elapsed().as_nanos() as u64,
            prefix_inverse_bytes: 0,
            vector_pairs: 0,
            vector_pclmul128_pairs: 0,
            vector_packed_square_pairs: 0,
            vector_const_pairs: 0,
            indexed_prepare_pairs: 0,
        })
    }
}

/// Evaluate every queued pair of one chunk with one batched inversion
/// and insert the abscissae in queue order (first witness wins, as in
/// the scalar builds).
fn flush_pairs(base: &MontBase, scratch: &mut PrimeBatchScratch, map: &mut PairWitnessMap) {
    let f = &base.field;
    scratch.dens.clear();
    for q in &scratch.pending {
        let xi = base.xs[q.i as usize];
        let d = match q.j {
            Some(j) => f.sub(base.xs[j as usize], xi),
            None => f.add(base.ys[q.i as usize], base.ys[q.i as usize]),
        };
        debug_assert_ne!(d, 0, "distinct abscissae and a non-zero ordinate");
        scratch.dens.push(d);
    }
    f.batch_inv(&mut scratch.dens, &mut scratch.prefix);
    scratch.abscissae.clear();
    scratch.witnesses.clear();
    for (q, &inv) in scratch.pending.iter().zip(&scratch.dens) {
        let (xi, yi) = (base.xs[q.i as usize], base.ys[q.i as usize]);
        match q.j {
            Some(j) => {
                let (xj, yj) = (base.xs[j as usize], base.ys[j as usize]);
                let s = f.add(xi, xj);
                let lp = f.mul(f.sub(yj, yi), inv);
                let x_plus = f.sub(f.sqr(lp), s);
                scratch.abscissae.push(Some(f.from_mont(x_plus)));
                scratch.witnesses.push((q.i, q.w_plus));
                if q.w_minus != u32::MAX {
                    let lm = f.mul(f.add(yj, yi), inv);
                    let x_minus = f.sub(f.sqr(lm), s);
                    scratch.abscissae.push(Some(f.from_mont(x_minus)));
                    scratch.witnesses.push((q.i, q.w_minus));
                }
            }
            None => {
                let l = f.mul(f.add(f.mul(f.add(f.add(xi, xi), xi), xi), base.a), inv);
                let x2 = f.sub(f.sqr(l), f.add(xi, xi));
                scratch.abscissae.push(Some(f.from_mont(x2)));
                scratch.witnesses.push((q.i, q.w_plus));
            }
        }
    }
    map.insert_abscissae(&scratch.abscissae, &scratch.witnesses);
    scratch.pending.clear();
}

/// Affine `R ± P_i` for a run of base abscissae, from one batched
/// inversion.  Appends, for each abscissa `x_i` of `groups[lo..hi]` in
/// order, the candidates the scalar three-summand loop would probe at
/// the points above it, in its index order: for the point with the
/// smaller ordinate `R − P_i`, for its negative `R + P_i`.  `None` marks
/// the identity (which the scalar loop skips).  Returns the number of
/// candidate points evaluated.
#[allow(clippy::too_many_arguments)]
pub fn prime_probe_candidates(
    base: &MontBase,
    groups: &[&Vec<usize>],
    target: PrimePoint,
    scratch: &mut PrimeBatchScratch,
    out: &mut Vec<(usize, Option<PrimePoint>)>,
) -> u64 {
    let f = &base.field;
    let (xr, yr) = (f.to_mont(target.x), f.to_mont(target.y));
    scratch.dens.clear();
    scratch.pending.clear();
    for group in groups {
        let i = group[0];
        let (xi, yi) = (base.xs[i], base.ys[i]);
        if xi != xr {
            scratch.dens.push(f.sub(xi, xr));
            scratch.pending.push(Pending {
                i: i as u32,
                j: Some(0),
                w_plus: 0,
                w_minus: 0,
            });
        } else {
            // R = ±P_i: one of R − P_i, R + P_i is the identity and the
            // other is ±2P_i, whose abscissa is the doubling's.
            let d = f.add(yi, yi);
            scratch.dens.push(if d == 0 { f.one() } else { d });
            scratch.pending.push(Pending {
                i: i as u32,
                j: None,
                w_plus: 0,
                w_minus: 0,
            });
        }
    }
    f.batch_inv(&mut scratch.dens, &mut scratch.prefix);
    let mut evaluated = 0u64;
    for ((group, q), &inv) in groups.iter().zip(&scratch.pending).zip(&scratch.dens) {
        let i = q.i as usize;
        let (xi, yi) = (base.xs[i], base.ys[i]);
        let neg_index = group.get(1).copied();
        match q.j {
            Some(_) => {
                // R − P_i = R + (x_i, −y_i): λ = (−y_i − y_R)/(x_i − x_R).
                let s = f.add(xr, xi);
                let lm = f.mul(f.neg(f.add(yi, yr)), inv);
                let x3 = f.sub(f.sqr(lm), s);
                let y3 = f.sub(f.mul(lm, f.sub(xr, x3)), yr);
                out.push((
                    i,
                    Some(PrimePoint::affine(f.from_mont(x3), f.from_mont(y3))),
                ));
                evaluated += 1;
                if let Some(ni) = neg_index {
                    // R + P_i: λ = (y_i − y_R)/(x_i − x_R).
                    let lp = f.mul(f.sub(yi, yr), inv);
                    let x3 = f.sub(f.sqr(lp), s);
                    let y3 = f.sub(f.mul(lp, f.sub(xr, x3)), yr);
                    out.push((
                        ni,
                        Some(PrimePoint::affine(f.from_mont(x3), f.from_mont(y3))),
                    ));
                    evaluated += 1;
                }
            }
            None => {
                // x_R = x_i.  2P_i is the identity when y_i = 0.
                let double = if yi == 0 {
                    None
                } else {
                    let l = f.mul(f.add(f.mul(f.add(f.add(xi, xi), xi), xi), base.a), inv);
                    let x2 = f.sub(f.sqr(l), f.add(xi, xi));
                    let y2 = f.sub(f.mul(l, f.sub(xi, x2)), yi);
                    Some((f.from_mont(x2), f.from_mont(y2)))
                };
                let r_is_p = yr == yi;
                // Index order: the smaller-ordinate point first.
                // R = P_i:  R − P_i = O,     R + P_i = 2P_i.
                // R = −P_i: R − P_i = −2P_i, R + P_i = O.
                let first = if r_is_p {
                    None
                } else {
                    double.map(|(x, y)| PrimePoint::affine(x, if y == 0 { 0 } else { f.p - y }))
                };
                out.push((i, first));
                evaluated += 1;
                if let Some(ni) = neg_index {
                    let second = if r_is_p {
                        double.map(|(x, y)| PrimePoint::affine(x, y))
                    } else {
                        None
                    };
                    out.push((ni, second));
                    evaluated += 1;
                }
            }
        }
    }
    evaluated
}

/// Scratch the counted group's pairwise addition keeps between batches.
#[derive(Default)]
pub struct PrimePairScratch {
    dens: Vec<u64>,
    prefix: Vec<u64>,
    lanes: Vec<Lane>,
    mont: Option<PrimeMont>,
}

impl PrimePairScratch {
    fn mont(&mut self, p: u64) -> Option<PrimeMont> {
        if self.mont.map(|m| m.modulus()) != Some(p) {
            self.mont = PrimeMont::new(p);
        }
        self.mont
    }
}

#[derive(Clone, Copy)]
enum Lane {
    /// Ordinary addition: `(x_p, y_p, x_q, y_q)` in Montgomery form.
    Add(u64, u64, u64, u64),
    /// Decided without an inversion.
    Done(PrimePoint),
}

/// `ps[k] + qs[k]` for every `k`, with one batched inversion per call.
/// The lanes that need no inversion (an identity operand, `P = −Q`) or a
/// doubling are decided inline; the rest share the inverse.  Results
/// are bit-identical to `PrimeCurve::add_raw`.
pub fn add_pairwise_prime(
    curve: &PrimeCurve,
    ps: &[PrimePoint],
    qs: &[PrimePoint],
    out: &mut Vec<PrimePoint>,
    scratch: &mut PrimePairScratch,
) {
    out.clear();
    let Some(f) = scratch.mont(curve.p) else {
        out.extend(ps.iter().zip(qs).map(|(&p, &q)| curve.add_scalar(p, q)));
        return;
    };
    scratch.lanes.clear();
    scratch.dens.clear();
    for (&p, &q) in ps.iter().zip(qs) {
        if p.infinity || q.infinity || p.x == q.x {
            scratch.lanes.push(Lane::Done(curve.add_scalar(p, q)));
            continue;
        }
        let (xp, yp, xq, yq) = (
            f.to_mont(p.x),
            f.to_mont(p.y),
            f.to_mont(q.x),
            f.to_mont(q.y),
        );
        scratch.dens.push(f.sub(xq, xp));
        scratch.lanes.push(Lane::Add(xp, yp, xq, yq));
    }
    f.batch_inv(&mut scratch.dens, &mut scratch.prefix);
    let mut d = scratch.dens.iter();
    for lane in &scratch.lanes {
        match *lane {
            Lane::Done(r) => out.push(r),
            Lane::Add(xp, yp, xq, yq) => {
                let inv = *d.next().expect("one inverse per added lane");
                let l = f.mul(f.sub(yq, yp), inv);
                let x3 = f.sub(f.sub(f.sqr(l), xp), xq);
                let y3 = f.sub(f.mul(l, f.sub(xp, x3)), yp);
                out.push(PrimePoint::affine(f.from_mont(x3), f.from_mont(y3)));
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::super::{
        decompose_mitm, prime_factor_base, roster_prime_instance, CountedGroup, GroupOps,
        OracleCounters,
    };
    use super::*;
    use rand::rngs::StdRng;
    use rand::{Rng, SeedableRng};

    fn mulmod(a: u64, b: u64, m: u64) -> u64 {
        ((a as u128 * b as u128) % m as u128) as u64
    }

    #[test]
    fn montgomery_arithmetic_agrees_with_u128() {
        let mut rng = StdRng::seed_from_u64(1);
        for &p in &[1_000_003u64, 2_147_483_647, (1u64 << 61) - 1, 4_294_967_291] {
            let f = PrimeMont::new(p).unwrap();
            for _ in 0..2000 {
                let a = rng.gen_range(0..p);
                let b = rng.gen_range(1..p);
                let (am, bm) = (f.to_mont(a), f.to_mont(b));
                assert_eq!(f.from_mont(f.mul(am, bm)), mulmod(a, b, p));
                assert_eq!(f.from_mont(f.add(am, bm)), (a + b) % p);
                assert_eq!(f.from_mont(f.sub(am, bm)), (a + p - b) % p);
                let inv = f.from_mont(f.inv(bm));
                assert_eq!(mulmod(inv, b, p), 1, "p={p} b={b}");
            }
            assert_eq!(f.inv(0), 0);
            assert_eq!(f.from_mont(f.one()), 1);
        }
    }

    #[test]
    fn batch_inversion_matches_one_at_a_time() {
        let p = 2_147_483_647u64;
        let f = PrimeMont::new(p).unwrap();
        let mut rng = StdRng::seed_from_u64(2);
        for len in [1usize, 2, 3, 17, 256] {
            let xs: Vec<u64> = (0..len).map(|_| f.to_mont(rng.gen_range(1..p))).collect();
            let want: Vec<u64> = xs.iter().map(|&x| f.inv(x)).collect();
            let mut got = xs.clone();
            f.batch_inv(&mut got, &mut Vec::new());
            assert_eq!(got, want, "len {len}");
        }
    }

    #[test]
    fn batched_table_has_the_scalar_tables_witness_map() {
        for bits in [14u32, 16, 18] {
            let inst = roster_prime_instance(bits).expect("roster instance");
            let fb = prime_factor_base(&inst, 1 << (bits / 3));
            let folded = PairTable::build_negation_folded(&inst.curve, &fb);
            let full = PairTable::build(&inst.curve, &fb);
            for chunk in [1usize, 7, 1024] {
                let batched = PairTable::build_prime_batched(&inst.curve, &fb, true, chunk)
                    .expect("word prime");
                assert!(
                    batched.same_witness_map(&folded),
                    "bits {bits} chunk {chunk}: folded witness map differs"
                );
                assert!(
                    batched.same_witness_map(&full),
                    "bits {bits} chunk {chunk}: full witness map differs"
                );
                assert_eq!(batched.entries, folded.entries);
                assert_eq!(batched.build_ops.adds, folded.build_ops.adds);
            }
            let unfolded = PairTable::build_prime_batched(&inst.curve, &fb, false, 64).unwrap();
            assert!(unfolded.same_witness_map(&full));
            assert_eq!(unfolded.build_ops.adds, full.build_ops.adds);
        }
    }

    #[test]
    fn pairwise_addition_is_the_scalar_addition() {
        let inst = roster_prime_instance(18).unwrap();
        let curve = &inst.curve;
        let g = inst.generator_point();
        let mut ops = GroupOps::default();
        let mut rng = StdRng::seed_from_u64(3);
        let pts: Vec<PrimePoint> = (0..64)
            .map(|_| curve.mul(&mut ops, g, rng.gen_range(1..inst.r)))
            .collect();
        let mut ps = Vec::new();
        let mut qs = Vec::new();
        for k in 0..64 {
            ps.push(pts[k]);
            qs.push(pts[(k * 7 + 3) % 64]);
        }
        // Doublings, inverses and identities in the same batch.
        ps.push(pts[0]);
        qs.push(pts[0]);
        ps.push(pts[1]);
        qs.push(curve.neg(pts[1]));
        ps.push(PrimePoint::INFINITY);
        qs.push(pts[2]);
        let mut out = Vec::new();
        let mut scratch = PrimePairScratch::default();
        add_pairwise_prime(curve, &ps, &qs, &mut out, &mut scratch);
        for ((p, q), r) in ps.iter().zip(&qs).zip(&out) {
            assert_eq!(*r, curve.add_scalar(*p, *q));
        }
    }

    #[test]
    fn batched_three_summand_candidates_match_the_scalar_loop() {
        let inst = roster_prime_instance(18).unwrap();
        let curve = &inst.curve;
        let fb = prime_factor_base(&inst, 48);
        let table = PairTable::build_prime_batched(curve, &fb, true, 256).unwrap();
        let base = MontBase::new(curve, &fb.points).unwrap();
        let groups: Vec<&Vec<usize>> = fb
            .abscissa_list
            .iter()
            .map(|x| fb.x_index.get(x).unwrap())
            .collect();
        let g = inst.generator_point();
        let mut ops = GroupOps::default();
        let mut rng = StdRng::seed_from_u64(4);
        let mut targets: Vec<PrimePoint> = (0..200)
            .map(|_| curve.mul(&mut ops, g, rng.gen_range(1..inst.r)))
            .collect();
        // Targets on the base itself, both signs, and sums of two base
        // points so the probe has hits to find.
        targets.push(fb.points[0]);
        targets.push(fb.points[1]);
        targets.push(curve.add_scalar(fb.points[2], fb.points[5]));
        targets.push(curve.add_scalar(fb.points[3], curve.add_scalar(fb.points[8], fb.points[13])));
        let mut scratch = PrimeBatchScratch::default();
        for target in targets {
            // The candidates, in index order, are the scalar loop's points.
            let mut cands = Vec::new();
            prime_probe_candidates(&base, &groups, target, &mut scratch, &mut cands);
            assert_eq!(cands.len(), fb.points.len());
            for (k, (i, c)) in cands.iter().enumerate() {
                assert_eq!(*i, k);
                let s = curve.add_scalar(target, curve.neg(fb.points[k]));
                let want = if s.infinity { None } else { Some(s) };
                assert_eq!(*c, want, "target {target:?} index {k}");
            }
            // And the decomposition they yield is the scalar oracle's.
            let mut o1 = GroupOps::default();
            let mut c1 = OracleCounters::default();
            let scalar = decompose_mitm(curve, &fb, &table, 3, &mut o1, &mut c1, target);
            let mut o2 = GroupOps::default();
            let mut c2 = OracleCounters::default();
            let mut batched = None;
            for (i, c) in cands {
                let Some(s) = c else { continue };
                if let Some((j, k)) = table.probe(curve, &fb, &mut o2, &mut c2.lookups, s) {
                    batched = Some(vec![i, j, k]);
                    break;
                }
            }
            assert_eq!(batched, scalar);
            if let Some(w) = &batched {
                let sum = w
                    .iter()
                    .fold(PrimePoint::INFINITY, |acc, &i| curve.add_scalar(acc, fb.points[i]));
                assert_eq!(sum, target);
            }
        }
    }
}
