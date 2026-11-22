//! Hashed-affine factor bases and the Boolean tensor-contraction oracle.
//!
//! This is the plug-in end of `cryptanalysis::hashed_ecdl` and the vendored
//! `hashed-ecdl-tensor` crate: `hashed-affine` builds the union of `m`
//! independent affine-hashed slot bases, and `hashed-tensor` asks the exact
//! Boolean tensor network for a witness and maps it back to base indices.
//!
//! The construction follows Bochum v0.2 §3 (affine hash, inverse-hash
//! enumeration) and the October 25 manuscript Appendix D.4 (recursive
//! contraction), both as pinned by the crate. The tensor backend's work is
//! priced as measured wall nanoseconds (`hashed_tensor_ns`, one group-addition
//! equivalent per `ns_per_add` nanoseconds, like `affine_s3_ns`): the factor
//! base build (hash-prime certification and slot enumeration), the oracle's
//! `prepare` and every `decompose` call, failures included. The crate's own
//! curve additions and square roots happen inside those intervals, so they
//! are kept as diagnostics (`hashed_curve_additions`, `hashed_square_roots`)
//! and not charged a second time. `hashed_tensor_steps` stays as the crate's
//! uncalibrated primitive count. See docs/ic/FRAMEWORK.md.

use std::collections::BTreeMap;

use num_traits::{ToPrimitive, Zero};

use super::stages::{DecompositionOracle, FactorBaseBuilder, InstanceCtx, Params};
use crate::cryptanalysis::ic_boundary::{
    fast_map, CountedGroup, FactorBase, FastMap, GroupOps, OracleCounters, PrimeCurve,
    PrimeInstance, PrimePoint,
};
use hashed_ecdl_tensor as tensor;
use tensor::arithmetic::RandomSource;
use tensor::curve::{Curve as TensorCurve, Point as TensorPoint};
use tensor::reduction::{decompose, FactorBase as TensorBase, HashSeed};
use tensor::{BigUint, Limits, Meter};

/// Which exact engine answers a query and enumerates slots.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum Engine {
    /// The vendored crate: Boolean network, functional-leaf contraction.
    Tensor,
    /// The Lead 2C short-box join: native slot enumeration along the inverse
    /// hash coordinate `t in [0, tau)` and an exact ordered meet-in-the-middle
    /// over the enumerated slot lists. Same slots and same exact decision as
    /// `Tensor`, none of the Boolean-network cost.
    Join,
}

fn engine_of(params: &Params) -> Result<Engine, String> {
    match params.get("engine").unwrap_or("tensor") {
        "tensor" => Ok(Engine::Tensor),
        "join" => Ok(Engine::Join),
        other => Err(format!("engine must be `tensor` or `join`, not `{other}`")),
    }
}

/// How the hash prime `s` is certified.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum Cert {
    /// Deterministic Miller-Rabin with the first twelve prime bases (exact for
    /// every n < 3.3e24, so for every u64).
    MillerRabin,
    /// The crate's AKS implementation (exact for any size, very slow).
    Aks,
}

fn cert_of(params: &Params) -> Result<Cert, String> {
    match params.get("prime_cert").unwrap_or("mr") {
        "mr" => Ok(Cert::MillerRabin),
        "aks" => Ok(Cert::Aks),
        other => Err(format!("prime_cert must be `mr` or `aks`, not `{other}`")),
    }
}

fn mulmod64(a: u64, b: u64, m: u64) -> u64 {
    ((a as u128 * b as u128) % m as u128) as u64
}

fn powmod64(mut a: u64, mut e: u64, m: u64) -> u64 {
    let mut r = 1 % m;
    a %= m;
    while e > 0 {
        if e & 1 == 1 {
            r = mulmod64(r, a, m);
        }
        a = mulmod64(a, a, m);
        e >>= 1;
    }
    r
}

/// Deterministic Miller-Rabin for every `u64`. The bases 2,3,5,...,37 are a
/// proved witness set for all n < 3,317,044,064,679,887,385,961,981 (Sorenson
/// and Webster 2015), which exceeds 2^64. Exact, not probabilistic.
pub fn is_prime_u64(n: u64) -> bool {
    const BASES: [u64; 12] = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37];
    if n < 2 {
        return false;
    }
    for &q in &BASES {
        if n == q {
            return true;
        }
        if n % q == 0 {
            return false;
        }
    }
    let mut d = n - 1;
    let mut r = 0u32;
    while d % 2 == 0 {
        d /= 2;
        r += 1;
    }
    'bases: for &a in &BASES {
        let mut x = powmod64(a, d, n);
        if x == 1 || x == n - 1 {
            continue;
        }
        for _ in 1..r {
            x = mulmod64(x, x, n);
            if x == n - 1 {
                continue 'bases;
            }
        }
        return false;
    }
    true
}

/// Modular inverse of `a` modulo `m` (extended Euclid on i128).
fn inv_mod64(a: u64, m: u64) -> Option<u64> {
    let (mut old_r, mut r) = (a as i128, m as i128);
    let (mut old_s, mut s) = (1i128, 0i128);
    while r != 0 {
        let q = old_r / r;
        (old_r, r) = (r, old_r - q * r);
        (old_s, s) = (s, old_s - q * s);
    }
    if old_r != 1 {
        return None;
    }
    Some(old_s.rem_euclid(m as i128) as u64)
}

/// Default per-query contraction budget, in charged primitive steps.
const DEFAULT_STEPS: u64 = 50_000_000;
/// Default vector-length limit for one contraction.
const DEFAULT_VECTOR: usize = 2_000_000;
/// Default integer-width limit for one contraction.
const DEFAULT_BITS: usize = 1_000_000;

