#!/usr/bin/env python3
"""Derive the op-counting field-ops-2 n=83 producer from the field-ops-2 producer, exactly.

Parent: the field-ops-2 producer (`koblitz-n83-fieldops2-20261107`,
`koblitz_orbit_dlp_fast_online_fieldops2.rs`, frozen
`fieldops2_source_sha256` d923d63a...). It is regenerated here by that
experiment's own `make_fieldops2_source.py` (verbatim, imported), which
re-derives its whole chain, checks every parent digest and its own inverse;
`parent_text()` then checks d923d63a....

The parent file and its binary `ic_online_fieldops2_r770` are not touched.
This script writes a new file, `derived/koblitz_orbit_dlp_fast_online_fieldops2_counted.rs`,
which `online-c/Cargo.toml` builds as `ic_online_fieldops2_counted_r770`
with the Cargo feature `op-counts`. Every edit is an exact replacement whose
old string must occur the stated number of times (`edits()`), and
`check_inverse()` undoes all of them back to the parent's bytes.

What the edits add: one counter of native work by kind (`mod opcount`,
global relaxed atomics, so a worker thread's work is counted too). Counting
is opt in twice over:

* without the `op-counts` feature every `bump` is an empty inline function
  (the uncounted build of this source);
* with the feature, counters are written only when the process runs with
  `KIC_OPCOUNTS=1` (read once). Without it the summary and every target
  record have exactly the parent's keys and values (no `op_counts` key), so
  the outputs and digests are the parent's.

With `KIC_OPCOUNTS=1` the summary gains `op_counts` (schema
`ic-op-counts/v1`, the opcounts experiment's phases: setup, rank_stage,
linear_algebra, between_linear_algebra_and_targets, targets,
after_targets_index_digest, end_to_end) and every target record gains its
online interval's counts. Counter reads are outside every timed interval,
but the counting binary is a separate counting pass: it is never a timed
arm.

Kinds and sites (the opcounts experiment's 24 kinds and classes, unchanged,
so `band.py` prices them as before):

* group: `ec_add`, `ec_double`, `ec_add_trivial`, `ec_scalar_mul`, through
  counted wrappers of the library group law at every production call site in
  `mod wide` (`lift128`, the base construction, the rank-stage queries, the
  factor-log verification and the target checks). `counted_add` classifies
  with the library's tests and calls the library's `add`.
  `counted_scalar_mul` returns the library's `scalar_mul` result; with
  counting on it also walks the library's double-and-add over the counted
  wrappers to count, and asserts the two results are equal.
* endomorphism: `frobenius_x` (x^(2^s), s != 0: the (n - 1) rotated stored
  roots of each scanned state, the n squarings of each shifted
  representative row, the 2 (n - 1) rotations of a new frame, and the two
  phi^s rotations of each regular frame candidate with s != 0),
  `fold_rotations` (2 per rebuilt mate state), `ec_frobenius` (base
  construction).
* native: `s3_root_solves` (every S3 solve: `S3Solver128::prepare`, the
  index build's `s3_roots_from_inverses`, and each regular frame candidate,
  whose two partner words x(T_s +- R_k) are the S3 roots of the pair, formed
  from one shared inversion), `s3_root_solves_library` (the library
  solver's calls), `canonicalizations` (`target_canonical`,
  `index_canonical128`, and 8 per `lift_linear_lanes8`),
  `root_index_probes` (every root-table `get`, both layouts),
  `root_index_inserts`, `root_filter_queries`, `root_filter_inserts`,
  `relation_lifts`, `ec_lift_x` (base construction's points from x, and
  `frame_root_xy`, a point's y from its x, two per frame state),
  `la_row_eliminations`, `la_mulmods`, `la_inversions`, `descent_mulmods`.
* field (reported, not priced): `field_mul`, `field_sqr` at every call of
  the inlined `fmul` / `fsqr` plus the two linear-map squarings of each
  `prepare`, `field_inv` once per `invert128` (the products and squares inside
  an inversion are taken back out, the opcounts convention), and
  `field_half_trace`. The library group law's field work is counted by the
  wrappers from its straight-line formulas, as in the opcounts experiment.

Partly counted: the rank-cut loop `scan_state128_padd` (`PIPE_PADD*`), which
no arm of this lineage runs, and its key derivation `rankcut_keys128` (run
only by the planted frame control) count one S3 solve per regular candidate
and their field work, but not their Frobenius rotations.

`--check` regenerates and requires byte identity with the existing output.
"""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELDOPS2 = HERE.parent / "koblitz-n83-fieldops2-20261107"
sys.path.insert(0, str(FIELDOPS2))
import make_fieldops2_source as parent  # noqa: E402  (koblitz-n83-fieldops2-20261107, verbatim)

