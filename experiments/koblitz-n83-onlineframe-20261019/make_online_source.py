#!/usr/bin/env python3
"""Derive the online-frame n=83 K600 producer from the rank-probe producer, exactly.

Input: `snapshots/r770/examples/koblitz_orbit_dlp_fast_online_logcache.rs`
(crypto 770f6a69 plus B's `ic_log_cache.patch`, restored and digest-checked
by `restore.py`).

1. `make_rankprobe_source.py` is `koblitz-n83-rankprobe-20261019`'s
   `make_online_source.py` (PR #980), verbatim, with its verbatim parents
   (`make_rankcut_source.py`, `make_stacked_source.py`,
   `make_tablefilter_source.py`, `make_probepipe_source.py`,
   `make_combined_source.py`). Its derived text must hash to the rank-probe
   protocol's frozen `online_source_sha256` (`RANKPROBE_SHA256` below). That
   is the rank-probe producer (arms cP / kP of run 39214027289, the current
   n = 83 baseline).
2. `onlineframe_edits`: counted, exact replacements in the wide module add
   `KIC_ONLINE_SOLVE`, read only by the one-target online scan:

   * `s3` (default, also when unset): the rank-probe producer's online scan,
     `scan_state128_filtered::<CANON_LIFT, PIPE_COMPACT>` (the batched S3
     solve per candidate), unchanged.
   * `frame`: the online scan runs the rank stage's loop,
     `scan_state128_frame::<CANON_LIFT, PIPE_FRAME>`, the same function and
     const parameters the rank stage runs under `KIC_RANK_SOLVE=frame`. Both
     scans are `extract128::<CANON_LIFT, ORDER_FEISTEL, P>` on one target
     point T: the same states in the same Feistel order keyed by the
     target's public hash, the same first hit. Only the probe loop differs.
     The frame loop's exactness against the S3 loop (relation, probes, root
     calls, relation checks) is the rank-probe experiment's (its tests
     compare `PIPE_FRAME` with `PIPE_COMPACT` on planted targets; its four
     Tier 1 rank blocks reproduce the S3 loop's relations and probes).
   * `frame_s3plant` (planted positive control): `frame`, plus the S3 loop
     redone on every state the scan reaches: the batched S3 solve of every
     candidate, its keys and its probe loop on a private probe counter. Per
     state the two must give the same relation (or none), the same probe
     counter, the same root calls and relation checks, and per candidate
     the same pair of keys (canonical, normal-basis partner, shift,
     candidate) up to the pair order the frame loop resolves at a hit; a
     panic on any difference. The S3 result is then discarded.

   Every target record gains `online_solve` and `online_counters` (this
   target's deltas of the frame loop's counters: frames built, fallback
   states, exceptional inputs, resolved hits, swapped pairs, and the planted
   control's checked candidates, states and swapped pairs). The summary's
   `rank_padd_*` / `rank_frame_*` counters are read before the online scan,
   so they stay the rank stage's own. Every other path (setup, index, rank
   stage, `s3` online scan) is the rank-probe producer's, byte for byte.

`--check` regenerates and requires byte identity with the existing output.
"""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_rankprobe_source as rankprobe  # noqa: E402  (koblitz-n83-rankprobe-20261019, verbatim)

EXAMPLES = HERE / "snapshots" / "r770" / "examples"
OUTPUT = EXAMPLES / "koblitz_orbit_dlp_fast_online_onlineframe.rs"
# protocol.json "sources.online_source_sha256" of koblitz-n83-rankprobe-20261019 (PR #980).
RANKPROBE_SHA256 = "d4394df35d065afbfb05022eac3006492239cc64b94de16fba501322cb578bb5"
WIDE_START = rankprobe.WIDE_START
WIDE_END = rankprobe.WIDE_END
replace = rankprobe.replace

HEAD_OLD = """// rank-cut loop in the target's Frobenius frame, exact to the rank-cut loop.
"""
HEAD_NEW = HEAD_OLD + """// koblitz-n83-onlineframe-20261019: derived from the rank-probe producer by
// make_online_source.py; adds KIC_ONLINE_SOLVE=s3 | frame | frame_s3plant,
// the rank stage's frame loop in the one-target online scan, exact to the
// S3 loop.
"""

