#!/usr/bin/env python3
"""Derive the online-frame round-2 n=83 producer from the current row's producer, exactly.

Parent: the round-2 index-build producer, the n = 83 a = 1 baseline row
(`koblitz-n83-indexbuild2-20261020`, PR #1009, run 39464544962, frozen
`indexbuild2_source_sha256` 4008a47a...). It is derived here by the parent's
own `make_indexbuild2_source.py` (verbatim), which re-derives the index-build
producer (bc6a31c7...) and the closure + index-lift producer (1d328b2e...)
through their verbatim chains and runs its own inverse check.
`parent_text()` checks 4008a47a....

This producer is the parent's text with nine counted, exact replacements
(`EDITS`; each old string must occur exactly once, and `check_inverse()`
undoes them back to the parent's bytes):

* one header comment (this file's);
* the seven wide-module replacements of `koblitz-n83-onlineframe-20261019`
  (PR #988, on main), IMPORTED from that experiment's `make_online_source.py`
  (copied verbatim here as `make_onlineframe_source.py`; its digest is
  pinned in `protocol.json`), not re-typed. They add `KIC_ONLINE_SOLVE`, read
  only by the one-target online scan:
  - `s3` (default, also when unset): the parent's online scan,
    `scan_state128_filtered::<CANON_LIFT, PIPE_COMPACT>`, unchanged;
  - `frame`: the online scan runs the rank stage's frame loop,
    `extract128::<CANON_LIFT, ORDER_FEISTEL, PIPE_FRAME>`, the same function
    and const parameters the parent's rank stage already runs under
    `KIC_RANK_SOLVE=frame` (on the M38 closure index, too);
  - `frame_s3plant`: the planted positive control, the S3 loop redone and
    compared on every state the scan reaches;
  - `online_solve` and `online_counters` in each target record; the summary's
    rank counters are read before the online scan.

  Their old strings were written against the rank-probe producer; every one
  occurs exactly once in the parent's text (checked by `replace`), none of
  them overlaps the closure, index-lift, index-build or round-2 index-build
  edits (the inverse check proves the composition is the parent plus these
  replacements, nothing else), and the setup, the root index, the rank stage
  and the `s3` online scan are the parent's bytes.
* one appended test module, `onlineframe2_tests` (before the imported
  `onlineframe_tests`, whose two tests run on this producer's own round-2
  index build): the imported comparison through `extract128` on the
  lift-keyed folded index (`INDEX_CANON_LIFT`, the arms' index
  canonicalizer), for two base sizes. `PIPE_COMPACT` there is the parent's
  online loop, byte for byte, so the frame loops are compared against the
  parent's online scan.

`--check` regenerates and requires byte identity with the existing output.
"""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_indexbuild2_source as parent  # noqa: E402  (koblitz-n83-indexbuild2-20261020, verbatim)
import make_onlineframe_source as onlineframe  # noqa: E402  (koblitz-n83-onlineframe-20261019, verbatim)

EXAMPLES = HERE / "snapshots" / "r770" / "examples"
OUTPUT = EXAMPLES / "koblitz_orbit_dlp_fast_online_onlineframe2.rs"
# protocol.json "sources.indexbuild2_source_sha256" of koblitz-n83-indexbuild2-20261020 (PR #1009).
PARENT_SHA256 = "4008a47aa13615f81134a537b5a514576e84be37d1c6fd46645d3cce16bba66e"


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


replace = parent.replace

HEAD_OLD = parent.HEAD_NEW
HEAD_NEW = HEAD_OLD + """// koblitz-n83-onlineframe2-20261021: derived from the round-2 index-build
// producer by make_onlineframe2_source.py; adds KIC_ONLINE_SOLVE (the seven
// replacements of koblitz-n83-onlineframe-20261019): the rank stage's frame
// loop in the one-target online scan, exact to the S3 loop.
"""

