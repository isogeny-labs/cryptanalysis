//! Large-genus index calculus (Enge–Gaudry) on any curve that can
//! enumerate and recognise its places of small degree.
//!
//! Factor base: every place of degree `≤ B` (hyperelliptic: `(π, ±v)`;
//! superelliptic: the residue-degree-one primes `(π, y − r)` and the
//! ramified primes). Relations: an `r`-adding walk whose steps are single
//! factor-base places (plus, in DLP mode, multiples of the base `D₁` and
//! target `D₂`); every reduced walk point is decomposed over the factor
//! base, and a smooth one yields `Σ (c_P − e_P) P = α D₁ + β D₂`.
//!
//! Two modes:
//!
//! - **order**: `α = β = 0`; the relation lattice `Λ ⊂ Z^{|FB|}` has index
//!   `h = [Z^{|FB|} : Λ] = #⟨FB⟩` once it is complete, computed here as the
//!   gcd of the determinants of a few random maximal minors (exact, by
//!   Chinese remaindering over 61-bit primes against the Hadamard bound).
//!   With the factor base generating the Jacobian, `h = #Jac(F_p)`; the
//!   result is checked against `h·R = 0` for random `R` and the Hasse–Weil
//!   interval, and reported as the order of the subgroup the factor base
//!   generates.
//! - **dlp**: the subgroup order `N` (prime) is known; the system
//!   `Σ r_{iP} y_P − β_i x ≡ α_i (mod N)` is solved by dense elimination
//!   modulo `N` (`N < 2^63`), and `x = log_{D₁} D₂` is **verified** by a
//!   scalar multiplication before it is returned. The relations hold in the
//!   whole group, hence in its projection to the cyclic `N`-part, so the
//!   factor base need not lie in `⟨D₁⟩` (it suffices that `N ∥ #Jac`).
//!
//! Costs: trials and group operations (from the group's counter), the
//! smoothness rate, and the linear-algebra wall time; no speed claim.

use std::collections::{HashMap, HashSet};
use std::time::Instant;

use num_bigint::{BigInt, BigUint};
use num_integer::Integer;
use num_traits::{One, Signed, ToPrimitive, Zero};
use rand::rngs::StdRng;
use rand::{RngCore, SeedableRng};
use rayon::prelude::*;

use super::cantor::{Divisor, HyperellipticCurve};
use super::fp::{is_prime_u64, Fp};
use super::kummer::{Ideal, SuperellipticCurve};
use super::poly::Poly;
use super::rho::{mod_inverse, random_below};
use super::{HgError, JacobianGroup};

/// Identifies a place: the monic irreducible `π` below it and the residue
/// `r` of `y` (reduced modulo `π`; `0` for a ramified place).
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct PlaceKey {
    pub pi: Poly,
    pub r: Poly,
}

/// A factor-base place.
#[derive(Clone, Debug)]
pub struct Place<E> {
    pub key: PlaceKey,
    pub degree: usize,
    pub elem: E,
}

/// What index calculus needs from a curve beyond the group law.
pub trait IndexCalculusCurve: JacobianGroup {
    fn field(&self) -> &Fp;
    fn genus(&self) -> u32;
    /// All places of degree `≤ bound`, as canonical group elements.
    fn enumerate_places(
        &self,
        bound: usize,
        rng: &mut impl RngCore,
    ) -> Result<Vec<Place<Self::Elem>>, HgError>;
    /// Decompose a canonical element over the places of degree `≤ bound`,
    /// or `None` when some prime in its support has degree `> bound` (or
    /// residue degree above one for the superelliptic model).
    fn decompose(
        &self,
        e: &Self::Elem,
        bound: usize,
        rng: &mut impl RngCore,
    ) -> Option<Vec<(PlaceKey, u32)>>;
}

/// Guard on the enumeration cost `Σ_d p^d` of the factor base.
const MAX_ENUMERATION: f64 = 1.0e8;

fn check_enumeration(p: u64, bound: usize) -> Result<(), HgError> {
    let mut total = 0f64;
    for d in 1..=bound {
        total += (p as f64).powi(d as i32);
    }
    if total > MAX_ENUMERATION {
        return Err(HgError::Unsupported(
            "factor-base enumeration p^B too large",
        ));
    }
    Ok(())
}

impl IndexCalculusCurve for HyperellipticCurve {
    fn field(&self) -> &Fp {
        &self.field
    }

    fn genus(&self) -> u32 {
        self.genus
    }

