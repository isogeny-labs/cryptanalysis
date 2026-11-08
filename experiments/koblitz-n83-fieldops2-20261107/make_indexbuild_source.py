#!/usr/bin/env python3
"""Derive the index-build n=83 producer from the current row's producer, exactly.

Parent: the closure + index-lift M38I producer, the n = 83 a = 1 baseline row
(`koblitz-n83-closure-indexlift-20261019`, PR #997, frozen
`online_source_sha256` 1d328b2e...; Tier 1 qualification
`koblitz-n83-closure-indexlift-rep-20261020`, run 39359922687). It is derived
here by the parent's own `make_online_source.py` (verbatim, with its verbatim
chain: rank-probe d4394df3..., index-lift 7df72603..., closure 8916e034...).
`parent_text()` checks every one of those digests and the composition's.

This producer is the parent's text with five counted, exact replacements
(`EDITS`; each old string must occur exactly once). Three change how the
root index and the scan self-test are computed, never what they compute:

1. **Row-batched inversion in the state loop** (`folded_states128`). The
   parent solves each stored state's S3 roots with `S3Solver128::roots`,
   one field inversion per state (about 6 of the 9.7 s of the state loop
   on the local profile). Here the states of one `(left, right)` row
   (83 states, or 42 when `left == right`) go through `RootBatch128::solve`,
   the producer's own batch solver (rank and target stages): the same
   `prepare`, Montgomery's trick over the row's non-zero denominators (one
   inversion per row), and the same `finish`. A field inverse is unique, so
   every inverse, every root and every root order is the parent's; a zero
   denominator takes `finish`'s scalar fallback exactly as `roots` does.
   The states are pushed in the parent's order, and the vector is allocated
   once at `fold.stored()`.
2. **Look-ahead canonicalization with a prefetched home slot** (the compact
   table insert loop). The parent canonicalizes root i and inserts it, one
   cache and TLB miss after another into a 1 GiB table. Here root i + 32 is
   canonicalized (`index_canonical128`, the same call, once per root, in
   increasing root order) and its home slot prefetched while root i is
   inserted. The inserts are the parent's, in the parent's order, into the
   same `CompactRootTable128`, so every slot word is the parent's
   (`table_slots_blake3`). The base-table branch is unchanged.
3. **The full scan self-test with eight images at a time**
   (`scan_permutation_selftest`). The predicate is the parent's, over the
   same domain: every image is below the domain, no in-range image repeats,
   and the in-range images number `len`. Only the evaluation order changes
   (eight `apply` calls, then their eight checks), so the verdict is the
   parent's for every `(len, key)` and every `apply`. Nothing is sampled or
   skipped.

The other two edits are the header comment and one summary field,
`index_build_pipeline`, so a receipt names which build ran (absent in the
parent's summaries).

`indexbuild_tests` (one test module, appended): the parent's state loop, insert
loop and self-test are kept there verbatim as references, and the derived
ones must reproduce their states, slot words, planted-check counts and
verdicts (folded and planted modes, all three index canonicalizers, both
table layouts, small and real lengths, and planted non-bijections).

`--check` regenerates and requires byte identity with the existing output.
"""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_online_source as parent  # noqa: E402  (koblitz-n83-closure-indexlift-20261019, verbatim)

EXAMPLES = HERE / "snapshots" / "r770" / "examples"
OUTPUT = EXAMPLES / "koblitz_orbit_dlp_fast_online_indexbuild.rs"
# protocol.json "sources.online_source_sha256" of koblitz-n83-closure-indexlift-20261019 (PR #997).
PARENT_SHA256 = "1d328b2e461a299f8daa2cdc79ca67568173504c569e94165f88c5acba79f0ea"
PIPELINE = "row_batched_inverse+lookahead32_prefetch+selftest_lanes8"


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def replace(text, old, new):
    found = text.count(old)
    if found != 1:
        raise ValueError("expected 1 occurrence, found %d: %r" % (found, old[:80]))
    return text.replace(old, new)


