#!/usr/bin/env python3
"""Derive the op-counting n=83 producer from the frozen stacked producer, exactly.

Input: the stacked producer `koblitz_orbit_dlp_fast_online_stacked.rs`
(koblitz-n83-stacked-20261016), regenerated here with that experiment's own
`make_online_source.py` and required to hash to its frozen digest
(`STACKED_SHA256`, protocol.json `sources.online_source_sha256`). The frozen
file and its binary `ic_online_stacked_r770` are not touched: this script
writes a new file, `derived/koblitz_orbit_dlp_fast_online_stacked_counted.rs`,
which `online/Cargo.toml` builds as `ic_online_stacked_counted_r770`.

The edits are counted, exact replacements (each must match the stated number
of times). They add one thing: a per-thread counter of native work by kind
(`mod opcount`), written only when the crate is built with the Cargo feature
`op-counts`. Without the feature every `bump` is an empty inline function and
the summary says `op_counts: {"enabled": false}`. With it, the wide path
(64 < n <= 127, so n = 83) reports in the summary the counts per phase (setup,
rank stage, linear algebra, targets, and the index digest after the targets)
and in each target record the counts of its online interval. Counter reads
are taken outside every timed interval.

What is counted (kind -> class; `opcount::KINDS` is the single list):

* group: `ec_add` (generic affine additions: 1 inv, 2 mul, 1 sqr each),
  `ec_double` (affine doublings: 1 inv, 2 mul, 2 sqr; including those an
  addition of equal points becomes and those inside scalar multiplications);
  `ec_add_trivial` (an operand at infinity, or P + (-P): no field work);
  `ec_scalar_mul` (scalar multiplications: their doublings and additions are
  in `ec_double`, `ec_add` and `ec_add_trivial`, so this kind is a count, not
  extra work).
* endomorphism (Frobenius): `frobenius_x` (an x-coordinate raised to 2^s,
  s != 0, as a normal-basis rotation in the scans or a polynomial-basis
  squaring in the index's shifted rows); `fold_rotations` (the two root
  rotations that rebuild a folded mate state); `ec_frobenius` (a point's
  Frobenius image in base construction).
* native (IC-specific work that is not a group operation): `s3_root_solves`
  (S3 summation-polynomial root solves, every site), `s3_root_solves_library`
  (the library solver: exceptional denominators and the setup self-test),
  `canonicalizations` (Frobenius-orbit canonical forms of a root, target scan
  and index build), `root_index_probes` (root-table lookups),
  `root_index_inserts`, `root_filter_queries`, `root_filter_inserts`,
  `relation_lifts` (candidate four-point lifts; their additions are in
  `ec_add`), `ec_lift_x` (point from x in base construction),
  `la_row_eliminations`, `la_mulmods` (mod-r multiply-subtracts and scalings
  of the echelon and back substitution), `la_inversions` (pivot inversions,
  each one Fermat powmod), `descent_mulmods`.
* field: `field_mul`, `field_sqr` (including linear-map squarings),
  `field_inv` (an Itoh-Tsujii or library inversion counts once; the
  multiplications inside it are not added to `field_mul`),
  `field_half_trace`. The field counts cover the producer's own root solver
  and the library group law it calls, from the library's straight-line
  formulas. The library's exceptional S3 solver, its point-from-x and its
  setup self-test calls are counted only as calls.

Nothing here changes a computation, an order, a branch or a random stream:
every edit only adds counter writes, and the counted group-law wrappers call
the library's own `add` / `double` in the library's order (the scalar
multiplication is the library's double-and-add loop over the same calls, so
its result is the same point; `counted_scalar_mul_matches_the_library` and
`counting_leaves_relations_and_probes_unchanged` test this, and
`check_identity.py` compares the counted and uncounted binaries with the frozen
binary end to end).

`--check` regenerates and requires byte identity with the existing output.
"""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STACKED = HERE.parent / "koblitz-n83-stacked-20261016"
sys.path.insert(0, str(STACKED))
import make_online_source as stacked  # noqa: E402  (the frozen stacked derivation, unchanged)