/// SplitMix64, byte-oriented so the tensor crate's square-root blinding can
/// draw from it. Deterministic from the plug-in's `seed`.
struct SeedRng(u64);
impl SeedRng {
    fn new(seed: u64) -> Self {
        Self(seed)
    }
    fn next_u64(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9e37_79b9_7f4a_7c15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
        z ^ (z >> 31)
    }
    fn below(&mut self, n: u64) -> u64 {
        let threshold = n.wrapping_neg() % n;
        loop {
            let x = self.next_u64();
            if x >= threshold {
                return x % n;
            }
        }
    }
}
impl RandomSource for SeedRng {
    fn fill(&mut self, bytes: &mut [u8]) -> tensor::Result<()> {
        for chunk in bytes.chunks_mut(8) {
            let word = self.next_u64().to_le_bytes();
            let n = chunk.len();
            chunk.copy_from_slice(&word[..n]);
        }
        Ok(())
    }
}

/// One instance's slot parameters: the shared hash prime `s`, threshold `tau`
/// and one `(alpha, beta)` per ordered slot.
struct SlotSpec {
    slots: usize,
    prime: BigUint,
    threshold: BigUint,
    seeds: Vec<HashSeed>,
}

fn limits_from(params: &Params) -> Result<Limits, String> {
    let steps = params.u64_or("steps", DEFAULT_STEPS)?;
    if steps == 0 {
        return Err("steps must be positive".into());
    }
    Ok(Limits {
        steps,
        vector: DEFAULT_VECTOR,
        bits: DEFAULT_BITS,
    })
}

fn big(v: u64) -> BigUint {
    BigUint::from(v)
}

/// Certify `n` prime: deterministic Miller-Rabin for a machine word, or the
/// crate's AKS (any size). Both are exact.
fn certify(n: &BigUint, cert: Cert, meter: &mut Meter) -> Result<bool, String> {
    match (cert, n.to_u64()) {
        (Cert::MillerRabin, Some(v)) => Ok(is_prime_u64(v)),
        _ => tensor::arithmetic::is_prime(n, meter).map_err(|e| format!("hash prime: {e}")),
    }
}

/// The smallest prime in `[2p, 4p]`.
fn hash_prime(p: &BigUint, cert: Cert, meter: &mut Meter) -> Result<BigUint, String> {
    let lower = p << 1;
    let upper = p << 2;
    let mut candidate = lower;
    while candidate <= upper {
        if certify(&candidate, cert, meter)? {
            return Ok(candidate);
        }
        candidate += BigUint::from(1u8);
    }
    Err("no affine-hash prime in [2p, 4p]".into())
}

/// Derive the slot parameters exactly as the reference reduction does:
/// `s` the first prime in `[2p, 4p]`, `tau = ceil(s*max(ceil(r^(1/m)),10m)/(r-1))`,
/// then SplitMix64 draws for `(alpha, beta)`.
fn slot_spec(ctx: &InstanceCtx<'_, PrimeCurve>, params: &Params) -> Result<SlotSpec, String> {
    let slots = params.u64_or("slots", 2)? as usize;
    if !(2..=8).contains(&slots) {
        return Err("slots must lie in 2..=8".into());
    }
    let seed = params.u64_or("seed", 1)?;
    let cert = cert_of(params)?;
    let mut meter = Meter::new(limits_from(params)?);
    let p = big(ctx.group.p);
    let r = big(ctx.r);
    let prime = match params.get("s") {
        Some(raw) => {
            let value: BigUint = raw
                .parse()
                .map_err(|_| format!("s is not an integer: `{raw}`"))?;
            if value < (&p << 1) || value > (&p << 2) || value.to_u64().is_none() {
                return Err("s must be an integer in [2p, 4p]".into());
            }
            if !certify(&value, cert, &mut meter)? {
                return Err("s must be prime".into());
            }
            value
        }
        None => hash_prime(&p, cert, &mut meter)?,
    };
    let s_u64 = prime.to_u64().ok_or_else(|| {
        "hash prime exceeds one word; this plug-in is limited to p < 2^61".to_string()
    })?;
    let mut root = BigUint::from(1u8);
    let m = u32::try_from(slots).map_err(|_| "slots out of range".to_string())?;
    while root.pow(m) < r {
        root += BigUint::from(1u8);
    }
    let floor = BigUint::from(10 * slots as u64);
    let expected = root.max(floor);
    let threshold = match params.get("tau") {
        Some(raw) => {
            let value: BigUint = raw
                .parse()
                .map_err(|_| format!("tau is not an integer: `{raw}`"))?;
            if value.is_zero() || value > prime {
                return Err("tau must lie in 1..=s".into());
            }
            value
        }
        None => {
            let numerator = &prime * &expected;
            let denominator = &r - BigUint::from(1u8);
            let (q, rem) = num_integer::Integer::div_rem(&numerator, &denominator);
            let mut value = q;
            if !rem.is_zero() {
                value += BigUint::from(1u8);
            }
            value.min(prime.clone())
        }
    };
    let mut rng = SeedRng::new(seed);
    let seeds = (0..slots)
        .map(|_| HashSeed {
            alpha: big(1 + rng.below(s_u64 - 1)),
            beta: big(rng.below(s_u64)),
        })
        .collect();
    Ok(SlotSpec {
        slots,
        prime,
        threshold,
        seeds,
    })
}

fn tensor_curve(ctx: &InstanceCtx<'_, PrimeCurve>, limits: &Limits) -> Result<TensorCurve, String> {
    let mut meter = Meter::new(limits.clone());
    let generator = TensorPoint::Affine {
        x: big(ctx.generator.x),
        y: big(ctx.generator.y),
    };
    TensorCurve::with_cofactor(
        big(ctx.group.p),
        big(ctx.group.a),
        big(ctx.group.b),
        big(ctx.r),
        big(ctx.cofactor),
        generator,
        &mut meter,
    )
    .map_err(|e| format!("hashed-tensor curve: {e}"))
}

