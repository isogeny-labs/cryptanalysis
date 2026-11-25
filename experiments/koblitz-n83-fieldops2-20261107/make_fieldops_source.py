#!/usr/bin/env python3
"""Derive the field-ops n=83 producer from the rank-finder producer, exactly.

Parent: the rank-finder producer, the n = 83 a = 1 baseline row
(`koblitz-n83-rankfinder-20261021`, on main, run 39527997793, frozen
`rankfinder_source_sha256` 301615b3...). It is derived here by the parent's
own `make_rankfinder_source.py` (verbatim), which re-derives its whole chain
and checks each digest; `parent_text()` checks 301615b3....

This producer is the parent's text with counted, exact edits (`edits`; each
old string must occur exactly once) and one counted call replacement
(`calls_forward`: every `gf.mul(` and `gf.sqr(` call inside `mod wide`, by
count). `check_inverse()` undoes all of them back to the parent's bytes.
None of them changes what is computed; each changes how:

F1. **Inlined field products and squares** (`fast_field`, `fmul`, `fsqr`).
    The library's `Gf2_128::mul` folds with its `clmul_u64`, which is not
    `#[inline]` and lives in the library crate, so every product makes six
    out-of-line calls (round 2's C8 enabled the carry-less multiply in the
    state loop but could not inline that call). `fast_field::mul` forms the
    same polynomial product with four carry-less 64 x 64 products (the
    library's Karatsuba uses three; both give the one product of the two
    polynomials) and reduces it with the library's two folds by the tail
    t = irr - z^n, statement for statement (`reduce` is `reduce_fold`).
    `fast_field::sqr` forms a0^2 + a1^2 z^128, the square in characteristic
    2, and the same reduction. A reduced field element is unique, so every
    product and square is the library's. Side B's binary is built with
    `-C target-feature=+pclmulqdq` (`online-b/.cargo/config.toml`) so the
    carry-less products inline. `fast_field::check` runs before any use and
    fails closed: the CPU has the instruction, the field meets the library's
    fold conditions (tail degree d <= 63, 2d < n + 2, n + d <= 129), and the
    inlined product and square equal the library's on edge cases and on
    65,536 pseudo-random pairs.
E1. **The state loop's three squarings by the inlined square.**
    `s3_roots_from_inverses` read `solver.square`, a byte-table map built by
    `S3Solver128::new` from the images `gf.sqr(e)` of the unit vectors.
    Squaring is GF(2)-linear and the table map is the linear map with those
    images, so the two agree on every element; its 45 KB of tables leave the
    state loop's cache footprint.
E2. **Byte-image lookups for every linear map** (`Linear128::apply`). The
    same eleven table lookups of the same tables and the same XORs, with the
    bytes read from `v.to_le_bytes()` instead of eleven variable shifts of v.
S4. **The scan self-test evaluated from per-round tables** (`RoundTables`).
    `ScanPermutation::apply` calls `round(right, key)` only with
    right = (index & mask) < 2^half, and every later right is masked again,
    so each round is read from a table of `round(v, key)` over [0, 2^half),
    filled by calling `round` itself. The table-evaluated `apply` is
    therefore `apply` on every index, and `scan_permutation_selftest` makes
    the parent's three checks (no image at or above the domain, no repeated
    in-range image, exactly `len` in-range images) of the same function over
    the same domain in the same order, with the parent's eight-image loop.
    The online and rank scans still evaluate `apply`; the self-test's
    sampled inverse check is unchanged.

Two more edits: the header comment and the summary field
`field_ops_pipeline` (this producer's name for the four changes; side A's
binary emits none). One appended test module (`fieldops_tests`, run by the
workflow's `cargo test --bins`) checks the equalities the proofs above rest
on: the inlined product and square against the library's on every pair of a
2^20-element sample and on edge cases, the square map against the inlined
square, the byte-image lookup against the parent's shift loop, and the
table-evaluated permutation against `apply` on every index of the M38 and
M10 domains for both self-test keys.

`--check` regenerates and requires byte identity with the existing output.
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_rankfinder_source as parent  # noqa: E402  (koblitz-n83-rankfinder-20261021, verbatim)

EXAMPLES = HERE / "snapshots" / "r770" / "examples"
OUTPUT = EXAMPLES / "koblitz_orbit_dlp_fast_online_fieldops.rs"
# protocol.json "sources.rankfinder_source_sha256" of koblitz-n83-rankfinder-20261021 (protocol sha256 3209eee1...).
PARENT_SHA256 = "301615b3e08a706575778d88103e41f45bbcb6114660ba7a725f10560cea5e45"
PIPELINE = "fmul_clmul_inline+sqr_clmul_inline+state_square_clmul+maps_le_bytes+selftest_round_tables"
WIDE = "mod wide {\n"
# Calls replaced inside `mod wide` by F1 (counted after E1, which adds three squarings).
CALLS = {"mul": 57, "sqr": 24}


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def replace(text, old, new):
    found = text.count(old)
    if found != 1:
        raise ValueError("expected 1 occurrence, found %d: %r" % (found, old[:80]))
    return text.replace(old, new)


HEAD_OLD = parent.HEAD_NEW
HEAD_NEW = HEAD_OLD + """// koblitz-n83-fieldops-20261104: derived from the rank-finder producer by
// make_fieldops_source.py; inlined field products and squares, the state
// loop's squarings by the inlined square, byte-image linear maps and the scan
// self-test from per-round tables. Built with -C target-feature=+pclmulqdq.
"""

E1_OLD = """        let c = solver.square.apply(p) ^ solver.b;
        let d = gf.mul(c, solver.square.apply(left_inverse ^ right_inverse));
