//! Executable reference for §3 of Bochum's *Subexponential ECDL*, v0.2.
//!
//! This implements affine-hashed factor bases and the index-calculus reduction,
//! **not** the compact Boolean tensor encoding or the assumed fast contraction
//! algorithm. The default oracle enumerates group decompositions (generic
//! decomposition, bounded by sqrt(r); cannot beat rho). No subexponential or
//! performance claim is made. Only small, cofactor-one prime-field curves are
//! supported. All returned answers carry a replayable algebraic certificate.
//!
//! Source: <https://github.com/bochum-crypto/subexponential-ecdl>, commit
//! `1ee44e562b1b9a50ea339f3b8f81112b5a24b96f`, §3.2–3.5, Figure 2.
//! Kept byte-identical in crypto and cryptanalysis's Rust binding.

use std::collections::BTreeMap;

/// Affine coordinates; `None` denotes the identity.
pub type Point = Option<(u64, u64)>;

/// A rejected input, exhausted bound, or invalid oracle/certificate.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    /// Invalid parameters or noncanonical coordinates.
    Invalid(&'static str),
    /// Work stopped; this is not a proof of nonexistence.
    Limit(&'static str),
    /// A proposed decomposition or certificate failed independent replay.
    Verification,
}

impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}
impl std::error::Error for Error {}

fn prime(n: u64) -> bool {
    n >= 2 && (2..).take_while(|d| d * d <= n).all(|d| n % d != 0)
}
fn pow(mut a: u64, mut n: u64, p: u64) -> u64 {
    let mut r = 1;
    while n != 0 {
        if n & 1 != 0 {
            r = r * a % p;
        }
        a = a * a % p;
        n >>= 1;
    }
    r
}
fn sub(a: u64, b: u64, p: u64) -> u64 {
    (a + p - b) % p
}

/// Validated short-Weierstrass curve of odd prime cardinality, cofactor one.
/// Construction counts points exactly; the deliberate field bound is 65521.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Curve {
    p: u64,
    a: u64,
    b: u64,
    r: u64,
    // Canonical square-root lookup, constructed in O(p), for tiny fixtures.
    // Replacing this with Tonelli–Shanks is needed before lifting the bound.
    roots: Vec<Option<u64>>,
}

impl Curve {
    /// Check primality, nonsingularity, and the exact prime group order.
    pub fn new(p: u64, a: u64, b: u64, r: u64) -> Result<Self, Error> {
        if !(5..=65521).contains(&p) || !(3..=131044).contains(&r) || !prime(p) || !prime(r) {
            return Err(Error::Invalid(
                "small prime field and odd prime order required",
            ));
        }
        if a >= p || b >= p || (4 * a * a % p * a + 27 * b * b) % p == 0 {
            return Err(Error::Invalid("noncanonical or singular curve"));
        }
        let mut roots = vec![None; p as usize];
        for y in 0..p {
            roots[(y * y % p) as usize].get_or_insert(y);
        }
        let curve = Self { p, a, b, r, roots };
        let count = 1
            + (0..p)
                .map(|x| match curve.roots[curve.rhs(x) as usize] {
                    None => 0,
                    Some(0) => 1,
                    Some(_) => 2,
                })
                .sum::<u64>();
        if count != r {
            return Err(Error::Invalid(
                "declared order is not the full curve cardinality",
            ));
        }
        Ok(curve)
    }

    /// Prime field modulus.
    pub fn modulus(&self) -> u64 {
        self.p
    }
    /// Verified full group cardinality.
    pub fn order(&self) -> u64 {
        self.r
    }
    fn rhs(&self, x: u64) -> u64 {
        (x * x % self.p * x + self.a * x + self.b) % self.p
    }

    /// Test canonical coordinates and the curve equation; accepts the identity.
    pub fn contains(&self, point: Point) -> bool {
        match point {
            None => true,
            Some((x, y)) => x < self.p && y < self.p && y * y % self.p == self.rhs(x),
        }
    }