OUTPUT = HERE / "derived" / "koblitz_orbit_dlp_fast_online_fieldops2_counted.rs"
# koblitz-n83-fieldops2-20261107/protocol.json "sources.fieldops2_source_sha256".
PARENT_SHA256 = "d923d63ab823353ceebd2dfe113baa2a4934beeb59c3859eb1604851c0a6b8fc"
WIDE_START = "\nmod wide {\n"
RUN_START = "    pub fn run(arguments: &[String]) -> ! {\n"


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


# ── head (outside the wide module) ──────────────────────────────────────────

HEAD_OLD = """// -C target-feature=+pclmulqdq.
#[path = "../../../lift2/src/lib.rs"]
#[allow(dead_code)]
mod lift2;
"""
HEAD_NEW = """// -C target-feature=+pclmulqdq.
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
"""

ECHELON_OLD = """            if let Some(pivot) = &self.pivots[column] {
                let factor = row[column];
                for (value, &p) in row.iter_mut().zip(pivot.iter()).skip(column) {
"""
ECHELON_NEW = """            if let Some(pivot) = &self.pivots[column] {
                let factor = row[column];
                opcount::bump(opcount::LA_ROW_ELIMINATIONS, 1);
                opcount::bump(opcount::LA_MULMODS, (row.len() - column) as u64);
                for (value, &p) in row.iter_mut().zip(pivot.iter()).skip(column) {
"""
PIVOT_OLD = """                let inverse = powmod(row[column], self.r - 2, self.r);
"""
PIVOT_NEW = """                let inverse = powmod(row[column], self.r - 2, self.r);
                opcount::bump(opcount::LA_INVERSIONS, 1);
                opcount::bump(opcount::LA_MULMODS, (row.len() - column) as u64);
"""
SOLVE_OLD = """            let mut value = pivot[self.columns];
            for other in column + 1..self.columns {
"""
SOLVE_NEW = """            let mut value = pivot[self.columns];
            opcount::bump(opcount::LA_MULMODS, (self.columns - column - 1) as u64);
            for other in column + 1..self.columns {
"""

# ── wide module ─────────────────────────────────────────────────────────────

IMPORT_OLD = """    use crypto_lib::cryptanalysis::semaev_decomp::Gf2_128;
    use num_bigint::BigUint;
"""
IMPORT_NEW = """    use crypto_lib::cryptanalysis::semaev_decomp::Gf2_128;
    use super::opcount as oc;
    use num_bigint::BigUint;
"""
FMUL_OLD = """    fn fmul(gf: &Gf2_128, a: u128, b: u128) -> u128 {
        // koblitz-n83-fieldops2-20261107 (R1)"""
FMUL_NEW = """    fn fmul(gf: &Gf2_128, a: u128, b: u128) -> u128 {
        oc::bump(oc::FIELD_MUL, 1);
        // koblitz-n83-fieldops2-20261107 (R1)"""
FSQR_OLD = """    fn fsqr(gf: &Gf2_128, a: u128) -> u128 {
        // koblitz-n83-fieldops2-20261107 (R1)"""
FSQR_NEW = """    fn fsqr(gf: &Gf2_128, a: u128) -> u128 {
        oc::bump(oc::FIELD_SQR, 1);
        // koblitz-n83-fieldops2-20261107 (R1)"""