"""
E1_NEW = """        // koblitz-n83-fieldops-20261104 (E1): the inlined square is the
        // table map `square` (both GF(2)-linear, equal on every unit vector).
        let c = gf.sqr(p) ^ solver.b;
        let d = gf.mul(c, gf.sqr(left_inverse ^ right_inverse));
"""
E1B_OLD = """        let q = gf.mul(p, solver.square.apply(sum_inverse));
"""
E1B_NEW = """        let q = gf.mul(p, gf.sqr(sum_inverse));
"""

E2_OLD = """        #[inline(always)]
        fn apply(&self, v: u128) -> u128 {
            let mut acc = 0u128;
            for (chunk, table) in self.tables.iter().enumerate() {
                acc ^= table[((v >> (8 * chunk)) & 0xff) as usize];
            }
            acc
        }
"""
E2_NEW = """        #[inline(always)]
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
"""

S4_TABLES_OLD = """    /// Bijection check on the real state count: every index in `[0, len)`
"""
S4_TABLES_NEW = """    /// koblitz-n83-fieldops-20261104 (S4): `ScanPermutation::apply` read from
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

""" + S4_TABLES_OLD

S4_CHECK_OLD = """    fn scan_permutation_selftest(len: usize, key: u64) -> bool {
        let permutation = ScanPermutation::new(len, key);
        bijection_selftest_lanes(len, permutation.domain, |index| permutation.apply(index))
    }
"""
S4_CHECK_NEW = """    fn scan_permutation_selftest(len: usize, key: u64) -> bool {
        let permutation = ScanPermutation::new(len, key);
        // koblitz-n83-fieldops-20261104 (S4): the same three checks of the
        // same function, `apply` read from the per-round tables.
        let rounds = RoundTables::new(&permutation);
        bijection_selftest_lanes(len, permutation.domain, |index| rounds.apply(index))
    }
"""

SUMMARY_OLD = """            "index_build_pipeline":"sum_inverse_lanes4+linear_canon_lanes8+lookahead32_prefetch+selftest_lanes8",
"""
SUMMARY_NEW = SUMMARY_OLD + """            "field_ops_pipeline":"%s",
""" % PIPELINE

FAST_ANCHOR = """    use std::io::Write;
    use std::time::Instant;