fn tensor_bases(
    curve: &TensorCurve,
    spec: &SlotSpec,
    meter: &mut Meter,
) -> Result<Vec<TensorBase>, String> {
    spec.seeds
        .iter()
        .map(|seed| {
            TensorBase::new(
                curve,
                spec.prime.clone(),
                spec.threshold.clone(),
                seed.clone(),
                meter,
            )
            .map_err(|e| format!("hashed-tensor base: {e}"))
        })
        .collect()
}

fn prime_point(point: &TensorPoint) -> Result<PrimePoint, String> {
    match point {
        TensorPoint::Infinity => Ok(PrimePoint::INFINITY),
        TensorPoint::Affine { x, y } => {
            let x = x
                .to_u64()
                .ok_or("hashed point coordinate exceeds one word")?;
            let y = y
                .to_u64()
                .ok_or("hashed point coordinate exceeds one word")?;
            Ok(PrimePoint::affine(x, y))
        }
    }
}

/// The crate path's whole setup: certified curve, certified slot bases (the
/// crate's `FactorBase::new` certifies `s` with AKS and cannot be bypassed)
/// and the enumerated slot lists, in slot order. Returns the crate's charged
/// steps, curve additions and square roots across all three.
type TensorSetup = (
    TensorCurve,
    Vec<TensorBase>,
    Vec<Vec<PrimePoint>>,
    u64,
    u64,
    u64,
);

fn tensor_setup(
    ctx: &InstanceCtx<'_, PrimeCurve>,
    spec: &SlotSpec,
    params: &Params,
) -> Result<TensorSetup, String> {
    let limits = limits_from(params)?;
    let cert_limits = Limits {
        steps: params.u64_or("cert_steps", limits.steps)?,
        ..limits.clone()
    };
    let curve = tensor_curve(ctx, &limits)?;
    let mut cert = Meter::new(cert_limits);
    let bases = tensor_bases(&curve, spec, &mut cert)?;
    let mut meter = Meter::new(limits);
    let mut rng = SeedRng::new(0x5eed_0000 ^ spec.slots as u64);
    let mut out = Vec::with_capacity(bases.len());
    for base in &bases {
        let points = base
            .enumerate(&curve, &mut rng, &mut meter)
            .map_err(|e| format!("hashed-tensor enumeration: {e}"))?;
        out.push(
            points
                .iter()
                .map(prime_point)
                .collect::<Result<Vec<_>, _>>()?,
        );
    }
    let steps = meter.used + cert.used;
    let additions = meter.curve_additions + cert.curve_additions;
    let roots = meter.square_roots + cert.square_roots;
    Ok((curve, bases, out, steps, additions, roots))
}

/// Short-box slot enumeration, native. Slot membership is
/// `(alpha*z + beta) mod s < tau` for the compressed encoding `z = 2x + y0`,
/// so the accepted labels are `z = alpha^-1 (t - beta) mod s` for the short
/// coordinate `t in [0, tau)`: one integer coordinate per slot, `z < 2p` and a
/// parity per label. No Boolean hash circuit and no `BigUint`: the same
/// points the crate's `FactorBase::enumerate` returns, in the same
/// (x, y)-sorted order, by u64/u128 arithmetic. Returns the slot lists, the
/// number of labels visited and the number of square roots taken.
fn native_slots(
    ctx: &InstanceCtx<'_, PrimeCurve>,
    spec: &SlotSpec,
) -> Result<(Vec<Vec<PrimePoint>>, u64, u64), String> {
    let s = spec.prime.to_u64().ok_or("hash prime exceeds one word")?;
    let tau = spec
        .threshold
        .to_u64()
        .ok_or("threshold exceeds one word")?;
    if tau as usize > DEFAULT_VECTOR {
        return Err("factor-base size: resource limit".into());
    }
    let p = ctx.group.p;
    let mut ops = GroupOps::default();
    let (mut labels, mut roots) = (0u64, 0u64);
    let mut out = Vec::with_capacity(spec.seeds.len());
    for seed in &spec.seeds {
        let alpha = seed.alpha.to_u64().ok_or("alpha exceeds one word")?;
        let beta = seed.beta.to_u64().ok_or("beta exceeds one word")?;
        let inv = inv_mod64(alpha, s).ok_or("alpha is not invertible modulo s")?;
        let mut points = Vec::new();
        for t in 0..tau {
            labels += 1;
            let z = mulmod64(inv, (t + s - beta % s) % s, s);
            if z >= 2 * p {
                continue;
            }
            let x = z >> 1;
            roots += 1;
            let Some(mut y) = ctx.group.sqrt(ctx.group.rhs(x)) else {
                continue;
            };
            if y & 1 != z & 1 {
                y = (p - y) % p;
            }
            if y & 1 != z & 1 {
                continue;
            }
            let point = PrimePoint::affine(x, y);
            if !ctx.group.is_on_curve(point) {
                return Err("compressed point replay".into());
            }
            // Subgroup test, as the crate's `in_subgroup`.
            if !ctx.group.mul(&mut ops, point, ctx.r).infinity {
                continue;
            }
            points.push(point);
        }
        points.sort_unstable_by_key(|q| (q.x, q.y));
        if points.windows(2).any(|w| w[0] == w[1]) {
            return Err("inverse hash produced duplicate points".into());
        }
        out.push(points);
    }
    Ok((out, labels, roots))
}