    fn enumerate_places(
        &self,
        bound: usize,
        rng: &mut impl RngCore,
    ) -> Result<Vec<Place<Divisor>>, HgError> {
        let k = &self.field;
        check_enumeration(k.p(), bound)?;
        let mut out = Vec::new();
        for d in 1..=bound {
            for pi in Poly::all_monic_irreducibles(d, k) {
                for place in self.places_above(&pi, rng) {
                    let key = PlaceKey {
                        pi: pi.clone(),
                        r: place.v.clone(),
                    };
                    let elem = self.reduce(place.u.clone(), place.v.clone());
                    out.push(Place {
                        key,
                        degree: d,
                        elem,
                    });
                }
            }
        }
        Ok(out)
    }

    fn decompose(
        &self,
        e: &Divisor,
        bound: usize,
        rng: &mut impl RngCore,
    ) -> Option<Vec<(PlaceKey, u32)>> {
        let k = &self.field;
        if e.is_identity() {
            return Some(Vec::new());
        }
        if !e.u.is_smooth(bound, k) {
            return None;
        }
        let mut out = Vec::new();
        for (pi, c) in e.u.factor(k, rng) {
            let r = e.v.rem(&pi, k);
            out.push((PlaceKey { pi, r }, c as u32));
        }
        Some(out)
    }
}

impl IndexCalculusCurve for SuperellipticCurve {
    fn field(&self) -> &Fp {
        &self.field
    }

    fn genus(&self) -> u32 {
        self.genus
    }

    fn enumerate_places(
        &self,
        bound: usize,
        rng: &mut impl RngCore,
    ) -> Result<Vec<Place<Ideal>>, HgError> {
        let k = &self.field;
        check_enumeration(k.p(), bound)?;
        let mut out = Vec::new();
        for d in 1..=bound {
            for pi in Poly::all_monic_irreducibles(d, k) {
                for (ideal, r) in self.places_above(&pi, rng) {
                    let key = PlaceKey { pi: pi.clone(), r };
                    let elem = self.canonical(&ideal);
                    out.push(Place {
                        key,
                        degree: d,
                        elem,
                    });
                }
            }
        }
        Ok(out)
    }

    fn decompose(
        &self,
        e: &Ideal,
        bound: usize,
        rng: &mut impl RngCore,
    ) -> Option<Vec<(PlaceKey, u32)>> {
        let k = &self.field;
        if e.is_unit() {
            return Some(Vec::new());
        }
        let n = e.norm(k);
        if !n.is_smooth(bound, k) {
            return None;
        }
        let mut out = Vec::new();
        for (pi, c) in n.factor(k, rng) {
            if self.big_f.rem(&pi, k).is_zero() {
                out.push((
                    PlaceKey {
                        pi,
                        r: Poly::zero(),
                    },
                    c as u32,
                ));
                continue;
            }
            let mut accounted = 0usize;
            for (_, r) in self.places_above(&pi, rng) {
                let a = self.valuation_unramified(e, &pi, &r, c);
                if a > 0 {
                    accounted += a;
                    out.push((PlaceKey { pi: pi.clone(), r }, a as u32));
                }
            }
            if accounted != c {
                return None; // a prime of residue degree > 1 is involved
            }
        }
        Some(out)
    }
}

/// The factor base with its index.
#[derive(Clone, Debug)]
pub struct FactorBase<E> {
    pub places: Vec<Place<E>>,
    pub index: HashMap<PlaceKey, usize>,
    pub bound: usize,
}

impl<E> FactorBase<E> {
    pub fn len(&self) -> usize {
        self.places.len()
    }

    pub fn is_empty(&self) -> bool {
        self.places.is_empty()
    }
}

/// Build the factor base of places of degree `≤ bound`.
pub fn build_factor_base<C: IndexCalculusCurve>(
    curve: &C,
    bound: usize,
    rng: &mut impl RngCore,
) -> Result<FactorBase<C::Elem>, HgError> {
    let places = curve.enumerate_places(bound, rng)?;
    let mut index = HashMap::with_capacity(places.len());
    for (i, pl) in places.iter().enumerate() {
        index.insert(pl.key.clone(), i);
    }
    Ok(FactorBase {
        places,
        index,
        bound,
    })
}

/// Parameters of the relation search.
#[derive(Clone, Debug)]
pub struct IcParams {
    /// Relations beyond the factor-base size.
    pub extra_relations: usize,
    /// Walk branches.
    pub branches: usize,
    /// Maximum walk trials (decompositions) before giving up.
    pub max_trials: u64,
    /// Re-randomise the walk after this many smooth hits (0 = never).
    pub restart_every: u64,
    pub seed: u64,
}

impl Default for IcParams {
    fn default() -> Self {
        Self {
            extra_relations: 16,
            branches: 32,
            max_trials: 50_000_000,
            restart_every: 8,
            seed: 1,
        }
    }
}

