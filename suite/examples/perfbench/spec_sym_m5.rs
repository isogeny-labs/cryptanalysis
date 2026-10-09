//! Area `pdp`, specialised paths: five-summand decomposition in the
//! symmetrised (Artin–Schreier) frame of `koblitz_symmetrised_m5`, against
//! the generic chains on the same instance.
//!
//! One instance per cell: `K_a/F_{2^n}`, a seeded random non-invariant
//! `V ∋ 1` of dimension `ℓ`, the factor base `F_u = {u(P) ∈ V}` and frozen
//! subgroup targets `[k]G` with `x ∉ {0, 1}`; all built in the untimed
//! setup, together with the per-base oracle state.  The timed region is the
//! decomposition alone.
//!
//! - `*_all_*` kernels enumerate **every** decomposition the shape reaches
//!   (`SymChainOracle::decompose_all`); their fingerprints cover the sorted
//!   decomposition sets, so the meet, the F4 `[4, 4]` pair, the folded `S₃`
//!   chain and the plain-`u` generic chain on one cell can be compared on
//!   identical output (the module's tests pin those sets equal).
//! - `*_first_*` kernels are the index-calculus oracle (first accepted
//!   relation): `symmetrised_decompose_dispatch` at `m = 5` under
//!   `ChainShape::Auto` (the meet), and the production generic `x`-chain
//!   `groebner_decompose` at `m = 5` on `F_x = {x(P) ∈ V}` — same curve,
//!   same `V`, same targets, but a different factor base, so the two
//!   compare on cost per target, not on the relation returned.

use crate::harness::{Closure, Fp, Kernel, Tier, Workload};
use cryptanalysis_suite::binary_ecc::BinaryPoint;
use cryptanalysis_suite::cryptanalysis::koblitz_groebner::{
    FieldStructure, SolveStats, SolverEngine,
};
use cryptanalysis_suite::cryptanalysis::koblitz_index_calculus::{
    groebner_decompose, point_key, KoblitzCurve,
};
use cryptanalysis_suite::cryptanalysis::koblitz_symmetrised::{
    build_symmetrised_factor_base_from_basis, plain_subspace_factor_base,
    random_subspace_containing_one, OracleOutcome, SymmetrisedFactorBase,
};
use cryptanalysis_suite::cryptanalysis::koblitz_symmetrised_m5::{
    subgroup_targets, symmetrised_decompose_dispatch, ChainEnumeration, ChainShape, ChainSolver,
    SymChainOracle,
};
use rand::{rngs::StdRng, SeedableRng};
use std::collections::HashMap;

const NODES: usize = 1_000_000;

fn f4() -> ChainSolver {
    ChainSolver::Groebner {
        engine: SolverEngine::default(),
        node_budget: NODES,
    }
}

/// A frozen cell, leaked so the per-base oracle can borrow it.
struct Cell {
    kc: &'static KoblitzCurve,
    st: &'static FieldStructure,
    fb: &'static SymmetrisedFactorBase,
    targets: Vec<BinaryPoint>,
}

fn cell(a: u8, n: u32, ell: usize, targets: usize) -> Cell {
    let kc: &'static KoblitzCurve = Box::leak(Box::new(KoblitzCurve::new(a, n).expect("curve")));
    let st: &'static FieldStructure =
        Box::leak(Box::new(FieldStructure::new(n, &kc.curve.irreducible)));
    let mut rng = StdRng::seed_from_u64(0x5359_4d35 ^ u64::from(n));
    let fb = loop {
        let v = random_subspace_containing_one(kc, ell, &mut rng);
        if let Some(fb) = build_symmetrised_factor_base_from_basis(kc, v) {
            break fb;
        }
    };
    let fb: &'static SymmetrisedFactorBase = Box::leak(Box::new(fb));
    let targets = subgroup_targets(kc, targets, 0x7A76_6574 ^ u64::from(n));
    Cell {
        kc,
        st,
        fb,
        targets,
    }
}

