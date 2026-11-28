//! Retained signed pair witnesses for staged three/four-point decomposition.
use crate::{
    BatchScratch, Curve, Error, FactorBase, MultiSignedRelation, Point, Result, SignedTerm,
};
use std::collections::HashMap;
use std::hash::{BuildHasherDefault, Hasher};
use std::sync::atomic::{AtomicU64, Ordering};
static NEXT_ID: AtomicU64 = AtomicU64::new(1);

#[derive(Default)]
struct KeyHasher(u64);
impl Hasher for KeyHasher {
    fn write(&mut self, bytes: &[u8]) {
        for &byte in bytes {
            self.0 = self
                .0
                .wrapping_mul(0x100000001b3)
                .wrapping_add(u64::from(byte));
        }
    }
    fn write_u64(&mut self, value: u64) {
        let mut x = value;
        x ^= x >> 30;
        x = x.wrapping_mul(0xbf58476d1ce4e5b9);
        x ^= x >> 27;
        x = x.wrapping_mul(0x94d049bb133111eb);
        self.0 = x ^ (x >> 31);
    }
    fn finish(&self) -> u64 {
        self.0
    }
}
type Lookup = HashMap<u64, usize, BuildHasherDefault<KeyHasher>>;
const X_BITMAP_BITS: usize = if option_env!("M31_HIGH_BITMAP").is_some()
    || option_env!("M31_DUAL_BITMAP").is_some()
    || option_env!("M31_B512_BITMAP").is_some()
{
    22
} else {
    20
};
fn x_bitmap_bit(x: u64) -> usize {
    if option_env!("M31_HIGH_BITMAP").is_some()
        || option_env!("M31_DUAL_BITMAP").is_some()
        || option_env!("M31_B512_BITMAP").is_some()
    {
        (x as usize) >> (31 - X_BITMAP_BITS)
    } else {
        (x.wrapping_mul(0x9e3779b97f4a7c15) >> (64 - X_BITMAP_BITS)) as usize
    }
}
type Pair = [SignedTerm; 2];
struct Entry {
    point: Option<Point>,
    first: Pair,
    collisions: Vec<Pair>,
}
impl Entry {
    fn witness_count(&self) -> usize {
        1 + self.collisions.len()
    }
    fn witness(&self, index: usize) -> &Pair {
        if index == 0 {
            &self.first
        } else {
            &self.collisions[index - 1]
        }
    }
    fn witnesses(&self) -> impl Iterator<Item = &Pair> {
        std::iter::once(&self.first).chain(self.collisions.iter())
    }
}

/// Exact counters for indexed decomposition, without performance qualification.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct PairIndexStats {
    /// Raw signed pair sums constructed, including exceptional identity pairs.
    pub constructed_pairs: u64,
    /// Distinct finite/identity pair classes retained.
    pub entries: usize,
    /// Additional witnesses retained for repeated pair classes.
    pub collision_witnesses: u64,
    /// Probe candidate points produced, including unused final chunk positions.
    pub generated_candidates: u64,
    /// Candidate points actually looked up in the pair index.
    pub lookups: u64,
    /// Successful signed decompositions, including cached ones.
    pub hits: u64,
    /// Reused signed witnesses for the most recent successful target x.
    pub cache_hits: u64,
    /// Full signed point sums replayed before accepting a fresh result.
    pub group_replays: u64,
}

/// Reusable pair table, independent of the target and its unknown scalar.
///
/// Every negation class retains all pair witnesses, so overlapping pair
/// decompositions can be tried without silently dropping valid alternatives.
/// Table construction and probe chunk memory are explicitly bounded.
pub struct PairIndex<const B: u32> {
    id: u64,
    curve: Curve<B>,
    base: Vec<Point>,
    entries: Vec<Entry>,
    lookup: Lookup,
    x_bitmap: Vec<u64>,
    x_bitmap_low: Vec<u64>,
    identity: Option<usize>,
    chunk: usize,
    stats: PairIndexStats,
}

/// Caller-owned probe buffers, counters and a one-entry signed target cache.
pub struct PairWorkspace {
    owner: u64,
    left: Vec<Option<Point>>,
    right: Vec<Option<Point>>,
    meta: Vec<(usize, bool)>,
    batch: BatchScratch,
    last: Option<(u8, Point, MultiSignedRelation)>,
    stats: PairIndexStats,
}

fn flip(mut pair: Pair, negative: bool) -> Pair {
    if negative {
        for term in &mut pair {
            term.negative = !term.negative;
        }
    }
    pair
}
fn noncancelling(terms: &[SignedTerm]) -> bool {
    for (i, a) in terms.iter().enumerate() {
        if terms[i + 1..]
            .iter()
            .any(|b| a.index == b.index && a.negative != b.negative)
        {
            return false;
        }
    }
    true
}