/// Exact ordered join over the slot lists. The left half (the first
/// `ceil(m/2)` slots) is tabulated once, keyed by the sum point; a query
/// walks the right half carrying `target - partial sum` and probes the table.
/// A miss over the whole right box is a certificate that no ordered witness
/// exists, exactly like the crate's `Ok(None)`.
struct Join {
    lists: Vec<Vec<PrimePoint>>,
    split: usize,
    /// Left tuples, `split` list positions per row.
    rows: Vec<u32>,
    index: FastMap<u32>,
}

impl Join {
    fn build(
        group: &PrimeCurve,
        lists: Vec<Vec<PrimePoint>>,
        table_cap: u64,
        query_cap: u64,
        adds: &mut u64,
    ) -> Result<Self, String> {
        let m = lists.len();
        let split = m.div_ceil(2);
        let size = |range: &[Vec<PrimePoint>]| -> u128 {
            range.iter().map(|l| l.len() as u128).product::<u128>()
        };
        if size(&lists[..split]) > u128::from(table_cap) {
            return Err(format!(
                "join table has {} rows, over table_cap {table_cap}: resource limit",
                size(&lists[..split])
            ));
        }
        if size(&lists[split..]) > u128::from(query_cap) {
            return Err(format!(
                "join query walks {} tuples, over query_cap {query_cap}: resource limit",
                size(&lists[split..])
            ));
        }
        let rows_total = size(&lists[..split]) as usize;
        let mut join = Join {
            lists,
            split,
            rows: Vec::with_capacity(rows_total * split),
            index: fast_map(rows_total),
        };
        let mut ops = GroupOps::default();
        let mut tuple = vec![0u32; split];
        join.fill(group, &mut ops, 0, PrimePoint::INFINITY, &mut tuple);
        *adds += ops.adds;
        Ok(join)
    }

    fn fill(
        &mut self,
        group: &PrimeCurve,
        ops: &mut GroupOps,
        depth: usize,
        partial: PrimePoint,
        tuple: &mut Vec<u32>,
    ) {
        if depth == self.split {
            let row = (self.rows.len() / self.split) as u32;
            if let std::collections::hash_map::Entry::Vacant(e) =
                self.index.entry(group.key(&partial))
            {
                e.insert(row);
                self.rows.extend_from_slice(tuple);
            }
            return;
        }
        for i in 0..self.lists[depth].len() {
            let next = group.add(ops, partial, self.lists[depth][i]);
            tuple[depth] = i as u32;
            self.fill(group, ops, depth + 1, next, tuple);
        }
    }

    /// One ordered witness (a list position per slot) for `target`, if any.
    fn query(
        &self,
        group: &PrimeCurve,
        ops: &mut GroupOps,
        probes: &mut u64,
        target: PrimePoint,
    ) -> Option<Vec<usize>> {
        let mut tuple = vec![0u32; self.lists.len() - self.split];
        let row = self.walk(group, ops, probes, self.split, target, &mut tuple)?;
        let mut out: Vec<usize> = self.rows[row as usize * self.split..][..self.split]
            .iter()
            .map(|&i| i as usize)
            .collect();
        out.extend(tuple.iter().map(|&i| i as usize));
        Some(out)
    }

    fn walk(
        &self,
        group: &PrimeCurve,
        ops: &mut GroupOps,
        probes: &mut u64,
        depth: usize,
        rest: PrimePoint,
        tuple: &mut Vec<u32>,
    ) -> Option<u32> {
        if depth == self.lists.len() {
            *probes += 1;
            return self.index.get(&group.key(&rest)).copied();
        }
        for i in 0..self.lists[depth].len() {
            let next = group.add(ops, rest, group.neg(self.lists[depth][i]));
            tuple[depth - self.split] = i as u32;
            if let Some(row) = self.walk(group, ops, probes, depth + 1, next, tuple) {
                return Some(row);
            }
        }
        None
    }
}

/// The union of `slots` affine-hashed bases, one column per point.
pub struct HashedAffineBase<'i> {
    pub instance: &'i PrimeInstance,
}

