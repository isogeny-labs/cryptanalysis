#!/usr/bin/env python3
"""Derive the round-2 index-build n=83 producer from the current row's producer, exactly.

Parent: the index-build producer, the n = 83 a = 1 baseline row
(`koblitz-n83-indexbuild-20261020`, PR #1006, run 39383739494, frozen
`indexbuild_source_sha256` bc6a31c7...). It is derived here by the parent's
own `make_indexbuild_source.py` (verbatim), which itself re-derives the
closure + index-lift producer (1d328b2e..., with its verbatim chain) and
checks that its edits invert to it. `parent_text()` checks bc6a31c7....

This producer is the parent's text with seven counted, exact replacements
(`EDITS`; each old string must occur exactly once, and `check_inverse()`
undoes them back to the parent's bytes). Two change how the root index is
computed, never what it computes:

1. **C9, the state loop from fewer field products** (`folded_states128`).
   For a regular state (l != r, l != 0, r != 0) the parent's `prepare`,
   batched inversion of `a*ps` and `finish` compute, with a = (l + r)^2,
   p = l*r, ps = p^2, c = ps + b:
   q = p * ps / (a * ps) = p / a and d = c * a * a / (a * ps) = c * a / ps.
   Here q = p * (1/(l + r))^2 and d = c * (1/l + 1/r)^2, which are the same
   field elements: a / ps = ((l + r) / (l r))^2 = (1/l + 1/r)^2. The
   inverses of every shifted representative are computed once (an inverse
   of x, squared k times, is the inverse of x^(2^k); each is checked by a
   product), and one row's sums l + r share one inversion over four
   interleaved Montgomery chains. A field inverse is unique, so every q, d,
   trace test, half trace and root is the parent's, in the parent's order;
   an irregular state takes the parent's own fallback
   (`s3_x_roots_128(gf, b, l, r)`, which is what `finish` returns for a zero
   denominator). Seven field products per state instead of eleven.
2. **C7, the linear run finder for the index keys** (the compact insert
   loop). For a nonconstant 83-bit word, z_1 = !v and
   z_(j+1) = z_j & rotl(z_j, 1) has bit p set iff the j + 1 bits p, p-1,
   ..., p-j are zero (cyclically), so the last nonzero z_j is Z_L, the
   tops of all longest zero runs: exactly the run set lift_scan's greedy
   lifting ends with. The candidates (s = N - 1 - p) and the choice (least
   rotation, ties to the smaller shift; order-independent) are lift_scan's,
   so the key and the shift are lift_scan's for every word, and 0 and the
   all-ones word return shift 0 as before. Eight roots run the finder in
   lock step (a lane that has reached its Z_L keeps it by a select). The
   keys are computed once per root in increasing root order, eight at a
   time, 32 to 40 roots ahead, and their home slots prefetched; the
   inserts are the parent's, in the parent's order, so every slot word is
   the parent's. `lift_plant` checks every key against lift_scan and the
   selected canonicalizer (one count per root, as before).

The other five edits are the header comment, two constants, the new
functions (placed before `index_canonical128`), the summary field
`index_build_pipeline` (now this pipeline's name) and one appended test
module. The parent's other changes (the eight-image self-test, the
look-ahead prefetch) are kept.

`indexbuild2_tests`: the parent's state loop and compact insert loop are
kept there verbatim (re-indented) as references; the derived ones must
reproduce their states, slot words and planted-check counts, and the
linear canonicalizer must equal the full scan on every word of 3..20 bits
(scalar and eight-lane), lift_scan on small two-limb geometries
exhaustively and on 2^22 random and structured 83-bit words.

`--check` regenerates and requires byte identity with the existing output.
"""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_indexbuild_source as parent  # noqa: E402  (koblitz-n83-indexbuild-20261020, verbatim)

EXAMPLES = HERE / "snapshots" / "r770" / "examples"
OUTPUT = EXAMPLES / "koblitz_orbit_dlp_fast_online_indexbuild2.rs"
# protocol.json "sources.indexbuild_source_sha256" of koblitz-n83-indexbuild-20261020 (PR #1006).
PARENT_SHA256 = "bc6a31c734726a16de6235595e16843b346ed86c978f7efa51a6686558661bb7"
PIPELINE = "sum_inverse_lanes4+linear_canon_lanes8+lookahead32_prefetch+selftest_lanes8"


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def replace(text, old, new):
    found = text.count(old)
    if found != 1:
        raise ValueError("expected 1 occurrence, found %d: %r" % (found, old[:80]))
    return text.replace(old, new)


def indent(text, spaces):
    pad = " " * spaces
    return "".join(pad + line if line.strip() else line for line in text.splitlines(True))


