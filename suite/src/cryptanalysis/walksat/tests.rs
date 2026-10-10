//! Differential tests: every model is checked against its instance,
//! every decomposition against the group and against the exhaustive
//! decomposition set, and the local search never claims UNSAT.

use super::*;
use crate::cryptanalysis::koblitz_index_calculus::{
    build_frobenius_factor_base, enumerate_decompose, koblitz_index_calculus_dlp_with_factor_base,
    sat_decompose, DecompositionStrategy, KoblitzIcOptions,
};
use crate::cryptanalysis::sat::{check_model, SolveResult, Solver};
use crate::cryptanalysis::semaev_sat::{encode_boolean_system_with, XorEncoding};
use std::collections::{BTreeSet, HashMap};

fn opts(seed: u64, tries: u32, flips: u64) -> WalkSatOptions {
    WalkSatOptions {
        seed,
        max_tries: tries,
        max_flips: flips,
        noise_permille: 400,
    }
}

/// A planted random 3-SAT instance at clause ratio `ratio`.
fn planted_3sat(rng: &mut SplitMix, n: u32, clauses: usize) -> (Vec<Vec<Lit>>, Vec<bool>) {
    let plant: Vec<bool> = (0..n).map(|_| rng.next() & 1 == 1).collect();
    let mut out = Vec::with_capacity(clauses);
    while out.len() < clauses {
        let c: Vec<Lit> = (0..3)
            .map(|_| {
                let v = rng.below(u64::from(n)) as Lit + 1;
                if rng.next() & 1 == 1 {
                    v
                } else {
                    -v
                }
            })
            .collect();
        if check_model(std::slice::from_ref(&c), &plant) {
            out.push(c);
        }
    }
    (out, plant)
}

#[test]
fn cnf_models_on_planted_3sat_always_check() {
    let mut rng = SplitMix(1);
    let mut found = 0;
    for inst in 0..24u64 {
        let n = 40 + (inst % 4) as u32 * 20;
        let (clauses, _) = planted_3sat(&mut rng, n, (n as usize * 41) / 10);
        let mut w = WalkSat::new(n);
        for c in &clauses {
            w.add_clause(c.clone());
        }
        if w.solve(&opts(inst, 10, 20_000)) == WalkResult::Sat {
            assert!(check_model(&clauses, w.model()), "instance {inst}");
            assert!(w.check(w.model()));
            found += 1;
        }
    }
    // Planted below the threshold: local search's home ground.
    assert_eq!(found, 24, "planted 3-SAT success count");
}

#[test]
fn cnf_xor_models_on_planted_parity_mix_always_check() {
    let mut rng = SplitMix(2);
    let mut found = 0;
    for inst in 0..16u64 {
        let n = 30u32;
        let (clauses, plant) = planted_3sat(&mut rng, n, 60);
        let mut w = WalkSat::new(n);
        let mut cdcl = Solver::new(n);
        for c in &clauses {
            w.add_clause(c.clone());
            cdcl.add_clause(c.clone());
        }
        let mut rows = Vec::new();
        for _ in 0..12 {
            let vars: Vec<u32> = (0..4).map(|_| rng.below(u64::from(n)) as u32 + 1).collect();
            let rhs = vars.iter().fold(false, |p, &v| p ^ plant[(v - 1) as usize]);
            w.add_xor(&vars, rhs);
            cdcl.add_xor(&vars, rhs);
            rows.push((vars, rhs));
        }
        assert_eq!(cdcl.solve(), SolveResult::Sat);
        if w.solve(&opts(inst, 10, 50_000)) == WalkResult::Sat {
            let model = w.model();
            assert!(check_model(&clauses, model));
            for (vars, rhs) in &rows {
                assert_eq!(
                    vars.iter().fold(false, |p, &v| p ^ model[(v - 1) as usize]),
                    *rhs
                );
            }
            found += 1;
        }
    }
    assert!(found >= 12, "planted parity mix: {found}/16");
}