impl<const B: u32> PairIndex<B> {
    /// Build at most `max_pairs` signed pair witnesses with batched arithmetic.
    /// Negation-folded construction evaluates exactly `columns^2` raw pairs.
    pub fn new(base: &FactorBase<B>, max_pairs: usize, chunk: usize) -> Result<Self> {
        let columns = base.representatives().len();
        let size = columns
            .checked_mul(columns)
            .ok_or(Error::ResourceLimit("pair index size overflow"))?;
        if size > max_pairs {
            return Err(Error::ResourceLimit("pair index reservation"));
        }
        if !(1..=16384).contains(&chunk) {
            return Err(Error::Invalid("pair chunk must be 1..=16384"));
        }
        let mut current = NEXT_ID.load(Ordering::Relaxed);
        let id = loop {
            let next = current
                .checked_add(1)
                .ok_or(Error::ResourceLimit("pair index identity"))?;
            match NEXT_ID.compare_exchange_weak(current, next, Ordering::Relaxed, Ordering::Relaxed)
            {
                Ok(_) => break current,
                Err(observed) => current = observed,
            }
        };
        let mut result = Self {
            id,
            curve: base.curve(),
            base: base.representatives().to_vec(),
            entries: Vec::with_capacity(size),
            lookup: Lookup::with_capacity_and_hasher(size, BuildHasherDefault::default()),
            x_bitmap: if B == 31
                && (columns <= 384 || (columns <= 512 && option_env!("M31_B512_BITMAP").is_some()))
            {
                vec![0; 1 << (X_BITMAP_BITS - 6)]
            } else {
                Vec::new()
            },
            x_bitmap_low: if B == 31 && columns <= 384 && option_env!("M31_DUAL_BITMAP").is_some() {
                vec![0; 1 << (X_BITMAP_BITS - 6)]
            } else {
                Vec::new()
            },
            identity: None,
            chunk,
            stats: PairIndexStats::default(),
        };
        let mut left = Vec::with_capacity(chunk);
        let mut right = Vec::with_capacity(chunk);
        let mut pairs = Vec::with_capacity(chunk);
        let mut batch = BatchScratch::default();
        for i in 0..columns {
            for j in i..columns {
                for negative in [false, true] {
                    if i == j && negative {
                        continue;
                    }
                    left.push(Some(result.base[i]));
                    right.push(Some(if negative {
                        result.curve.neg_inner(result.base[j])
                    } else {
                        result.base[j]
                    }));
                    pairs.push([
                        SignedTerm {
                            index: i,
                            negative: false,
                        },
                        SignedTerm { index: j, negative },
                    ]);
                    if left.len() == chunk {
                        result.flush_build(&mut left, &right, &pairs, &mut batch);
                        left.clear();
                        right.clear();
                        pairs.clear();
                    }
                }
            }
        }
        result.flush_build(&mut left, &right, &pairs, &mut batch);
        result.stats.entries = result.entries.len();
        Ok(result)
    }
    fn flush_build(
        &mut self,
        left: &mut [Option<Point>],
        right: &[Option<Point>],
        pairs: &[Pair],
        scratch: &mut BatchScratch,
    ) {
        self.curve.batch_add_inner(left, right, scratch);
        for (point, pair) in left.iter().copied().zip(pairs) {
            self.stats.constructed_pairs += 1;
            let (canonical, negative) = point.map_or((None, false), |p| {
                if p.y() > self.curve.modulus() / 2 {
                    (Some(self.curve.neg_inner(p)), true)
                } else {
                    (Some(p), false)
                }
            });
            let witness = flip(*pair, negative);
            let old = canonical.map_or(self.identity, |p| self.lookup.get(&p.x()).copied());
            if let Some(index) = old {
                self.entries[index].collisions.push(witness);
                self.stats.collision_witnesses += 1;
            } else {
                let index = self.entries.len();
                if let Some(p) = canonical {
                    self.lookup.insert(p.x(), index);
                    if !self.x_bitmap.is_empty() {
                        let bit = x_bitmap_bit(p.x());
                        self.x_bitmap[bit >> 6] |= 1u64 << (bit & 63);
                        if !self.x_bitmap_low.is_empty() {
                            let low = p.x() as usize & ((1 << X_BITMAP_BITS) - 1);
                            self.x_bitmap_low[low >> 6] |= 1u64 << (low & 63);
                        }
                    }
                } else {
                    self.identity = Some(index);
                }
                self.entries.push(Entry {
                    point: canonical,
                    first: witness,
                    collisions: Vec::new(),
                });
            }
        }
    }
    /// Construction counts. Online counts are in the caller workspace.
    pub fn stats(&self) -> &PairIndexStats {
        &self.stats
    }
    /// Allocate bounded scratch for repeated target queries.
    pub fn workspace(&self) -> PairWorkspace {
        PairWorkspace {
            owner: self.id,
            left: Vec::with_capacity(self.chunk),
            right: Vec::with_capacity(self.chunk),
            meta: Vec::with_capacity(self.chunk),
            batch: BatchScratch::default(),
            last: None,
            stats: PairIndexStats::default(),
        }
    }
    pub(crate) fn matches(&self, base: &FactorBase<B>) -> bool {
        self.curve.coefficients() == base.curve().coefficients()
            && self.base == base.representatives()
    }
    fn find(&self, p: Option<Point>) -> Option<(usize, bool)> {
        let index = match p {
            None => self.identity?,
            Some(p) => {
                if !self.x_bitmap.is_empty() {
                    let bit = x_bitmap_bit(p.x());
                    if self.x_bitmap[bit >> 6] & (1u64 << (bit & 63)) == 0 {
                        return None;
                    }
                    if !self.x_bitmap_low.is_empty() {
                        let low = p.x() as usize & ((1 << X_BITMAP_BITS) - 1);
                        if self.x_bitmap_low[low >> 6] & (1u64 << (low & 63)) == 0 {
                            return None;
                        }
                    }
                }
                *self.lookup.get(&p.x())?
            }
        };
        Some((
            index,
            p.is_some_and(|p| Some(p) != self.entries[index].point),
        ))
    }
    fn accepted(
        &self,
        target: Point,
        terms: &[SignedTerm],
        workspace: &mut PairWorkspace,
    ) -> Result<Option<MultiSignedRelation>> {
        if !noncancelling(terms) {
            return Ok(None);
        }
        let row = MultiSignedRelation::new(terms)?;
        let sum = terms.iter().fold(None, |sum, term| {
            self.curve.add_inner(
                sum,
                Some(if term.negative {
                    self.curve.neg_inner(self.base[term.index])
                } else {
                    self.base[term.index]
                }),
            )
        });
        workspace.stats.group_replays += 1;
        if sum != Some(target) {
            return Err(Error::InvalidCertificate("indexed pair witness replay"));
        }
        workspace.stats.hits += 1;
        workspace.last = Some((terms.len() as u8, target, row));
        Ok(Some(row))
    }
    fn probe(
        &self,
        m: u8,
        target: Point,
        workspace: &mut PairWorkspace,
    ) -> Result<Option<MultiSignedRelation>> {
        self.curve
            .batch_add_inner(&mut workspace.left, &workspace.right, &mut workspace.batch);
        workspace.stats.generated_candidates += workspace.left.len() as u64;
        for i in 0..workspace.left.len() {
            workspace.stats.lookups += 1;
            let Some((inner, negative)) = self.find(workspace.left[i]) else {
                continue;
            };
            let (outer, outer_negative) = workspace.meta[i];
            let outer_count = if m == 3 {
                1
            } else {
                self.entries[outer].witness_count()
            };
            for oi in 0..outer_count {
                for inner_pair in self.entries[inner].witnesses() {
                    let mut terms = [SignedTerm::default(); 4];
                    if m == 3 {
                        terms[0] = SignedTerm {
                            index: outer,
                            negative: outer_negative,
                        };
                        terms[1..3].copy_from_slice(&flip(*inner_pair, negative));
                    } else {
                        terms[..2].copy_from_slice(&flip(
                            *self.entries[outer].witness(oi),
                            outer_negative,
                        ));
                        terms[2..].copy_from_slice(&flip(*inner_pair, negative));
                    }
                    if let Some(row) = self.accepted(target, &terms[..m as usize], workspace)? {
                        return Ok(Some(row));
                    }
                }
            }
        }
        Ok(None)
    }
    /// Recover an exact signed `m=2,3,4` witness, excluding explicit opposite
    /// occurrences of the same base point. Identity pair intermediates and
    /// exceptional additions are handled by the native group arithmetic.
    pub fn decompose(
        &self,
        m: u8,
        target: Point,
        workspace: &mut PairWorkspace,
    ) -> Result<Option<MultiSignedRelation>> {
        if workspace.owner != self.id {
            return Err(Error::Invalid("pair workspace belongs to another index"));
        }
        if !(2..=4).contains(&m) || !self.curve.contains(Some(target)) {
            return Err(Error::Invalid("indexed decomposition input"));
        }
        if let Some((old_m, old_target, row)) = workspace.last {
            if old_m == m && old_target.x() == target.x() {
                let mut terms = row.summands().to_vec();
                if old_target != target {
                    for term in &mut terms {
                        term.negative = !term.negative;
                    }
                }
                workspace.stats.cache_hits += 1;
                workspace.stats.hits += 1;
                return Ok(Some(MultiSignedRelation::new(&terms)?));
            }
        }
        if m == 2 {
            if let Some((index, negative)) = self.find(Some(target)) {
                for pair in self.entries[index].witnesses() {
                    if let Some(row) = self.accepted(target, &flip(*pair, negative), workspace)? {
                        return Ok(Some(row));
                    }
                }
            }
            return Ok(None);
        }
        workspace.left.clear();
        workspace.right.clear();
        workspace.meta.clear();
        let count = if m == 3 {
            self.base.len()
        } else {
            self.entries.len()
        };
        for outer in 0..count {
            for negative in [false, true] {
                let point = if m == 3 {
                    Some(self.base[outer])
                } else {
                    self.entries[outer].point
                };
                if point.is_none() && negative {
                    continue;
                }
                // Candidate = target - signed outer point.
                let step = point.map(|p| if negative { p } else { self.curve.neg_inner(p) });
                workspace.left.push(Some(target));
                workspace.right.push(step);
                workspace.meta.push((outer, negative));
                if workspace.left.len() == self.chunk {
                    if let Some(row) = self.probe(m, target, workspace)? {
                        return Ok(Some(row));
                    }
                    workspace.left.clear();
                    workspace.right.clear();
                    workspace.meta.clear();
                }
            }
        }
        if !workspace.left.is_empty() {
            return self.probe(m, target, workspace);
        }
        Ok(None)
    }
}