    /// Injective nonidentity encoding `2*x + (y mod 2)` from §3.2.
    pub fn encode(&self, point: Point) -> Result<u64, Error> {
        if !self.contains(point) {
            return Err(Error::Invalid("point"));
        }
        point
            .map(|(x, y)| 2 * x + (y & 1))
            .ok_or(Error::Invalid("identity has no factor-base encoding"))
    }

    /// Invert the compressed encoding, rejecting absent roots and wrong parity.
    pub fn decode(&self, z: u64) -> Point {
        if z >= 2 * self.p {
            return None;
        }
        let x = z / 2;
        let mut y = self.roots[self.rhs(x) as usize]?;
        if y & 1 != z & 1 {
            y = (self.p - y) % self.p;
        }
        (y & 1 == z & 1).then_some((x, y))
    }

    fn neg(&self, a: Point) -> Point {
        a.map(|(x, y)| (x, (self.p - y) % self.p))
    }
    fn add_valid(&self, a: Point, b: Point) -> Point {
        let (x, y) = match a {
            None => return b,
            Some(p) => p,
        };
        let (xx, yy) = match b {
            None => return a,
            Some(p) => p,
        };
        let p = self.p;
        if x == xx && (y + yy) % p == 0 {
            return None;
        }
        let (num, den) = if x == xx {
            ((3 * x * x + self.a) % p, 2 * y % p)
        } else {
            (sub(yy, y, p), sub(xx, x, p))
        };
        let slope = num * pow(den, p - 2, p) % p;
        let nx = sub(sub(slope * slope % p, x, p), xx, p);
        Some((nx, sub(slope * sub(x, nx, p) % p, y, p)))
    }

    /// Checked affine addition, including identity, inverses, and doubling.
    pub fn add(&self, a: Point, b: Point) -> Result<Point, Error> {
        if !self.contains(a) || !self.contains(b) {
            return Err(Error::Invalid("point"));
        }
        Ok(self.add_valid(a, b))
    }

    /// Checked scalar multiplication (variable time, public research inputs).
    pub fn mul(&self, mut a: Point, mut n: u64) -> Result<Point, Error> {
        if !self.contains(a) {
            return Err(Error::Invalid("point"));
        }
        let mut out = None;
        while n != 0 {
            if n & 1 != 0 {
                out = self.add_valid(out, a);
            }
            a = self.add_valid(a, a);
            n >>= 1;
        }
        Ok(out)
    }
}

/// One affine hash and its threshold, defining a slot-specific factor base.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct HashBase {
    /// Prime hash modulus, in `[2p,4p]`.
    pub s: u64,
    /// Nonzero multiplier modulo `s`.
    pub alpha: u64,
    /// Additive offset modulo `s`.
    pub beta: u64,
    /// Membership is `(alpha*enc(A)+beta) mod s < tau`.
    pub tau: u64,
}

impl HashBase {
    fn validate(&self, curve: &Curve) -> Result<(), Error> {
        if self.s < 2 * curve.p
            || self.s > 4 * curve.p
            || !prime(self.s)
            || self.alpha == 0
            || self.alpha >= self.s
            || self.beta >= self.s
            || self.tau == 0
            || self.tau > self.s
        {
            return Err(Error::Invalid("hash parameters"));
        }
        Ok(())
    }

    /// Enumerate by inverse hashing, not by scanning all curve points (§3.5).
    pub fn enumerate(&self, curve: &Curve) -> Result<Vec<Point>, Error> {
        self.validate(curve)?;
        let inv = pow(self.alpha, self.s - 2, self.s);
        let mut points = Vec::new();
        for t in 0..self.tau {
            let z = inv * sub(t, self.beta, self.s) % self.s;
            if let Some(point) = curve.decode(z) {
                points.push(Some(point));
            }
        }
        points.sort_unstable();
        Ok(points)
    }
}

/// Deterministic decomposition interface. The oracle receives no `u`, `v`,
/// generator, or target logarithm. `None` must certify exhaustive nonexistence;
/// a resource limit must return `Error::Limit` instead.
pub trait DecompositionOracle {
    /// Find an ordered slot-specific decomposition of `target`.
    fn find(
        &mut self,
        curve: &Curve,
        bases: &[Vec<Point>],
        target: Point,
        max_work: u64,
    ) -> Result<Option<Vec<Point>>, Error>;
}

