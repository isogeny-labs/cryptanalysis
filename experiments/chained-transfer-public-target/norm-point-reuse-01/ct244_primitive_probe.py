#!/usr/bin/env python3
"""CT244: exact-source additive primitive clocks for the CT125 norm reuse derivative.

Only emits measurements on a separately generated sibling when
CT244_PRIMITIVE_TRACE=1. Real native execution and all cost claims remain gated.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import build_norm_reuse as ct125

LABELS = [
    "C13_0_to_1", "C13_1_to_0",
    "C13_1_to_2", "C13_2_to_1",
    "C169_0_to_2", "C169_2_to_0",
    "D_target_norm",
]
TESTS_BLOB = "bcd27773a7b179c3beeb3d5782a5de97a7df19f2"

CLOCK = """#[derive(Clone, Copy, Default)]
struct Ct244Clock {
    counts: [u64; 7],
    nanoseconds: [u128; 7],
}
"""
RUNTIME_OLD = "    calls: Cell<Calls>,\n"
RUNTIME_NEW = RUNTIME_OLD + """    ct244_enabled: bool,
    ct244_clock: Cell<Ct244Clock>,
    ct244_epoch: Cell<Ct244Clock>,
    ct248_seq: Cell<u64>,
"""
INIT_OLD = "            calls: Cell::new(Calls::default()),\n"
INIT_NEW = INIT_OLD + """            ct244_enabled: std::env::var("CT244_PRIMITIVE_TRACE").ok().as_deref() == Some("1"),
            ct244_clock: Cell::new(Ct244Clock::default()),
            ct244_epoch: Cell::new(Ct244Clock::default()),
            ct248_seq: Cell::new(0),
"""
MAP_OLD = """        let q = self.maps[from][to]
            .as_ref()
            .unwrap()
            .eval(&self.geometry.models[from].quadratic.f, p);
"""
MAP_NEW = """        let ct244_started = self.ct244_enabled.then(std::time::Instant::now);
        let q = self.maps[from][to]
            .as_ref()
            .unwrap()
            .eval(&self.geometry.models[from].quadratic.f, p);
        if let Some(started) = ct244_started {
            self.ct244_record(Self::ct244_slot(from, to), started.elapsed().as_nanos());
        }
"""
DOUBLING_OLD = "        let doubled = curve::padd(&target.f, &target.curve, &z, &z);\n"
DOUBLING_NEW = """        let ct244_started = self.ct244_enabled.then(std::time::Instant::now);
        let doubled = curve::padd(&target.f, &target.curve, &z, &z);
        if let Some(started) = ct244_started {
            self.ct244_record(6, started.elapsed().as_nanos());
        }
"""
METHODS = """    // Clock slots distinguish the actual directed maps, not a generic C13 proxy.
    fn ct244_slot(from: usize, to: usize) -> usize {
        match (from, to) {
            (0, 1) => 0, (1, 0) => 1, (1, 2) => 2, (2, 1) => 3,
            (0, 2) => 4, (2, 0) => 5,
            _ => unreachable!("CT244: unsupported map direction"),
        }
    }
    fn ct244_record(&self, slot: usize, elapsed_ns: u128) {
        let mut c = self.ct244_clock.get();
        c.counts[slot] = c.counts[slot].checked_add(1).expect("CT244 call overflow");
        c.nanoseconds[slot] = c.nanoseconds[slot]
            .checked_add(elapsed_ns).expect("CT244 time overflow");
        self.ct244_clock.set(c);
        let mut e = self.ct244_epoch.get();
        e.counts[slot] = e.counts[slot].checked_add(1).expect("CT248 epoch call overflow");
        e.nanoseconds[slot] = e.nanoseconds[slot]
            .checked_add(elapsed_ns).expect("CT248 epoch time overflow");
        self.ct244_epoch.set(e);
    }
    fn ct248_emit_sample(&self, source: Calls) {
        let e = self.ct244_epoch.get();
        let sum = |slots: &[usize]| -> u64 {
            slots.iter().fold(0_u64, |count, &slot| {
                count.checked_add(e.counts[slot]).expect("CT248 grouped call overflow")
            })
        };
        assert_eq!(sum(&[0, 1, 2, 3]), source.degree13_elliptic_evaluation,
                   "CT248 C13: epoch clock and original source counter diverged");
        assert_eq!(sum(&[4, 5]), source.degree169_elliptic_evaluation,
                   "CT248 C169: epoch clock and original source counter diverged");
        assert_eq!(e.counts[6], source.norm_point_doubling,
                   "CT248 D: epoch clock and original source counter diverged");
        let sequence = self.ct248_seq.get();
        self.ct248_seq.set(sequence.checked_add(1).expect("CT248 sample overflow"));
        eprintln!("CT248_PRIMITIVE_SAMPLE {}", json!({
            "schema": "ct248-scoped-primitives-v1",
            "sequence": sequence,
            "scope": "reset_calls_to_calls; eval_and_padd_only",
            "calls": e.counts,
            "elapsed_ns": e.nanoseconds,
            "source_C13": source.degree13_elliptic_evaluation,
            "source_C169": source.degree169_elliptic_evaluation,
            "source_D": source.norm_point_doubling,
            "measured_complete_solve": false,
            "pcc": "unverified"
        }));
    }
