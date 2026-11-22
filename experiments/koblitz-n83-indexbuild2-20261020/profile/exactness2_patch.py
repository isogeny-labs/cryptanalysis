"""Scratch-only: patch a COPY of the round-2 producer with a whole-base exactness check (diagnostic).

With `KIC_INDEX_EXACT2=1` the patched copy loads its base exactly as the
producer does, then (instead of the online flow):

* builds the stored states with the producer's `folded_states128` (C9) and
  with the parent's state loop (the parent's text, verbatim, from
  `make_indexbuild_source.STATES_NEW`), and compares every state;
* canonicalizes every stored root with the producer's eight-lane linear run
  finder (C7) and with `lift_scan_wide`, and counts the roots whose key or
  shift differ;
* builds the compact table with the producer's insert loop (via
  `build_index128_stacked`) and with the parent's insert loop (verbatim,
  `make_indexbuild_source.INSERT_NEW`), and compares every slot word;
* prints one JSON line.

The patched copy is never committed as a producer.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import make_indexbuild_source as round1  # noqa: E402


src = Path(sys.argv[1]).read_text()
out = Path(sys.argv[2])
ANCHOR = "    // ── koblitz-n83-stacked-20261016: the folded root index on every layout ──\n"
assert src.count(ANCHOR) == 1
PATCH = r'''
    fn exact2_parent_states(gf: &Gf2_128, basis: &NormalBasis128, solver: &S3Solver128, shifted: &[Vec<u128>],
                            fold: &Fold128) -> Vec<State128> {
''' + round1.STATES_NEW + r'''        states
    }

    fn exact2_parent_compact(basis: &NormalBasis128, states: &[State128], canon: u8) -> CompactRootTable128 {
        let mode = IndexMode128 { fold: true, plant: false, canon };
''' + round1.INSERT_NEW + r'''        slots
    }

    fn exact2_index128(gf: &Gf2_128, basis: &NormalBasis128, solver: &S3Solver128, reps: &[u128]) {
        let n = gf.n as usize;
        let mode = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_LIFT };
        let t = Instant::now();
        let index = build_index128_stacked(gf, basis, solver, reps, TABLE_COMPACT, 28, mode);
        let build_ms = ms(t.elapsed());
        let fold = Fold128::new(reps.len(), n, false);
        let parent_states = exact2_parent_states(gf, basis, solver, &index.shifted, &fold);
        let states_equal = parent_states.len() == index.states.len() && parent_states.iter().zip(&index.states).all(|(x, y)|
            (x.left, x.right, x.relative, x.normal_roots) == (y.left, y.right, y.relative, y.normal_roots));
        let irregular = index.states.iter().filter(|s| {
            let l = index.shifted[s.left as usize][0];
            let r = index.shifted[s.right as usize][s.relative as usize];
            l == 0 || r == 0 || l == r }).count();
        let roots: Vec<u128> = index.states.iter().flat_map(|s| s.normal_roots).collect();
        let mut key_mismatches = 0u64;
        let mut shift_mismatches = 0u64;
        let mut nonzero_shift = 0u64;
        let mut tie_roots = 0u64;
        let chunks = roots.len() / INDEX_BUILD_LANES;
        for c in 0..chunks {
            let words: [u128; INDEX_BUILD_LANES] = roots[c * INDEX_BUILD_LANES..(c + 1) * INDEX_BUILD_LANES].try_into().unwrap();
            let got = lift_linear_lanes8::<83>(&words);
            for (lane, &v) in words.iter().enumerate() {
                let want = super::lift2::lift_scan_wide(v, 83);
                key_mismatches += (got[lane].0 != want.0) as u64;
                shift_mismatches += (got[lane].1 != want.1) as u64;
                nonzero_shift += (want.1 != 0) as u64;
                let (tops, _) = super::lift2::F83::longest_runs(super::lift2::F83::from_u128(v));
                tie_roots += ((tops[0].count_ones() + tops[1].count_ones()) > 1) as u64;
            }
        }
        for &v in &roots[chunks * INDEX_BUILD_LANES..] {
            let got = lift_linear::<83>(v);
            let want = super::lift2::lift_scan_wide(v, 83);
            key_mismatches += (got.0 != want.0) as u64;
            shift_mismatches += (got.1 != want.1) as u64;
        }
        let reference = exact2_parent_compact(basis, &parent_states, INDEX_CANON_LIFT);
        let compact = index.compact.as_ref().unwrap();
        let slots_equal = compact.slots == reference.slots && compact.len == reference.len;
        println!("{}", json!({"stored_states": index.states.len(), "roots_checked": roots.len(),
            "irregular_states_fallback": irregular, "states_equal_parent": states_equal,
            "linear_vs_lift_scan_key_mismatches": key_mismatches, "linear_vs_lift_scan_shift_mismatches": shift_mismatches,
            "roots_with_nonzero_shift": nonzero_shift, "roots_with_tied_longest_runs": tie_roots,
            "table_slots": compact.slots.len(), "table_entries": compact.len, "slots_equal_parent": slots_equal,
            "producer_index_build_ms": build_ms}));
    }

'''
src = src.replace(ANCHOR, PATCH + ANCHOR)
CALL = "        let index_started = Instant::now();\n        let (index_mode, index_canon_name) = index_mode_from_env();\n"
assert src.count(CALL) == 1
src = src.replace(CALL, "        if std::env::var(\"KIC_INDEX_EXACT2\").is_ok() { exact2_index128(&gf, &basis, &solver, &reps); std::process::exit(0); }\n" + CALL)
out.write_text(src)