/// Generic reference oracle: enumerate the first `m-1` slots and look up the
/// final residual. This is not Boolean tensor contraction.
#[derive(Default)]
pub struct Enumerate;

impl DecompositionOracle for Enumerate {
    fn find(
        &mut self,
        curve: &Curve,
        bases: &[Vec<Point>],
        target: Point,
        max_work: u64,
    ) -> Result<Option<Vec<Point>>, Error> {
        if bases.len() < 2
            || bases.len() > 8
            || !curve.contains(target)
            || bases.iter().any(|b| {
                b.iter().any(|&a| a.is_none() || !curve.contains(a))
                    || b.windows(2).any(|w| w[0] >= w[1])
            })
        {
            return Err(Error::Invalid("oracle input"));
        }
        if bases.iter().any(Vec::is_empty) {
            return Ok(None);
        }
        let mut indices = vec![0; bases.len() - 1];
        for _ in 0..max_work {
            let mut tuple: Vec<_> = indices
                .iter()
                .enumerate()
                .map(|(i, &j)| bases[i][j])
                .collect();
            let sum = tuple.iter().fold(None, |acc, &a| curve.add_valid(acc, a));
            let last = curve.add_valid(target, curve.neg(sum));
            if bases.last().unwrap().binary_search(&last).is_ok() {
                tuple.push(last);
                return Ok(Some(tuple));
            }
            let mut slot = indices.len();
            loop {
                if slot == 0 {
                    return Ok(None);
                }
                slot -= 1;
                indices[slot] += 1;
                if indices[slot] < bases[slot].len() {
                    break;
                }
                indices[slot] = 0;
            }
        }
        Err(Error::Limit(
            "decomposition work; nonexistence not established",
        ))
    }
}

/// Bounded reduction parameters. Bounds make exhaustion explicit.
#[derive(Clone, Debug)]
pub struct Config {
    /// Number of ordered factor-base slots, 2 through 8.
    pub m: usize,
    /// Override the Lemma 13 threshold; `None` uses its integer ceiling.
    pub tau: Option<u64>,
    /// Public reproducibility seed for SplitMix64; not a cryptographic RNG.
    pub seed: u64,
    /// Maximum number of fresh factor-base trials.
    pub max_trials: usize,
    /// Per-query oracle work bound (first `m-1` tuples for `Enumerate`).
    pub max_work: u64,
    /// Maximum total slot-specific columns, at most 512 for dense elimination.
    pub max_columns: usize,
}
impl Default for Config {
    fn default() -> Self {
        Self {
            m: 2,
            tau: None,
            seed: 1,
            max_trials: 16,
            max_work: 1_000_000,
            max_columns: 512,
        }
    }
}

/// A checked relation `[u]P + [v]Q = sum(points)`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Relation {
    /// Coefficient of the generator, reduced modulo `r`.
    pub u: u64,
    /// Coefficient of the target, reduced modulo `r`.
    pub v: u64,
    /// One point per ordered factor-base slot.
    pub points: Vec<Point>,
}

/// Independently replayable certificate for the successful trial.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Certificate {
    /// Recovered logarithm, checked against the target before returning.
    pub scalar: u64,
    /// Hash seeds, kept fixed throughout the successful trial.
    pub hashes: Vec<HashBase>,
    /// Exactly `N+1` verified successful relations (except identity target).
    pub relations: Vec<Relation>,
    /// Deterministically chosen nonzero row dependency over `F_r`.
    pub dependency: Vec<u64>,
    /// Number of trials attempted, including the successful one.
    pub trials: usize,
    /// Total target queries, including unsuccessful and discarded trials.
    pub attempts: usize,
}

struct Rng(u64);
impl Rng {
    fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9e3779b97f4a7c15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94d049bb133111eb);
        z ^ (z >> 31)
    }
    fn below(&mut self, n: u64) -> u64 {
        // Rejection removes modulo bias; SplitMix is still only a fixture RNG.
        let threshold = n.wrapping_neg() % n;
        loop {
            let x = self.next();
            if x >= threshold {
                return x % n;
            }
        }
    }
}

