#!/usr/bin/env python3
"""Derive the rank-finder n=83 producer from the current row's producer, exactly.

Parent: the round-2 index-build producer, the n = 83 a = 1 baseline row
(`koblitz-n83-indexbuild2-20261020`, PR #1009, run 39464544962, frozen
`indexbuild2_source_sha256` 4008a47a...). It is derived here by the parent's
own `make_indexbuild2_source.py` (verbatim), which itself re-derives the
index-build producer (bc6a31c7..., with its verbatim chain) and checks that
its edits invert to it. `parent_text()` checks 4008a47a... and re-runs the
parent's inverse check.

This producer is the parent's text with six counted, exact replacements
(`edits()`; each old string must occur exactly once, and `check_inverse()`
undoes them back to the parent's bytes). Two of them (`keys`, `push`)
change how the rank stage's probe keys are computed, never what they are:

**C7 in the rank stage's probe loop** (`scan_state128_frame`, the loop of
`KIC_RANK_SOLVE=frame` / `frame_plant`, used only by the rank stage). The
parent canonicalizes every partner word with `target_canonical::<C>`, which
for `C = CANON_LIFT` is `lift_scan_wide(v, 83)`. Round 2 proved (and
tested on every stored root of K600, M38 and M10) that the linear run
finder `lift_linear_lanes8::<83>` returns lift_scan's (key, shift) for
every 83-bit word: for a nonconstant word, z_1 = !v and
z_(j+1) = z_j & rotl(z_j, 1) end at Z_L, the tops of all longest zero
runs (lift_scan's final run set), and the candidate loop and tie rule
(least rotation, ties to the smaller shift) are lift_scan's own; 0 and the
all-ones word give shift 0. Here the partner words are pushed in the
parent's order with their candidate index, and every time eight keys are
pending their (canonical, shift) are computed together by the round-2
function and their home slots prefetched; the at most seven left at the
end of the state take the parent's call. Every key, partner, shift,
candidate and pair start is the parent's, before any lookup, so the probe
positions, first hit, relation, root calls and counters are the parent's.
`frame_plant` still recomputes every key by the rank-cut loop with
lift_scan and compares them key by key (now: linear keys against
lift_scan). For any other canonicalizer or field size the parent's code
runs unchanged.

The other four edits are the header comment, one constant, the summary
field `rank_probe_pipeline` (`linear_canon_lanes8`; the parent emits no
such field) and one appended test module that keeps the parent's
`scan_state128_frame` verbatim (re-indented, renamed
`parent_scan_state128_frame`) and requires the derived loop to reproduce
its relations, probe counts, split counters, keys and pair starts.

`--check` regenerates and requires byte identity with the existing output.
"""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_indexbuild2_source as parent  # noqa: E402  (koblitz-n83-indexbuild2-20261020, verbatim)

EXAMPLES = HERE / "snapshots" / "r770" / "examples"
OUTPUT = EXAMPLES / "koblitz_orbit_dlp_fast_online_rankfinder.rs"
# protocol.json "sources.indexbuild2_source_sha256" of koblitz-n83-indexbuild2-20261020 (PR #1009).
PARENT_SHA256 = "4008a47aa13615f81134a537b5a514576e84be37d1c6fd46645d3cce16bba66e"
PIPELINE = "linear_canon_lanes8"


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
HEAD_NEW = HEAD_OLD + """// koblitz-n83-rankfinder-20261021: derived from the round-2 index-build
// producer by make_rankfinder_source.py; the rank stage's probe keys
// computed with the linear run finder, eight keys at a time.
"""

CONST_OLD = """    const INDEX_BUILD_LANES: usize = 8;
"""
CONST_NEW = CONST_OLD + """    // koblitz-n83-rankfinder-20261021: the rank stage's probe keys are
    // canonicalized eight at a time (lift_linear_lanes8).
    const RANK_PROBE_LANES: usize = INDEX_BUILD_LANES;
"""

# The parent's frame loop, from its doc comment to its closing brace (kept verbatim in the tests).
FRAME_START = """    /// [`scan_state128_padd`] (`PIPE_PADD`) in the target's Frobenius frame:
"""
FRAME_END = """        *probes = first + len as u64;
        split.filter_passes = passes + len as u64;
        None
    }
"""

KEYS_OLD = """        scan.keys.clear();
        fr.pair_start.clear();
        for shift in 0..n as usize {
            for k in 0..FRAME_ROOTS {
"""
KEYS_NEW = """        scan.keys.clear();
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
"""

PUSH_OLD = """                fr.pair_start.push(scan.keys.len() as u32);
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
"""
PUSH_NEW = """                fr.pair_start.push(scan.keys.len() as u32);
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
"""

SUMMARY_OLD = """            "rank_solve":rank_solve_name,
"""
SUMMARY_NEW = SUMMARY_OLD + """            "rank_probe_pipeline":"%s",
""" % PIPELINE

TESTS_ANCHOR = """    /// `P` picks the target scan's probe loop at compile time.
"""


def frame_function(text):
    start = text.index(FRAME_START)
    end = text.index(FRAME_END, start) + len(FRAME_END)
    body = text[start:end]
    if text.count(body) != 1:
        raise ValueError("the parent's frame loop is not unique")
    return body


def tests_new(parent_frame):
    renamed = parent_frame.replace("    fn scan_state128_frame<const C: u8, const P: u8>(",
                                   "    fn parent_scan_state128_frame<const C: u8, const P: u8>(")
    if renamed.count("fn parent_scan_state128_frame<") != 1:
        raise ValueError("the parent's frame loop signature is not unique")
    return """    #[cfg(test)]
    mod rankfinder_tests {
        // koblitz-n83-rankfinder-20261021: the parent's (koblitz-n83-indexbuild2-20261020)
        // frame loop, verbatim (re-indented, renamed), as the reference.
        use super::*;

""" + indent(renamed, 4) + """
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

""" + TESTS_ANCHOR


def parent_text():
    text = parent.derive()
    parent.check_inverse(text)
    if sha(text) != PARENT_SHA256:
        raise ValueError("the parent derivation differs from the row's frozen producer: " + sha(text))
    return text


def edits(text):
    tests = tests_new(frame_function(text))
    return (("header", HEAD_OLD, HEAD_NEW), ("const", CONST_OLD, CONST_NEW), ("keys", KEYS_OLD, KEYS_NEW),
            ("push", PUSH_OLD, PUSH_NEW), ("summary", SUMMARY_OLD, SUMMARY_NEW), ("tests", TESTS_ANCHOR, tests))


def derive():
    text = parent_text()
    for _, old, new in edits(text):
        text = replace(text, old, new)
    return text


def check_inverse(text):
    """Undoing the edits in reverse gives back the parent's text byte for byte."""
    for name, old, new in reversed(edits(parent_text())):
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
            raise SystemExit("derived rank-finder source differs from " + str(OUTPUT))
    else:
        OUTPUT.write_text(text)
    print("parent_source_sha256=" + PARENT_SHA256)
    print("rankfinder_source_sha256=" + sha(text))
    print("edits=%d" % len(edits(parent_text())))


if __name__ == "__main__":
    sys.exit(main())
