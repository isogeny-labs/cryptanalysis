//! Area `bool_gb`, kernels `spec_*blocks*`: crossbred and XL with `(D, k)`
//! read off the summand blocks of a Semaev chain
//! (`cryptanalysis::crossbred_blocks`), each beside the generic split it
//! replaces (`D = deg`, `k = n_vars / 2`) on the same systems where that
//! one finishes.
//!
//! Systems are the native-order chains `crossbred_decompose` hands to
//! crossbred (`build_decomposition_system`, summands then intermediates),
//! built in the untimed setup.  The fingerprint covers every root in the
//! order returned and the solver counters.  All work runs on the calling
//! thread.

use crate::harness::{Closure, Fp, Kernel, Tier, Workload};
use cryptanalysis_suite::binary_ecc::BinaryPoint;
use cryptanalysis_suite::cryptanalysis::crossbred::{
    extract_crossbred, solve_crossbred, CrossbredParams, SearchOptions, SearchStats,
};
use cryptanalysis_suite::cryptanalysis::crossbred_blocks::{
    solve_block_xl, solve_crossbred_blocks, BlockXlOptions, CrossbredBlockOptions, Preprocess,
    SummandBlocks,
};
use cryptanalysis_suite::cryptanalysis::koblitz_groebner::{
    build_decomposition_system, DecompositionSystem, FieldStructure,
};
use cryptanalysis_suite::cryptanalysis::koblitz_index_calculus::{
    build_frobenius_factor_base, crossbred_decompose, KoblitzCurve,
};
use num_bigint::BigUint;
use rand::{rngs::StdRng, Rng, SeedableRng};

/// `planted` planted and `random` random targets on `K_a / F_2^n`
/// (factor-base divisor `fi`, `m` summands), in native chain order.
fn systems(
    a: u8,
    n: u32,
    fi: usize,
    m: usize,
    planted: usize,
    random: u32,
    seed: u64,
) -> Vec<DecompositionSystem> {
    let kc = KoblitzCurve::new(a, n).expect("Koblitz curve exists");
    let fb = build_frobenius_factor_base(&kc, fi).expect("factor base exists");
    let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
    let mut rng = StdRng::seed_from_u64(seed);
    let mut targets = Vec::new();
    let mut draws = 0usize;
    while targets.len() < planted {
        // Bounded: some factor bases (K_0/2^7 divisor 0 is one point) have
        // no affine m-sum, and an unbounded retry would hang the harness.
        draws += 1;
        assert!(draws <= 100_000, "no affine {m}-sum of factor-base points");
        let t = (0..m).fold(BinaryPoint::Infinity, |acc, _| {
            kc.add(&acc, &fb.points[rng.gen_range(0..fb.points.len())])
        });
        if matches!(t, BinaryPoint::Affine { .. }) {
            targets.push(t);
        }
    }
    for i in 0..random {
        let s = BigUint::from(1u64 + (i as u64).wrapping_mul(2_654_435_761) % 1_000_003);
        targets.push(kc.mul(kc.generator(), &s));
    }
    targets
        .iter()
        .filter_map(|t| match t {
            BinaryPoint::Affine { x, .. } => Some(x.clone()),
            BinaryPoint::Infinity => None,
        })
        .map(|x| {
            build_decomposition_system(&fb.subspace_basis, &x, &kc.curve.b, m, &st)
                .expect("system fits in 64 unknowns")
        })
        .collect()
}

fn fp_search(fp: Fp, st: &SearchStats) -> Fp {
    fp.u64(st.points)
        .u64(st.survivors)
        .u64(st.linear_solves)
        .u64(st.candidates)
        .u64(st.verified)
        .u64(st.transform_word_ops)
        .u64(st.filter_word_ops)
        .u64(st.solve_row_ops)
        .bool(st.exhausted)
}

/// The generic split `crossbred_decompose` used: `D` = the system's
/// degree, `k = n_vars / 2` capped at the search's table budget.
fn generic_params(sys: &DecompositionSystem) -> CrossbredParams {
    let degree = sys
        .equations
        .iter()
        .flat_map(|p| p.terms.iter())
        .map(|t| t.mask.count_ones())
        .max()
        .unwrap_or(2)
        .max(2);
    let budget = SearchOptions::default().max_enumerated_bits as usize;
    CrossbredParams {
        macaulay_degree: degree,
        enumerated: (sys.n_vars / 2).clamp(1, sys.n_vars.saturating_sub(1).min(budget)),
        target_degree: 1,
        ..CrossbredParams::default()
    }
}

fn generic_kernel(sys: Vec<DecompositionSystem>) -> Box<dyn Workload> {
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for s in &sys {
            let xb = extract_crossbred(&s.equations, s.n_vars, &generic_params(s))
                .expect("generic extraction fits");
            let (roots, st) = solve_crossbred(&s.equations, &xb, &SearchOptions::default());
            let e = xb.stats;
            fp = fp_search(
                fp.words(&roots)
                    .usize(e.macaulay_rows)
                    .usize(e.kernel_dim)
                    .u64(e.word_ops),
                &st,
            );
        }
        fp.finish()
    }))
}