PREPARE_OLD = """            let denominator = if a == 0 || ps == 0 { 0 } else { fmul(&gf, a, ps) };
            PreparedRoot128 {
"""
PREPARE_NEW = """            let denominator = if a == 0 || ps == 0 { 0 } else { fmul(&gf, a, ps) };
            oc::bump(oc::S3_SOLVES, 1);
            oc::bump(oc::FIELD_SQR, 2);
            PreparedRoot128 {
"""
FINISH_OLD = """            if prepared.denominator == 0 {
                return s3_x_roots_128(gf, self.b, prepared.left, prepared.right);
            }
"""
FINISH_NEW = """            if prepared.denominator == 0 {
                return s3_x_roots_128_counted(gf, self.b, prepared.left, prepared.right);
            }
"""
FINISH_HT_OLD = """            let first = fmul(&gf, q, self.half_trace.apply(d));
"""
FINISH_HT_NEW = """            oc::bump(oc::FIELD_HALF_TRACE, 1);
            let first = fmul(&gf, q, self.half_trace.apply(d));
"""
INVERT_OLD = """    fn invert128(gf: &Gf2_128, basis: &NormalBasis128, a: u128) -> u128 {
        let e = gf.n - 1;
"""
INVERT_NEW = """    fn invert128(gf: &Gf2_128, basis: &NormalBasis128, a: u128) -> u128 {
        oc::bump(oc::FIELD_INV, 1);
        let _inversion = oc::InversionScope::new();
        let e = gf.n - 1;
"""
TABLE_INSERT_OLD = """        fn insert_if_absent(&mut self, key: u128, value: u64) {
            let mask = self.slots.len() - 1;
"""
TABLE_INSERT_NEW = """        fn insert_if_absent(&mut self, key: u128, value: u64) {
            oc::bump(oc::ROOT_INSERTS, 1);
            let mask = self.slots.len() - 1;
"""
TABLE_GET_OLD = """        fn get(&self, key: u128) -> Option<u64> {
            if self
                .bloom
"""
TABLE_GET_NEW = """        fn get(&self, key: u128) -> Option<u64> {
            oc::bump(oc::ROOT_PROBES, 1);
            if self
                .bloom
"""
COMPACT_INSERT_OLD = """        fn insert_if_absent(&mut self, key: u128, value: u64) {
            assert!(key <= COMPACT_KEY_MASK, "compact root slot key exceeds 83 bits");
"""
COMPACT_INSERT_NEW = """        fn insert_if_absent(&mut self, key: u128, value: u64) {
            oc::bump(oc::ROOT_INSERTS, 1);
            assert!(key <= COMPACT_KEY_MASK, "compact root slot key exceeds 83 bits");
"""
COMPACT_GET_OLD = """        fn get(&self, key: u128) -> Option<u64> {
            if key > COMPACT_KEY_MASK {
"""
COMPACT_GET_NEW = """        fn get(&self, key: u128) -> Option<u64> {
            oc::bump(oc::ROOT_PROBES, 1);
            if key > COMPACT_KEY_MASK {
"""
FILTER_OLD = """        fn insert(&mut self, key: u128) {
            let (word, mask) = self.locate(key);
            self.words[word] |= mask;
        }

        #[inline(always)]
        fn contains(&self, key: u128) -> bool {
            let (word, mask) = self.locate(key);
"""
FILTER_NEW = """        fn insert(&mut self, key: u128) {
            oc::bump(oc::FILTER_INSERTS, 1);
            let (word, mask) = self.locate(key);
            self.words[word] |= mask;
        }

        #[inline(always)]
        fn contains(&self, key: u128) -> bool {
            oc::bump(oc::FILTER_QUERIES, 1);
            let (word, mask) = self.locate(key);
"""
TARGET_CANON_OLD = """    fn target_canonical<const C: u8>(basis: &NormalBasis128, v: u128) -> (u128, u32) {
        match C {
"""
TARGET_CANON_NEW = """    fn target_canonical<const C: u8>(basis: &NormalBasis128, v: u128) -> (u128, u32) {
        oc::bump(oc::CANONICALIZATIONS, 1);
        match C {
"""
INDEX_CANON_OLD = """    fn index_canonical128(basis: &NormalBasis128, canon: u8, v: u128) -> (u128, u32) {
"""
INDEX_CANON_NEW = """    fn index_canonical128(basis: &NormalBasis128, canon: u8, v: u128) -> (u128, u32) {
        oc::bump(oc::CANONICALIZATIONS, 1);
"""
LANES_OLD = """    fn lift_linear_lanes8<const N: u32>(words: &[u128; INDEX_BUILD_LANES]) -> [(u128, u32); INDEX_BUILD_LANES] {
"""
LANES_NEW = LANES_OLD + """        oc::bump(oc::CANONICALIZATIONS, INDEX_BUILD_LANES as u64);
"""
SHIFTED_OLD = """                for _ in 0..n {
                    row.push(value);
                    value = fsqr(&gf, value);
                }
                row
"""
SHIFTED_NEW = """                for _ in 0..n {
                    row.push(value);
                    value = fsqr(&gf, value);
                }
                oc::bump(oc::FROBENIUS_X, n as u64);
                row
"""
FROM_INVERSES_OLD = """    ) -> Option<[u128; 2]> {
        let p = fmul(&gf, left, right);
"""
FROM_INVERSES_NEW = """    ) -> Option<[u128; 2]> {
        oc::bump(oc::S3_SOLVES, 1);
        let p = fmul(&gf, left, right);
"""
FROM_INVERSES_HT_OLD = """        let q = fmul(&gf, p, fsqr(&gf, sum_inverse));
        let first = fmul(&gf, q, solver.half_trace.apply(d));
"""
FROM_INVERSES_HT_NEW = """        let q = fmul(&gf, p, fsqr(&gf, sum_inverse));
        oc::bump(oc::FIELD_HALF_TRACE, 1);
        let first = fmul(&gf, q, solver.half_trace.apply(d));
"""
STATE_FALLBACK_OLD = """                        s3_x_roots_128(gf, solver.b, l, r)
"""
STATE_FALLBACK_NEW = """                        s3_x_roots_128_counted(gf, solver.b, l, r)
"""
FOLD_OLD = """        let stored = &index.states[fold.slot(right, left, (fold.n - relative) % fold.n)];
        let k = relative as u32;
"""
FOLD_NEW = """        let stored = &index.states[fold.slot(right, left, (fold.n - relative) % fold.n)];
        let k = relative as u32;
        oc::bump(oc::FOLD_ROTATIONS, if k != 0 { 2 } else { 0 });
"""
SCAN_INPUTS_OLD = """        scan.inputs.clear();
        for shift in 0..n {
            for &normal_root in &state.normal_roots {
                let absolute = basis.to_poly.apply(basis.rotate(normal_root, shift));
                scan.inputs.push((absolute, target_x));
            }
        }
"""
SCAN_INPUTS_NEW = SCAN_INPUTS_OLD + """        oc::bump(oc::FROBENIUS_X, (n as u64 - 1) * state.normal_roots.len() as u64);
"""
LIFT_OLD = """    ) -> Option<[usize; 4]> {
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
"""
LIFT_NEW = """    ) -> Option<[usize; 4]> {
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
"""
COUNTED_GROUP_LAW = """
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
"""
FRAME_BUILD_OLD = """        FRAME_BUILDS.fetch_add(1, Ordering::Relaxed);
        let n = basis.n;
"""
FRAME_BUILD_NEW = """        FRAME_BUILDS.fetch_add(1, Ordering::Relaxed);
        let n = basis.n;
        oc::bump(oc::FROBENIUS_X, 2 * (n as u64 - 1));
"""
FRAME_ROOT_OLD = """    ) -> Option<(u128, u128)> {
        let xp = basis.to_poly.apply(xn);
        if xp == 0 {
            return None;
        }
"""
FRAME_ROOT_NEW = """    ) -> Option<(u128, u128)> {
        oc::bump(oc::EC_LIFT_X, 1);
        let xp = basis.to_poly.apply(xn);
        if xp == 0 {
            return None;
        }
"""
FRAME_ROOT_HT_OLD = """        let u = solver.half_trace.apply(rhs);
        Some((xp, fmul(&gf, xp, u)))
"""
FRAME_ROOT_HT_NEW = """        oc::bump(oc::FIELD_HALF_TRACE, 1);
        let u = solver.half_trace.apply(rhs);
        Some((xp, fmul(&gf, xp, u)))
"""
FRAME_PAIR_OLD = """                let pair: [u128; 2] = if fr.regular[i] {
                    let inverse = fr.inverse[i];
"""
FRAME_PAIR_NEW = """                let pair: [u128; 2] = if fr.regular[i] {
                    oc::bump(oc::S3_SOLVES, 1);
                    oc::bump(oc::FROBENIUS_X, if shift != 0 { 2 } else { 0 });
                    let inverse = fr.inverse[i];
"""
RANKCUT_PAIR_OLD = """            let pair: [u128; 2] = if pad.regular[i] {
"""
RANKCUT_PAIR_NEW = """            let pair: [u128; 2] = if pad.regular[i] {
                oc::bump(oc::S3_SOLVES, 1);
"""
CONSTRUCT_OLD = """            for point in fast.points_with_x(b, raw_x as u128) {
                let Some((px, py)) = fast.scalar_mul(point, &curve.cofactor) else {
"""
CONSTRUCT_NEW = """            oc::bump(oc::EC_LIFT_X, 1);
            for point in fast.points_with_x(b, raw_x as u128) {
                let Some((px, py)) = counted_scalar_mul(fast, point, &curve.cofactor) else {
"""
CONSTRUCT_KEY_OLD = """                for _ in 1..n {
                    x = fsqr(&gf, x);
                    key = key.min(x);
                }
"""
CONSTRUCT_KEY_NEW = CONSTRUCT_KEY_OLD + """                oc::bump(oc::CANONICALIZATIONS, 1);
                oc::bump(oc::FROBENIUS_X, n as u64 - 1);
"""
CONSTRUCT_FROB_OLD = """                    cx = fsqr(&gf, cx);
                    cy = fsqr(&gf, cy);
"""
CONSTRUCT_FROB_NEW = CONSTRUCT_FROB_OLD + """                    oc::bump(oc::EC_FROBENIUS, 1);
"""
CONSTRUCT_CHECK_OLD = """            fast.scalar_mul(rep, &BigUint::from(lambda)),
            rep.map(|(x, y)| (fsqr(&gf, x), fsqr(&gf, y))),
"""
CONSTRUCT_CHECK_NEW = """            counted_scalar_mul(fast, rep, &BigUint::from(lambda)),
            rep.map(|(x, y)| (fsqr(&gf, x), fsqr(&gf, y))),
"""
SELFTEST_OLD = """                s3_x_roots_128(&gf, b, x, y)
"""
SELFTEST_NEW = """                s3_x_roots_128_counted(&gf, b, x, y)
"""
DESCENT_OLD = """                    (acc + super::mulmod(coefficient, logs[column], r)) % r
"""
DESCENT_NEW = """                    oc::bump(oc::DESCENT_MULMODS, 1);
                    (acc + super::mulmod(coefficient, logs[column], r)) % r
"""
RUN_START_OLD = RUN_START + """        assert_eq!(arguments.len(), 5);
        let process_started = Instant::now();
"""
RUN_START_NEW = RUN_START_OLD + """        let ops_start = oc::snapshot();
"""
SETUP_END_OLD = """        let setup_ms = ms(setup_started.elapsed());
"""
SETUP_END_NEW = SETUP_END_OLD + """        let ops_setup = oc::snapshot();
"""
RANK_END_OLD = """        let rank_elapsed = rank_started.elapsed();
        let rank_ms = ms(rank_elapsed);
"""
RANK_END_NEW = RANK_END_OLD + """        let ops_rank = oc::snapshot();
"""
LA_END_OLD = """        let la_elapsed = la_started.elapsed();
        let la_ms = ms(la_elapsed);
"""
LA_END_NEW = LA_END_OLD + """        let ops_la = oc::snapshot();
        let mut ops_targets_start = None;
"""
TARGET_START_OLD = """            let online_counters = HwCounters::open();
            online_counters.start();
"""
TARGET_START_NEW = """            let ops_target_start = oc::snapshot();
            ops_targets_start.get_or_insert(ops_target_start);
""" + TARGET_START_OLD
TARGET_END_OLD = """            let online_hw_counts = online_counters.stop();
"""
TARGET_END_NEW = TARGET_END_OLD + """            let ops_target = oc::snapshot();
"""
RECORD_OLD = """            writeln!(out, "{record}").unwrap();
        }
        let targets_ms = targets_started.elapsed().as_secs_f64() * 1000.0;
"""
RECORD_NEW = """            let mut record = record;
            if oc::on() {
                record["op_counts"] = oc::delta(&ops_target_start, &ops_target);
            }
            writeln!(out, "{record}").unwrap();
        }
        let targets_ms = targets_started.elapsed().as_secs_f64() * 1000.0;
        let ops_targets = oc::snapshot();
"""
SUMMARY_OLD = """        summary["factor_log_table"] = json!({
"""
SUMMARY_NEW = """        let ops_after = oc::snapshot();
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
"""