#[test]
fn never_claims_a_model_of_an_unsatisfiable_instance() {
    // Root contradictions.
    let mut w = WalkSat::new(2);
    w.add_clause(vec![]);
    assert_eq!(w.solve(&opts(0, 3, 100)), WalkResult::Unknown);
    assert_eq!(w.stats.flips, 0);
    let mut w = WalkSat::new(2);
    w.add_xor(&[1, 1], true);
    assert_eq!(w.solve(&opts(0, 3, 100)), WalkResult::Unknown);
    // Contradictions only search can meet.
    let mut w = WalkSat::new(3);
    w.add_xor(&[1, 2], false);
    w.add_xor(&[2, 3], false);
    w.add_xor(&[1, 3], true);
    assert_eq!(w.solve(&opts(1, 5, 1_000)), WalkResult::Unknown);
    assert_eq!(w.stats.flips, 5_000);
    let mut w = WalkSat::new(1);
    w.add_clause(vec![1]);
    w.add_clause(vec![-1]);
    assert_eq!(w.solve(&opts(1, 2, 500)), WalkResult::Unknown);
    // Random 3-SAT far above the threshold, proven UNSAT by CDCL.
    let mut rng = SplitMix(3);
    let mut unsat_seen = 0;
    for inst in 0..12u64 {
        let n = 12u32;
        let clauses: Vec<Vec<Lit>> = (0..120)
            .map(|_| {
                (0..3)
                    .map(|_| {
                        let v = rng.below(u64::from(n)) as Lit + 1;
                        if rng.next() & 1 == 1 {
                            v
                        } else {
                            -v
                        }
                    })
                    .collect()
            })
            .collect();
        let mut cdcl = Solver::new(n);
        let mut w = WalkSat::new(n);
        for c in &clauses {
            cdcl.add_clause(c.clone());
            w.add_clause(c.clone());
        }
        let verdict = cdcl.solve();
        let walk = w.solve(&opts(inst, 4, 2_000));
        if verdict == SolveResult::Unsat {
            unsat_seen += 1;
            assert_eq!(walk, WalkResult::Unknown);
        }
        if walk == WalkResult::Sat {
            assert!(check_model(&clauses, w.model()));
        }
    }
    assert!(unsat_seen >= 6, "the generator must produce UNSAT cases");
}

/// A random sparse polynomial system of degree ≤ `deg` with `plant` as
/// a root when `planted`.
fn random_system(
    rng: &mut SplitMix,
    n_vars: usize,
    n_eqs: usize,
    terms: usize,
    deg: u32,
    plant: Option<u64>,
) -> Vec<F2BoolPoly> {
    (0..n_eqs)
        .map(|_| {
            let mut monos = Vec::new();
            for _ in 0..terms {
                let d = 1 + rng.below(u64::from(deg)) as u32;
                let mut mask = 0u64;
                for _ in 0..d {
                    mask |= 1u64 << rng.below(n_vars as u64);
                }
                monos.push(F2BoolMono::from_mask(mask));
            }
            if rng.next() & 1 == 1 {
                monos.push(F2BoolMono::one());
            }
            let mut p = F2BoolPoly::from_monos(monos, n_vars);
            if let Some(a) = plant {
                if p.eval(a) == 1 {
                    p = F2BoolPoly::from_monos(
                        p.terms.iter().copied().chain([F2BoolMono::one()]).collect(),
                        n_vars,
                    );
                }
            }
            p
        })
        .collect()
}

fn brute_roots(n_vars: usize, eqs: &[F2BoolPoly]) -> BTreeSet<u64> {
    (0..1u64 << n_vars)
        .filter(|&a| eqs.iter().all(|e| e.eval(a) == 0))
        .collect()
}

/// Every root AnfWalk reaches by blocking each one it returns.
fn anf_enumerate(n_vars: usize, eqs: &[F2BoolPoly], o: &WalkSatOptions) -> BTreeSet<u64> {
    let mut w = AnfWalk::new(n_vars, eqs);
    let mut out = BTreeSet::new();
    let mut o = *o;
    while w.solve(&o) == WalkResult::Sat {
        let a = w.model();
        assert!(eqs.iter().all(|e| e.eval(a) == 0), "unchecked model");
        assert!(out.insert(a), "a blocked root came back");
        w.block(a);
        o.seed = o.seed.wrapping_add(1);
    }
    out
}