HEAD_OLD = """// KIC_SCAN_SELFTEST=full | sampled and two layout digests (KIC_INDEX_DIGEST).
"""
HEAD_NEW = HEAD_OLD + """// koblitz-n83-indexbuild-20261020: derived from the closure + index-lift
// producer by make_indexbuild_source.py; the same root index and self-test
// verdict, computed with one inversion per state row, a prefetched
// look-ahead insert loop and an eight-image self-test loop.
"""

STATES_OLD = """        let n = gf.n as usize;
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
"""
STATES_NEW = """        let n = gf.n as usize;
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
"""

INSERT_OLD = """            // The same inserts, in the same order, into the 16-byte layout.
            let mut slots = CompactRootTable128::with_capacity(states.len() * 2);
            for state in &states {
                for &root in &state.normal_roots {
                    let (canonical, shift) = index_canonical128(basis, mode.canon, root);
                    slots.insert_if_absent(
                        canonical,
                        pack(state.left, state.right, state.relative, shift),
                    );
                }
            }
"""
INSERT_NEW = """            // The same inserts, in the same order, into the 16-byte layout.
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
"""

SELFTEST_OLD = """    fn scan_permutation_selftest(len: usize, key: u64) -> bool {
        let permutation = ScanPermutation::new(len, key);
        let mut seen = vec![0u64; len.div_ceil(64)];
        let mut visited = 0usize;
        for index in 0..permutation.domain {
            let image = permutation.apply(index);
            if image >= permutation.domain {
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
"""
SELFTEST_NEW = """    fn scan_permutation_selftest(len: usize, key: u64) -> bool {
        let permutation = ScanPermutation::new(len, key);
        bijection_selftest_lanes(len, permutation.domain, |index| permutation.apply(index))
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
"""

CONST_OLD = """    const INDEX_CANON_SELECTED: u8 = 0;
"""
CONST_NEW = """    // koblitz-n83-indexbuild-20261020: roots canonicalized ahead of the insert.
    const INDEX_BUILD_LOOKAHEAD: usize = 32;
    const INDEX_CANON_SELECTED: u8 = 0;
"""

SUMMARY_OLD = """            "index_canonicalizer":index_canon_name,
"""
SUMMARY_NEW = SUMMARY_OLD + """            "index_build_pipeline":"%s",
""" % PIPELINE

TESTS_ANCHOR = """    #[cfg(test)]
    mod stacked_tests {
"""
TESTS_NEW = """    #[cfg(test)]
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
                            value = gf.sqr(value);
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

""" + TESTS_ANCHOR

EDITS = (("header", HEAD_OLD, HEAD_NEW), ("const", CONST_OLD, CONST_NEW), ("states", STATES_OLD, STATES_NEW),
         ("insert", INSERT_OLD, INSERT_NEW), ("selftest", SELFTEST_OLD, SELFTEST_NEW),
         ("summary", SUMMARY_OLD, SUMMARY_NEW), ("tests", TESTS_ANCHOR, TESTS_NEW))


def parent_text():
    text = parent.derive()
    if sha(text) != PARENT_SHA256:
        raise ValueError("the parent derivation differs from the row's frozen producer: " + sha(text))
    return text


def derive():
    text = parent_text()
    for _, old, new in EDITS:
        text = replace(text, old, new)
    return text


def check_inverse(text):
    """Undoing the edits in reverse gives back the parent's text byte for byte."""
    for name, old, new in reversed(EDITS):
        if text.count(new) != 1:
            raise ValueError("edit %s is not present exactly once" % name)
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
            raise SystemExit("derived index-build source differs from " + str(OUTPUT))
    else:
        OUTPUT.write_text(text)
    print("parent_source_sha256=" + PARENT_SHA256)
    print("indexbuild_source_sha256=" + sha(text))
    print("edits=%d" % len(EDITS))


if __name__ == "__main__":
    sys.exit(main())