TESTS_ANCHOR = """    #[cfg(test)]
    mod onlineframe_tests {
"""
TESTS_NEW = """    #[cfg(test)]
    mod onlineframe2_tests {
        use super::*;

        /// The imported comparison on the arms' index: the folded index keyed
        /// by lift_scan (`INDEX_CANON_LIFT`), built by this producer's round-2
        /// state loop and insert loop. Through `extract128`, `PIPE_FRAME` and
        /// `PIPE_FRAME_S3PLANT` must return the parent's S3 loop's
        /// (`PIPE_COMPACT`, unchanged) relation, probe count, root calls and
        /// relation checks on every planted target, for two base sizes.
        #[test]
        fn online_frame_matches_s3_on_the_lift_keyed_index() {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let b = gf.from_element(&curve.curve.b);
            let r = curve.subgroup_order.to_u64().unwrap();
            let basis = NormalBasis128::new(&gf);
            let solver = S3Solver128::new(&gf, b);
            const LIFT: IndexMode128 = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_LIFT };
            let mut total = 0usize;
            for (columns, trials) in [(7usize, 40u64), (12, 40)] {
                let (points, labels, reps, _) = construct_base128(&fast, &curve, b, columns, r);
                let mut by_x: HashMap<u128, Vec<usize>> = HashMap::new();
                for (i, point) in points.iter().enumerate() {
                    by_x.entry(point.unwrap().0).or_default().push(i);
                }
                let reps: Vec<u128> = reps.iter().map(|p| p.unwrap()[0]).collect();
                let base = Base128 { points, labels, by_x, columns };
                let index = build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28, LIFT);
                let mut seed = 0x0F2A_5EED_83C0_1D21u64 ^ columns as u64;
                let mut solved = 0usize;
                for trial in 0..trials {
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
                        ($p:expr) => {{
                            let mut clock = PhaseClock::start();
                            let mut split = ExtractSplit::default();
                            let relation = extract128::<CANON_LIFT, ORDER_FEISTEL, { $p }>(
                                &gf, &fast, &basis, &solver, &index, &base, target, start, &mut clock,
                                &mut split,
                            );
                            (relation.map(|r| ((r.point_indices, r.x_codes, r.intermediates), r.probes)),
                             split.root_calls, split.relation_checks)
                        }};
                    }
                    let want = run!(PIPE_COMPACT);
                    if want.0.is_none() {
                        continue;
                    }
                    assert_eq!(run!(PIPE_FRAME), want, "the online frame loop differs from S3");
                    assert_eq!(run!(PIPE_FRAME_S3PLANT), want, "the planted loop differs from S3");
                    solved += 1;
                }
                assert!(solved >= 20, "too few planted targets decomposed at {columns} columns");
                total += solved;
            }
            assert!(total >= 40);
        }
    }

""" + TESTS_ANCHOR

# The imported replacements, in onlineframe_edits()'s order; the header edit
# is this experiment's own (the parent's header chain ends with round 2).
EDITS = (("header", HEAD_OLD, HEAD_NEW),
         ("onlineframe_code", onlineframe.SELECT_DOC_OLD, onlineframe.SELECT_DOC_NEW),
         ("select", onlineframe.SELECT_OLD, onlineframe.SELECT_NEW),
         ("online_select", onlineframe.ONLINE_SELECT_OLD, onlineframe.ONLINE_SELECT_NEW),
         ("online_counters", onlineframe.ONLINE_COUNTERS_OLD, onlineframe.ONLINE_COUNTERS_NEW),
         ("table_match", onlineframe.TABLE_MATCH_OLD, onlineframe.TABLE_MATCH_NEW),
         ("record", onlineframe.RECORD_OLD, onlineframe.RECORD_NEW),
         ("summary", onlineframe.SUMMARY_OLD, onlineframe.SUMMARY_NEW),
         ("tests", TESTS_ANCHOR, TESTS_NEW))


def parent_text():
    text = parent.derive()
    parent.check_inverse(text)
    if sha(text) != PARENT_SHA256:
        raise ValueError("the parent derivation differs from the row's frozen producer: " + sha(text))
    return text


def derive():
    text = parent_text()
    head, rest = text.split(onlineframe.WIDE_START, 1)
    wide, tail = rest.split(onlineframe.WIDE_END, 1)
    for name, old, new in EDITS:
        if name == "header":
            head = replace(head, old, new)
        else:
            wide = replace(wide, old, new)
    return head + onlineframe.WIDE_START + wide + onlineframe.WIDE_END + tail


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
            raise SystemExit("derived online-frame-2 source differs from " + str(OUTPUT))
    else:
        OUTPUT.write_text(text)
    print("parent_source_sha256=" + PARENT_SHA256)
    print("onlineframe2_source_sha256=" + sha(text))
    print("edits=%d" % len(EDITS))


if __name__ == "__main__":
    sys.exit(main())
