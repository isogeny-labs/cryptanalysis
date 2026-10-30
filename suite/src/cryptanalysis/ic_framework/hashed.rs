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
//! reported as an uncalibrated native step count: `see the notes on
//! S-accounting in `docs/ic/FRAMEWORK.md`. Never read an S for this arm as a
//! priced end-to-end cost until the contraction steps have a calibration.

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

/// The smallest prime in `[2p, 4p]`, checked with the crate's primality test.
fn hash_prime(p: &BigUint, meter: &mut Meter) -> Result<BigUint, String> {
    let lower = p << 1;
    let upper = p << 2;
    let mut candidate = lower;
    while candidate <= upper {
        if tensor::arithmetic::is_prime(&candidate, meter)
            .map_err(|e| format!("hash prime: {e}"))?
        {
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
    let mut meter = Meter::new(limits_from(params)?);
    let p = big(ctx.group.p);
    let r = big(ctx.r);
    let prime = match params.get("s") {
        Some(raw) => {
            let value: BigUint = raw
                .parse()
                .map_err(|_| format!("s is not an integer: `{raw}`"))?;
            if value < (&p << 1) || value > (&p << 2) || !value.to_u64().is_some() {
                return Err("s must be an integer in [2p, 4p]".into());
            }
            if !tensor::arithmetic::is_prime(&value, &mut meter)
                .map_err(|e| format!("hash prime: {e}"))?
            {
                return Err("s must be prime".into());
            }
            value
        }
        None => hash_prime(&p, &mut meter)?,
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

/// Enumerate every slot base, in slot order. This is the same deterministic
/// ordering the oracle reconstructs, so the union base and the oracle agree.
fn enumerate_slots(
    curve: &TensorCurve,
    spec: &SlotSpec,
    limits: &Limits,
) -> Result<(Vec<Vec<PrimePoint>>, u64, u64, u64), String> {
    let mut meter = Meter::new(limits.clone());
    let bases = tensor_bases(curve, spec, &mut meter)?;
    let mut rng = SeedRng::new(0x5eed_0000 ^ spec.slots as u64);
    let mut out = Vec::with_capacity(bases.len());
    for base in &bases {
        let points = base
            .enumerate(curve, &mut rng, &mut meter)
            .map_err(|e| format!("hashed-tensor enumeration: {e}"))?;
        out.push(
            points
                .iter()
                .map(prime_point)
                .collect::<Result<Vec<_>, _>>()?,
        );
    }
    Ok((out, meter.used, meter.curve_additions, meter.square_roots))
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
        ]
    }

    fn build(
        &self,
        ctx: &InstanceCtx<PrimeCurve>,
        params: &Params,
        ops: &mut GroupOps,
    ) -> Result<FactorBase<PrimePoint>, String> {
        let limits = limits_from(params)?;
        let spec = slot_spec(ctx, params)?;
        let curve = tensor_curve(ctx, &limits)?;
        let (slots, steps, additions, square_roots) = enumerate_slots(&curve, &spec, &limits)?;
        ops.adds = ops.adds.saturating_add(additions);
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
        fb.cost.count("hashed_tensor_steps", steps);
        fb.cost.count("sqrt_solves", square_roots);
        fb.cost.wall_ns = starting_wall.elapsed().as_nanos() as u64;
        Ok(fb)
    }
}

/// The exact Boolean tensor-contraction oracle over the same slot bases.
pub struct HashedTensorOracle {
    curve: Option<TensorCurve>,
    bases: Vec<TensorBase>,
    limits: Option<Limits>,
    slots: Vec<Vec<PrimePoint>>,
    slot_index: Vec<std::collections::HashMap<u64, usize>>,
    setup_steps: u64,
    setup_square_roots: u64,
    relation_steps: u64,
    limit_hits: u64,
    integrity_failures: u64,
}

impl Default for HashedTensorOracle {
    fn default() -> Self {
        Self {
            curve: None,
            bases: Vec::new(),
            limits: None,
            slots: Vec::new(),
            slot_index: Vec::new(),
            setup_steps: 0,
            setup_square_roots: 0,
            relation_steps: 0,
            limit_hits: 0,
            integrity_failures: 0,
        }
    }
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
        ]
    }

    fn prepare(
        &mut self,
        ctx: &InstanceCtx<PrimeCurve>,
        fb: &FactorBase<PrimePoint>,
        params: &Params,
        ops: &mut GroupOps,
    ) -> Result<(), String> {
        let limits = limits_from(params)?;
        let spec = slot_spec(ctx, params)?;
        let curve = tensor_curve(ctx, &limits)?;
        let bases = tensor_bases(&curve, &spec, &mut Meter::new(limits.clone()))?;
        let (slots, steps, additions, square_roots) = enumerate_slots(&curve, &spec, &limits)?;
        ops.adds = ops.adds.saturating_add(additions);
        let all: Vec<PrimePoint> = slots.iter().flatten().copied().collect();
        if all != fb.points {
            return Err(
                "hashed-tensor requires `hashed-affine` with identical slots, seed, tau and s"
                    .into(),
            );
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
        self.bases = bases;
        self.curve = Some(curve);
        self.limits = Some(limits);
        self.setup_steps = steps;
        self.setup_square_roots = square_roots;
        Ok(())
    }

    fn setup_native(&self) -> BTreeMap<String, u64> {
        let mut out = BTreeMap::new();
        if self.setup_steps > 0 {
            out.insert("hashed_tensor_steps".to_string(), self.setup_steps);
        }
        if self.setup_square_roots > 0 {
            out.insert("sqrt_solves".to_string(), self.setup_square_roots);
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
        ops.adds = ops.adds.saturating_add(meter.curve_additions);
        counters.sqrt_solves = counters.sqrt_solves.saturating_add(meter.square_roots);
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

    fn relation_counters(&self) -> BTreeMap<String, u64> {
        let mut out = BTreeMap::new();
        out.insert("hashed_tensor_steps".to_string(), self.relation_steps);
        out.insert("hashed_limit_hits".to_string(), self.limit_hits);
        out.insert(
            "hashed_integrity_failures".to_string(),
            self.integrity_failures,
        );
        out
    }
}