impl FactorBaseBuilder<PrimeCurve> for HashedAffineBase<'_> {
    fn name(&self) -> &str {
        "hashed-affine"
    }

    fn describe(&self, params: &Params) -> String {
        format!(
            "union of {} independent affine-hashed slot bases, one column per point",
            params.get("slots").unwrap_or("2")
        )
    }

    fn parameters(&self) -> &[(&str, &str)] {
        &[
            (
                "slots",
                "independent ordered factor bases, 2..=8; must equal the oracle's slots",
            ),
            ("seed", "SplitMix64 seed for the hash seeds; default 1"),
            (
                "tau",
                "shared threshold; default the Lemma 13 integer ceiling",
            ),
            (
                "s",
                "shared hash prime in [2p,4p]; default the first prime there",
            ),
            (
                "steps",
                "enumeration work budget in charged primitive steps",
            ),
            (
                "cert_steps",
                "engine=tensor only: separate step budget for the crate's AKS certification of s inside each slot base; default `steps`",
            ),
            (
                "engine",
                "`tensor` (default, the crate's Boolean contraction) or `join` (short-box native slot enumeration and an exact ordered meet-in-the-middle); must equal the other stage's",
            ),
            (
                "prime_cert",
                "`mr` (default, deterministic Miller-Rabin, exact for every u64) or `aks` (the crate's AKS) for the hash prime s",
            ),
        ]
    }

    fn build(
        &self,
        ctx: &InstanceCtx<PrimeCurve>,
        params: &Params,
        ops: &mut GroupOps,
    ) -> Result<FactorBase<PrimePoint>, String> {
        let started = std::time::Instant::now();
        let _ = &ops; // all native work is priced as measured ns below
        let engine = engine_of(params)?;
        let spec = slot_spec(ctx, params)?;
        let (slots, steps, additions, square_roots) = match engine {
            Engine::Tensor => {
                let (_, _, slots, steps, additions, roots) = tensor_setup(ctx, &spec, params)?;
                (slots, steps, additions, roots)
            }
            Engine::Join => {
                let (slots, labels, roots) = native_slots(ctx, &spec)?;
                (slots, labels, 0, roots)
            }
        };
        let starting_wall = std::time::Instant::now();
        let mut fb = FactorBase::empty(self.describe(params));
        fb.columns = slots.iter().map(Vec::len).sum();
        fb.points = slots.into_iter().flatten().collect();
        fb.col_of = (0..fb.points.len()).collect();
        fb.coef_of = vec![1; fb.points.len()];
        let mut point_index = fast_map(fb.points.len());
        let mut x_index: FastMap<Vec<usize>> = fast_map(fb.points.len());
        for (i, point) in fb.points.iter().enumerate() {
            point_index
                .entry(self.instance.curve.key(point))
                .or_insert(i);
            x_index.entry(point.x).or_default().push(i);
        }
        fb.neg_index = fb
            .points
            .iter()
            .enumerate()
            .map(|(i, point)| {
                let neg = self.instance.curve.neg(*point);
                point_index
                    .get(&self.instance.curve.key(&neg))
                    .copied()
                    .unwrap_or(i)
            })
            .collect();
        fb.abscissae = x_index.len();
        fb.abscissa_list = x_index.keys().copied().collect();
        fb.abscissa_list.sort_unstable();
        fb.point_index = point_index;
        fb.x_index = x_index;
        fb.cost.count("hashed_slots", spec.slots as u64);
        fb.cost.count("hashed_points", fb.points.len() as u64);
        fb.cost.count(
            if engine == Engine::Join {
                "hashed_join_labels"
            } else {
                "hashed_tensor_steps"
            },
            steps,
        );
        fb.cost.count("hashed_curve_additions", additions);
        fb.cost.count("hashed_square_roots", square_roots);
        let _ = starting_wall;
        let native = started.elapsed().as_nanos() as u64;
        fb.cost.count("hashed_tensor_ns", native);
        fb.cost.wall_ns = native;
        Ok(fb)
    }
}

/// The exact Boolean tensor-contraction oracle over the same slot bases.
#[derive(Default)]
pub struct HashedTensorOracle {
    curve: Option<TensorCurve>,
    bases: Vec<TensorBase>,
    limits: Option<Limits>,
    slots: Vec<Vec<PrimePoint>>,
    slot_index: Vec<std::collections::HashMap<u64, usize>>,
    setup_steps: u64,
    setup_square_roots: u64,
    setup_additions: u64,
    setup_ns: u64,
    relation_steps: u64,
    relation_ns: u64,
    relation_additions: u64,
    relation_square_roots: u64,
    limit_hits: u64,
    integrity_failures: u64,
    join: Option<Join>,
    join_adds: u64,
    join_probes: u64,
}

impl HashedTensorOracle {
    pub fn new() -> Self {
        Self::default()
    }
}

impl DecompositionOracle<PrimeCurve> for HashedTensorOracle {
    fn name(&self) -> &str {
        "hashed-tensor"
    }

    fn summands(&self) -> u32 {
        self.slots.len().max(2) as u32
    }

    fn describe(&self, params: &Params) -> String {
        format!(
            "exact Boolean tensor contraction over {} affine-hashed slot bases",
            params.get("slots").unwrap_or("2")
        )
    }

    fn parameters(&self) -> &[(&str, &str)] {
        &[
            (
                "slots",
                "independent ordered factor bases, 2..=8; must equal the factor base's slots",
            ),
            ("seed", "SplitMix64 seed for the hash seeds; default 1"),
            ("tau", "shared threshold; must equal the factor base's tau"),
            ("s", "shared hash prime; must equal the factor base's s"),
            (
                "steps",
                "per-target contraction budget in charged primitive steps",
            ),
            (
                "cert_steps",
                "engine=tensor only: separate step budget for the crate's AKS certification of s; default `steps`",
            ),
            (
                "engine",
                "`tensor` (default, the crate's Boolean contraction) or `join` (short-box native slot enumeration and an exact ordered meet-in-the-middle); must equal the other stage's",
            ),
            (
                "prime_cert",
                "`mr` (default, deterministic Miller-Rabin, exact for every u64) or `aks` (the crate's AKS) for the hash prime s",
            ),
            (
                "table_cap",
                "engine=join: most left-half tuples tabulated, default 4000000",
            ),
            (
                "query_cap",
                "engine=join: most right-half tuples one query may walk, default 4194304",
            ),
        ]
    }

