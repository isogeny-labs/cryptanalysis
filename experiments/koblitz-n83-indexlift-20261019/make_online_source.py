#!/usr/bin/env python3
"""Derive the index-lift n=83 K600 producer from the rank-probe producer, exactly.

Input: `snapshots/r770/examples/koblitz_orbit_dlp_fast_online_logcache.rs`
(crypto 770f6a69 plus B's `ic_log_cache.patch`, restored and digest-checked
by `restore.py`).

1. `make_rankprobe_source.py` is `koblitz-n83-rankprobe-20261019`'s
   `make_online_source.py` (PR #980), verbatim, with its verbatim parents
   (`make_rankcut_source.py`, `make_stacked_source.py`,
   `make_tablefilter_source.py`, `make_probepipe_source.py`,
   `make_combined_source.py`). Its derived text must hash to the rank-probe
   protocol's frozen `online_source_sha256` (`RANKPROBE_SHA256` below,
   d4394df3...). That is the rank-probe producer (arms cP / kP of run
   39214027289, the current n = 83 baseline).
2. `indexlift_edits`: counted, exact replacements in the wide module. None
   of them touches a timed path of the baseline (`KIC_INDEX_CANON=selected`,
   `KIC_SCAN_SELFTEST` unset):

   * `KIC_INDEX_CANON=lift_plant` (planted positive control): the index
     build keys every root with lift_scan, as `lift` does, and also
     computes the baseline's canonical key and shift (`canonical_selected`)
     for the same root, panics on any difference, and counts the check
     (`index_plant_checked_inputs`). So it costs `lift` plus the work that
     `lift` removes, and it checks every index canonicalization of the
     process. `selected` and `lift` are unchanged (the rank-probe producer
     already has both).
   * `KIC_SCAN_SELFTEST` = `full` (default, unchanged: the exhaustive
     bijection sweep of the Feistel scan order over its whole 2^26 domain
     for two fixed keys, about 1.9 s of every cold process) or `sampled`
     (secondary arm only): the sweep is skipped and the folded index's
     sampled inverse check (`scan_inverse_selftest`, 65,536 positions per
     key, already part of `full`) is kept. The scan itself, its key and its
     visit order are unchanged; the bijection is a property of the Feistel
     construction and is checked exhaustively on the real state count by
     the crate tests the workflow runs on this source. The summary records
     the mode.
   * `KIC_INDEX_DIGEST=1` (after the target, outside every timed interval)
     adds two layout digests to the existing ones: `stored_states_blake3`
     (every stored state's bytes, in stored order) and `table_slots_blake3`
     (every slot word of the root table, empty slots included, in slot
     order). Equal values mean the same stored states and the same table
     layout, byte for byte, not only the same logical states and map.
   * one test module: every canonicalizer mode builds the same stored
     states and the same slot array on a 9-orbit base, and `lift_plant`
     checks every insert.

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
OUTPUT = EXAMPLES / "koblitz_orbit_dlp_fast_online_indexlift.rs"
# protocol.json "sources.online_source_sha256" of koblitz-n83-rankprobe-20261019 (PR #980).
RANKPROBE_SHA256 = "d4394df35d065afbfb05022eac3006492239cc64b94de16fba501322cb578bb5"
WIDE_START = rankprobe.WIDE_START
WIDE_END = rankprobe.WIDE_END
replace = rankprobe.replace

HEAD_OLD = """// rank-cut loop in the target's Frobenius frame, exact to the rank-cut loop.
"""
HEAD_NEW = HEAD_OLD + """// koblitz-n83-indexlift-20261019: derived from the rank-probe producer by
// make_online_source.py; adds KIC_INDEX_CANON=lift_plant (planted control),
// KIC_SCAN_SELFTEST=full | sampled and two layout digests (KIC_INDEX_DIGEST).
"""

CONST_OLD = """    const INDEX_CANON_LIFT: u8 = 1;
    static FOLD_AUDIT_PROBES: AtomicU64 = AtomicU64::new(0);