fn matrix(bases: &[Vec<Point>], relations: &[Relation]) -> Result<Vec<Vec<u64>>, Error> {
    let n: usize = bases.iter().map(Vec::len).sum();
    relations
        .iter()
        .map(|rel| {
            if rel.points.len() != bases.len() {
                return Err(Error::Verification);
            }
            let mut row = vec![0; n];
            let mut offset = 0;
            for (base, point) in bases.iter().zip(&rel.points) {
                let index = base.binary_search(point).map_err(|_| Error::Verification)?;
                row[offset + index] = 1;
                offset += base.len();
            }
            Ok(row)
        })
        .collect()
}

// First row dependency by deterministic elimination, independent of u and v.
fn dependency(rows: &[Vec<u64>], r: u64) -> Option<Vec<u64>> {
    let mut pivots: BTreeMap<usize, (Vec<u64>, Vec<u64>)> = BTreeMap::new();
    for (i, source) in rows.iter().enumerate() {
        let mut row = source.clone();
        let mut combination = vec![0; rows.len()];
        combination[i] = 1;
        for (&col, (pivot, coeff)) in &pivots {
            let k = row[col];
            for (a, &b) in row.iter_mut().zip(pivot) {
                *a = sub(*a, k * b % r, r);
            }
            for (a, &b) in combination.iter_mut().zip(coeff) {
                *a = sub(*a, k * b % r, r);
            }
        }
        match row.iter().position(|&a| a != 0) {
            None => return Some(combination),
            Some(col) => {
                let inv = pow(row[col], r - 2, r);
                for a in &mut row {
                    *a = *a * inv % r;
                }
                for a in &mut combination {
                    *a = *a * inv % r;
                }
                pivots.insert(col, (row, combination));
            }
        }
    }
    None
}

fn extract(relations: &[Relation], coeff: &[u64], r: u64) -> Option<u64> {
    let (mut u, mut v) = (0, 0);
    for (rel, &c) in relations.iter().zip(coeff) {
        u = (u + c * rel.u) % r;
        v = (v + c * rel.v) % r;
    }
    (v != 0).then(|| sub(0, u, r) * pow(v, r - 2, r) % r)
}

/// Run Figure 2 with the bounded generic enumeration backend.
pub fn solve(curve: &Curve, p: Point, q: Point, config: &Config) -> Result<Certificate, Error> {
    solve_with_oracle(curve, p, q, config, &mut Enumerate)
}

