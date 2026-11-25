//! Compact-orbit relation extraction with a shared-factor-log DLP pass.
//!
//! Public synthetic Koblitz fixtures only. Reads a retained
//! `point_defined_factor_base` header, builds the Frobenius-quotiented S3
//! regular-root index once (no pair table, no edge selectors), then:
//!
//! 1. rank stage: decomposes random `[a]G` until the K orbit logs are fixed,
//! 2. target stage: decomposes each published target and recovers its log.
//!
//! Every stage is timed in this one process.
//!
//! Frobenius is a bit rotation in a normal basis, so a demanded partner
//! x-coordinate needs one canonical-rotation probe instead of n probes.
//!
//! Single-target online version of `koblitz_orbit_dlp_fast.rs` (which stays
//! frozen for the evidence that pins it). The relation search, rank stage and
//! descent are unchanged; only the target timers differ. Each target's online
//! interval is one chain of laps on a single clock, from the first operation on
//! the target point (`target_query_begin`) to the end of the `[d]G = Q` check
//! (`recovery_check_end`), so the five exclusive phases sum to the interval:
//! query hash, PDP (candidate generation, partner roots, index probes),
//! relation check (every `lift` call: base-point choice and group sum), descent
//! (log combination) and recovery check. Reusable setup (base, index, rank
//! stage, linear algebra) ends before the first target's interval starts.
//!
//! Usage: <base_header.jsonl> <target_points.jsonl|legacy_scalars.txt> <rank_seed> <out.jsonl>

#![recursion_limit = "256"]

// koblitz-n83-combined-20261015: derived from the log-cache producer by
// make_online_source.py; adds the KIC_TARGET_CANON target canonicalizer
// (lift_scan, claude/n83-liftscan) and the KIC_SCAN_ORDER state order
// (Feistel, claude/n83-scan-order).
// koblitz-n83-probepipe-20261015: derived from the combined producer by
// make_online_source.py; adds the KIC_PROBE_PIPELINE target-scan selector
// (software-pipelined root-table probes with prefetch).
// koblitz-n83-tablefilter-20261015: derived from the probe-pipeline
// producer by make_online_source.py; adds the KIC_ROOT_TABLE layout selector
// (16-byte exact slots and a TLB-resident blocked filter in front of them).
// koblitz-n83-stacked-20261016: derived from the two-level root-table
// producer by make_online_source.py; ports the folded S3 root index of
// koblitz-n83-state-fold-20261015 (KIC_STATE_FOLD, KIC_FOLD_PLANT,
// KIC_INDEX_CANON, KIC_INDEX_DIGEST) onto every root-table layout and probe
// loop, and adds the rank-stage selectors (KIC_RANK_CANON, KIC_RANK_ORDER,
// KIC_RANK_PROBE) so the rank stage runs on the compact table in process.
// koblitz-n83-rankcut-20261016: derived from the stacked producer by
// make_online_source.py; adds KIC_RANK_SOLVE (s3 | padd | padd_plant), the
// rank stage's partner roots by point addition, exact to the S3 loop.
// koblitz-n83-rankprobe-20261019: derived from the rank-cut producer by
// make_online_source.py; adds KIC_RANK_SOLVE=frame | frame_plant, the
// rank-cut loop in the target's Frobenius frame, exact to the rank-cut loop.
// koblitz-n83-closure-20261019: derived from the rank-probe producer by
// make_online_source.py; a Z[tau]-closure base header builds the root index
// from one representative per orbit, apart from the K' log columns.
// koblitz-n83-closure-indexlift-20261019: the index-lift producer with the
// closure's four replacements (make_online_source.py); one binary for every arm.
// koblitz-n83-indexlift-20261019: derived from the rank-probe producer by
// make_online_source.py; adds KIC_INDEX_CANON=lift_plant (planted control),
// KIC_SCAN_SELFTEST=full | sampled and two layout digests (KIC_INDEX_DIGEST).
// koblitz-n83-indexbuild-20261020: derived from the closure + index-lift
// producer by make_indexbuild_source.py; the same root index and self-test
// verdict, computed with one inversion per state row, a prefetched
// look-ahead insert loop and an eight-image self-test loop.
// koblitz-n83-indexbuild2-20261020: derived from the index-build producer
// by make_indexbuild2_source.py; the same root index, its states computed
// with seven field products instead of eleven and its keys with the linear
// run finder, eight roots at a time.
// koblitz-n83-rankfinder-20261021: derived from the round-2 index-build
// producer by make_rankfinder_source.py; the rank stage's probe keys
// computed with the linear run finder, eight keys at a time.
// koblitz-n83-fieldops-20261104: derived from the rank-finder producer by
// make_fieldops_source.py; inlined field products and squares, the state
// loop's squarings by the inlined square, byte-image linear maps and the scan
// self-test from per-round tables. Built with -C target-feature=+pclmulqdq.
// koblitz-n83-fieldops2-20261107: derived from the field-ops producer by
// make_fieldops2_source.py; at n = 83 the inlined field product and square
// are called with the degree and mask as constants (R1). Built with
// -C target-feature=+pclmulqdq.
// koblitz-n83-opcounts2-20261108: derived from the field-ops-2 producer by
// make_counted2_source.py; counts native work by kind when built with the
// `op-counts` feature AND run with KIC_OPCOUNTS=1, and reports it per phase
// and per target. Without either, every output is the parent's.
#[path = "../../koblitz-n83-fieldops2-20261107/lift2/src/lib.rs"]
#[allow(dead_code)]
mod lift2;

/// koblitz-n83-opcounts2-20261108: native work counted by kind (global
/// relaxed atomics). `bump` compiles to nothing without `op-counts` and
/// writes nothing unless KIC_OPCOUNTS=1.
mod opcount {
    use serde_json::{json, Map, Value};
    use std::sync::atomic::{AtomicU64, Ordering};
    use std::sync::OnceLock;

    pub const KINDS: [(&str, &str); 24] = [
        ("ec_add", "group"),
        ("ec_double", "group"),
        ("ec_add_trivial", "group_trivial"),
        ("ec_scalar_mul", "group_composite"),
        ("frobenius_x", "endomorphism"),
        ("fold_rotations", "endomorphism"),
        ("ec_frobenius", "endomorphism"),
        ("s3_root_solves", "native"),
        ("s3_root_solves_library", "native"),
        ("canonicalizations", "native"),
        ("root_index_probes", "native"),
        ("root_index_inserts", "native"),
        ("root_filter_queries", "native"),
        ("root_filter_inserts", "native"),
        ("relation_lifts", "native"),
        ("ec_lift_x", "native"),
        ("la_row_eliminations", "native_grouping"),
        ("la_mulmods", "native"),
        ("la_inversions", "native"),
        ("descent_mulmods", "native"),
        ("field_mul", "field"),
        ("field_sqr", "field"),
        ("field_inv", "field"),
        ("field_half_trace", "field"),
    ];
    pub const N: usize = KINDS.len();
    pub const EC_ADD: usize = 0;
    pub const EC_DOUBLE: usize = 1;
    pub const EC_ADD_TRIVIAL: usize = 2;
    pub const EC_SCALAR_MUL: usize = 3;
    pub const FROBENIUS_X: usize = 4;
    pub const FOLD_ROTATIONS: usize = 5;
    pub const EC_FROBENIUS: usize = 6;
    pub const S3_SOLVES: usize = 7;
    pub const S3_SOLVES_LIBRARY: usize = 8;
    pub const CANONICALIZATIONS: usize = 9;
    pub const ROOT_PROBES: usize = 10;
    pub const ROOT_INSERTS: usize = 11;
    pub const FILTER_QUERIES: usize = 12;
    pub const FILTER_INSERTS: usize = 13;
    pub const RELATION_LIFTS: usize = 14;
    pub const EC_LIFT_X: usize = 15;
    pub const LA_ROW_ELIMINATIONS: usize = 16;
    pub const LA_MULMODS: usize = 17;
    pub const LA_INVERSIONS: usize = 18;
    pub const DESCENT_MULMODS: usize = 19;
    pub const FIELD_MUL: usize = 20;
    pub const FIELD_SQR: usize = 21;
    pub const FIELD_INV: usize = 22;
    pub const FIELD_HALF_TRACE: usize = 23;

    #[allow(dead_code)]
    static COUNTS: [AtomicU64; N] = [const { AtomicU64::new(0) }; N];
    #[allow(dead_code)]
    static ON: OnceLock<bool> = OnceLock::new();

    /// Counting is on: built with `op-counts` and run with KIC_OPCOUNTS=1.
    #[inline(always)]
    pub fn on() -> bool {
        #[cfg(feature = "op-counts")]
        return *ON.get_or_init(|| std::env::var("KIC_OPCOUNTS").as_deref() == Ok("1"));
        #[cfg(not(feature = "op-counts"))]
        return false;
    }

    #[inline(always)]
    pub fn bump(kind: usize, by: u64) {
        #[cfg(feature = "op-counts")]
        if on() {
            COUNTS[kind].fetch_add(by, Ordering::Relaxed);
        }
        #[cfg(not(feature = "op-counts"))]
        let _ = (kind, by);
    }

    pub fn snapshot() -> [u64; N] {
        std::array::from_fn(|kind| COUNTS[kind].load(Ordering::Relaxed))
    }

    /// Takes the field products and squares made inside an inversion back
    /// out when dropped (an inversion counts once, as `field_inv`).
    pub struct InversionScope([u64; 2]);

    impl InversionScope {
        #[inline(always)]
        pub fn new() -> Self {
            if on() {
                InversionScope([COUNTS[FIELD_MUL].load(Ordering::Relaxed), COUNTS[FIELD_SQR].load(Ordering::Relaxed)])
            } else {
                InversionScope([0, 0])
            }
        }
    }

    impl Drop for InversionScope {
        #[inline(always)]
        fn drop(&mut self) {
            if on() {
                COUNTS[FIELD_MUL].store(self.0[0], Ordering::Relaxed);
                COUNTS[FIELD_SQR].store(self.0[1], Ordering::Relaxed);
            }
        }
    }

    pub fn delta(before: &[u64; N], after: &[u64; N]) -> Value {
        let mut map = Map::new();
        for (kind, &(name, _)) in KINDS.iter().enumerate() {
            map.insert(name.to_owned(), json!(after[kind] - before[kind]));
        }
        Value::Object(map)
    }

    pub fn kinds() -> Value {
        let mut map = Map::new();
        for &(name, class) in KINDS.iter() {
            map.insert(name.to_owned(), json!(class));
        }
        Value::Object(map)
    }
}

use crypto_lib::cryptanalysis::ecbench::isolation::HwCounters;
use crypto_lib::cryptanalysis::koblitz_fast_arith::{s3_x_roots, FastBinaryCurve, FastPoint};
use crypto_lib::cryptanalysis::koblitz_index_calculus::KoblitzCurve;
use crypto_lib::cryptanalysis::semaev_decomp::Gf2;
use num_bigint::BigUint;
use num_traits::ToPrimitive;
use serde_json::{json, Value};
use std::collections::HashMap;
use std::io::Write;
use std::process::ExitCode;
use std::time::{Duration, Instant};

/// Consecutive laps on one clock: the laps of an interval sum to its length.
struct PhaseClock {
    last: Instant,
}

impl PhaseClock {
    fn start() -> Self {
        Self {
            last: Instant::now(),
        }
    }

    fn lap(&mut self) -> Duration {
        let now = Instant::now();
        let elapsed = now - self.last;
        self.last = now;
        elapsed
    }
}

/// Exclusive PDP / relation-check time of one `extract` call.
#[derive(Default)]
struct ExtractSplit {
    pdp: Duration,
    relation_check: Duration,
    relation_checks: u64,
    root_calls: u64,
    skipped_symmetric_states: u64,
    filter_passes: u64,
    planted_found: u64,
}

fn ms(duration: Duration) -> f64 {
    duration.as_secs_f64() * 1000.0
}

/// F2-linear map on n <= 64 bits applied by byte tables.
struct Linear {
    tables: Vec<[u64; 256]>,
}

impl Linear {
    fn from_images(images: &[u64]) -> Self {
        let chunks = images.len().div_ceil(8);
        let mut tables = vec![[0u64; 256]; chunks];
        for (chunk, table) in tables.iter_mut().enumerate() {
            for byte in 1usize..256 {
                let low = byte & (byte - 1);
                let bit = chunk * 8 + byte.trailing_zeros() as usize;
                let image = images.get(bit).copied().unwrap_or(0);
                table[byte] = table[low] ^ image;
            }
        }
        Self { tables }
    }

    #[inline(always)]
    fn apply(&self, v: u64) -> u64 {
        let mut acc = 0u64;
        for (chunk, table) in self.tables.iter().enumerate() {
            acc ^= table[((v >> (8 * chunk)) & 0xff) as usize];
        }
        acc
    }
}

struct NormalBasis {
    n: u32,
    mask: u64,
    to_normal: Linear,
    to_poly: Linear,
}

impl NormalBasis {
    fn new(gf: &Gf2) -> Self {
        let n = gf.n as usize;
        let mask = if n == 64 { u64::MAX } else { (1u64 << n) - 1 };
        for candidate in 2u64.. {
            let mut conjugates = Vec::with_capacity(n);
            let mut value = candidate & mask;
            for _ in 0..n {
                conjugates.push(value);
                value = gf.sqr(value);
            }
            let Some(inverse_columns) = invert_columns(&conjugates, n) else {
                continue;
            };
            let basis = Self {
                n: gf.n,
                mask,
                to_normal: Linear::from_images(&inverse_columns),
                to_poly: Linear::from_images(&conjugates),
            };
            return basis;
        }
        unreachable!()
    }

    #[inline(always)]
    fn rotate(&self, v: u64, k: u32) -> u64 {
        if k == 0 {
            return v;
        }
        ((v << k) | (v >> (self.n - k))) & self.mask
    }

    /// Smallest rotation of `v` and the shift that produces it.
    #[inline(always)]
    fn canonical(&self, v: u64) -> (u64, u32) {
        let mut best = v;
        let mut best_shift = 0;
        let mut current = v;
        for shift in 1..self.n {
            current = ((current << 1) | (current >> (self.n - 1))) & self.mask;
            if current < best {
                best = current;
                best_shift = shift;
            }
        }
        (best, best_shift)
    }
}

/// Columns `c_i` form matrix M (poly = M * normal). Returns the images of the
/// poly basis vectors under M^{-1}, or None when M is singular.
fn invert_columns(columns: &[u64], n: usize) -> Option<Vec<u64>> {
    // Row r of [M | I]: low n bits are M[r][i] over normal index i.
    let mut rows: Vec<u128> = (0..n)
        .map(|r| {
            let mut row = 0u128;
            for (i, &column) in columns.iter().enumerate() {
                if (column >> r) & 1 == 1 {
                    row |= 1u128 << i;
                }
            }
            row | (1u128 << (64 + r))
        })
        .collect();
    for pivot in 0..n {
        let found = (pivot..n).find(|&r| (rows[r] >> pivot) & 1 == 1)?;
        rows.swap(pivot, found);
        for r in 0..n {
            if r != pivot && (rows[r] >> pivot) & 1 == 1 {
                rows[r] ^= rows[pivot];
            }
        }
    }
    // Row i now reads x_i = sum_r Minv[i][r] y_r in its high half.
    let mut images = vec![0u64; n];
    for (i, row) in rows.iter().enumerate() {
        let high = (row >> 64) as u64;
        for (r, image) in images.iter_mut().enumerate() {
            if (high >> r) & 1 == 1 {
                *image |= 1u64 << i;
            }
        }
    }
    Some(images)
}

/// Table-driven S3 root solver: S3(u, v, t) = 0 as a quadratic in v.
struct S3Solver {
    square: Linear,
    half_trace: Linear,
    trace_mask: u64,
    b: u64,
}

impl S3Solver {
    fn new(gf: &Gf2, b: u64) -> Self {
        let n = gf.n as usize;
        assert!(n % 2 == 1, "half-trace solver needs odd n");
        let unit: Vec<u64> = (0..n).map(|bit| 1u64 << bit).collect();
        let half_trace_images: Vec<u64> = unit
            .iter()
            .map(|&e| {
                let mut acc = e;
                let mut power = e;
                for _ in 0..(n - 1) / 2 {
                    power = gf.sqr(gf.sqr(power));
                    acc ^= power;
                }
                acc
            })
            .collect();
        let mut trace_mask = 0u64;
        for (bit, &e) in unit.iter().enumerate() {
            let mut acc = e;
            let mut power = e;
            for _ in 1..n {
                power = gf.sqr(power);
                acc ^= power;
            }
            if acc & 1 == 1 {
                trace_mask |= 1u64 << bit;
            }
        }
        Self {
            square: Linear::from_images(&unit.iter().map(|&e| gf.sqr(e)).collect::<Vec<_>>()),
            half_trace: Linear::from_images(&half_trace_images),
            trace_mask,
            b,
        }
    }

    /// Same roots, in the same order, as `s3_x_roots` on the generic branch.
    #[inline(always)]
    fn roots(&self, gf: &Gf2, basis: &NormalBasis, left: u64, right: u64) -> Option<[u64; 2]> {
        let s = left ^ right;
        let a = self.square.apply(s);
        let p = gf.mul(left, right);
        let ps = self.square.apply(p);
        if a == 0 || ps == 0 {
            return s3_x_roots(gf, self.b, left, right);
        }
        let inv_combined = invert(gf, basis, gf.mul(a, ps));
        let q = gf.mul(p, gf.mul(ps, inv_combined));
        let c = ps ^ self.b;
        let d = gf.mul(gf.mul(c, a), gf.mul(a, inv_combined));
        if (d & self.trace_mask).count_ones() & 1 == 1 {
            return None;
        }
        let first = gf.mul(q, self.half_trace.apply(d));
        Some([first, first ^ q])
    }
}

/// Itoh-Tsujii inversion with the `a^(2^k)` steps done as normal-basis rotations.
#[inline(always)]
fn invert(gf: &Gf2, basis: &NormalBasis, a: u64) -> u64 {
    let e = gf.n - 1;
    let mut c = a;
    let mut k = 1u32;
    let bits = 32 - e.leading_zeros();
    for i in (0..bits - 1).rev() {
        let raised = basis
            .to_poly
            .apply(basis.rotate(basis.to_normal.apply(c), k));
        c = gf.mul(c, raised);
        k *= 2;
        if (e >> i) & 1 == 1 {
            c = gf.mul(gf.sqr(c), a);
            k += 1;
        }
    }
    gf.sqr(c)
}

/// Open-addressing u64 -> u64 table; keys are < 2^63 so u64::MAX marks empty.
/// Key and value share a slot so a probe touches one cache line.
/// A negative answer skips an exact root-table probe. Every inserted key is
/// also inserted here, so the filter cannot discard a table witness.
struct RootBloom {
    words: Vec<u64>,
    bit_mask: usize,
}

impl RootBloom {
    fn with_capacity(keys: usize) -> Self {
        let bits = keys
            .checked_mul(8)
            .and_then(usize::checked_next_power_of_two)
            .expect("root Bloom size overflow")
            .max(64);
        Self {
            words: vec![0; bits / 64],
            bit_mask: bits - 1,
        }
    }

    #[inline(always)]
    fn positions(&self, key: u64) -> [usize; 3] {
        let first = mix_root_bloom(key ^ 0xA5A5_38F9_9328_6F3D);
        let step = mix_root_bloom(key.rotate_left(17) ^ 0xD4C9_3E72_B719_485B) | 1;
        [0, 1, 2].map(|index| first.wrapping_add(index * step) as usize & self.bit_mask)
    }

    #[inline(always)]
    fn insert(&mut self, key: u64) {
        for bit in self.positions(key) {
            self.words[bit >> 6] |= 1u64 << (bit & 63);
        }
    }

    #[inline(always)]
    fn contains(&self, key: u64) -> bool {
        self.positions(key)
            .into_iter()
            .all(|bit| self.words[bit >> 6] & (1u64 << (bit & 63)) != 0)
    }

    fn bytes(&self) -> usize {
        self.words.len() * std::mem::size_of::<u64>()
    }
}