"""
CONST_NEW = """    const INDEX_CANON_LIFT: u8 = 1;
    // koblitz-n83-indexlift-20261019: lift_scan keys, each checked against
    // the selected canonicalizer (planted positive control).
    const INDEX_CANON_LIFT_PLANT: u8 = 2;
    static INDEX_PLANT_CHECKED: AtomicU64 = AtomicU64::new(0);
    static FOLD_AUDIT_PROBES: AtomicU64 = AtomicU64::new(0);
"""

ENV_OLD = """            Ok("lift") => (INDEX_CANON_LIFT, "lift"),
"""
ENV_NEW = ENV_OLD + """            Ok("lift_plant") => (INDEX_CANON_LIFT_PLANT, "lift_plant"),
"""

CANON_OLD = """        if canon == INDEX_CANON_LIFT {
            super::lift2::lift_scan_wide(v, basis.n)
        } else {
            basis.canonical_selected(v)
        }
"""
CANON_NEW = """        if canon == INDEX_CANON_LIFT {
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
"""

SELFTEST_OLD = """        let scan_selftest_started = Instant::now();
        let scan_selftest_keys = [0x0123_4567_89AB_CDEFu64, 0xFEDC_BA98_7654_3210u64];
        let scan_selftest_ok = scan_selftest_keys
            .iter()
            .all(|&key| {
                scan_permutation_selftest(index.logical_states, key)
                    && (index.fold.is_none() || scan_inverse_selftest(index.logical_states, key))
            });
"""
SELFTEST_NEW = """        // koblitz-n83-indexlift-20261019: KIC_SCAN_SELFTEST=full (default,
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
"""

DIGEST_OLD = """        let index_digest = (std::env::var("KIC_INDEX_DIGEST").as_deref() == Ok("1"))
            .then(|| index_digest128(&index, &basis));
"""
DIGEST_NEW = """        // koblitz-n83-indexlift-20261019: plus the stored layout, byte for byte.
        let index_digest = (std::env::var("KIC_INDEX_DIGEST").as_deref() == Ok("1")).then(|| {
            let mut digest = index_digest128(&index, &basis);
            let (stored_states_blake3, table_slots_blake3) = index_layout_digest128(&index);
            digest["stored_states_blake3"] = json!(stored_states_blake3);
            digest["table_slots_blake3"] = json!(table_slots_blake3);
            digest
        });
"""

DIGEST_FN_OLD = """    #[cfg(test)]
    mod stacked_tests {
"""
DIGEST_FN_NEW = r'''    /// koblitz-n83-indexlift-20261019: every stored state in stored order,
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
    mod stacked_tests {
'''

SUMMARY_OLD = """            "index_canonicalizer":index_canon_name,
"""
SUMMARY_NEW = SUMMARY_OLD + """            "index_plant_checked_inputs":INDEX_PLANT_CHECKED.load(Ordering::Relaxed),
"""

SELFTEST_SUMMARY_OLD = """                                   "bijection":scan_selftest_ok, "ms":scan_selftest_ms,
"""
SELFTEST_SUMMARY_NEW = """                                   "bijection":scan_selftest_ok, "ms":scan_selftest_ms,
                                   "mode":scan_selftest_mode,
"""


def indexlift_edits(head, wide):
    head = replace(head, HEAD_OLD, HEAD_NEW)
    wide = replace(wide, CONST_OLD, CONST_NEW)
    wide = replace(wide, ENV_OLD, ENV_NEW)
    wide = replace(wide, CANON_OLD, CANON_NEW)
    wide = replace(wide, SELFTEST_OLD, SELFTEST_NEW)
    wide = replace(wide, DIGEST_OLD, DIGEST_NEW)
    wide = replace(wide, DIGEST_FN_OLD, DIGEST_FN_NEW)
    wide = replace(wide, SUMMARY_OLD, SUMMARY_NEW)
    wide = replace(wide, SELFTEST_SUMMARY_OLD, SELFTEST_SUMMARY_NEW)
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
    head, wide = indexlift_edits(head, wide)
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