/// Every root CDCL reaches by blocking clause (the generic path).
fn cdcl_enumerate(n_vars: usize, eqs: &[F2BoolPoly]) -> BTreeSet<u64> {
    cdcl_enumerate_capped(n_vars, eqs, usize::MAX).0
}

/// At most `cap` CDCL roots; the flag says whether the set is complete
/// (the last solve ended UNSAT).
fn cdcl_enumerate_capped(n_vars: usize, eqs: &[F2BoolPoly], cap: usize) -> (BTreeSet<u64>, bool) {
    let mut enc = encode_boolean_system_with(n_vars, eqs, &[], XorEncoding::Native);
    let mut out = BTreeSet::new();
    if enc.trivially_unsat {
        return (out, true);
    }
    loop {
        if out.len() >= cap {
            return (out, false);
        }
        match enc.solver.solve() {
            SolveResult::Sat => {}
            SolveResult::Unsat => return (out, true),
            SolveResult::Unknown => panic!("no conflict budget is set"),
        }
        let a = enc.model_assignment();
        out.insert(a);
        enc.solver.reset_search();
        enc.solver.add_clause(
            (0..n_vars)
                .map(|i| {
                    let l = (i + 1) as Lit;
                    if (a >> i) & 1 == 1 {
                        -l
                    } else {
                        l
                    }
                })
                .collect(),
        );
    }
}

#[test]
fn anf_root_enumeration_equals_brute_force_and_cdcl() {
    let mut rng = SplitMix(4);
    for inst in 0..40u64 {
        let n_vars = 6 + (inst % 11) as usize; // 6..=16
        let planted = inst % 4 != 3;
        let plant = planted.then(|| rng.next() & ((1u64 << n_vars) - 1));
        let eqs = random_system(&mut rng, n_vars, n_vars, 6, 3, plant);
        let truth = brute_roots(n_vars, &eqs);
        if let Some(p) = plant {
            assert!(truth.contains(&p));
        }
        let walk = anf_enumerate(n_vars, &eqs, &opts(inst, 6, 20_000));
        assert_eq!(walk, truth, "instance {inst}: ANF walk roots");
        assert_eq!(cdcl_enumerate(n_vars, &eqs), truth, "instance {inst}: CDCL");
    }
}

#[test]
fn cnf_xor_walk_on_bool_systems_decodes_to_roots() {
    let mut rng = SplitMix(5);
    let mut found = 0;
    for inst in 0..30u64 {
        let n_vars = 6 + (inst % 9) as usize;
        let plant = (inst % 5 != 4).then(|| rng.next() & ((1u64 << n_vars) - 1));
        let eqs = random_system(&mut rng, n_vars, n_vars, 5, 3, plant);
        let truth = brute_roots(n_vars, &eqs);
        let mut w = WalkSat::from_bool_system(n_vars, &eqs);
        match w.solve(&opts(inst, 8, 20_000)) {
            WalkResult::Sat => {
                let root = w.assignment() & ((1u64 << n_vars) - 1);
                assert!(truth.contains(&root), "instance {inst}");
                found += 1;
            }
            WalkResult::Unknown => {}
        }
        // Blocking every true root leaves an instance with no model.
        let mut w = WalkSat::from_bool_system(n_vars, &eqs);
        for &r in &truth {
            w.block_assignment(r, n_vars);
        }
        assert_eq!(w.solve(&opts(inst, 2, 3_000)), WalkResult::Unknown);
    }
    assert!(found >= 20, "CNF+XOR walk found {found}/30");
}