"""
DROP = """
// Independent timing namespace: original N4_FIXED_CHAIN_ event stream stays untouched.
// Cumulative over this Runtime's lifetime, including setup? Runtime setup is
// before the clock is constructed, so constructor work is expressly excluded.
impl Drop for Runtime {
    fn drop(&mut self) {
        if !self.ct244_enabled {
            return;
        }
        let c = self.ct244_clock.get();
        eprintln!("CT244_PRIMITIVE_TIMING {}", json!({
            "schema": "ct244-primitives-v1",
            "scope": "runtime_lifetime_after_constructor; eval-only; uncalibrated",
            "slots": [
                "C13_0_to_1", "C13_1_to_0", "C13_1_to_2", "C13_2_to_1",
                "C169_0_to_2", "C169_2_to_0", "D_target_norm"
            ],
            "calls": c.counts,
            "scoped_samples_emitted": self.ct248_seq.get(),
            "elapsed_ns": c.nanoseconds,
            "measured_complete_solve": false,
            "pcc": "unverified"
        }));
    }
}
"""

def replace_once(s, old, new, name):
    occurrences = s.count(old)
    if occurrences != 1:
        raise ValueError(f"CT244 {name}: expected one anchor; saw {occurrences}")
    return s.replace(old, new, 1)

RESET_OLD = """    pub fn reset_calls(&self) {
        self.calls.set(Calls::default());
    }
"""
RESET_NEW = """    pub fn reset_calls(&self) {
        self.calls.set(Calls::default());
        if self.ct244_enabled {
            self.ct244_epoch.set(Ct244Clock::default());
        }
    }
"""
CALLS_OLD = """    pub fn calls(&self) -> Calls {
        self.calls.get()
    }
"""
CALLS_NEW = """    pub fn calls(&self) -> Calls {
        let c = self.calls.get();
        if self.ct244_enabled {
            self.ct248_emit_sample(c);
        }
        c
    }