fn xb_kernel(sys: Vec<DecompositionSystem>, preprocess: Preprocess) -> Box<dyn Workload> {
    let opts = CrossbredBlockOptions {
        preprocess,
        ..CrossbredBlockOptions::default()
    };
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for s in &sys {
            let layout = SummandBlocks::of_system(s).expect("chain layout");
            let (roots, st) =
                solve_crossbred_blocks(&s.equations, &layout, &opts).expect("block plan fits");
            fp = fp_search(
                fp.words(&roots)
                    .usize(st.enumerated)
                    .u64(u64::from(st.macaulay_degree))
                    .usize(st.crossbred_polys)
                    .usize(st.extract.macaulay_rows)
                    .u64(st.extract.word_ops)
                    .bool(st.preprocess_fallback),
                &st.search,
            );
        }
        fp.finish()
    }))
}

/// Block-elimination XL over `sys`, swept `reps` times (the per-sweep
/// cost is the kernel time over `reps`; the systems are the same ones the
/// generic and crossbred kernels of the same suffix solve once).
fn xl_kernel(sys: Vec<DecompositionSystem>, reps: usize) -> Box<dyn Workload> {
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for s in sys.iter().cycle().take(sys.len() * reps) {
            let layout = SummandBlocks::of_system(s).expect("chain layout");
            let (roots, st) = solve_block_xl(&s.equations, &layout, &BlockXlOptions::default())
                .expect("block-XL plan fits");
            fp = fp
                .words(&roots)
                .usize(st.enumerated)
                .u64(st.points)
                .u64(st.survivors)
                .u64(st.linear_solves)
                .u64(st.solve_row_ops)
                .u64(st.term_evals)
                .u64(st.candidates)
                .u64(st.verified)
                .bool(st.exhausted);
        }
        fp.finish()
    }))
}

/// The production oracle `crossbred_decompose` with default parameters on
/// `planted` planted and `random` random targets.  The same kernel id
/// measures both paths: by default it takes the block path; with
/// `IC_CROSSBRED_BLOCKS=0` in the environment it takes the generic
/// `k = n_vars / 2` split.  The fingerprint covers only what both paths
/// must agree on — the decomposition returned for every target (the
/// differential tests in `crossbred_blocks` pin that they are equal) —
/// so the two arms compare under `perfindex.py`; each path's own
/// counters are fingerprinted by the `bool_gb/spec_*` kernels above.
fn decompose_kernel(
    a: u8,
    n: u32,
    fi: usize,
    m: usize,
    planted: usize,
    random: u32,
    seed: u64,
) -> Box<dyn Workload> {
    let kc = KoblitzCurve::new(a, n).expect("Koblitz curve exists");
    let fb = build_frobenius_factor_base(&kc, fi).expect("factor base exists");
    let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
    let index = fb.index_map();
    let mut rng = StdRng::seed_from_u64(seed);
    let mut targets = Vec::new();
    let mut draws = 0usize;
    while targets.len() < planted {
        // Bounded: some factor bases (K_0/2^7 divisor 0 is one point) have
        // no affine m-sum, and an unbounded retry would hang the harness.
        draws += 1;
        assert!(draws <= 100_000, "no affine {m}-sum of factor-base points");
        let t = (0..m).fold(BinaryPoint::Infinity, |acc, _| {
            kc.add(&acc, &fb.points[rng.gen_range(0..fb.points.len())])
        });
        if matches!(t, BinaryPoint::Affine { .. }) {
            targets.push(t);
        }
    }
    for i in 0..random {
        let s = BigUint::from(1u64 + (i as u64).wrapping_mul(2_654_435_761) % 1_000_003);
        targets.push(kc.mul(kc.generator(), &s));
    }
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for t in &targets {
            let (found, _) = crossbred_decompose(&kc, &fb, &index, &st, t, m, None);
            fp = match found {
                Some(idxs) => {
                    let w: Vec<u64> = idxs.iter().map(|&i| i as u64).collect();
                    fp.bool(true).words(&w)
                }
                None => fp.bool(false),
            };
        }
        fp.finish()
    }))
}

// K_0 / F_2^15, divisor 1 (ℓ = 4, n = 15): m = 3 (27 vars), m = 4 (46 vars).
fn decompose_m3_n15() -> Box<dyn Workload> {
    decompose_kernel(0, 15, 1, 3, 3, 3, 3150)
}
fn m3_n15() -> Vec<DecompositionSystem> {
    systems(0, 15, 1, 3, 1, 1, 315)
}
fn m4_n15() -> Vec<DecompositionSystem> {
    systems(0, 15, 1, 4, 2, 2, 415)
}
// K_1 / F_2^7 (ℓ = 3): m = 4 (26 vars), where the generic split finishes.
fn decompose_m4_n7() -> Box<dyn Workload> {
    decompose_kernel(1, 7, 0, 4, 3, 3, 4070)
}
fn m4_n7() -> Vec<DecompositionSystem> {
    systems(1, 7, 0, 4, 2, 2, 407)
}
// K_1 / F_2^23 (ℓ = 11): m = 2.
fn m2_n23() -> Vec<DecompositionSystem> {
    systems(1, 23, 0, 2, 2, 2, 223)
}