#[test]
fn anf_handles_the_64_variable_boundary_and_constants() {
    let mut rng = SplitMix(6);
    let plant = rng.next();
    let eqs = random_system(&mut rng, 64, 40, 4, 2, Some(plant));
    let mut w = AnfWalk::new(64, &eqs);
    assert_eq!(w.solve(&opts(7, 20, 200_000)), WalkResult::Sat);
    assert!(eqs.iter().all(|e| e.eval(w.model()) == 0));
    // `1 = 0` is never satisfiable and needs no search.
    let mut w = AnfWalk::new(5, &[F2BoolPoly::one(5)]);
    assert_eq!(w.solve(&opts(0, 3, 100)), WalkResult::Unknown);
    assert_eq!(w.stats.flips, 0);
    // No variables at all: the empty system has the single root 0.
    let mut w = AnfWalk::new(0, &[]);
    assert_eq!(w.solve(&opts(0, 1, 1)), WalkResult::Sat);
    w.block(0);
    assert_eq!(w.solve(&opts(0, 1, 1)), WalkResult::Unknown);
    // x0·x1 = 1 and x0 = 0: unsatisfiable, walk must not claim a model.
    let eqs = vec![
        F2BoolPoly::from_monos(vec![F2BoolMono::from_mask(3), F2BoolMono::one()], 2),
        F2BoolPoly::from_monos(vec![F2BoolMono::var(0)], 2),
    ];
    let mut w = AnfWalk::new(2, &eqs);
    assert_eq!(w.solve(&opts(0, 4, 1_000)), WalkResult::Unknown);
}

// ── Decomposition: differential against CDCL and exhaustive search ──

/// Every sorted index multiset over the base summing to `target`:
/// `m − 1` summands by nested loops, the last one by lookup.
fn all_decompositions(
    kc: &KoblitzCurve,
    fb: &FrobeniusFactorBase,
    target: &BinaryPoint,
    m: usize,
) -> BTreeSet<Vec<usize>> {
    use crate::cryptanalysis::koblitz_index_calculus::pack_point;
    fn neg(p: &BinaryPoint) -> BinaryPoint {
        match p {
            BinaryPoint::Infinity => BinaryPoint::Infinity,
            BinaryPoint::Affine { x, y } => BinaryPoint::Affine {
                x: x.clone(),
                y: x.add(y),
            },
        }
    }
    #[allow(clippy::too_many_arguments)]
    fn rec(
        kc: &KoblitzCurve,
        fb: &FrobeniusFactorBase,
        key: &HashMap<u64, usize>,
        target: &BinaryPoint,
        left: usize,
        from: usize,
        acc: &BinaryPoint,
        chosen: &mut Vec<usize>,
        out: &mut BTreeSet<Vec<usize>>,
    ) {
        if left == 1 {
            let rest = kc.add(target, &neg(acc));
            if let Some(&j) = key.get(&pack_point(&rest)) {
                if j >= from && fb.points[j] == rest {
                    let mut d = chosen.clone();
                    d.push(j);
                    out.insert(d);
                }
            }
            return;
        }
        for i in from..fb.points.len() {
            chosen.push(i);
            let next = kc.add(acc, &fb.points[i]);
            rec(kc, fb, key, target, left - 1, i, &next, chosen, out);
            chosen.pop();
        }
    }
    let key: HashMap<u64, usize> = fb
        .points
        .iter()
        .enumerate()
        .map(|(i, p)| (pack_point(p), i))
        .collect();
    assert_eq!(key.len(), fb.points.len(), "packed keys are distinct");
    let mut out = BTreeSet::new();
    rec(
        kc,
        fb,
        &key,
        target,
        m,
        0,
        &BinaryPoint::Infinity,
        &mut Vec::new(),
        &mut out,
    );
    out
}

/// Planted targets (sums of `m` base points), multiples of the
/// generator, the 2-torsion point `(0, √b)` when it exists, and `O`.
fn targets(kc: &KoblitzCurve, fb: &FrobeniusFactorBase, m: usize, seed: u64) -> Vec<BinaryPoint> {
    let mut rng = SplitMix(seed);
    let mut out: Vec<BinaryPoint> = (0..10)
        .map(|_| {
            (0..m).fold(BinaryPoint::Infinity, |acc, _| {
                kc.add(&acc, &fb.points[rng.below(fb.points.len() as u64) as usize])
            })
        })
        .collect();
    let g = kc.generator().clone();
    for k in 1..=10u32 {
        out.push(kc.mul(&g, &BigUint::from(k * 7 + 1)));
    }
    out.extend(crate::cryptanalysis::koblitz_index_calculus::points_with_x(
        &kc.curve,
        &F2mElement::zero(kc.n),
    ));
    out.push(BinaryPoint::Infinity);
    out
}