HEAD_OLD = parent.HEAD_NEW
HEAD_NEW = HEAD_OLD + """// koblitz-n83-indexbuild2-20261020: derived from the index-build producer
// by make_indexbuild2_source.py; the same root index, its states computed
// with seven field products instead of eleven and its keys with the linear
// run finder, eight roots at a time.
"""

CONST_OLD = parent.CONST_NEW
CONST_NEW = """    // koblitz-n83-indexbuild2-20261020: keys computed eight roots at a time
    // into a ring of 64 (at most 40 are live).
    const INDEX_BUILD_LANES: usize = 8;
    const INDEX_BUILD_RING: usize = 64;
""" + CONST_OLD

FUNCS_ANCHOR = """    #[inline(always)]
    fn index_canonical128(basis: &NormalBasis128, canon: u8, v: u128) -> (u128, u32) {
"""
FUNCS_NEW = """    // ── koblitz-n83-indexbuild2-20261020: C7, the linear run finder ──
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
        let p = gf.mul(left, right);
        let c = solver.square.apply(p) ^ solver.b;
        let d = gf.mul(c, solver.square.apply(left_inverse ^ right_inverse));
        if (d & solver.trace_mask).count_ones() & 1 == 1 {
            return None;
        }
        let q = gf.mul(p, solver.square.apply(sum_inverse));
        let first = gf.mul(q, solver.half_trace.apply(d));
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
            chains[lane] = gf.mul(chains[lane], values[k]);
        }
        let low = gf.mul(chains[0], chains[1]);
        let high = gf.mul(chains[2], chains[3]);
        // A product of non-zero field elements is non-zero.
        let all = invert128(gf, basis, gf.mul(low, high));
        let low_inverse = gf.mul(all, high);
        let high_inverse = gf.mul(all, low);
        let mut lane_inverses = [
            gf.mul(low_inverse, chains[1]),
            gf.mul(low_inverse, chains[0]),
            gf.mul(high_inverse, chains[3]),
            gf.mul(high_inverse, chains[2]),
        ];
        for (position, &k) in regular.iter().enumerate().rev() {
            let lane = position & 3;
            inverses[k] = gf.mul(lane_inverses[lane], prefixes[k]);
            lane_inverses[lane] = gf.mul(lane_inverses[lane], values[k]);
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
                        assert!(value == 0 || gf.mul(value, here) == 1, "a shifted representative's inverse is wrong");
                        inverse = gf.sqr(inverse);
                        if value == 0 { 0 } else { here }
                    })
                    .collect()
            })
            .collect()
    }

""" + FUNCS_ANCHOR

STATES_OLD = parent.STATES_NEW
STATES_NEW = """        let n = gf.n as usize;
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
                        s3_x_roots_128(gf, solver.b, l, r)
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
"""

INSERT_OLD = parent.INSERT_NEW
INSERT_NEW = """            // The same inserts, in the same order, into the 16-byte layout.
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
"""

SUMMARY_OLD = parent.SUMMARY_NEW
SUMMARY_NEW = parent.SUMMARY_OLD + """            "index_build_pipeline":"%s",
""" % PIPELINE

TESTS_ANCHOR = """    #[cfg(test)]
    mod indexbuild_tests {
"""
TESTS_NEW = """    #[cfg(test)]
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
""" + indent(STATES_OLD, 4) + """            states
        }

        fn parent_compact(basis: &NormalBasis128, states: &[State128], canon: u8) -> CompactRootTable128 {
            let mode = IndexMode128 { fold: true, plant: false, canon };
""" + indent(INSERT_OLD, 0) + """            slots
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
                        value = gf.sqr(value);
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
                    assert_eq!(gf.mul(values[k], inverses[k]), 1, "count {count} k {k}");
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

""" + TESTS_ANCHOR

EDITS = (("header", HEAD_OLD, HEAD_NEW), ("const", CONST_OLD, CONST_NEW), ("functions", FUNCS_ANCHOR, FUNCS_NEW),
         ("states", STATES_OLD, STATES_NEW), ("insert", INSERT_OLD, INSERT_NEW),
         ("summary", SUMMARY_OLD, SUMMARY_NEW), ("tests", TESTS_ANCHOR, TESTS_NEW))


def parent_text():
    text = parent.derive()
    parent.check_inverse(text)
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
            raise SystemExit("derived index-build-2 source differs from " + str(OUTPUT))
    else:
        OUTPUT.write_text(text)
    print("parent_source_sha256=" + PARENT_SHA256)
    print("indexbuild2_source_sha256=" + sha(text))
    print("edits=%d" % len(EDITS))


if __name__ == "__main__":
    sys.exit(main())
