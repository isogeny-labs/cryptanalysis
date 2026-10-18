//! Area `pdp`, specialised kernels `pdp/spec_fes_*`: the Gray-code chain
//! search of `cryptanalysis::fes_chain` (what `mq_fes_decompose`
//! dispatches to for `m ≥ 3`) against the generic chained-system oracles
//! (`sat_decompose`, `groebner_decompose`) on the **same** cells and
//! targets.
//!
//! Cells are built as `pdp.rs` builds its ladder cells (same base rule:
//! the admissible Frobenius-invariant base with the most points), with
//! this file's own seed so every `spec_fes_*` kernel on one `(n, ℓ, m)`
//! sees identical targets.  The specialised kernels fingerprint the
//! returned decompositions, the `SatDecompositionStats` and the walk's
//! machine-independent counters (leaves, quadratic solves, table probes,
//! roots, lifts).  The generic kernels fingerprint their own decompositions
//! and counters; the two return valid decompositions of the same targets
//! but not necessarily the same ones (different search orders), so their
//! fingerprints are not comparable with each other — only with the same
//! kernel on another revision.

use crate::harness::{Closure, Fp, Kernel, Tier, Workload};
use cryptanalysis_suite::binary_ecc::BinaryPoint;
use cryptanalysis_suite::cryptanalysis::fes_chain::{
    fes_chain_decompose_with, FesChainStats, Symmetry,
};
use cryptanalysis_suite::cryptanalysis::koblitz_groebner::{
    FieldStructure, SolveStats, SolverEngine,
};
use cryptanalysis_suite::cryptanalysis::koblitz_index_calculus::{
    build_frobenius_factor_base_from_divisor, groebner_decompose, invariant_factors, sat_decompose,
    FrobeniusFactorBase, KoblitzCurve, SatDecompositionStats,
};
use num_bigint::BigUint;
use rand::{rngs::StdRng, Rng, SeedableRng};
use std::collections::HashMap;

const SEED: u64 = 0x5350_4543_4645_5321;

fn fp_decomp(fp: Fp, d: &Option<Vec<usize>>) -> Fp {
    match d {
        None => fp.u64(u64::MAX),
        Some(idxs) => {
            let mut fp = fp.usize(idxs.len());
            for &i in idxs {
                fp = fp.usize(i);
            }
            fp
        }
    }
}

fn fp_sat_stats(fp: Fp, s: &SatDecompositionStats) -> Fp {
    fp.usize(s.solver_calls)
        .usize(s.models)
        .bool(s.refuted)
        .bool(s.exhausted)
        .usize(s.spurious)
        .usize(s.implied_rows)
        .u64(s.conflicts)
}

fn fp_chain(fp: Fp, s: &FesChainStats) -> Fp {
    fp.u64(s.counters.leaves)
        .u64(s.counters.solves)
        .u64(s.counters.probes)
        .u64(s.counters.roots)
        .u64(s.lifts)
}

fn fp_solve_stats(fp: Fp, s: &SolveStats) -> Fp {
    fp.usize(s.reductions)
        .usize(s.infeasible_branches)
        .usize(s.propagations)
        .usize(s.splits)
        .bool(s.exhausted)
        .u64(u64::from(s.max_degree_built))
        .usize(s.oversize)
        .usize(s.eliminated)
}

struct Cell {
    kc: KoblitzCurve,
    fb: FrobeniusFactorBase,
    index_of: HashMap<(BigUint, BigUint), usize>,
    st: FieldStructure,
    m: usize,
    targets: Vec<BinaryPoint>,
}

/// `pdp.rs::choose_base`: the admissible invariant base of dimension
/// `ell` with the most points over `K_0`, `K_1`.
fn choose_base(n: u32, ell: u32, m: usize) -> (KoblitzCurve, FrobeniusFactorBase) {
    let mut best: Option<(KoblitzCurve, FrobeniusFactorBase)> = None;
    for a in 0u8..=1 {
        let Some(kc) = KoblitzCurve::new(a, n) else {
            continue;
        };
        let degs: Vec<usize> = invariant_factors(&kc)
            .iter()
            .map(|f| f.degree().unwrap_or(0))
            .collect();
        let k = degs.len().min(16);
        for mask in 1u32..1 << k {
            let idx: Vec<usize> = (0..k).filter(|&i| mask >> i & 1 == 1).collect();
            if idx.iter().map(|&i| degs[i]).sum::<usize>() != ell as usize {
                continue;
            }
            let Some(fb) = build_frobenius_factor_base_from_divisor(&kc, &idx) else {
                continue;
            };
            if !fb.m_can_decompose(&kc, m) {
                continue;
            }
            if best
                .as_ref()
                .is_none_or(|b| fb.points.len() > b.1.points.len())
            {
                best = Some((kc.clone(), fb));
            }
        }
    }
    best.expect("cell has an admissible base")
}