fn check_cell(a: u8, n: u32, m: usize) -> (usize, usize) {
    let kc = KoblitzCurve::new(a, n).unwrap();
    let fb = build_frobenius_factor_base(&kc, 0).unwrap();
    let index_of = fb.index_map();
    let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
    let (mut decomposable, mut walk_found) = (0, 0);
    for (t, target) in targets(&kc, &fb, m, 9 + n as u64).iter().enumerate() {
        let truth = all_decompositions(&kc, &fb, target, m);
        let (cdcl, cdcl_stats) = sat_decompose(&kc, &fb, &index_of, &st, target, m, 4096, None);
        assert_eq!(cdcl_stats.spurious, 0);
        if *target != BinaryPoint::Infinity {
            assert_eq!(
                cdcl.is_some(),
                !truth.is_empty(),
                "K{a}/2^{n} m={m} target {t}"
            );
        }
        decomposable += usize::from(cdcl.is_some());
        for encoding in [WalkEncoding::Anf, WalkEncoding::CnfXor] {
            let o = WalkSatDecompositionOptions {
                encoding,
                ..WalkSatDecompositionOptions::default()
            };
            let (walk, ws) = walksat_decompose(&kc, &fb, &index_of, &st, target, m, &o);
            assert_eq!(ws.spurious, 0);
            assert!(!ws.unsupported);
            if let Some(idxs) = &walk {
                // In the exhaustive set, so also a group identity.
                assert!(truth.contains(idxs), "{encoding:?} target {t}: {idxs:?}");
                assert!(cdcl.is_some(), "walk found what CDCL refuted");
                if encoding == WalkEncoding::Anf {
                    walk_found += 1;
                }
            } else {
                assert!(ws.exhausted, "a miss is always reported as unknown");
            }
            // Same seed and target, same answer and counters.
            let again = walksat_decompose(&kc, &fb, &index_of, &st, target, m, &o);
            assert_eq!((walk.clone(), ws), again);

            // The portfolio's verdict is the CDCL verdict.
            let (port, ps) = walksat_then_sat_decompose(
                &kc,
                &fb,
                &index_of,
                &st,
                target,
                m,
                4096,
                None,
                SatDecompositionOptions::default(),
                &o,
            );
            assert_eq!(
                port.is_some(),
                cdcl.is_some(),
                "portfolio verdict, target {t}"
            );
            assert_eq!(ps.spurious, 0);
            if walk.is_some() {
                assert_eq!(port, walk);
                assert!(!ps.refuted);
            } else {
                assert_eq!(port, cdcl, "fallback must return the CDCL answer");
                assert_eq!(ps.refuted, cdcl_stats.refuted);
            }
            if let Some(idxs) = &port {
                assert!(truth.contains(idxs));
            }
        }
    }
    (decomposable, walk_found)
}

#[test]
fn decompositions_m2_match_cdcl_and_exhaustive_search() {
    for (a, n) in [(0u8, 9u32), (1, 9), (1, 11), (0, 13)] {
        let (dec, found) = check_cell(a, n, 2);
        assert!(dec >= 10, "K{a}/2^{n}: planted targets decompose");
        assert_eq!(found, dec, "K{a}/2^{n} m=2: walk found {found} of {dec}");
    }
}

#[test]
fn decompositions_m3_match_cdcl_and_exhaustive_search() {
    for (a, n) in [(0u8, 9u32), (1, 9)] {
        let (dec, found) = check_cell(a, n, 3);
        assert!(dec >= 10, "K{a}/2^{n}: planted targets decompose");
        assert!(
            found * 2 >= dec,
            "K{a}/2^{n} m=3: walk found {found} of {dec}"
        );
    }
}