ONLINEFRAME_CODE = r'''
    // koblitz-n83-onlineframe-20261019: the one-target online scan's probe
    // loop (KIC_ONLINE_SOLVE) and its planted control.
    const PIPE_FRAME_S3PLANT: u8 = 11;

    static S3PLANT_CANDIDATES: AtomicU64 = AtomicU64::new(0);
    static S3PLANT_STATES: AtomicU64 = AtomicU64::new(0);
    static S3PLANT_SWAPPED: AtomicU64 = AtomicU64::new(0);

    /// `KIC_ONLINE_SOLVE`: the online target scan's partner-root solve.
    fn online_solve_from_env() -> (u8, &'static str) {
        match std::env::var("KIC_ONLINE_SOLVE").as_deref() {
            Err(_) | Ok("") | Ok("s3") => (PIPE_COMPACT, "s3"),
            Ok("frame") => (PIPE_FRAME, "frame"),
            Ok("frame_s3plant") => (PIPE_FRAME_S3PLANT, "frame_s3plant"),
            Ok(other) => panic!("unknown KIC_ONLINE_SOLVE {other}"),
        }
    }

    const ONLINE_COUNTER_NAMES: [&str; 8] = [
        "frame_builds",
        "fallback_states",
        "irregular_inputs",
        "resolved_hits",
        "swapped_pairs",
        "s3plant_checked_candidates",
        "s3plant_checked_states",
        "s3plant_swapped_pairs",
    ];

    fn online_counter_values() -> [u64; 8] {
        [
            FRAME_BUILDS.load(Ordering::Relaxed),
            PADD_FALLBACK_STATES.load(Ordering::Relaxed),
            PADD_IRREGULAR_INPUTS.load(Ordering::Relaxed),
            PADD_RESOLVED_HITS.load(Ordering::Relaxed),
            PADD_SWAPPED_PAIRS.load(Ordering::Relaxed),
            S3PLANT_CANDIDATES.load(Ordering::Relaxed),
            S3PLANT_STATES.load(Ordering::Relaxed),
            S3PLANT_SWAPPED.load(Ordering::Relaxed),
        ]
    }

    fn online_counter_delta(start: &[u64; 8]) -> Value {
        let now = online_counter_values();
        let mut record = serde_json::Map::new();
        for (i, name) in ONLINE_COUNTER_NAMES.iter().enumerate() {
            record.insert((*name).to_string(), json!(now[i] - start[i]));
        }
        Value::Object(record)
    }

    /// [`scan_state128_frame`] (`PIPE_FRAME`) with the S3 loop
    /// ([`scan_state128_filtered`], `PIPE_COMPACT`) redone on the same state
    /// first, on a private probe counter and split, and compared: the same
    /// relation or none, the same probe counter, root calls and relation
    /// checks, and per candidate the same two keys up to pair order. The S3
    /// result is discarded; the frame loop's is returned.
    #[inline(never)]
    #[allow(clippy::too_many_arguments)]
    fn scan_state128_frame_s3plant<const C: u8>(
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
        let mut s3_probes = *probes;
        let mut s3_split = ExtractSplit::default();
        let s3 = scan_state128_filtered::<C, PIPE_COMPACT>(
            gf, fast, basis, solver, index, base, target, target_x, state, scan, &mut s3_probes,
            clock, &mut s3_split,
        );
        scan.frame.check.clear();
        scan.frame.check.extend_from_slice(&scan.keys);
        let calls_before = split.root_calls;
        let checks_before = split.relation_checks;
        let fallback_before = PADD_FALLBACK_STATES.load(Ordering::Relaxed);
        let got = scan_state128_frame::<C, PIPE_FRAME>(
            gf, fast, basis, solver, index, base, target, target_x, state, scan, probes, clock,
            split,
        );
        let fallback = PADD_FALLBACK_STATES.load(Ordering::Relaxed) != fallback_before;
        let view = |r: &Option<Relation128>| {
            r.as_ref().map(|r| (r.point_indices, r.x_codes, r.intermediates, r.probes))
        };
        assert_eq!(view(&got), view(&s3), "frame relation differs from the S3 relation");
        assert_eq!(*probes, s3_probes, "frame probe counter differs from the S3 loop's");
        assert_eq!(split.root_calls - calls_before, s3_split.root_calls, "root calls differ");
        assert_eq!(split.relation_checks - checks_before, s3_split.relation_checks,
                   "relation checks differ");
        let want = &scan.frame.check;
        let keys = &scan.keys;
        assert_eq!(keys.len(), want.len(), "frame and S3 key counts differ");
        assert!(keys.len() % 2 == 0);
        let mut swapped = 0u64;
        for pair in 0..keys.len() / 2 {
            let at = 2 * pair;
            // The S3 loop's partners are in the polynomial basis; the frame
            // loop's in the normal basis (the fallback path emits the S3
            // loop's own keys).
            let s3_key = |k: &ProbeKey128| {
                let partner = if fallback { k.partner } else { basis.to_normal.apply(k.partner) };
                (k.canonical, partner, k.partner_shift, k.candidate)
            };
            let frame_key = |k: &ProbeKey128| (k.canonical, k.partner, k.partner_shift, k.candidate);
            let s3_pair = [s3_key(&want[at]), s3_key(&want[at + 1])];
            let frame_pair = [frame_key(&keys[at]), frame_key(&keys[at + 1])];
            assert_eq!(s3_pair[0].3, s3_pair[1].3, "an S3 pair spans two candidates");
            if frame_pair == s3_pair {
                continue;
            }
            assert_eq!([frame_pair[1], frame_pair[0]], s3_pair,
                       "frame keys differ from the S3 keys");
            swapped += 1;
        }
        // The redone S3 work stays inside the online interval: its laps are
        // charged to this target's PDP and relation-check phases.
        split.pdp += s3_split.pdp;
        split.relation_check += s3_split.relation_check;
        S3PLANT_CANDIDATES.fetch_add((keys.len() / 2) as u64, Ordering::Relaxed);
        S3PLANT_STATES.fetch_add(1, Ordering::Relaxed);
        S3PLANT_SWAPPED.fetch_add(swapped, Ordering::Relaxed);
        got
    }

    #[cfg(test)]
    mod onlineframe_tests {
        use super::*;

        /// On planted four-point targets, the online selector's three loops
        /// give the S3 loop's relation, probes, root calls and relation
        /// checks through `extract128`, the online scan's entry point, and
        /// the planted control compares keys on every state it reaches.
        #[test]
        fn online_frame_loops_find_the_s3_relation_with_the_s3_probes() {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let b = gf.from_element(&curve.curve.b);
            let r = curve.subgroup_order.to_u64().unwrap();
            let (points, labels, reps, _) = construct_base128(&fast, &curve, b, 9, r);
            let mut by_x: HashMap<u128, Vec<usize>> = HashMap::new();
            for (i, point) in points.iter().enumerate() {
                by_x.entry(point.unwrap().0).or_default().push(i);
            }
            let reps: Vec<u128> = reps.iter().map(|p| p.unwrap()[0]).collect();
            let base = Base128 { points, labels, by_x, columns: 9 };
            let basis = NormalBasis128::new(&gf);
            let solver = S3Solver128::new(&gf, b);
            const FOLDED: IndexMode128 = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_SELECTED };
            let index = build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28, FOLDED);
            let mut seed = 0x5DEE_CE66_D1CE_4E5Bu64;
            let mut solved = 0usize;
            let states_before = S3PLANT_STATES.load(Ordering::Relaxed);
            let candidates_before = S3PLANT_CANDIDATES.load(Ordering::Relaxed);
            for trial in 0..60u64 {
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
                assert!(want.0.is_some(), "a planted four-point target decomposes");
                assert_eq!(run!(PIPE_FRAME), want, "the online frame loop differs from S3");
                assert_eq!(run!(PIPE_FRAME_S3PLANT), want, "the planted loop differs from S3");
                solved += 1;
            }
            assert!(solved >= 40);
            assert!(S3PLANT_STATES.load(Ordering::Relaxed) > states_before);
            assert!(S3PLANT_CANDIDATES.load(Ordering::Relaxed) > candidates_before);
        }

        #[test]
        fn online_solve_selector_defaults_to_s3() {
            // The selector is read from the environment; without it the
            // online scan is the rank-probe producer's S3 loop.
            if std::env::var("KIC_ONLINE_SOLVE").is_err() {
                assert_eq!(online_solve_from_env(), (PIPE_COMPACT, "s3"));
            }
        }
    }

'''

