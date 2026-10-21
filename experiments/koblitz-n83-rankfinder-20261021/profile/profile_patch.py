#!/usr/bin/env python3
"""Instrument a SCRATCH copy of a producer's rank-stage frame loop (never committed as a producer).

Usage: profile_patch.py <producer.rs> <out.rs>

Adds, inside `scan_state128_frame` (the rank stage's probe loop):

* per-state timers: frame setup (frame_root_xy, frame build, the batched
  inverse) and key derivation (partner words, canonicalization, prefetch),
  summed over the rank stage; the probe loop and relation checks are the
  rest of the rank stage;
* with `KIC_RANKPROF=canon`, after each state's keys are complete, the
  canonicalization ALONE on that state's real partner words, timed twice
  and discarded through black_box: lift_scan per word (the parent's call)
  and the linear run finder eight words at a time (round 2's function).

The sums are printed to stderr as one `rankprof=` JSON line before the
summary. With KIC_RANKPROF unset only the two timers run.
"""

import sys
from pathlib import Path


def replace(text, old, new):
    if text.count(old) != 1:
        raise SystemExit("anchor found %d times: %r" % (text.count(old), old[:60]))
    return text.replace(old, new)


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    text = src.read_text()
    text = replace(text, "\n    #[inline(always)]\n    fn frame_root_xy(", """
    static PROF_SETUP_NS: AtomicU64 = AtomicU64::new(0);
    static PROF_KEYS_NS: AtomicU64 = AtomicU64::new(0);
    static PROF_LIFT_NS: AtomicU64 = AtomicU64::new(0);
    static PROF_LINEAR_NS: AtomicU64 = AtomicU64::new(0);
    static PROF_KEYS: AtomicU64 = AtomicU64::new(0);
    static PROF_STATES: AtomicU64 = AtomicU64::new(0);
    fn prof_canon() -> bool {
        static MODE: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
        *MODE.get_or_init(|| std::env::var("KIC_RANKPROF").as_deref() == Ok("canon"))
    }

    #[inline(always)]
    fn frame_root_xy(""")
    text = replace(text, """        assert_eq!(state.normal_roots.len(), FRAME_ROOTS);
        let mut xk = [0u128; FRAME_ROOTS];""", """        assert_eq!(state.normal_roots.len(), FRAME_ROOTS);
        let prof_t0 = std::time::Instant::now();
        let mut xk = [0u128; FRAME_ROOTS];""")
    text = replace(text, "\n        scan.keys.clear();\n        fr.pair_start.clear();\n",
                   "\n        let prof_t1 = std::time::Instant::now();\n        scan.keys.clear();\n        fr.pair_start.clear();\n")
    text = replace(text, "\n        if P == PIPE_FRAME_PLANT {\n            // The removed work", """
        let prof_t2 = std::time::Instant::now();
        PROF_SETUP_NS.fetch_add((prof_t1 - prof_t0).as_nanos() as u64, Ordering::Relaxed);
        PROF_KEYS_NS.fetch_add((prof_t2 - prof_t1).as_nanos() as u64, Ordering::Relaxed);
        PROF_KEYS.fetch_add(scan.keys.len() as u64, Ordering::Relaxed);
        PROF_STATES.fetch_add(1, Ordering::Relaxed);
        if prof_canon() {
            let t = std::time::Instant::now();
            for key in scan.keys.iter() {
                black_box(super::lift2::lift_scan_wide(black_box(key.partner), 83));
            }
            let t_lift = t.elapsed();
            let t = std::time::Instant::now();
            for chunk in scan.keys.chunks(8) {
                let words: [u128; 8] = std::array::from_fn(|lane| black_box(chunk.get(lane).map_or(0, |k| k.partner)));
                black_box(lift_linear_lanes8::<83>(&words));
            }
            let t_linear = t.elapsed();
            PROF_LIFT_NS.fetch_add(t_lift.as_nanos() as u64, Ordering::Relaxed);
            PROF_LINEAR_NS.fetch_add(t_linear.as_nanos() as u64, Ordering::Relaxed);
        }
        if P == PIPE_FRAME_PLANT {
            // The removed work""")
    text = replace(text, "\n        let index_digest = (std::env::var(\"KIC_INDEX_DIGEST\")", """
        eprintln!("rankprof={}", json!({
            "states": PROF_STATES.load(Ordering::Relaxed),
            "keys": PROF_KEYS.load(Ordering::Relaxed),
            "setup_ns": PROF_SETUP_NS.load(Ordering::Relaxed),
            "keys_ns": PROF_KEYS_NS.load(Ordering::Relaxed),
            "lift_alone_ns": PROF_LIFT_NS.load(Ordering::Relaxed),
            "linear_alone_ns": PROF_LINEAR_NS.load(Ordering::Relaxed),
        }));
        let index_digest = (std::env::var("KIC_INDEX_DIGEST")""")
    out.write_text(text)


if __name__ == "__main__":
    main()