OUTPUT = HERE / "derived" / "koblitz_orbit_dlp_fast_online_stacked_counted.rs"
# koblitz-n83-stacked-20261016/protocol.json "sources.online_source_sha256".
STACKED_SHA256 = "83b589880e5bbd80b2dcf0debf7d20ab268877d4de409c71cf5da17b2f62563c"
WIDE_START = stacked.WIDE_START
WIDE_END = stacked.WIDE_END


def replace(text, old, new, count=1):
    found = text.count(old)
    if found != count:
        raise ValueError("expected %d occurrence(s), found %d of:\n%s" % (count, found, old))
    return text.replace(old, new)


# ── head (outside the wide module) ──────────────────────────────────────────

HEAD_OLD = """// KIC_RANK_PROBE) so the rank stage runs on the compact table in process.
#[path = "../../../lift2/src/lib.rs"]
#[allow(dead_code)]
mod lift2;
"""
HEAD_NEW = """// KIC_RANK_PROBE) so the rank stage runs on the compact table in process.
// koblitz-n83-opcounts-20261023: derived from the stacked producer by
// make_counted_source.py; counts native work by kind (group operations,
// Frobenius applications, root solves, probes, inserts, canonicalizations,
// linear algebra, field operations) when built with the `op-counts` feature,
// and reports it per phase and per target. Nothing else changes.
#[path = "../../koblitz-n83-stacked-20261016/lift2/src/lib.rs"]
#[allow(dead_code)]
mod lift2;

/// koblitz-n83-opcounts-20261023: native work counted by kind, per thread
/// (the producer is single-threaded; per-thread counters keep the parallel
/// test harness exact). `bump` compiles to nothing without `op-counts`.
mod opcount {
    use serde_json::{json, Map, Value};
    use std::cell::Cell;

    pub const KINDS: [(&str, &str); 30] = [
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
        ("reserved_24", "reserved"),
        ("reserved_25", "reserved"),
        ("reserved_26", "reserved"),
        ("reserved_27", "reserved"),
        ("reserved_28", "reserved"),
        ("reserved_29", "reserved"),
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

    thread_local! {
        static COUNTS: [Cell<u64>; N] = const { [const { Cell::new(0) }; N] };
    }

    pub const ENABLED: bool = cfg!(feature = "op-counts");

    #[inline(always)]
    pub fn bump(kind: usize, by: u64) {
        #[cfg(feature = "op-counts")]
        COUNTS.with(|counts| counts[kind].set(counts[kind].get().wrapping_add(by)));
        #[cfg(not(feature = "op-counts"))]
        let _ = (kind, by);
    }

    pub fn snapshot() -> [u64; N] {
        COUNTS.with(|counts| std::array::from_fn(|kind| counts[kind].get()))
    }

    pub fn delta(before: &[u64; N], after: &[u64; N]) -> Value {
        if !ENABLED {
            return Value::Null;
        }
        let mut map = Map::new();
        for (kind, &(name, class)) in KINDS.iter().enumerate() {
            if class != "reserved" {
                map.insert(name.to_owned(), json!(after[kind] - before[kind]));
            }
        }
        Value::Object(map)
    }

    pub fn kinds() -> Value {
        let mut map = Map::new();
        for &(name, class) in KINDS.iter() {
            if class != "reserved" {
                map.insert(name.to_owned(), json!(class));
            }
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
"""
IMPORT_NEW = """    use crypto_lib::cryptanalysis::semaev_decomp::Gf2_128;
    use super::opcount as oc;
"""