/// `planted` sums of `m` base points then `random` points `[k]G`.
fn cell(n: u32, ell: u32, m: usize, planted: usize, random: usize) -> Cell {
    let (kc, fb) = choose_base(n, ell, m);
    let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
    let index_of = fb.index_map();
    let mut rng = StdRng::seed_from_u64(SEED ^ (u64::from(n) << 8) ^ m as u64);
    let mut targets = Vec::new();
    while targets.len() < planted {
        let t = (0..m).fold(BinaryPoint::Infinity, |acc, _| {
            kc.add(&acc, &fb.points[rng.gen_range(0..fb.points.len())])
        });
        if matches!(t, BinaryPoint::Affine { .. }) {
            targets.push(t);
        }
    }
    while targets.len() < planted + random {
        let k = BigUint::from(rng.gen_range(1u64..u64::MAX));
        let t = kc.mul(kc.generator(), &k);
        if matches!(t, BinaryPoint::Affine { .. }) {
            targets.push(t);
        }
    }
    Cell {
        kc,
        fb,
        index_of,
        st,
        m,
        targets,
    }
}

/// The specialised chain search (the `mq_fes` `m ≥ 3` dispatch target
/// for `Sorted`).
fn spec_on(
    n: u32,
    ell: u32,
    m: usize,
    planted: usize,
    random: usize,
    sym: Symmetry,
) -> Box<dyn Workload> {
    let c = cell(n, ell, m, planted, random);
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for t in &c.targets {
            let (d, s, x) = fes_chain_decompose_with(&c.kc, &c.fb, &c.index_of, t, c.m, sym)
                .expect("the specialised path applies");
            fp = fp_chain(fp_sat_stats(fp_decomp(fp, &d), &s), &x);
        }
        fp.finish()
    }))
}

/// Generic: `sat_decompose` on the chained system (64 models, Macaulay
/// degree 2, the pdp ladder's settings).
fn sat_on(n: u32, ell: u32, m: usize, planted: usize, random: usize) -> Box<dyn Workload> {
    let c = cell(n, ell, m, planted, random);
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for t in &c.targets {
            let (d, s) = sat_decompose(&c.kc, &c.fb, &c.index_of, &c.st, t, c.m, 64, Some(2));
            fp = fp_sat_stats(fp_decomp(fp, &d), &s);
        }
        fp.finish()
    }))
}

/// Generic: `groebner_decompose` (default engine, 20k nodes).
fn groebner_on(n: u32, ell: u32, m: usize, planted: usize, random: usize) -> Box<dyn Workload> {
    let c = cell(n, ell, m, planted, random);
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for t in &c.targets {
            let (d, s) = groebner_decompose(
                &c.kc,
                &c.fb,
                &c.index_of,
                &c.st,
                t,
                c.m,
                SolverEngine::default(),
                20_000,
            );
            fp = fp_solve_stats(fp_decomp(fp, &d), &s);
        }
        fp.finish()
    }))
}

fn spec_fes_m3_n9() -> Box<dyn Workload> {
    spec_on(9, 3, 3, 160, 160, Symmetry::Sorted)
}
fn spec_fes_m3_n9_generic_groebner() -> Box<dyn Workload> {
    groebner_on(9, 3, 3, 160, 160)
}
fn spec_fes_m3_n9_small() -> Box<dyn Workload> {
    spec_on(9, 3, 3, 8, 8, Symmetry::Sorted)
}
fn spec_fes_m3_n9_small_generic_sat() -> Box<dyn Workload> {
    sat_on(9, 3, 3, 8, 8)
}
fn spec_fes_m3_n15() -> Box<dyn Workload> {
    spec_on(15, 5, 3, 64, 64, Symmetry::Sorted)
}
fn spec_fes_m3_n15_full() -> Box<dyn Workload> {
    spec_on(15, 5, 3, 64, 64, Symmetry::Full)
}
fn spec_fes_m3_n15_small() -> Box<dyn Workload> {
    spec_on(15, 5, 3, 2, 2, Symmetry::Sorted)
}
fn spec_fes_m3_n15_small_generic_groebner() -> Box<dyn Workload> {
    groebner_on(15, 5, 3, 2, 2)
}
fn spec_fes_m4_n9() -> Box<dyn Workload> {
    spec_on(9, 2, 4, 128, 128, Symmetry::Sorted)
}
fn spec_fes_m4_n9_small() -> Box<dyn Workload> {
    spec_on(9, 2, 4, 4, 4, Symmetry::Sorted)
}
fn spec_fes_m4_n9_small_generic_sat() -> Box<dyn Workload> {
    sat_on(9, 2, 4, 4, 4)
}
fn spec_fes_m4_n9_small_generic_groebner() -> Box<dyn Workload> {
    groebner_on(9, 2, 4, 4, 4)
}
fn spec_fes_m3_n31() -> Box<dyn Workload> {
    spec_on(31, 10, 3, 2, 2, Symmetry::Sorted)
}