#[test]
fn walk_roots_of_a_decomposition_system_equal_the_cdcl_roots() {
    // The root set — not just one root — of real systems, with the
    // trace row: every root the walk reaches (blocking each one it
    // returns) is a CDCL root, and where the root set is small the walk
    // reaches all of it.  Sets compare as sorted integers.
    let mut compared_equal = 0;
    for (a, n, m) in [(0u8, 7u32, 2usize), (1, 9, 2), (0, 9, 3)] {
        let kc = KoblitzCurve::new(a, n).unwrap();
        let fb = build_frobenius_factor_base(&kc, 0).unwrap();
        let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
        for target in targets(&kc, &fb, m, 3).iter().take(8) {
            let BinaryPoint::Affine { x: x_r, .. } = target else {
                continue;
            };
            let sys = crate::cryptanalysis::polynomial_reuse::build_decomposition_system_reusing(
                &fb.subspace_basis,
                x_r,
                &kc.curve.b,
                m,
                &st,
            )
            .unwrap();
            let mut eqs = sys.equations.clone();
            eqs.push(trace_row(&kc, &fb, x_r, m, sys.n_vars));
            let (truth, complete) = cdcl_enumerate_capped(sys.n_vars, &eqs, 65);
            if complete && truth.len() <= 64 {
                let walk = anf_enumerate(sys.n_vars, &eqs, &opts(11, 8, 20_000));
                assert_eq!(walk, truth, "K{a}/2^{n} m={m}: small root set");
                compared_equal += 1;
            } else {
                // Large root sets: every walk root is a root (checked
                // against the system), and distinct once blocked.
                let mut w = AnfWalk::new(sys.n_vars, &eqs);
                let mut seen = BTreeSet::new();
                for seed in 0..4 {
                    if w.solve(&opts(seed, 4, 20_000)) == WalkResult::Sat {
                        assert!(eqs.iter().all(|e| e.eval(w.model()) == 0));
                        assert!(seen.insert(w.model()));
                        w.block(w.model());
                    }
                }
            }
        }
    }
    assert!(
        compared_equal >= 8,
        "{compared_equal} systems compared exactly"
    );
}

#[test]
fn degenerate_base_never_yields_a_walk_decomposition() {
    // K_0 / F_2^7 with this base: nothing decomposes (CDCL refutes all).
    let kc = KoblitzCurve::new(0, 7).unwrap();
    let fb = build_frobenius_factor_base(&kc, 0).unwrap();
    let index_of = fb.index_map();
    let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
    let g = kc.generator().clone();
    for k in 1..29u32 {
        let target = kc.mul(&g, &BigUint::from(k));
        assert!(enumerate_decompose(&kc, &fb, &index_of, &target, 2).is_none());
        let o = WalkSatDecompositionOptions::default();
        let (out, stats) = walksat_decompose(&kc, &fb, &index_of, &st, &target, 2, &o);
        assert!(out.is_none());
        assert!(stats.exhausted);
        assert_eq!(stats.spurious, 0);
    }
}

#[test]
fn walksat_strategy_solves_the_dlp() {
    let kc = KoblitzCurve::new(0, 9).unwrap();
    let g = kc.generator().clone();
    let d = BigUint::from(53u32);
    let q = kc.mul(&g, &d);
    let fb = build_frobenius_factor_base(&kc, 0).unwrap();
    let run = |strategy| {
        koblitz_index_calculus_dlp_with_factor_base(
            &kc,
            &q,
            &fb,
            &KoblitzIcOptions {
                strategy,
                ..KoblitzIcOptions::default()
            },
        )
        .unwrap()
    };
    let walk = run(DecompositionStrategy::WalkSat);
    let cdcl = run(DecompositionStrategy::Sat);
    assert_eq!(walk.log, Some(d.clone()));
    assert_eq!(cdcl.log, Some(d));
    assert!(walk.sat_models > 0);
    assert_eq!(walk.sat_invalid_models, 0);
    // Same targets, same verdicts: the relation counts agree.
    assert_eq!(walk.relations, cdcl.relations);
    assert_eq!(walk.trials, cdcl.trials);
}

#[test]
#[ignore = "diagnostic: prints system and base sizes"]
fn print_cell_sizes() {
    for (a, n) in [(0u8, 7u32), (0, 9), (1, 9), (1, 11), (0, 13)] {
        let kc = KoblitzCurve::new(a, n).unwrap();
        let fb = build_frobenius_factor_base(&kc, 0).unwrap();
        println!(
            "K{a}/2^{n}: ell={} |F|={}",
            fb.subspace_basis.len(),
            fb.points.len()
        );
    }
}