TESTS_ANCHOR = """    #[cfg(test)]
    mod fieldops2_tests {
"""
COUNT_TESTS = """    // koblitz-n83-opcounts2-20261108: the counted wrappers return the
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

"""


def wide_run_group_law(text):
    """Every library group-law call in `wide::run` (to the end of `mod wide`) is counted."""
    start = text.index(RUN_START, text.index(WIDE_START))
    end = text.index("\n}\n", start)
    region = text[start:end]
    if region.count("fast.add(") != 1 or region.count("fast.scalar_mul(") != 4:
        raise ValueError("unexpected group-law calls in wide::run: add %d, scalar_mul %d"
                         % (region.count("fast.add("), region.count("fast.scalar_mul(")))
    new = region.replace("fast.add(", "counted_add(&fast, ").replace("fast.scalar_mul(", "counted_scalar_mul(&fast, ")
    return ("wide_run_group_law", region, new, 1)


def edits(text=None):
    """(name, old, new, count) in application order. The last edit depends on the text it is applied to."""
    out = [
        ("head", HEAD_OLD, HEAD_NEW, 1),
        ("echelon", ECHELON_OLD, ECHELON_NEW, 1),
        ("pivot", PIVOT_OLD, PIVOT_NEW, 1),
        ("back_substitution", SOLVE_OLD, SOLVE_NEW, 1),
        ("import", IMPORT_OLD, IMPORT_NEW, 1),
        ("fmul", FMUL_OLD, FMUL_NEW, 1),
        ("fsqr", FSQR_OLD, FSQR_NEW, 1),
        ("prepare", PREPARE_OLD, PREPARE_NEW, 1),
        ("finish_exceptional", FINISH_OLD, FINISH_NEW, 1),
        ("finish_half_trace", FINISH_HT_OLD, FINISH_HT_NEW, 1),
        ("invert", INVERT_OLD, INVERT_NEW, 1),
        ("table_insert", TABLE_INSERT_OLD, TABLE_INSERT_NEW, 1),
        ("table_get", TABLE_GET_OLD, TABLE_GET_NEW, 1),
        ("compact_insert", COMPACT_INSERT_OLD, COMPACT_INSERT_NEW, 1),
        ("compact_get", COMPACT_GET_OLD, COMPACT_GET_NEW, 1),
        ("filter", FILTER_OLD, FILTER_NEW, 1),
        ("target_canonical", TARGET_CANON_OLD, TARGET_CANON_NEW, 1),
        ("index_canonical", INDEX_CANON_OLD, INDEX_CANON_NEW, 1),
        ("lanes8", LANES_OLD, LANES_NEW, 1),
        ("shifted_rows", SHIFTED_OLD, SHIFTED_NEW, 1),
        ("roots_from_inverses", FROM_INVERSES_OLD, FROM_INVERSES_NEW, 1),
        ("roots_from_inverses_half_trace", FROM_INVERSES_HT_OLD, FROM_INVERSES_HT_NEW, 1),
        ("state_fallback", STATE_FALLBACK_OLD, STATE_FALLBACK_NEW, 1),
        ("fold", FOLD_OLD, FOLD_NEW, 1),
        ("scan_inputs", SCAN_INPUTS_OLD, SCAN_INPUTS_NEW, 3),
        ("lift", LIFT_OLD, LIFT_NEW, 1),
        ("group_law", "\n    fn lift128(\n", COUNTED_GROUP_LAW, 1),
        ("frame_build", FRAME_BUILD_OLD, FRAME_BUILD_NEW, 1),
        ("frame_root", FRAME_ROOT_OLD, FRAME_ROOT_NEW, 1),
        ("frame_root_half_trace", FRAME_ROOT_HT_OLD, FRAME_ROOT_HT_NEW, 1),
        ("frame_pair", FRAME_PAIR_OLD, FRAME_PAIR_NEW, 1),
        ("rankcut_pair", RANKCUT_PAIR_OLD, RANKCUT_PAIR_NEW, 2),
        ("construct", CONSTRUCT_OLD, CONSTRUCT_NEW, 1),
        ("construct_key", CONSTRUCT_KEY_OLD, CONSTRUCT_KEY_NEW, 1),
        ("construct_frobenius", CONSTRUCT_FROB_OLD, CONSTRUCT_FROB_NEW, 1),
        ("construct_check", CONSTRUCT_CHECK_OLD, CONSTRUCT_CHECK_NEW, 1),
        ("selftest", SELFTEST_OLD, SELFTEST_NEW, 1),
        ("descent", DESCENT_OLD, DESCENT_NEW, 1),
        ("run_start", RUN_START_OLD, RUN_START_NEW, 1),
        ("setup_end", SETUP_END_OLD, SETUP_END_NEW, 1),
        ("rank_end", RANK_END_OLD, RANK_END_NEW, 1),
        ("la_end", LA_END_OLD, LA_END_NEW, 1),
        ("target_start", TARGET_START_OLD, TARGET_START_NEW, 1),
        ("target_end", TARGET_END_OLD, TARGET_END_NEW, 1),
        ("record", RECORD_OLD, RECORD_NEW, 1),
        ("summary", SUMMARY_OLD, SUMMARY_NEW, 1),
        ("tests", TESTS_ANCHOR, COUNT_TESTS + TESTS_ANCHOR, 1),
    ]
    return out