/// One relation `Σ coeffs[i]·P_i = alpha·D₁ + beta·D₂`.
#[derive(Clone, Debug)]
pub struct Relation {
    pub coeffs: Vec<(usize, i64)>,
    pub alpha: BigUint,
    pub beta: BigUint,
}

/// Statistics of a relation search.
#[derive(Clone, Debug, Default)]
pub struct SearchStats {
    pub trials: u64,
    pub smooth: u64,
    pub duplicates: u64,
    pub walk_ops: u64,
    pub setup_ops: u64,
    pub walks: u64,
}

impl SearchStats {
    pub fn smooth_rate(&self) -> f64 {
        if self.trials == 0 {
            0.0
        } else {
            self.smooth as f64 / self.trials as f64
        }
    }
}

struct Step<E> {
    places: Vec<(usize, i64)>,
    alpha: BigUint,
    beta: BigUint,
    elem: E,
}

/// Number of recent walk points remembered for cycle detection.
const CYCLE_WINDOW: usize = 64;

/// Collect `count` distinct relations. In order mode pass `dlp = None`;
/// in DLP mode pass `(D₁, D₂, N)` and the walk also moves by random
/// multiples of them.
pub fn collect_relations<C: IndexCalculusCurve>(
    curve: &C,
    fb: &FactorBase<C::Elem>,
    dlp: Option<(&C::Elem, &C::Elem, &BigUint)>,
    count: usize,
    params: &IcParams,
    rng: &mut impl RngCore,
) -> Result<(Vec<Relation>, SearchStats), HgError> {
    if fb.is_empty() {
        return Err(HgError::Unsupported("empty factor base"));
    }
    let mut stats = SearchStats::default();
    let ops0 = curve.group_ops();
    // Steps: small random combinations of places (2–3 distinct places, so no
    // step is the negative of another), with (α, β) in DLP mode.
    let mut steps: Vec<Step<C::Elem>> = Vec::with_capacity(params.branches);
    for _ in 0..params.branches.max(4) {
        let width = 2 + (rng.next_u64() % 2) as usize;
        let mut places: Vec<(usize, i64)> = Vec::with_capacity(width);
        let mut elem = curve.identity();
        while places.len() < width.min(fb.len()) {
            let idx = (rng.next_u64() as usize) % fb.len();
            if places.iter().any(|&(i, _)| i == idx) {
                continue;
            }
            places.push((idx, 1));
            elem = curve.add(&elem, &fb.places[idx].elem);
        }
        let (alpha, beta) = match dlp {
            Some((d1, d2, n)) => {
                let a = random_below(rng, n);
                let b = random_below(rng, n);
                elem = curve.add(
                    &elem,
                    &curve.add(&curve.scalar_mul(&a, d1), &curve.scalar_mul(&b, d2)),
                );
                (a, b)
            }
            None => (BigUint::zero(), BigUint::zero()),
        };
        steps.push(Step {
            places,
            alpha,
            beta,
            elem,
        });
    }
    stats.setup_ops = curve.group_ops() - ops0;
    let walk0 = curve.group_ops();
    let r = steps.len() as u64;
    let n_mod = dlp.map(|(_, _, n)| n.clone());

    let mut relations: Vec<Relation> = Vec::with_capacity(count);
    let mut seen: HashSet<Vec<(usize, i64)>> = HashSet::new();

    'walks: loop {
        stats.walks += 1;
        // Fresh start: a random combination of a few places (+ αD₁ + βD₂ in DLP mode).
        let mut expo: HashMap<usize, i64> = HashMap::new();
        let mut x = curve.identity();
        let g = curve.genus() as usize;
        for _ in 0..g.clamp(1, 8) {
            let idx = (rng.next_u64() as usize) % fb.len();
            *expo.entry(idx).or_insert(0) += 1;
            x = curve.add(&x, &fb.places[idx].elem);
        }
        let (mut alpha, mut beta) = match dlp {
            Some((d1, d2, n)) => {
                let a = random_below(rng, n);
                let b = random_below(rng, n);
                x = curve.add(
                    &x,
                    &curve.add(&curve.scalar_mul(&a, d1), &curve.scalar_mul(&b, d2)),
                );
                (a, b)
            }
            None => (BigUint::zero(), BigUint::zero()),
        };
        let mut hits_this_walk = 0u64;
        let mut recent: std::collections::VecDeque<u64> =
            std::collections::VecDeque::with_capacity(CYCLE_WINDOW);
        loop {
            if relations.len() >= count {
                break 'walks;
            }
            if stats.trials >= params.max_trials {
                return Err(HgError::Exhausted("relation search trials"));
            }
            let hx = curve.hash64(&x);
            if recent.contains(&hx) {
                continue 'walks; // cycle: restart from a fresh random point
            }
            if recent.len() == CYCLE_WINDOW {
                recent.pop_front();
            }
            recent.push_back(hx);
            stats.trials += 1;
            if stats.trials.is_multiple_of(100_000) && std::env::var_os("HG_VERBOSE").is_some() {
                eprintln!(
                    "[ic] trials {} smooth {} relations {}/{} walks {} ops {}",
                    stats.trials,
                    stats.smooth,
                    relations.len(),
                    count,
                    stats.walks,
                    curve.group_ops() - walk0
                );
            }
            if let Some(dec) = curve.decompose(&x, fb.bound, rng) {
                stats.smooth += 1;
                // Relation: Σ (c_P − e_P) P = α D₁ + β D₂.
                let mut coeffs: HashMap<usize, i64> = expo.iter().map(|(&i, &e)| (i, -e)).collect();
                let mut ok = true;
                for (key, c) in dec {
                    match fb.index.get(&key) {
                        Some(&i) => *coeffs.entry(i).or_insert(0) += c as i64,
                        None => {
                            ok = false; // place of allowed degree not in the base (should not happen)
                            break;
                        }
                    }
                }
                if ok {
                    let mut v: Vec<(usize, i64)> =
                        coeffs.into_iter().filter(|&(_, c)| c != 0).collect();
                    v.sort_unstable();
                    let trivial = v.is_empty() && alpha.is_zero() && beta.is_zero();
                    if !trivial && seen.insert(v.clone()) {
                        relations.push(Relation {
                            coeffs: v,
                            alpha: alpha.clone(),
                            beta: beta.clone(),
                        });
                    } else {
                        stats.duplicates += 1;
                    }
                }
                hits_this_walk += 1;
                if params.restart_every > 0 && hits_this_walk >= params.restart_every {
                    continue 'walks;
                }
            }
            // Step.
            let j = (hx % r) as usize;
            let st = &steps[j];
            for &(idx, e) in &st.places {
                *expo.entry(idx).or_insert(0) += e;
            }
            if let Some(n) = &n_mod {
                alpha = (&alpha + &st.alpha) % n;
                beta = (&beta + &st.beta) % n;
            }
            x = curve.add(&x, &st.elem);
        }
    }
    stats.walk_ops = curve.group_ops() - walk0;
    Ok((relations, stats))
}