/// Run the reduction using a deterministic oracle. No runtime property of
/// an injected oracle is assumed or claimed. Every witness is checked.
pub fn solve_with_oracle(
    curve: &Curve,
    p: Point,
    q: Point,
    config: &Config,
    oracle: &mut impl DecompositionOracle,
) -> Result<Certificate, Error> {
    if p.is_none() || !curve.contains(p) || !curve.contains(q) {
        return Err(Error::Invalid("generator or target"));
    }
    if !(2..=8).contains(&config.m)
        || config.max_trials == 0
        || config.max_trials > 1000
        || config.max_columns == 0
        || config.max_columns > 512
        || config.max_work == 0
    {
        return Err(Error::Invalid("reduction bounds"));
    }
    if q.is_none() {
        return Ok(Certificate {
            scalar: 0,
            hashes: vec![],
            relations: vec![],
            dependency: vec![],
            trials: 0,
            attempts: 0,
        });
    }
    let s = (2 * curve.p..=4 * curve.p).find(|&s| prime(s)).unwrap();
    let mut root = 1u64;
    while root.pow(config.m as u32) < curve.r {
        root += 1;
    }
    let tau = config
        .tau
        .unwrap_or_else(|| (s * root.max(10 * config.m as u64)).div_ceil(curve.r - 1));
    if tau == 0 || tau > s {
        return Err(Error::Invalid(
            "threshold outside 1..=s; use a larger toy group or explicit tau",
        ));
    }
    let mut rng = Rng(config.seed);
    let mut attempts = 0;
    for trial in 1..=config.max_trials {
        let hashes: Vec<_> = (0..config.m)
            .map(|_| HashBase {
                s,
                alpha: 1 + rng.below(s - 1),
                beta: rng.below(s),
                tau,
            })
            .collect();
        let bases: Vec<_> = hashes
            .iter()
            .map(|h| h.enumerate(curve))
            .collect::<Result<_, _>>()?;
        let n: usize = bases.iter().map(Vec::len).sum();
        if n > config.max_columns {
            return Err(Error::Limit("dense relation matrix columns"));
        }
        if bases.iter().any(Vec::is_empty) {
            continue;
        }
        let mut relations = Vec::new();
        for _ in 0..20 * (n + 1) {
            attempts += 1;
            let (u, v) = (rng.below(curve.r), rng.below(curve.r));
            let target = curve.add_valid(curve.mul(p, u)?, curve.mul(q, v)?);
            if let Some(points) = oracle.find(curve, &bases, target, config.max_work)? {
                let rel = Relation { u, v, points };
                check_relation(curve, p, q, &bases, &rel)?;
                relations.push(rel);
                if relations.len() == n + 1 {
                    break;
                }
            }
        }
        if relations.len() != n + 1 {
            continue;
        }
        let coeff = dependency(&matrix(&bases, &relations)?, curve.r).ok_or(Error::Verification)?;
        if let Some(scalar) = extract(&relations, &coeff, curve.r) {
            let cert = Certificate {
                scalar,
                hashes,
                relations,
                dependency: coeff,
                trials: trial,
                attempts,
            };
            verify(curve, p, q, &cert)?;
            return Ok(cert);
        }
    }
    Err(Error::Limit(
        "factor-base trials exhausted; logarithm unresolved",
    ))
}

fn check_relation(
    curve: &Curve,
    p: Point,
    q: Point,
    bases: &[Vec<Point>],
    rel: &Relation,
) -> Result<(), Error> {
    if rel.u >= curve.r || rel.v >= curve.r || rel.points.len() != bases.len() {
        return Err(Error::Verification);
    }
    let mut sum = None;
    for (base, &point) in bases.iter().zip(&rel.points) {
        if point.is_none() || !curve.contains(point) || base.binary_search(&point).is_err() {
            return Err(Error::Verification);
        }
        sum = curve.add_valid(sum, point);
    }
    if sum != curve.add_valid(curve.mul(p, rel.u)?, curve.mul(q, rel.v)?) {
        return Err(Error::Verification);
    }
    Ok(())
}