SELECT_DOC_OLD = """    /// `P` picks the target scan's probe loop at compile time.
"""
SELECT_DOC_NEW = ONLINEFRAME_CODE + SELECT_DOC_OLD

SELECT_OLD = """        if P >= PIPE_FRAME {
            return scan_state128_frame::<C, P>(
"""
SELECT_NEW = """        if P == PIPE_FRAME_S3PLANT {
            return scan_state128_frame_s3plant::<C>(
                gf, fast, basis, solver, index, base, target, target_x, state, scan, probes, clock,
                split,
            );
        }
""" + SELECT_OLD

ONLINE_SELECT_OLD = """            _ => PIPE_OFF,
        };
        for (fixture_index, &target_input) in target_inputs.iter().enumerate() {
"""
ONLINE_SELECT_NEW = """            _ => PIPE_OFF,
        };
        // koblitz-n83-onlineframe-20261019: the online scan's partner-root
        // solve; the rank stage's counters are read here, before it.
        let (online_solve, online_solve_name) = online_solve_from_env();
        assert!(
            online_solve == PIPE_COMPACT || table_loop == PIPE_COMPACT,
            "KIC_ONLINE_SOLVE=frame runs with KIC_ROOT_TABLE=compact"
        );
        let rank_counters = [
            PADD_FALLBACK_STATES.load(Ordering::Relaxed),
            PADD_IRREGULAR_INPUTS.load(Ordering::Relaxed),
            PADD_RESOLVED_HITS.load(Ordering::Relaxed),
            PADD_SWAPPED_PAIRS.load(Ordering::Relaxed),
            PADD_PLANT_CHECKED.load(Ordering::Relaxed),
            FRAME_BUILDS.load(Ordering::Relaxed),
            FRAME_PLANT_CHECKED.load(Ordering::Relaxed),
        ];
        for (fixture_index, &target_input) in target_inputs.iter().enumerate() {
"""