// ── Order from the relation lattice ─────────────────────────────────────

/// Primes just below `2^61` for Chinese remaindering.
fn crt_primes(count: usize) -> Vec<u64> {
    let mut out = Vec::with_capacity(count);
    let mut c = (1u64 << 61) - 1;
    while out.len() < count {
        if is_prime_u64(c) {
            out.push(c);
        }
        c -= 2;
    }
    out
}

fn mulmod64(a: u64, b: u64, m: u64) -> u64 {
    ((a as u128 * b as u128) % m as u128) as u64
}

fn powmod64(mut a: u64, mut e: u64, m: u64) -> u64 {
    let mut r = 1u64;
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

fn inv64(a: u64, m: u64) -> u64 {
    powmod64(a, m - 2, m)
}

/// Determinant of a square integer matrix modulo a prime `m`.
fn det_mod(rows: &[Vec<i64>], m: u64) -> u64 {
    let n = rows.len();
    let mut a: Vec<Vec<u64>> = rows
        .iter()
        .map(|r| {
            r.iter()
                .map(|&x| ((x % m as i64 + m as i64) % m as i64) as u64)
                .collect()
        })
        .collect();
    let mut det = 1u64;
    for c in 0..n {
        let Some(piv) = (c..n).find(|&r| a[r][c] != 0) else {
            return 0;
        };
        if piv != c {
            a.swap(piv, c);
            det = m - det;
            if det == m {
                det = 0;
            }
        }
        det = mulmod64(det, a[c][c], m);
        let inv = inv64(a[c][c], m);
        let pivot_row = a[c].clone();
        for r in c + 1..n {
            if a[r][c] == 0 {
                continue;
            }
            let f = mulmod64(a[r][c], inv, m);
            let row = &mut a[r];
            for k in c..n {
                let sub = mulmod64(f, pivot_row[k], m);
                row[k] = if row[k] >= sub {
                    row[k] - sub
                } else {
                    row[k] + m - sub
                };
            }
        }
    }
    det
}

/// Exact determinant of a square integer matrix (Hadamard bound + CRT).
pub fn det_exact(rows: &[Vec<i64>]) -> BigInt {
    let n = rows.len();
    if n == 0 {
        return BigInt::one();
    }
    let mut bits = 1.0f64;
    for r in rows {
        let norm2: f64 = r.iter().map(|&x| (x as f64) * (x as f64)).sum();
        bits += 0.5 * norm2.max(1.0).log2();
    }
    let count = ((bits + 2.0) / 60.0).ceil() as usize + 1;
    let primes = crt_primes(count);
    let residues: Vec<u64> = primes.par_iter().map(|&m| det_mod(rows, m)).collect();
    // Garner / incremental CRT in BigInt, symmetric range.
    let mut x = BigInt::zero();
    let mut modulus = BigInt::one();
    for (&m, &r) in primes.iter().zip(residues.iter()) {
        let mb = BigInt::from(m);
        // Find t with x + modulus·t ≡ r (mod m).
        let cur = ((&x % &mb) + &mb) % &mb;
        let diff = ((BigInt::from(r) - cur) % &mb + &mb) % &mb;
        let modinv = {
            let mm = (&modulus % &mb).to_u64().unwrap_or(0);
            inv64(mm, m)
        };
        let t = (diff * BigInt::from(modinv)) % &mb;
        x += &modulus * t;
        modulus *= &mb;
    }
    let half = &modulus >> 1u32;
    if x > half {
        x -= &modulus;
    }
    x
}

/// The index of the lattice spanned by the relation rows in `Z^{fb_size}`:
/// gcd of the determinants of `minors` random maximal minors.
pub fn lattice_index(
    relations: &[Relation],
    fb_size: usize,
    minors: usize,
    seed: u64,
) -> Result<BigUint, HgError> {
    if relations.len() < fb_size {
        return Err(HgError::Unsupported(
            "fewer relations than factor-base elements",
        ));
    }
    let dense: Vec<Vec<i64>> = relations
        .iter()
        .map(|r| {
            let mut row = vec![0i64; fb_size];
            for &(i, c) in &r.coeffs {
                row[i] = c;
            }
            row
        })
        .collect();
    let mut rng = StdRng::seed_from_u64(seed);
    let mut acc = BigInt::zero();
    let mut tried = 0;
    let mut used = 0;
    while used < minors && tried < 4 * minors + 8 {
        tried += 1;
        // Random subset of fb_size rows.
        let mut idx: Vec<usize> = (0..dense.len()).collect();
        for i in (1..idx.len()).rev() {
            let j = (rng.next_u64() as usize) % (i + 1);
            idx.swap(i, j);
        }
        let sub: Vec<Vec<i64>> = idx[..fb_size].iter().map(|&i| dense[i].clone()).collect();
        let d = det_exact(&sub);
        if d.is_zero() {
            continue;
        }
        used += 1;
        acc = acc.gcd(&d);
    }
    if used == 0 {
        return Err(HgError::Exhausted(
            "every sampled minor was singular (relations do not span)",
        ));
    }
    acc.abs().to_biguint().ok_or(HgError::Exhausted("gcd"))
}

/// Order report.
#[derive(Clone, Debug)]
pub struct OrderReport {
    pub order: BigUint,
    pub fb_size: usize,
    pub stats: SearchStats,
    pub relations: usize,
    pub la_ms: u128,
    /// `h·R = 0` held for every random `R` tried.
    pub annihilates_random: bool,
    pub within_hasse_weil: bool,
}

/// Compute the order of the subgroup generated by the factor base.
pub fn index_calculus_group_order<C: IndexCalculusCurve>(
    curve: &C,
    fb: &FactorBase<C::Elem>,
    params: &IcParams,
) -> Result<OrderReport, HgError> {
    let mut rng = StdRng::seed_from_u64(params.seed);
    let count = fb.len() + params.extra_relations;
    let (relations, stats) = collect_relations(curve, fb, None, count, params, &mut rng)?;
    let t0 = Instant::now();
    let order = lattice_index(&relations, fb.len(), 3, params.seed ^ 0xabcd)?;
    let la_ms = t0.elapsed().as_millis();
    let mut annihilates = true;
    for _ in 0..3 {
        let idx = (rng.next_u64() as usize) % fb.len();
        let r = &fb.places[idx].elem;
        if !curve.is_identity(&curve.scalar_mul(&order, r)) {
            annihilates = false;
        }
    }
    let within = hasse_weil_contains(curve.field().p(), curve.genus(), &order);
    Ok(OrderReport {
        order,
        fb_size: fb.len(),
        stats,
        relations: relations.len(),
        la_ms,
        annihilates_random: annihilates,
        within_hasse_weil: within,
    })
}

/// `(√p − 1)^{2g} ≤ h ≤ (√p + 1)^{2g}` in floating point.
pub fn hasse_weil_contains(p: u64, genus: u32, h: &BigUint) -> bool {
    let lh = h.bits() as f64; // coarse: log2 within 1 bit
    let s = (p as f64).sqrt();
    let lo = 2.0 * genus as f64 * (s - 1.0).max(1e-9).log2();
    let hi = 2.0 * genus as f64 * (s + 1.0).log2();
    lh + 1.0 >= lo && lh - 1.0 <= hi
}

// ── DLP mod N ───────────────────────────────────────────────────────────

/// DLP report.
#[derive(Clone, Debug)]
pub struct DlpReport {
    pub k: BigUint,
    pub fb_size: usize,
    pub stats: SearchStats,
    pub relations: usize,
    pub la_ms: u128,
    /// Dense system dimension after dropping unused columns.
    pub la_dim: usize,
}

/// Solve `D₂ = k·D₁` in the subgroup of prime order `n < 2^63`.
pub fn index_calculus_dlp<C: IndexCalculusCurve>(
    curve: &C,
    fb: &FactorBase<C::Elem>,
    d1: &C::Elem,
    d2: &C::Elem,
    n: &BigUint,
    params: &IcParams,
) -> Result<DlpReport, HgError> {
    let n64 = n
        .to_u64()
        .filter(|&v| v < (1u64 << 63) && v > 1)
        .ok_or(HgError::Unsupported("N must be a prime below 2^63"))?;
    let mut rng = StdRng::seed_from_u64(params.seed);
    let mut count = fb.len() + params.extra_relations;
    let mut all: Vec<Relation> = Vec::new();
    let mut stats_total = SearchStats::default();
    for _round in 0..4 {
        let (rels, stats) = collect_relations(
            curve,
            fb,
            Some((d1, d2, n)),
            count - all.len(),
            params,
            &mut rng,
        )?;
        stats_total.trials += stats.trials;
        stats_total.smooth += stats.smooth;
        stats_total.duplicates += stats.duplicates;
        stats_total.walk_ops += stats.walk_ops;
        stats_total.setup_ops += stats.setup_ops;
        stats_total.walks += stats.walks;
        all.extend(rels);
        let t0 = Instant::now();
        if std::env::var_os("HG_VERBOSE").is_some() {
            eprintln!("[ic] solving with {} relations over {} places", all.len(), fb.len());
        }
        let (sol, dim) = solve_log_mod_n(&all, fb.len(), n64);
        let la_ms = t0.elapsed().as_millis();
        if std::env::var_os("HG_VERBOSE").is_some() {
            eprintln!("[ic] solve {la_ms} ms dim {dim} -> {sol:?}");
        }
        if let Some(x) = sol {
            let k = BigUint::from(x);
            if curve.scalar_mul(&k, d1) == *d2 {
                return Ok(DlpReport {
                    k,
                    fb_size: fb.len(),
                    stats: stats_total,
                    relations: all.len(),
                    la_ms,
                    la_dim: dim,
                });
            }
            // A wrong solution means the N-part assumption failed; gather more relations and retry.
        }
        count += fb.len() / 4 + 16;
    }
    Err(HgError::Exhausted(
        "index calculus: no verified logarithm from the collected relations",
    ))
}

/// Solve for `x = log D₂` from relations `Σ r_P y_P − β x ≡ α (mod n)`.
/// Returns `(x, dimension of the dense system)`.
pub fn solve_log_mod_n(relations: &[Relation], fb_size: usize, n: u64) -> (Option<u64>, usize) {
    // Columns: used factor-base places (compressed), then x.
    let mut used = vec![false; fb_size];
    for r in relations {
        for &(i, _) in &r.coeffs {
            used[i] = true;
        }
    }
    let mut col_of = vec![usize::MAX; fb_size];
    let mut ncols = 0;
    for i in 0..fb_size {
        if used[i] {
            col_of[i] = ncols;
            ncols += 1;
        }
    }
    let xcol = ncols;
    let width = ncols + 2; // + x + rhs
    let red = |v: i64| -> u64 { (((v % n as i64) + n as i64) % n as i64) as u64 };
    let mut mat: Vec<Vec<u64>> = relations
        .iter()
        .map(|r| {
            let mut row = vec![0u64; width];
            for &(i, c) in &r.coeffs {
                row[col_of[i]] = red(c);
            }
            let beta = (&r.beta % n).to_u64().unwrap_or(0);
            row[xcol] = if beta == 0 { 0 } else { n - beta };
            row[xcol + 1] = (&r.alpha % n).to_u64().unwrap_or(0);
            row
        })
        .collect();
    let rows = mat.len();
    let mut pivot_row = 0usize;
    for c in 0..=xcol {
        if pivot_row >= rows {
            break;
        }
        let Some(piv) = (pivot_row..rows).find(|&r| mat[r][c] != 0) else {
            continue;
        };
        mat.swap(piv, pivot_row);
        let inv = inv64(mat[pivot_row][c], n);
        for k in c..width {
            mat[pivot_row][k] = mulmod64(mat[pivot_row][k], inv, n);
        }
        let prow = mat[pivot_row].clone();
        let (above, rest) = mat.split_at_mut(pivot_row);
        let below = &mut rest[1..];
        let eliminate = |row: &mut Vec<u64>| {
            if row[c] == 0 {
                return;
            }
            let f = row[c];
            for k in c..width {
                if prow[k] == 0 {
                    continue;
                }
                let sub = mulmod64(f, prow[k], n);
                row[k] = if row[k] >= sub {
                    row[k] - sub
                } else {
                    row[k] + n - sub
                };
            }
        };
        if c == xcol {
            above.par_iter_mut().for_each(eliminate);
        }
        below.par_iter_mut().for_each(eliminate);
        pivot_row += 1;
    }
    // Find a row with a pivot at x and zeros elsewhere.
    for row in &mat {
        if row[xcol] == 1 && row[..xcol].iter().all(|&v| v == 0) {
            return (Some(row[xcol + 1]), ncols + 1);
        }
    }
    (None, ncols + 1)
}

/// Largest prime factor of `h` found by trial division and Brent rho,
/// with the cofactor; `None` if a composite cofactor above the rho budget
/// remains unfactored.
pub fn largest_prime_factor(h: &BigUint, rho_budget: u64) -> Option<(BigUint, BigUint)> {
    let one = BigUint::one();
    let mut rest = h.clone();
    let mut primes: Vec<BigUint> = Vec::new();
    // Trial division to 2^16.
    let mut d = 2u64;
    while d < 65_536 && rest > one {
        let db = BigUint::from(d);
        if (&rest % &db).is_zero() {
            primes.push(db.clone());
            while (&rest % &db).is_zero() {
                rest /= &db;
            }
        }
        d += if d == 2 { 1 } else { 2 };
    }
    let mut stack = vec![rest];
    while let Some(c) = stack.pop() {
        if c <= one {
            continue;
        }
        if super::jacobi::is_probable_prime_big(&c) {
            primes.push(c);
            continue;
        }
        let f = brent_rho(&c, rho_budget)?;
        let g = &c / &f;
        stack.push(f);
        stack.push(g);
    }
    let n = primes.into_iter().max()?;
    let cof = h / &n;
    Some((n, cof))
}

fn brent_rho(n: &BigUint, budget: u64) -> Option<BigUint> {
    let two = BigUint::from(2u32);
    if (n % &two).is_zero() {
        return Some(two);
    }
    let mut rng = StdRng::seed_from_u64(n.bits());
    for _ in 0..8 {
        let c = random_below(&mut rng, n);
        let mut x = random_below(&mut rng, n);
        let mut y = x.clone();
        let mut d = BigUint::one();
        let mut steps = 0u64;
        let f = |v: &BigUint| (v * v + &c) % n;
        while d.is_one() && steps < budget {
            x = f(&x);
            y = f(&f(&y));
            let diff = if x > y { &x - &y } else { &y - &x };
            d = diff.gcd(n);
            steps += 1;
        }
        if !d.is_one() && d != *n {
            return Some(d);
        }
    }
    None
}

/// Shared helper: `a⁻¹ mod n` as `BigUint`.
pub fn inverse_mod(a: &BigUint, n: &BigUint) -> Option<BigUint> {
    mod_inverse(a, n)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::highgenus::cantor::HyperellipticCurve;

    #[test]
    fn det_exact_matches_small_cases() {
        let m = vec![vec![2i64, 1], vec![7, 4]];
        assert_eq!(det_exact(&m), BigInt::from(1));
        let m = vec![vec![0i64, 1, 0], vec![1, 0, 0], vec![0, 0, 5]];
        assert_eq!(det_exact(&m), BigInt::from(-5));
        // A 12×12 matrix with a known determinant: diagonal 3 with ones above.
        let n = 12;
        let mut m = vec![vec![0i64; n]; n];
        for i in 0..n {
            m[i][i] = 3;
            if i + 1 < n {
                m[i][i + 1] = 1;
            }
        }
        assert_eq!(det_exact(&m), BigInt::from(3i64.pow(12)));
    }

    fn rank_mod(rows: &[Vec<i64>], m: u64) -> usize {
        let mut a: Vec<Vec<u64>> = rows
            .iter()
            .map(|r| {
                r.iter()
                    .map(|&x| ((x % m as i64 + m as i64) % m as i64) as u64)
                    .collect()
            })
            .collect();
        let n = a.first().map(|r| r.len()).unwrap_or(0);
        let mut rank = 0;
        for c in 0..n {
            let Some(piv) = (rank..a.len()).find(|&r| a[r][c] != 0) else {
                continue;
            };
            a.swap(piv, rank);
            let inv = inv64(a[rank][c], m);
            let prow: Vec<u64> = a[rank].iter().map(|&v| mulmod64(v, inv, m)).collect();
            for r in 0..a.len() {
                if r != rank && a[r][c] != 0 {
                    let f = a[r][c];
                    for k in 0..n {
                        let sub = mulmod64(f, prow[k], m);
                        a[r][k] = if a[r][k] >= sub {
                            a[r][k] - sub
                        } else {
                            a[r][k] + m - sub
                        };
                    }
                }
            }
            rank += 1;
        }
        rank
    }

    #[test]
    fn relation_lattice_has_full_rank() {
        let k = Fp::new(23).unwrap();
        let c = HyperellipticCurve::new(k, Poly::from_coeffs(vec![1, 1, 2, 3, 0, 1], &k)).unwrap();
        let mut rng = StdRng::seed_from_u64(11);
        let fb = build_factor_base(&c, 1, &mut rng).unwrap();
        let params = IcParams {
            extra_relations: 12,
            seed: 3,
            ..Default::default()
        };
        let (rels, stats) =
            collect_relations(&c, &fb, None, fb.len() + 12, &params, &mut rng).unwrap();
        assert!(stats.smooth >= rels.len() as u64);
        let dense: Vec<Vec<i64>> = rels
            .iter()
            .map(|r| {
                let mut row = vec![0i64; fb.len()];
                for &(i, v) in &r.coeffs {
                    row[i] = v;
                }
                row
            })
            .collect();
        assert_eq!(
            rank_mod(&dense, (1u64 << 61) - 1),
            fb.len(),
            "relations span the lattice"
        );
        // Check each relation actually holds in the group.
        for r in rels.iter().take(20) {
            let mut acc = c.identity();
            for &(i, v) in &r.coeffs {
                let e = if v >= 0 {
                    c.scalar_mul(&BigUint::from(v as u64), &fb.places[i].elem)
                } else {
                    c.neg(&c.scalar_mul(&BigUint::from((-v) as u64), &fb.places[i].elem))
                };
                acc = c.add(&acc, &e);
            }
            assert!(
                c.is_identity(&acc),
                "relation does not hold: {:?}",
                r.coeffs
            );
        }
    }

    #[test]
    fn order_and_dlp_on_a_genus_two_toy() {
        // y² = x⁵ + 3x³ + 2x² + x + 1 over F_23.
        let k = Fp::new(23).unwrap();
        let c = HyperellipticCurve::new(k, Poly::from_coeffs(vec![1, 1, 2, 3, 0, 1], &k)).unwrap();
        let mut rng = StdRng::seed_from_u64(11);
        let fb = build_factor_base(&c, 1, &mut rng).unwrap();
        assert!(fb.len() > 5);
        let params = IcParams {
            extra_relations: 12,
            seed: 3,
            ..Default::default()
        };
        let rep = index_calculus_group_order(&c, &fb, &params).unwrap();
        assert!(rep.annihilates_random, "{rep:?}");
        assert!(rep.within_hasse_weil, "{rep:?}");
        // Cross-check against the BigUint reference's brute-force order.
        let big_f = crate::prime_hyperelliptic::FpPoly::from_coeffs(
            c.f.c.iter().map(|&x| BigUint::from(x)).collect(),
            BigUint::from(23u32),
        );
        let cb = crate::prime_hyperelliptic::HyperellipticCurveP::try_new(
            BigUint::from(23u32),
            big_f,
            2,
        )
        .unwrap();
        let brute = crate::prime_hyperelliptic::brute_force_jac_order(&cb);
        assert_eq!(rep.order, brute);
        // DLP in the largest prime-order subgroup.
        let (n, cof) = largest_prime_factor(&rep.order, 1_000_000).unwrap();
        let mut d1 = c.identity();
        while c.is_identity(&d1) {
            d1 = c.scalar_mul(&cof, &c.random_element(2, &mut rng));
        }
        let kk = BigUint::from(1234567u32) % &n;
        let d2 = c.scalar_mul(&kk, &d1);
        let rep = index_calculus_dlp(&c, &fb, &d1, &d2, &n, &params).unwrap();
        assert_eq!(rep.k, kk);
    }
}