    fn prepare(
        &mut self,
        ctx: &InstanceCtx<PrimeCurve>,
        fb: &FactorBase<PrimePoint>,
        params: &Params,
        ops: &mut GroupOps,
    ) -> Result<(), String> {
        let started = std::time::Instant::now();
        let _ = &ops; // priced as measured ns (setup_native)
        let engine = engine_of(params)?;
        let limits = limits_from(params)?;
        let spec = slot_spec(ctx, params)?;
        let (slots, steps, additions, square_roots) = match engine {
            Engine::Tensor => {
                let (curve, bases, slots, steps, additions, roots) =
                    tensor_setup(ctx, &spec, params)?;
                self.bases = bases;
                self.curve = Some(curve);
                (slots, steps, additions, roots)
            }
            Engine::Join => {
                let (slots, labels, roots) = native_slots(ctx, &spec)?;
                (slots, labels, 0, roots)
            }
        };
        self.setup_additions = additions;
        let all: Vec<PrimePoint> = slots.iter().flatten().copied().collect();
        if all != fb.points {
            return Err(
                "hashed-tensor requires `hashed-affine` with identical slots, seed, tau, s and engine"
                    .into(),
            );
        }
        if engine == Engine::Join {
            let table_cap = params.u64_or("table_cap", 4_000_000)?;
            let query_cap = params.u64_or("query_cap", 4_194_304)?;
            let mut adds = 0;
            self.join = Some(Join::build(
                ctx.group,
                slots.clone(),
                table_cap,
                query_cap,
                &mut adds,
            )?);
            self.setup_additions = adds;
        }
        self.slot_index = slots
            .iter()
            .map(|points| {
                points
                    .iter()
                    .enumerate()
                    .map(|(i, point)| (ctx.group.key(point), i))
                    .collect()
            })
            .collect();
        self.slots = slots;
        self.limits = Some(limits);
        self.setup_steps = steps;
        self.setup_square_roots = square_roots;
        self.setup_ns = started.elapsed().as_nanos() as u64;
        Ok(())
    }

    fn setup_native(&self) -> BTreeMap<String, u64> {
        let mut out = BTreeMap::new();
        if self.setup_steps > 0 {
            out.insert("hashed_tensor_steps".to_string(), self.setup_steps);
        }
        if self.setup_square_roots > 0 {
            out.insert("hashed_square_roots".to_string(), self.setup_square_roots);
        }
        out.insert("hashed_curve_additions".to_string(), self.setup_additions);
        out.insert("hashed_tensor_ns".to_string(), self.setup_ns);
        if self.join.is_some() {
            out.remove("hashed_tensor_steps");
            out.insert("hashed_join_labels".to_string(), self.setup_steps);
        }
        out
    }

    fn decompose(
        &mut self,
        ctx: &InstanceCtx<PrimeCurve>,
        _fb: &FactorBase<PrimePoint>,
        ops: &mut GroupOps,
        counters: &mut OracleCounters,
        point: PrimePoint,
    ) -> Option<Vec<usize>> {
        let started = std::time::Instant::now();
        let result = self.decompose_inner(ctx, ops, counters, point);
        self.relation_ns = self
            .relation_ns
            .saturating_add(started.elapsed().as_nanos() as u64);
        result
    }

    fn relation_counters(&self) -> BTreeMap<String, u64> {
        let mut out = BTreeMap::new();
        out.insert("hashed_tensor_steps".to_string(), self.relation_steps);
        out.insert("hashed_tensor_ns".to_string(), self.relation_ns);
        out.insert(
            "hashed_curve_additions".to_string(),
            self.relation_additions,
        );
        out.insert(
            "hashed_square_roots".to_string(),
            self.relation_square_roots,
        );
        out.insert("hashed_limit_hits".to_string(), self.limit_hits);
        out.insert(
            "hashed_integrity_failures".to_string(),
            self.integrity_failures,
        );
        if self.join.is_some() {
            out.insert("hashed_join_adds".to_string(), self.join_adds);
            out.insert("hashed_join_probes".to_string(), self.join_probes);
        }
        out
    }
}