def replace(text, name, old, new, count):
    found = text.count(old)
    if found != count:
        raise ValueError("edit %s: expected %d occurrence(s), found %d of:\n%s" % (name, count, found, old[:200]))
    return text.replace(old, new)


def parent_text():
    text = parent.derive()
    parent.check_inverse(text)
    if sha(text) != PARENT_SHA256:
        raise ValueError("the parent derivation differs from the frozen field-ops-2 producer: " + sha(text))
    return text


def derive():
    text = parent_text()
    for name, old, new, count in edits():
        text = replace(text, name, old, new, count)
    name, old, new, count = wide_run_group_law(text)
    return replace(text, name, old, new, count)


def check_inverse(text):
    """Undoing every edit in reverse order gives back the parent's text byte for byte."""
    steps = list(edits())
    region_start = text.index(RUN_START, text.index(WIDE_START))
    region_end = text.index("\n}\n", region_start)
    region = text[region_start:region_end]
    old = region.replace("counted_add(&fast, ", "fast.add(").replace("counted_scalar_mul(&fast, ", "fast.scalar_mul(")
    steps.append(("wide_run_group_law", old, region, 1))
    for name, old, new, count in reversed(steps):
        if text.count(new) != count:
            raise ValueError("edit %s is not present exactly %d time(s)" % (name, count))
        text = text.replace(new, old)
    if sha(text) != PARENT_SHA256:
        raise ValueError("the edits do not invert to the parent")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = derive()
    check_inverse(text)
    if args.check:
        if OUTPUT.read_text() != text:
            raise SystemExit("derived counted source differs from " + str(OUTPUT))
    else:
        OUTPUT.parent.mkdir(exist_ok=True)
        OUTPUT.write_text(text)
    print("parent_source_sha256=" + PARENT_SHA256)
    print("counted2_source_sha256=" + sha(text))
    print("edits=%d" % (len(edits()) + 1))


if __name__ == "__main__":
    sys.exit(main())