"""

def validate_selected_test_source(tests):
    if ct125.git_blob(tests) != TESTS_BLOB:
        raise ValueError("CT248 original selected-vector tests blob changed")
    if tests.count("runtime.reset_calls();") != 3 or tests.count("runtime.calls();") != 3:
        raise ValueError("CT248 expected exactly three selected per-arm reset/read pairs")
    if "assert_eq!(vectors.len(), 48);" not in tests:
        raise ValueError("CT248 original selected 48-vector assertion missing")
    return True

def instrument_derivative(src):
    # Guard all real calls; do not instrument the constructor's different
    # two-torsion evaluations, or replace the independent actual norm check.
    if "if ep(n.norm(&entry.class)?) != entry.norm {" not in src:
        raise ValueError("CT244 independent final actual norm check missing")
    if src.count("norm_from_target_point(to, ") != 2:
        raise ValueError("CT244 two reused route calls missing")
    if src.count("norm_point_doubling += 1") != 1:
        raise ValueError("CT244 original doubling counter missing")
    result = src
    for name, old, new in (
        ("clock struct", "#[derive(Clone)]\nstruct Correction {\n",
         CLOCK + "#[derive(Clone)]\nstruct Correction {\n"),
        ("runtime field", RUNTIME_OLD, RUNTIME_NEW),
        ("constructor", INIT_OLD, INIT_NEW),
        ("map evaluator", MAP_OLD, MAP_NEW),
        ("target norm doubling", DOUBLING_OLD, DOUBLING_NEW),
        ("selected reset epoch", RESET_OLD, RESET_NEW),
        ("selected clock readout", CALLS_OLD, CALLS_NEW),
        ("runtime clock methods",
         "    fn gamma(&self, from: usize, to: usize, p: Pt<ER>) -> Result<Pt<ER>> {\n",
         METHODS + "    fn gamma(&self, from: usize, to: usize, p: Pt<ER>) -> Result<Pt<ER>> {\n"),
    ):
        result = replace_once(result, old, new, name)
    if "impl Drop for Runtime {" in result or "CT244_PRIMITIVE_TIMING" in result:
        raise ValueError("CT244 existing clock or Drop implementation")
    result += DROP
    if result.count("ct244_record(") != 3 or len(LABELS) != 7:
        raise ValueError("CT244 unexpected number of map/doubling clock call sites")
    return result

def instrument(original):
    # CT125 transformer independently verifies the exact original Git blob.
    return instrument_derivative(ct125.transform(original))

def self_test(original, tests):
    validate_selected_test_source(tests)
    good = ct125.transform(original)
    out = instrument_derivative(good)
    assert "CT244_PRIMITIVE_TIMING" in out
    assert "if ep(n.norm(&entry.class)?) != entry.norm {" in out
    assert all(label in out for label in LABELS)
    assert "ct244_enabled: std::env::var" in out
    bad = [
        original.replace("pub type Result<T>", "pub type ResultMutated<T>", 1),
        good.replace(MAP_OLD, "", 1),
        good.replace(MAP_OLD, MAP_OLD + MAP_OLD, 1),
        good.replace(DOUBLING_OLD, "", 1),
        good.replace("if ep(n.norm(&entry.class)?) != entry.norm {",
                     "if false {", 1),
        good.replace("norm_point_doubling += 1", "norm_point_doubling += 2", 1),
        good.replace(RESET_OLD, "", 1),
        good.replace(RESET_OLD, RESET_OLD + RESET_OLD, 1),
        good.replace(CALLS_OLD, "", 1),
        good.replace(CALLS_OLD, CALLS_OLD + CALLS_OLD, 1),
    ]
    for i, src in enumerate(bad):
        try:
            if i == 0:
                instrument(src)
            else:
                instrument_derivative(src)
        except ValueError:
            continue
        raise AssertionError(f"CT244 mutation {i} was accepted")
    mutated_tests = tests.replace("runtime.reset_calls();", "", 1)
    try:
        validate_selected_test_source(mutated_tests)
    except ValueError:
        pass
    else:
        raise AssertionError("CT248 mutated selected-vector tests were accepted")
    assert "CT248_PRIMITIVE_SAMPLE" in out
    assert "CT248 C13: epoch clock" in out
    assert "CT248 C169: epoch clock" in out
    assert "CT248 D: epoch clock" in out
    print("CT248_SOURCE_SELFTEST_PASS 11 guarded mutations; scoped runtime timing still unavailable")

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    original = args.original.resolve()
    if original.name != "fixed-jacobian-chain-evaluator-01":
        ap.error("CT244 original must be exact evaluator directory")
    old = (original / "src/lib.rs").read_text("utf-8")
    tests = (original / "src/tests.rs").read_text("utf-8")
    validate_selected_test_source(tests)
    if args.self_test:
        self_test(old, tests)
        if args.out is None:
            return
    if args.out is None:
        ap.error("provide --out or --self-test")
    out = args.out.resolve()
    if out.name != "fixed-jacobian-chain-priced-01" or out.parent != original.parent:
        ap.error("CT244 out must be fresh declared sibling")
    if out.exists():
        ap.error("CT244 refuses to overwrite priced sibling")
    new = instrument(old)
    shutil.copytree(original, out, symlinks=True,
                    ignore=shutil.ignore_patterns("target", "*.tmp", "__pycache__"))
    (out / "src/lib.rs").write_text(new, "utf-8")
    receipt = {
        "source_blob": ct125.git_blob(old),
        "ct125_derivative_blob": ct125.git_blob(ct125.transform(old)),
        "ct244_derivative_blob": ct125.git_blob(new),
        "clock_slots": LABELS,
        "ct248_selected_tests_blob": TESTS_BLOB,
        "ct248_source_arms": 48 * 3,
        "ct248_scope": "per reset_calls() to calls() readout; exact C13/C169/D counter parity",
        "clock_scope": "Runtime after construct; map eval-only; doubling padd-only",
        "measurements": None,
        "status": "[pcc:unverified]; syntax-only until native execution and full-corpus replay",
    }
    (out / "CT244_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", "utf-8")
    print(json.dumps(receipt, sort_keys=True))

if __name__ == "__main__":
    main()