fn fp_stats(fp: Fp, s: &SolveStats) -> Fp {
    fp.usize(s.reductions)
        .usize(s.infeasible_branches)
        .usize(s.propagations)
        .usize(s.splits)
        .bool(s.exhausted)
        .u64(u64::from(s.max_degree_built))
        .usize(s.oversize)
        .usize(s.eliminated)
}

fn fp_enumeration(mut fp: Fp, e: &ChainEnumeration) -> Fp {
    fp = fp.usize(e.decompositions.len());
    for d in &e.decompositions {
        fp = fp.bool(d.via_t);
        for &i in &d.indices {
            fp = fp.usize(i);
        }
    }
    fp = fp
        .usize(e.roots)
        .bool(e.complete)
        .usize(e.n_vars)
        .usize(e.n_equations)
        .u64(u64::from(e.degree))
        .u64(e.meet.root_finds)
        .u64(e.meet.identically_zero)
        .u64(e.meet.roots);
    fp_stats(fp, &e.stats)
}

fn fp_outcome(fp: Fp, o: &OracleOutcome) -> Fp {
    let mut fp = match &o.relation {
        None => fp.u64(u64::MAX),
        Some(r) => {
            let mut fp = fp.usize(r.len());
            for &i in r {
                fp = fp.usize(i);
            }
            fp
        }
    };
    fp = fp
        .bool(o.used_t)
        .bool(o.complete)
        .usize(o.n_vars)
        .usize(o.n_equations)
        .u64(u64::from(o.degree))
        .u64(o.effort)
        .u64(u64::from(o.built_degree))
        .usize(o.oversize);
    fp
}

fn all_on(c: Cell, shape: ChainShape, solver: ChainSolver) -> Box<dyn Workload> {
    let oracle = SymChainOracle::new(c.kc, c.fb, c.st).expect("oracle");
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for t in &c.targets {
            let e = oracle
                .decompose_all(t, 5, shape, solver)
                .expect("system builds");
            fp = fp_enumeration(fp, &e);
        }
        fp.finish()
    }))
}

fn dispatch_first_on(c: Cell) -> Box<dyn Workload> {
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for t in &c.targets {
            let o = symmetrised_decompose_dispatch(
                c.kc,
                c.fb,
                c.st,
                t,
                5,
                ChainShape::Auto,
                SolverEngine::default(),
                NODES,
            )
            .expect("dispatch decides");
            fp = fp_outcome(fp, &o);
        }
        fp.finish()
    }))
}

/// The production generic chain at `m = 5` on `F_x` over the cell's `V`.
fn xchain_first_on(c: Cell) -> Box<dyn Workload> {
    let fbx = plain_subspace_factor_base(c.kc, &c.fb.v_basis).expect("F_x");
    let index_of: HashMap<_, _> = fbx
        .points
        .iter()
        .enumerate()
        .map(|(i, p)| (point_key(p), i))
        .collect();
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for t in &c.targets {
            let (rel, stats) = groebner_decompose(
                c.kc,
                &fbx,
                &index_of,
                c.st,
                t,
                5,
                SolverEngine::default(),
                NODES,
            );
            fp = match &rel {
                None => fp.u64(u64::MAX),
                Some(r) => {
                    let mut fp = fp.usize(r.len());
                    for &i in r {
                        fp = fp.usize(i);
                    }
                    fp
                }
            };
            fp = fp_stats(fp, &stats);
        }
        fp.finish()
    }))
}