#[inline(always)]
fn mix_root_bloom(mut value: u64) -> u64 {
    value = (value ^ (value >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    value ^ (value >> 31)
}

struct RootTable {
    slots: Vec<(u64, u64)>,
    shift: u32,
    len: usize,
    bloom: Option<RootBloom>,
}

impl RootTable {
    fn with_capacity(entries: usize) -> Self {
        let slots = (entries * 2).next_power_of_two().max(16);
        Self {
            slots: vec![(u64::MAX, 0); slots],
            shift: 64 - slots.trailing_zeros(),
            len: 0,
            bloom: (std::env::var("KIC_ROOT_BLOOM").as_deref() == Ok("1"))
                .then(|| RootBloom::with_capacity(entries)),
        }
    }

    #[inline(always)]
    fn slot(&self, key: u64) -> usize {
        (key.wrapping_mul(0x9E37_79B9_7F4A_7C15) >> self.shift) as usize
    }

    fn insert_if_absent(&mut self, key: u64, value: u64) {
        let mask = self.slots.len() - 1;
        let mut slot = self.slot(key);
        loop {
            if self.slots[slot].0 == u64::MAX {
                self.slots[slot] = (key, value);
                self.len += 1;
                if let Some(bloom) = &mut self.bloom {
                    bloom.insert(key);
                }
                return;
            }
            if self.slots[slot].0 == key {
                return;
            }
            slot = (slot + 1) & mask;
        }
    }

    #[inline(always)]
    fn get(&self, key: u64) -> Option<u64> {
        if self
            .bloom
            .as_ref()
            .is_some_and(|bloom| !bloom.contains(key))
        {
            return None;
        }
        let mask = self.slots.len() - 1;
        let mut slot = self.slot(key);
        loop {
            let (stored, value) = self.slots[slot];
            if stored == key {
                return Some(value);
            }
            if stored == u64::MAX {
                return None;
            }
            slot = (slot + 1) & mask;
        }
    }
}

#[cfg(test)]
mod root_bloom_table_tests {
    use super::{mix_root_bloom, RootBloom, RootTable};

    #[test]
    fn screened_lookup_matches_exact_table() {
        let mut reference = RootTable::with_capacity(4096);
        reference.bloom = None;
        let mut screened = RootTable::with_capacity(4096);
        screened.bloom = Some(RootBloom::with_capacity(4096));
        for i in 0..4096u64 {
            let key = mix_root_bloom(i) & (u64::MAX >> 1);
            reference.insert_if_absent(key, i);
            screened.insert_if_absent(key, i);
            screened.insert_if_absent(key, i + 1);
        }
        for i in 0..100_000u64 {
            let key = mix_root_bloom(i ^ 0xD1B5_4A32_D192_ED03) & (u64::MAX >> 1);
            assert_eq!(screened.get(key), reference.get(key));
        }
        for &(key, value) in &reference.slots {
            if key != u64::MAX {
                assert!(screened.bloom.as_ref().unwrap().contains(key));
                assert_eq!(screened.get(key), Some(value));
            }
        }
    }
}

#[derive(Clone, Copy)]
struct State {
    left: u16,
    right: u16,
    relative: u16,
    normal_roots: [u64; 2],
}

struct Index {
    states: Vec<State>,
    table: RootTable,
    shifted: Vec<Vec<u64>>,
    pair_candidates: usize,
    counterparts: Option<Vec<u32>>,
}

fn pack(left: u16, right: u16, relative: u16, shift: u32) -> u64 {
    (left as u64) | ((right as u64) << 16) | ((relative as u64) << 32) | ((shift as u64) << 48)
}

fn unpack(value: u64) -> (usize, usize, usize, u32) {
    (
        (value & 0xffff) as usize,
        ((value >> 16) & 0xffff) as usize,
        ((value >> 32) & 0xffff) as usize,
        ((value >> 48) & 0xffff) as u32,
    )
}

fn build_index(
    gf: &Gf2,
    basis: &NormalBasis,
    solver: &S3Solver,
    reps: &[u64],
    pair_symmetry: bool,
) -> Index {
    let n = gf.n as usize;
    let shifted: Vec<Vec<u64>> = reps
        .iter()
        .map(|&code| {
            let mut row = Vec::with_capacity(n);
            let mut value = code;
            for _ in 0..n {
                row.push(value);
                value = gf.sqr(value);
            }
            row
        })
        .collect();
    let width = reps.len();
    let slot = |left: usize, right: usize, relative: usize| (left * width + right) * n + relative;
    let mate_slot =
        |left: usize, right: usize, relative: usize| slot(right, left, (n - relative) % n);
    let mut pair_candidates = 0;
    let (states, counterparts) = if pair_symmetry {
        // Build each unordered pair orbit once, then restore its swapped
        // alias in the original scan position without another S3 solve.
        // This keeps the public-query scan origin identical to the control.
        let mut slots: Vec<Option<State>> = vec![None; width * width * n];
        for left in 0..width {
            for right in left..width {
                for relative in 0..n {
                    if left == right && relative > n - relative {
                        continue;
                    }
                    pair_candidates += 1;
                    if let Some(roots) =
                        solver.roots(gf, basis, shifted[left][0], shifted[right][relative])
                    {
                        let normal_roots = [
                            basis.to_normal.apply(roots[0]),
                            basis.to_normal.apply(roots[1]),
                        ];
                        let original = slot(left, right, relative);
                        let swapped = mate_slot(left, right, relative);
                        assert!(slots[original].is_none());
                        slots[original] = Some(State {
                            left: left as u16,
                            right: right as u16,
                            relative: relative as u16,
                            normal_roots,
                        });
                        if swapped != original {
                            assert!(slots[swapped].is_none());
                            slots[swapped] = Some(State {
                                left: right as u16,
                                right: left as u16,
                                relative: ((n - relative) % n) as u16,
                                normal_roots: [
                                    basis.rotate(normal_roots[0], ((n - relative) % n) as u32),
                                    basis.rotate(normal_roots[1], ((n - relative) % n) as u32),
                                ],
                            });
                        }
                    }
                }
            }
        }
        let mut positions = vec![u32::MAX; slots.len()];
        let mut states = Vec::new();
        for (candidate_slot, state) in slots.into_iter().enumerate() {
            if let Some(state) = state {
                positions[candidate_slot] = states.len() as u32;
                states.push(state);
            }
        }
        let counterparts = states
            .iter()
            .map(|state| {
                let mate = mate_slot(
                    state.left as usize,
                    state.right as usize,
                    state.relative as usize,
                );
                let position = positions[mate];
                assert_ne!(position, u32::MAX);
                position
            })
            .collect();
        (states, Some(counterparts))
    } else {
        let mut states = Vec::new();
        for left in 0..width {
            for right in 0..width {
                for relative in 0..n {
                    pair_candidates += 1;
                    if let Some(roots) =
                        solver.roots(gf, basis, shifted[left][0], shifted[right][relative])
                    {
                        states.push(State {
                            left: left as u16,
                            right: right as u16,
                            relative: relative as u16,
                            normal_roots: [
                                basis.to_normal.apply(roots[0]),
                                basis.to_normal.apply(roots[1]),
                            ],
                        });
                    }
                }
            }
        }
        (states, None)
    };
    let mut table = RootTable::with_capacity(pair_candidates * 2);
    for (index, state) in states.iter().enumerate() {
        if counterparts
            .as_ref()
            .is_some_and(|partners: &Vec<u32>| partners[index] < index as u32)
        {
            continue;
        }
        for &root in &state.normal_roots {
            let (canonical, shift) = basis.canonical(root);
            table.insert_if_absent(
                canonical,
                pack(state.left, state.right, state.relative, shift),
            );
        }
    }
    Index {
        states,
        table,
        shifted,
        pair_candidates,
        counterparts,
    }
}

struct Relation {
    point_indices: [usize; 4],
    x_codes: [u64; 4],
    intermediates: [u64; 2],
    probes: u64,
}

struct ExtractOutcome {
    relation: Option<Relation>,
    probes: u64,
    capped: bool,
}

#[derive(Clone, Copy)]
enum TargetInput {
    PublicPoint(FastPoint),
    KnownAnswerScalar(u64),
}

struct Base {
    points: Vec<FastPoint>,
    labels: Vec<(usize, u64)>,
    by_x: HashMap<u64, Vec<usize>>,
    columns: usize,
}

fn lift(
    fast: &FastBinaryCurve,
    base: &Base,
    codes: &[u64; 4],
    target: FastPoint,
) -> Option<[usize; 4]> {
    let choices: Vec<&Vec<usize>> = codes
        .iter()
        .map(|code| base.by_x.get(code))
        .collect::<Option<_>>()?;
    for &a in choices[0] {
        for &b in choices[1] {
            let ab = fast.add(base.points[a], base.points[b]);
            for &c in choices[2] {
                let abc = fast.add(ab, base.points[c]);
                for &d in choices[3] {
                    if fast.add(abc, base.points[d]) == target {
                        return Some([a, b, c, d]);
                    }
                }
            }
        }
    }
    None
}

fn extract(
    gf: &Gf2,
    fast: &FastBinaryCurve,
    basis: &NormalBasis,
    solver: &S3Solver,
    index: &Index,
    base: &Base,
    target: FastPoint,
    start: usize,
    probe_cap: Option<u64>,
    clock: &mut PhaseClock,
    split: &mut ExtractSplit,
) -> ExtractOutcome {
    let relation = extract_timed(
        gf, fast, basis, solver, index, base, target, start, probe_cap, clock, split,
    );
    split.pdp += clock.lap();
    relation
}

/// The search of `koblitz_orbit_dlp_fast.rs`; laps are taken only around
/// `lift`, which runs on index hits, so the probe loop carries no timer.
#[allow(clippy::too_many_arguments)]
fn extract_timed(
    gf: &Gf2,
    fast: &FastBinaryCurve,
    basis: &NormalBasis,
    solver: &S3Solver,
    index: &Index,
    base: &Base,
    target: FastPoint,
    start: usize,
    probe_cap: Option<u64>,
    clock: &mut PhaseClock,
    split: &mut ExtractSplit,
) -> ExtractOutcome {
    let Some((target_x, _)) = target else {
        return ExtractOutcome {
            relation: None,
            probes: 0,
            capped: false,
        };
    };
    let n = gf.n;
    let mut probes = 0u64;
    // Callers provide a rotating, target-dependent origin so rank-stage rows
    // do not concentrate on the same early columns.
    let len = index.states.len();
    let start = start % len.max(1);
    let first = index.states[start..]
        .iter()
        .enumerate()
        .map(|(offset, state)| (start + offset, state));
    let second = index.states[..start].iter().enumerate();
    for (state_index, state) in first.chain(second) {
        if let Some(counterparts) = &index.counterparts {
            let mate_index = counterparts[state_index] as usize;
            let distance = (state_index + len - start) % len;
            let mate_distance = (mate_index + len - start) % len;
            if mate_distance < distance {
                split.skipped_symmetric_states += 1;
                continue;
            }
        }
        for shift in 0..n {
            let left_x = index.shifted[state.left as usize][shift as usize];
            let right_x = index.shifted[state.right as usize]
                [(shift as usize + state.relative as usize) % n as usize];
            for &normal_root in &state.normal_roots {
                let absolute = basis.to_poly.apply(basis.rotate(normal_root, shift));
                split.root_calls += 1;
                let Some(partners) = solver.roots(gf, basis, absolute, target_x) else {
                    continue;
                };
                for partner in partners {
                    probes += 1;
                    let (canonical, partner_shift) =
                        basis.canonical(basis.to_normal.apply(partner));
                    let Some(value) = index.table.get(canonical) else {
                        if probe_cap.is_some_and(|cap| probes >= cap) {
                            return ExtractOutcome {
                                relation: None,
                                probes,
                                capped: true,
                            };
                        }
                        continue;
                    };
                    let (left2, right2, relative2, stored_shift) = unpack(value);
                    let left_shift2 = ((stored_shift + n - partner_shift) % n) as usize;
                    let right_shift2 = (left_shift2 + relative2) % n as usize;
                    let codes = [
                        left_x,
                        right_x,
                        index.shifted[left2][left_shift2],
                        index.shifted[right2][right_shift2],
                    ];
                    split.pdp += clock.lap();
                    let lifted = lift(fast, base, &codes, target);
                    split.relation_check += clock.lap();
                    split.relation_checks += 1;
                    if let Some(point_indices) = lifted {
                        return ExtractOutcome {
                            relation: Some(Relation {
                                point_indices,
                                x_codes: codes,
                                intermediates: [absolute, partner],
                                probes,
                            }),
                            probes,
                            capped: false,
                        };
                    }
                    if probe_cap.is_some_and(|cap| probes >= cap) {
                        return ExtractOutcome {
                            relation: None,
                            probes,
                            capped: true,
                        };
                    }
                }
            }
        }
    }
    ExtractOutcome {
        relation: None,
        probes,
        capped: false,
    }
}

/// Frobenius-closed signed-orbit base from a deterministic public x-scan.
///
/// Each accepted x lifts to a point, is projected into the order-r subgroup by
/// the cofactor, and contributes its whole signed Frobenius orbit. Point logs
/// are unknown; the label of member `phi^k(+-R_j)` is `(j, +-lambda^k)`.
fn construct_base(
    fast: &FastBinaryCurve,
    curve: &KoblitzCurve,
    b: u64,
    columns: usize,
    r: u64,
) -> (
    Vec<FastPoint>,
    Vec<(usize, u64)>,
    Vec<Option<[u64; 2]>>,
    u64,
) {
    let gf = &fast.gf;
    let n = fast.n as usize;
    let lambda = curve.lambda.to_u64().unwrap();
    let mut seen = std::collections::HashSet::new();
    let mut points = Vec::with_capacity(columns * 2 * n);
    let mut labels = Vec::with_capacity(columns * 2 * n);
    let mut reps = Vec::with_capacity(columns);
    let mut scanned = 0u64;
    let mut raw_x = 1u64;
    while reps.len() < columns {
        scanned += 1;
        for point in fast.points_with_x(b, raw_x) {
            let Some((px, py)) = fast.scalar_mul(point, &curve.cofactor) else {
                continue;
            };
            if px <= 1 {
                continue;
            }
            let mut key = px;
            let mut x = px;
            for _ in 1..n {
                x = gf.sqr(x);
                key = key.min(x);
            }
            if !seen.insert(key) {
                continue;
            }
            let column = reps.len();
            reps.push(Some([px, py]));
            let (mut cx, mut cy) = (px, py);
            let mut coefficient = 1u64;
            for _ in 0..n {
                points.push(Some((cx, cy)));
                labels.push((column, coefficient));
                points.push(Some((cx, cx ^ cy)));
                labels.push((column, (r - coefficient) % r));
                cx = gf.sqr(cx);
                cy = gf.sqr(cy);
                coefficient = mulmod(coefficient, lambda, r);
            }
            if reps.len() == columns {
                break;
            }
        }
        raw_x += 1;
    }
    let rep = reps[0].map(|[x, y]| (x, y));
    assert_eq!(
        fast.scalar_mul(rep, &BigUint::from(lambda)),
        rep.map(|(x, y)| (gf.sqr(x), gf.sqr(y))),
        "Frobenius must act as lambda on the subgroup"
    );
    (points, labels, reps, scanned)
}

fn mulmod(a: u64, b: u64, r: u64) -> u64 {
    ((a as u128 * b as u128) % r as u128) as u64
}

fn powmod(mut a: u64, mut e: u64, r: u64) -> u64 {
    let mut acc = 1u64;
    while e > 0 {
        if e & 1 == 1 {
            acc = mulmod(acc, a, r);
        }
        a = mulmod(a, a, r);
        e >>= 1;
    }
    acc
}

/// Incremental row echelon mod prime r over K unknowns plus a right-hand side.
struct Echelon {
    r: u64,
    columns: usize,
    pivots: Vec<Option<Vec<u64>>>,
    rank: usize,
}

impl Echelon {
    fn insert(&mut self, mut row: Vec<u64>) -> bool {
        for column in 0..self.columns {
            if row[column] == 0 {
                continue;
            }
            if let Some(pivot) = &self.pivots[column] {
                let factor = row[column];
                opcount::bump(opcount::LA_ROW_ELIMINATIONS, 1);
                opcount::bump(opcount::LA_MULMODS, (row.len() - column) as u64);
                for (value, &p) in row.iter_mut().zip(pivot.iter()).skip(column) {
                    *value = (*value + self.r - mulmod(factor, p, self.r)) % self.r;
                }
            } else {
                let inverse = powmod(row[column], self.r - 2, self.r);
                opcount::bump(opcount::LA_INVERSIONS, 1);
                opcount::bump(opcount::LA_MULMODS, (row.len() - column) as u64);
                for value in row.iter_mut().skip(column) {
                    *value = mulmod(*value, inverse, self.r);
                }
                self.pivots[column] = Some(row);
                self.rank += 1;
                return true;
            }
        }
        false
    }

    fn solve(&self) -> Vec<u64> {
        let mut solution = vec![0u64; self.columns];
        for column in (0..self.columns).rev() {
            let pivot = self.pivots[column].as_ref().expect("full rank");
            let mut value = pivot[self.columns];
            opcount::bump(opcount::LA_MULMODS, (self.columns - column - 1) as u64);
            for other in column + 1..self.columns {
                value = (value + self.r - mulmod(pivot[other], solution[other], self.r)) % self.r;
            }
            solution[column] = value;
        }
        solution
    }
}

fn relation_row(base: &Base, relation: &Relation, rhs: u64, r: u64) -> Vec<u64> {
    let mut row = vec![0u64; base.columns + 1];
    for &index in &relation.point_indices {
        let (column, coefficient) = base.labels[index];
        row[column] = (row[column] + coefficient) % r;
    }
    row[base.columns] = rhs % r;
    row
}

fn peak_rss_bytes() -> Option<u64> {
    #[cfg(unix)]
    {
        let mut usage = std::mem::MaybeUninit::<libc::rusage>::uninit();
        // SAFETY: getrusage writes the complete rusage value on success.
        if unsafe { libc::getrusage(libc::RUSAGE_SELF, usage.as_mut_ptr()) } != 0 {
            return None;
        }
        // SAFETY: the successful getrusage call initialized usage above.
        let rss = unsafe { usage.assume_init() }.ru_maxrss;
        if rss < 0 {
            return None;
        }
        #[cfg(target_os = "macos")]
        return Some(rss as u64);
        #[cfg(not(target_os = "macos"))]
        return (rss as u64).checked_mul(1024);
    }
    #[cfg(not(unix))]
    {
        None
    }
}

// ── Tier 1 factor-log cache (cryptanalysis n83-onetarget-tier1 patch) ──
//
// Added by `experiments/koblitz-single-target-n83-tier1-20261014/ic_log_cache.patch`
// in aburan28/cryptanalysis; the upstream file is unchanged.  The base logs
// `L_j = log_G(R_j)` of the orbit representatives are the unique full-rank
// solution of the rank stage, a function of the factor base alone.
// `KIC_LOG_TABLE_OUT=<path>` writes them after the rank stage;
// `KIC_LOG_TABLE_IN=<path>` skips the rank stage, reads them, checks the table
// names this curve and base, and verifies every `[L_j]G = R_j` before any
// target work.  Load and verification are timed as the relation-LA phase of
// the reusable setup, outside the target interval.  The relation search, the
// descent and the five target-phase timers are unchanged.  Wide path only.
mod log_cache {
    use serde_json::{json, Value};

    pub const KIND: &str = "compact_orbit_factor_log_table";

    pub fn input_path() -> Option<String> {
        std::env::var("KIC_LOG_TABLE_IN").ok().filter(|p| !p.is_empty())
    }

    pub fn output_path() -> Option<String> {
        std::env::var("KIC_LOG_TABLE_OUT").ok().filter(|p| !p.is_empty())
    }

    /// Read a table and check that it names this curve and base.
    pub fn load(
        path: &str,
        n: u32,
        a: u8,
        r: u64,
        base_hash: &str,
        columns: usize,
    ) -> (Vec<u64>, String) {
        let bytes = std::fs::read(path).expect("read KIC_LOG_TABLE_IN");
        let digest = blake3::hash(&bytes).to_hex().to_string();
        let table: Value = serde_json::from_slice(&bytes).expect("parse factor-log table");
        assert_eq!(table["kind"], KIND, "not a factor-log table");
        assert_eq!(table["n"].as_u64(), Some(u64::from(n)), "log table n differs");
        assert_eq!(table["a"].as_u64(), Some(u64::from(a)), "log table a differs");
        assert_eq!(
            table["subgroup_order"].as_str(),
            Some(r.to_string().as_str()),
            "log table r differs"
        );
        assert_eq!(table["base_hash"].as_str(), Some(base_hash), "log table base differs");
        assert_eq!(
            table["orbit_columns"].as_u64(),
            Some(columns as u64),
            "log table width differs"
        );
        let logs: Vec<u64> = table["logs"]
            .as_array()
            .expect("logs array")
            .iter()
            .map(|v| {
                v.as_str()
                    .expect("decimal log string")
                    .parse::<u64>()
                    .expect("u64 log")
            })
            .collect();
        assert_eq!(logs.len(), columns, "log table length differs");
        assert!(logs.iter().all(|&l| l < r), "log out of range");
        (logs, digest)
    }

    pub fn write(path: &str, n: u32, a: u8, r: u64, base_hash: &str, logs: &[u64], provenance: Value) {
        let table = json!({
            "kind": KIND,
            "schema_version": 1,
            "n": n,
            "a": a,
            "subgroup_order": r.to_string(),
            "base_hash": base_hash,
            "orbit_columns": logs.len(),
            "log_definition": "logs[j] = log_G(R_j) for factor_base_representatives[j]",
            "logs": logs.iter().map(|l| l.to_string()).collect::<Vec<_>>(),
            "provenance": provenance,
        });
        std::fs::write(path, format!("{table}\n")).expect("write KIC_LOG_TABLE_OUT");
    }
}

// ── Wide (`u128`-word) compact-orbit pipeline for `64 < n ≤ 127` ──
//
// Twin of the `u64` path above with identical stage semantics and the same
// online-interval instrumentation (five phase timers on one clock, hardware
// counters around the whole target interval).  Subgroup scalars, orbit
// indices, packed witnesses, and the rank linear algebra stay `u64`; only
// field elements move to the wider word.
mod wide {
    use super::{
        ms, mix_root_bloom, pack, unpack, Echelon, ExtractSplit, HwCounters, PhaseClock,
    };
    use crypto_lib::cryptanalysis::koblitz_fast_arith::{
        s3_x_roots_128, FastBinaryCurve128, FastPoint128,
    };
    use crypto_lib::cryptanalysis::koblitz_index_calculus::KoblitzCurve;
    use crypto_lib::cryptanalysis::semaev_decomp::Gf2_128;
    use super::opcount as oc;
    use num_bigint::BigUint;
    use num_traits::ToPrimitive;
    use serde_json::{json, Value};
    use std::collections::HashMap;
    use std::io::Write;
    use std::time::Instant;

    // koblitz-n83-fieldops-20261104 (F1): every field product and square of
    // this module, inlined (see make_fieldops_source.py for the proof).
    #[inline(always)]
    fn fmul(gf: &Gf2_128, a: u128, b: u128) -> u128 {
        oc::bump(oc::FIELD_MUL, 1);
        // koblitz-n83-fieldops2-20261107 (R1): at n = 83 the degree and mask are
        // the constants gf.n and gf.mask already hold, so the folds' shifts are fixed.
        if gf.n == 83 {
            // SAFETY: as below.
            return unsafe { fast_field::mul(83, (1u128 << 83) - 1, (gf.irr ^ (1u128 << 83)) as u64, a, b) };
        }
        // SAFETY: fast_field::check asserted the carry-less multiply before any use.
        unsafe { fast_field::mul(gf.n, gf.mask, (gf.irr ^ (1u128 << gf.n)) as u64, a, b) }
    }

    #[inline(always)]
    fn fsqr(gf: &Gf2_128, a: u128) -> u128 {
        oc::bump(oc::FIELD_SQR, 1);
        // koblitz-n83-fieldops2-20261107 (R1): as for fmul.
        if gf.n == 83 {
            // SAFETY: as below.
            return unsafe { fast_field::sqr(83, (1u128 << 83) - 1, (gf.irr ^ (1u128 << 83)) as u64, a) };
        }
        // SAFETY: as for fmul.
        unsafe { fast_field::sqr(gf.n, gf.mask, (gf.irr ^ (1u128 << gf.n)) as u64, a) }
    }

    mod fast_field {
        use super::Gf2_128;
        use std::arch::x86_64::*;

        #[inline(always)]
        fn word(v: __m128i) -> u128 {
            // SAFETY: __m128i and u128 are 16 plain bytes; lane 0 is the low word.
            unsafe { std::mem::transmute::<__m128i, u128>(v) }
        }

        #[inline(always)]
        unsafe fn clmul(a: u64, b: u64) -> u128 {
            word(_mm_clmulepi64_si128::<0x00>(_mm_cvtsi64_si128(a as i64), _mm_cvtsi64_si128(b as i64)))
        }

        /// The library's `Gf2_128::reduce_fold`, statement for statement:
        /// P = hi z^128 + lo of degree at most 2n - 2.
        #[inline(always)]
        unsafe fn reduce(n: u32, mask: u128, tail: u64, lo: u128, hi: u128) -> u128 {
            let h = (lo >> n) | (hi << (128 - n));
            let acc = lo & mask;
            let ht = clmul(h as u64, tail) ^ (clmul((h >> 64) as u64, tail) << 64);
            let h1 = (ht >> n) as u64;
            acc ^ (ht & mask) ^ clmul(h1, tail)
        }

        /// a b: lo = a0 b0 + (a0 b1 + a1 b0) z^64, hi = a1 b1 + (a0 b1 + a1 b0) z^-64.
        #[inline(always)]
        pub unsafe fn mul(n: u32, mask: u128, tail: u64, a: u128, b: u128) -> u128 {
            let x = _mm_set_epi64x((a >> 64) as i64, a as i64);
            let y = _mm_set_epi64x((b >> 64) as i64, b as i64);
            let z0 = _mm_clmulepi64_si128::<0x00>(x, y);
            let z2 = _mm_clmulepi64_si128::<0x11>(x, y);
            let z1 = _mm_xor_si128(_mm_clmulepi64_si128::<0x01>(x, y), _mm_clmulepi64_si128::<0x10>(x, y));
            let lo = word(_mm_xor_si128(z0, _mm_slli_si128::<8>(z1)));
            let hi = word(_mm_xor_si128(z2, _mm_srli_si128::<8>(z1)));
            reduce(n, mask, tail, lo, hi)
        }

        /// a^2 = a0^2 + a1^2 z^128 in characteristic 2.
        #[inline(always)]
        pub unsafe fn sqr(n: u32, mask: u128, tail: u64, a: u128) -> u128 {
            let x = _mm_set_epi64x((a >> 64) as i64, a as i64);
            let lo = word(_mm_clmulepi64_si128::<0x00>(x, x));
            let hi = word(_mm_clmulepi64_si128::<0x11>(x, x));
            reduce(n, mask, tail, lo, hi)
        }

        /// Fail closed unless the CPU has the carry-less multiply, the field
        /// meets the library's fold conditions, and the inlined product and
        /// square equal the library's on edge cases and 65,536 pseudo-random
        /// pairs.
        pub fn check(gf: &Gf2_128) {
            assert!(std::arch::is_x86_feature_detected!("pclmulqdq"), "the field ops need the carry-less multiply");
            let n = gf.n;
            assert!((2..=127).contains(&n), "the field ops need 2 <= n <= 127");
            let tail = gf.irr ^ (1u128 << n);
            assert!(tail != 0 && tail >> 64 == 0, "the field ops need a non-zero tail below z^64");
            let d = 127 - tail.leading_zeros();
            assert!(2 * d < n + 2 && n + d <= 129, "the library's two folds do not apply to this field");
            let mut values = vec![0u128, 1, 2, gf.mask, gf.mask >> 1, 1u128 << (n - 1), gf.mask ^ 1, tail];
            let mut x = 0x243F_6A88_85A3_08D3_1319_8A2E_0370_7344u128;
            for _ in 0..504 {
                x ^= x << 13;
                x ^= x >> 7;
                x ^= x << 17;
                values.push(x & gf.mask);
            }
            for &a in &values {
                assert_eq!(super::fsqr(gf, a), gf.sqr(a), "an inlined square differs from the library's");
                for &b in values.iter().take(128) {
                    assert_eq!(super::fmul(gf, a, b), gf.mul(a, b), "an inlined product differs from the library's");
                }
            }
        }
    }

    // koblitz-n83-scanorder-20261015: target-scan state order selector
    // (KIC_SCAN_ORDER), a const generic of the target scan so every arm is
    // its own monomorphized loop.
    const ORDER_LEFT_MAJOR: u8 = 0;
    const ORDER_FEISTEL: u8 = 1;

    fn scan_order_from_env() -> (u8, &'static str) {
        match std::env::var("KIC_SCAN_ORDER").as_deref() {
            Err(_) | Ok("") | Ok("left_major") => (ORDER_LEFT_MAJOR, "left_major"),
            Ok("feistel") => (ORDER_FEISTEL, "feistel"),
            Ok(other) => panic!("unknown KIC_SCAN_ORDER {other}"),
        }
    }

    fn scan_start_override_from_env() -> Option<usize> {
        match std::env::var("KIC_SCAN_START_OVERRIDE").as_deref() {
            Err(_) | Ok("") => None,
            Ok(value) => Some(value.parse().expect("KIC_SCAN_START_OVERRIDE must be a state index")),
        }
    }

    /// Keyed bijection on `[0, 2^(2·half))`: a balanced four-round Feistel
    /// network with a keyed multiply-shift round function. Any round
    /// function gives a bijection; restricting the images to `[0, len)` by
    /// skipping the others visits every state index exactly once.
    struct ScanPermutation {
        half: u32,
        mask: u64,
        keys: [u64; 4],
        domain: u64,
    }

    impl ScanPermutation {
        fn new(len: usize, key: u64) -> Self {
            let mut bits = 1u32;
            while (1u64 << bits) < len as u64 {
                bits += 1;
            }
            let half = (bits + 1) / 2;
            let mut state = key ^ 0x6A09_E667_F3BC_C908;
            let mut keys = [0u64; 4];
            for slot in keys.iter_mut() {
                // splitmix64
                state = state.wrapping_add(0x9E37_79B9_7F4A_7C15);
                let mut z = state;
                z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
                z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
                *slot = z ^ (z >> 31);
            }
            Self { half, mask: (1u64 << half) - 1, keys, domain: 1u64 << (2 * half) }
        }

        #[inline(always)]
        fn round(&self, value: u64, key: u64) -> u64 {
            ((value ^ key).wrapping_mul(0x9E37_79B9_7F4A_7C15) ^ key.rotate_left(29))
                .wrapping_mul(0xD6E8_FEB8_6659_FD93)
                >> (64 - self.half)
        }

        #[inline(always)]
        fn apply(&self, index: u64) -> u64 {
            let mut left = index >> self.half;
            let mut right = index & self.mask;
            for &key in &self.keys {
                let next = left ^ self.round(right, key);
                left = right;
                right = next & self.mask;
            }
            (left << self.half) | right
        }

        /// Inverse of `apply` (koblitz-n83-state-fold-20261015): the rounds
        /// undone in reverse key order.
        #[inline(always)]
        fn invert(&self, image: u64) -> u64 {
            let mut left = image >> self.half;
            let mut right = image & self.mask;
            for &key in self.keys.iter().rev() {
                let previous_right = left;
                let previous_left = (right ^ self.round(previous_right, key)) & self.mask;
                left = previous_left;
                right = previous_right;
            }
            (left << self.half) | right
        }
    }

    /// koblitz-n83-fieldops-20261104 (S4): `ScanPermutation::apply` read from
    /// per-round tables. `apply` calls `round(right, key)` only with
    /// right < 2^half, so table r holds `round(v, keys[r])` for every
    /// v < 2^half, filled by `round` itself, and `apply` here equals
    /// `ScanPermutation::apply` on every index.
    struct RoundTables {
        tables: [Vec<u32>; 4],
        half: u32,
        mask: u64,
    }

    impl RoundTables {
        fn new(permutation: &ScanPermutation) -> Self {
            let size = 1usize << permutation.half;
            // One table per round key, in key order (`keys: [u64; 4]`).
            let tables = permutation
                .keys
                .map(|key| (0..size).map(|value| permutation.round(value as u64, key) as u32).collect());
            Self { tables, half: permutation.half, mask: permutation.mask }
        }

        #[inline(always)]
        fn apply(&self, index: u64) -> u64 {
            let mut left = index >> self.half;
            let mut right = index & self.mask;
            for table in &self.tables {
                let next = left ^ table[right as usize] as u64;
                left = right;
                right = next & self.mask;
            }
            (left << self.half) | right
        }
    }

    /// Bijection check on the real state count: every index in `[0, len)`
    /// is produced exactly once and nothing else survives the range filter.
    fn scan_permutation_selftest(len: usize, key: u64) -> bool {
        let permutation = ScanPermutation::new(len, key);
        // koblitz-n83-fieldops-20261104 (S4): the same three checks of the
        // same function, `apply` read from the per-round tables.
        let rounds = RoundTables::new(&permutation);
        bijection_selftest_lanes(len, permutation.domain, |index| rounds.apply(index))
    }

    /// koblitz-n83-indexbuild-20261020: the parent's exhaustive check over
    /// every index of `[0, domain)`, eight images at a time: false iff some
    /// image is at least `domain`, an in-range image repeats, or the
    /// in-range images do not number `len`. Only the evaluation order
    /// differs from the parent's loop, so the verdict is the same.
    const SELFTEST_LANES: u64 = 8;

    #[inline(always)]
    fn bijection_selftest_lanes(len: usize, domain: u64, apply: impl Fn(u64) -> u64) -> bool {
        let mut seen = vec![0u64; len.div_ceil(64)];
        let mut visited = 0usize;
        let mut mark = |image: u64| -> bool {
            if image >= domain {
                return false;
            }
            if image < len as u64 {
                let (word, bit) = ((image / 64) as usize, image % 64);
                if seen[word] >> bit & 1 == 1 {
                    return false;
                }
                seen[word] |= 1 << bit;
                visited += 1;
            }
            true
        };
        let mut index = 0u64;
        while index + SELFTEST_LANES <= domain {
            let images: [u64; SELFTEST_LANES as usize] =
                std::array::from_fn(|lane| apply(index + lane as u64));
            for image in images {
                if !mark(image) {
                    return false;
                }
            }
            index += SELFTEST_LANES;
        }
        while index < domain {
            if !mark(apply(index)) {
                return false;
            }
            index += 1;
        }
        visited == len
    }

    #[cfg(test)]
    mod scan_order_tests {
        use super::*;

        #[test]
        fn feistel_order_is_a_bijection_on_every_small_length() {
            for len in 1..=2100usize {
                for key in [0u64, 1, 0xDEAD_BEEF, u64::MAX, len as u64 * 0x9E37] {
                    assert!(scan_permutation_selftest(len, key), "len {len} key {key}");
                }
            }
        }

        #[test]
        fn feistel_order_is_a_bijection_on_the_n83_k600_state_count() {
            // 600 * 600 * 83 regular states (the K600 receipts' regular_states).
            assert!(scan_permutation_selftest(29_880_000, 0x0123_4567_89AB_CDEF));
        }

        #[test]
        fn feistel_order_depends_on_the_key() {
            let a = ScanPermutation::new(29_880_000, 1);
            let b = ScanPermutation::new(29_880_000, 2);
            let differ = (0..1000u64).filter(|&i| a.apply(i) != b.apply(i)).count();
            assert!(differ > 990);
        }
    }
    use std::hint::black_box;
    use std::sync::atomic::{AtomicU64, Ordering};

    // Target canonicalizer selector (KIC_TARGET_CANON), a const generic of
    // the target scan so every arm is its own monomorphized loop.
    const CANON_FULL: u8 = 0;
    const CANON_GAP: u8 = 1;
    const CANON_LIFT: u8 = 2;
    const CANON_FULL_X2: u8 = 3;
    const CANON_VERIFY: u8 = 4;
    // koblitz-n83-combined-20261015 planted control: lift_scan's result plus
    // one discarded (black_box) full scan of the same word.
    const CANON_LIFT_PLUS_FULL: u8 = 5;
    static VERIFY_WORDS: AtomicU64 = AtomicU64::new(0);
    static VERIFY_GAP_MISMATCHES: AtomicU64 = AtomicU64::new(0);
    static VERIFY_LIFT_MISMATCHES: AtomicU64 = AtomicU64::new(0);

    fn target_canon_from_env() -> (u8, &'static str) {
        match std::env::var("KIC_TARGET_CANON").as_deref() {
            Err(_) | Ok("") | Ok("full") => (CANON_FULL, "full"),
            Ok("gap") => (CANON_GAP, "gap"),
            Ok("lift") => (CANON_LIFT, "lift"),
            Ok("full_x2") => (CANON_FULL_X2, "full_x2"),
            Ok("verify") => (CANON_VERIFY, "verify"),
            Ok("lift_plus_full") => (CANON_LIFT_PLUS_FULL, "lift_plus_full"),
            Ok(other) => panic!("unknown KIC_TARGET_CANON {other}"),
        }
    }

    /// Canonical rotation `(min_s rotl(v, s), least s)` of a partner root.
    #[inline(always)]
    fn target_canonical<const C: u8>(basis: &NormalBasis128, v: u128) -> (u128, u32) {
        oc::bump(oc::CANONICALIZATIONS, 1);
        match C {
            CANON_FULL => basis.canonical(v),
            CANON_GAP => basis.canonical_sparse(v),
            CANON_LIFT => super::lift2::lift_scan_wide(v, basis.n),
            CANON_FULL_X2 => {
                let result = basis.canonical(v);
                black_box(basis.canonical(black_box(v)));
                result
            }
            CANON_LIFT_PLUS_FULL => {
                let result = super::lift2::lift_scan_wide(v, basis.n);
                black_box(basis.canonical(black_box(v)));
                result
            }
            _ => {
                let result = basis.canonical(v);
                VERIFY_WORDS.fetch_add(1, Ordering::Relaxed);
                if basis.canonical_sparse(v) != result {
                    VERIFY_GAP_MISMATCHES.fetch_add(1, Ordering::Relaxed);
                }
                if super::lift2::lift_scan_wide(v, basis.n) != result {
                    VERIFY_LIFT_MISMATCHES.fetch_add(1, Ordering::Relaxed);
                }
                result
            }
        }
    }

    /// F2-linear map on n ≤ 128 bits applied by byte tables.
    struct Linear128 {
        tables: Vec<[u128; 256]>,
    }

    impl Linear128 {
        fn from_images(images: &[u128]) -> Self {
            let chunks = images.len().div_ceil(8);
            let mut tables = vec![[0u128; 256]; chunks];
            for (chunk, table) in tables.iter_mut().enumerate() {
                for byte in 1usize..256 {
                    let low = byte & (byte - 1);
                    let bit = chunk * 8 + byte.trailing_zeros() as usize;
                    let image = images.get(bit).copied().unwrap_or(0);
                    table[byte] = table[low] ^ image;
                }
            }
            Self { tables }
        }

        #[inline(always)]
        fn apply(&self, v: u128) -> u128 {
            // koblitz-n83-fieldops-20261104 (E2): the same eleven lookups,
            // the bytes read from the little-endian image of v.
            let bytes = v.to_le_bytes();
            let mut acc = 0u128;
            for (chunk, table) in self.tables.iter().enumerate() {
                acc ^= table[bytes[chunk] as usize];
            }
            acc
        }
    }

    struct NormalBasis128 {
        n: u32,
        mask: u128,
        to_normal: Linear128,
        to_poly: Linear128,
        sparse_canonical: bool,
    }

    impl NormalBasis128 {
        fn new(gf: &Gf2_128) -> Self {
            let n = gf.n as usize;
            let mask = (1u128 << n) - 1;
            for candidate in 2u128.. {
                let mut conjugates = Vec::with_capacity(n);
                let mut value = candidate & mask;
                for _ in 0..n {
                    conjugates.push(value);
                    value = fsqr(&gf, value);
                }
                let Some(inverse_columns) = invert_columns128(&conjugates, n) else {
                    continue;
                };
                return Self {
                    n: gf.n,
                    mask,
                    to_normal: Linear128::from_images(&inverse_columns),
                    to_poly: Linear128::from_images(&conjugates),
                    sparse_canonical: std::env::var("KIC_SPARSE_CANONICAL").as_deref() == Ok("1"),
                };
            }
            unreachable!()
        }

        #[inline(always)]
        fn rotate(&self, v: u128, k: u32) -> u128 {
            if k == 0 {
                return v;
            }
            ((v << k) | (v >> (self.n - k))) & self.mask
        }

        #[inline(always)]
        fn canonical(&self, v: u128) -> (u128, u32) {
            let mut best = v;
            let mut best_shift = 0;
            let mut current = v;
            for shift in 1..self.n {
                current = ((current << 1) | (current >> (self.n - 1))) & self.mask;
                if current < best {
                    best = current;
                    best_shift = shift;
                }
            }
            (best, best_shift)
        }

        /// Wide-word analogue of the exact cyclic zero-gap selector.
        #[inline(always)]
        fn canonical_sparse(&self, v: u128) -> (u128, u32) {
            let value = v & self.mask;
            if value == 0 || value == self.mask {
                return (value, 0);
            }

            let n = self.n as usize;
            let zeros = (!value) & self.mask;
            let mut zero_runs = [0u128; 7];
            zero_runs[0] = zeros;
            for level in 1..zero_runs.len() {
                let previous_length = 1usize << (level - 1);
                if previous_length >= n {
                    zero_runs[level] = 0;
                    continue;
                }
                zero_runs[level] = zero_runs[level - 1]
                    & self.rotate(zero_runs[level - 1], previous_length as u32);
            }

            let mut longest_gap = 0usize;
            let mut starts = self.mask;
            for level in (0..zero_runs.len()).rev() {
                let length = 1usize << level;
                if longest_gap + length >= n {
                    continue;
                }
                let eligible = starts & self.rotate(zero_runs[level], longest_gap as u32);
                if eligible != 0 {
                    starts = eligible;
                    longest_gap += length;
                }
            }

            let mut best_value = u128::MAX;
            let mut best_shift = u32::MAX;
            while starts != 0 {
                let start = starts.trailing_zeros() as usize;
                starts &= starts - 1;
                let shift = (n - 1 - start) as u32;
                let rotated = self.rotate(value, shift);
                if rotated < best_value || (rotated == best_value && shift < best_shift) {
                    best_value = rotated;
                    best_shift = shift;
                }
            }
            (best_value, best_shift)
        }

        #[inline(always)]
        fn canonical_selected(&self, v: u128) -> (u128, u32) {
            if self.sparse_canonical {
                self.canonical_sparse(v)
            } else {
                self.canonical(v)
            }
        }
    }

    /// Same Gauss-Jordan as the twin, with rows as `(m, i)` word pairs.
    fn invert_columns128(columns: &[u128], n: usize) -> Option<Vec<u128>> {
        let mut rows: Vec<(u128, u128)> = (0..n)
            .map(|r| {
                let mut m = 0u128;
                for (i, &column) in columns.iter().enumerate() {
                    if (column >> r) & 1 == 1 {
                        m |= 1u128 << i;
                    }
                }
                (m, 1u128 << r)
            })
            .collect();
        for pivot in 0..n {
            let found = (pivot..n).find(|&r| (rows[r].0 >> pivot) & 1 == 1)?;
            rows.swap(pivot, found);
            for r in 0..n {
                if r != pivot && (rows[r].0 >> pivot) & 1 == 1 {
                    rows[r].0 ^= rows[pivot].0;
                    rows[r].1 ^= rows[pivot].1;
                }
            }
        }
        let mut images = vec![0u128; n];
        for (i, &(_, ih)) in rows.iter().enumerate() {
            for r in 0..n {
                if (ih >> r) & 1 == 1 {
                    images[r] |= 1u128 << i;
                }
            }
        }
        Some(images)
    }

    /// Table-driven S3 root solver on wide words.
    struct S3Solver128 {
        square: Linear128,
        half_trace: Linear128,
        trace_mask: u128,
        b: u128,
    }

    impl S3Solver128 {
        fn new(gf: &Gf2_128, b: u128) -> Self {
            let n = gf.n as usize;
            assert!(n % 2 == 1, "half-trace solver needs odd n");
            let unit: Vec<u128> = (0..n).map(|bit| 1u128 << bit).collect();
            let half_trace_images: Vec<u128> = unit
                .iter()
                .map(|&e| {
                    let mut acc = e;
                    let mut power = e;
                    for _ in 0..(n - 1) / 2 {
                        power = fsqr(&gf, fsqr(&gf, power));
                        acc ^= power;
                    }
                    acc
                })
                .collect();
            let mut trace_mask = 0u128;
            for (bit, &e) in unit.iter().enumerate() {
                let mut acc = e;
                let mut power = e;
                for _ in 1..n {
                    power = fsqr(&gf, power);
                    acc ^= power;
                }
                if acc & 1 == 1 {
                    trace_mask |= 1u128 << bit;
                }
            }
            Self {
                square: Linear128::from_images(
                    &unit.iter().map(|&e| fsqr(&gf, e)).collect::<Vec<_>>(),
                ),
                half_trace: Linear128::from_images(&half_trace_images),
                trace_mask,
                b,
            }
        }

        /// Everything before the inversion: `a = (left + right)^2`,
        /// `p = left·right`, `ps = p^2`, and the denominator `a·ps`.
        #[inline(always)]
        fn prepare(&self, gf: &Gf2_128, left: u128, right: u128) -> PreparedRoot128 {
            let a = self.square.apply(left ^ right);
            let p = fmul(&gf, left, right);
            let ps = self.square.apply(p);
            let denominator = if a == 0 || ps == 0 { 0 } else { fmul(&gf, a, ps) };
            oc::bump(oc::S3_SOLVES, 1);
            oc::bump(oc::FIELD_SQR, 2);
            PreparedRoot128 {
                left,
                right,
                a,
                p,
                ps,
                denominator,
            }
        }

        /// Everything after the inversion, given `inverse = denominator^{-1}`.
        #[inline(always)]
        fn finish(
            &self,
            gf: &Gf2_128,
            prepared: PreparedRoot128,
            inverse: u128,
        ) -> Option<[u128; 2]> {
            if prepared.denominator == 0 {
                return s3_x_roots_128_counted(gf, self.b, prepared.left, prepared.right);
            }
            let q = fmul(&gf, prepared.p, fmul(&gf, prepared.ps, inverse));
            let c = prepared.ps ^ self.b;
            let d = fmul(&gf, fmul(&gf, c, prepared.a), fmul(&gf, prepared.a, inverse));
            if (d & self.trace_mask).count_ones() & 1 == 1 {
                return None;
            }
            oc::bump(oc::FIELD_HALF_TRACE, 1);
            let first = fmul(&gf, q, self.half_trace.apply(d));
            Some([first, first ^ q])
        }

        /// Scalar form: one inversion per call, same root order as the
        /// batched form.
        #[inline(always)]
        fn roots(
            &self,
            gf: &Gf2_128,
            basis: &NormalBasis128,
            left: u128,
            right: u128,
        ) -> Option<[u128; 2]> {
            let prepared = self.prepare(gf, left, right);
            let inverse = if prepared.denominator == 0 {
                0
            } else {
                invert128(gf, basis, prepared.denominator)
            };
            self.finish(gf, prepared, inverse)
        }
    }

    #[derive(Clone, Copy)]
    struct PreparedRoot128 {
        left: u128,
        right: u128,
        a: u128,
        p: u128,
        ps: u128,
        denominator: u128,
    }

    /// Reusable scratch for solving many S3 root pairs with one shared
    /// inversion (Montgomery's trick over the non-exceptional
    /// denominators).
    struct RootBatch128 {
        prepared: Vec<PreparedRoot128>,
        inverses: Vec<u128>,
        prefixes: Vec<u128>,
        regular: Vec<usize>,
        results: Vec<Option<[u128; 2]>>,
    }

    impl RootBatch128 {
        fn with_capacity(entries: usize) -> Self {
            Self {
                prepared: Vec::with_capacity(entries),
                inverses: Vec::with_capacity(entries),
                prefixes: Vec::with_capacity(entries),
                regular: Vec::with_capacity(entries),
                results: Vec::with_capacity(entries),
            }
        }

        fn solve(
            &mut self,
            gf: &Gf2_128,
            basis: &NormalBasis128,
            solver: &S3Solver128,
            inputs: &[(u128, u128)],
        ) {
            self.prepared.clear();
            self.inverses.clear();
            self.prefixes.clear();
            self.regular.clear();
            self.results.clear();
            self.inverses.resize(inputs.len(), 0);
            self.prefixes.resize(inputs.len(), 0);
            for (index, &(left, right)) in inputs.iter().enumerate() {
                let prepared = solver.prepare(gf, left, right);
                if prepared.denominator != 0 {
                    self.regular.push(index);
                }
                self.prepared.push(prepared);
            }
            if !self.regular.is_empty() {
                let mut product = 1u128;
                for &index in &self.regular {
                    self.prefixes[index] = product;
                    product = fmul(&gf, product, self.prepared[index].denominator);
                }
                // A product of non-zero field elements is non-zero.
                let mut inverse_product = invert128(gf, basis, product);
                for &index in self.regular.iter().rev() {
                    self.inverses[index] = fmul(&gf, inverse_product, self.prefixes[index]);
                    inverse_product = fmul(&gf, inverse_product, self.prepared[index].denominator);
                }
            }
            for (prepared, &inverse) in self.prepared.iter().zip(&self.inverses) {
                self.results.push(solver.finish(gf, *prepared, inverse));
            }
        }
    }

    #[inline(always)]
    fn invert128(gf: &Gf2_128, basis: &NormalBasis128, a: u128) -> u128 {
        oc::bump(oc::FIELD_INV, 1);
        let _inversion = oc::InversionScope::new();
        let e = gf.n - 1;
        let mut c = a;
        let mut k = 1u32;
        let bits = 32 - e.leading_zeros();
        for i in (0..bits - 1).rev() {
            let raised = basis
                .to_poly
                .apply(basis.rotate(basis.to_normal.apply(c), k));
            c = fmul(&gf, c, raised);
            k *= 2;
            if (e >> i) & 1 == 1 {
                c = fmul(&gf, fsqr(&gf, c), a);
                k += 1;
            }
        }
        fsqr(&gf, c)
    }

    /// Open-addressing `u128 -> u64` table; `u128::MAX` marks empty.
    /// Prefilter is the frozen wide example's two-word Bloom.
    struct RootBloom128 {
        words: Vec<u64>,
        bit_mask: usize,
    }

    impl RootBloom128 {
        const HASHES: usize = 3;

        fn with_capacity(keys: usize) -> Self {
            let bits = keys
                .checked_mul(8)
                .and_then(usize::checked_next_power_of_two)
                .expect("root Bloom size overflow")
                .max(64);
            Self {
                words: vec![0; bits / 64],
                bit_mask: bits - 1,
            }
        }

        #[inline(always)]
        fn hash_pair(key: u128) -> (u64, u64) {
            let low = key as u64;
            let high = (key >> 64) as u64;
            (
                mix_root_bloom(low ^ high.rotate_left(23) ^ 0xA5A5_38F9_9328_6F3D),
                mix_root_bloom(high ^ low.rotate_left(17) ^ 0xD4C9_3E72_B719_485B) | 1,
            )
        }

        #[inline(always)]
        fn insert(&mut self, key: u128) {
            let (first, step) = Self::hash_pair(key);
            for index in 0..Self::HASHES {
                let bit =
                    first.wrapping_add((index as u64).wrapping_mul(step)) as usize & self.bit_mask;
                self.words[bit >> 6] |= 1u64 << (bit & 63);
            }
        }

        #[inline(always)]
        fn contains(&self, key: u128) -> bool {
            let (first, step) = Self::hash_pair(key);
            for index in 0..Self::HASHES {
                let bit =
                    first.wrapping_add((index as u64).wrapping_mul(step)) as usize & self.bit_mask;
                if self.words[bit >> 6] & (1u64 << (bit & 63)) == 0 {
                    return false;
                }
            }
            true
        }

        fn bytes(&self) -> usize {
            self.words.len() * std::mem::size_of::<u64>()
        }
    }

    /// Open-addressing `u128 -> u64` table; `u128::MAX` marks empty.
    struct RootTable128 {
        slots: Vec<(u128, u64)>,
        shift: u32,
        len: usize,
        bloom: Option<RootBloom128>,
    }

    impl RootTable128 {
        fn with_capacity(entries: usize) -> Self {
            let slots = (entries * 2).next_power_of_two().max(16);
            Self {
                slots: vec![(u128::MAX, 0); slots],
                shift: 128 - slots.trailing_zeros(),
                len: 0,
                bloom: (std::env::var("KIC_ROOT_BLOOM").as_deref() == Ok("1"))
                    .then(|| RootBloom128::with_capacity(entries)),
            }
        }

        #[inline(always)]
        fn slot(&self, key: u128) -> usize {
            (key.wrapping_mul(0x9E37_79B9_7F4A_7C15_9E37_79B9_7F4A_7C15) >> self.shift) as usize
        }

        fn insert_if_absent(&mut self, key: u128, value: u64) {
            oc::bump(oc::ROOT_INSERTS, 1);
            let mask = self.slots.len() - 1;
            let mut slot = self.slot(key);
            loop {
                if self.slots[slot].0 == u128::MAX {
                    self.slots[slot] = (key, value);
                    self.len += 1;
                    if let Some(bloom) = &mut self.bloom {
                        bloom.insert(key);
                    }
                    return;
                }
                if self.slots[slot].0 == key {
                    return;
                }
                slot = (slot + 1) & mask;
            }
        }

        #[inline(always)]
        fn get(&self, key: u128) -> Option<u64> {
            oc::bump(oc::ROOT_PROBES, 1);
            if self
                .bloom
                .as_ref()
                .is_some_and(|bloom| !bloom.contains(key))
            {
                return None;
            }
            let mask = self.slots.len() - 1;
            let mut slot = self.slot(key);
            loop {
                let (stored, value) = self.slots[slot];
                if stored == key {
                    return Some(value);
                }
                if stored == u128::MAX {
                    return None;
                }
                slot = (slot + 1) & mask;
            }
        }
    }

    // koblitz-n83-tablefilter-20261015: root-table layout selector
    // (KIC_ROOT_TABLE), read once when the index is built.
    const TABLE_BASE: u8 = 0;
    const TABLE_COMPACT: u8 = 1;
    const TABLE_FILTER: u8 = 2;
    const TABLE_FILTER_PLANT: u8 = 3;
    const TABLE_NAMES: [&str; 4] = ["base", "compact", "filter", "filter_plant"];

    fn root_table_from_env() -> u8 {
        match std::env::var("KIC_ROOT_TABLE").as_deref() {
            Err(_) | Ok("") | Ok("base") => TABLE_BASE,
            Ok("compact") => TABLE_COMPACT,
            Ok("filter") => TABLE_FILTER,
            Ok("filter_plant") => TABLE_FILTER_PLANT,
            Ok(other) => panic!("unknown KIC_ROOT_TABLE {other}"),
        }
    }

    const ROOT_FILTER_DEFAULT_LOG2_BITS: u32 = 28;

    fn root_filter_log2_bits_from_env() -> u32 {
        match std::env::var("KIC_ROOT_FILTER_LOG2_BITS").as_deref() {
            Err(_) | Ok("") => ROOT_FILTER_DEFAULT_LOG2_BITS,
            Ok(value) => {
                let bits: u32 = value.parse().expect("KIC_ROOT_FILTER_LOG2_BITS must be an integer");
                assert!((12..=34).contains(&bits), "KIC_ROOT_FILTER_LOG2_BITS out of range");
                bits
            }
        }
    }

    /// Hint the cache line at `address`. A prefetch never faults and changes
    /// no architectural state.
    #[inline(always)]
    fn prefetch_address<T>(address: *const T) {
        #[cfg(target_arch = "x86_64")]
        {
            // SAFETY: `_mm_prefetch` is a hint; it does not dereference
            // `address` architecturally and cannot fault. SSE is part of
            // the x86_64 baseline.
            #[allow(unused_unsafe)]
            unsafe {
                std::arch::x86_64::_mm_prefetch(address as *const i8, std::arch::x86_64::_MM_HINT_T0);
            }
        }
        #[cfg(not(target_arch = "x86_64"))]
        {
            let _ = address;
        }
    }

    const COMPACT_KEY_BITS: u32 = 83;
    const COMPACT_KEY_MASK: u128 = (1u128 << COMPACT_KEY_BITS) - 1;
    const COMPACT_FIELD_BITS: u32 = 11;
    const COMPACT_OCCUPIED: u128 = 1u128 << 127;

    /// Exact open-addressing `u128 -> u64` root table with one 16-byte word
    /// per slot: bits 0..83 hold the key (an 83-bit normal-basis word),
    /// bits 83..127 the four `pack` fields in 11 bits each, bit 127 marks
    /// an occupied slot; 0 is empty. Same capacity rule, hash and
    /// linear-probe sequence as `RootTable128`, so the same key -> value
    /// map in half the bytes. Out-of-range keys or fields panic on insert.
    struct CompactRootTable128 {
        slots: Vec<u128>,
        shift: u32,
        len: usize,
    }

    impl CompactRootTable128 {
        fn with_capacity(entries: usize) -> Self {
            let slots = (entries * 2).next_power_of_two().max(16);
            Self {
                slots: vec![0; slots],
                shift: 128 - slots.trailing_zeros(),
                len: 0,
            }
        }

        #[inline(always)]
        fn slot(&self, key: u128) -> usize {
            (key.wrapping_mul(0x9E37_79B9_7F4A_7C15_9E37_79B9_7F4A_7C15) >> self.shift) as usize
        }

        fn compress(value: u64) -> u128 {
            let mut packed = 0u128;
            for field in 0..4 {
                let part = (value >> (16 * field)) & 0xffff;
                assert!(part < 1 << COMPACT_FIELD_BITS, "compact root slot field overflow");
                packed |= (part as u128) << (COMPACT_KEY_BITS + COMPACT_FIELD_BITS * field);
            }
            packed
        }

        #[inline(always)]
        fn expand(word: u128) -> u64 {
            let mut value = 0u64;
            for field in 0..4 {
                let part = (word >> (COMPACT_KEY_BITS + COMPACT_FIELD_BITS * field)) as u64
                    & ((1u64 << COMPACT_FIELD_BITS) - 1);
                value |= part << (16 * field);
            }
            value
        }

        fn insert_if_absent(&mut self, key: u128, value: u64) {
            oc::bump(oc::ROOT_INSERTS, 1);
            assert!(key <= COMPACT_KEY_MASK, "compact root slot key exceeds 83 bits");
            let word = COMPACT_OCCUPIED | Self::compress(value) | key;
            debug_assert_eq!(Self::expand(word), value);
            let mask = self.slots.len() - 1;
            let mut slot = self.slot(key);
            loop {
                let stored = self.slots[slot];
                if stored == 0 {
                    self.slots[slot] = word;
                    self.len += 1;
                    return;
                }
                if stored & COMPACT_KEY_MASK == key {
                    return;
                }
                slot = (slot + 1) & mask;
            }
        }

        #[inline(always)]
        fn get(&self, key: u128) -> Option<u64> {
            oc::bump(oc::ROOT_PROBES, 1);
            if key > COMPACT_KEY_MASK {
                // Never inserted (insert asserts the width).
                return None;
            }
            let mask = self.slots.len() - 1;
            let mut slot = self.slot(key);
            loop {
                let stored = self.slots[slot];
                if stored == 0 {
                    return None;
                }
                if stored & COMPACT_KEY_MASK == key {
                    return Some(Self::expand(stored));
                }
                slot = (slot + 1) & mask;
            }
        }

        #[inline(always)]
        fn prefetch(&self, key: u128) {
            prefetch_address(self.slots.as_ptr().wrapping_add(self.slot(key)));
        }

        fn bytes(&self) -> usize {
            self.slots.len() * std::mem::size_of::<u128>()
        }
    }

    const ROOT_FILTER_HASHES: u32 = 5;

    /// Register-blocked Bloom filter over the root-table keys: one 64-bit
    /// word per key, chosen by the top bits of a 64-bit hash, with
    /// `ROOT_FILTER_HASHES` bits from its low 6-bit groups. No false
    /// negatives: every inserted key tests positive.
    struct RootFilter128 {
        words: Vec<u64>,
        word_shift: u32,
        log2_bits: u32,
    }

    impl RootFilter128 {
        fn new(log2_bits: u32) -> Self {
            let log2_words = log2_bits - 6;
            assert!(log2_words + 6 * ROOT_FILTER_HASHES <= 64, "root filter hash bits overlap");
            Self {
                words: vec![0; 1usize << log2_words],
                word_shift: 64 - log2_words,
                log2_bits,
            }
        }

        #[inline(always)]
        fn hash(key: u128) -> u64 {
            mix_root_bloom(key as u64 ^ mix_root_bloom((key >> 64) as u64 ^ 0x2545_F491_4F6C_DD1D))
        }

        #[inline(always)]
        fn locate(&self, key: u128) -> (usize, u64) {
            let hash = Self::hash(key);
            let mut mask = 0u64;
            for index in 0..ROOT_FILTER_HASHES {
                mask |= 1u64 << ((hash >> (6 * index)) & 63);
            }
            ((hash >> self.word_shift) as usize, mask)
        }

        fn insert(&mut self, key: u128) {
            oc::bump(oc::FILTER_INSERTS, 1);
            let (word, mask) = self.locate(key);
            self.words[word] |= mask;
        }

        #[inline(always)]
        fn contains(&self, key: u128) -> bool {
            oc::bump(oc::FILTER_QUERIES, 1);
            let (word, mask) = self.locate(key);
            self.words[word] & mask == mask
        }

        #[inline(always)]
        fn prefetch(&self, key: u128) {
            let word = (Self::hash(key) >> self.word_shift) as usize;
            prefetch_address(self.words.as_ptr().wrapping_add(word));
        }

        fn bytes(&self) -> usize {
            self.words.len() * std::mem::size_of::<u64>()
        }

        fn ones_fraction(&self) -> f64 {
            let ones: u64 = self.words.iter().map(|word| word.count_ones() as u64).sum();
            ones as f64 / (self.words.len() as f64 * 64.0)
        }
    }

    struct State128 {
        left: u16,
        right: u16,
        relative: u16,
        normal_roots: [u128; 2],
    }

    struct Index128 {
        states: Vec<State128>,
        table: RootTable128,
        shifted: Vec<Vec<u128>>,
        root_table: u8,
        compact: Option<CompactRootTable128>,
        filter: Option<RootFilter128>,
        filter_build_ms: f64,
        // koblitz-n83-stacked-20261016 (from the state fold): the unfolded
        // state count, and the fold map when the index stores one state per
        // unordered class.
        logical_states: usize,
        fold: Option<Fold128>,
    }

    impl Index128 {
        /// Distinct root keys stored, in whichever layout this index uses.
        fn root_entries(&self) -> usize {
            self.compact.as_ref().map_or(self.table.len, |compact| compact.len)
        }

        fn root_table_bytes(&self) -> usize {
            self.compact.as_ref().map_or(
                self.table.slots.len() * std::mem::size_of::<(u128, u64)>(),
                CompactRootTable128::bytes,
            )
        }
    }

    struct Relation128 {
        point_indices: [usize; 4],
        x_codes: [u128; 4],
        intermediates: [u128; 2],
        probes: u64,
    }

    #[derive(Clone, Copy)]
    enum TargetInput128 {
        PublicPoint(FastPoint128),
        KnownAnswerScalar(u64),
    }

    // serde_json's default Number representation cannot emit arbitrary
    // u128 field elements, so every wide field coordinate is a decimal
    // string on the wire.
    fn encode_point128(point: FastPoint128) -> Option<[String; 2]> {
        point.map(|(x, y)| [x.to_string(), y.to_string()])
    }

    fn encode_pair128(point: Option<[u128; 2]>) -> Option<[String; 2]> {
        point.map(|[x, y]| [x.to_string(), y.to_string()])
    }

    fn decode_word128(value: &Value) -> u128 {
        if let Some(decimal) = value.as_str() {
            decimal
                .parse()
                .expect("wide field coordinate must be decimal")
        } else if let Some(word) = value.as_u64() {
            word as u128
        } else {
            panic!("wide field coordinate must be a decimal string or u64")
        }
    }

    /// Parse a `[x, y]` target line directly from decimal text: JSON
    /// numbers beyond `u64` lose precision in `serde_json::Value`, so wide
    /// coordinates are read from the raw line (integers or quoted strings).
    fn parse_wide_pair_line(line: &str) -> [u128; 2] {
        let inner = line.trim().trim_start_matches('[').trim_end_matches(']');
        let mut words = inner.split(',');
        let parse = |raw: &str| -> u128 {
            raw.trim().trim_matches('"').parse().expect(
                "wide field coordinate must be a decimal integer or string",
            )
        };
        let x = parse(words.next().expect("wide point needs two coordinates"));
        let y = parse(words.next().expect("wide point needs two coordinates"));
        assert!(words.next().is_none(), "wide point must have two coordinates");
        [x, y]
    }

    fn decode_pair128(value: &Value) -> Option<[u128; 2]> {
        if value.is_null() {
            return None;
        }
        let pair = value.as_array().expect("wide point must be a [x,y] array");
        assert_eq!(pair.len(), 2, "wide point must have two coordinates");
        Some([decode_word128(&pair[0]), decode_word128(&pair[1])])
    }

    fn decode_point_list128(value: &Value) -> Vec<Option<[u128; 2]>> {
        value
            .as_array()
            .expect("wide point list must be an array")
            .iter()
            .map(decode_pair128)
            .collect()
    }

    struct Base128 {
        points: Vec<FastPoint128>,
        labels: Vec<(usize, u64)>,
        by_x: HashMap<u128, Vec<usize>>,
        columns: usize,
    }

    fn build_index128(
        gf: &Gf2_128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        reps: &[u128],
        mode: IndexMode128,
    ) -> Index128 {
        build_index128_stacked(
            gf,
            basis,
            solver,
            reps,
            root_table_from_env(),
            root_filter_log2_bits_from_env(),
            mode,
        )
    }

    #[allow(dead_code)]
    fn build_index128_mode(
        gf: &Gf2_128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        reps: &[u128],
        root_table: u8,
        filter_log2_bits: u32,
    ) -> Index128 {
        build_index128_stacked(
            gf,
            basis,
            solver,
            reps,
            root_table,
            filter_log2_bits,
            IndexMode128::UNFOLDED,
        )
    }

    fn build_index128_stacked(
        gf: &Gf2_128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        reps: &[u128],
        root_table: u8,
        filter_log2_bits: u32,
        mode: IndexMode128,
    ) -> Index128 {
        let n = gf.n as usize;
        let shifted: Vec<Vec<u128>> = reps
            .iter()
            .map(|&code| {
                let mut row = Vec::with_capacity(n);
                let mut value = code;
                for _ in 0..n {
                    row.push(value);
                    value = fsqr(&gf, value);
                }
                oc::bump(oc::FROBENIUS_X, n as u64);
                row
            })
            .collect();
        let fold = mode.fold.then(|| Fold128::new(reps.len(), n, mode.plant));
        let mut states = Vec::new();
        if let Some(fold) = &fold {
            states = folded_states128(gf, basis, solver, &shifted, fold, mode);
        } else {
        for left in 0..reps.len() {
            for right in 0..reps.len() {
                for relative in 0..n {
                    if let Some(roots) =
                        solver.roots(gf, basis, shifted[left][0], shifted[right][relative])
                    {
                        states.push(State128 {
                            left: left as u16,
                            right: right as u16,
                            relative: relative as u16,
                            normal_roots: [
                                basis.to_normal.apply(roots[0]),
                                basis.to_normal.apply(roots[1]),
                            ],
                        });
                    }
                }
            }
        }
        }
        let mut table = RootTable128::with_capacity(if root_table == TABLE_BASE {
            states.len() * 2
        } else {
            0
        });
        let mut compact = None;
        let mut filter = None;
        let mut filter_build_ms = 0.0;
        if root_table == TABLE_BASE {
            for state in &states {
                for &root in &state.normal_roots {
                    let (canonical, shift) = index_canonical128(basis, mode.canon, root);
                    table.insert_if_absent(
                        canonical,
                        pack(state.left, state.right, state.relative, shift),
                    );
                }
            }
        } else {
            // The same inserts, in the same order, into the 16-byte layout.
            // koblitz-n83-indexbuild-20261020: roots canonicalized ahead and
            // their home slots prefetched while root i is inserted.
            // koblitz-n83-indexbuild2-20261020 (C7): the keys of roots
            // [ready, ready + 8) are computed together (index_keys8, the
            // parent's keys) whenever at most INDEX_BUILD_LOOKAHEAD keys are
            // ready ahead of root i; every root is canonicalized once, in
            // increasing root order, and the ring holds at most 40 live keys.
            let mut slots = CompactRootTable128::with_capacity(states.len() * 2);
            let total = states.len() * 2;
            let root_at = |i: usize| states[i >> 1].normal_roots[i & 1];
            let mut ring = [(0u128, 0u32); INDEX_BUILD_RING];
            let mut ready = 0usize;
            let fill = |ring: &mut [(u128, u32); INDEX_BUILD_RING], slots: &CompactRootTable128, ready: &mut usize| {
                let start = *ready;
                if start + INDEX_BUILD_LANES <= total {
                    let words: [u128; INDEX_BUILD_LANES] = std::array::from_fn(|lane| root_at(start + lane));
                    let keys = index_keys8(basis, mode.canon, &words);
                    for (lane, key) in keys.into_iter().enumerate() {
                        slots.prefetch(key.0);
                        ring[(start + lane) % INDEX_BUILD_RING] = key;
                    }
                    *ready = start + INDEX_BUILD_LANES;
                } else {
                    for i in start..total {
                        let key = index_canonical128(basis, mode.canon, root_at(i));
                        slots.prefetch(key.0);
                        ring[i % INDEX_BUILD_RING] = key;
                    }
                    *ready = total;
                }
            };
            while ready < INDEX_BUILD_LOOKAHEAD.min(total) {
                fill(&mut ring, &slots, &mut ready);
            }
            for i in 0..total {
                if ready < total && ready <= i + INDEX_BUILD_LOOKAHEAD {
                    fill(&mut ring, &slots, &mut ready);
                }
                let (canonical, shift) = ring[i % INDEX_BUILD_RING];
                let state = &states[i >> 1];
                slots.insert_if_absent(
                    canonical,
                    pack(state.left, state.right, state.relative, shift),
                );
            }
            if root_table != TABLE_COMPACT {
                let filter_started = Instant::now();
                let mut bloom = RootFilter128::new(filter_log2_bits);
                for &word in &slots.slots {
                    if word != 0 {
                        bloom.insert(word & COMPACT_KEY_MASK);
                    }
                }
                filter_build_ms = ms(filter_started.elapsed());
                filter = Some(bloom);
            }
            compact = Some(slots);
        }
        Index128 {
            logical_states: fold.as_ref().map_or(states.len(), Fold128::logical),
            states,
            table,
            shifted,
            root_table,
            compact,
            filter,
            filter_build_ms,
            fold,
        }
    }

    // ── koblitz-n83-stacked-20261016: the folded root index on every layout ──
    //
    // From koblitz-n83-state-fold-20261015 (FOLD_CODE): state (l, r, rel)
    // holds the roots x(A ± τ^rel B) of S3(x(A), x(τ^rel B), X), A = reps[l],
    // B = reps[r]. Its mate (r, l, (n - rel) % n) holds x(B ± τ^-rel A) =
    // Frob^-rel of the same roots, in the same root order, so over all n shifts
    // it makes exactly the representative's probes with the first two codes
    // swapped. The fold stores l < r, or l == r with 2·rel ≤ n. The only
    // change here: the folded scan calls the layout's probe loop
    // (`scan_state128_select::<C, P>`) instead of `scan_state128::<C>`.
    // koblitz-n83-indexbuild2-20261020: keys computed eight roots at a time
    // into a ring of 64 (at most 40 are live).
    const INDEX_BUILD_LANES: usize = 8;
    // koblitz-n83-rankfinder-20261021: the rank stage's probe keys are
    // canonicalized eight at a time (lift_linear_lanes8).
    const RANK_PROBE_LANES: usize = INDEX_BUILD_LANES;
    const INDEX_BUILD_RING: usize = 64;
    // koblitz-n83-indexbuild-20261020: roots canonicalized ahead of the insert.
    const INDEX_BUILD_LOOKAHEAD: usize = 32;
    const INDEX_CANON_SELECTED: u8 = 0;
    const INDEX_CANON_LIFT: u8 = 1;
    // koblitz-n83-indexlift-20261019: lift_scan keys, each checked against
    // the selected canonicalizer (planted positive control).
    const INDEX_CANON_LIFT_PLANT: u8 = 2;
    static INDEX_PLANT_CHECKED: AtomicU64 = AtomicU64::new(0);
    static FOLD_AUDIT_PROBES: AtomicU64 = AtomicU64::new(0);

    #[derive(Clone, Copy)]
    struct IndexMode128 {
        fold: bool,
        plant: bool,
        canon: u8,
    }

    impl IndexMode128 {
        const UNFOLDED: Self = Self { fold: false, plant: false, canon: INDEX_CANON_SELECTED };
    }

    fn index_mode_from_env() -> (IndexMode128, &'static str) {
        let fold = match std::env::var("KIC_STATE_FOLD").as_deref() {
            Err(_) | Ok("") | Ok("0") => false,
            Ok("1") => true,
            Ok(other) => panic!("unknown KIC_STATE_FOLD {other}"),
        };
        let plant = match std::env::var("KIC_FOLD_PLANT").as_deref() {
            Err(_) | Ok("") | Ok("0") => false,
            Ok("1") => true,
            Ok(other) => panic!("unknown KIC_FOLD_PLANT {other}"),
        };
        let (canon, canon_name) = match std::env::var("KIC_INDEX_CANON").as_deref() {
            Err(_) | Ok("") | Ok("selected") => (INDEX_CANON_SELECTED, "selected"),
            Ok("lift") => (INDEX_CANON_LIFT, "lift"),
            Ok("lift_plant") => (INDEX_CANON_LIFT_PLANT, "lift_plant"),
            Ok(other) => panic!("unknown KIC_INDEX_CANON {other}"),
        };
        assert!(fold || (!plant && canon == INDEX_CANON_SELECTED),
                "KIC_FOLD_PLANT and KIC_INDEX_CANON need KIC_STATE_FOLD=1");
        (IndexMode128 { fold, plant, canon }, canon_name)
    }

    /// The rank stage's canonicalizer, state order and probe loop.
    fn rank_selectors_from_env() -> (&'static str, &'static str, &'static str) {
        let canon = match std::env::var("KIC_RANK_CANON").as_deref() {
            Err(_) | Ok("") | Ok("full") => "full",
            Ok("lift") => "lift",
            Ok(other) => panic!("unknown KIC_RANK_CANON {other}"),
        };
        let order = match std::env::var("KIC_RANK_ORDER").as_deref() {
            Err(_) | Ok("") | Ok("left_major") => "left_major",
            Ok("feistel") => "feistel",
            Ok(other) => panic!("unknown KIC_RANK_ORDER {other}"),
        };
        let probe = match std::env::var("KIC_RANK_PROBE").as_deref() {
            Err(_) | Ok("") | Ok("off") => "off",
            Ok("target") => "target",
            Ok(other) => panic!("unknown KIC_RANK_PROBE {other}"),
        };
        assert!(probe == "off" || (canon == "lift" && order == "feistel"),
                "KIC_RANK_PROBE=target runs with KIC_RANK_CANON=lift and KIC_RANK_ORDER=feistel");
        (canon, order, probe)
    }

    // ── koblitz-n83-indexbuild2-20261020: C7, the linear run finder ──
    //
    // The least rotation of an N-bit word in lift_scan's convention (bit i is
    // normal-basis coefficient i, rotl(x, s) = ((x << s) | (x >> (N - s))) &
    // mask, the canonical form is (min_s rotl(x, s), least such s); 0 and the
    // all-ones word give shift 0). For a nonconstant word, z_1 = !x and
    // z_(j+1) = z_j & rotl(z_j, 1): bit p of z_j is set iff bits p, p-1, ...,
    // p-j+1 are zero (cyclically). The last nonzero z_j is Z_L, L the longest
    // zero run (1 <= L <= N - 1), the tops of all longest runs: the run set
    // lift_scan's greedy lifting ends with. Every top p gives the candidate
    // s = N - 1 - p; the least rotation wins, ties to the smaller shift.

    const fn word_mask(bits: u32) -> u128 {
        (1u128 << bits) - 1
    }

    #[inline(always)]
    fn rotl_word<const N: u32>(v: u128, s: u32) -> u128 {
        if s == 0 {
            v
        } else {
            ((v << s) | (v >> (N - s))) & word_mask(N)
        }
    }

    /// lift_scan's candidate loop over the run tops `tops` of a nonconstant word.
    #[inline(always)]
    fn least_rotation_from_tops<const N: u32>(v: u128, mut tops: u128) -> (u128, u32) {
        let mut best = word_mask(N);
        let mut best_shift = 0u32;
        while tops != 0 {
            let p = tops.trailing_zeros();
            tops &= tops - 1;
            let s = N - 1 - p;
            let rotated = rotl_word::<N>(v, s);
            if rotated < best || (rotated == best && s < best_shift) {
                best = rotated;
                best_shift = s;
            }
        }
        (best, best_shift)
    }

    /// The scalar form (the lanes' reference in `indexbuild2_tests`).
    #[allow(dead_code)]
    #[inline(always)]
    fn lift_linear<const N: u32>(v: u128) -> (u128, u32) {
        if v == 0 || v == word_mask(N) {
            return (v, 0);
        }
        let mut z = !v & word_mask(N);
        loop {
            let next = z & rotl_word::<N>(z, 1);
            if next == 0 {
                break;
            }
            z = next;
        }
        least_rotation_from_tops::<N>(v, z)
    }

    /// `lift_linear` on eight words in lock step: a lane whose next step is
    /// zero keeps its Z_L (a select, no jump); the loop ends when every
    /// lane's next step is zero. The word 0 starts at z = 0 (no runs to
    /// lift) and, like the all-ones word, returns shift 0.
    #[inline(always)]
    fn lift_linear_lanes8<const N: u32>(words: &[u128; INDEX_BUILD_LANES]) -> [(u128, u32); INDEX_BUILD_LANES] {
        oc::bump(oc::CANONICALIZATIONS, INDEX_BUILD_LANES as u64);
        let mut z: [u128; INDEX_BUILD_LANES] =
            std::array::from_fn(|lane| if words[lane] == 0 { 0 } else { !words[lane] & word_mask(N) });
        loop {
            let mut any = 0u128;
            for lane in z.iter_mut() {
                let next = *lane & rotl_word::<N>(*lane, 1);
                let keep = super::lift2::barrier(0u64.wrapping_sub((next != 0) as u64)) as u128;
                let keep = keep | (keep << 64);
                *lane = (next & keep) | (*lane & !keep);
                any |= next;
            }
            if any == 0 {
                break;
            }
        }
        std::array::from_fn(|lane| {
            let v = words[lane];
            if v == 0 || v == word_mask(N) {
                (v, 0)
            } else {
                least_rotation_from_tops::<N>(v, z[lane])
            }
        })
    }

    /// The index keys of eight roots: `index_canonical128`'s value for every
    /// mode. lift (n = 83): the linear run finder; lift_plant: the same keys,
    /// each also checked against lift_scan and the selected canonicalizer by
    /// `index_canonical128` (one planted count per root); otherwise the
    /// parent's call per root.
    #[inline(always)]
    fn index_keys8(basis: &NormalBasis128, canon: u8, words: &[u128; INDEX_BUILD_LANES]) -> [(u128, u32); INDEX_BUILD_LANES] {
        if basis.n != 83 || (canon != INDEX_CANON_LIFT && canon != INDEX_CANON_LIFT_PLANT) {
            return std::array::from_fn(|lane| index_canonical128(basis, canon, words[lane]));
        }
        let keys = lift_linear_lanes8::<83>(words);
        if canon == INDEX_CANON_LIFT_PLANT {
            for (lane, key) in keys.iter().enumerate() {
                assert_eq!(*key, index_canonical128(basis, canon, words[lane]),
                           "the linear canonicalizer and lift_scan differ on an index root");
            }
        }
        keys
    }

    // ── koblitz-n83-indexbuild2-20261020: C9, the state roots from fewer products ──

    /// The S3 roots of a regular state (l != r, l != 0, r != 0) from
    /// 1/l, 1/r and 1/(l + r): q = p * (1/(l + r))^2 = p / a and
    /// d = c * (1/l + 1/r)^2 = c * a / ps, the parent's q and d; then the
    /// parent's trace test, half trace and root order.
    #[inline(always)]
    fn s3_roots_from_inverses(
        gf: &Gf2_128,
        solver: &S3Solver128,
        left: u128,
        right: u128,
        left_inverse: u128,
        right_inverse: u128,
        sum_inverse: u128,
    ) -> Option<[u128; 2]> {
        oc::bump(oc::S3_SOLVES, 1);
        let p = fmul(&gf, left, right);
        // koblitz-n83-fieldops-20261104 (E1): the inlined square is the
        // table map `square` (both GF(2)-linear, equal on every unit vector).
        let c = fsqr(&gf, p) ^ solver.b;
        let d = fmul(&gf, c, fsqr(&gf, left_inverse ^ right_inverse));
        if (d & solver.trace_mask).count_ones() & 1 == 1 {
            return None;
        }
        let q = fmul(&gf, p, fsqr(&gf, sum_inverse));
        oc::bump(oc::FIELD_HALF_TRACE, 1);
        let first = fmul(&gf, q, solver.half_trace.apply(d));
        Some([first, first ^ q])
    }

    /// Montgomery's trick over `values[k]` for every k in `regular` (all
    /// non-zero), as four interleaved chains (by position mod 4) that share
    /// one inversion; `inverses[k]` is the field inverse of `values[k]`.
    fn sum_inverses_lanes4(
        gf: &Gf2_128,
        basis: &NormalBasis128,
        values: &[u128],
        regular: &[usize],
        prefixes: &mut [u128],
        inverses: &mut [u128],
    ) {
        if regular.is_empty() {
            return;
        }
        let mut chains = [1u128; 4];
        for (position, &k) in regular.iter().enumerate() {
            let lane = position & 3;
            prefixes[k] = chains[lane];
            chains[lane] = fmul(&gf, chains[lane], values[k]);
        }
        let low = fmul(&gf, chains[0], chains[1]);
        let high = fmul(&gf, chains[2], chains[3]);
        // A product of non-zero field elements is non-zero.
        let all = invert128(gf, basis, fmul(&gf, low, high));
        let low_inverse = fmul(&gf, all, high);
        let high_inverse = fmul(&gf, all, low);
        let mut lane_inverses = [
            fmul(&gf, low_inverse, chains[1]),
            fmul(&gf, low_inverse, chains[0]),
            fmul(&gf, high_inverse, chains[3]),
            fmul(&gf, high_inverse, chains[2]),
        ];
        for (position, &k) in regular.iter().enumerate().rev() {
            let lane = position & 3;
            inverses[k] = fmul(&gf, lane_inverses[lane], prefixes[k]);
            lane_inverses[lane] = fmul(&gf, lane_inverses[lane], values[k]);
        }
    }

    /// The field inverse of every shifted representative x^(2^k): the
    /// inverse of x squared k times, each checked by a product (0 maps to 0).
    fn shifted_inverses128(gf: &Gf2_128, basis: &NormalBasis128, shifted: &[Vec<u128>]) -> Vec<Vec<u128>> {
        shifted
            .iter()
            .map(|row| {
                let mut inverse = if row[0] == 0 { 0 } else { invert128(gf, basis, row[0]) };
                row.iter()
                    .map(|&value| {
                        let here = inverse;
                        assert!(value == 0 || fmul(&gf, value, here) == 1, "a shifted representative's inverse is wrong");
                        inverse = fsqr(&gf, inverse);
                        if value == 0 { 0 } else { here }
                    })
                    .collect()
            })
            .collect()
    }

    #[inline(always)]
    fn index_canonical128(basis: &NormalBasis128, canon: u8, v: u128) -> (u128, u32) {
        oc::bump(oc::CANONICALIZATIONS, 1);
        if canon == INDEX_CANON_LIFT {
            super::lift2::lift_scan_wide(v, basis.n)
        } else if canon == INDEX_CANON_LIFT_PLANT {
            let lifted = super::lift2::lift_scan_wide(v, basis.n);
            let selected = basis.canonical_selected(black_box(v));
            assert_eq!(lifted, selected, "lift_scan and the selected canonicalizer differ on an index root");
            INDEX_PLANT_CHECKED.fetch_add(1, Ordering::Relaxed);
            lifted
        } else {
            basis.canonical_selected(v)
        }
    }

    struct Fold128 {
        width: usize,
        n: usize,
        selfs: usize,
        offsets: Vec<usize>,
        plant: bool,
    }

    impl Fold128 {
        fn new(width: usize, n: usize, plant: bool) -> Self {
            let selfs = (0..n).filter(|&relative| 2 * relative <= n).count();
            let mut offsets = Vec::with_capacity(width + 1);
            let mut total = 0usize;
            for left in 0..width {
                offsets.push(total);
                total += selfs + (width - 1 - left) * n;
            }
            offsets.push(total);
            Self { width, n, selfs, offsets, plant }
        }

        fn stored(&self) -> usize {
            self.offsets[self.width]
        }

        fn logical(&self) -> usize {
            self.width * self.width * self.n
        }

        #[inline(always)]
        fn decompose(&self, index: usize) -> (usize, usize, usize) {
            let pair = index / self.n;
            (pair / self.width, pair % self.width, index % self.n)
        }

        #[inline(always)]
        fn compose(&self, left: usize, right: usize, relative: usize) -> usize {
            (left * self.width + right) * self.n + relative
        }

        #[inline(always)]
        fn is_representative(&self, left: usize, right: usize, relative: usize) -> bool {
            left < right || (left == right && 2 * relative <= self.n)
        }

        #[inline(always)]
        fn mate_index(&self, index: usize) -> usize {
            let (left, right, relative) = self.decompose(index);
            self.compose(right, left, (self.n - relative) % self.n)
        }

        #[inline(always)]
        fn slot(&self, left: usize, right: usize, relative: usize) -> usize {
            self.offsets[left]
                + if left == right {
                    relative
                } else {
                    self.selfs + (right - left - 1) * self.n + relative
                }
        }
    }

    /// The unfolded state at logical index `index`: the stored representative,
    /// or its mate rebuilt by rotating the representative's normal roots.
    #[inline(always)]
    fn fold_state128(index: &Index128, fold: &Fold128, basis: &NormalBasis128, logical: usize) -> State128 {
        let (left, right, relative) = fold.decompose(logical);
        if fold.is_representative(left, right, relative) {
            let stored = &index.states[fold.slot(left, right, relative)];
            return State128 {
                left: stored.left,
                right: stored.right,
                relative: stored.relative,
                normal_roots: stored.normal_roots,
            };
        }
        let stored = &index.states[fold.slot(right, left, (fold.n - relative) % fold.n)];
        let k = relative as u32;
        oc::bump(oc::FOLD_ROTATIONS, if k != 0 { 2 } else { 0 });
        State128 {
            left: left as u16,
            right: right as u16,
            relative: relative as u16,
            normal_roots: [
                basis.rotate(stored.normal_roots[0], k),
                basis.rotate(stored.normal_roots[1], k),
            ],
        }
    }

    /// The fold's stored representatives (the state fold's
    /// `build_index128_folded` state loop and planted work, unchanged); the
    /// caller fills the selected root table from them.
    fn folded_states128(
        gf: &Gf2_128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        shifted: &[Vec<u128>],
        fold: &Fold128,
        mode: IndexMode128,
    ) -> Vec<State128> {
        let n = gf.n as usize;
        let width = shifted.len();
        // koblitz-n83-indexbuild2-20261020 (C9): the same states in the same
        // order. A regular state's roots come from 1/l, 1/r (computed once
        // per shifted representative) and 1/(l + r) (one row's sums share
        // one inversion over four interleaved chains): seven field products
        // per state, the parent's q, d, trace test, half trace and root
        // order. An irregular state (l == r, or a zero input) takes the
        // parent's fallback, s3_x_roots_128(gf, b, l, r). The vector is
        // allocated once at its final length.
        let inverses = shifted_inverses128(gf, basis, shifted);
        let mut states = Vec::with_capacity(fold.stored());
        let mut relatives: Vec<usize> = Vec::with_capacity(n);
        let mut regular: Vec<usize> = Vec::with_capacity(n);
        let mut sums = vec![0u128; n];
        let mut prefixes = vec![0u128; n];
        let mut sum_inverses = vec![0u128; n];
        for left in 0..width {
            let l = shifted[left][0];
            let left_inverse = inverses[left][0];
            for right in left..width {
                relatives.clear();
                regular.clear();
                for relative in 0..n {
                    if left == right && 2 * relative > n {
                        continue;
                    }
                    let r = shifted[right][relative];
                    if l != 0 && r != 0 && l != r {
                        sums[relatives.len()] = l ^ r;
                        regular.push(relatives.len());
                    }
                    relatives.push(relative);
                }
                sum_inverses_lanes4(gf, basis, &sums, &regular, &mut prefixes, &mut sum_inverses);
                let mut next_regular = 0usize;
                for (k, &relative) in relatives.iter().enumerate() {
                    let r = shifted[right][relative];
                    let roots = if next_regular < regular.len() && regular[next_regular] == k {
                        next_regular += 1;
                        s3_roots_from_inverses(gf, solver, l, r, left_inverse, inverses[right][relative], sum_inverses[k])
                    } else {
                        s3_x_roots_128_counted(gf, solver.b, l, r)
                    };
                    let roots = roots.expect("the state fold needs every state regular");
                    states.push(State128 {
                        left: left as u16,
                        right: right as u16,
                        relative: relative as u16,
                        normal_roots: [
                            basis.to_normal.apply(roots[0]),
                            basis.to_normal.apply(roots[1]),
                        ],
                    });
                }
            }
        }
        assert_eq!(states.len(), fold.stored());
        if mode.plant {
            // Planted control: redo, and discard, the S3 solve and both root
            // canonicalizations of every mate state the fold does not store.
            for left in 0..width {
                for right in 0..=left {
                    for relative in 0..n {
                        if fold.is_representative(left, right, relative) {
                            continue;
                        }
                        let roots = solver
                            .roots(gf, basis, shifted[left][0], shifted[right][relative])
                            .expect("the state fold needs every state regular");
                        for root in roots {
                            black_box(index_canonical128(
                                basis,
                                mode.canon,
                                basis.to_normal.apply(black_box(root)),
                            ));
                        }
                    }
                }
            }
        }
        states
    }

    /// The baseline scan over the logical states (same order, same `start`
    /// or Feistel key), each class scanned once at its first occurrence, with
    /// the layout's probe loop `P`.
    #[allow(clippy::too_many_arguments)]
    fn extract128_folded<const C: u8, const O: u8, const P: u8>(
        gf: &Gf2_128,
        fast: &FastBinaryCurve128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        index: &Index128,
        fold: &Fold128,
        base: &Base128,
        target: FastPoint128,
        target_x: u128,
        start: usize,
        probes: &mut u64,
        scan: &mut StateScan128,
        clock: &mut PhaseClock,
        split: &mut ExtractSplit,
    ) -> Option<Relation128> {
        let len = index.logical_states;
        macro_rules! visit {
            ($logical:expr, $skip:expr) => {{
                let logical = $logical;
                let skip = $skip;
                if skip {
                    split.skipped_symmetric_states += 1;
                }
                if !skip || fold.plant {
                    let state = fold_state128(index, fold, basis, logical);
                    if skip {
                        let mut audit = 0u64;
                        let found = scan_state128_select::<C, P>(
                            gf, fast, basis, solver, index, base, target, target_x, &state, scan,
                            &mut audit, clock, split,
                        );
                        assert!(found.is_none(), "a skipped mate state found a relation");
                        FOLD_AUDIT_PROBES.fetch_add(audit, Ordering::Relaxed);
                    } else if let Some(relation) = scan_state128_select::<C, P>(
                        gf, fast, basis, solver, index, base, target, target_x, &state, scan,
                        probes, clock, split,
                    ) {
                        return Some(relation);
                    }
                }
            }};
        }
        if O == ORDER_FEISTEL {
            let permutation = ScanPermutation::new(len, start as u64);
            for position in 0..permutation.domain {
                let logical = permutation.apply(position);
                if logical >= len as u64 {
                    continue;
                }
                let logical = logical as usize;
                let mate = fold.mate_index(logical);
                visit!(logical, mate != logical && permutation.invert(mate as u64) < position);
            }
            return None;
        }
        let start = start % len.max(1);
        for offset in 0..len {
            let logical = if start + offset < len { start + offset } else { start + offset - len };
            let mate = fold.mate_index(logical);
            let mate_offset = if mate >= start { mate - start } else { mate + len - start };
            visit!(logical, mate != logical && mate_offset < offset);
        }
        None
    }

    /// Sampled check that `invert` undoes `apply` (the crate tests check the
    /// whole domain).
    fn scan_inverse_selftest(len: usize, key: u64) -> bool {
        let permutation = ScanPermutation::new(len, key);
        let mut x = key | 1;
        (0..65_536).all(|_| {
            x ^= x << 13;
            x ^= x >> 7;
            x ^= x << 17;
            let position = x % permutation.domain;
            permutation.invert(permutation.apply(position)) == position
        })
    }

    #[inline(always)]
    fn digest_mix64(mut z: u64) -> u64 {
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }

    /// The state fold's digests: every logical state in index order, and an
    /// order-independent digest of the root table's key -> value map, read
    /// from whichever table this index holds (equal for every arm iff the
    /// arm reproduces B's states and B's table map).
    fn index_digest128(index: &Index128, basis: &NormalBasis128) -> Value {
        let mut hasher = blake3::Hasher::new();
        hasher.update(b"n83-state-fold-logical-states-v1");
        let mut buffer = Vec::with_capacity(1 << 16);
        for logical in 0..index.logical_states {
            let rebuilt;
            let state = match &index.fold {
                Some(fold) => {
                    rebuilt = fold_state128(index, fold, basis, logical);
                    &rebuilt
                }
                None => &index.states[logical],
            };
            buffer.extend_from_slice(&state.left.to_le_bytes());
            buffer.extend_from_slice(&state.right.to_le_bytes());
            buffer.extend_from_slice(&state.relative.to_le_bytes());
            buffer.extend_from_slice(&state.normal_roots[0].to_le_bytes());
            buffer.extend_from_slice(&state.normal_roots[1].to_le_bytes());
            if buffer.len() >= (1 << 16) - 64 {
                hasher.update(&buffer);
                buffer.clear();
            }
        }
        hasher.update(&buffer);
        let (mut sum, mut xor, mut entries) = (0u64, 0u64, 0u64);
        let mut add = |key: u128, value: u64| {
            let h = digest_mix64(
                digest_mix64(key as u64 ^ 0x243F_6A88_85A3_08D3)
                    ^ digest_mix64((key >> 64) as u64 ^ 0x1319_8A2E_0370_7344)
                    ^ digest_mix64(value ^ 0xA409_3822_299F_31D0).rotate_left(1),
            );
            sum = sum.wrapping_add(h);
            xor ^= h.rotate_left(23);
            entries += 1;
        };
        match &index.compact {
            Some(compact) => {
                for &word in &compact.slots {
                    if word != 0 {
                        add(word & COMPACT_KEY_MASK, CompactRootTable128::expand(word));
                    }
                }
            }
            None => {
                for &(key, value) in &index.table.slots {
                    if key != u128::MAX {
                        add(key, value);
                    }
                }
            }
        }
        json!({
            "logical_states": index.logical_states,
            "logical_states_blake3": hasher.finalize().to_hex().to_string(),
            "table_entries": entries,
            "table_map_sum64": format!("{sum:016x}"),
            "table_map_xor64": format!("{xor:016x}"),
            "accounting": "after the last target; outside setup and every online interval",
        })
    }

    /// koblitz-n83-indexlift-20261019: every stored state in stored order,
    /// and every slot word of the root table (empty slots included) in slot
    /// order. Equal digests mean the same stored states and the same table
    /// layout, not only the same logical states and key -> value map.
    fn index_layout_digest128(index: &Index128) -> (String, String) {
        let mut states = blake3::Hasher::new();
        states.update(b"n83-indexlift-stored-states-v1");
        let mut buffer = Vec::with_capacity(1 << 16);
        for state in &index.states {
            buffer.extend_from_slice(&state.left.to_le_bytes());
            buffer.extend_from_slice(&state.right.to_le_bytes());
            buffer.extend_from_slice(&state.relative.to_le_bytes());
            buffer.extend_from_slice(&state.normal_roots[0].to_le_bytes());
            buffer.extend_from_slice(&state.normal_roots[1].to_le_bytes());
            if buffer.len() >= (1 << 16) - 64 {
                states.update(&buffer);
                buffer.clear();
            }
        }
        states.update(&buffer);
        buffer.clear();
        let mut slots = blake3::Hasher::new();
        slots.update(b"n83-indexlift-table-slots-v1");
        match &index.compact {
            Some(compact) => {
                slots.update(b"compact");
                for &word in &compact.slots {
                    buffer.extend_from_slice(&word.to_le_bytes());
                    if buffer.len() >= (1 << 16) - 64 {
                        slots.update(&buffer);
                        buffer.clear();
                    }
                }
            }
            None => {
                slots.update(b"base");
                for &(key, value) in &index.table.slots {
                    buffer.extend_from_slice(&key.to_le_bytes());
                    buffer.extend_from_slice(&value.to_le_bytes());
                    if buffer.len() >= (1 << 16) - 64 {
                        slots.update(&buffer);
                        buffer.clear();
                    }
                }
            }
        }
        slots.update(&buffer);
        (states.finalize().to_hex().to_string(), slots.finalize().to_hex().to_string())
    }

    #[cfg(test)]
    mod indexlift_tests {
        use super::*;

        #[test]
        fn every_index_canonicalizer_builds_the_same_layout() {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let b = gf.from_element(&curve.curve.b);
            let r = curve.subgroup_order.to_u64().unwrap();
            let (_, _, reps, _) = construct_base128(&fast, &curve, b, 9, r);
            let reps: Vec<u128> = reps.iter().map(|p| p.unwrap()[0]).collect();
            let basis = NormalBasis128::new(&gf);
            let solver = S3Solver128::new(&gf, b);
            let mode = |canon| IndexMode128 { fold: true, plant: false, canon };
            for table in [TABLE_BASE, TABLE_COMPACT] {
                let reference = build_index128_stacked(&gf, &basis, &solver, &reps, table, 28,
                                                       mode(INDEX_CANON_SELECTED));
                let want = index_layout_digest128(&reference);
                let want_map = index_digest128(&reference, &basis);
                for canon in [INDEX_CANON_LIFT, INDEX_CANON_LIFT_PLANT] {
                    let before = INDEX_PLANT_CHECKED.load(Ordering::Relaxed);
                    let index = build_index128_stacked(&gf, &basis, &solver, &reps, table, 28, mode(canon));
                    let checked = INDEX_PLANT_CHECKED.load(Ordering::Relaxed) - before;
                    if canon == INDEX_CANON_LIFT_PLANT {
                        assert!(checked >= 2 * index.states.len() as u64);
                    }
                    assert_eq!(index_layout_digest128(&index), want);
                    assert_eq!(index_digest128(&index, &basis), want_map);
                    match (&index.compact, &reference.compact) {
                        (Some(a), Some(b)) => assert!(a.slots == b.slots),
                        (None, None) => assert!(index.table.slots == reference.table.slots),
                        _ => panic!("layouts differ"),
                    }
                }
            }
        }

        #[test]
        fn lift_scan_equals_the_selected_canonicalizer_with_its_shift() {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let basis = NormalBasis128::new(&gf);
            let mut x = 0x9E37_79B9_7F4A_7C15_D1B5_4A32_D192_ED03u128;
            let mut words = vec![0u128, basis.mask, 1, 3, basis.mask ^ 1];
            for _ in 0..200_000 {
                x ^= x << 13;
                x ^= x >> 7;
                x ^= x << 17;
                words.push(x & basis.mask);
                words.push(x & basis.mask & (x >> 3));
            }
            for v in words {
                assert_eq!(super::super::lift2::lift_scan_wide(v, basis.n), basis.canonical_selected(v), "{v:#x}");
            }
        }
    }

    #[cfg(test)]
    mod indexbuild2_tests {
        // koblitz-n83-indexbuild2-20261020: the parent's (koblitz-n83-indexbuild-20261020)
        // state loop and compact insert loop, verbatim (re-indented), as references.
        use super::*;

        fn parent_folded_states(
            gf: &Gf2_128,
            basis: &NormalBasis128,
            solver: &S3Solver128,
            shifted: &[Vec<u128>],
            fold: &Fold128,
        ) -> Vec<State128> {
            let n = gf.n as usize;
            let width = shifted.len();
            // koblitz-n83-indexbuild-20261020: the same states in the same order.
            // One (left, right) row's S3 solves share one field inversion
            // (RootBatch128: the same prepare and finish as S3Solver128::roots,
            // Montgomery's trick over the row's non-zero denominators; a zero
            // denominator takes finish's scalar fallback, as in roots). The
            // vector is allocated once at its final length.
            let mut states = Vec::with_capacity(fold.stored());
            let mut batch = RootBatch128::with_capacity(n);
            let mut inputs: Vec<(u128, u128)> = Vec::with_capacity(n);
            let mut relatives: Vec<u16> = Vec::with_capacity(n);
            for left in 0..width {
                for right in left..width {
                    inputs.clear();
                    relatives.clear();
                    for relative in 0..n {
                        if left == right && 2 * relative > n {
                            continue;
                        }
                        inputs.push((shifted[left][0], shifted[right][relative]));
                        relatives.push(relative as u16);
                    }
                    batch.solve(gf, basis, solver, &inputs);
                    for (&relative, roots) in relatives.iter().zip(&batch.results) {
                        let roots = roots.expect("the state fold needs every state regular");
                        states.push(State128 {
                            left: left as u16,
                            right: right as u16,
                            relative,
                            normal_roots: [
                                basis.to_normal.apply(roots[0]),
                                basis.to_normal.apply(roots[1]),
                            ],
                        });
                    }
                }
            }
            assert_eq!(states.len(), fold.stored());
            states
        }

        fn parent_compact(basis: &NormalBasis128, states: &[State128], canon: u8) -> CompactRootTable128 {
            let mode = IndexMode128 { fold: true, plant: false, canon };
            // The same inserts, in the same order, into the 16-byte layout.
            // koblitz-n83-indexbuild-20261020: root i + INDEX_BUILD_LOOKAHEAD
            // is canonicalized (once, in root order) and its home slot
            // prefetched while root i is inserted.
            let mut slots = CompactRootTable128::with_capacity(states.len() * 2);
            let total = states.len() * 2;
            let root_at = |i: usize| states[i >> 1].normal_roots[i & 1];
            let mut ahead = [(0u128, 0u32); INDEX_BUILD_LOOKAHEAD];
            for i in 0..INDEX_BUILD_LOOKAHEAD.min(total) {
                let key = index_canonical128(basis, mode.canon, root_at(i));
                slots.prefetch(key.0);
                ahead[i] = key;
            }
            for i in 0..total {
                let (canonical, shift) = ahead[i % INDEX_BUILD_LOOKAHEAD];
                if i + INDEX_BUILD_LOOKAHEAD < total {
                    let key = index_canonical128(basis, mode.canon, root_at(i + INDEX_BUILD_LOOKAHEAD));
                    slots.prefetch(key.0);
                    ahead[i % INDEX_BUILD_LOOKAHEAD] = key;
                }
                let state = &states[i >> 1];
                slots.insert_if_absent(
                    canonical,
                    pack(state.left, state.right, state.relative, shift),
                );
            }
            slots
        }

        fn same_states(a: &[State128], b: &[State128]) -> bool {
            a.len() == b.len()
                && a.iter().zip(b).all(|(x, y)| {
                    (x.left, x.right, x.relative, x.normal_roots) == (y.left, y.right, y.relative, y.normal_roots)
                })
        }

        fn n83_setup() -> (FastBinaryCurve128, KoblitzCurve, Gf2_128, NormalBasis128, S3Solver128, u64) {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let b = gf.from_element(&curve.curve.b);
            let r = curve.subgroup_order.to_u64().unwrap();
            let basis = NormalBasis128::new(&gf);
            let solver = S3Solver128::new(&gf, b);
            (fast, curve, gf, basis, solver, r)
        }

        fn shifted_rows(gf: &Gf2_128, reps: &[u128]) -> Vec<Vec<u128>> {
            let n = gf.n as usize;
            reps.iter()
                .map(|&code| {
                    let mut row = Vec::with_capacity(n);
                    let mut value = code;
                    for _ in 0..n {
                        row.push(value);
                        value = fsqr(&gf, value);
                    }
                    row
                })
                .collect()
        }

        struct XorShift(u64);

        impl XorShift {
            fn next(&mut self) -> u64 {
                self.0 ^= self.0 << 13;
                self.0 ^= self.0 >> 7;
                self.0 ^= self.0 << 17;
                self.0
            }

            fn word(&mut self, bits: u32) -> u128 {
                (((self.next() as u128) << 64) | self.next() as u128) & word_mask(bits)
            }
        }

        fn check_every_word<const N: u32>() {
            let mut lanes = [0u128; INDEX_BUILD_LANES];
            for v in 0..(1u128 << N) {
                let want = super::super::lift2::full_scan_u128(v, N);
                assert_eq!(lift_linear::<N>(v), want, "n {N} word {v:#x}");
                lanes[(v as usize) % INDEX_BUILD_LANES] = v;
                if (v as usize) % INDEX_BUILD_LANES == INDEX_BUILD_LANES - 1 {
                    let got = lift_linear_lanes8::<N>(&lanes);
                    for (lane, &word) in lanes.iter().enumerate() {
                        assert_eq!(got[lane], super::super::lift2::full_scan_u128(word, N), "lanes n {N} word {word:#x}");
                    }
                }
            }
        }

        #[test]
        fn linear_canonicalizer_equals_the_full_scan_on_every_word_of_3_to_20_bits() {
            macro_rules! every {
                ($($n:literal),*) => { $( check_every_word::<$n>(); )* };
            }
            every!(3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20);
        }

        #[test]
        fn linear_canonicalizer_equals_lift_scan_on_every_word_of_small_two_limb_geometries() {
            macro_rules! geometry {
                ($(($n:literal, $b:literal)),*) => { $(
                    for v in 0..(1u128 << $n) {
                        assert_eq!(lift_linear::<$n>(v), super::super::lift2::L2::<$n, $b>::canonical_u128(v), "n {} word {v:#x}", $n);
                    }
                )* };
            }
            geometry!((5, 3), (7, 4), (9, 5), (12, 8), (13, 7), (16, 8), (18, 12), (20, 11));
        }

        fn structured_n83_words() -> Vec<u128> {
            let mask = word_mask(83);
            let mut words = vec![0, mask, 1, mask ^ 1, 1 << 82, mask ^ (1 << 82)];
            for bit in 0..83 {
                words.push(1 << bit);
                words.push(mask ^ (1 << bit));
            }
            // One zero run of every length at every start, including runs across the wrap.
            for length in 1..83u32 {
                for start in 0..83u32 {
                    let run = rotl_word::<83>(word_mask(length), start);
                    words.push(mask ^ run);
                }
            }
            // Two or three equal longest runs (ties between candidates), and sparse words.
            for length in 1..27u32 {
                for gap in [length + 1, length + 2, 27, 41] {
                    let run = word_mask(length);
                    let two = mask ^ (run | rotl_word::<83>(run, gap + length));
                    words.push(two);
                    words.push(mask ^ (run | rotl_word::<83>(run, gap + length) | rotl_word::<83>(run, 2 * (gap + length) % 83)));
                }
            }
            let mut rng = XorShift(0x5DEE_CE66_D1CE_4E5B);
            for _ in 0..100_000 {
                let mut v = 0u128;
                for _ in 0..(rng.next() % 6 + 1) {
                    v |= 1u128 << (rng.next() % 83);
                }
                words.push(v);
                words.push(mask ^ v);
            }
            words.push(0x5555_5555_5555_5555_5555 & mask);
            words.push(0x2AAA_AAAA_AAAA_AAAA_AAAA & mask);
            words
        }

        #[test]
        fn linear_canonicalizer_equals_lift_scan_on_random_and_structured_n83_words() {
            let mut words = structured_n83_words();
            let mut rng = XorShift(0x0123_4567_89AB_CDEF);
            for _ in 0..(1usize << 22) {
                words.push(rng.word(83));
            }
            while words.len() % INDEX_BUILD_LANES != 0 {
                words.push(rng.word(83));
            }
            for chunk in words.chunks_exact(INDEX_BUILD_LANES) {
                let lanes: [u128; INDEX_BUILD_LANES] = chunk.try_into().unwrap();
                let got = lift_linear_lanes8::<83>(&lanes);
                for (lane, &v) in lanes.iter().enumerate() {
                    let want = super::super::lift2::lift_scan_wide(v, 83);
                    assert_eq!(lift_linear::<83>(v), want, "word {v:#x}");
                    assert_eq!(got[lane], want, "lanes word {v:#x}");
                }
            }
            // The full scan on the structured words (a direct reference, not through lift_scan).
            for &v in structured_n83_words().iter().step_by(7) {
                assert_eq!(lift_linear::<83>(v), super::super::lift2::full_scan_u128(v, 83), "full scan word {v:#x}");
            }
        }

        #[test]
        fn roots_from_inverses_equal_the_scalar_solver() {
            let (_, _, gf, basis, solver, _) = n83_setup();
            let mut rng = XorShift(0x9E37_79B9_7F4A_7C15);
            let mut none = 0;
            for _ in 0..200_000 {
                let (l, r) = (rng.word(83), rng.word(83));
                if l == 0 || r == 0 || l == r {
                    continue;
                }
                let got = s3_roots_from_inverses(&gf, &solver, l, r, gf.inv(l), gf.inv(r), gf.inv(l ^ r));
                let want = solver.roots(&gf, &basis, l, r);
                assert_eq!(got, want, "l {l:#x} r {r:#x}");
                none += want.is_none() as u32;
            }
            assert!(none > 0, "the trace test's None branch is exercised");
        }

        #[test]
        fn sum_inverses_are_field_inverses_for_every_count() {
            let (_, _, gf, basis, _, _) = n83_setup();
            let mut rng = XorShift(0xC0FF_EE00_1234_5678);
            for count in 0..=90usize {
                let values: Vec<u128> = (0..count).map(|_| rng.word(83) | 1).collect();
                let regular: Vec<usize> = (0..count).filter(|&k| k % 5 != 3).collect();
                let mut prefixes = vec![0u128; count];
                let mut inverses = vec![0u128; count];
                sum_inverses_lanes4(&gf, &basis, &values, &regular, &mut prefixes, &mut inverses);
                for &k in &regular {
                    assert_eq!(fmul(&gf, values[k], inverses[k]), 1, "count {count} k {k}");
                    assert_eq!(inverses[k], gf.inv(values[k]));
                }
            }
        }

        #[test]
        fn derived_states_and_lane_keys_reproduce_the_parent_index() {
            let (fast, curve, gf, basis, solver, r) = n83_setup();
            for width in [1usize, 2, 9, 17] {
                let (_, _, reps, _) = construct_base128(&fast, &curve, gf.from_element(&curve.curve.b), width, r);
                let reps: Vec<u128> = reps.iter().map(|p| p.unwrap()[0]).collect();
                let shifted = shifted_rows(&gf, &reps);
                let fold = Fold128::new(reps.len(), gf.n as usize, false);
                let want = parent_folded_states(&gf, &basis, &solver, &shifted, &fold);
                // The diagonal relative-0 states (l == r) take the fallback path.
                assert!(want.iter().any(|s| s.left == s.right && s.relative == 0));
                for canon in [INDEX_CANON_SELECTED, INDEX_CANON_LIFT, INDEX_CANON_LIFT_PLANT] {
                    for plant in [false, true] {
                        let mode = IndexMode128 { fold: true, plant, canon };
                        let got = folded_states128(&gf, &basis, &solver, &shifted, &fold, mode);
                        assert!(same_states(&got, &want), "states differ at width {width}");
                        let reference = parent_compact(&basis, &want, canon);
                        let before = INDEX_PLANT_CHECKED.load(Ordering::Relaxed);
                        let index = build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28, mode);
                        let checked = INDEX_PLANT_CHECKED.load(Ordering::Relaxed) - before;
                        let compact = index.compact.as_ref().expect("compact layout");
                        assert!(compact.slots == reference.slots, "slot words differ at width {width}");
                        assert_eq!(compact.len, reference.len);
                        assert!(same_states(&index.states, &want));
                        if canon == INDEX_CANON_LIFT_PLANT {
                            assert!(checked >= 2 * want.len() as u64, "every root is checked at width {width}");
                        }
                        let base = build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_BASE, 28, mode);
                        assert!(same_states(&base.states, &want));
                    }
                }
            }
        }

        #[test]
        fn index_keys8_equal_index_canonical128_in_every_mode() {
            let (_, _, gf, basis, _, _) = n83_setup();
            let mut words = structured_n83_words();
            words.truncate(words.len() / INDEX_BUILD_LANES * INDEX_BUILD_LANES);
            for canon in [INDEX_CANON_SELECTED, INDEX_CANON_LIFT, INDEX_CANON_LIFT_PLANT] {
                for chunk in words.chunks_exact(INDEX_BUILD_LANES).step_by(3) {
                    let lanes: [u128; INDEX_BUILD_LANES] = chunk.try_into().unwrap();
                    let got = index_keys8(&basis, canon, &lanes);
                    for (lane, &v) in lanes.iter().enumerate() {
                        assert_eq!(got[lane], index_canonical128(&basis, canon, v));
                    }
                }
            }
        }
    }

    #[cfg(test)]
    mod indexbuild_tests {
        // koblitz-n83-indexbuild-20261020: the parent's state loop, compact
        // insert loop and self-test, verbatim, as references.
        use super::*;

        fn reference_folded_states(
            gf: &Gf2_128,
            basis: &NormalBasis128,
            solver: &S3Solver128,
            shifted: &[Vec<u128>],
            fold: &Fold128,
        ) -> Vec<State128> {
            let n = gf.n as usize;
            let width = shifted.len();
            let mut states = Vec::new();
            for left in 0..width {
                for right in left..width {
                    for relative in 0..n {
                        if left == right && 2 * relative > n {
                            continue;
                        }
                        let roots = solver
                            .roots(gf, basis, shifted[left][0], shifted[right][relative])
                            .expect("the state fold needs every state regular");
                        states.push(State128 {
                            left: left as u16,
                            right: right as u16,
                            relative: relative as u16,
                            normal_roots: [
                                basis.to_normal.apply(roots[0]),
                                basis.to_normal.apply(roots[1]),
                            ],
                        });
                    }
                }
            }
            assert_eq!(states.len(), fold.stored());
            states
        }

        fn reference_compact(basis: &NormalBasis128, states: &[State128], canon: u8) -> CompactRootTable128 {
            let mut slots = CompactRootTable128::with_capacity(states.len() * 2);
            for state in states {
                for &root in &state.normal_roots {
                    let (canonical, shift) = index_canonical128(basis, canon, root);
                    slots.insert_if_absent(
                        canonical,
                        pack(state.left, state.right, state.relative, shift),
                    );
                }
            }
            slots
        }

        fn reference_selftest(len: usize, domain: u64, apply: impl Fn(u64) -> u64) -> bool {
            let mut seen = vec![0u64; len.div_ceil(64)];
            let mut visited = 0usize;
            for index in 0..domain {
                let image = apply(index);
                if image >= domain {
                    return false;
                }
                if image < len as u64 {
                    let (word, bit) = ((image / 64) as usize, image % 64);
                    if seen[word] >> bit & 1 == 1 {
                        return false;
                    }
                    seen[word] |= 1 << bit;
                    visited += 1;
                }
            }
            visited == len
        }

        fn same_states(a: &[State128], b: &[State128]) -> bool {
            a.len() == b.len()
                && a.iter().zip(b).all(|(x, y)| {
                    (x.left, x.right, x.relative, x.normal_roots) == (y.left, y.right, y.relative, y.normal_roots)
                })
        }

        #[test]
        fn batched_states_and_lookahead_inserts_reproduce_the_parent_index() {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let b = gf.from_element(&curve.curve.b);
            let r = curve.subgroup_order.to_u64().unwrap();
            let basis = NormalBasis128::new(&gf);
            let solver = S3Solver128::new(&gf, b);
            for width in [1usize, 2, 9, 17] {
                let (_, _, reps, _) = construct_base128(&fast, &curve, b, width, r);
                let reps: Vec<u128> = reps.iter().map(|p| p.unwrap()[0]).collect();
                let n = gf.n as usize;
                let shifted: Vec<Vec<u128>> = reps
                    .iter()
                    .map(|&code| {
                        let mut row = Vec::with_capacity(n);
                        let mut value = code;
                        for _ in 0..n {
                            row.push(value);
                            value = fsqr(&gf, value);
                        }
                        row
                    })
                    .collect();
                let fold = Fold128::new(reps.len(), n, false);
                let want = reference_folded_states(&gf, &basis, &solver, &shifted, &fold);
                for canon in [INDEX_CANON_SELECTED, INDEX_CANON_LIFT, INDEX_CANON_LIFT_PLANT] {
                    for plant in [false, true] {
                        let mode = IndexMode128 { fold: true, plant, canon };
                        let got = folded_states128(&gf, &basis, &solver, &shifted, &fold, mode);
                        assert!(same_states(&got, &want), "states differ at width {width}");
                        let before = INDEX_PLANT_CHECKED.load(Ordering::Relaxed);
                        let reference = reference_compact(&basis, &want, canon);
                        let reference_checked = INDEX_PLANT_CHECKED.load(Ordering::Relaxed) - before;
                        let before = INDEX_PLANT_CHECKED.load(Ordering::Relaxed);
                        let index = build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28, mode);
                        let checked = INDEX_PLANT_CHECKED.load(Ordering::Relaxed) - before;
                        let compact = index.compact.as_ref().expect("compact layout");
                        assert!(compact.slots == reference.slots, "slot words differ at width {width}");
                        assert_eq!(compact.len, reference.len);
                        assert!(same_states(&index.states, &want));
                        if canon == INDEX_CANON_LIFT_PLANT {
                            assert!(checked >= reference_checked && reference_checked == 2 * want.len() as u64);
                        }
                        let base = build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_BASE, 28, mode);
                        assert!(same_states(&base.states, &want));
                    }
                }
            }
        }

        #[test]
        fn lanes_selftest_equals_the_parent_on_every_small_length_and_key() {
            for len in 1..=1500usize {
                for key in [0u64, 1, 0xDEAD_BEEF, u64::MAX, len as u64 * 0x9E37] {
                    let permutation = ScanPermutation::new(len, key);
                    let apply = |index| permutation.apply(index);
                    let want = reference_selftest(len, permutation.domain, apply);
                    assert!(want, "len {len} key {key}");
                    assert_eq!(scan_permutation_selftest(len, key), want);
                    assert_eq!(bijection_selftest_lanes(len, permutation.domain, apply), want);
                }
            }
        }

        #[test]
        fn lanes_selftest_rejects_every_planted_non_bijection_the_parent_rejects() {
            for len in [5usize, 64, 100, 1000, 4097] {
                let permutation = ScanPermutation::new(len, 0x0123_4567_89AB_CDEF);
                let domain = permutation.domain;
                for at in [0u64, 1, 7, 8, 9, domain / 2, domain - 1] {
                    let collide = |index: u64| {
                        if index == at { permutation.apply((at + 1) % domain) } else { permutation.apply(index) }
                    };
                    let escape = |index: u64| if index == at { domain + at } else { permutation.apply(index) };
                    let mut first_in_range = 0;
                    while permutation.apply(first_in_range) >= len as u64 {
                        first_in_range += 1;
                    }
                    let drop = |index: u64| {
                        if index == first_in_range { domain - 1 } else { permutation.apply(index) }
                    };
                    for (name, ok_lanes, ok_reference) in [
                        ("collide", bijection_selftest_lanes(len, domain, collide), reference_selftest(len, domain, collide)),
                        ("escape", bijection_selftest_lanes(len, domain, escape), reference_selftest(len, domain, escape)),
                        ("drop", bijection_selftest_lanes(len, domain, drop), reference_selftest(len, domain, drop)),
                    ] {
                        assert_eq!(ok_lanes, ok_reference, "{name} len {len} at {at}");
                    }
                    assert!(!bijection_selftest_lanes(len, domain, escape));
                }
                // A state vector shorter than the one the permutation was keyed for: both verdicts agree.
                for shorter in [len.saturating_sub(64).max(1), len / 2] {
                    assert_eq!(bijection_selftest_lanes(shorter, domain, |index| permutation.apply(index)),
                               reference_selftest(shorter, domain, |index| permutation.apply(index)));
                }
            }
        }

        #[test]
        fn lanes_selftest_equals_the_parent_on_the_frozen_n83_state_counts() {
            // M38 / M10 (608 orbits) and K600 logical states: 83 * N^2.
            for len in [30_682_112usize, 29_880_000] {
                for key in [0x0123_4567_89AB_CDEFu64, 0xFEDC_BA98_7654_3210u64] {
                    let permutation = ScanPermutation::new(len, key);
                    let want = reference_selftest(len, permutation.domain, |index| permutation.apply(index));
                    assert!(want);
                    assert_eq!(scan_permutation_selftest(len, key), want);
                }
            }
        }
    }

    #[cfg(test)]
    mod stacked_tests {
        use super::*;

        const FOLDED: IndexMode128 = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_SELECTED };
        const PLANTED: IndexMode128 = IndexMode128 { fold: true, plant: true, canon: INDEX_CANON_SELECTED };
        const FOLDED_LIFT: IndexMode128 = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_LIFT };

        fn small_instance(
            columns: usize,
        ) -> (FastBinaryCurve128, Gf2_128, NormalBasis128, S3Solver128, Base128, Vec<u128>) {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let b = gf.from_element(&curve.curve.b);
            let r = curve.subgroup_order.to_u64().unwrap();
            let (points, labels, reps, _) = construct_base128(&fast, &curve, b, columns, r);
            let mut by_x: HashMap<u128, Vec<usize>> = HashMap::new();
            for (i, point) in points.iter().enumerate() {
                by_x.entry(point.unwrap().0).or_default().push(i);
            }
            let reps: Vec<u128> = reps.iter().map(|p| p.unwrap()[0]).collect();
            let base = Base128 { points, labels, by_x, columns };
            let basis = NormalBasis128::new(&gf);
            let solver = S3Solver128::new(&gf, b);
            (fast, gf, basis, solver, base, reps)
        }

        #[test]
        fn feistel_invert_undoes_apply_on_the_whole_domain() {
            for (len, key) in [(1usize, 3u64), (2, 0), (97, 5), (2100, 0xDEAD_BEEF), (29_880_000, 0x0123_4567_89AB_CDEF)] {
                let permutation = ScanPermutation::new(len, key);
                let step = if permutation.domain > 1 << 20 { 7919 } else { 1 };
                let mut position = 0u64;
                while position < permutation.domain {
                    assert_eq!(permutation.invert(permutation.apply(position)), position);
                    position += step;
                }
            }
        }

        #[test]
        fn fold_counts_match_the_unordered_classes() {
            let fold = Fold128::new(600, 83, false);
            assert_eq!(fold.logical(), 29_880_000);
            assert_eq!(fold.stored(), 14_940_300);
            let small = Fold128::new(7, 5, false);
            let mut seen = vec![false; small.stored()];
            for logical in 0..small.logical() {
                let (l, r, rel) = small.decompose(logical);
                assert_eq!(small.compose(l, r, rel), logical);
                let mate = small.mate_index(logical);
                assert_eq!(small.mate_index(mate), logical);
                let rep = small.is_representative(l, r, rel);
                let (ml, mr, mrel) = small.decompose(mate);
                assert!(rep || small.is_representative(ml, mr, mrel));
                if rep {
                    assert!(!seen[small.slot(l, r, rel)]);
                    seen[small.slot(l, r, rel)] = true;
                }
            }
            assert!(seen.iter().all(|&s| s));
        }

        #[test]
        fn every_stacked_index_holds_the_reference_states_and_map() {
            let (_, gf, basis, solver, _, reps) = small_instance(9);
            let reference =
                build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_BASE, 28, IndexMode128::UNFOLDED);
            let want = index_digest128(&reference, &basis);
            for (table, mode) in [
                (TABLE_BASE, FOLDED),
                (TABLE_BASE, PLANTED),
                (TABLE_COMPACT, IndexMode128::UNFOLDED),
                (TABLE_COMPACT, FOLDED),
                (TABLE_COMPACT, PLANTED),
                (TABLE_COMPACT, FOLDED_LIFT),
                (TABLE_FILTER, FOLDED),
            ] {
                let index = build_index128_stacked(&gf, &basis, &solver, &reps, table, 28, mode);
                assert_eq!(index.logical_states, reference.states.len());
                assert_eq!(index.root_entries(), reference.table.len);
                if mode.fold {
                    assert_eq!(index.states.len(), (9 * 9 * 83 - 9 * 83) / 2 + 9 * 42);
                }
                for logical in 0..reference.states.len() {
                    let a = &reference.states[logical];
                    let b = match &index.fold {
                        Some(fold) => fold_state128(&index, fold, &basis, logical),
                        None => {
                            let s = &index.states[logical];
                            State128 { left: s.left, right: s.right, relative: s.relative, normal_roots: s.normal_roots }
                        }
                    };
                    assert_eq!((a.left, a.right, a.relative, a.normal_roots),
                               (b.left, b.right, b.relative, b.normal_roots), "state {logical}");
                }
                for &(key, value) in &reference.table.slots {
                    if key != u128::MAX {
                        let got = match &index.compact {
                            Some(compact) => compact.get(key),
                            None => index.table.get(key),
                        };
                        assert_eq!(got, Some(value));
                        if let Some(filter) = &index.filter {
                            assert!(filter.contains(key), "filter false negative");
                        }
                    }
                }
                assert_eq!(index_digest128(&index, &basis), want);
            }
        }

        #[test]
        fn every_stacked_arm_finds_the_reference_relation() {
            let (fast, gf, basis, solver, base, reps) = small_instance(9);
            let build = |table, mode| build_index128_stacked(&gf, &basis, &solver, &reps, table, 28, mode);
            let reference = build(TABLE_BASE, IndexMode128::UNFOLDED);
            let base_fold = build(TABLE_BASE, FOLDED);
            let compact = build(TABLE_COMPACT, IndexMode128::UNFOLDED);
            let stack = build(TABLE_COMPACT, FOLDED);
            let planted = build(TABLE_COMPACT, PLANTED);
            let stack_lift = build(TABLE_COMPACT, FOLDED_LIFT);
            let filtered = build(TABLE_FILTER, FOLDED);
            let mut seed = 0x9E37_79B9_7F4A_7C15u64;
            let mut skipped_total = 0u64;
            let mut solved = 0usize;
            for trial in 0..24u64 {
                let mut pick = || {
                    seed = digest_mix64(seed.wrapping_add(trial));
                    (seed % base.points.len() as u64) as usize
                };
                let mut target = base.points[pick()];
                for _ in 0..3 {
                    target = fast.add(target, base.points[pick()]);
                }
                let Some((tx, ty)) = target else { continue };
                let start = digest_mix64((tx ^ ty.rotate_left(29)) as u64) as usize;
                macro_rules! run {
                    ($c:expr, $o:expr, $p:expr, $index:expr) => {{
                        let mut clock = PhaseClock::start();
                        let mut split = ExtractSplit::default();
                        FOLD_AUDIT_PROBES.store(0, Ordering::Relaxed);
                        let relation = extract128::<{ $c }, { $o }, { $p }>(
                            &gf, &fast, &basis, &solver, $index, &base, target, start, &mut clock,
                            &mut split,
                        );
                        (relation.map(|r| ((r.point_indices, r.x_codes, r.intermediates), r.probes)),
                         split.skipped_symmetric_states, FOLD_AUDIT_PROBES.load(Ordering::Relaxed))
                    }};
                }
                macro_rules! compare {
                    ($c:expr, $o:expr) => {{
                        let (want, skipped, _) = run!($c, $o, PIPE_OFF, &reference);
                        assert_eq!(skipped, 0);
                        let (want, want_probes) = want.expect("a planted four-point target decomposes");
                        for (got, skipped, audit) in [
                            run!($c, $o, PIPE_PREFETCH, &reference),
                            run!($c, $o, PIPE_COMPACT, &compact),
                        ] {
                            assert_eq!(got, Some((want, want_probes)), "unfolded layout differs");
                            assert_eq!((skipped, audit), (0, 0));
                        }
                        let (folded, skipped, audit) = run!($c, $o, PIPE_COMPACT, &stack);
                        let (folded, folded_probes) = folded.unwrap();
                        assert_eq!(folded, want, "the stack's relation differs");
                        assert!(folded_probes <= want_probes);
                        assert_eq!(audit, 0);
                        skipped_total += skipped;
                        for (got, _, audit) in [
                            run!($c, $o, PIPE_OFF, &base_fold),
                            run!($c, $o, PIPE_PREFETCH, &base_fold),
                            run!($c, $o, PIPE_COMPACT, &stack_lift),
                            run!($c, $o, PIPE_FILTER, &filtered),
                        ] {
                            assert_eq!(got, Some((want, folded_probes)), "a folded arm differs");
                            assert_eq!(audit, 0);
                        }
                        let (got, _, audit) = run!($c, $o, PIPE_COMPACT, &planted);
                        assert_eq!(got, Some((want, folded_probes)));
                        assert_eq!(folded_probes + audit, want_probes, "planted probe identity");
                        solved += 1;
                    }};
                }
                compare!(CANON_LIFT, ORDER_FEISTEL);
                compare!(CANON_LIFT, ORDER_LEFT_MAJOR);
                compare!(CANON_FULL, ORDER_FEISTEL);
                compare!(CANON_FULL, ORDER_LEFT_MAJOR);
            }
            assert!(solved >= 80);
            assert!(skipped_total > 0, "the small instance should exercise the skip");
        }
    }

    // koblitz-n83-opcounts2-20261108: the library group law with its work
    // counted. Each wrapper classifies the operands with the library's own
    // tests, counts, and returns the library function's result.
    #[inline]
    fn counted_double(fast: &FastBinaryCurve128, x1: u128, y1: u128) -> FastPoint128 {
        if x1 == 0 {
            oc::bump(oc::EC_ADD_TRIVIAL, 1);
        } else {
            oc::bump(oc::EC_DOUBLE, 1);
            oc::bump(oc::FIELD_INV, 1);
            oc::bump(oc::FIELD_MUL, 2);
            oc::bump(oc::FIELD_SQR, 2);
        }
        fast.double(x1, y1)
    }

    #[inline]
    fn counted_add(fast: &FastBinaryCurve128, p: FastPoint128, q: FastPoint128) -> FastPoint128 {
        if oc::on() {
            match (p, q) {
                (Some((x1, y1)), Some((x2, y2))) => {
                    if x1 != x2 {
                        oc::bump(oc::EC_ADD, 1);
                        oc::bump(oc::FIELD_INV, 1);
                        oc::bump(oc::FIELD_MUL, 2);
                        oc::bump(oc::FIELD_SQR, 1);
                    } else if (y1 ^ y2) == x1 || x1 == 0 {
                        oc::bump(oc::EC_ADD_TRIVIAL, 1);
                    } else {
                        oc::bump(oc::EC_DOUBLE, 1);
                        oc::bump(oc::FIELD_INV, 1);
                        oc::bump(oc::FIELD_MUL, 2);
                        oc::bump(oc::FIELD_SQR, 2);
                    }
                }
                _ => oc::bump(oc::EC_ADD_TRIVIAL, 1),
            }
        }
        fast.add(p, q)
    }

    /// The library's `scalar_mul` result. With counting on, its
    /// double-and-add loop is also walked over the counted wrappers of the
    /// same library calls (to count), and the two results must be equal.
    fn counted_scalar_mul(fast: &FastBinaryCurve128, p: FastPoint128, k: &BigUint) -> FastPoint128 {
        let library = fast.scalar_mul(p, k);
        if !oc::on() {
            return library;
        }
        oc::bump(oc::EC_SCALAR_MUL, 1);
        let mut result: FastPoint128 = None;
        for i in (0..k.bits()).rev() {
            result = match result {
                None => None,
                Some((x, y)) => counted_double(fast, x, y),
            };
            if k.bit(i) {
                result = counted_add(fast, result, p);
            }
        }
        assert_eq!(result, library, "the counted double-and-add differs from the library's scalar_mul");
        library
    }

    #[inline]
    fn s3_x_roots_128_counted(gf: &Gf2_128, b: u128, left: u128, right: u128) -> Option<[u128; 2]> {
        oc::bump(oc::S3_SOLVES_LIBRARY, 1);
        s3_x_roots_128(gf, b, left, right)
    }

    fn lift128(
        fast: &FastBinaryCurve128,
        base: &Base128,
        codes: &[u128; 4],
        target: FastPoint128,
    ) -> Option<[usize; 4]> {
        oc::bump(oc::RELATION_LIFTS, 1);
        let choices: Vec<&Vec<usize>> = codes
            .iter()
            .map(|code| base.by_x.get(code))
            .collect::<Option<_>>()?;
        for &a in choices[0] {
            for &b in choices[1] {
                let ab = counted_add(fast, base.points[a], base.points[b]);
                for &c in choices[2] {
                    let abc = counted_add(fast, ab, base.points[c]);
                    for &d in choices[3] {
                        if counted_add(fast, abc, base.points[d]) == target {
                            return Some([a, b, c, d]);
                        }
                    }
                }
            }
        }
        None
    }

    /// Per-state scratch for [`scan_state128`]: the `2n` candidate pairs
    /// and their batched root solutions.
    struct StateScan128 {
        inputs: Vec<(u128, u128)>,
        batch: RootBatch128,
        keys: Vec<ProbeKey128>,
        survivors: Vec<u32>,
        padd: PaddScratch128,
        frame: FrameScratch128,
    }

    impl StateScan128 {
        fn new(n: u32) -> Self {
            let entries = 2 * n as usize;
            Self {
                inputs: Vec::with_capacity(entries),
                batch: RootBatch128::with_capacity(entries),
                keys: Vec::with_capacity(2 * entries),
                survivors: Vec::with_capacity(2 * entries),
                padd: PaddScratch128::with_capacity(entries),
                frame: FrameScratch128::with_capacity(entries),
            }
        }
    }

    /// Scan one index state against `target` in the sequential candidate
    /// order (shift outer, stored root inner) and return the first lifted
    /// relation.  Candidate order, probe count and published relation are
    /// exactly those of the frozen wide example; the laps around `lift128`
    /// feed the online PDP / relation-check split.
    #[inline(always)]
    #[allow(clippy::too_many_arguments)]
    fn scan_state128<const C: u8>(
        gf: &Gf2_128,
        fast: &FastBinaryCurve128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        index: &Index128,
        base: &Base128,
        target: FastPoint128,
        target_x: u128,
        state: &State128,
        scan: &mut StateScan128,
        probes: &mut u64,
        clock: &mut PhaseClock,
        split: &mut ExtractSplit,
    ) -> Option<Relation128> {
        let n = gf.n;
        scan.inputs.clear();
        for shift in 0..n {
            for &normal_root in &state.normal_roots {
                let absolute = basis.to_poly.apply(basis.rotate(normal_root, shift));
                scan.inputs.push((absolute, target_x));
            }
        }
        oc::bump(oc::FROBENIUS_X, (n as u64 - 1) * state.normal_roots.len() as u64);
        scan.batch.solve(gf, basis, solver, &scan.inputs);
        split.root_calls += scan.inputs.len() as u64;
        let mut candidate = 0usize;
        for shift in 0..n {
            let left_x = index.shifted[state.left as usize][shift as usize];
            let right_x = index.shifted[state.right as usize]
                [(shift as usize + state.relative as usize) % n as usize];
            for _ in 0..state.normal_roots.len() {
                let absolute = scan.inputs[candidate].0;
                let result = scan.batch.results[candidate];
                candidate += 1;
                let Some(partners) = result else {
                    continue;
                };
                for partner in partners {
                    *probes += 1;
                    let (canonical, partner_shift) =
                        target_canonical::<C>(basis, basis.to_normal.apply(partner));
                    let Some(value) = index.table.get(canonical) else {
                        continue;
                    };
                    let (left2, right2, relative2, stored_shift) = unpack(value);
                    let left_shift2 = ((stored_shift + n - partner_shift) % n) as usize;
                    let right_shift2 = (left_shift2 + relative2) % n as usize;
                    let codes = [
                        left_x,
                        right_x,
                        index.shifted[left2][left_shift2],
                        index.shifted[right2][right_shift2],
                    ];
                    split.pdp += clock.lap();
                    let lifted = lift128(fast, base, &codes, target);
                    split.relation_check += clock.lap();
                    split.relation_checks += 1;
                    if let Some(point_indices) = lifted {
                        return Some(Relation128 {
                            point_indices,
                            x_codes: codes,
                            intermediates: [absolute, partner],
                            probes: *probes,
                        });
                    }
                }
            }
        }
        None
    }

    // koblitz-n83-probepipe-20261015: target-scan probe pipeline selector
    // (KIC_PROBE_PIPELINE), a const generic of the target scan so every arm
    // is its own monomorphized loop.
    const PIPE_OFF: u8 = 0;
    const PIPE_PREFETCH: u8 = 1;

    fn probe_pipeline_from_env() -> (u8, &'static str) {
        match std::env::var("KIC_PROBE_PIPELINE").as_deref() {
            Err(_) | Ok("") | Ok("off") => (PIPE_OFF, "off"),
            Ok("prefetch") => (PIPE_PREFETCH, "prefetch"),
            Ok(other) => panic!("unknown KIC_PROBE_PIPELINE {other}"),
        }
    }

    /// One partner probe of a state, computed ahead of its table lookup.
    #[derive(Clone, Copy)]
    struct ProbeKey128 {
        canonical: u128,
        partner: u128,
        partner_shift: u32,
        candidate: u32,
    }

    /// Hint the cache line of `key`'s home slot. A prefetch never faults and
    /// changes no architectural state; the lookup itself is unchanged.
    #[inline(always)]
    fn prefetch_root_slot(table: &RootTable128, key: u128) {
        #[cfg(target_arch = "x86_64")]
        {
            let slot = table.slot(key);
            debug_assert!(slot < table.slots.len());
            let address = table.slots.as_ptr().wrapping_add(slot) as *const i8;
            // SAFETY: `_mm_prefetch` is a hint; it does not dereference
            // `address` architecturally and cannot fault. SSE is part of
            // the x86_64 baseline.
            #[allow(unused_unsafe)]
            unsafe {
                std::arch::x86_64::_mm_prefetch(address, std::arch::x86_64::_MM_HINT_T0);
            }
        }
        #[cfg(not(target_arch = "x86_64"))]
        {
            let _ = (table, key);
        }
    }

    /// [`scan_state128`] with its probes software-pipelined: the same root
    /// batch; then every partner's canonical key in the same candidate order
    /// (shift outer, stored root inner, solver partner order), each followed
    /// by a prefetch of its home slot; then the lookups, lift and relation
    /// check in that same order with the same probe counter and the same
    /// early return. Probe count, relation and laps are those of
    /// `scan_state128`; memory latency overlaps the key computation.
    #[inline(always)]
    #[allow(clippy::too_many_arguments)]
    fn scan_state128_pipelined<const C: u8>(
        gf: &Gf2_128,
        fast: &FastBinaryCurve128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        index: &Index128,
        base: &Base128,
        target: FastPoint128,
        target_x: u128,
        state: &State128,
        scan: &mut StateScan128,
        probes: &mut u64,
        clock: &mut PhaseClock,
        split: &mut ExtractSplit,
    ) -> Option<Relation128> {
        let n = gf.n;
        scan.inputs.clear();
        for shift in 0..n {
            for &normal_root in &state.normal_roots {
                let absolute = basis.to_poly.apply(basis.rotate(normal_root, shift));
                scan.inputs.push((absolute, target_x));
            }
        }
        oc::bump(oc::FROBENIUS_X, (n as u64 - 1) * state.normal_roots.len() as u64);
        scan.batch.solve(gf, basis, solver, &scan.inputs);
        split.root_calls += scan.inputs.len() as u64;
        scan.keys.clear();
        for (candidate, result) in scan.batch.results.iter().enumerate() {
            let Some(partners) = *result else {
                continue;
            };
            for partner in partners {
                let (canonical, partner_shift) =
                    target_canonical::<C>(basis, basis.to_normal.apply(partner));
                prefetch_root_slot(&index.table, canonical);
                scan.keys.push(ProbeKey128 {
                    canonical,
                    partner,
                    partner_shift,
                    candidate: candidate as u32,
                });
            }
        }
        let roots_per_shift = state.normal_roots.len();
        for key in &scan.keys {
            *probes += 1;
            let Some(value) = index.table.get(key.canonical) else {
                continue;
            };
            let candidate = key.candidate as usize;
            let shift = candidate / roots_per_shift;
            let left_x = index.shifted[state.left as usize][shift];
            let right_x =
                index.shifted[state.right as usize][(shift + state.relative as usize) % n as usize];
            let absolute = scan.inputs[candidate].0;
            let partner = key.partner;
            let partner_shift = key.partner_shift;
            let (left2, right2, relative2, stored_shift) = unpack(value);
            let left_shift2 = ((stored_shift + n - partner_shift) % n) as usize;
            let right_shift2 = (left_shift2 + relative2) % n as usize;
            let codes = [
                left_x,
                right_x,
                index.shifted[left2][left_shift2],
                index.shifted[right2][right_shift2],
            ];
            split.pdp += clock.lap();
            let lifted = lift128(fast, base, &codes, target);
            split.relation_check += clock.lap();
            split.relation_checks += 1;
            if let Some(point_indices) = lifted {
                return Some(Relation128 {
                    point_indices,
                    x_codes: codes,
                    intermediates: [absolute, partner],
                    probes: *probes,
                });
            }
        }
        None
    }

    // koblitz-n83-tablefilter-20261015: the scan loops of the new layouts.
    const PIPE_COMPACT: u8 = 2;
    const PIPE_FILTER: u8 = 3;
    const PIPE_FILTER_PLANT: u8 = 4;

    /// [`scan_state128_pipelined`] over the two-level root table. The same
    /// root batch and the same keys in the same order (shift outer, stored
    /// root inner, solver partner order); each key is followed by a
    /// prefetch of its filter word (`PIPE_COMPACT`: of its home slot). Then,
    /// in probe order, the filter test; each survivor's home slot is
    /// prefetched. Then the survivors, in probe order, get the exact
    /// compact-table lookup, lift and relation check; the probe counter is
    /// set to the survivor's position, so the probes, relation and early
    /// return are the pipeline's. The filter has no false negatives, so a
    /// rejected key is absent from the table; a false positive only costs a
    /// lookup that misses. `PIPE_FILTER_PLANT` also looks every rejected key
    /// up in the compact table (prefetched with its filter word) and
    /// discards the result, which must be `None`.
    #[inline(always)]
    #[allow(clippy::too_many_arguments)]
    fn scan_state128_filtered<const C: u8, const P: u8>(
        gf: &Gf2_128,
        fast: &FastBinaryCurve128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        index: &Index128,
        base: &Base128,
        target: FastPoint128,
        target_x: u128,
        state: &State128,
        scan: &mut StateScan128,
        probes: &mut u64,
        clock: &mut PhaseClock,
        split: &mut ExtractSplit,
    ) -> Option<Relation128> {
        let n = gf.n;
        let compact = index.compact.as_ref().expect("the compact root table");
        let filter = if P == PIPE_COMPACT {
            None
        } else {
            Some(index.filter.as_ref().expect("the root filter"))
        };
        scan.inputs.clear();
        for shift in 0..n {
            for &normal_root in &state.normal_roots {
                let absolute = basis.to_poly.apply(basis.rotate(normal_root, shift));
                scan.inputs.push((absolute, target_x));
            }
        }
        oc::bump(oc::FROBENIUS_X, (n as u64 - 1) * state.normal_roots.len() as u64);
        scan.batch.solve(gf, basis, solver, &scan.inputs);
        split.root_calls += scan.inputs.len() as u64;
        scan.keys.clear();
        for (candidate, result) in scan.batch.results.iter().enumerate() {
            let Some(partners) = *result else {
                continue;
            };
            for partner in partners {
                let (canonical, partner_shift) =
                    target_canonical::<C>(basis, basis.to_normal.apply(partner));
                match filter {
                    Some(filter) => {
                        filter.prefetch(canonical);
                        if P == PIPE_FILTER_PLANT {
                            compact.prefetch(canonical);
                        }
                    }
                    None => compact.prefetch(canonical),
                }
                scan.keys.push(ProbeKey128 {
                    canonical,
                    partner,
                    partner_shift,
                    candidate: candidate as u32,
                });
            }
        }
        scan.survivors.clear();
        let mut planted_found = 0u64;
        for (position, key) in scan.keys.iter().enumerate() {
            match filter {
                Some(filter) => {
                    if filter.contains(key.canonical) {
                        compact.prefetch(key.canonical);
                        scan.survivors.push(position as u32);
                    } else if P == PIPE_FILTER_PLANT {
                        planted_found += black_box(compact.get(black_box(key.canonical))).is_some() as u64;
                    }
                }
                None => scan.survivors.push(position as u32),
            }
        }
        split.planted_found += planted_found;
        let first = *probes;
        let roots_per_shift = state.normal_roots.len();
        for &position in &scan.survivors {
            let key = &scan.keys[position as usize];
            *probes = first + position as u64 + 1;
            split.filter_passes += 1;
            let Some(value) = compact.get(key.canonical) else {
                continue;
            };
            let candidate = key.candidate as usize;
            let shift = candidate / roots_per_shift;
            let left_x = index.shifted[state.left as usize][shift];
            let right_x =
                index.shifted[state.right as usize][(shift + state.relative as usize) % n as usize];
            let absolute = scan.inputs[candidate].0;
            let partner = key.partner;
            let partner_shift = key.partner_shift;
            let (left2, right2, relative2, stored_shift) = unpack(value);
            let left_shift2 = ((stored_shift + n - partner_shift) % n) as usize;
            let right_shift2 = (left_shift2 + relative2) % n as usize;
            let codes = [
                left_x,
                right_x,
                index.shifted[left2][left_shift2],
                index.shifted[right2][right_shift2],
            ];
            split.pdp += clock.lap();
            let lifted = lift128(fast, base, &codes, target);
            split.relation_check += clock.lap();
            split.relation_checks += 1;
            if let Some(point_indices) = lifted {
                return Some(Relation128 {
                    point_indices,
                    x_codes: codes,
                    intermediates: [absolute, partner],
                    probes: *probes,
                });
            }
        }
        *probes = first + scan.keys.len() as u64;
        None
    }

    #[cfg(test)]
    mod table_filter_tests {
        use super::*;

        fn small_instance(
            columns: usize,
        ) -> (FastBinaryCurve128, Gf2_128, NormalBasis128, S3Solver128, Base128, Vec<u128>) {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let b = gf.from_element(&curve.curve.b);
            let r = curve.subgroup_order.to_u64().unwrap();
            let (points, labels, reps, _) = construct_base128(&fast, &curve, b, columns, r);
            let mut by_x: HashMap<u128, Vec<usize>> = HashMap::new();
            for (i, point) in points.iter().enumerate() {
                by_x.entry(point.unwrap().0).or_default().push(i);
            }
            let reps: Vec<u128> = reps.iter().map(|p| p.unwrap()[0]).collect();
            let base = Base128 { points, labels, by_x, columns };
            let basis = NormalBasis128::new(&gf);
            let solver = S3Solver128::new(&gf, b);
            (fast, gf, basis, solver, base, reps)
        }

        fn mix(value: u64) -> u64 {
            mix_root_bloom(value.wrapping_add(0x9E37_79B9_7F4A_7C15))
        }

        #[test]
        fn compact_slot_round_trips_every_field_and_rejects_overflow() {
            for value in [0u64, pack(599, 599, 82, 82), pack(1, 2, 3, 4), pack(2047, 2047, 2047, 2047)] {
                let word = COMPACT_OCCUPIED | CompactRootTable128::compress(value) | COMPACT_KEY_MASK;
                assert_eq!(CompactRootTable128::expand(word), value);
                assert_eq!(word & COMPACT_KEY_MASK, COMPACT_KEY_MASK);
            }
            assert!(std::panic::catch_unwind(|| CompactRootTable128::compress(pack(2048, 0, 0, 0))).is_err());
            let mut table = CompactRootTable128::with_capacity(8);
            assert!(std::panic::catch_unwind(move || table.insert_if_absent(1u128 << 83, 0)).is_err());
        }

        #[test]
        fn layouts_store_the_same_map_and_the_filter_has_no_false_negatives() {
            let (_, gf, basis, solver, _, reps) = small_instance(9);
            let reference = build_index128_mode(&gf, &basis, &solver, &reps, TABLE_BASE, 28);
            assert!(reference.compact.is_none() && reference.filter.is_none());
            for (mode, bits) in [(TABLE_COMPACT, 28), (TABLE_FILTER, 28), (TABLE_FILTER, 14), (TABLE_FILTER_PLANT, 16)] {
                let index = build_index128_mode(&gf, &basis, &solver, &reps, mode, bits);
                assert_eq!(index.states.len(), reference.states.len());
                assert_eq!(index.root_entries(), reference.table.len);
                assert_eq!(index.table.len, 0);
                let compact = index.compact.as_ref().unwrap();
                assert_eq!(compact.slots.len(), reference.table.slots.len());
                assert_eq!(index.root_table_bytes() * 2, reference.root_table_bytes());
                for &(key, value) in &reference.table.slots {
                    if key != u128::MAX {
                        assert_eq!(compact.get(key), Some(value));
                        if let Some(filter) = &index.filter {
                            assert!(filter.contains(key), "filter false negative");
                        }
                    }
                }
                let mut rejected = 0u64;
                for trial in 0..200_000u64 {
                    let key = ((mix(trial) as u128) << 64 | mix(!trial) as u128) & basis.mask;
                    let expected = reference.table.get(key);
                    assert_eq!(compact.get(key), expected);
                    if let Some(filter) = &index.filter {
                        if !filter.contains(key) {
                            rejected += 1;
                            assert_eq!(expected, None);
                        }
                    }
                }
                assert_eq!(compact.get(1u128 << 100), None);
                if mode != TABLE_COMPACT {
                    assert!(rejected > 0);
                }
            }
        }

        #[test]
        fn every_layout_finds_the_pipelines_relation_with_the_same_probes() {
            let (fast, gf, basis, solver, base, reps) = small_instance(9);
            let reference = build_index128_mode(&gf, &basis, &solver, &reps, TABLE_BASE, 28);
            let compact = build_index128_mode(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28);
            let filtered = build_index128_mode(&gf, &basis, &solver, &reps, TABLE_FILTER, 28);
            let tiny = build_index128_mode(&gf, &basis, &solver, &reps, TABLE_FILTER, 13);
            let planted = build_index128_mode(&gf, &basis, &solver, &reps, TABLE_FILTER_PLANT, 15);
            let mut seed = 0x0123_4567_89AB_CDEFu64;
            let mut false_positive_probes = 0u64;
            let mut solved = 0usize;
            for trial in 0..24u64 {
                let mut pick = || {
                    seed = mix(seed ^ trial);
                    (seed % base.points.len() as u64) as usize
                };
                let mut target = base.points[pick()];
                for _ in 0..3 {
                    target = fast.add(target, base.points[pick()]);
                }
                let Some((tx, ty)) = target else { continue };
                let start = mix((tx ^ ty.rotate_left(29)) as u64) as usize;
                macro_rules! run {
                    ($c:expr, $o:expr, $p:expr, $index:expr) => {{
                        let mut clock = PhaseClock::start();
                        let mut split = ExtractSplit::default();
                        let relation = extract128::<{ $c }, { $o }, { $p }>(
                            &gf, &fast, &basis, &solver, $index, &base, target, start, &mut clock,
                            &mut split,
                        );
                        (relation.map(|r| (r.point_indices, r.x_codes, r.intermediates, r.probes)),
                         split.filter_passes, split.planted_found, split.relation_checks)
                    }};
                }
                macro_rules! compare {
                    ($c:expr, $o:expr) => {{
                        let (want, _, _, checks) = run!($c, $o, PIPE_PREFETCH, &reference);
                        let (off, _, _, _) = run!($c, $o, PIPE_OFF, &reference);
                        assert_eq!(want, off);
                        let want = want.expect("a planted four-point target decomposes");
                        let probes = want.3;
                        for (got, passes, found, got_checks) in [
                            run!($c, $o, PIPE_COMPACT, &compact),
                            run!($c, $o, PIPE_FILTER, &filtered),
                            run!($c, $o, PIPE_FILTER, &tiny),
                            run!($c, $o, PIPE_FILTER_PLANT, &planted),
                        ] {
                            assert_eq!(got, Some(want), "relation and probes differ");
                            assert_eq!(found, 0, "a rejected key was found in the table");
                            assert_eq!(got_checks, checks);
                            assert!(passes >= checks && passes <= probes);
                        }
                        let (_, tiny_passes, _, _) = run!($c, $o, PIPE_FILTER, &tiny);
                        false_positive_probes += tiny_passes - checks;
                        solved += 1;
                    }};
                }
                compare!(CANON_LIFT, ORDER_FEISTEL);
                compare!(CANON_LIFT, ORDER_LEFT_MAJOR);
                compare!(CANON_FULL, ORDER_FEISTEL);
            }
            assert!(solved >= 60);
            assert!(false_positive_probes > 0, "the tiny filter should produce false positives");
        }
    }


    // koblitz-n83-rankcut-20261016: the rank stage's partner roots by point
    // addition (KIC_RANK_SOLVE). `PIPE_PADD_SWAPPED` emits each pair in the
    // other order; the tests use it to force the exact-order resolution.
    const PIPE_PADD: u8 = 5;
    const PIPE_PADD_PLANT: u8 = 6;
    const PIPE_PADD_SWAPPED: u8 = 7;

    static PADD_FALLBACK_STATES: AtomicU64 = AtomicU64::new(0);
    static PADD_IRREGULAR_INPUTS: AtomicU64 = AtomicU64::new(0);
    static PADD_RESOLVED_HITS: AtomicU64 = AtomicU64::new(0);
    static PADD_SWAPPED_PAIRS: AtomicU64 = AtomicU64::new(0);
    static PADD_PLANT_CHECKED: AtomicU64 = AtomicU64::new(0);

    /// `KIC_RANK_SOLVE`: the rank stage's partner-root solve.
    fn rank_solve_from_env() -> (u8, &'static str) {
        match std::env::var("KIC_RANK_SOLVE").as_deref() {
            Err(_) | Ok("") | Ok("s3") => (PIPE_COMPACT, "s3"),
            Ok("padd") => (PIPE_PADD, "padd"),
            Ok("padd_plant") => (PIPE_PADD_PLANT, "padd_plant"),
            Ok(other) => panic!("unknown KIC_RANK_SOLVE {other}"),
        }
    }

    /// Per-state scratch of [`scan_state128_padd`].
    struct PaddScratch128 {
        ys: Vec<u128>,
        prefix: Vec<u128>,
        inverse: Vec<u128>,
        regular: Vec<bool>,
        pair_start: Vec<u32>,
    }

    impl PaddScratch128 {
        fn with_capacity(entries: usize) -> Self {
            Self {
                ys: Vec::with_capacity(entries),
                prefix: Vec::with_capacity(entries),
                inverse: Vec::with_capacity(entries),
                regular: Vec::with_capacity(entries),
                pair_start: Vec::with_capacity(entries),
            }
        }
    }

    /// The normal-basis y of a point of E with normal-basis x `xn`
    /// (`y = x * HT(x + a + b / x^2)`), or `None` when `x = 0` or `x` is not
    /// the x of a point of E over the field.
    #[inline(always)]
    fn padd_root_y(
        gf: &Gf2_128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        a: u128,
        xn: u128,
    ) -> Option<u128> {
        let xp = basis.to_poly.apply(xn);
        if xp == 0 {
            return None;
        }
        let xi = invert128(gf, basis, xp);
        let rhs = xp ^ a ^ fmul(&gf, solver.b, fsqr(&gf, xi));
        if (rhs & solver.trace_mask).count_ones() & 1 == 1 {
            return None;
        }
        let u = solver.half_trace.apply(rhs);
        Some(basis.to_normal.apply(fmul(&gf, xp, u)))
    }

    /// [`scan_state128_filtered`] (`PIPE_COMPACT`) with the partner roots by
    /// point addition: the same candidates (shift outer, stored root inner),
    /// the same keys and probe positions, the same first hit and relation.
    /// At every root-table hit the candidate's S3 pair is recomputed and the
    /// pair is evaluated in the S3 order, so the result does not depend on
    /// the emission order.
    #[inline(always)]
    #[allow(clippy::too_many_arguments)]
    fn scan_state128_padd<const C: u8, const P: u8>(
        gf: &Gf2_128,
        fast: &FastBinaryCurve128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        index: &Index128,
        base: &Base128,
        target: FastPoint128,
        target_x: u128,
        state: &State128,
        scan: &mut StateScan128,
        probes: &mut u64,
        clock: &mut PhaseClock,
        split: &mut ExtractSplit,
    ) -> Option<Relation128> {
        let n = gf.n;
        let compact = index.compact.as_ref().expect("the compact root table");
        let (tx, ty) = target.expect("a target point");
        debug_assert_eq!(tx, target_x);
        let a = fast.a;
        let roots = state.normal_roots.len();
        let mut yn = [0u128; 2];
        for (k, &root) in state.normal_roots.iter().enumerate() {
            match padd_root_y(gf, basis, solver, a, root) {
                Some(y) => yn[k] = y,
                None => {
                    PADD_FALLBACK_STATES.fetch_add(1, Ordering::Relaxed);
                    return scan_state128_filtered::<C, PIPE_COMPACT>(
                        gf, fast, basis, solver, index, base, target, target_x, state, scan,
                        probes, clock, split,
                    );
                }
            }
        }
        scan.inputs.clear();
        let pad = &mut scan.padd;
        pad.ys.clear();
        pad.prefix.clear();
        pad.regular.clear();
        let mut product = 1u128;
        for shift in 0..n {
            for k in 0..roots {
                let xs = basis.to_poly.apply(basis.rotate(state.normal_roots[k], shift));
                let ys = basis.to_poly.apply(basis.rotate(yn[k], shift));
                // Exactly the S3 batch's exceptional inputs (zero denominator).
                let regular = xs != tx && xs != 0 && tx != 0;
                scan.inputs.push((xs, tx));
                pad.ys.push(ys);
                pad.prefix.push(product);
                pad.regular.push(regular);
                if regular {
                    product = fmul(&gf, product, xs ^ tx);
                }
            }
        }
        split.root_calls += scan.inputs.len() as u64;
        let count = scan.inputs.len();
        pad.inverse.clear();
        pad.inverse.resize(count, 0);
        // A product of non-zero field elements is non-zero.
        let mut inverse = invert128(gf, basis, product);
        for i in (0..count).rev() {
            if pad.regular[i] {
                pad.inverse[i] = fmul(&gf, inverse, pad.prefix[i]);
                inverse = fmul(&gf, inverse, scan.inputs[i].0 ^ tx);
            }
        }
        let normal_c = basis.to_normal.apply(tx ^ a);
        scan.keys.clear();
        pad.pair_start.clear();
        for i in 0..count {
            let xs = scan.inputs[i].0;
            let pair: [u128; 2] = if pad.regular[i] {
                oc::bump(oc::S3_SOLVES, 1);
                let lambda = basis.to_normal.apply(fmul(&gf, ty ^ pad.ys[i], pad.inverse[i]));
                let lambda2 = lambda ^ basis.to_normal.apply(fmul(&gf, xs, pad.inverse[i]));
                let c = normal_c ^ basis.rotate(state.normal_roots[i % roots], (i / roots) as u32);
                let plus = basis.rotate(lambda, 1) ^ lambda ^ c;
                let minus = basis.rotate(lambda2, 1) ^ lambda2 ^ c;
                if P == PIPE_PADD_SWAPPED { [plus, minus] } else { [minus, plus] }
            } else {
                PADD_IRREGULAR_INPUTS.fetch_add(1, Ordering::Relaxed);
                match solver.roots(gf, basis, xs, tx) {
                    Some([first, second]) => {
                        [basis.to_normal.apply(first), basis.to_normal.apply(second)]
                    }
                    None => {
                        pad.pair_start.push(u32::MAX);
                        continue;
                    }
                }
            };
            pad.pair_start.push(scan.keys.len() as u32);
            for partner in pair {
                let (canonical, partner_shift) = target_canonical::<C>(basis, partner);
                compact.prefetch(canonical);
                scan.keys.push(ProbeKey128 {
                    canonical,
                    partner,
                    partner_shift,
                    candidate: i as u32,
                });
            }
        }
        if P == PIPE_PADD_PLANT {
            // The removed work, redone and discarded: the S3 batch solve and
            // both partners' normal-basis maps, compared with the pair.
            scan.batch.solve(gf, basis, solver, &scan.inputs);
            for (i, result) in scan.batch.results.iter().enumerate() {
                let start = pad.pair_start[i];
                match *result {
                    Some([first, second]) => {
                        let s3 = [
                            black_box(basis.to_normal.apply(first)),
                            black_box(basis.to_normal.apply(second)),
                        ];
                        assert_ne!(start, u32::MAX, "S3 found a pair the point addition did not");
                        let got = [scan.keys[start as usize].partner, scan.keys[start as usize + 1].partner];
                        assert!(
                            got == s3 || got == [s3[1], s3[0]],
                            "point-addition partners differ from the S3 roots"
                        );
                    }
                    None => assert_eq!(start, u32::MAX, "point addition found a pair S3 did not"),
                }
            }
            PADD_PLANT_CHECKED.fetch_add(count as u64, Ordering::Relaxed);
        }
        let first = *probes;
        let passes = split.filter_passes;
        let len = scan.keys.len();
        let mut position = 0usize;
        while position < len {
            *probes = first + position as u64 + 1;
            split.filter_passes = passes + position as u64 + 1;
            if compact.get(scan.keys[position].canonical).is_none() {
                position += 1;
                continue;
            }
            // First hit in this candidate's pair: evaluate the pair in the S3
            // order, at the S3 loop's probe positions.
            let candidate = scan.keys[position].candidate as usize;
            let start = pad.pair_start[candidate] as usize;
            let order = if pad.regular[candidate] {
                PADD_RESOLVED_HITS.fetch_add(1, Ordering::Relaxed);
                let exact = solver
                    .roots(gf, basis, scan.inputs[candidate].0, tx)
                    .expect("the S3 roots of a regular candidate");
                let emitted = [
                    basis.to_poly.apply(scan.keys[start].partner),
                    basis.to_poly.apply(scan.keys[start + 1].partner),
                ];
                if emitted == exact {
                    [start, start + 1]
                } else {
                    assert_eq!([emitted[1], emitted[0]], exact,
                               "point-addition partners differ from the S3 roots");
                    PADD_SWAPPED_PAIRS.fetch_add(1, Ordering::Relaxed);
                    [start + 1, start]
                }
            } else {
                [start, start + 1]
            };
            for (rank, &at) in order.iter().enumerate() {
                let exact_position = start + rank;
                if at < position {
                    // Emitted before this hit and already looked up: a miss.
                    continue;
                }
                *probes = first + exact_position as u64 + 1;
                split.filter_passes = passes + exact_position as u64 + 1;
                let key = scan.keys[at];
                let Some(value) = compact.get(key.canonical) else {
                    continue;
                };
                let shift = candidate / roots;
                let left_x = index.shifted[state.left as usize][shift];
                let right_x =
                    index.shifted[state.right as usize][(shift + state.relative as usize) % n as usize];
                let (left2, right2, relative2, stored_shift) = unpack(value);
                let left_shift2 = ((stored_shift + n - key.partner_shift) % n) as usize;
                let right_shift2 = (left_shift2 + relative2) % n as usize;
                let codes = [
                    left_x,
                    right_x,
                    index.shifted[left2][left_shift2],
                    index.shifted[right2][right_shift2],
                ];
                split.pdp += clock.lap();
                let lifted = lift128(fast, base, &codes, target);
                split.relation_check += clock.lap();
                split.relation_checks += 1;
                if let Some(point_indices) = lifted {
                    return Some(Relation128 {
                        point_indices,
                        x_codes: codes,
                        intermediates: [scan.inputs[candidate].0, basis.to_poly.apply(key.partner)],
                        probes: *probes,
                    });
                }
            }
            position = start + 2;
        }
        *probes = first + len as u64;
        split.filter_passes = passes + len as u64;
        None
    }

    #[cfg(test)]
    mod rankcut_tests {
        use super::*;

        fn small_instance(
            columns: usize,
        ) -> (FastBinaryCurve128, Gf2_128, NormalBasis128, S3Solver128, Base128, Vec<u128>) {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let b = gf.from_element(&curve.curve.b);
            let r = curve.subgroup_order.to_u64().unwrap();
            let (points, labels, reps, _) = construct_base128(&fast, &curve, b, columns, r);
            let mut by_x: HashMap<u128, Vec<usize>> = HashMap::new();
            for (i, point) in points.iter().enumerate() {
                by_x.entry(point.unwrap().0).or_default().push(i);
            }
            let reps: Vec<u128> = reps.iter().map(|p| p.unwrap()[0]).collect();
            let base = Base128 { points, labels, by_x, columns };
            let basis = NormalBasis128::new(&gf);
            let solver = S3Solver128::new(&gf, b);
            (fast, gf, basis, solver, base, reps)
        }

        #[test]
        fn point_addition_pairs_are_the_s3_roots() {
            let (fast, gf, basis, solver, base, _) = small_instance(9);
            let mut seed = 0x0123_4567_89AB_CDEFu64;
            let mut checked = 0u64;
            let mut first_is_minus = 0u64;
            for _ in 0..4000 {
                seed = digest_mix64(seed);
                let r = base.points[(seed % base.points.len() as u64) as usize];
                seed = digest_mix64(seed);
                let t = fast.add(r, base.points[(seed % base.points.len() as u64) as usize]);
                let (Some((rx, ry)), Some((tx, ty))) = (r, t) else { continue };
                if rx == tx {
                    continue;
                }
                let exact = solver.roots(&gf, &basis, rx, tx).expect("S3 roots of two points");
                let plus = fast.add(t, r).unwrap().0;
                let minus = fast.add(t, FastBinaryCurve128::neg(r)).unwrap().0;
                assert!(exact == [plus, minus] || exact == [minus, plus]);
                first_is_minus += (exact[0] == minus) as u64;
                // The recovered y gives the same pair (either sign of y).
                let y = basis.to_poly.apply(padd_root_y(&gf, &basis, &solver, fast.a, basis.to_normal.apply(rx)).unwrap());
                assert!(y == ry || y == (rx ^ ry));
                let _ = ty;
                checked += 1;
            }
            assert!(checked > 3000);
            eprintln!("first root is x(T - R) in {first_is_minus} of {checked}");
        }

        #[test]
        fn padd_loops_find_the_s3_relation_with_the_s3_probes() {
            let (fast, gf, basis, solver, base, reps) = small_instance(9);
            const FOLDED: IndexMode128 = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_SELECTED };
            let stack = build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28, FOLDED);
            let unfolded =
                build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28, IndexMode128::UNFOLDED);
            let mut seed = 0xA076_1D64_78BD_642Fu64;
            let mut solved = 0usize;
            let swapped_before = PADD_SWAPPED_PAIRS.load(Ordering::Relaxed);
            for trial in 0..40u64 {
                let mut pick = || {
                    seed = digest_mix64(seed.wrapping_add(trial));
                    (seed % base.points.len() as u64) as usize
                };
                let mut target = base.points[pick()];
                for _ in 0..3 {
                    target = fast.add(target, base.points[pick()]);
                }
                let Some((tx, ty)) = target else { continue };
                let start = digest_mix64((tx ^ ty.rotate_left(29)) as u64) as usize;
                macro_rules! run {
                    ($o:expr, $p:expr, $index:expr) => {{
                        let mut clock = PhaseClock::start();
                        let mut split = ExtractSplit::default();
                        let relation = extract128::<CANON_LIFT, { $o }, { $p }>(
                            &gf, &fast, &basis, &solver, $index, &base, target, start, &mut clock,
                            &mut split,
                        );
                        (relation.map(|r| ((r.point_indices, r.x_codes, r.intermediates), r.probes)),
                         split.root_calls, split.relation_checks)
                    }};
                }
                for (order, index) in [(ORDER_FEISTEL, &stack), (ORDER_LEFT_MAJOR, &stack), (ORDER_FEISTEL, &unfolded)] {
                    macro_rules! compare {
                        ($o:expr) => {{
                            let want = run!($o, PIPE_COMPACT, index);
                            assert!(want.0.is_some(), "a planted four-point target decomposes");
                            for got in [run!($o, PIPE_PADD, index), run!($o, PIPE_PADD_PLANT, index),
                                        run!($o, PIPE_PADD_SWAPPED, index)] {
                                assert_eq!(got, want, "a point-addition loop differs from the S3 loop");
                            }
                            solved += 1;
                        }};
                    }
                    if order == ORDER_FEISTEL { compare!(ORDER_FEISTEL) } else { compare!(ORDER_LEFT_MAJOR) }
                }
            }
            assert!(solved >= 100);
            assert!(PADD_SWAPPED_PAIRS.load(Ordering::Relaxed) > swapped_before,
                    "the swapped loop must exercise the exact-order resolution");
            assert!(PADD_PLANT_CHECKED.load(Ordering::Relaxed) > 0);
        }
    }


    // koblitz-n83-rankprobe-20261019: the rank-cut loop in the target's
    // Frobenius frame (KIC_RANK_SOLVE=frame). `PIPE_FRAME_SWAPPED` emits
    // each pair in the other order; the tests use it to force the
    // exact-order resolution.
    const PIPE_FRAME: u8 = 8;
    const PIPE_FRAME_PLANT: u8 = 9;
    const PIPE_FRAME_SWAPPED: u8 = 10;
    const FRAME_ROOTS: usize = 2;

    static FRAME_BUILDS: AtomicU64 = AtomicU64::new(0);
    static FRAME_PLANT_CHECKED: AtomicU64 = AtomicU64::new(0);

    /// `KIC_RANK_SOLVE` values of this experiment; `None` defers to the
    /// rank-cut selector.
    fn rank_solve_frame_from_env() -> Option<(u8, &'static str)> {
        match std::env::var("KIC_RANK_SOLVE").as_deref() {
            Ok("frame") => Some((PIPE_FRAME, "frame")),
            Ok("frame_plant") => Some((PIPE_FRAME_PLANT, "frame_plant")),
            _ => None,
        }
    }

    /// Per-target frame and per-state scratch of [`scan_state128_frame`]:
    /// for every shift `s`, the polynomial-basis `x` and `y` of
    /// `T_s = phi^(-s)(T)` and the normal-basis `x(T_s) + a`.
    struct FrameScratch128 {
        target: Option<(u128, u128)>,
        x: Vec<u128>,
        y: Vec<u128>,
        normal_c: Vec<u128>,
        prefix: Vec<u128>,
        inverse: Vec<u128>,
        regular: Vec<bool>,
        pair_start: Vec<u32>,
        check: Vec<ProbeKey128>,
    }

    impl FrameScratch128 {
        fn with_capacity(entries: usize) -> Self {
            Self {
                target: None,
                x: Vec::with_capacity(entries),
                y: Vec::with_capacity(entries),
                normal_c: Vec::with_capacity(entries),
                prefix: Vec::with_capacity(entries),
                inverse: Vec::with_capacity(entries),
                regular: Vec::with_capacity(entries),
                pair_start: Vec::with_capacity(entries),
                check: Vec::with_capacity(2 * entries),
            }
        }
    }

    /// Tabulate the frame of target `(tx, ty)` unless it is already the
    /// scratch's: `x(T_s)`, `y(T_s)` (polynomial basis) and
    /// `x(T_s) + a` (normal basis) for `s = 0 .. n - 1`.
    fn frame_build128(frame: &mut FrameScratch128, basis: &NormalBasis128, a: u128, tx: u128, ty: u128) {
        if frame.target == Some((tx, ty)) {
            return;
        }
        FRAME_BUILDS.fetch_add(1, Ordering::Relaxed);
        let n = basis.n;
        oc::bump(oc::FROBENIUS_X, 2 * (n as u64 - 1));
        let normal_x = basis.to_normal.apply(tx);
        let normal_y = basis.to_normal.apply(ty);
        let normal_a = basis.to_normal.apply(a);
        frame.x.clear();
        frame.y.clear();
        frame.normal_c.clear();
        for shift in 0..n {
            let back = (n - shift) % n;
            let xs = basis.rotate(normal_x, back);
            frame.x.push(basis.to_poly.apply(xs));
            frame.y.push(basis.to_poly.apply(basis.rotate(normal_y, back)));
            frame.normal_c.push(xs ^ normal_a);
        }
        frame.target = Some((tx, ty));
    }

    /// The polynomial-basis `(x, y)` of a point of E with normal-basis x
    /// `xn`: [`padd_root_y`]'s y (`y = x * HT(x + a + b / x^2)`) before its
    /// normal-basis map, and `None` exactly when [`padd_root_y`] is `None`.
    #[inline(always)]
    fn frame_root_xy(
        gf: &Gf2_128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        a: u128,
        xn: u128,
    ) -> Option<(u128, u128)> {
        oc::bump(oc::EC_LIFT_X, 1);
        let xp = basis.to_poly.apply(xn);
        if xp == 0 {
            return None;
        }
        let xi = invert128(gf, basis, xp);
        let rhs = xp ^ a ^ fmul(&gf, solver.b, fsqr(&gf, xi));
        if (rhs & solver.trace_mask).count_ones() & 1 == 1 {
            return None;
        }
        oc::bump(oc::FIELD_HALF_TRACE, 1);
        let u = solver.half_trace.apply(rhs);
        Some((xp, fmul(&gf, xp, u)))
    }

    /// The rank-cut loop's key derivation ([`scan_state128_padd`] up to its
    /// lookups), verbatim in its arithmetic, into `out`; the planted
    /// control's redone work. `false` when a root fails the curve check.
    #[inline(always)]
    #[allow(clippy::too_many_arguments)]
    fn rankcut_keys128<const C: u8>(
        gf: &Gf2_128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        a: u128,
        target: (u128, u128),
        state: &State128,
        inputs: &mut Vec<(u128, u128)>,
        pad: &mut PaddScratch128,
        out: &mut Vec<ProbeKey128>,
    ) -> bool {
        let n = gf.n;
        let (tx, ty) = target;
        let roots = state.normal_roots.len();
        let mut yn = [0u128; 2];
        for (k, &root) in state.normal_roots.iter().enumerate() {
            match padd_root_y(gf, basis, solver, a, root) {
                Some(y) => yn[k] = y,
                None => return false,
            }
        }
        inputs.clear();
        pad.ys.clear();
        pad.prefix.clear();
        pad.regular.clear();
        let mut product = 1u128;
        for shift in 0..n {
            for k in 0..roots {
                let xs = basis.to_poly.apply(basis.rotate(state.normal_roots[k], shift));
                let ys = basis.to_poly.apply(basis.rotate(yn[k], shift));
                let regular = xs != tx && xs != 0 && tx != 0;
                inputs.push((xs, tx));
                pad.ys.push(ys);
                pad.prefix.push(product);
                pad.regular.push(regular);
                if regular {
                    product = fmul(&gf, product, xs ^ tx);
                }
            }
        }
        let count = inputs.len();
        pad.inverse.clear();
        pad.inverse.resize(count, 0);
        let mut inverse = invert128(gf, basis, product);
        for i in (0..count).rev() {
            if pad.regular[i] {
                pad.inverse[i] = fmul(&gf, inverse, pad.prefix[i]);
                inverse = fmul(&gf, inverse, inputs[i].0 ^ tx);
            }
        }
        let normal_c = basis.to_normal.apply(tx ^ a);
        out.clear();
        for i in 0..count {
            let xs = inputs[i].0;
            let pair: [u128; 2] = if pad.regular[i] {
                oc::bump(oc::S3_SOLVES, 1);
                let lambda = basis.to_normal.apply(fmul(&gf, ty ^ pad.ys[i], pad.inverse[i]));
                let lambda2 = lambda ^ basis.to_normal.apply(fmul(&gf, xs, pad.inverse[i]));
                let c = normal_c ^ basis.rotate(state.normal_roots[i % roots], (i / roots) as u32);
                let plus = basis.rotate(lambda, 1) ^ lambda ^ c;
                let minus = basis.rotate(lambda2, 1) ^ lambda2 ^ c;
                [minus, plus]
            } else {
                match solver.roots(gf, basis, xs, tx) {
                    Some([first, second]) => {
                        [basis.to_normal.apply(first), basis.to_normal.apply(second)]
                    }
                    None => continue,
                }
            };
            for partner in pair {
                let (canonical, partner_shift) = target_canonical::<C>(basis, partner);
                out.push(ProbeKey128 { canonical, partner, partner_shift, candidate: i as u32 });
            }
        }
        true
    }

    /// [`scan_state128_padd`] (`PIPE_PADD`) in the target's Frobenius frame:
    /// the same candidates (shift outer, stored root inner), the same
    /// partner words in the same order, so the same keys and probe
    /// positions, the same first hit and relation. At every root-table hit
    /// the candidate's S3 input is formed and the rank-cut loop's
    /// exact-order resolution runs unchanged.
    #[inline(always)]
    #[allow(clippy::too_many_arguments)]
    fn scan_state128_frame<const C: u8, const P: u8>(
        gf: &Gf2_128,
        fast: &FastBinaryCurve128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        index: &Index128,
        base: &Base128,
        target: FastPoint128,
        target_x: u128,
        state: &State128,
        scan: &mut StateScan128,
        probes: &mut u64,
        clock: &mut PhaseClock,
        split: &mut ExtractSplit,
    ) -> Option<Relation128> {
        let n = gf.n;
        let compact = index.compact.as_ref().expect("the compact root table");
        let (tx, ty) = target.expect("a target point");
        debug_assert_eq!(tx, target_x);
        let a = fast.a;
        assert_eq!(state.normal_roots.len(), FRAME_ROOTS);
        let mut xk = [0u128; FRAME_ROOTS];
        let mut yk = [0u128; FRAME_ROOTS];
        for (k, &root) in state.normal_roots.iter().enumerate() {
            match frame_root_xy(gf, basis, solver, a, root) {
                Some((x, y)) => {
                    xk[k] = x;
                    yk[k] = y;
                }
                None => {
                    PADD_FALLBACK_STATES.fetch_add(1, Ordering::Relaxed);
                    return scan_state128_filtered::<C, PIPE_COMPACT>(
                        gf, fast, basis, solver, index, base, target, target_x, state, scan,
                        probes, clock, split,
                    );
                }
            }
        }
        frame_build128(&mut scan.frame, basis, a, tx, ty);
        let fr = &mut scan.frame;
        fr.prefix.clear();
        fr.regular.clear();
        let mut product = 1u128;
        for shift in 0..n as usize {
            let xt = fr.x[shift];
            for k in 0..FRAME_ROOTS {
                // The rank-cut loop's exceptional inputs: x(R_k)^(2^s) = x(T)
                // iff x(R_k) = x(T_s); x(R_k)^(2^s) = 0 iff x(R_k) = 0;
                // x(T) = 0 iff x(T_s) = 0.
                let regular = xk[k] != xt && xk[k] != 0 && xt != 0;
                fr.prefix.push(product);
                fr.regular.push(regular);
                if regular {
                    product = fmul(&gf, product, xk[k] ^ xt);
                }
            }
        }
        let count = fr.regular.len();
        split.root_calls += count as u64;
        fr.inverse.clear();
        fr.inverse.resize(count, 0);
        // A product of non-zero field elements is non-zero.
        let mut inverse = invert128(gf, basis, product);
        for i in (0..count).rev() {
            if fr.regular[i] {
                fr.inverse[i] = fmul(&gf, inverse, fr.prefix[i]);
                inverse = fmul(&gf, inverse, xk[i % FRAME_ROOTS] ^ fr.x[i / FRAME_ROOTS]);
            }
        }
        scan.keys.clear();
        fr.pair_start.clear();
        // koblitz-n83-rankfinder-20261021 (C7): with lift_scan keys at n = 83
        // the partner words are pushed in the parent's order and keyed eight
        // at a time by the linear run finder (lift_scan's key and shift for
        // every word); the at most seven left at the end take the parent's
        // call. Every key is complete before the first lookup.
        let linear = C == CANON_LIFT && n == 83;
        let mut keyed = 0usize;
        for shift in 0..n as usize {
            for k in 0..FRAME_ROOTS {
                let i = shift * FRAME_ROOTS + k;
                let pair: [u128; 2] = if fr.regular[i] {
                    oc::bump(oc::S3_SOLVES, 1);
                    oc::bump(oc::FROBENIUS_X, if shift != 0 { 2 } else { 0 });
                    let inverse = fr.inverse[i];
                    let lambda = basis.to_normal.apply(fmul(&gf, fr.y[shift] ^ yk[k], inverse));
                    let lambda2 = lambda ^ basis.to_normal.apply(fmul(&gf, xk[k], inverse));
                    let c = fr.normal_c[shift] ^ state.normal_roots[k];
                    // x(T_s +- R_k) in the normal basis, then phi^s.
                    let plus = basis.rotate(basis.rotate(lambda, 1) ^ lambda ^ c, shift as u32);
                    let minus = basis.rotate(basis.rotate(lambda2, 1) ^ lambda2 ^ c, shift as u32);
                    if P == PIPE_FRAME_SWAPPED { [plus, minus] } else { [minus, plus] }
                } else {
                    PADD_IRREGULAR_INPUTS.fetch_add(1, Ordering::Relaxed);
                    let xs = basis.to_poly.apply(basis.rotate(state.normal_roots[k], shift as u32));
                    match solver.roots(gf, basis, xs, tx) {
                        Some([first, second]) => {
                            [basis.to_normal.apply(first), basis.to_normal.apply(second)]
                        }
                        None => {
                            fr.pair_start.push(u32::MAX);
                            continue;
                        }
                    }
                };
                fr.pair_start.push(scan.keys.len() as u32);
                if linear {
                    for partner in pair {
                        scan.keys.push(ProbeKey128 { canonical: 0, partner, partner_shift: 0, candidate: i as u32 });
                    }
                    if scan.keys.len() - keyed >= RANK_PROBE_LANES {
                        let chunk = &mut scan.keys[keyed..keyed + RANK_PROBE_LANES];
                        let words: [u128; RANK_PROBE_LANES] = std::array::from_fn(|lane| chunk[lane].partner);
                        let keys = lift_linear_lanes8::<83>(&words);
                        for (key, (canonical, partner_shift)) in chunk.iter_mut().zip(keys) {
                            compact.prefetch(canonical);
                            key.canonical = canonical;
                            key.partner_shift = partner_shift;
                        }
                        keyed += RANK_PROBE_LANES;
                    }
                    continue;
                }
                for partner in pair {
                    let (canonical, partner_shift) = target_canonical::<C>(basis, partner);
                    compact.prefetch(canonical);
                    scan.keys.push(ProbeKey128 {
                        canonical,
                        partner,
                        partner_shift,
                        candidate: i as u32,
                    });
                }
            }
        }
        if linear {
            for key in &mut scan.keys[keyed..] {
                let (canonical, partner_shift) = target_canonical::<C>(basis, key.partner);
                compact.prefetch(canonical);
                key.canonical = canonical;
                key.partner_shift = partner_shift;
            }
        }
        if P == PIPE_FRAME_PLANT {
            // The removed work, redone and discarded: the rank-cut loop's
            // key derivation on every candidate, compared key by key.
            let complete = rankcut_keys128::<C>(
                gf, basis, solver, a, (tx, ty), state, &mut scan.inputs, &mut scan.padd, &mut fr.check,
            );
            assert!(complete, "a root the frame accepted failed the rank-cut curve check");
            assert_eq!(fr.check.len(), scan.keys.len(), "frame and rank-cut key counts differ");
            for (got, want) in scan.keys.iter().zip(&fr.check) {
                assert!(
                    black_box(got.canonical) == want.canonical
                        && got.partner == want.partner
                        && got.partner_shift == want.partner_shift
                        && got.candidate == want.candidate,
                    "frame keys differ from the rank-cut keys"
                );
            }
            FRAME_PLANT_CHECKED.fetch_add(count as u64, Ordering::Relaxed);
        }
        let first = *probes;
        let passes = split.filter_passes;
        let len = scan.keys.len();
        let mut position = 0usize;
        while position < len {
            *probes = first + position as u64 + 1;
            split.filter_passes = passes + position as u64 + 1;
            if compact.get(scan.keys[position].canonical).is_none() {
                position += 1;
                continue;
            }
            // First hit in this candidate's pair: form its S3 input and
            // evaluate the pair in the S3 order, at the S3 loop's probe
            // positions (the rank-cut loop's resolution).
            let candidate = scan.keys[position].candidate as usize;
            let shift = candidate / FRAME_ROOTS;
            let xs = basis.to_poly.apply(basis.rotate(state.normal_roots[candidate % FRAME_ROOTS], shift as u32));
            let start = fr.pair_start[candidate] as usize;
            let order = if fr.regular[candidate] {
                PADD_RESOLVED_HITS.fetch_add(1, Ordering::Relaxed);
                let exact = solver
                    .roots(gf, basis, xs, tx)
                    .expect("the S3 roots of a regular candidate");
                let emitted = [
                    basis.to_poly.apply(scan.keys[start].partner),
                    basis.to_poly.apply(scan.keys[start + 1].partner),
                ];
                if emitted == exact {
                    [start, start + 1]
                } else {
                    assert_eq!([emitted[1], emitted[0]], exact,
                               "frame partners differ from the S3 roots");
                    PADD_SWAPPED_PAIRS.fetch_add(1, Ordering::Relaxed);
                    [start + 1, start]
                }
            } else {
                [start, start + 1]
            };
            for (rank, &at) in order.iter().enumerate() {
                let exact_position = start + rank;
                if at < position {
                    // Emitted before this hit and already looked up: a miss.
                    continue;
                }
                *probes = first + exact_position as u64 + 1;
                split.filter_passes = passes + exact_position as u64 + 1;
                let key = scan.keys[at];
                let Some(value) = compact.get(key.canonical) else {
                    continue;
                };
                let left_x = index.shifted[state.left as usize][shift];
                let right_x =
                    index.shifted[state.right as usize][(shift + state.relative as usize) % n as usize];
                let (left2, right2, relative2, stored_shift) = unpack(value);
                let left_shift2 = ((stored_shift + n - key.partner_shift) % n) as usize;
                let right_shift2 = (left_shift2 + relative2) % n as usize;
                let codes = [
                    left_x,
                    right_x,
                    index.shifted[left2][left_shift2],
                    index.shifted[right2][right_shift2],
                ];
                split.pdp += clock.lap();
                let lifted = lift128(fast, base, &codes, target);
                split.relation_check += clock.lap();
                split.relation_checks += 1;
                if let Some(point_indices) = lifted {
                    return Some(Relation128 {
                        point_indices,
                        x_codes: codes,
                        intermediates: [xs, basis.to_poly.apply(key.partner)],
                        probes: *probes,
                    });
                }
            }
            position = start + 2;
        }
        *probes = first + len as u64;
        split.filter_passes = passes + len as u64;
        None
    }

    #[cfg(test)]
    mod closure_tests {
        use super::*;

        /// alpha(P) = [a]P + [b]phi(P) is [(a + b lambda) mod r]P for every
        /// norm <= 64 multiplier (a odd, a > 0), in the producer's arithmetic.
        #[test]
        fn closure_multiplier_is_its_label() {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let b = gf.from_element(&curve.curve.b);
            let r = curve.subgroup_order.to_u64().unwrap();
            let lambda = curve.lambda.to_u64().unwrap();
            let (_, _, reps, _) = construct_base128(&fast, &curve, b, 3, r);
            let mut checked = 0;
            for rep in reps {
                let p: FastPoint128 = rep.map(|[x, y]| (x, y));
                let phi = p.map(|(x, y)| (fsqr(&gf, x), fsqr(&gf, y)));
                for a in (1i64..=7).step_by(2) {
                    for bb in -6i64..=6 {
                        if a * a + a * bb + 2 * bb * bb > 64 {
                            continue;
                        }
                        let pa = fast.scalar_mul(p, &BigUint::from(a as u64));
                        let pb = fast.scalar_mul(phi, &BigUint::from(bb.unsigned_abs()));
                        let pb = if bb < 0 { FastBinaryCurve128::neg(pb) } else { pb };
                        let image = fast.add(pa, pb);
                        let weight = ((a as i128 + bb as i128 * lambda as i128).rem_euclid(r as i128)) as u64;
                        assert_eq!(image, fast.scalar_mul(p, &BigUint::from(weight)), "a={a} b={bb}");
                        checked += 1;
                    }
                }
            }
            assert_eq!(checked, 3 * 38);
        }
    }

    #[cfg(test)]
    mod rankprobe_tests {
        use super::*;

        fn small_instance(
            columns: usize,
        ) -> (FastBinaryCurve128, Gf2_128, NormalBasis128, S3Solver128, Base128, Vec<u128>) {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let b = gf.from_element(&curve.curve.b);
            let r = curve.subgroup_order.to_u64().unwrap();
            let (points, labels, reps, _) = construct_base128(&fast, &curve, b, columns, r);
            let mut by_x: HashMap<u128, Vec<usize>> = HashMap::new();
            for (i, point) in points.iter().enumerate() {
                by_x.entry(point.unwrap().0).or_default().push(i);
            }
            let reps: Vec<u128> = reps.iter().map(|p| p.unwrap()[0]).collect();
            let base = Base128 { points, labels, by_x, columns };
            let basis = NormalBasis128::new(&gf);
            let solver = S3Solver128::new(&gf, b);
            (fast, gf, basis, solver, base, reps)
        }

        /// phi^s(T_s +- R) = T +- phi^s(R) on random points, with the frame
        /// tabulated by `frame_build128` (the identity the loop relies on).
        #[test]
        fn frame_conjugates_commute_with_point_addition() {
            let (fast, gf, basis, _solver, base, _) = small_instance(9);
            let frob = |p: FastPoint128, s: u32| -> FastPoint128 {
                p.map(|(x, y)| {
                    (basis.to_poly.apply(basis.rotate(basis.to_normal.apply(x), s)),
                     basis.to_poly.apply(basis.rotate(basis.to_normal.apply(y), s)))
                })
            };
            let mut frame = FrameScratch128::with_capacity(2 * gf.n as usize);
            let mut seed = 0x9E37_79B9_7F4A_7C15u64;
            let mut checked = 0u64;
            for _ in 0..300 {
                seed = digest_mix64(seed);
                let r = base.points[(seed % base.points.len() as u64) as usize];
                seed = digest_mix64(seed);
                let t = fast.add(r, base.points[(seed % base.points.len() as u64) as usize]);
                let Some((tx, ty)) = t else { continue };
                frame_build128(&mut frame, &basis, fast.a, tx, ty);
                seed = digest_mix64(seed);
                let s = (seed % gf.n as u64) as u32;
                let ts = Some((frame.x[s as usize], frame.y[s as usize]));
                assert_eq!(frob(ts, s), t, "phi^s(T_s) = T");
                assert_eq!(frame.normal_c[s as usize],
                           basis.to_normal.apply(frame.x[s as usize]) ^ basis.to_normal.apply(fast.a));
                for sign in [false, true] {
                    let rr = if sign { FastBinaryCurve128::neg(r) } else { r };
                    assert_eq!(frob(fast.add(ts, rr), s), fast.add(t, frob(rr, s)));
                }
                checked += 1;
            }
            assert!(checked > 200);
        }

        /// The frame keys equal the rank-cut keys on random states of
        /// random points (the planted control's comparison, standalone).
        #[test]
        fn frame_keys_are_the_rankcut_keys() {
            let (fast, gf, basis, solver, base, _) = small_instance(9);
            let mut scan = StateScan128::new(gf.n);
            let mut seed = 0x0123_4567_89AB_CDEFu64;
            let mut checked = 0u64;
            for _ in 0..200 {
                let mut pick = || {
                    seed = digest_mix64(seed);
                    base.points[(seed % base.points.len() as u64) as usize]
                };
                let (p1, p2, t) = (pick(), pick(), fast.add(pick(), pick()));
                let (Some((x1, _)), Some((x2, _)), Some((tx, ty))) = (p1, p2, t) else { continue };
                if x1 == x2 {
                    continue;
                }
                let Some(roots) = solver.roots(&gf, &basis, x1, x2) else { continue };
                let state = State128 {
                    left: 0,
                    right: 0,
                    relative: 0,
                    normal_roots: [basis.to_normal.apply(roots[0]), basis.to_normal.apply(roots[1])],
                };
                let mut want = Vec::new();
                assert!(rankcut_keys128::<CANON_LIFT>(&gf, &basis, &solver, fast.a, (tx, ty), &state,
                                                       &mut scan.inputs, &mut scan.padd, &mut want));
                // The frame loop's key derivation, run through the planted
                // loop on an index-free path is covered by the next test; here
                // the keys are rebuilt from the frame directly.
                let mut frame = FrameScratch128::with_capacity(2 * gf.n as usize);
                frame_build128(&mut frame, &basis, fast.a, tx, ty);
                let (xk, yk): (Vec<u128>, Vec<u128>) = state.normal_roots.iter()
                    .map(|&root| frame_root_xy(&gf, &basis, &solver, fast.a, root).unwrap()).unzip();
                let mut got = Vec::new();
                for shift in 0..gf.n as usize {
                    for k in 0..FRAME_ROOTS {
                        let i = shift * FRAME_ROOTS + k;
                        let d = xk[k] ^ frame.x[shift];
                        assert!(d != 0 && xk[k] != 0 && frame.x[shift] != 0);
                        let inverse = invert128(&gf, &basis, d);
                        let lambda = basis.to_normal.apply(fmul(&gf, frame.y[shift] ^ yk[k], inverse));
                        let lambda2 = lambda ^ basis.to_normal.apply(fmul(&gf, xk[k], inverse));
                        let c = frame.normal_c[shift] ^ state.normal_roots[k];
                        let plus = basis.rotate(basis.rotate(lambda, 1) ^ lambda ^ c, shift as u32);
                        let minus = basis.rotate(basis.rotate(lambda2, 1) ^ lambda2 ^ c, shift as u32);
                        for partner in [minus, plus] {
                            let (canonical, partner_shift) = target_canonical::<CANON_LIFT>(&basis, partner);
                            got.push((canonical, partner, partner_shift, i as u32));
                        }
                    }
                }
                let want: Vec<_> = want.iter().map(|k| (k.canonical, k.partner, k.partner_shift, k.candidate)).collect();
                assert_eq!(got, want, "frame keys differ from the rank-cut keys");
                checked += 1;
            }
            assert!(checked > 100);
        }

        #[test]
        fn frame_loops_find_the_rankcut_relation_with_the_rankcut_probes() {
            let (fast, gf, basis, solver, base, reps) = small_instance(9);
            const FOLDED: IndexMode128 = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_SELECTED };
            let stack = build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28, FOLDED);
            let unfolded =
                build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28, IndexMode128::UNFOLDED);
            let mut seed = 0xA076_1D64_78BD_642Fu64;
            let mut solved = 0usize;
            let swapped_before = PADD_SWAPPED_PAIRS.load(Ordering::Relaxed);
            let checked_before = FRAME_PLANT_CHECKED.load(Ordering::Relaxed);
            let builds_before = FRAME_BUILDS.load(Ordering::Relaxed);
            for trial in 0..40u64 {
                let mut pick = || {
                    seed = digest_mix64(seed.wrapping_add(trial));
                    (seed % base.points.len() as u64) as usize
                };
                let mut target = base.points[pick()];
                for _ in 0..3 {
                    target = fast.add(target, base.points[pick()]);
                }
                let Some((tx, ty)) = target else { continue };
                let start = digest_mix64((tx ^ ty.rotate_left(29)) as u64) as usize;
                macro_rules! run {
                    ($o:expr, $p:expr, $index:expr) => {{
                        let mut clock = PhaseClock::start();
                        let mut split = ExtractSplit::default();
                        let relation = extract128::<CANON_LIFT, { $o }, { $p }>(
                            &gf, &fast, &basis, &solver, $index, &base, target, start, &mut clock,
                            &mut split,
                        );
                        (relation.map(|r| ((r.point_indices, r.x_codes, r.intermediates), r.probes)),
                         split.root_calls, split.relation_checks)
                    }};
                }
                for (order, index) in [(ORDER_FEISTEL, &stack), (ORDER_LEFT_MAJOR, &stack), (ORDER_FEISTEL, &unfolded)] {
                    macro_rules! compare {
                        ($o:expr) => {{
                            let want = run!($o, PIPE_COMPACT, index);
                            assert!(want.0.is_some(), "a planted four-point target decomposes");
                            assert_eq!(run!($o, PIPE_PADD, index), want, "the rank-cut loop differs from S3");
                            for got in [run!($o, PIPE_FRAME, index), run!($o, PIPE_FRAME_PLANT, index),
                                        run!($o, PIPE_FRAME_SWAPPED, index)] {
                                assert_eq!(got, want, "a frame loop differs from the rank-cut loop");
                            }
                            solved += 1;
                        }};
                    }
                    if order == ORDER_FEISTEL { compare!(ORDER_FEISTEL) } else { compare!(ORDER_LEFT_MAJOR) }
                }
            }
            assert!(solved >= 100);
            assert!(PADD_SWAPPED_PAIRS.load(Ordering::Relaxed) > swapped_before,
                    "the swapped loop must exercise the exact-order resolution");
            assert!(FRAME_PLANT_CHECKED.load(Ordering::Relaxed) > checked_before);
            assert!(FRAME_BUILDS.load(Ordering::Relaxed) > builds_before);
        }
    }

    #[cfg(test)]
    mod rankfinder_tests {
        // koblitz-n83-rankfinder-20261021: the parent's (koblitz-n83-indexbuild2-20261020)
        // frame loop, verbatim (re-indented, renamed), as the reference.
        use super::*;

        /// [`scan_state128_padd`] (`PIPE_PADD`) in the target's Frobenius frame:
        /// the same candidates (shift outer, stored root inner), the same
        /// partner words in the same order, so the same keys and probe
        /// positions, the same first hit and relation. At every root-table hit
        /// the candidate's S3 input is formed and the rank-cut loop's
        /// exact-order resolution runs unchanged.
        #[inline(always)]
        #[allow(clippy::too_many_arguments)]
        fn parent_scan_state128_frame<const C: u8, const P: u8>(
            gf: &Gf2_128,
            fast: &FastBinaryCurve128,
            basis: &NormalBasis128,
            solver: &S3Solver128,
            index: &Index128,
            base: &Base128,
            target: FastPoint128,
            target_x: u128,
            state: &State128,
            scan: &mut StateScan128,
            probes: &mut u64,
            clock: &mut PhaseClock,
            split: &mut ExtractSplit,
        ) -> Option<Relation128> {
            let n = gf.n;
            let compact = index.compact.as_ref().expect("the compact root table");
            let (tx, ty) = target.expect("a target point");
            debug_assert_eq!(tx, target_x);
            let a = fast.a;
            assert_eq!(state.normal_roots.len(), FRAME_ROOTS);
            let mut xk = [0u128; FRAME_ROOTS];
            let mut yk = [0u128; FRAME_ROOTS];
            for (k, &root) in state.normal_roots.iter().enumerate() {
                match frame_root_xy(gf, basis, solver, a, root) {
                    Some((x, y)) => {
                        xk[k] = x;
                        yk[k] = y;
                    }
                    None => {
                        PADD_FALLBACK_STATES.fetch_add(1, Ordering::Relaxed);
                        return scan_state128_filtered::<C, PIPE_COMPACT>(
                            gf, fast, basis, solver, index, base, target, target_x, state, scan,
                            probes, clock, split,
                        );
                    }
                }
            }
            frame_build128(&mut scan.frame, basis, a, tx, ty);
            let fr = &mut scan.frame;
            fr.prefix.clear();
            fr.regular.clear();
            let mut product = 1u128;
            for shift in 0..n as usize {
                let xt = fr.x[shift];
                for k in 0..FRAME_ROOTS {
                    // The rank-cut loop's exceptional inputs: x(R_k)^(2^s) = x(T)
                    // iff x(R_k) = x(T_s); x(R_k)^(2^s) = 0 iff x(R_k) = 0;
                    // x(T) = 0 iff x(T_s) = 0.
                    let regular = xk[k] != xt && xk[k] != 0 && xt != 0;
                    fr.prefix.push(product);
                    fr.regular.push(regular);
                    if regular {
                        product = fmul(&gf, product, xk[k] ^ xt);
                    }
                }
            }
            let count = fr.regular.len();
            split.root_calls += count as u64;
            fr.inverse.clear();
            fr.inverse.resize(count, 0);
            // A product of non-zero field elements is non-zero.
            let mut inverse = invert128(gf, basis, product);
            for i in (0..count).rev() {
                if fr.regular[i] {
                    fr.inverse[i] = fmul(&gf, inverse, fr.prefix[i]);
                    inverse = fmul(&gf, inverse, xk[i % FRAME_ROOTS] ^ fr.x[i / FRAME_ROOTS]);
                }
            }
            scan.keys.clear();
            fr.pair_start.clear();
            for shift in 0..n as usize {
                for k in 0..FRAME_ROOTS {
                    let i = shift * FRAME_ROOTS + k;
                    let pair: [u128; 2] = if fr.regular[i] {
                        let inverse = fr.inverse[i];
                        let lambda = basis.to_normal.apply(fmul(&gf, fr.y[shift] ^ yk[k], inverse));
                        let lambda2 = lambda ^ basis.to_normal.apply(fmul(&gf, xk[k], inverse));
                        let c = fr.normal_c[shift] ^ state.normal_roots[k];
                        // x(T_s +- R_k) in the normal basis, then phi^s.
                        let plus = basis.rotate(basis.rotate(lambda, 1) ^ lambda ^ c, shift as u32);
                        let minus = basis.rotate(basis.rotate(lambda2, 1) ^ lambda2 ^ c, shift as u32);
                        if P == PIPE_FRAME_SWAPPED { [plus, minus] } else { [minus, plus] }
                    } else {
                        PADD_IRREGULAR_INPUTS.fetch_add(1, Ordering::Relaxed);
                        let xs = basis.to_poly.apply(basis.rotate(state.normal_roots[k], shift as u32));
                        match solver.roots(gf, basis, xs, tx) {
                            Some([first, second]) => {
                                [basis.to_normal.apply(first), basis.to_normal.apply(second)]
                            }
                            None => {
                                fr.pair_start.push(u32::MAX);
                                continue;
                            }
                        }
                    };
                    fr.pair_start.push(scan.keys.len() as u32);
                    for partner in pair {
                        let (canonical, partner_shift) = target_canonical::<C>(basis, partner);
                        compact.prefetch(canonical);
                        scan.keys.push(ProbeKey128 {
                            canonical,
                            partner,
                            partner_shift,
                            candidate: i as u32,
                        });
                    }
                }
            }
            if P == PIPE_FRAME_PLANT {
                // The removed work, redone and discarded: the rank-cut loop's
                // key derivation on every candidate, compared key by key.
                let complete = rankcut_keys128::<C>(
                    gf, basis, solver, a, (tx, ty), state, &mut scan.inputs, &mut scan.padd, &mut fr.check,
                );
                assert!(complete, "a root the frame accepted failed the rank-cut curve check");
                assert_eq!(fr.check.len(), scan.keys.len(), "frame and rank-cut key counts differ");
                for (got, want) in scan.keys.iter().zip(&fr.check) {
                    assert!(
                        black_box(got.canonical) == want.canonical
                            && got.partner == want.partner
                            && got.partner_shift == want.partner_shift
                            && got.candidate == want.candidate,
                        "frame keys differ from the rank-cut keys"
                    );
                }
                FRAME_PLANT_CHECKED.fetch_add(count as u64, Ordering::Relaxed);
            }
            let first = *probes;
            let passes = split.filter_passes;
            let len = scan.keys.len();
            let mut position = 0usize;
            while position < len {
                *probes = first + position as u64 + 1;
                split.filter_passes = passes + position as u64 + 1;
                if compact.get(scan.keys[position].canonical).is_none() {
                    position += 1;
                    continue;
                }
                // First hit in this candidate's pair: form its S3 input and
                // evaluate the pair in the S3 order, at the S3 loop's probe
                // positions (the rank-cut loop's resolution).
                let candidate = scan.keys[position].candidate as usize;
                let shift = candidate / FRAME_ROOTS;
                let xs = basis.to_poly.apply(basis.rotate(state.normal_roots[candidate % FRAME_ROOTS], shift as u32));
                let start = fr.pair_start[candidate] as usize;
                let order = if fr.regular[candidate] {
                    PADD_RESOLVED_HITS.fetch_add(1, Ordering::Relaxed);
                    let exact = solver
                        .roots(gf, basis, xs, tx)
                        .expect("the S3 roots of a regular candidate");
                    let emitted = [
                        basis.to_poly.apply(scan.keys[start].partner),
                        basis.to_poly.apply(scan.keys[start + 1].partner),
                    ];
                    if emitted == exact {
                        [start, start + 1]
                    } else {
                        assert_eq!([emitted[1], emitted[0]], exact,
                                   "frame partners differ from the S3 roots");
                        PADD_SWAPPED_PAIRS.fetch_add(1, Ordering::Relaxed);
                        [start + 1, start]
                    }
                } else {
                    [start, start + 1]
                };
                for (rank, &at) in order.iter().enumerate() {
                    let exact_position = start + rank;
                    if at < position {
                        // Emitted before this hit and already looked up: a miss.
                        continue;
                    }
                    *probes = first + exact_position as u64 + 1;
                    split.filter_passes = passes + exact_position as u64 + 1;
                    let key = scan.keys[at];
                    let Some(value) = compact.get(key.canonical) else {
                        continue;
                    };
                    let left_x = index.shifted[state.left as usize][shift];
                    let right_x =
                        index.shifted[state.right as usize][(shift + state.relative as usize) % n as usize];
                    let (left2, right2, relative2, stored_shift) = unpack(value);
                    let left_shift2 = ((stored_shift + n - key.partner_shift) % n) as usize;
                    let right_shift2 = (left_shift2 + relative2) % n as usize;
                    let codes = [
                        left_x,
                        right_x,
                        index.shifted[left2][left_shift2],
                        index.shifted[right2][right_shift2],
                    ];
                    split.pdp += clock.lap();
                    let lifted = lift128(fast, base, &codes, target);
                    split.relation_check += clock.lap();
                    split.relation_checks += 1;
                    if let Some(point_indices) = lifted {
                        return Some(Relation128 {
                            point_indices,
                            x_codes: codes,
                            intermediates: [xs, basis.to_poly.apply(key.partner)],
                            probes: *probes,
                        });
                    }
                }
                position = start + 2;
            }
            *probes = first + len as u64;
            split.filter_passes = passes + len as u64;
            None
        }

        fn small_instance(
            columns: usize,
        ) -> (FastBinaryCurve128, Gf2_128, NormalBasis128, S3Solver128, Base128, Vec<u128>) {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let b = gf.from_element(&curve.curve.b);
            let r = curve.subgroup_order.to_u64().unwrap();
            let (points, labels, reps, _) = construct_base128(&fast, &curve, b, columns, r);
            let mut by_x: HashMap<u128, Vec<usize>> = HashMap::new();
            for (i, point) in points.iter().enumerate() {
                by_x.entry(point.unwrap().0).or_default().push(i);
            }
            let reps: Vec<u128> = reps.iter().map(|p| p.unwrap()[0]).collect();
            let base = Base128 { points, labels, by_x, columns };
            let basis = NormalBasis128::new(&gf);
            let solver = S3Solver128::new(&gf, b);
            (fast, gf, basis, solver, base, reps)
        }

        type Keys = Vec<(u128, u128, u32, u32)>;
        type Outcome = (Option<([usize; 4], [u128; 4], [u128; 2], u64)>, u64, u64, u64, u64, Keys, Vec<u32>);

        fn outcome(relation: Option<Relation128>, probes: u64, split: &ExtractSplit, scan: &StateScan128) -> Outcome {
            (
                relation.map(|r| (r.point_indices, r.x_codes, r.intermediates, r.probes)),
                probes,
                split.root_calls,
                split.filter_passes,
                split.relation_checks,
                scan.keys.iter().map(|k| (k.canonical, k.partner, k.partner_shift, k.candidate)).collect(),
                scan.frame.pair_start.clone(),
            )
        }

        /// Every state of a small folded index against random targets
        /// (planted four-point sums, so hits and relations occur): the
        /// derived loop and the parent's verbatim loop give the same
        /// relation, probe count, root calls, filter passes, relation
        /// checks, keys (canonical, partner, shift, candidate) and pair
        /// starts, for PIPE_FRAME, PIPE_FRAME_PLANT and PIPE_FRAME_SWAPPED,
        /// with lift_scan keys (the linear path) and full-scan keys (the
        /// parent's path).
        #[test]
        fn derived_frame_loop_reproduces_the_parent_loop_on_every_state() {
            let (fast, gf, basis, solver, base, reps) = small_instance(9);
            const FOLDED: IndexMode128 = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_LIFT };
            let index = build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28, FOLDED);
            let mut seed = 0x51ED_2701_8A3F_C64Du64;
            let (mut states, mut hits, mut tails) = (0u64, 0u64, 0u64);
            for trial in 0..8u64 {
                let mut pick = || {
                    seed = digest_mix64(seed.wrapping_add(trial));
                    (seed % base.points.len() as u64) as usize
                };
                let mut target = base.points[pick()];
                for _ in 0..3 {
                    target = fast.add(target, base.points[pick()]);
                }
                let Some((tx, _)) = target else { continue };
                for state in index.states.iter() {
                    macro_rules! run {
                        ($f:ident, $c:expr, $p:expr) => {{
                            let mut scan = StateScan128::new(gf.n);
                            let mut clock = PhaseClock::start();
                            let mut split = ExtractSplit::default();
                            let mut probes = 1000u64;
                            split.filter_passes = 77;
                            let relation = $f::<{ $c }, { $p }>(
                                &gf, &fast, &basis, &solver, &index, &base, target, tx, state, &mut scan,
                                &mut probes, &mut clock, &mut split,
                            );
                            outcome(relation, probes, &split, &scan)
                        }};
                    }
                    for (got, want) in [
                        (run!(scan_state128_frame, CANON_LIFT, PIPE_FRAME), run!(parent_scan_state128_frame, CANON_LIFT, PIPE_FRAME)),
                        (run!(scan_state128_frame, CANON_LIFT, PIPE_FRAME_PLANT), run!(parent_scan_state128_frame, CANON_LIFT, PIPE_FRAME_PLANT)),
                        (run!(scan_state128_frame, CANON_LIFT, PIPE_FRAME_SWAPPED), run!(parent_scan_state128_frame, CANON_LIFT, PIPE_FRAME_SWAPPED)),
                        (run!(scan_state128_frame, CANON_FULL, PIPE_FRAME), run!(parent_scan_state128_frame, CANON_FULL, PIPE_FRAME)),
                    ] {
                        assert!(got == want, "the derived frame loop differs from the parent's");
                        hits += got.0.is_some() as u64;
                        tails += (got.5.len() % RANK_PROBE_LANES != 0) as u64;
                    }
                    states += 1;
                }
            }
            assert!(states > 1000, "states checked {states}");
            assert!(hits > 0, "some state finds a relation");
            assert!(tails > 0, "the scalar tail runs");
        }

        /// The extract loop end to end: PIPE_FRAME (derived) equals the
        /// rank-cut loop's relation, probes, root calls and relation checks
        /// on planted targets, in both state orders (as the parent's test
        /// does for the parent loop).
        #[test]
        fn derived_frame_extract_equals_the_rankcut_extract() {
            let (fast, gf, basis, solver, base, reps) = small_instance(9);
            const FOLDED: IndexMode128 = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_LIFT };
            let index = build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28, FOLDED);
            let mut seed = 0x2545_F491_4F6C_DD1Du64;
            let mut solved = 0usize;
            for trial in 0..40u64 {
                let mut pick = || {
                    seed = digest_mix64(seed.wrapping_add(trial));
                    (seed % base.points.len() as u64) as usize
                };
                let mut target = base.points[pick()];
                for _ in 0..3 {
                    target = fast.add(target, base.points[pick()]);
                }
                let Some((tx, ty)) = target else { continue };
                let start = digest_mix64((tx ^ ty.rotate_left(29)) as u64) as usize;
                macro_rules! run {
                    ($o:expr, $p:expr) => {{
                        let mut clock = PhaseClock::start();
                        let mut split = ExtractSplit::default();
                        let relation = extract128::<CANON_LIFT, { $o }, { $p }>(
                            &gf, &fast, &basis, &solver, &index, &base, target, start, &mut clock, &mut split,
                        );
                        (relation.map(|r| ((r.point_indices, r.x_codes, r.intermediates), r.probes)),
                         split.root_calls, split.relation_checks, split.filter_passes)
                    }};
                }
                let want = run!(ORDER_FEISTEL, PIPE_PADD);
                assert!(want.0.is_some());
                assert_eq!(run!(ORDER_FEISTEL, PIPE_FRAME), want);
                assert_eq!(run!(ORDER_FEISTEL, PIPE_FRAME_PLANT), want);
                assert_eq!(run!(ORDER_LEFT_MAJOR, PIPE_FRAME), run!(ORDER_LEFT_MAJOR, PIPE_PADD));
                solved += 1;
            }
            assert!(solved >= 30);
        }
    }

    #[cfg(test)]
    mod fieldops_tests {
        use super::*;

        fn field() -> (Gf2_128, NormalBasis128, S3Solver128) {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            fast_field::check(&gf);
            let b = gf.from_element(&curve.curve.b);
            let basis = NormalBasis128::new(&gf);
            let solver = S3Solver128::new(&gf, b);
            (gf, basis, solver)
        }

        fn sample(gf: &Gf2_128, count: usize, seed: u128) -> Vec<u128> {
            let mut x = seed | 1;
            let mut out = vec![0u128, 1, 2, 3, gf.mask, gf.mask >> 1, gf.mask ^ 1, 1u128 << (gf.n - 1)];
            while out.len() < count {
                x ^= x << 13;
                x ^= x >> 7;
                x ^= x << 17;
                out.push(x & gf.mask);
            }
            out
        }

        #[test]
        fn inlined_product_and_square_equal_the_library() {
            let (gf, _, _) = field();
            let values = sample(&gf, 1 << 10, 0x9E37_79B9_7F4A_7C15_F39C_C060_5CED_C834);
            for &a in &values {
                assert_eq!(fsqr(&gf, a), gf.sqr(a));
                for &b in &values {
                    assert_eq!(fmul(&gf, a, b), gf.mul(a, b));
                }
            }
        }

        #[test]
        fn square_map_is_the_inlined_square() {
            let (gf, _, solver) = field();
            for &a in &sample(&gf, 1 << 18, 0x0123_4567_89AB_CDEF_FEDC_BA98_7654_3211) {
                assert_eq!(solver.square.apply(a), fsqr(&gf, a));
            }
        }

        #[test]
        fn byte_image_lookup_is_the_shift_loop() {
            let (gf, basis, solver) = field();
            let shift_loop = |map: &Linear128, v: u128| {
                let mut acc = 0u128;
                for (chunk, table) in map.tables.iter().enumerate() {
                    acc ^= table[((v >> (8 * chunk)) & 0xff) as usize];
                }
                acc
            };
            for &v in &sample(&gf, 1 << 18, 0x5555_AAAA_3333_CCCC_0F0F_F0F0_00FF_FF01) {
                for map in [&basis.to_normal, &basis.to_poly, &solver.square, &solver.half_trace] {
                    assert_eq!(map.apply(v), shift_loop(map, v));
                }
            }
        }

        #[test]
        fn table_permutation_is_apply_on_every_index() {
            // M38 (30,682,112 logical states) and M10 (29,880,600) with both self-test keys.
            for len in [30_682_112usize, 29_880_600, 2_100, 1] {
                for key in [0x0123_4567_89AB_CDEFu64, 0xFEDC_BA98_7654_3210u64] {
                    let permutation = ScanPermutation::new(len, key);
                    let rounds = RoundTables::new(&permutation);
                    for index in 0..permutation.domain {
                        assert_eq!(rounds.apply(index), permutation.apply(index), "len {len} key {key} index {index}");
                    }
                    assert!(scan_permutation_selftest(len, key));
                }
            }
        }
    }

    // koblitz-n83-opcounts2-20261108: the counted wrappers return the
    // library's results (counting on or off).
    #[cfg(test)]
    mod opcounts2_tests {
        use super::*;

        #[test]
        fn counted_group_law_returns_the_library_results() {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            // Koblitz a = 1: b = 1. Points from small abscissae (both y of each x).
            let mut points: Vec<FastPoint128> = Vec::new();
            for x in 2u128..200 {
                points.extend(fast.points_with_x(1, x));
            }
            assert!(points.len() >= 64, "only {} points", points.len());
            for (i, &p) in points.iter().enumerate() {
                let q = points[(i * 7 + 3) % points.len()];
                for (x, y) in [(p, q), (p, p), (p, FastBinaryCurve128::neg(p)), (None, p), (p, None), (None, None)] {
                    assert_eq!(counted_add(&fast, x, y), fast.add(x, y));
                }
                for k in [0u64, 1, 2, 3, 0b1011_0001, digest_mix64(i as u64)] {
                    let k = BigUint::from(k);
                    assert_eq!(counted_scalar_mul(&fast, p, &k), fast.scalar_mul(p, &k));
                }
            }
        }

        #[test]
        fn counting_is_off_without_the_environment_flag() {
            if std::env::var("KIC_OPCOUNTS").as_deref() != Ok("1") {
                assert!(!oc::on());
                let before = oc::snapshot();
                oc::bump(oc::EC_ADD, 1);
                assert_eq!(before, oc::snapshot());
            }
        }
    }

    #[cfg(test)]
    mod fieldops2_tests {
        use super::*;

        fn field() -> Gf2_128 {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            fast_field::check(&gf);
            gf
        }

        fn sample(gf: &Gf2_128, count: usize, seed: u128) -> Vec<u128> {
            let mut x = seed | 1;
            let mut out = vec![0u128, 1, 2, 3, gf.mask, gf.mask >> 1, gf.mask ^ 1, 1u128 << (gf.n - 1)];
            while out.len() < count {
                x ^= x << 13;
                x ^= x >> 7;
                x ^= x << 17;
                out.push(x & gf.mask);
            }
            out
        }

        #[test]
        fn the_specialised_field_is_n83_with_the_full_mask() {
            let gf = field();
            assert_eq!(gf.n, 83);
            assert_eq!(gf.mask, (1u128 << 83) - 1);
        }

        #[test]
        fn specialised_product_equals_the_library_and_the_general_path() {
            let gf = field();
            let tail = (gf.irr ^ (1u128 << gf.n)) as u64;
            let values = sample(&gf, 1 << 10, 0xD1B5_4A32_D192_ED03_9E37_79B9_7F4A_7C15);
            for &a in &values {
                for &b in &values {
                    let product = fmul(&gf, a, b);
                    assert_eq!(product, gf.mul(a, b));
                    assert_eq!(product, unsafe { fast_field::mul(gf.n, gf.mask, tail, a, b) });
                }
            }
        }

        #[test]
        fn specialised_square_equals_the_library_and_the_general_path() {
            let gf = field();
            let tail = (gf.irr ^ (1u128 << gf.n)) as u64;
            for &a in &sample(&gf, 1 << 18, 0x0123_4567_89AB_CDEF_FEDC_BA98_7654_3215) {
                let square = fsqr(&gf, a);
                assert_eq!(square, gf.sqr(a));
                assert_eq!(square, unsafe { fast_field::sqr(gf.n, gf.mask, tail, a) });
            }
        }
    }

    /// `P` picks the target scan's probe loop at compile time.
    #[inline(always)]
    #[allow(clippy::too_many_arguments)]
    fn scan_state128_select<const C: u8, const P: u8>(
        gf: &Gf2_128,
        fast: &FastBinaryCurve128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        index: &Index128,
        base: &Base128,
        target: FastPoint128,
        target_x: u128,
        state: &State128,
        scan: &mut StateScan128,
        probes: &mut u64,
        clock: &mut PhaseClock,
        split: &mut ExtractSplit,
    ) -> Option<Relation128> {
        if P >= PIPE_FRAME {
            return scan_state128_frame::<C, P>(
                gf, fast, basis, solver, index, base, target, target_x, state, scan, probes, clock,
                split,
            );
        }
        if P >= PIPE_PADD {
            return scan_state128_padd::<C, P>(
                gf, fast, basis, solver, index, base, target, target_x, state, scan, probes, clock,
                split,
            );
        }
        if P >= PIPE_COMPACT {
            scan_state128_filtered::<C, P>(
                gf, fast, basis, solver, index, base, target, target_x, state, scan, probes, clock,
                split,
            )
        } else if P == PIPE_PREFETCH {
            scan_state128_pipelined::<C>(
                gf, fast, basis, solver, index, base, target, target_x, state, scan, probes, clock,
                split,
            )
        } else {
            scan_state128::<C>(
                gf, fast, basis, solver, index, base, target, target_x, state, scan, probes, clock,
                split,
            )
        }
    }

    /// The wide search with the same candidate order as the frozen wide
    /// example; laps are taken only around `lift128`, so the probe loop
    /// carries no timer.
    #[allow(clippy::too_many_arguments)]
    fn extract128_timed<const C: u8, const O: u8, const P: u8>(
        gf: &Gf2_128,
        fast: &FastBinaryCurve128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        index: &Index128,
        base: &Base128,
        target: FastPoint128,
        start: usize,
        clock: &mut PhaseClock,
        split: &mut ExtractSplit,
    ) -> Option<Relation128> {
        let (target_x, _) = target?;
        let mut probes = 0u64;
        let mut scan = StateScan128::new(gf.n);
        if let Some(fold) = &index.fold {
            return extract128_folded::<C, O, P>(
                gf, fast, basis, solver, index, fold, base, target, target_x, start, &mut probes,
                &mut scan, clock, split,
            );
        }
        if O == ORDER_FEISTEL {
            // Same states, each once, in a keyed pseudo-random order; the
            // key is the public-point hash B's producer uses as `start`.
            let len = index.states.len();
            let permutation = ScanPermutation::new(len, start as u64);
            for position in 0..permutation.domain {
                let state_index = permutation.apply(position);
                if state_index >= len as u64 {
                    continue;
                }
                if let Some(relation) = scan_state128_select::<C, P>(
                    gf,
                    fast,
                    basis,
                    solver,
                    index,
                    base,
                    target,
                    target_x,
                    &index.states[state_index as usize],
                    &mut scan,
                    &mut probes,
                    clock,
                    split,
                ) {
                    return Some(relation);
                }
            }
            return None;
        }
        let start = start % index.states.len().max(1);
        for state in index.states[start..].iter().chain(&index.states[..start]) {
            if let Some(relation) = scan_state128_select::<C, P>(
                gf,
                fast,
                basis,
                solver,
                index,
                base,
                target,
                target_x,
                state,
                &mut scan,
                &mut probes,
                clock,
                split,
            ) {
                return Some(relation);
            }
        }
        None
    }

    /// Exclusive PDP / relation-check time of one wide `extract` call.
    #[allow(clippy::too_many_arguments)]
    fn extract128<const C: u8, const O: u8, const P: u8>(
        gf: &Gf2_128,
        fast: &FastBinaryCurve128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        index: &Index128,
        base: &Base128,
        target: FastPoint128,
        start: usize,
        clock: &mut PhaseClock,
        split: &mut ExtractSplit,
    ) -> Option<Relation128> {
        let relation = extract128_timed::<C, O, P>(
            gf, fast, basis, solver, index, base, target, start, clock, split,
        );
        split.pdp += clock.lap();
        relation
    }

    /// Frobenius-closed signed-orbit base from a deterministic public
    /// x-scan (wide twin: scanned abscissae are small integers, so the
    /// u64 scan counter converts losslessly).
    fn construct_base128(
        fast: &FastBinaryCurve128,
        curve: &KoblitzCurve,
        b: u128,
        columns: usize,
        r: u64,
    ) -> (
        Vec<FastPoint128>,
        Vec<(usize, u64)>,
        Vec<Option<[u128; 2]>>,
        u64,
    ) {
        let gf = &fast.gf;
        let n = fast.n as usize;
        let lambda = curve.lambda.to_u64().unwrap();
        let mut seen = std::collections::HashSet::new();
        let mut points = Vec::with_capacity(columns * 2 * n);
        let mut labels = Vec::with_capacity(columns * 2 * n);
        let mut reps = Vec::with_capacity(columns);
        let mut scanned = 0u64;
        let mut raw_x = 1u64;
        while reps.len() < columns {
            scanned += 1;
            oc::bump(oc::EC_LIFT_X, 1);
            for point in fast.points_with_x(b, raw_x as u128) {
                let Some((px, py)) = counted_scalar_mul(fast, point, &curve.cofactor) else {
                    continue;
                };
                if px <= 1 {
                    continue;
                }
                let mut key = px;
                let mut x = px;
                for _ in 1..n {
                    x = fsqr(&gf, x);
                    key = key.min(x);
                }
                oc::bump(oc::CANONICALIZATIONS, 1);
                oc::bump(oc::FROBENIUS_X, n as u64 - 1);
                if !seen.insert(key) {
                    continue;
                }
                let column = reps.len();
                reps.push(Some([px, py]));
                let (mut cx, mut cy) = (px, py);
                let mut coefficient = 1u64;
                for _ in 0..n {
                    points.push(Some((cx, cy)));
                    labels.push((column, coefficient));
                    points.push(Some((cx, cx ^ cy)));
                    labels.push((column, (r - coefficient) % r));
                    cx = fsqr(&gf, cx);
                    cy = fsqr(&gf, cy);
                    oc::bump(oc::EC_FROBENIUS, 1);
                    coefficient = super::mulmod(coefficient, lambda, r);
                }
                if reps.len() == columns {
                    break;
                }
            }
            raw_x += 1;
        }
        let rep = reps[0].map(|[x, y]| (x, y));
        assert_eq!(
            counted_scalar_mul(fast, rep, &BigUint::from(lambda)),
            rep.map(|(x, y)| (fsqr(&gf, x), fsqr(&gf, y))),
            "Frobenius must act as lambda on the subgroup"
        );
        (points, labels, reps, scanned)
    }

    fn relation_row128(base: &Base128, relation: &Relation128, rhs: u64, r: u64) -> Vec<u64> {
        let mut row = vec![0u64; base.columns + 1];
        for &index in &relation.point_indices {
            let (column, coefficient) = base.labels[index];
            row[column] = (row[column] + coefficient) % r;
        }
        row[base.columns] = rhs % r;
        row
    }

    /// Wide online pipeline for `64 < n ≤ 127`: same stages, record
    /// fields and JSON shapes as the frozen wide flow, plus the online
    /// interval instrumentation of the `u64` flow above (five phase
    /// timers on one clock, hardware counters, relation-check counting).
    pub fn run(arguments: &[String]) -> ! {
        assert_eq!(arguments.len(), 5);
        let process_started = Instant::now();
        let ops_start = oc::snapshot();
        let constructed: Option<(u32, u8, usize)> =
            arguments[1].strip_prefix("construct:").map(|spec| {
                let parts: Vec<&str> = spec.split(':').collect();
                assert_eq!(parts.len(), 3, "construct:<n>:<a>:<columns>");
                (
                    parts[0].parse().unwrap(),
                    parts[1].parse().unwrap(),
                    parts[2].parse().unwrap(),
                )
            });
        let header: Value = match constructed {
            Some((n, a, _)) => json!({"n":n, "a":a}),
            None => {
                let header_bytes = std::fs::read(&arguments[1]).expect("read base header");
                let header_line = header_bytes.split(|&b| b == b'\n').next().unwrap();
                let header: Value = serde_json::from_slice(header_line).expect("parse base header");
                assert_eq!(header["kind"], "point_defined_factor_base");
                header
            }
        };
        let n = header["n"].as_u64().unwrap() as u32;
        let a = header["a"].as_u64().unwrap() as u8;
        assert!((64..=127).contains(&n), "wide pipeline needs 64 < n ≤ 127");
        let target_inputs: Vec<TargetInput128> = std::fs::read_to_string(&arguments[2])
            .expect("read target points or legacy fixture scalars")
            .lines()
            .filter(|line| !line.trim().is_empty())
            .map(|line| {
                let line = line.trim();
                if line.starts_with('[') {
                    let [x, y] = parse_wide_pair_line(line);
                    TargetInput128::PublicPoint(Some((x, y)))
                } else {
                    TargetInput128::KnownAnswerScalar(line.parse().unwrap())
                }
            })
            .collect();
        let mut rank_seed: u64 = arguments[3].parse().unwrap();
        let mut out = std::fs::File::create(&arguments[4]).expect("create output");

        let setup_started = Instant::now();
        let curve = KoblitzCurve::new(a, n).expect("admitted Koblitz rung");
        let r = curve.subgroup_order.to_u64().unwrap();
        if constructed.is_none() {
            assert_eq!(header["subgroup_order"].as_u64(), Some(r));
            let low_terms: Vec<u64> =
                serde_json::from_value(header["field_modulus_low_terms"].clone()).unwrap();
            assert_eq!(
                low_terms,
                curve
                    .curve
                    .irreducible
                    .low_terms
                    .iter()
                    .map(|&t| t as u64)
                    .collect::<Vec<_>>(),
                "base header field must match the constructed curve"
            );
        }
        let fast = FastBinaryCurve128::new(&curve.curve.irreducible, a as u128).unwrap();
        let gf = Gf2_128::new(&curve.curve.irreducible);
        // koblitz-n83-fieldops-20261104 (F1): fail closed before any use.
        fast_field::check(&gf);
        let b = gf.from_element(&curve.curve.b);
        let generator: FastPoint128 = match curve.generator() {
            crypto_lib::binary_ecc::BinaryPoint::Affine { x, y } => {
                Some((fast.word(x), fast.word(y)))
            }
            crypto_lib::binary_ecc::BinaryPoint::Infinity => panic!("generator must be affine"),
        };
        let mut scanned_x = None;
        let (points, labels, representatives): (
            Vec<FastPoint128>,
            Vec<(usize, u64)>,
            Vec<Option<[u128; 2]>>,
        ) = match constructed {
            Some((_, _, columns)) => {
                let (points, labels, reps, scanned) =
                    construct_base128(&fast, &curve, b, columns, r);
                scanned_x = Some(scanned);
                (points, labels, reps)
            }
            None => {
                let coordinates = decode_point_list128(&header["factor_base_point_coordinates"]);
                let representatives = decode_point_list128(&header["factor_base_representatives"]);
                (
                    coordinates.iter().map(|c| c.map(|[x, y]| (x, y))).collect(),
                    serde_json::from_value(header["factor_base_point_labels"].clone()).unwrap(),
                    representatives,
                )
            }
        };
        let base_hash = match constructed {
            Some(_) => {
                let mut hasher = blake3::Hasher::new();
                hasher.update(b"compact-orbit-constructed-base-v1");
                for (point, &(column, coefficient)) in points.iter().zip(&labels) {
                    let (x, y): (u128, u128) = point.unwrap();
                    for word in [x, y] {
                        hasher.update(&word.to_le_bytes());
                    }
                    hasher.update(&(column as u64).to_le_bytes());
                    hasher.update(&coefficient.to_le_bytes());
                }
                hasher.finalize().to_hex().to_string()
            }
            None => header["base_hash"].as_str().unwrap().to_owned(),
        };
        let mut by_x: HashMap<u128, Vec<usize>> = HashMap::new();
        for (index, point) in points.iter().enumerate() {
            if let Some((x, _)) = point {
                by_x.entry(*x).or_default().push(index);
            }
        }
        let base = Base128 {
            points,
            labels,
            by_x,
            columns: representatives.len(),
        };
        // koblitz-n83-closure-20261019: a Z[tau]-closure header lists one
        // representative per orbit (the root index) apart from one per
        // column (the logs, the guided rank stage and the log check).
        let orbit_representatives: Option<Vec<Option<[u128; 2]>>> = match constructed {
            Some(_) => None,
            None => header.get("orbit_representatives").map(decode_point_list128),
        };
        let reps: Vec<u128> = orbit_representatives
            .as_ref()
            .unwrap_or(&representatives)
            .iter()
            .map(|p| p.expect("affine representative")[0])
            .collect();
        for x in &reps {
            assert!(base.by_x.contains_key(x), "every orbit representative must be a base point");
        }
        let base_elapsed = setup_started.elapsed();
        let base_load_ms = ms(base_elapsed);

        let basis_started = Instant::now();
        let basis = NormalBasis128::new(&gf);
        let solver = S3Solver128::new(&gf, b);
        for probe in 1..2048u128 {
            let x = probe.wrapping_mul(0x2545_F491_4F6C_DD1D) & basis.mask;
            assert_eq!(
                basis
                    .to_poly
                    .apply(basis.rotate(basis.to_normal.apply(x), 1)),
                fsqr(&gf, x)
            );
            let y = (probe * 0x9E37_79B9) & basis.mask;
            assert_eq!(
                solver.roots(&gf, &basis, x, y),
                s3_x_roots_128_counted(&gf, b, x, y)
            );
        }
        let basis_elapsed = basis_started.elapsed();
        let basis_ms = ms(basis_elapsed);

        let index_started = Instant::now();
        let (index_mode, index_canon_name) = index_mode_from_env();
        let index = build_index128(&gf, &basis, &solver, &reps, index_mode);
        let index_elapsed = index_started.elapsed();
        let index_ms = ms(index_elapsed);
        let setup_ms = ms(setup_started.elapsed());
        let ops_setup = oc::snapshot();

        // Rank stage: rows sum(coefficient * L_column) = a for random [a]G,
        // with the same query / PDP / relation-check split as the `u64`
        // online flow so the cold-phase accounting stays complete.
        let cached_log_table = super::log_cache::input_path();
        // koblitz-n83-stacked-20261016: the rank stage's canonicalizer, order
        // and probe loop; `target` runs the arm's own layout loop.
        let (rank_canon_name, rank_order_name, rank_probe_name) = rank_selectors_from_env();
        let rank_loop = if rank_probe_name == "off" {
            PIPE_OFF
        } else {
            match index.root_table {
                TABLE_COMPACT => PIPE_COMPACT,
                TABLE_FILTER => PIPE_FILTER,
                TABLE_FILTER_PLANT => PIPE_FILTER_PLANT,
                _ => PIPE_PREFETCH,
            }
        };
        assert!(
            index.root_table == TABLE_BASE || rank_loop != PIPE_OFF || cached_log_table.is_some(),
            "KIC_ROOT_TABLE other than base needs KIC_RANK_PROBE=target or the verified cached factor-log table"
        );
        // koblitz-n83-rankcut-20261016: the rank stage's partner-root solve.
        // koblitz-n83-rankprobe-20261019: frame | frame_plant, else the rank-cut selector.
        let (rank_solve, rank_solve_name) = rank_solve_frame_from_env().unwrap_or_else(rank_solve_from_env);
        assert!(
            rank_solve == PIPE_COMPACT || rank_loop == PIPE_COMPACT,
            "KIC_RANK_SOLVE=padd runs with KIC_ROOT_TABLE=compact and KIC_RANK_PROBE=target"
        );
        let rank_loop = if rank_solve == PIPE_COMPACT { rank_loop } else { rank_solve };
        for counter in [&PADD_FALLBACK_STATES, &PADD_IRREGULAR_INPUTS, &PADD_RESOLVED_HITS,
                        &PADD_SWAPPED_PAIRS, &PADD_PLANT_CHECKED, &FRAME_BUILDS, &FRAME_PLANT_CHECKED] {
            counter.store(0, Ordering::Relaxed);
        }
        let rank_started = Instant::now();
        let mut echelon = Echelon {
            r,
            columns: base.columns,
            pivots: vec![None; base.columns],
            rank: 0,
        };
        let mut rank_attempts = 0u64;
        let mut rank_failures = 0u64;
        let mut rank_relations = 0u64;
        let mut rank_probes = 0u64;
        let mut rank_root_calls = 0u64;
        let mut rank_skipped_symmetric_states = 0u64;
        let mut rank_attempt_probes: Vec<Option<u64>> = Vec::new();
        let mut rank_attempt_ns: Vec<u64> = Vec::new();
        let mut rank_relations_hasher = blake3::Hasher::new();
        rank_relations_hasher.update(b"n83-stacked-rank-relations-v1");
        let mut rank_rows_without_gain = 0u64;
        let mut rank_query_elapsed = std::time::Duration::ZERO;
        let mut rank_pdp_elapsed = std::time::Duration::ZERO;
        let mut rank_relation_check_elapsed = std::time::Duration::ZERO;
        // Guided: decompose [a]G - R_j for a column j that has no pivot yet.
        while cached_log_table.is_none() && echelon.rank < base.columns {
            let query_started = Instant::now();
            rank_seed = rank_seed
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            let scalar = (rank_seed >> 11) % (r - 1) + 1;
            let column = (0..base.columns)
                .find(|&c| echelon.pivots[c].is_none())
                .unwrap();
            let rep: FastPoint128 = representatives[column].map(|[x, y]| (x, y));
            let point = counted_add(&fast, 
                counted_scalar_mul(&fast, generator, &BigUint::from(scalar)),
                FastBinaryCurve128::neg(rep),
            );
            rank_attempts += 1;
            let query_elapsed = query_started.elapsed();
            rank_query_elapsed += query_elapsed;
            let mut rank_clock = PhaseClock::start();
            let mut rank_split = ExtractSplit::default();
            macro_rules! rank_extract {
                ($c:expr, $o:expr, $p:expr) => {
                    extract128::<{ $c }, { $o }, { $p }>(
                        &gf,
                        &fast,
                        &basis,
                        &solver,
                        &index,
                        &base,
                        point,
                        (rank_seed >> 20) as usize,
                        &mut rank_clock,
                        &mut rank_split,
                    )
                };
            }
            let relation = match (rank_canon_name, rank_order_name, rank_loop) {
                ("full", "left_major", _) => rank_extract!(CANON_FULL, ORDER_LEFT_MAJOR, PIPE_OFF),
                ("full", _, _) => rank_extract!(CANON_FULL, ORDER_FEISTEL, PIPE_OFF),
                (_, "left_major", _) => rank_extract!(CANON_LIFT, ORDER_LEFT_MAJOR, PIPE_OFF),
                (_, _, PIPE_OFF) => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_OFF),
                (_, _, PIPE_PREFETCH) => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_PREFETCH),
                (_, _, PIPE_COMPACT) => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_COMPACT),
                (_, _, PIPE_PADD) => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_PADD),
                (_, _, PIPE_PADD_PLANT) => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_PADD_PLANT),
                (_, _, PIPE_FRAME) => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_FRAME),
                (_, _, PIPE_FRAME_PLANT) => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_FRAME_PLANT),
                (_, _, PIPE_FILTER) => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_FILTER),
                _ => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_FILTER_PLANT),
            };
            rank_pdp_elapsed += rank_split.pdp;
            rank_relation_check_elapsed += rank_split.relation_check;
            rank_root_calls += rank_split.root_calls;
            rank_skipped_symmetric_states += rank_split.skipped_symmetric_states;
            rank_attempt_probes.push(relation.as_ref().map(|relation| relation.probes));
            rank_attempt_ns.push(
                (query_elapsed + rank_split.pdp + rank_split.relation_check).as_nanos() as u64,
            );
            if let Some(relation) = &relation {
                rank_relations_hasher.update(&rank_attempts.to_le_bytes());
                for &point_index in &relation.point_indices {
                    rank_relations_hasher.update(&(point_index as u64).to_le_bytes());
                }
            }
            match relation {
                Some(relation) => {
                    rank_relations += 1;
                    rank_probes += relation.probes;
                    let mut row = relation_row128(&base, &relation, scalar, r);
                    row[column] = (row[column] + 1) % r;
                    if !echelon.insert(row) {
                        rank_rows_without_gain += 1;
                    }
                }
                None => rank_failures += 1,
            }
        }
        let rank_elapsed = rank_started.elapsed();
        let rank_ms = ms(rank_elapsed);
        let ops_rank = oc::snapshot();
        let rank_matrix_elapsed = rank_elapsed
            .checked_sub(rank_query_elapsed + rank_pdp_elapsed + rank_relation_check_elapsed)
            .expect("rank phase accounting exceeds rank interval");
        let la_started = Instant::now();
        let (logs, log_table_digest) = match cached_log_table.as_deref() {
            Some(path) => {
                let (logs, digest) =
                    super::log_cache::load(path, n, a, r, &base_hash, base.columns);
                (logs, Some(digest))
            }
            None => (echelon.solve(), None),
        };
        // Every factor log is checked against its representative before any
        // target work, whether it was solved here or read from the cache.
        let log_verify_started = Instant::now();
        for (column, &log) in logs.iter().enumerate() {
            let rep: FastPoint128 = representatives[column].map(|[x, y]| (x, y));
            assert_eq!(
                counted_scalar_mul(&fast, generator, &BigUint::from(log)),
                rep,
                "factor log {column} does not map G to its representative"
            );
        }
        let log_verify_ms = ms(log_verify_started.elapsed());
        let la_elapsed = la_started.elapsed();
        let la_ms = ms(la_elapsed);
        let ops_la = oc::snapshot();
        let mut ops_targets_start = None;
        if let Some(path) = super::log_cache::output_path() {
            assert!(
                cached_log_table.is_none(),
                "KIC_LOG_TABLE_OUT needs an in-process rank stage"
            );
            super::log_cache::write(
                &path,
                n,
                a,
                r,
                &base_hash,
                &logs,
                json!({
                    "producer": "koblitz_orbit_dlp_fast_online_logcache (wide path)",
                    "rank_seed_argument": arguments[3],
                    "rank_threads": 1,
                    "rank": echelon.rank,
                    "rank_attempts": rank_attempts,
                    "rank_relations": rank_relations,
                    "rank_failures": rank_failures,
                    "rank_rows_without_gain": rank_rows_without_gain,
                    "rank_probes_total": rank_probes,
                    "rank_stage_ms": rank_ms,
                    "every_log_verified_against_representative": true,
                }),
            );
        }
        let (scan_order, scan_order_name) = scan_order_from_env();
        let scan_start_override = scan_start_override_from_env();
        assert!(
            scan_start_override.is_none() || scan_order == ORDER_LEFT_MAJOR,
            "KIC_SCAN_START_OVERRIDE is a left-major planted control"
        );
        // koblitz-n83-indexlift-20261019: KIC_SCAN_SELFTEST=full (default,
        // unchanged) | sampled (skip the exhaustive sweep, keep the sampled
        // inverse check of the folded index).
        let scan_selftest_mode = match std::env::var("KIC_SCAN_SELFTEST").as_deref() {
            Err(_) | Ok("") | Ok("full") => "full",
            Ok("sampled") => "sampled",
            Ok(other) => panic!("unknown KIC_SCAN_SELFTEST {other}"),
        };
        assert!(scan_selftest_mode == "full" || index.fold.is_some(),
                "KIC_SCAN_SELFTEST=sampled needs KIC_STATE_FOLD=1");
        let scan_selftest_started = Instant::now();
        let scan_selftest_keys = [0x0123_4567_89AB_CDEFu64, 0xFEDC_BA98_7654_3210u64];
        let scan_selftest_ok = scan_selftest_keys
            .iter()
            .all(|&key| {
                (scan_selftest_mode == "sampled" || scan_permutation_selftest(index.logical_states, key))
                    && (index.fold.is_none() || scan_inverse_selftest(index.logical_states, key))
            });
        assert!(scan_selftest_ok, "feistel scan order is not a bijection on the state vector");
        let scan_selftest_ms = ms(scan_selftest_started.elapsed());
        let setup_complete_elapsed = process_started.elapsed();
        let setup_complete_ns = setup_complete_elapsed.as_nanos() as u64;
        let input_control_elapsed = setup_complete_elapsed
            .checked_sub(base_elapsed + basis_elapsed + index_elapsed + rank_elapsed + la_elapsed)
            .expect("setup phase accounting exceeds setup interval");

        let targets_started = Instant::now();
        let mut solved = 0usize;
        let mut failed = 0usize;
        let mut target_query_ms = Vec::with_capacity(target_inputs.len());
        let mut single_target_phases = None;
        let (target_canon, target_canon_name) = target_canon_from_env();
        let (probe_pipeline, probe_pipeline_name) = probe_pipeline_from_env();
        let root_table_name = TABLE_NAMES[index.root_table as usize];
        assert!(
            index.root_table == TABLE_BASE
                || (probe_pipeline == PIPE_PREFETCH
                    && target_canon == CANON_LIFT
                    && scan_order == ORDER_FEISTEL),
            "KIC_ROOT_TABLE other than base runs with prefetch, lift and feistel"
        );
        let table_loop = match index.root_table {
            TABLE_COMPACT => PIPE_COMPACT,
            TABLE_FILTER => PIPE_FILTER,
            TABLE_FILTER_PLANT => PIPE_FILTER_PLANT,
            _ => PIPE_OFF,
        };
        for (fixture_index, &target_input) in target_inputs.iter().enumerate() {
            // Fixture construction is outside the online interval: a real
            // query arrives as a point Q, not as its known-answer scalar.
            let (target, published, target_generation_ms) = match target_input {
                TargetInput128::PublicPoint(target) => (target, None, 0.0),
                TargetInput128::KnownAnswerScalar(scalar) => {
                    let target_generation_started = Instant::now();
                    let target = counted_scalar_mul(&fast, generator, &BigUint::from(scalar));
                    let elapsed = target_generation_started.elapsed().as_secs_f64() * 1000.0;
                    (target, Some(scalar), elapsed)
                }
            };
            let ops_target_start = oc::snapshot();
            ops_targets_start.get_or_insert(ops_target_start);
            let online_counters = HwCounters::open();
            online_counters.start();
            let mut clock = PhaseClock::start();
            let online_started = clock.last;
            // The scan origin must be a function of the public target point
            // only; the wide hash matches the frozen wide producer.
            let (target_x, target_y) = target.expect("published fixture target is not infinity");
            let mut query_hash =
                target_x ^ target_y.rotate_left(29) ^ 0x9E37_79B9_7F4A_7C15_9E37_79B9_7F4A_7C15;
            query_hash = (query_hash ^ (query_hash >> 30))
                .wrapping_mul(0xBF58_476D_1CE4_E5B9_BF58_476D_1CE4_E5B9);
            query_hash = (query_hash ^ (query_hash >> 27))
                .wrapping_mul(0x94D0_49BB_1331_11EB_94D0_49BB_1331_11EB);
            query_hash ^= query_hash >> 31;
            let start = scan_start_override.unwrap_or(query_hash as usize);
            let query_phase = clock.lap();
            let mut split = ExtractSplit::default();
            VERIFY_WORDS.store(0, Ordering::Relaxed);
            VERIFY_GAP_MISMATCHES.store(0, Ordering::Relaxed);
            VERIFY_LIFT_MISMATCHES.store(0, Ordering::Relaxed);
            FOLD_AUDIT_PROBES.store(0, Ordering::Relaxed);
            macro_rules! target_extract_pipe {
                ($c:expr, $o:expr) => {
                    if probe_pipeline == PIPE_PREFETCH {
                        extract128::<{ $c }, { $o }, PIPE_PREFETCH>(
                            &gf, &fast, &basis, &solver, &index, &base, target, start,
                            &mut clock, &mut split,
                        )
                    } else {
                        extract128::<{ $c }, { $o }, PIPE_OFF>(
                            &gf, &fast, &basis, &solver, &index, &base, target, start,
                            &mut clock, &mut split,
                        )
                    }
                };
            }
            macro_rules! target_extract {
                ($c:expr) => {
                    if scan_order == ORDER_FEISTEL {
                        target_extract_pipe!($c, ORDER_FEISTEL)
                    } else {
                        target_extract_pipe!($c, ORDER_LEFT_MAJOR)
                    }
                };
            }
            macro_rules! table_extract {
                ($p:expr) => {
                    extract128::<CANON_LIFT, ORDER_FEISTEL, { $p }>(
                        &gf, &fast, &basis, &solver, &index, &base, target, start,
                        &mut clock, &mut split,
                    )
                };
            }
            let relation = if table_loop != PIPE_OFF {
                match table_loop {
                    PIPE_COMPACT => table_extract!(PIPE_COMPACT),
                    PIPE_FILTER => table_extract!(PIPE_FILTER),
                    _ => table_extract!(PIPE_FILTER_PLANT),
                }
            } else { match target_canon {
                CANON_FULL => target_extract!(CANON_FULL),
                CANON_GAP => target_extract!(CANON_GAP),
                CANON_LIFT => target_extract!(CANON_LIFT),
                CANON_FULL_X2 => target_extract!(CANON_FULL_X2),
                CANON_LIFT_PLUS_FULL => target_extract!(CANON_LIFT_PLUS_FULL),
                _ => target_extract!(CANON_VERIFY),
            } };
            let recovered = relation.as_ref().map(|relation| {
                relation.point_indices.iter().fold(0u64, |acc, &index| {
                    let (column, coefficient) = base.labels[index];
                    oc::bump(oc::DESCENT_MULMODS, 1);
                    (acc + super::mulmod(coefficient, logs[column], r)) % r
                })
            });
            let descent_phase = clock.lap();
            let verified =
                recovered.map(|d| counted_scalar_mul(&fast, generator, &BigUint::from(d)) == target);
            let recovery_check_phase = clock.lap();
            let online_stopped = clock.last;
            let online_hw_counts = online_counters.stop();
            let ops_target = oc::snapshot();
            let online = online_stopped - online_started;
            if target_inputs.len() == 1 {
                single_target_phases = Some((
                    query_phase,
                    split.pdp,
                    split.relation_check,
                    descent_phase,
                    recovery_check_phase,
                ));
            }
            let elapsed = ms(online);
            target_query_ms.push(elapsed);
            if verified == Some(true) {
                solved += 1;
            } else {
                failed += 1;
            }
            let target_exit_code = if verified == Some(true) { 0 } else { 1 };
            let record = json!({
                "kind":"compact_orbit_dlp_target",
                "n":n, "a":a, "fixture_index":fixture_index,
                "published_fixture_scalar":published,
                "field_value_encoding":"base-10 strings for u128 field values",
                "generator":encode_point128(generator),
                "target":encode_point128(target),
                "published_q":encode_point128(target),
                "exit_code":target_exit_code,
                "x_codes":relation.as_ref().map(|relation| relation.x_codes.map(|x| x.to_string())),
                "pinned_intermediates":relation.as_ref().map(|relation| relation.intermediates.map(|x| x.to_string())),
                "point_indices":relation.as_ref().map(|relation| relation.point_indices),
                "probes":relation.as_ref().map(|relation| relation.probes),
                "recovered_scalar":recovered,
                "recovered_matches_published":published.and_then(|scalar| recovered.map(|d| d == scalar % r)),
                "group_verified":verified,
                "relation_checks":split.relation_checks,
                "root_calls":split.root_calls,
                "skipped_symmetric_states":split.skipped_symmetric_states,
                "fold_audit_probes":FOLD_AUDIT_PROBES.load(Ordering::Relaxed),
                "root_table":root_table_name,
                "filter_passes":split.filter_passes,
                "planted_rejected_found":split.planted_found,
                "target_generation_ms_excluded":target_generation_ms,
                "online_start_event":"target_query_begin",
                "online_stop_event":"recovery_check_end",
                "online_start_ns":(online_started - process_started).as_nanos() as u64,
                "online_stop_ns":(online_stopped - process_started).as_nanos() as u64,
                "online_ms":elapsed,
                "online_hw_counts":online_hw_counts,
                "online_hw_scope":"calling thread, user space, target query through recovery check",
                "target_query_ms":ms(query_phase),
                "target_pdp_ms":ms(split.pdp),
                "target_relation_check_ms":ms(split.relation_check),
                "target_descent_ms":ms(descent_phase),
                "target_recovery_check_ms":ms(recovery_check_phase),
                "target_phase_sum_ms":ms(query_phase + split.pdp + split.relation_check + descent_phase + recovery_check_phase),
                "target_ms":elapsed,
                "target_canonicalizer":target_canon_name,
                "scan_order":scan_order_name,
"probe_pipeline":probe_pipeline_name,
                "scan_start_override":scan_start_override,
                "scan_start_or_key":start as u64,
                "target_canon_verification":if target_canon == CANON_VERIFY {
                    json!({"words":VERIFY_WORDS.load(Ordering::Relaxed),
                           "gap_mismatches_vs_full":VERIFY_GAP_MISMATCHES.load(Ordering::Relaxed),
                           "lift_mismatches_vs_full":VERIFY_LIFT_MISMATCHES.load(Ordering::Relaxed)})
                } else { Value::Null },
            });
            let mut record = record;
            if oc::on() {
                record["op_counts"] = oc::delta(&ops_target_start, &ops_target);
            }
            writeln!(out, "{record}").unwrap();
        }
        let targets_ms = targets_started.elapsed().as_secs_f64() * 1000.0;
        let ops_targets = oc::snapshot();
        let total_ms = process_started.elapsed().as_secs_f64() * 1000.0;
        let mut sorted = target_query_ms.clone();
        sorted.sort_by(|x, y| x.partial_cmp(y).unwrap());
        let median = sorted.get(sorted.len() / 2).copied();
        let (cold_in_process_ms, cold_phase_ms) = if let Some((
            target_query,
            target_pdp,
            target_relation_check,
            target_descent,
            target_recovery_check,
        )) = single_target_phases
        {
            let phases = [
                input_control_elapsed,
                base_elapsed,
                basis_elapsed,
                index_elapsed,
                rank_query_elapsed,
                rank_pdp_elapsed,
                rank_relation_check_elapsed,
                rank_matrix_elapsed,
                la_elapsed,
                target_query,
                target_pdp,
                target_relation_check,
                target_descent,
                target_recovery_check,
            ];
            let phase_sum: std::time::Duration = phases.iter().copied().sum();
            let cold_total = setup_complete_elapsed
                + target_query
                + target_pdp
                + target_relation_check
                + target_descent
                + target_recovery_check;
            assert_eq!(phase_sum, cold_total, "exclusive cold phases differ");
            (
                Some(ms(cold_total)),
                Some(json!({
                    "setup_input_control":ms(input_control_elapsed),
                    "isogeny":0.0,
                    "factor_base":ms(base_elapsed),
                    "precompute_basis_and_selftest":ms(basis_elapsed),
                    "precompute_index":ms(index_elapsed),
                    "rank_query":ms(rank_query_elapsed),
                    "rank_pdp":ms(rank_pdp_elapsed),
                    "rank_relation_check":ms(rank_relation_check_elapsed),
                    "rank_matrix_build":ms(rank_matrix_elapsed),
                    "relation_la":ms(la_elapsed),
                    "target_query":ms(target_query),
                    "target_pdp":ms(target_pdp),
                    "target_relation_check":ms(target_relation_check),
                    "target_descent":ms(target_descent),
                    "target_recovery_check":ms(target_recovery_check),
                })),
            )
        } else {
            (None, None)
        };
        // koblitz-n83-indexlift-20261019: plus the stored layout, byte for byte.
        let index_digest = (std::env::var("KIC_INDEX_DIGEST").as_deref() == Ok("1")).then(|| {
            let mut digest = index_digest128(&index, &basis);
            let (stored_states_blake3, table_slots_blake3) = index_layout_digest128(&index);
            digest["stored_states_blake3"] = json!(stored_states_blake3);
            digest["table_slots_blake3"] = json!(table_slots_blake3);
            digest
        });
        let mut summary = json!({
            "kind":"compact_orbit_dlp_summary",
            "schema_version":"1.0",
            "producer_version":"compact_orbit_online_pair_symmetry_v1",
            "setup_complete_ns":setup_complete_ns,
            "cold_in_process_ms":cold_in_process_ms,
            "cold_phase_ms":cold_phase_ms,
            "n":n, "a":a,
            "base_hash":base_hash,
            "base_source":if constructed.is_some() { "constructed_in_process_x_scan" } else { "retained_header" },
            "base_scanned_x":scanned_x,
            "orbit_columns":base.columns,
            "factor_base_points":base.points.len(),
            "index_orbits":reps.len(),
            "closure":header.get("closure").cloned(),
            "regular_states":index.logical_states,
            "stored_states":index.states.len(),
            "state_fold":index.fold.is_some(),
            "fold_plant":index.fold.as_ref().is_some_and(|fold| fold.plant),
            "index_canonicalizer":index_canon_name,
            "index_build_pipeline":"sum_inverse_lanes4+linear_canon_lanes8+lookahead32_prefetch+selftest_lanes8",
            "field_ops_pipeline":"fmul_clmul_inline+sqr_clmul_inline+state_square_clmul+maps_le_bytes+selftest_round_tables+n83_const_reduce_shift",
            "index_plant_checked_inputs":INDEX_PLANT_CHECKED.load(Ordering::Relaxed),
            "index_digest":index_digest,
            "rank_canonicalizer":rank_canon_name,
            "rank_order":rank_order_name,
            "rank_probe":rank_probe_name,
            "rank_solve":rank_solve_name,
            "rank_probe_pipeline":"linear_canon_lanes8",
            "rank_padd_fallback_states":PADD_FALLBACK_STATES.load(Ordering::Relaxed),
            "rank_padd_irregular_inputs":PADD_IRREGULAR_INPUTS.load(Ordering::Relaxed),
            "rank_padd_resolved_hits":PADD_RESOLVED_HITS.load(Ordering::Relaxed),
            "rank_padd_swapped_pairs":PADD_SWAPPED_PAIRS.load(Ordering::Relaxed),
            "rank_padd_plant_checked_inputs":PADD_PLANT_CHECKED.load(Ordering::Relaxed),
            "rank_frame_builds":FRAME_BUILDS.load(Ordering::Relaxed),
            "rank_frame_plant_checked_inputs":FRAME_PLANT_CHECKED.load(Ordering::Relaxed),
            "rank_skipped_symmetric_states":rank_skipped_symmetric_states,
            "rank_attempt_probes":rank_attempt_probes,
            "rank_attempt_ns":rank_attempt_ns,
            "rank_relations_blake3":rank_relations_hasher.finalize().to_hex().to_string(),
            "root_table_entries":index.root_entries(),
            "root_table":root_table_name,
            "root_table_slots":index.compact.as_ref().map_or(index.table.slots.len(), |c| c.slots.len()),
            "root_table_bytes":index.root_table_bytes(),
            "root_filter_bytes":index.filter.as_ref().map_or(0, RootFilter128::bytes),
            "root_filter_log2_bits":index.filter.as_ref().map(|f| f.log2_bits),
            "root_filter_hashes":index.filter.as_ref().map(|_| ROOT_FILTER_HASHES),
            "root_filter_ones_fraction":index.filter.as_ref().map(RootFilter128::ones_fraction),
            "root_filter_build_ms":index.filter_build_ms,
            "root_bloom_enabled":index.table.bloom.is_some(),
            "root_bloom_bytes":index.table.bloom.as_ref().map_or(0, RootBloom128::bytes),
            "sparse_canonical_enabled":basis.sparse_canonical,
            "target_canonicalizer":target_canon_name,
            "scan_order":scan_order_name,
"probe_pipeline":probe_pipeline_name,
            "scan_start_override":scan_start_override,
            "scan_order_selftest":{"states":index.logical_states, "keys":scan_selftest_keys.len(),
                                   "bijection":scan_selftest_ok, "ms":scan_selftest_ms,
                                   "mode":scan_selftest_mode,
                                   "accounting":"setup (setup_input_control), before setup_complete"},
            "pair_table_entries":0,
            "edge_selectors":0,
            "timing_ms":{
                "base_load":base_load_ms,
                "normal_basis_and_selftest":basis_ms,
                "index_build":index_ms,
                "setup_total":setup_ms,
                "rank_stage":rank_ms,
                "linear_algebra":la_ms,
                "targets_total":targets_ms,
                "target_median":median,
                "process_total":total_ms,
            },
            "rank_attempts":rank_attempts,
            "rank_relations":rank_relations,
            "rank_failures":rank_failures,
            "rank_probes_total":rank_probes,
            "rank_root_calls_total":rank_root_calls,
            "rank_rows_without_gain":rank_rows_without_gain,
            "rank_policy":"guided: decompose [a]G - R_j for the first pivotless column j",
            "rank_probes_mean":if rank_relations > 0 { rank_probes as f64 / rank_relations as f64 } else { 0.0 },
            "rank":echelon.rank,
            "targets":target_inputs.len(),
            "targets_solved":solved,
            "targets_failed":failed,
            "peak_rss_bytes":super::peak_rss_bytes(),
            "threads":1,
            "target_threads":1,
            "scope":"public synthetic Koblitz fixtures; shared-factor-log DLP with every stage timed in one process; no external points or key recovery",
        });
        let ops_after = oc::snapshot();
        let ops_targets_start = ops_targets_start.unwrap_or(ops_targets);
        if oc::on() {
            summary["op_counts"] = json!({
                "schema": "ic-op-counts/v1",
                "enabled": true,
                "producer": "koblitz-n83-opcounts2-20261108 ic_online_fieldops2_counted_r770 (feature op-counts, KIC_OPCOUNTS=1)",
                "kinds": oc::kinds(),
                "phases": {
                    "setup": oc::delta(&ops_start, &ops_setup),
                    "rank_stage": oc::delta(&ops_setup, &ops_rank),
                    "linear_algebra": oc::delta(&ops_rank, &ops_la),
                    "between_linear_algebra_and_targets": oc::delta(&ops_la, &ops_targets_start),
                    "targets": oc::delta(&ops_targets_start, &ops_targets),
                    "after_targets_index_digest": oc::delta(&ops_targets, &ops_after),
                },
                "end_to_end": oc::delta(&ops_start, &ops_targets),
                "accounting": "setup = process start to the index built; rank_stage = the timed rank interval; linear_algebra = echelon solve or cached-table load plus the verification of every factor log; targets = every target's online interval and the code between them; end_to_end = process start to the last target; after_targets_index_digest is diagnostic work outside every interval and outside end_to_end",
            });
        }
        summary["factor_log_table"] = json!({
            "source": if cached_log_table.is_some() { "verified_cache" } else { "in_process_rank" },
            "input_blake3": log_table_digest,
            "relation_la_or_load_and_verify_ms": la_ms,
            "verify_all_logs_ms": log_verify_ms,
            "verified_columns": logs.len(),
            "rank_stage_skipped": cached_log_table.is_some(),
        });
        println!("{summary}");
        if let Ok(path) = std::env::var("KIC_DUMP_BASE") {
            let dump = json!({
                "kind":"point_defined_factor_base",
                "n":n, "a":a,
                "subgroup_order":r,
                "field_modulus_low_terms":curve.curve.irreducible.low_terms,
                "orbit_columns":base.columns,
                "base_hash":base_hash,
                "factor_base_points":base.points.len(),
                "field_value_encoding":"base-10 strings for u128 field values",
                "factor_base_point_coordinates":base.points.iter().map(|p| encode_point128(*p)).collect::<Vec<_>>(),
                "factor_base_point_labels":base.labels,
                "factor_base_representatives":representatives.iter().copied().map(encode_pair128).collect::<Vec<_>>(),
            });
            std::fs::write(path, format!("{dump}\n")).expect("write base dump");
        }
        std::process::exit(if failed == 0 { 0 } else { 1 });
    }
}