fn generic_m3_n15() -> Box<dyn Workload> {
    generic_kernel(m3_n15())
}
fn xb_direct_m3_n15() -> Box<dyn Workload> {
    xb_kernel(m3_n15(), Preprocess::Direct)
}
fn xb_macaulay_m3_n15() -> Box<dyn Workload> {
    xb_kernel(m3_n15(), Preprocess::Macaulay { max_rows: 20_000 })
}
fn xl_m3_n15() -> Box<dyn Workload> {
    xl_kernel(m3_n15(), 8)
}
fn xl_m4_n15() -> Box<dyn Workload> {
    xl_kernel(m4_n15(), 1)
}
fn generic_m4_n7() -> Box<dyn Workload> {
    generic_kernel(m4_n7())
}
fn xl_m4_n7() -> Box<dyn Workload> {
    xl_kernel(m4_n7(), 8)
}
fn generic_m2_n23() -> Box<dyn Workload> {
    generic_kernel(m2_n23())
}
fn xb_direct_m2_n23() -> Box<dyn Workload> {
    xb_kernel(m2_n23(), Preprocess::Direct)
}
fn xl_m2_n23() -> Box<dyn Workload> {
    xl_kernel(m2_n23(), 1)
}

pub fn register(kernels: &mut Vec<Kernel>) {
    let mut k = |id: &'static str,
                 area: &'static str,
                 desc: &'static str,
                 setup: fn() -> Box<dyn Workload>| {
        kernels.push(Kernel {
            id,
            area,
            desc,
            tier: Tier::Quick,
            setup,
        })
    };
    k(
        "pdp/spec_xb_decompose_m3_n15",
        "pdp",
        "crossbred_decompose, default params (block path; IC_CROSSBRED_BLOCKS=0: generic k=n_vars/2), K_0/2^15 divisor 1, m=3: 3 planted + 3 random targets",
        decompose_m3_n15,
    );
    k(
        "pdp/spec_xb_decompose_m4_n7",
        "pdp",
        "crossbred_decompose, default params (block path; IC_CROSSBRED_BLOCKS=0: generic k=n_vars/2), K_1/2^7, m=4: 3 planted + 3 random targets",
        decompose_m4_n7,
    );
    k(
        "bool_gb/spec_base_xb_generic_m3_n15",
        "bool_gb",
        "generic crossbred split (D=3, k=n_vars/2=13) on K_0/2^15 (divisor 1) m=3 chains (27 vars): 1 planted + 1 random",
        generic_m3_n15,
    );
    k(
        "bool_gb/spec_xb_blocks_m3_n15",
        "bool_gb",
        "crossbred_blocks (D=3, k=12 = summands, U_0 linear, direct) on the same K_0/2^15 m=3 chains",
        xb_direct_m3_n15,
    );
    k(
        "bool_gb/spec_xb_blocks_macaulay_m3_n15",
        "bool_gb",
        "crossbred_blocks with Macaulay extraction at the block (D=3, k=12) on the same K_0/2^15 m=3 chains",
        xb_macaulay_m3_n15,
    );
    k(
        "bool_gb/spec_xl_blocks_m3_n15",
        "bool_gb",
        "block-elimination XL (enumerate X_0,X_1; D=1 on U_0 then X_2) on the same K_0/2^15 m=3 chains, 8 sweeps",
        xl_m3_n15,
    );
    k(
        "bool_gb/spec_base_xb_generic_m4_n7",
        "bool_gb",
        "generic crossbred split (D=3, k=n_vars/2=13) on K_1/2^7 m=4 chains (26 vars): 2 planted + 2 random",
        generic_m4_n7,
    );
    k(
        "bool_gb/spec_xl_blocks_m4_n7",
        "bool_gb",
        "block-elimination XL (k=9 over 3 stages) on the same K_1/2^7 m=4 chains, 8 sweeps",
        xl_m4_n7,
    );
    k(
        "bool_gb/spec_xl_blocks_m4_n15",
        "bool_gb",
        "block-elimination XL (k=12 over 3 stages) on K_0/2^15 (divisor 1) m=4 chains (46 vars; no generic baseline: k=22 at D=3 does not finish): 2 planted + 2 random",
        xl_m4_n15,
    );
    k(
        "bool_gb/spec_base_xb_generic_m2_n23",
        "bool_gb",
        "generic crossbred split (D=2, k=11) on K_1/2^23 m=2 systems (22 vars): 2 planted + 2 random",
        generic_m2_n23,
    );
    k(
        "bool_gb/spec_xb_blocks_m2_n23",
        "bool_gb",
        "crossbred_blocks (D=2, k=11 = X_0, direct) on the same K_1/2^23 m=2 systems; same k as the generic split, so a constant-factor gain only, not an algorithmic one",
        xb_direct_m2_n23,
    );
    k(
        "bool_gb/spec_xl_blocks_m2_n23",
        "bool_gb",
        "block-elimination XL (enumerate X_0, D=1 on X_1) on the same K_1/2^23 m=2 systems",
        xl_m2_n23,
    );
}