/// Independently rebuild bases and columns, replay every relation, check a
/// nonzero modular dependency and `V != 0`, and verify `[scalar]P = Q`.
/// Trial/attempt counters are descriptive; replay does not attest their history.
pub fn verify(curve: &Curve, p: Point, q: Point, cert: &Certificate) -> Result<(), Error> {
    if p.is_none() || !curve.contains(p) || !curve.contains(q) || cert.scalar >= curve.r {
        return Err(Error::Verification);
    }
    if q.is_none() {
        return if cert.scalar == 0
            && cert.hashes.is_empty()
            && cert.relations.is_empty()
            && cert.dependency.is_empty()
            && cert.trials == 0
            && cert.attempts == 0
        {
            Ok(())
        } else {
            Err(Error::Verification)
        };
    }
    if !(2..=8).contains(&cert.hashes.len()) {
        return Err(Error::Verification);
    }
    let bases: Vec<_> = cert
        .hashes
        .iter()
        .map(|h| h.enumerate(curve))
        .collect::<Result<_, _>>()?;
    let n: usize = bases.iter().map(Vec::len).sum();
    if n > 512
        || bases.iter().any(Vec::is_empty)
        || cert.relations.len() != n + 1
        || cert.dependency.len() != n + 1
        || cert.dependency.iter().all(|&c| c == 0)
        || cert.dependency.iter().any(|&c| c >= curve.r)
    {
        return Err(Error::Verification);
    }
    for rel in &cert.relations {
        check_relation(curve, p, q, &bases, rel)?;
    }
    let rows = matrix(&bases, &cert.relations)?;
    for col in 0..n {
        let sum = rows
            .iter()
            .zip(&cert.dependency)
            .fold(0, |a, (row, &c)| (a + row[col] * c) % curve.r);
        if sum != 0 {
            return Err(Error::Verification);
        }
    }
    if extract(&cert.relations, &cert.dependency, curve.r) != Some(cert.scalar)
        || curve.mul(p, cert.scalar)? != q
    {
        return Err(Error::Verification);
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    fn fixture() -> (Curve, Point) {
        (Curve::new(211, 0, 7, 199).unwrap(), Some((3, 33)))
    }

    #[test]
    fn validates_curve_and_canonical_points() {
        let (c, p) = fixture();
        assert!(Curve::new(211, 0, 7, 197).is_err());
        assert!(Curve::new(15, 2, 2, 19).is_err());
        assert!(Curve::new(17, 0, 0, 19).is_err());
        assert!(Curve::new(u64::MAX, 0, 7, 199).is_err());
        assert!(c.encode(None).is_err());
        assert!(c.add(Some((214, 33)), p).is_err());
        assert_eq!(c.mul(p, 199).unwrap(), None);
        assert_eq!(c.add(p, c.neg(p)).unwrap(), None);
        assert_eq!(c.add(None, p).unwrap(), p);
        assert_eq!(c.add(p, p).unwrap(), c.mul(p, 2).unwrap());
    }

    #[test]
    fn inverse_hash_enumeration_matches_complete_group_scan() {
        let (c, p) = fixture();
        for (alpha, beta, tau) in [(1, 0, 1), (7, 19, 44), (430, 430, 431)] {
            let h = HashBase {
                s: 431,
                alpha,
                beta,
                tau,
            };
            let mut expected = Vec::new();
            for k in 1..c.r {
                let point = c.mul(p, k).unwrap();
                let z = c.encode(point).unwrap();
                assert_eq!(c.decode(z), point);
                if (alpha * z + beta) % 431 < tau {
                    expected.push(point);
                }
            }
            expected.sort_unstable();
            assert_eq!(h.enumerate(&c).unwrap(), expected);
        }
        assert_eq!(c.decode(2 * c.p), None);
        assert!(HashBase {
            s: 431,
            alpha: 0,
            beta: 0,
            tau: 20
        }
        .enumerate(&c)
        .is_err());
    }

    #[test]
    fn oracle_matches_cartesian_sum_for_every_target() {
        let (c, p) = fixture();
        let bases = vec![
            vec![c.mul(p, 1).unwrap(), c.mul(p, 2).unwrap()],
            vec![c.mul(p, 3).unwrap(), c.mul(p, 4).unwrap()],
        ];
        let mut bases = bases;
        for b in &mut bases {
            b.sort_unstable();
        }
        for k in 0..c.r {
            let target = c.mul(p, k).unwrap();
            let expected = bases[0]
                .iter()
                .any(|&a| bases[1].iter().any(|&b| c.add(a, b).unwrap() == target));
            let found = Enumerate.find(&c, &bases, target, 2).unwrap();
            assert_eq!(found.is_some(), expected);
        }
        assert!(matches!(
            Enumerate.find(&c, &bases, None, 1),
            Err(Error::Limit(_))
        ));
    }

    #[test]
    fn overlapping_slots_keep_separate_columns() {
        let (c, p) = fixture();
        let rows = matrix(
            &[vec![p], vec![p]],
            &[Relation {
                u: 2,
                v: 0,
                points: vec![p, p],
            }],
        )
        .unwrap();
        assert_eq!(rows, vec![vec![1, 1]]);
        let rows = vec![vec![1, 0], vec![0, 1], vec![1, 1]];
        assert_eq!(dependency(&rows, c.r).unwrap(), vec![198, 198, 1]);
    }

    #[test]
    fn solves_and_replays_seeded_known_answers() {
        let (c, p) = fixture();
        for (seed, scalar, m) in [(1, 1, 2), (2, 42, 2), (3, 198, 2), (5, 87, 3)] {
            let q = c.mul(p, scalar).unwrap();
            let config = Config {
                seed,
                m,
                ..Config::default()
            };
            let cert = solve(&c, p, q, &config).unwrap();
            assert_eq!(cert.scalar, scalar);
            verify(&c, p, q, &cert).unwrap();
            assert_eq!(cert, solve(&c, p, q, &config).unwrap());
            let mut bad = cert.clone();
            bad.relations[0].u = (bad.relations[0].u + 1) % c.r;
            assert!(verify(&c, p, q, &bad).is_err());
            let mut bad = cert.clone();
            bad.dependency.fill(0);
            assert!(verify(&c, p, q, &bad).is_err());
            let mut bad = cert.clone();
            bad.scalar = (bad.scalar + 1) % c.r;
            assert!(verify(&c, p, q, &bad).is_err());
            let mut bad = cert;
            bad.hashes[0].alpha = 0;
            assert!(verify(&c, p, q, &bad).is_err());
        }
    }

    #[test]
    fn identity_and_bounds_are_explicit() {
        let (c, p) = fixture();
        let cert = solve(&c, p, None, &Config::default()).unwrap();
        verify(&c, p, None, &cert).unwrap();
        for config in [
            Config {
                m: 1,
                ..Config::default()
            },
            Config {
                tau: Some(0),
                ..Config::default()
            },
            Config {
                max_trials: 0,
                ..Config::default()
            },
        ] {
            assert!(solve(&c, p, p, &config).is_err());
        }
        assert!(matches!(
            solve(
                &c,
                p,
                p,
                &Config {
                    max_columns: 1,
                    ..Config::default()
                }
            ),
            Err(Error::Limit(_))
        ));
        assert_eq!(
            extract(
                &[Relation {
                    u: 0,
                    v: 0,
                    points: vec![]
                }],
                &[1],
                c.r
            ),
            None
        );
    }

    #[test]
    fn small_curve_all_logarithms_and_uninformative_dependency() {
        let curve = Curve::new(17, 2, 2, 19).unwrap();
        let p = Some((5, 1));
        let config = Config {
            tau: Some(20),
            ..Config::default()
        };
        for scalar in 0..19 {
            let q = curve.mul(p, scalar).unwrap();
            let cert = solve(&curve, p, q, &config).unwrap();
            assert_eq!(cert.scalar, scalar);
            verify(&curve, p, q, &cert).unwrap();
        }
        assert!(Curve::new(17, 2, 2, 18446744073709551557).is_err());
        // A genuine but uninformative dependency has V = 0 and must restart.
        assert_eq!(
            extract(
                &[
                    Relation {
                        u: 7,
                        v: 3,
                        points: vec![]
                    },
                    Relation {
                        u: 7,
                        v: 3,
                        points: vec![]
                    },
                ],
                &[1, 18],
                19
            ),
            None
        );
    }

    #[test]
    fn exhausted_trials_and_empty_bases_are_not_successes() {
        struct Never;
        impl DecompositionOracle for Never {
            fn find(
                &mut self,
                _: &Curve,
                _: &[Vec<Point>],
                _: Point,
                _: u64,
            ) -> Result<Option<Vec<Point>>, Error> {
                Ok(None)
            }
        }
        let (c, p) = fixture();
        let config = Config {
            max_trials: 1,
            ..Config::default()
        };
        assert!(matches!(
            solve_with_oracle(&c, p, p, &config, &mut Never),
            Err(Error::Limit(_))
        ));
        assert_eq!(
            Enumerate.find(&c, &[vec![], vec![p]], None, 0).unwrap(),
            None
        );
    }

    #[test]
    fn rejects_corrupt_oracle_instead_of_accepting_a_relation() {
        struct Bad;
        impl DecompositionOracle for Bad {
            fn find(
                &mut self,
                _: &Curve,
                _: &[Vec<Point>],
                _: Point,
                _: u64,
            ) -> Result<Option<Vec<Point>>, Error> {
                Ok(Some(vec![None, None]))
            }
        }
        let (c, p) = fixture();
        assert_eq!(
            solve_with_oracle(&c, p, p, &Config::default(), &mut Bad),
            Err(Error::Verification)
        );
    }
}