fn main() -> ExitCode {
    let arguments: Vec<String> = std::env::args().collect();
    assert_eq!(
        arguments.len(),
        5,
        "usage: <base_header.jsonl | construct:<n>:<a>:<columns>> <target_points_or_legacy_scalars.txt> <rank_seed> <out.jsonl>"
    );
    // Wide pipeline (`u128` words) for 64 < n ≤ 127.  The degree is
    // detected here so the `u64` flow below stays byte-identical; the wide
    // path re-parses its own arguments.
    {
        let wide_n: Option<u32> = match arguments[1].strip_prefix("construct:") {
            Some(spec) => spec.split(':').next().and_then(|n| n.parse().ok()),
            None => {
                let header_bytes = std::fs::read(&arguments[1]).expect("read base header");
                let header_line = header_bytes.split(|&b| b == b'\n').next().unwrap();
                let header: Value = serde_json::from_slice(header_line).expect("parse base header");
                header["n"].as_u64().map(|n| n as u32)
            }
        };
        if wide_n.is_some_and(|n| n > 63) {
            wide::run(&arguments);
        }
    }
    let process_started = Instant::now();
    let constructed: Option<(u32, u8, usize)> =
        arguments[1].strip_prefix("construct:").map(|spec| {
            let parts: Vec<&str> = spec.split(':').collect();
            assert_eq!(parts.len(), 3, "construct:<n>:<a>:<columns>");
            (
                parts[0].parse().unwrap(),
                parts[1].parse().unwrap(),
                parts[2].parse().unwrap(),
            )
        });
    let header: Value = match constructed {
        Some((n, a, _)) => json!({"n":n, "a":a}),
        None => {
            let header_bytes = std::fs::read(&arguments[1]).expect("read base header");
            let header_line = header_bytes.split(|&b| b == b'\n').next().unwrap();
            let header: Value = serde_json::from_slice(header_line).expect("parse base header");
            assert_eq!(header["kind"], "point_defined_factor_base");
            header
        }
    };
    let n = header["n"].as_u64().unwrap() as u32;
    let a = header["a"].as_u64().unwrap() as u8;
    let target_inputs: Vec<TargetInput> = std::fs::read_to_string(&arguments[2])
        .expect("read target points or legacy fixture scalars")
        .lines()
        .filter(|line| !line.trim().is_empty())
        .map(|line| {
            let line = line.trim();
            if line.starts_with('[') {
                let [x, y]: [u64; 2] =
                    serde_json::from_str(line).expect("target point must be [x,y]");
                TargetInput::PublicPoint(Some((x, y)))
            } else {
                TargetInput::KnownAnswerScalar(line.parse().unwrap())
            }
        })
        .collect();
    let mut rank_seed: u64 = arguments[3].parse().unwrap();
    let rank_probe_cap = std::env::var("KIC_RANK_PROBE_CAP").ok().map(|raw| {
        let cap: u64 = raw
            .parse()
            .expect("KIC_RANK_PROBE_CAP must be a positive integer");
        assert!(cap > 0, "KIC_RANK_PROBE_CAP must be positive");
        cap
    });
    let pair_symmetry = match std::env::var("KIC_PAIR_SYMMETRY").as_deref() {
        Ok("1") => true,
        Ok("0") | Err(_) => false,
        Ok(_) => panic!("KIC_PAIR_SYMMETRY must be 0 or 1"),
    };
    let mut out = std::fs::File::create(&arguments[4]).expect("create output");

    let setup_started = Instant::now();
    let curve = KoblitzCurve::new(a, n).expect("admitted Koblitz rung");
    let r = curve.subgroup_order.to_u64().unwrap();
    if constructed.is_none() {
        assert_eq!(header["subgroup_order"].as_u64(), Some(r));
        let low_terms: Vec<u64> =
            serde_json::from_value(header["field_modulus_low_terms"].clone()).unwrap();
        assert_eq!(
            low_terms,
            curve
                .curve
                .irreducible
                .low_terms
                .iter()
                .map(|&t| t as u64)
                .collect::<Vec<_>>(),
            "base header field must match the constructed curve"
        );
    }
    let fast = FastBinaryCurve::new(&curve.curve.irreducible, a as u64).unwrap();
    let gf = Gf2::new(&curve.curve.irreducible);
    let b = gf.from_element(&curve.curve.b);
    let generator: FastPoint = match curve.generator() {
        crypto_lib::binary_ecc::BinaryPoint::Affine { x, y } => Some((fast.word(x), fast.word(y))),
        crypto_lib::binary_ecc::BinaryPoint::Infinity => panic!("generator must be affine"),
    };
    let mut scanned_x = None;
    let (points, labels, representatives): (
        Vec<FastPoint>,
        Vec<(usize, u64)>,
        Vec<Option<[u64; 2]>>,
    ) = match constructed {
        Some((_, _, columns)) => {
            let (points, labels, reps, scanned) = construct_base(&fast, &curve, b, columns, r);
            scanned_x = Some(scanned);
            (points, labels, reps)
        }
        None => {
            let coordinates: Vec<Option<[u64; 2]>> =
                serde_json::from_value(header["factor_base_point_coordinates"].clone()).unwrap();
            (
                coordinates.iter().map(|c| c.map(|[x, y]| (x, y))).collect(),
                serde_json::from_value(header["factor_base_point_labels"].clone()).unwrap(),
                serde_json::from_value(header["factor_base_representatives"].clone()).unwrap(),
            )
        }
    };
    let base_hash = match constructed {
        Some(_) => {
            let mut hasher = blake3::Hasher::new();
            hasher.update(b"compact-orbit-constructed-base-v1");
            for (point, &(column, coefficient)) in points.iter().zip(&labels) {
                let (x, y) = point.unwrap();
                for word in [x, y, column as u64, coefficient] {
                    hasher.update(&word.to_le_bytes());
                }
            }
            hasher.finalize().to_hex().to_string()
        }
        None => header["base_hash"].as_str().unwrap().to_owned(),
    };
    let mut by_x: HashMap<u64, Vec<usize>> = HashMap::new();
    for (index, point) in points.iter().enumerate() {
        if let Some((x, _)) = point {
            by_x.entry(*x).or_default().push(index);
        }
    }
    let base = Base {
        points,
        labels,
        by_x,
        columns: representatives.len(),
    };
    let reps: Vec<u64> = representatives
        .iter()
        .map(|p| p.expect("affine representative")[0])
        .collect();
    let base_elapsed = setup_started.elapsed();
    let base_load_ms = ms(base_elapsed);

    let basis_started = Instant::now();
    let basis = NormalBasis::new(&gf);
    let solver = S3Solver::new(&gf, b);
    for probe in 1..2048u64 {
        let x = probe.wrapping_mul(0x2545_F491_4F6C_DD1D) & basis.mask;
        assert_eq!(
            basis
                .to_poly
                .apply(basis.rotate(basis.to_normal.apply(x), 1)),
            gf.sqr(x)
        );
        let y = (probe * 0x9E37_79B9) & basis.mask;
        assert_eq!(solver.roots(&gf, &basis, x, y), s3_x_roots(&gf, b, x, y));
    }
    let basis_elapsed = basis_started.elapsed();
    let basis_ms = ms(basis_elapsed);

    let index_started = Instant::now();
    let index = build_index(&gf, &basis, &solver, &reps, pair_symmetry);
    let index_elapsed = index_started.elapsed();
    let index_ms = ms(index_elapsed);
    let setup_ms = ms(setup_started.elapsed());

    // Rank stage: rows sum(coefficient * L_column) = a for random [a]G.
    // The optional trace lets a separate implementation replay every attempted
    // group relation, rank transition, and final base-log solution.
    let rank_started = Instant::now();
    let mut rank_trace = std::env::var("KIC_DUMP_RANK")
        .ok()
        .map(|path| std::fs::File::create(path).expect("create rank trace"));
    if let Some(trace) = rank_trace.as_mut() {
        writeln!(
            trace,
            "{}",
            json!({
                "kind":"compact_orbit_rank_header", "schema_version":1,
                "n":n, "a":a, "subgroup_order":r, "base_hash":base_hash,
                "rank_probe_cap":rank_probe_cap,
                "pair_symmetry":pair_symmetry,
                "generator":generator.map(|(x, y)| [x, y]),
                "orbit_columns":base.columns, "factor_base_points":base.points.len(),
            })
        )
        .unwrap();
    }
    let mut echelon = Echelon {
        r,
        columns: base.columns,
        pivots: vec![None; base.columns],
        rank: 0,
    };
    let mut rank_attempts = 0u64;
    let mut rank_failures = 0u64;
    let mut rank_relations = 0u64;
    let mut rank_probes = 0u64;
    let mut rank_root_calls = 0u64;
    let mut rank_skipped_symmetric_states = 0u64;
    let mut rank_relation_probes = 0u64;
    let mut rank_capped_attempts = 0u64;
    let mut rank_capped_probes = 0u64;
    let mut rank_query_elapsed = Duration::ZERO;
    let mut rank_pdp_elapsed = Duration::ZERO;
    let mut rank_relation_check_elapsed = Duration::ZERO;
    // Guided: decompose [a]G - R_j for a column j that has no pivot yet, so the
    // row a = L_j + sum(...) always contains column j and raises the rank.
    let mut rank_rows_without_gain = 0u64;
    while echelon.rank < base.columns {
        let query_started = Instant::now();
        rank_seed = rank_seed
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        let scalar = (rank_seed >> 11) % (r - 1) + 1;
        let column = (0..base.columns)
            .find(|&c| echelon.pivots[c].is_none())
            .unwrap();
        let rep: FastPoint = representatives[column].map(|[x, y]| (x, y));
        let point = fast.add(
            fast.scalar_mul(generator, &BigUint::from(scalar)),
            FastBinaryCurve::neg(rep),
        );
        rank_attempts += 1;
        let rank_before = echelon.rank;
        let query_elapsed = query_started.elapsed();
        rank_query_elapsed += query_elapsed;
        let mut rank_clock = PhaseClock::start();
        let mut rank_split = ExtractSplit::default();
        let outcome = extract(
            &gf,
            &fast,
            &basis,
            &solver,
            &index,
            &base,
            point,
            (rank_seed >> 20) as usize,
            rank_probe_cap,
            &mut rank_clock,
            &mut rank_split,
        );
        rank_pdp_elapsed += rank_split.pdp;
        rank_relation_check_elapsed += rank_split.relation_check;
        rank_root_calls += rank_split.root_calls;
        rank_skipped_symmetric_states += rank_split.skipped_symmetric_states;
        let ExtractOutcome {
            relation,
            probes,
            capped,
        } = outcome;
        rank_probes += probes;
        match relation {
            Some(relation) => {
                rank_relations += 1;
                rank_relation_probes += probes;
                let mut row = relation_row(&base, &relation, scalar, r);
                row[column] = (row[column] + 1) % r;
                let gained = echelon.insert(row.clone());
                if !gained {
                    rank_rows_without_gain += 1;
                }
                if let Some(trace) = rank_trace.as_mut() {
                    writeln!(
                        trace,
                        "{}",
                        json!({
                            "kind":"compact_orbit_rank_attempt", "attempt_index":rank_attempts - 1,
                            "found":true, "scalar":scalar, "pivotless_column":column,
                            "target":point.map(|(x, y)| [x, y]),
                            "point_indices":relation.point_indices, "x_codes":relation.x_codes,
                            "pinned_intermediates":relation.intermediates,
                            "probes":probes, "capped":false, "row":row,
                            "query_ms":ms(query_elapsed), "pdp_ms":ms(rank_split.pdp),
                            "relation_check_ms":ms(rank_split.relation_check),
                            "relation_checks":rank_split.relation_checks,
                            "root_calls":rank_split.root_calls,
                            "skipped_symmetric_states":rank_split.skipped_symmetric_states,
                            "rank_before":rank_before, "rank_after":echelon.rank, "gained":gained,
                        })
                    )
                    .unwrap();
                }
            }
            None => {
                rank_failures += 1;
                if capped {
                    rank_capped_attempts += 1;
                    rank_capped_probes += probes;
                }
                if let Some(trace) = rank_trace.as_mut() {
                    writeln!(
                        trace,
                        "{}",
                        json!({
                            "kind":"compact_orbit_rank_attempt", "attempt_index":rank_attempts - 1,
                            "found":false, "scalar":scalar, "pivotless_column":column,
                            "target":point.map(|(x, y)| [x, y]),
                            "probes":probes, "capped":capped,
                            "query_ms":ms(query_elapsed), "pdp_ms":ms(rank_split.pdp),
                            "relation_check_ms":ms(rank_split.relation_check),
                            "relation_checks":rank_split.relation_checks,
                            "root_calls":rank_split.root_calls,
                            "skipped_symmetric_states":rank_split.skipped_symmetric_states,
                            "rank_before":rank_before, "rank_after":echelon.rank,
                        })
                    )
                    .unwrap();
                }
            }
        }
    }
    let rank_elapsed = rank_started.elapsed();
    let rank_ms = ms(rank_elapsed);
    let rank_matrix_elapsed = rank_elapsed
        .checked_sub(rank_query_elapsed + rank_pdp_elapsed + rank_relation_check_elapsed)
        .expect("rank phase accounting exceeds rank interval");
    let la_started = Instant::now();
    let logs = echelon.solve();
    if let Some(trace) = rank_trace.as_mut() {
        writeln!(
            trace,
            "{}",
            json!({
                "kind":"compact_orbit_rank_solution", "rank":echelon.rank,
                "attempts":rank_attempts, "relations":rank_relations,
                "failures":rank_failures, "rows_without_gain":rank_rows_without_gain,
                "rank_probe_cap":rank_probe_cap, "probes_total":rank_probes,
                "capped_attempts":rank_capped_attempts, "capped_probes":rank_capped_probes,
                "logs":logs,
            })
        )
        .unwrap();
        trace.flush().unwrap();
    }
    let la_elapsed = la_started.elapsed();
    let la_ms = ms(la_elapsed);
    let setup_complete_elapsed = process_started.elapsed();
    let setup_complete_ns = setup_complete_elapsed.as_nanos() as u64;
    let input_control_elapsed = setup_complete_elapsed
        .checked_sub(base_elapsed + basis_elapsed + index_elapsed + rank_elapsed + la_elapsed)
        .expect("setup phase accounting exceeds setup interval");

    let targets_started = Instant::now();
    let mut solved = 0usize;
    let mut failed = 0usize;
    let mut target_query_ms = Vec::with_capacity(target_inputs.len());
    let mut single_target_phases = None;
    for (fixture_index, &target_input) in target_inputs.iter().enumerate() {
        // Fixture construction is outside the online interval: a real query
        // arrives as a point Q, not as its known-answer scalar.
        let (target, published, target_generation_ms) = match target_input {
            TargetInput::PublicPoint(target) => (target, None, 0.0),
            TargetInput::KnownAnswerScalar(scalar) => {
                let target_generation_started = Instant::now();
                let target = fast.scalar_mul(generator, &BigUint::from(scalar));
                let elapsed = target_generation_started.elapsed().as_secs_f64() * 1000.0;
                (target, Some(scalar), elapsed)
            }
        };
        let online_counters = HwCounters::open();
        online_counters.start();
        let mut clock = PhaseClock::start();
        let online_started = clock.last;
        // The scan origin must be a function of the public target point only;
        // using the fixture's known-answer scalar here would leak the DLP.
        let (target_x, target_y) = target.expect("published fixture target is not infinity");
        let mut query_hash = target_x ^ target_y.rotate_left(29) ^ 0x9E37_79B9_7F4A_7C15;
        query_hash = (query_hash ^ (query_hash >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        query_hash = (query_hash ^ (query_hash >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        query_hash ^= query_hash >> 31;
        let start = query_hash as usize;
        let query_phase = clock.lap();
        let mut split = ExtractSplit::default();
        let relation = extract(
            &gf, &fast, &basis, &solver, &index, &base, target, start, None, &mut clock, &mut split,
        )
        .relation;
        let recovered = relation.as_ref().map(|relation| {
            relation.point_indices.iter().fold(0u64, |acc, &index| {
                let (column, coefficient) = base.labels[index];
                (acc + mulmod(coefficient, logs[column], r)) % r
            })
        });
        let descent_phase = clock.lap();
        let verified = recovered.map(|d| fast.scalar_mul(generator, &BigUint::from(d)) == target);
        let recovery_check_phase = clock.lap();
        let online_stopped = clock.last;
        let online_hw_counts = online_counters.stop();
        let online = online_stopped - online_started;
        if target_inputs.len() == 1 {
            single_target_phases = Some((
                query_phase,
                split.pdp,
                split.relation_check,
                descent_phase,
                recovery_check_phase,
            ));
        }
        let elapsed = ms(online);
        target_query_ms.push(elapsed);
        if verified == Some(true) {
            solved += 1;
        } else {
            failed += 1;
        }
        let target_exit_code = if verified == Some(true) { 0 } else { 1 };
        let record = json!({
            "kind":"compact_orbit_dlp_target",
            "n":n, "a":a, "fixture_index":fixture_index,
            "published_fixture_scalar":published,
            "generator":generator.map(|(x, y)| [x, y]),
            "target":target.map(|(x, y)| [x, y]),
            "published_q":target.map(|(x, y)| [x, y]),
            "exit_code":target_exit_code,
            "x_codes":relation.as_ref().map(|relation| relation.x_codes),
            "pinned_intermediates":relation.as_ref().map(|relation| relation.intermediates),
            "point_indices":relation.as_ref().map(|relation| relation.point_indices),
            "probes":relation.as_ref().map(|relation| relation.probes),
            "recovered_scalar":recovered,
            "recovered_matches_published":published.and_then(|scalar| recovered.map(|d| d == scalar % r)),
            "group_verified":verified,
            "relation_checks":split.relation_checks,
            "root_calls":split.root_calls,
            "skipped_symmetric_states":split.skipped_symmetric_states,
            "target_generation_ms_excluded":target_generation_ms,
            "online_start_event":"target_query_begin",
            "online_stop_event":"recovery_check_end",
            "online_start_ns":(online_started - process_started).as_nanos() as u64,
            "online_stop_ns":(online_stopped - process_started).as_nanos() as u64,
            "online_ms":elapsed,
            "online_hw_counts":online_hw_counts,
            "online_hw_scope":"calling thread, user space, target query through recovery check",
            "target_query_ms":ms(query_phase),
            "target_pdp_ms":ms(split.pdp),
            "target_relation_check_ms":ms(split.relation_check),
            "target_descent_ms":ms(descent_phase),
            "target_recovery_check_ms":ms(recovery_check_phase),
            "target_phase_sum_ms":ms(query_phase + split.pdp + split.relation_check + descent_phase + recovery_check_phase),
            "target_ms":elapsed,
        });
        writeln!(out, "{record}").unwrap();
    }
    let targets_ms = targets_started.elapsed().as_secs_f64() * 1000.0;
    let total_ms = process_started.elapsed().as_secs_f64() * 1000.0;
    let mut sorted = target_query_ms.clone();
    sorted.sort_by(|x, y| x.partial_cmp(y).unwrap());
    let median = sorted.get(sorted.len() / 2).copied();
    let (cold_in_process_ms, cold_phase_ms) = if let Some((
        target_query,
        target_pdp,
        target_relation_check,
        target_descent,
        target_recovery_check,
    )) = single_target_phases
    {
        let phases = [
            input_control_elapsed,
            base_elapsed,
            basis_elapsed,
            index_elapsed,
            rank_query_elapsed,
            rank_pdp_elapsed,
            rank_relation_check_elapsed,
            rank_matrix_elapsed,
            la_elapsed,
            target_query,
            target_pdp,
            target_relation_check,
            target_descent,
            target_recovery_check,
        ];
        let phase_sum: Duration = phases.iter().copied().sum();
        let cold_total = setup_complete_elapsed
            + target_query
            + target_pdp
            + target_relation_check
            + target_descent
            + target_recovery_check;
        assert_eq!(phase_sum, cold_total, "exclusive cold phases differ");
        (
            Some(ms(cold_total)),
            Some(json!({
                "setup_input_control":ms(input_control_elapsed),
                "isogeny":0.0,
                "factor_base":ms(base_elapsed),
                "precompute_basis_and_selftest":ms(basis_elapsed),
                "precompute_index":ms(index_elapsed),
                "rank_query":ms(rank_query_elapsed),
                "rank_pdp":ms(rank_pdp_elapsed),
                "rank_relation_check":ms(rank_relation_check_elapsed),
                "rank_matrix_build":ms(rank_matrix_elapsed),
                "relation_la":ms(la_elapsed),
                "target_query":ms(target_query),
                "target_pdp":ms(target_pdp),
                "target_relation_check":ms(target_relation_check),
                "target_descent":ms(target_descent),
                "target_recovery_check":ms(target_recovery_check),
            })),
        )
    } else {
        (None, None)
    };
    let summary = json!({
        "kind":"compact_orbit_dlp_summary",
        "schema_version":"1.0",
        "producer_version":"compact_orbit_online_pair_symmetry_v1",
        "setup_complete_ns":setup_complete_ns,
        "cold_in_process_ms":cold_in_process_ms,
        "cold_phase_ms":cold_phase_ms,
        "n":n, "a":a,
        "base_hash":base_hash,
        "base_source":if constructed.is_some() { "constructed_in_process_x_scan" } else { "retained_header" },
        "base_scanned_x":scanned_x,
        "orbit_columns":base.columns,
        "factor_base_points":base.points.len(),
        "regular_states":index.states.len(),
        "index_pair_candidates":index.pair_candidates,
        "pair_symmetry":pair_symmetry,
        "root_table_entries":index.table.len,
        "root_bloom_enabled":index.table.bloom.is_some(),
        "root_bloom_bytes":index.table.bloom.as_ref().map_or(0, RootBloom::bytes),
        "pair_table_entries":0,
        "edge_selectors":0,
        "timing_ms":{
            "base_load":base_load_ms,
            "normal_basis_and_selftest":basis_ms,
            "index_build":index_ms,
            "setup_total":setup_ms,
            "rank_stage":rank_ms,
            "linear_algebra":la_ms,
            "targets_total":targets_ms,
            "target_median":median,
            "process_total":total_ms,
        },
        "rank_attempts":rank_attempts,
        "rank_relations":rank_relations,
        "rank_failures":rank_failures,
        "rank_probe_cap":rank_probe_cap,
        "rank_capped_attempts":rank_capped_attempts,
        "rank_capped_probes":rank_capped_probes,
        "rank_exhausted_attempts":rank_failures - rank_capped_attempts,
        "rank_probes_total":rank_probes,
        "rank_root_calls_total":rank_root_calls,
        "rank_skipped_symmetric_states":rank_skipped_symmetric_states,
        "rank_rows_without_gain":rank_rows_without_gain,
        "rank_policy":"guided: decompose [a]G - R_j for the first pivotless column j",
        "rank_restart_policy":if rank_probe_cap.is_some() { "abandon after cap support probes; draw next scalar" } else { "unbounded" },
        "rank_probes_mean":if rank_relations > 0 { rank_relation_probes as f64 / rank_relations as f64 } else { 0.0 },
        "rank_probes_mean_per_attempt":if rank_attempts > 0 { rank_probes as f64 / rank_attempts as f64 } else { 0.0 },
        "rank":echelon.rank,
        "targets":target_inputs.len(),
        "targets_solved":solved,
        "targets_failed":failed,
        "peak_rss_bytes":peak_rss_bytes(),
        "threads":1,
        "scope":"public synthetic Koblitz fixtures; shared-factor-log DLP with every stage timed in one process; no external points or key recovery",
    });
    println!("{summary}");
    if let Ok(path) = std::env::var("KIC_DUMP_BASE") {
        let dump = json!({
            "kind":"point_defined_factor_base",
            "n":n, "a":a,
            "subgroup_order":r,
            "field_modulus_low_terms":curve.curve.irreducible.low_terms,
            "orbit_columns":base.columns,
            "base_hash":base_hash,
            "factor_base_points":base.points.len(),
            "factor_base_point_coordinates":base.points.iter().map(|p| p.map(|(x, y)| [x, y])).collect::<Vec<_>>(),
            "factor_base_point_labels":base.labels,
            "factor_base_representatives":representatives,
        });
        std::fs::write(path, format!("{dump}\n")).expect("write base dump");
    }
    if failed == 0 {
        ExitCode::SUCCESS
    } else {
        ExitCode::FAILURE
    }
}

#[cfg(test)]
mod pair_symmetry_tests {
    use super::*;

    #[test]
    fn unordered_pair_orbits_preserve_every_index_root() {
        let curve = KoblitzCurve::new(0, 13).unwrap();
        let gf = Gf2::new(&curve.curve.irreducible);
        let basis = NormalBasis::new(&gf);
        let solver = S3Solver::new(&gf, gf.from_element(&curve.curve.b));
        let reps = [2, 3, 5, 7, 11];
        let full = build_index(&gf, &basis, &solver, &reps, false);
        let folded = build_index(&gf, &basis, &solver, &reps, true);
        let keys = |index: &Index| {
            let mut roots: Vec<u64> = index
                .table
                .slots
                .iter()
                .filter_map(|&(key, _)| (key != u64::MAX).then_some(key))
                .collect();
            roots.sort_unstable();
            roots
        };
        assert_eq!(
            full.pair_candidates,
            reps.len() * reps.len() * gf.n as usize
        );
        assert_eq!(folded.pair_candidates, 165);
        let full_keys = keys(&full);
        assert_eq!(full_keys, keys(&folded));
        assert_eq!(folded.states.len(), full.states.len());
        for key in full_keys {
            assert_eq!(full.table.get(key), folded.table.get(key));
        }
        for (index, &mate) in folded.counterparts.as_ref().unwrap().iter().enumerate() {
            assert_eq!(
                folded.counterparts.as_ref().unwrap()[mate as usize],
                index as u32
            );
        }
    }

    #[test]
    fn n53_pair_quotient_preserves_the_complete_root_table() {
        let curve = KoblitzCurve::new(0, 53).unwrap();
        let fast = FastBinaryCurve::new(&curve.curve.irreducible, 0).unwrap();
        let gf = Gf2::new(&curve.curve.irreducible);
        let b = gf.from_element(&curve.curve.b);
        let (_, _, representatives, _) = construct_base(
            &fast,
            &curve,
            b,
            220,
            curve.subgroup_order.to_u64().unwrap(),
        );
        let reps: Vec<u64> = representatives
            .iter()
            .map(|point| point.unwrap()[0])
            .collect();
        let basis = NormalBasis::new(&gf);
        let solver = S3Solver::new(&gf, b);
        let full = build_index(&gf, &basis, &solver, &reps, false);
        let folded = build_index(&gf, &basis, &solver, &reps, true);
        assert_eq!(full.pair_candidates, 2_565_200);
        assert_eq!(folded.pair_candidates, 1_282_710);
        assert_eq!(full.states.len(), folded.states.len());
        assert_eq!(full.table.len, folded.table.len);
        for &(key, value) in &full.table.slots {
            if key != u64::MAX {
                assert_eq!(folded.table.get(key), Some(value));
            }
        }
    }
}
