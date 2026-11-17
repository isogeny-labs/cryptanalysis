#!/usr/bin/env python3
"""CT191 exact-source Rust norm price guard. Source only, [pcc:unverified]."""
from pathlib import Path
import hashlib

HERE = Path(__file__).resolve().parent
ORIGINAL_BLOB = "ac4146577f5019fc17674deb342eb5d9fc749715"
RUNTIME_BLOB = "b80eb91a39ae1e87f0fcde95e52ea3d3634558bc"

def git_blob(data):
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\x00" + data
    ).hexdigest()

def replace_one(source, old, new):
    if source.count(old) != 1:
        raise ValueError("CT191 not exactly one source anchor: " + old[:65])
    return source.replace(old, new)

def derivative(original):
    s = original
    changes = (
        ('use chained_n4_public_target::CheckedInstance;',
         'use chained_n4_public_target::CheckedInstance;\n'
         'use chained_n4_paired_fourth_preflight::models::even::back6;'),
        ('        target.quadratic.admit(&doubled).expect("actual target double");',
         """        target.quadratic.admit(&doubled).expect("actual target double");
        // Exact CT125 norm-point path: pmul(P,2) THEN descent, not D_padd.
        let optimized_norm = match curve::pmul(&target.quadratic.f, e, &z169, 2) {
            Pt::Inf => Pt::Inf,
            Pt::Aff(x, y) => Pt::Aff(back6(x), back6(y)),
        };
        let padd_then_descend = match doubled {
            Pt::Inf => Pt::Inf,
            Pt::Aff(x, y) => Pt::Aff(back6(x), back6(y)),
        };
        assert_eq!(optimized_norm, padd_then_descend,
                   "N2_actual and descended D_padd disagree mathematically");
        target.quadratic.admit(&optimized_norm)
            .expect("actual optimized norm point on target quadratic curve");"""),
        ('    let labels = ["C169","C13_first","C13_second","D","direct_warm","retained_warm"];',
         '    let labels = ["C169","C13_first","C13_second","D_padd","N2_actual","direct_warm","retained_warm"];'),
        ('    let mut readings: [Vec<u64>; 6] = std::array::from_fn(|_| Vec::new());',
         '    let mut readings: [Vec<u64>; 7] = std::array::from_fn(|_| Vec::new());'),
        ('let order = if block % 2 == 0 { [0,1,2,3,4,5] }\n'
         '                    else { [5,4,3,2,1,0] };',
         'let order = if block % 2 == 0 { [0,1,2,3,4,5,6] }\n'
         '                    else { [6,5,4,3,2,1,0] };'),
        ('let reps = if op < 4 { 64 } else { 5 };',
         'let reps = if op < 5 { 64 } else { 5 };'),
        ('                    4 | 5 => {',
         """                    4 => {
                        // Source-identical arithmetic to CT125 Runtime::norm_point
                        // (its Cell counter bump is intentionally NOT timed).
                        // The selected operand cohort remains CT126's FIVE
                        // points, NOT the full 48/695 population.
                        let doubled = curve::pmul(&target.quadratic.f, e, &final_pts[i], 2);
                        let actual_norm = match doubled {
                            Pt::Inf => Pt::Inf,
                            Pt::Aff(x, y) => Pt::Aff(back6(x), back6(y)),
                        };
                        black_box(actual_norm);
                    }
                    5 | 6 => {"""),
        ('let out = if op == 4 {', 'let out = if op == 5 {'),
        ('if i < 4 {64} else {5}', 'if i < 5 {64} else {5}'),
        ('"schema":"ct126-primitive-price/v1"',
         '"schema":"ct191-exact-norm-warm-price/v1"'),
        ('"scope":"actual elliptic arithmetic in prebuilt geometry; NOT cold single-target ECDLP"',
         '"scope":"five original CT126 toy input points, same warm geometry; N2_actual executes pmul(2)+back6; NOT full 48/695 custody, cold ECDLP or signed PCC"'),
        ('"timing_order":"ABBA by block; original/optimized process ABBA must be external"',
         '"timing_order":"alternating forward/reverse seven-arm order; external cold-process randomization separately required"'),
    )
    for old, new in changes:
        s = replace_one(s, old, new)
    return s

def audit(original, changed, runtime, cargo):
    if git_blob(original) != ORIGINAL_BLOB:
        raise ValueError("CT126 source changed from immutable historical blob")
    if git_blob(runtime) != RUNTIME_BLOB:
        raise ValueError("CT125 optimized runtime changed from immutable blob")
    if changed != derivative(original.decode("utf-8")).encode("utf-8"):
        raise ValueError("CT191 Rust source differs from strictly allowed CT126 patch")
    needle = b"descend_point(curve::pmul(&target.f, &target.curve, &point, 2))"
    if runtime.count(needle) != 1:
        raise ValueError("optimized norm-point runtime contract changed")
    if b"Pt::Aff(x, y) => Pt::Aff(back6(x), back6(y))" not in runtime:
        raise ValueError("CT125 actual descent is not the expected back6")
    names = ('chained-n4-fixed-jacobian-chain-evaluator',
             'chained-n4-fixed-jacobian-chain',
             'chained-n4-beta-rational-lift',
             'chained-n4-public-target',
             'chained-n4-paired-fourth-preflight',
             'isogeny_algos', 'serde_json')
    for n in names:
        if cargo.count(n.encode()) != 1:
            raise ValueError("missing or repeated dependency " + n)
    if b'path = "../../paired-fourth-preflight"' not in cargo:
        raise ValueError("CT125 back6 dependency path missing")
    if b'path = "../../../../../crypto/isogeny_algos"' not in cargo:
        raise ValueError("original source crypto library dependency path changed")
    return {
        "schema":"ct191-exact-norm-source-audit/v1",
        "standing":"[pcc:unverified]",
        "source_guard_passed":True,
        "old_ct126_git_blob":ORIGINAL_BLOB,
        "actual_ct125_git_blob":RUNTIME_BLOB,
        "rust_native_executed":False,
        "full_48_695_701_native_parity_reproduced":False,
        "complete_single_target_ecdlp_advantage_established":False,
    }

def read_inputs():
    return (
        (HERE.parent / "src/main.rs").read_bytes(),
        (HERE / "src/main.rs").read_bytes(),
        (HERE.parent.parent / "fixed-jacobian-chain-evaluator-02/derived/lib.rs").read_bytes(),
        (HERE / "Cargo.toml").read_bytes()
    )

if __name__ == "__main__":
    import json
    print(json.dumps(audit(*read_inputs()),sort_keys=True))
