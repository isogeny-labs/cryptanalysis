#!/usr/bin/env python3
"""Derive the field-ops-2 n=83 producer from the field-ops producer, exactly.

Parent: the field-ops producer, the n = 83 a = 1 baseline row
(`koblitz-n83-fieldops-20261104`, on main via PR #1400, run 41869146827,
frozen `fieldops_source_sha256` `8dc428ea...`). It is derived here by the
parent's own `make_fieldops_source.py` (verbatim), which re-derives its whole
chain and checks each digest; `parent_text()` checks 8dc428ea....

This producer is the parent's text with four counted, exact edits (`edits`;
each old string must occur exactly once). `check_inverse()` undoes all of them
back to the parent's bytes. The change, named R1, is one specialisation of the
parent's inlined field product and square:

R1. **A constant reduce shift at n = 83** (`fmul`, `fsqr`). The parent's
    `fast_field::mul` and `fast_field::sqr` take the field degree `n`, the
    mask `2^n - 1` and the tail `t = irr - z^n` as runtime arguments, so the
    two folds of `reduce` (`h = (lo >> n) | (hi << (128 - n))`, `ht >> n`,
    `& mask`) shift by a value the compiler cannot see even after inlining
    (`gf.n` is a field of a struct read from memory). R1 adds, at the head of
    `fmul` and of `fsqr`,

        if gf.n == 83 { return unsafe { fast_field::mul(83, (1u128 << 83) - 1,
                        (gf.irr ^ (1u128 << 83)) as u64, a, b) }; }

    and the same for `sqr`. When `gf.n == 83`, `gf.mask` is `2^83 - 1` by the
    definition of the mask and `gf.n` is 83, so the arguments are the very
    values the parent passes; the same function is called with the same
    arguments, only with `n` and `mask` as constants so the shifts fold into
    immediates. For every other field the parent's line runs unchanged. A
    reduced field element is unique, so every product and square is the
    parent's, and through it the library's. The parent's `fast_field::check`
    still runs before any use and compares `fmul` and `fsqr` (now the
    specialised path at n = 83) with the library's `gf.mul` and `gf.sqr` on
    edge cases and 65,536 pseudo-random pairs, failing closed.

The edits are the two insertions, a header comment, the summary's
`field_ops_pipeline` (the parent's name plus `+n83_const_reduce_shift`, so a
row says which producer ran), and an appended test module `fieldops2_tests`
(run by the workflow's `cargo test --bins`): the specialised product against
the library's on all 2^20 pairs of a 1,024-element sample, the specialised
square against the library's and against the parent's general path on 2^18
elements, and the field it runs on (n = 83, mask 2^83 - 1).

Nothing else changes: the proto_r12 candidate (R2) that also touched the
linear run finder was rejected and is not here.

`--check` regenerates and requires byte identity with the existing output.
"""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_fieldops_source as parent  # noqa: E402  (koblitz-n83-fieldops-20261104, verbatim)

EXAMPLES = HERE / "snapshots" / "r770" / "examples"
OUTPUT = EXAMPLES / "koblitz_orbit_dlp_fast_online_fieldops2.rs"
# protocol.json "sources.fieldops_source_sha256" of koblitz-n83-fieldops-20261104 (on main, PR #1400).
PARENT_SHA256 = "8dc428ea7d788b8041b5ce59dcff7e72ed0896f0a5a05571dd45d05e67fce772"
PIPELINE = parent.PIPELINE + "+n83_const_reduce_shift"


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def replace(text, old, new):
    found = text.count(old)
    if found != 1:
        raise ValueError("expected 1 occurrence, found %d: %r" % (found, old[:80]))
    return text.replace(old, new)


HEAD_OLD = parent.HEAD_NEW
HEAD_NEW = HEAD_OLD + """// koblitz-n83-fieldops2-20261107: derived from the field-ops producer by
// make_fieldops2_source.py; at n = 83 the inlined field product and square
// are called with the degree and mask as constants (R1). Built with
// -C target-feature=+pclmulqdq.
"""

FMUL_OLD = """    fn fmul(gf: &Gf2_128, a: u128, b: u128) -> u128 {
"""
FMUL_NEW = FMUL_OLD + """        // koblitz-n83-fieldops2-20261107 (R1): at n = 83 the degree and mask are
        // the constants gf.n and gf.mask already hold, so the folds' shifts are fixed.
        if gf.n == 83 {
            // SAFETY: as below.
            return unsafe { fast_field::mul(83, (1u128 << 83) - 1, (gf.irr ^ (1u128 << 83)) as u64, a, b) };
        }
"""

FSQR_OLD = """    fn fsqr(gf: &Gf2_128, a: u128) -> u128 {
"""
FSQR_NEW = FSQR_OLD + """        // koblitz-n83-fieldops2-20261107 (R1): as for fmul.
        if gf.n == 83 {
            // SAFETY: as below.
            return unsafe { fast_field::sqr(83, (1u128 << 83) - 1, (gf.irr ^ (1u128 << 83)) as u64, a) };
        }
"""

SUMMARY_OLD = '"field_ops_pipeline":"%s"' % parent.PIPELINE
SUMMARY_NEW = '"field_ops_pipeline":"%s"' % PIPELINE

TESTS_ANCHOR = parent.TESTS_ANCHOR
TESTS_NEW = """    #[cfg(test)]
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

""" + TESTS_ANCHOR


def parent_text():
    text = parent.derive()
    parent.check_inverse(text)
    if sha(text) != PARENT_SHA256:
        raise ValueError("the parent derivation differs from the row's frozen producer: " + sha(text))
    return text


def edits():
    return (("header", HEAD_OLD, HEAD_NEW), ("r1_fmul", FMUL_OLD, FMUL_NEW), ("r1_fsqr", FSQR_OLD, FSQR_NEW),
            ("summary", SUMMARY_OLD, SUMMARY_NEW), ("tests", TESTS_ANCHOR, TESTS_NEW))


def derive():
    text = parent_text()
    for _, old, new in edits():
        text = replace(text, old, new)
    return text


def check_inverse(text):
    """Undoing every edit in reverse gives back the parent's text byte for byte."""
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
            raise SystemExit("derived field-ops-2 source differs from " + str(OUTPUT))
    else:
        OUTPUT.write_text(text)
    print("parent_source_sha256=" + PARENT_SHA256)
    print("fieldops2_source_sha256=" + sha(text))
    print("edits=%d" % len(edits()))


if __name__ == "__main__":
    sys.exit(main())