#[cfg(test)]
mod bitmap_tests {
    use super::*;

    #[test]
    fn every_indexed_m31_point_survives_both_bitmap_projections() {
        let curve = Curve::<31>::new(2, 14).unwrap();
        let roots: Vec<u64> = (0..80)
            .filter(|&x| curve.lift_x(x).unwrap().is_some())
            .take(16)
            .collect();
        let base = FactorBase::without_maps(curve, &roots).unwrap();
        let index = PairIndex::new(&base, 256, 8).unwrap();
        assert!(!index.x_bitmap.is_empty());
        for entry in &index.entries {
            if let Some(point) = entry.point {
                let direct = index.find(Some(point)).expect("inserted point");
                assert_eq!(index.entries[direct.0].point, Some(point));
                let negative = curve.negate(point).unwrap();
                let opposite = index.find(Some(negative)).expect("negative class");
                assert_eq!(direct.0, opposite.0);
            }
        }
    }

    #[test]
    fn b512_bitmap_preserves_every_retained_pair_payload() {
        if option_env!("M31_B512_BITMAP").is_none() {
            return;
        }
        let curve = Curve::<31>::new(2, 14).unwrap();
        let roots: Vec<u64> = (0..curve.modulus())
            .filter(|&x| curve.lift_x(x).unwrap().is_some())
            .take(512)
            .collect();
        let base = FactorBase::without_maps(curve, &roots).unwrap();
        let index = PairIndex::new(&base, 512 * 512, 64).unwrap();
        assert_eq!(index.x_bitmap.len(), 1 << (22 - 6));
        let mut witnessed = 0;
        for (entry_id, entry) in index.entries.iter().enumerate() {
            if let Some(point) = entry.point {
                let bit = x_bitmap_bit(point.x());
                assert_ne!(index.x_bitmap[bit >> 6] & (1u64 << (bit & 63)), 0);
                assert_eq!(index.find(Some(point)), Some((entry_id, false)));
                assert_eq!(
                    index.find(Some(curve.neg_inner(point))),
                    Some((entry_id, true))
                );
            }
            for pair in entry.witnesses() {
                let signed = |term: SignedTerm| {
                    let point = index.base[term.index];
                    Some(if term.negative {
                        curve.neg_inner(point)
                    } else {
                        point
                    })
                };
                assert_eq!(
                    curve.add_inner(signed(pair[0]), signed(pair[1])),
                    entry.point
                );
                witnessed += 1;
            }
        }
        assert_eq!(witnessed, 512 * 512);
    }
}
impl PairWorkspace {
    /// Accumulated online counts for this workspace.
    pub fn stats(&self) -> &PairIndexStats {
        &self.stats
    }
}