pub fn register(kernels: &mut Vec<Kernel>) {
    let mut add =
        |id: &'static str, desc: &'static str, tier: Tier, setup: fn() -> Box<dyn Workload>| {
            kernels.push(Kernel {
                id,
                area: "pdp",
                desc,
                tier,
                setup,
            });
        };
    add(
        "pdp/spec_fes_m3_n9",
        "fes_chain Gray-code chain search (sorted), cell n=9 l=3 m=3, 160 planted + 160 random",
        Tier::Quick,
        spec_fes_m3_n9,
    );
    add(
        "pdp/spec_fes_m3_n9_generic_groebner",
        "generic groebner_decompose (default engine, 20k nodes) on the spec_fes_m3_n9 cell and targets",
        Tier::Quick,
        spec_fes_m3_n9_generic_groebner,
    );
    add(
        "pdp/spec_fes_m3_n9_small",
        "fes_chain chain search (sorted), cell n=9 l=3 m=3, 8 planted + 8 random",
        Tier::Full,
        spec_fes_m3_n9_small,
    );
    add(
        "pdp/spec_fes_m3_n9_small_generic_sat",
        "generic sat_decompose (64 models, Macaulay 2) on the spec_fes_m3_n9_small cell and targets",
        Tier::Full,
        spec_fes_m3_n9_small_generic_sat,
    );
    add(
        "pdp/spec_fes_m3_n15",
        "fes_chain Gray-code chain search (sorted), cell n=15 l=5 m=3, 64 planted + 64 random",
        Tier::Quick,
        spec_fes_m3_n15,
    );
    add(
        "pdp/spec_fes_m3_n15_full",
        "fes_chain Gray-code chain search (all orderings), cell n=15 l=5 m=3, 64 + 64",
        Tier::Quick,
        spec_fes_m3_n15_full,
    );
    add(
        "pdp/spec_fes_m3_n15_small",
        "fes_chain chain search (sorted), cell n=15 l=5 m=3, 2 planted + 2 random",
        Tier::Full,
        spec_fes_m3_n15_small,
    );
    add(
        "pdp/spec_fes_m3_n15_small_generic_groebner",
        "generic groebner_decompose (default engine, 20k nodes) on the spec_fes_m3_n15_small cell and targets",
        Tier::Full,
        spec_fes_m3_n15_small_generic_groebner,
    );
    add(
        "pdp/spec_fes_m4_n9",
        "fes_chain Gray-code chain search (sorted), cell n=9 l=2 m=4, 128 planted + 128 random",
        Tier::Quick,
        spec_fes_m4_n9,
    );
    add(
        "pdp/spec_fes_m4_n9_small",
        "fes_chain chain search (sorted), cell n=9 l=2 m=4, 4 planted + 4 random",
        Tier::Full,
        spec_fes_m4_n9_small,
    );
    add(
        "pdp/spec_fes_m4_n9_small_generic_sat",
        "generic sat_decompose (64 models, Macaulay 2) on the spec_fes_m4_n9_small cell and targets",
        Tier::Full,
        spec_fes_m4_n9_small_generic_sat,
    );
    add(
        "pdp/spec_fes_m4_n9_small_generic_groebner",
        "generic groebner_decompose (default engine, 20k nodes) on the spec_fes_m4_n9_small cell and targets",
        Tier::Full,
        spec_fes_m4_n9_small_generic_groebner,
    );
    add(
        "pdp/spec_fes_m3_n31",
        "fes_chain chain search (sorted), cell n=31 l=10 m=3 (past the generic reach), 2 + 2",
        Tier::Full,
        spec_fes_m3_n31,
    );
}