PREPARE_OLD = """            let denominator = if a == 0 || ps == 0 { 0 } else { gf.mul(a, ps) };
            PreparedRoot128 {
"""
PREPARE_NEW = """            let denominator = if a == 0 || ps == 0 { 0 } else { gf.mul(a, ps) };
            oc::bump(oc::S3_SOLVES, 1);
            oc::bump(oc::FIELD_SQR, 2);
            oc::bump(oc::FIELD_MUL, 1 + (denominator != 0) as u64);
            PreparedRoot128 {
"""
FINISH_OLD = """            if prepared.denominator == 0 {
                return s3_x_roots_128(gf, self.b, prepared.left, prepared.right);
            }
            let q = gf.mul(prepared.p, gf.mul(prepared.ps, inverse));
            let c = prepared.ps ^ self.b;
            let d = gf.mul(gf.mul(c, prepared.a), gf.mul(prepared.a, inverse));
            if (d & self.trace_mask).count_ones() & 1 == 1 {
                return None;
            }
"""
FINISH_NEW = """            if prepared.denominator == 0 {
                return s3_x_roots_128_counted(gf, self.b, prepared.left, prepared.right);
            }
            let q = gf.mul(prepared.p, gf.mul(prepared.ps, inverse));
            let c = prepared.ps ^ self.b;
            let d = gf.mul(gf.mul(c, prepared.a), gf.mul(prepared.a, inverse));
            oc::bump(oc::FIELD_MUL, 5);
            if (d & self.trace_mask).count_ones() & 1 == 1 {
                return None;
            }
            oc::bump(oc::FIELD_MUL, 1);
            oc::bump(oc::FIELD_HALF_TRACE, 1);
"""
BATCH_OLD = """            if !self.regular.is_empty() {
                let mut product = 1u128;
"""
BATCH_NEW = """            if !self.regular.is_empty() {
                oc::bump(oc::FIELD_MUL, 3 * self.regular.len() as u64);
                let mut product = 1u128;
"""
INVERT_OLD = """    fn invert128(gf: &Gf2_128, basis: &NormalBasis128, a: u128) -> u128 {
        let e = gf.n - 1;
"""
INVERT_NEW = """    fn invert128(gf: &Gf2_128, basis: &NormalBasis128, a: u128) -> u128 {
        oc::bump(oc::FIELD_INV, 1);
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
SHIFTED_OLD = """                for _ in 0..n {
                    row.push(value);
                    value = gf.sqr(value);
                }
                row