// K_1/F_{2^9}, ℓ = 3: every arm finishes.
fn meet_all_n9() -> Box<dyn Workload> {
    all_on(cell(1, 9, 3, 6), ChainShape::S4Pair, ChainSolver::Meet)
}
fn f4pair_all_n9() -> Box<dyn Workload> {
    all_on(cell(1, 9, 3, 6), ChainShape::S4Pair, f4())
}
fn s3links_all_n9() -> Box<dyn Workload> {
    all_on(cell(1, 9, 3, 6), ChainShape::S3Links, f4())
}
fn plainu_all_n9() -> Box<dyn Workload> {
    all_on(cell(1, 9, 3, 6), ChainShape::PlainU, f4())
}
fn meet_first_n9() -> Box<dyn Workload> {
    dispatch_first_on(cell(1, 9, 3, 12))
}
fn xchain_first_n9() -> Box<dyn Workload> {
    xchain_first_on(cell(1, 9, 3, 12))
}

// K_1/F_{2^11}, ℓ = 4.
fn meet_all_n11() -> Box<dyn Workload> {
    all_on(cell(1, 11, 4, 4), ChainShape::S4Pair, ChainSolver::Meet)
}
fn s3links_all_n11() -> Box<dyn Workload> {
    all_on(cell(1, 11, 4, 4), ChainShape::S3Links, f4())
}
fn meet_first_n11() -> Box<dyn Workload> {
    dispatch_first_on(cell(1, 11, 4, 8))
}
fn xchain_first_n11() -> Box<dyn Workload> {
    xchain_first_on(cell(1, 11, 4, 8))
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
        "pdp/spec_sym_m5_meet_all_n9",
        "koblitz_symmetrised_m5 decompose_all, [4,4] pair by root-meet, K_1/2^9 l=3 m=5, 6 targets",
        Tier::Quick,
        meet_all_n9,
    );
    add(
        "pdp/spec_sym_m5_f4pair_all_n9",
        "koblitz_symmetrised_m5 decompose_all, [4,4] pair by F4 (default engine), K_1/2^9 l=3 m=5, 6 targets",
        Tier::Quick,
        f4pair_all_n9,
    );
    add(
        "pdp/spec_sym_m5_s3links_all_n9",
        "koblitz_symmetrised_m5 decompose_all, folded S3 chain by F4 (generic fallback), K_1/2^9 l=3 m=5, 6 targets",
        Tier::Quick,
        s3links_all_n9,
    );
    add(
        "pdp/spec_sym_m5_plainu_all_n9",
        "koblitz_symmetrised_m5 decompose_all, plain-u generic S3 chain by F4 (R and R+T), K_1/2^9 l=3 m=5, 6 targets",
        Tier::Full,
        plainu_all_n9,
    );
    add(
        "pdp/spec_sym_m5_meet_first_n9",
        "symmetrised_decompose_dispatch m=5 Auto (root-meet), K_1/2^9 l=3, 12 targets",
        Tier::Quick,
        meet_first_n9,
    );
    add(
        "pdp/spec_sym_m5_xchain_first_n9",
        "generic x-chain groebner_decompose m=5 on F_x (same V), K_1/2^9 l=3, 12 targets",
        Tier::Quick,
        xchain_first_n9,
    );
    add(
        "pdp/spec_sym_m5_meet_all_n11",
        "koblitz_symmetrised_m5 decompose_all, [4,4] pair by root-meet, K_1/2^11 l=4 m=5, 4 targets",
        Tier::Quick,
        meet_all_n11,
    );
    add(
        "pdp/spec_sym_m5_s3links_all_n11",
        "koblitz_symmetrised_m5 decompose_all, folded S3 chain by F4 (generic fallback), K_1/2^11 l=4 m=5, 4 targets",
        Tier::Full,
        s3links_all_n11,
    );
    add(
        "pdp/spec_sym_m5_meet_first_n11",
        "symmetrised_decompose_dispatch m=5 Auto (root-meet), K_1/2^11 l=4, 8 targets",
        Tier::Quick,
        meet_first_n11,
    );
    add(
        "pdp/spec_sym_m5_xchain_first_n11",
        "generic x-chain groebner_decompose m=5 on F_x (same V), K_1/2^11 l=4, 8 targets",
        Tier::Full,
        xchain_first_n11,
    );
}