"""
FAST_MODULE = FAST_ANCHOR + """
    // koblitz-n83-fieldops-20261104 (F1): every field product and square of
    // this module, inlined (see make_fieldops_source.py for the proof).
    #[inline(always)]
    fn fmul(gf: &Gf2_128, a: u128, b: u128) -> u128 {
        // SAFETY: fast_field::check asserted the carry-less multiply before any use.
        unsafe { fast_field::mul(gf.n, gf.mask, (gf.irr ^ (1u128 << gf.n)) as u64, a, b) }
    }

    #[inline(always)]
    fn fsqr(gf: &Gf2_128, a: u128) -> u128 {
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
"""

MAIN_OLD = """        let gf = Gf2_128::new(&curve.curve.irreducible);
        let b = gf.from_element(&curve.curve.b);
"""
MAIN_NEW = """        let gf = Gf2_128::new(&curve.curve.irreducible);
        // koblitz-n83-fieldops-20261104 (F1): fail closed before any use.
        fast_field::check(&gf);
        let b = gf.from_element(&curve.curve.b);
"""

TESTS_ANCHOR = parent.TESTS_ANCHOR
TESTS_NEW = """    #[cfg(test)]
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

""" + TESTS_ANCHOR


def parent_text():
    text = parent.derive()
    parent.check_inverse(text)
    if sha(text) != PARENT_SHA256:
        raise ValueError("the parent derivation differs from the row's frozen producer: " + sha(text))
    return text


def edits():
    """Applied in order before the counted call replacement."""
    return (("header", HEAD_OLD, HEAD_NEW), ("e1", E1_OLD, E1_NEW), ("e1b", E1B_OLD, E1B_NEW),
            ("e2", E2_OLD, E2_NEW), ("s4_tables", S4_TABLES_OLD, S4_TABLES_NEW),
            ("s4_check", S4_CHECK_OLD, S4_CHECK_NEW), ("summary", SUMMARY_OLD, SUMMARY_NEW))


def post_edits():
    """Applied after the call replacement (the check keeps the library's own calls)."""
    return (("fast_field", FAST_ANCHOR, FAST_MODULE), ("main_check", MAIN_OLD, MAIN_NEW),
            ("tests", TESTS_ANCHOR, TESTS_NEW))


def wide_span(text):
    """`mod wide { ... }`: from its header to its closing brace at column 0."""
    start = text.index(WIDE)
    return start, text.index("\n}\n", start) + 3


def calls_forward(text):
    start, end = wide_span(text)
    body = text[start:end]
    for op, want in CALLS.items():
        pattern = r"(?<![\w.])gf\.%s\(" % op
        got = len(re.findall(pattern, body))
        if got != want or body.count("gf.%s(" % op) != want or ("f%s(&gf, " % op) in text:
            raise ValueError("expected %d bare gf.%s( calls in mod wide, found %d" % (want, op, got))
        body = re.sub(pattern, "f%s(&gf, " % op, body)
    return text[:start] + body + text[end:]


def calls_inverse(text):
    start, end = wide_span(text)
    body = text[start:end]
    for op, want in CALLS.items():
        if body.count("f%s(&gf, " % op) != want:
            raise ValueError("the %s call replacement is not present %d times" % (op, want))
        body = body.replace("f%s(&gf, " % op, "gf.%s(" % op)
    return text[:start] + body + text[end:]


def derive():
    text = parent_text()
    for _, old, new in edits():
        text = replace(text, old, new)
    text = calls_forward(text)
    for _, old, new in post_edits():
        text = replace(text, old, new)
    return text


def check_inverse(text):
    """Undoing every edit in reverse gives back the parent's text byte for byte."""
    for name, old, new in reversed(post_edits()):
        if text.count(new) != 1:
            raise ValueError("edit %s is not present exactly once" % name)
        text = text.replace(new, old)
    text = calls_inverse(text)
    for name, old, new in reversed(edits()):
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
            raise SystemExit("derived field-ops source differs from " + str(OUTPUT))
    else:
        OUTPUT.write_text(text)
    print("parent_source_sha256=" + PARENT_SHA256)
    print("fieldops_source_sha256=" + sha(text))
    print("edits=%d calls=%s" % (len(edits()) + len(post_edits()), CALLS))


if __name__ == "__main__":
    sys.exit(main())