ONLINE_COUNTERS_OLD = """            let online_counters = HwCounters::open();
            online_counters.start();
"""
ONLINE_COUNTERS_NEW = """            let online_counter_start = online_counter_values();
""" + ONLINE_COUNTERS_OLD

TABLE_MATCH_OLD = """                match table_loop {
                    PIPE_COMPACT => table_extract!(PIPE_COMPACT),
"""
TABLE_MATCH_NEW = """                match table_loop {
                    PIPE_COMPACT if online_solve == PIPE_FRAME => table_extract!(PIPE_FRAME),
                    PIPE_COMPACT if online_solve == PIPE_FRAME_S3PLANT => table_extract!(PIPE_FRAME_S3PLANT),
                    PIPE_COMPACT => table_extract!(PIPE_COMPACT),
"""

RECORD_OLD = """                "root_table":root_table_name,
                "filter_passes":split.filter_passes,
"""
RECORD_NEW = RECORD_OLD + """                "online_solve":online_solve_name,
                "online_counters":online_counter_delta(&online_counter_start),
"""

SUMMARY_OLD = """            "rank_solve":rank_solve_name,
            "rank_padd_fallback_states":PADD_FALLBACK_STATES.load(Ordering::Relaxed),
            "rank_padd_irregular_inputs":PADD_IRREGULAR_INPUTS.load(Ordering::Relaxed),
            "rank_padd_resolved_hits":PADD_RESOLVED_HITS.load(Ordering::Relaxed),
            "rank_padd_swapped_pairs":PADD_SWAPPED_PAIRS.load(Ordering::Relaxed),
            "rank_padd_plant_checked_inputs":PADD_PLANT_CHECKED.load(Ordering::Relaxed),
            "rank_frame_builds":FRAME_BUILDS.load(Ordering::Relaxed),
            "rank_frame_plant_checked_inputs":FRAME_PLANT_CHECKED.load(Ordering::Relaxed),
"""
SUMMARY_NEW = """            "rank_solve":rank_solve_name,
            "rank_padd_fallback_states":rank_counters[0],
            "rank_padd_irregular_inputs":rank_counters[1],
            "rank_padd_resolved_hits":rank_counters[2],
            "rank_padd_swapped_pairs":rank_counters[3],
            "rank_padd_plant_checked_inputs":rank_counters[4],
            "rank_frame_builds":rank_counters[5],
            "rank_frame_plant_checked_inputs":rank_counters[6],
            "online_solve":online_solve_name,
"""


def onlineframe_edits(head, wide):
    head = replace(head, HEAD_OLD, HEAD_NEW)
    wide = replace(wide, SELECT_DOC_OLD, SELECT_DOC_NEW)
    wide = replace(wide, SELECT_OLD, SELECT_NEW)
    wide = replace(wide, ONLINE_SELECT_OLD, ONLINE_SELECT_NEW)
    wide = replace(wide, ONLINE_COUNTERS_OLD, ONLINE_COUNTERS_NEW)
    wide = replace(wide, TABLE_MATCH_OLD, TABLE_MATCH_NEW)
    wide = replace(wide, RECORD_OLD, RECORD_NEW)
    wide = replace(wide, SUMMARY_OLD, SUMMARY_NEW)
    return head, wide


def rankprobe_text():
    text = rankprobe.derive(rankprobe.rankcut_text())
    digest = hashlib.sha256(text.encode()).hexdigest()
    if digest != RANKPROBE_SHA256:
        raise ValueError("rank-probe derivation differs from koblitz-n83-rankprobe-20261019's frozen producer: "
                         + digest)
    return text


def derive(text):
    head, rest = text.split(WIDE_START, 1)
    wide, tail = rest.split(WIDE_END, 1)
    head, wide = onlineframe_edits(head, wide)
    return head + WIDE_START + wide + WIDE_END + tail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = derive(rankprobe_text())
    if args.check:
        if OUTPUT.read_text() != text:
            raise SystemExit("derived online source differs from " + str(OUTPUT))
    else:
        OUTPUT.write_text(text)
    print("online_source_sha256=" + hashlib.sha256(text.encode()).hexdigest())


if __name__ == "__main__":
    sys.exit(main())