"""
SHIFTED_NEW = """                for _ in 0..n {
                    row.push(value);
                    value = gf.sqr(value);
                }
                oc::bump(oc::FROBENIUS_X, n as u64);
                row
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
"""
LIFT_NEW = """    ) -> Option<[usize; 4]> {
        oc::bump(oc::RELATION_LIFTS, 1);
        let choices: Vec<&Vec<usize>> = codes
"""
COUNTED_GROUP_LAW = """
    // koblitz-n83-opcounts-20261023: the library group law with its work
    // counted. Each wrapper classifies the operands with the library's own
    // tests, counts, and then calls the library function unchanged.
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
        match (p, q) {
            (Some((x1, y1)), Some((x2, y2))) => {
                if x1 != x2 {
                    oc::bump(oc::EC_ADD, 1);
                    oc::bump(oc::FIELD_INV, 1);
                    oc::bump(oc::FIELD_MUL, 2);
                    oc::bump(oc::FIELD_SQR, 1);
                } else if (y1 ^ y2) == x1 {
                    oc::bump(oc::EC_ADD_TRIVIAL, 1);
                } else if x1 == 0 {
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
        fast.add(p, q)
    }

    /// `FastBinaryCurve128::scalar_mul`'s double-and-add loop, step for
    /// step, over the counted wrappers of the same library calls.
    fn counted_scalar_mul(fast: &FastBinaryCurve128, p: FastPoint128, k: &BigUint) -> FastPoint128 {
        oc::bump(oc::EC_SCALAR_MUL, 1);
        if k.bits() == 0 {
            return None;
        }
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
        result
    }

    #[inline]
    fn s3_x_roots_128_counted(gf: &Gf2_128, b: u128, left: u128, right: u128) -> Option<[u128; 2]> {
        oc::bump(oc::S3_SOLVES_LIBRARY, 1);
        s3_x_roots_128(gf, b, left, right)
    }

    fn lift128(
"""
CONSTRUCT_OLD = """            for point in fast.points_with_x(b, raw_x as u128) {
"""
CONSTRUCT_NEW = """            oc::bump(oc::EC_LIFT_X, 1);
            for point in fast.points_with_x(b, raw_x as u128) {
"""
CONSTRUCT_KEY_OLD = """                for _ in 1..n {
                    x = gf.sqr(x);
                    key = key.min(x);
                }
"""
CONSTRUCT_KEY_NEW = CONSTRUCT_KEY_OLD + """                oc::bump(oc::CANONICALIZATIONS, 1);
                oc::bump(oc::FROBENIUS_X, n as u64 - 1);
"""
CONSTRUCT_FROB_OLD = """                    cx = gf.sqr(cx);
                    cy = gf.sqr(cy);
"""
CONSTRUCT_FROB_NEW = CONSTRUCT_FROB_OLD + """                    oc::bump(oc::EC_FROBENIUS, 1);
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

RUN_START_OLD = """    pub fn run(arguments: &[String]) -> ! {
        assert_eq!(arguments.len(), 5);
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
TARGET_END_NEW = TARGET_END_OLD + """            let ops_target = oc::delta(&ops_target_start, &oc::snapshot());
"""
RECORD_OLD = """            writeln!(out, "{record}").unwrap();
        }
        let targets_ms = targets_started.elapsed().as_secs_f64() * 1000.0;
"""
RECORD_NEW = """            let mut record = record;
            record["op_counts"] = ops_target;
            writeln!(out, "{record}").unwrap();
        }
        let targets_ms = targets_started.elapsed().as_secs_f64() * 1000.0;
        let ops_targets = oc::snapshot();
"""
SUMMARY_OLD = """        summary["factor_log_table"] = json!({
"""
SUMMARY_NEW = """        let ops_after = oc::snapshot();
        let ops_targets_start = ops_targets_start.unwrap_or(ops_targets);
        summary["op_counts"] = if oc::ENABLED {
            json!({
                "schema": "ic-op-counts/v1",
                "enabled": true,
                "producer": "koblitz-n83-opcounts-20261023 ic_online_stacked_counted_r770 (feature op-counts)",
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
                "accounting": "setup = process start to the index built (base, normal basis and self-test, index); rank_stage = the timed rank interval; linear_algebra = echelon solve or cached-table load plus the verification of every factor log; targets = every target's online interval and the code between them; end_to_end = process start to the last target; after_targets_index_digest is diagnostic work outside every interval and outside end_to_end",
            })
        } else {
            json!({"enabled": false})
        };
        summary["factor_log_table"] = json!({
"""


def head_edits(head):
    head = replace(head, HEAD_OLD, HEAD_NEW)
    head = replace(head, ECHELON_OLD, ECHELON_NEW)
    head = replace(head, PIVOT_OLD, PIVOT_NEW)
    head = replace(head, SOLVE_OLD, SOLVE_NEW)
    return head


def wide_edits(wide):
    wide = replace(wide, IMPORT_OLD, IMPORT_NEW)
    wide = replace(wide, PREPARE_OLD, PREPARE_NEW)
    wide = replace(wide, FINISH_OLD, FINISH_NEW)
    wide = replace(wide, BATCH_OLD, BATCH_NEW)
    wide = replace(wide, INVERT_OLD, INVERT_NEW)
    wide = replace(wide, TABLE_INSERT_OLD, TABLE_INSERT_NEW)
    wide = replace(wide, TABLE_GET_OLD, TABLE_GET_NEW)
    wide = replace(wide, COMPACT_INSERT_OLD, COMPACT_INSERT_NEW)
    wide = replace(wide, COMPACT_GET_OLD, COMPACT_GET_NEW)
    wide = replace(wide, FILTER_OLD, FILTER_NEW)
    wide = replace(wide, TARGET_CANON_OLD, TARGET_CANON_NEW)
    wide = replace(wide, INDEX_CANON_OLD, INDEX_CANON_NEW)
    wide = replace(wide, SHIFTED_OLD, SHIFTED_NEW)
    wide = replace(wide, FOLD_OLD, FOLD_NEW)
    wide = replace(wide, SCAN_INPUTS_OLD, SCAN_INPUTS_NEW, count=3)
    wide = replace(wide, LIFT_OLD, LIFT_NEW)
    # Call sites first, then the wrappers (which call the library directly).
    wide = replace(wide, "fast.add(", "counted_add(&fast, ", count=6)
    wide = replace(wide, "fast.scalar_mul(", "counted_scalar_mul(&fast, ", count=6)
    wide = replace(wide, "\n    fn lift128(\n", COUNTED_GROUP_LAW)
    wide = replace(wide, CONSTRUCT_OLD, CONSTRUCT_NEW)
    wide = replace(wide, CONSTRUCT_KEY_OLD, CONSTRUCT_KEY_NEW)
    wide = replace(wide, CONSTRUCT_FROB_OLD, CONSTRUCT_FROB_NEW)
    wide = replace(wide, SELFTEST_OLD, SELFTEST_NEW)
    wide = replace(wide, DESCENT_OLD, DESCENT_NEW)
    wide = replace(wide, RUN_START_OLD, RUN_START_NEW)
    wide = replace(wide, SETUP_END_OLD, SETUP_END_NEW)
    wide = replace(wide, RANK_END_OLD, RANK_END_NEW)
    wide = replace(wide, LA_END_OLD, LA_END_NEW)
    wide = replace(wide, TARGET_START_OLD, TARGET_START_NEW)
    wide = replace(wide, TARGET_END_OLD, TARGET_END_NEW)
    wide = replace(wide, RECORD_OLD, RECORD_NEW)
    wide = replace(wide, SUMMARY_OLD, SUMMARY_NEW)
    wide = replace(wide, TESTS_ANCHOR, TESTS_ANCHOR + COUNT_TESTS)
    return wide


TESTS_ANCHOR = """    #[cfg(test)]
    mod stacked_tests {
        use super::*;
"""
COUNT_TESTS = """
        // koblitz-n83-opcounts-20261023: counting is exact and leaves the
        // computation unchanged.
        #[test]
        fn counted_scalar_mul_matches_the_library() {
            let (fast, _, _, _, base, _) = small_instance(3);
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let r = curve.subgroup_order.to_u64().unwrap();
            let mut seed = 0x0123_4567_89AB_CDEFu64;
            for trial in 0..200u64 {
                seed = digest_mix64(seed ^ trial);
                let point = base.points[(seed % base.points.len() as u64) as usize];
                let scalar = match trial {
                    0 => 0,
                    1 => 1,
                    2 => 2,
                    3 => r,
                    4 => r - 1,
                    _ => digest_mix64(seed) % (4 * r),
                };
                let k = BigUint::from(scalar);
                assert_eq!(counted_scalar_mul(&fast, point, &k), fast.scalar_mul(point, &k));
                let other = base.points[(digest_mix64(seed ^ 7) % base.points.len() as u64) as usize];
                for (p, q) in [(point, other), (point, point), (point, FastBinaryCurve128::neg(point)),
                               (None, point), (point, None), (None, None)] {
                    assert_eq!(counted_add(&fast, p, q), fast.add(p, q));
                }
            }
            if oc::ENABLED {
                // Double-and-add of a b-bit scalar: b - 1 doublings and one
                // addition per further set bit, the first set bit an add to infinity.
                let k = BigUint::from(0b1011_0001u64);
                let before = oc::snapshot();
                let point = base.points[0];
                let _ = counted_scalar_mul(&fast, point, &k);
                let after = oc::snapshot();
                let d = |kind: usize| after[kind] - before[kind];
                assert_eq!(d(oc::EC_SCALAR_MUL), 1);
                assert_eq!(d(oc::EC_DOUBLE) + d(oc::EC_ADD_TRIVIAL) + d(oc::EC_ADD), 7 + 4);
                assert_eq!(d(oc::EC_ADD_TRIVIAL), 1, "the first set bit adds to infinity");
            }
        }

        /// Relations, probes, root calls and skips of every stacked arm on
        /// 24 planted four-point targets, as one digest. It is pinned from a
        /// build without `op-counts` and must be the same with it.
        fn planted_relations_digest() -> (String, u64) {
            let (fast, gf, basis, solver, base, reps) = small_instance(9);
            let build = |table, mode| build_index128_stacked(&gf, &basis, &solver, &reps, table, 28, mode);
            let reference = build(TABLE_BASE, IndexMode128::UNFOLDED);
            let stack = build(TABLE_COMPACT, FOLDED);
            let base_fold = build(TABLE_BASE, FOLDED);
            let mut hasher = blake3::Hasher::new();
            let mut seed = 0x9E37_79B9_7F4A_7C15u64;
            let mut solved = 0u64;
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
                        let relation = extract128::<{ $c }, { $o }, { $p }>(
                            &gf, &fast, &basis, &solver, $index, &base, target, start, &mut clock,
                            &mut split,
                        );
                        if let Some(relation) = &relation {
                            solved += 1;
                            for index in relation.point_indices {
                                hasher.update(&(index as u64).to_le_bytes());
                            }
                            for word in relation.x_codes.iter().chain(&relation.intermediates) {
                                hasher.update(&word.to_le_bytes());
                            }
                            hasher.update(&relation.probes.to_le_bytes());
                        }
                        hasher.update(&[relation.is_some() as u8]);
                        for value in [split.root_calls, split.relation_checks, split.skipped_symmetric_states,
                                      split.filter_passes] {
                            hasher.update(&value.to_le_bytes());
                        }
                    }};
                }
                run!(CANON_LIFT, ORDER_FEISTEL, PIPE_OFF, &reference);
                run!(CANON_FULL, ORDER_LEFT_MAJOR, PIPE_OFF, &reference);
                run!(CANON_LIFT, ORDER_FEISTEL, PIPE_PREFETCH, &base_fold);
                run!(CANON_LIFT, ORDER_FEISTEL, PIPE_COMPACT, &stack);
                run!(CANON_FULL, ORDER_FEISTEL, PIPE_COMPACT, &stack);
            }
            (hasher.finalize().to_hex().to_string(), solved)
        }

        // From `cargo test` of this source without `op-counts` (see README).
        const PLANTED_RELATIONS_DIGEST: &str = "PINNED_BELOW";

        #[test]
        fn counting_leaves_relations_and_probes_unchanged() {
            let before = oc::snapshot();
            let (digest, solved) = planted_relations_digest();
            let after = oc::snapshot();
            assert!(solved >= 100, "only {solved} planted relations");
            if PLANTED_RELATIONS_DIGEST != "PINNED_BELOW" {
                assert_eq!(digest, PLANTED_RELATIONS_DIGEST,
                           "relations, probes or root calls changed (op-counts {})", oc::ENABLED);
            } else {
                println!("planted_relations_digest={digest}");
            }
            if oc::ENABLED {
                assert!(after[oc::ROOT_PROBES] > before[oc::ROOT_PROBES]);
                assert!(after[oc::S3_SOLVES] > before[oc::S3_SOLVES]);
                assert!(after[oc::EC_ADD] > before[oc::EC_ADD]);
            } else {
                assert_eq!(before, [0; oc::N]);
                assert_eq!(after, [0; oc::N]);
            }
        }
"""


def stacked_text():
    text = stacked.derive(stacked.tablefilter_text())
    digest = hashlib.sha256(text.encode()).hexdigest()
    if digest != STACKED_SHA256:
        raise ValueError("stacked derivation differs from koblitz-n83-stacked-20261016's frozen producer: "
                         + digest)
    return text


def derive(text, pinned_digest=None):
    head, rest = text.split(WIDE_START, 1)
    wide, tail = rest.split(WIDE_END, 1)
    head = head_edits(head)
    wide = wide_edits(wide)
    if pinned_digest:
        wide = replace(wide, '"PINNED_BELOW";', '"%s";' % pinned_digest)
    return head + WIDE_START + wide + WIDE_END + tail


# The planted-relations digest, from `cargo test` of the unpinned source
# without `op-counts` (README, "Bit identity"). `None` writes the unpinned
# source, which prints the digest instead of asserting it.
PINNED_DIGEST = "43045c8089a56bcdb199fb5a4b238910ca6b3678bd6bcf621e5e182c1b2deca4"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--unpinned", action="store_true", help="write the source without the pinned digest")
    args = parser.parse_args()
    text = derive(stacked_text(), None if args.unpinned else PINNED_DIGEST)
    if args.check:
        if OUTPUT.read_text() != text:
            raise SystemExit("derived counted source differs from " + str(OUTPUT))
    else:
        OUTPUT.parent.mkdir(exist_ok=True)
        OUTPUT.write_text(text)
    print("counted_source_sha256=" + hashlib.sha256(text.encode()).hexdigest())


if __name__ == "__main__":
    sys.exit(main())