impl HashedTensorOracle {
    /// One query. Its wall time, crate curve additions and square roots
    /// included, is charged by `decompose` as `hashed_tensor_ns`.
    fn decompose_inner(
        &mut self,
        ctx: &InstanceCtx<PrimeCurve>,
        _ops: &mut GroupOps,
        _counters: &mut OracleCounters,
        point: PrimePoint,
    ) -> Option<Vec<usize>> {
        if let Some(join) = &self.join {
            if point.infinity {
                return None;
            }
            let mut ops = GroupOps::default();
            let found = join.query(ctx.group, &mut ops, &mut self.join_probes, point);
            self.join_adds += ops.adds;
            let positions = found?;
            // Integrity: every position is in range and the ordered sum is the target.
            let mut sum = PrimePoint::INFINITY;
            let mut indices = Vec::with_capacity(positions.len());
            let mut offset = 0usize;
            for (slot, &local) in positions.iter().enumerate() {
                let Some(member) = join.lists[slot].get(local) else {
                    self.integrity_failures += 1;
                    return None;
                };
                sum = ctx.group.add(&mut ops, sum, *member);
                indices.push(offset + local);
                offset += join.lists[slot].len();
            }
            if sum != point {
                self.integrity_failures += 1;
                return None;
            }
            return Some(indices);
        }
        let curve = self.curve.as_ref()?;
        if point.infinity || self.bases.is_empty() {
            return None;
        }
        let target = TensorPoint::Affine {
            x: big(point.x),
            y: big(point.y),
        };
        let mut meter = Meter::new(self.limits.clone()?);
        let mut counter = tensor::contraction::Counter::default();
        let witness = decompose(curve, &self.bases, &target, &mut counter, &mut meter);
        self.relation_steps = self.relation_steps.saturating_add(meter.used);
        self.relation_additions = self
            .relation_additions
            .saturating_add(meter.curve_additions);
        self.relation_square_roots = self
            .relation_square_roots
            .saturating_add(meter.square_roots);
        match witness {
            Ok(None) => None,
            Ok(Some(points)) => {
                if points.len() != self.slots.len() {
                    self.integrity_failures += 1;
                    return None;
                }
                let mut indices = Vec::with_capacity(points.len());
                for (slot, point) in points.iter().enumerate() {
                    let point = match prime_point(point) {
                        Ok(point) => point,
                        Err(_) => {
                            self.integrity_failures += 1;
                            return None;
                        }
                    };
                    let key = ctx.group.key(&point);
                    let Some(local) = self
                        .slot_index
                        .get(slot)
                        .and_then(|index| index.get(&key))
                        .copied()
                    else {
                        self.integrity_failures += 1;
                        return None;
                    };
                    let offset: usize = self.slots[..slot].iter().map(Vec::len).sum();
                    indices.push(offset + local);
                }
                Some(indices)
            }
            Err(tensor::Error::Limit(_)) => {
                self.limit_hits += 1;
                None
            }
            Err(_) => {
                self.integrity_failures += 1;
                None
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::ic_boundary::find_prime_order_curve;

    fn sieve(limit: usize) -> Vec<bool> {
        let mut is = vec![true; limit + 1];
        is[0] = false;
        is[1] = false;
        let mut i = 2;
        while i * i <= limit {
            if is[i] {
                let mut j = i * i;
                while j <= limit {
                    is[j] = false;
                    j += i;
                }
            }
            i += 1;
        }
        is
    }

    #[test]
    fn miller_rabin_matches_sieve() {
        let limit = 3_000_000usize;
        let is = sieve(limit);
        for n in 0..=limit {
            assert_eq!(is_prime_u64(n as u64), is[n], "n = {n}");
        }
    }

    #[test]
    fn miller_rabin_rejects_strong_pseudoprimes_and_carmichaels() {
        // Strong pseudoprimes to the first k prime bases, Carmichael numbers,
        // and prime squares: every one is composite.
        for n in [
            561u64,
            1105,
            1729,
            41041,
            825_265,
            321_197_185,
            5_394_826_801,
            2047,
            1_373_653,
            25_326_001,
            3_215_031_751,
            2_152_302_898_747,
            3_474_749_660_383,
            341_550_071_728_321,
            3_825_123_056_546_413_051,
            4_295_098_369,
            4_294_967_297,
        ] {
            assert!(!is_prime_u64(n), "composite {n} accepted");
        }
    }

    #[test]
    fn miller_rabin_accepts_large_primes() {
        for n in [
            2_147_483_647u64,
            4_294_967_291,
            (1u64 << 61) - 1,
            9_223_372_036_854_775_783,
            18_446_744_073_709_551_557,
        ] {
            assert!(is_prime_u64(n), "prime {n} rejected");
        }
        assert!(!is_prime_u64(u64::MAX));
        assert!(!is_prime_u64(1u64 << 63));
        // (2^31 - 1)^2 and a product of the two largest 32-bit primes.
        assert!(!is_prime_u64(2_147_483_647u64 * 2_147_483_647));
        assert!(!is_prime_u64(4_294_967_291u64 * 4_294_967_279));
    }

    #[test]
    fn miller_rabin_agrees_with_aks_above_sixteen_bits() {
        let limits = Limits {
            steps: 2_000_000_000,
            vector: DEFAULT_VECTOR,
            bits: DEFAULT_BITS,
        };
        for n in [65_537u64, 65_539, 100_003, 100_005, 131_071, 131_073] {
            let mut meter = Meter::new(limits.clone());
            let aks = tensor::arithmetic::is_prime(&BigUint::from(n), &mut meter).unwrap();
            assert_eq!(is_prime_u64(n), aks, "n = {n}");
        }
    }

    #[test]
    fn certify_modes_pick_the_same_hash_prime() {
        let limits = Limits {
            steps: 2_000_000_000,
            vector: DEFAULT_VECTOR,
            bits: DEFAULT_BITS,
        };
        for p in [251u64, 1009, 4093, 8191] {
            let mr = hash_prime(&big(p), Cert::MillerRabin, &mut Meter::new(limits.clone()));
            let aks = hash_prime(&big(p), Cert::Aks, &mut Meter::new(limits.clone()));
            assert_eq!(mr, aks, "p = {p}");
        }
    }

    #[test]
    fn modular_inverse_is_exact() {
        for (a, m) in [
            (3u64, 7u64),
            (5, 1_000_003),
            (123_456_789, 2_305_843_009_213_693_951),
        ] {
            let inv = inv_mod64(a, m).unwrap();
            assert_eq!(mulmod64(a, inv, m), 1);
        }
        assert!(inv_mod64(6, 9).is_none());
    }

    fn params(pairs: &[(&str, &str)]) -> Params {
        Params(
            pairs
                .iter()
                .map(|(k, v)| (k.to_string(), v.to_string()))
                .collect(),
        )
    }

    fn with_ctx<R>(bits: u32, f: impl FnOnce(&InstanceCtx<'_, PrimeCurve>) -> R) -> R {
        let inst = find_prime_order_curve(bits, 7);
        let g = inst.generator_point();
        let ctx = InstanceCtx {
            group: &inst.curve,
            generator: g,
            target: g,
            r: inst.r,
            cofactor: inst.cofactor,
            group_order: inst.group_order,
            name: inst.name.clone(),
            field_degree: None,
        };
        f(&ctx)
    }

    #[test]
    fn native_enumeration_equals_the_crate_enumeration() {
        for bits in [8u32, 10, 12] {
            with_ctx(bits, |ctx| {
                for slots in [2usize, 3] {
                    let p = params(&[("slots", &slots.to_string()), ("seed", "5")]);
                    let spec = slot_spec(ctx, &p).unwrap();
                    let (_, _, crate_slots, _, _, _) = tensor_setup(ctx, &spec, &p).unwrap();
                    let (native, _, _) = native_slots(ctx, &spec).unwrap();
                    assert_eq!(crate_slots, native, "bits {bits} slots {slots}");
                }
            });
        }
    }

    /// The join answers `Some` exactly when an ordered witness exists, and
    /// every witness sums to the target.
    #[test]
    fn join_is_an_exact_decision() {
        for (bits, slots) in [(8u32, 2usize), (9, 2), (10, 3)] {
            with_ctx(bits, |ctx| {
                let p = params(&[("slots", &slots.to_string()), ("seed", "3")]);
                let spec = slot_spec(ctx, &p).unwrap();
                let (lists, _, _) = native_slots(ctx, &spec).unwrap();
                let mut adds = 0;
                let join =
                    Join::build(ctx.group, lists.clone(), 4_000_000, 4_194_304, &mut adds).unwrap();
                // Brute force: every reachable sum.
                let mut reachable = std::collections::HashSet::new();
                let mut ops = GroupOps::default();
                let mut stack = vec![(0usize, PrimePoint::INFINITY)];
                while let Some((depth, sum)) = stack.pop() {
                    if depth == slots {
                        reachable.insert(ctx.group.key(&sum));
                        continue;
                    }
                    for q in &lists[depth] {
                        stack.push((depth + 1, ctx.group.add(&mut ops, sum, *q)));
                    }
                }
                let (mut hit, mut miss) = (0, 0);
                let mut point = PrimePoint::INFINITY;
                for _ in 0..ctx.r {
                    point = ctx.group.add(&mut ops, point, ctx.generator);
                    if point.infinity {
                        continue;
                    }
                    let mut probes = 0;
                    let found = join.query(ctx.group, &mut ops, &mut probes, point);
                    assert_eq!(found.is_some(), reachable.contains(&ctx.group.key(&point)));
                    if let Some(positions) = found {
                        hit += 1;
                        let mut sum = PrimePoint::INFINITY;
                        for (slot, &i) in positions.iter().enumerate() {
                            sum = ctx.group.add(&mut ops, sum, lists[slot][i]);
                        }
                        assert_eq!(sum, point);
                    } else {
                        miss += 1;
                    }
                }
                assert!(hit > 0, "bits {bits} slots {slots}: no witnesses at all");
                eprintln!("bits {bits} slots {slots}: {hit} decomposable, {miss} not");
            });
        }
    }

    #[test]
    fn join_refuses_oversize_tables() {
        with_ctx(10, |ctx| {
            let p = params(&[("slots", "2")]);
            let spec = slot_spec(ctx, &p).unwrap();
            let (lists, _, _) = native_slots(ctx, &spec).unwrap();
            let mut adds = 0;
            assert!(Join::build(ctx.group, lists.clone(), 1, 1 << 22, &mut adds).is_err());
            assert!(Join::build(ctx.group, lists, 1 << 22, 1, &mut adds).is_err());
        });
    }

    /// Timing helper, not a test: `cargo test --release hashed::tests::setup_timing -- --ignored --nocapture`.
    #[test]
    #[ignore]
    fn setup_timing() {
        for bits in [16u32, 18] {
            with_ctx(bits, |ctx| {
                let big_limits = Limits {
                    steps: 40_000_000_000,
                    vector: DEFAULT_VECTOR,
                    bits: DEFAULT_BITS,
                };
                let p = big(ctx.group.p);
                for (name, cert) in [("mr", Cert::MillerRabin), ("aks", Cert::Aks)] {
                    let t = std::time::Instant::now();
                    let s = hash_prime(&p, cert, &mut Meter::new(big_limits.clone())).unwrap();
                    eprintln!("bits {bits} hash_prime {name}: {:?} (s = {s})", t.elapsed());
                }
                let pr = params(&[
                    ("slots", "2"),
                    ("steps", "40000000000"),
                    ("prime_cert", "mr"),
                ]);
                let spec = slot_spec(ctx, &pr).unwrap();
                let t = std::time::Instant::now();
                let (_, _, slots, steps, _, _) = tensor_setup(ctx, &spec, &pr).unwrap();
                eprintln!(
                    "bits {bits} crate setup (curve, 2 slot bases with AKS, enumeration): {:?}, steps {steps}, points {}",
                    t.elapsed(),
                    slots.iter().map(Vec::len).sum::<usize>()
                );
                let t = std::time::Instant::now();
                let (native, _, _) = native_slots(ctx, &spec).unwrap();
                eprintln!(
                    "bits {bits} native slots: {:?}, equal to crate: {}",
                    t.elapsed(),
                    native == slots
                );
            });
        }
    }

    /// Size of the crate's exact-fallback search space, not a test:
    /// `cargo test --release hashed::tests::network_size -- --ignored --nocapture`.
    #[test]
    #[ignore]
    fn network_size() {
        for bits in [8u32, 10, 12, 16] {
            with_ctx(bits, |ctx| {
                for slots in [2usize, 3] {
                    let pr = params(&[("slots", &slots.to_string())]);
                    let spec = slot_spec(ctx, &pr).unwrap();
                    let limits = Limits {
                        steps: u64::MAX / 2,
                        vector: DEFAULT_VECTOR,
                        bits: DEFAULT_BITS,
                    };
                    let curve = tensor_curve(ctx, &limits).unwrap();
                    let mut cert = Meter::new(limits.clone());
                    let bases = tensor_bases(&curve, &spec, &mut cert).unwrap();
                    let target = TensorPoint::Affine {
                        x: big(ctx.generator.x),
                        y: big(ctx.generator.y),
                    };
                    let mut meter = Meter::new(limits);
                    let net = tensor::reduction::decomposition_network(
                        &curve, &bases, &target, &mut meter,
                    )
                    .unwrap();
                    eprintln!(
                        "bits {bits} slots {slots}: edges {}, free input bits {:?}, max degree {}",
                        net.edge_count(),
                        net.input_bit_count(),
                        net.maximum_degree()
                    );
                }
            });
        }
    }
}
