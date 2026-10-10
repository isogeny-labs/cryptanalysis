//! Kernels for the symbolic Weil descent at four or more summands and with
//! a 128-bit monomial mask
//! (`cryptanalysis::pq_descent_symbolic_wide`).
//!
//! The `spec_descend_*` kernels run the specialised [`Engine::Tensor`]
//! path.  With `PERFBENCH_SPEC_GENERIC=1` in the environment, the same
//! kernel ids run the generic path on the same inputs instead.  At four or
//! more summands, and for the wide mask, that is [`Engine::Naive`].  At
//! three summands it is the existing 64-bit fast path,
//! `pq_descent_symbolic::descend`.  Both return the same descent monomial
//! for monomial, so the fingerprints agree, and `perfindex.py compare`
//! can pair a binary run with and without the variable.
//! `spec_descend_s4_n23_np6` uses the inputs of `pdp/descend_s4_n23_np6`.
//! `spec_descend_wide_s3_n47_np40` measures the 128-bit mask itself: at
//! two summands both engines expand the same closed form of `S_3`, so its
//! generic run is the same code, and nothing in the repository descended
//! past 64 variables before this module.
//! The oracle kernel has no generic twin: before this module,
//! `descent-algebraic` refused `m = 4`.

use crate::harness::{Closure, Fp, Kernel, Tier, Workload};
use cryptanalysis_suite::cryptanalysis::ic_boundary::{
    random_binary_instance, BinaryGroup, CountedGroup, GroupOps, OracleCounters,
};
use cryptanalysis_suite::cryptanalysis::ic_framework::plugins::{
    BinarySubspaceBase, DescentAlgebraicOracle,
};
use cryptanalysis_suite::cryptanalysis::ic_framework::solvers::solver_by_name;
use cryptanalysis_suite::cryptanalysis::ic_framework::stages::{
    DecompositionOracle, FactorBaseBuilder, InstanceCtx, Params,
};
use cryptanalysis_suite::cryptanalysis::koblitz_index_calculus::find_irreducible_sparse;
use cryptanalysis_suite::cryptanalysis::pq_descent_symbolic::descend;
use cryptanalysis_suite::cryptanalysis::pq_descent_symbolic_wide::{
    descend_narrow_with, descend_wide_with, Engine,
};
use cryptanalysis_suite::cryptanalysis::semaev_decomp::Gf2;
use rand::{rngs::StdRng, Rng, SeedableRng};

/// The inputs `pdp::descend_on` draws, so the kernels here can share them.
fn inputs(n: u32, n_prime: u32, summands: u32, targets: usize) -> (Gf2, u64, Vec<u64>, Vec<u64>) {
    let irr = find_irreducible_sparse(n).expect("irreducible exists");
    let gf = Gf2::new(&irr);
    let mask = (1u64 << n) - 1;
    let mut rng = StdRng::seed_from_u64(0x4445_5343 ^ u64::from(n) << 8 ^ u64::from(summands));
    let v_basis: Vec<u64> = (0..n_prime).map(|_| rng.gen::<u64>() & mask).collect();
    let b = rng.gen::<u64>() & mask | 1;
    let xs: Vec<u64> = (0..targets).map(|_| rng.gen::<u64>() & mask).collect();
    (gf, b, v_basis, xs)
}

/// Whether this run measures the generic path (see the module docs).
fn generic() -> bool {
    std::env::var("PERFBENCH_SPEC_GENERIC").is_ok_and(|v| v == "1")
}

fn descend_narrow_on(n: u32, n_prime: u32, summands: u32, targets: usize) -> Box<dyn Workload> {
    let (gf, b, v_basis, xs) = inputs(n, n_prime, summands, targets);
    let generic = generic();
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for &x_r in &xs {
            let sys = match (generic, summands) {
                (true, 2 | 3) => descend(&gf, b, x_r, &v_basis, summands),
                (true, _) => descend_narrow_with(Engine::Naive, &gf, b, x_r, &v_basis, summands),
                (false, _) => descend_narrow_with(Engine::Tensor, &gf, b, x_r, &v_basis, summands),
            }
            .expect("inside the caps");
            fp = fp.usize(sys.n_vars).usize(sys.field_monomials);
            fp = fp.usize(sys.equations.len());
            for e in &sys.equations {
                fp = fp.usize(e.n_vars).usize(e.terms.len());
                for t in &e.terms {
                    fp = fp.u64(t.mask);
                }
            }
        }
        fp.finish()
    }))
}

fn descend_wide_on(n: u32, n_prime: u32, summands: u32, targets: usize) -> Box<dyn Workload> {
    let (gf, b, v_basis, xs) = inputs(n, n_prime, summands, targets);
    let engine = if generic() {
        Engine::Naive
    } else {
        Engine::Tensor
    };
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for &x_r in &xs {
            let sys = descend_wide_with(engine, &gf, b, x_r, &v_basis, summands)
                .expect("inside the caps");
            fp = fp.usize(sys.n_vars).usize(sys.field_monomials);
            for e in &sys.equations {
                fp = fp.usize(e.terms.len());
                for &t in &e.terms {
                    fp = fp.u128(t);
                }
            }
        }
        fp.finish()
    }))
}

fn s5_n23_np4() -> Box<dyn Workload> {
    descend_narrow_on(23, 4, 4, 2)
}

fn s6_n23_np3() -> Box<dyn Workload> {
    descend_narrow_on(23, 3, 5, 1)
}

fn s4_n23_np6() -> Box<dyn Workload> {
    descend_narrow_on(23, 6, 3, 2)
}

fn wide_s3_n47_np40() -> Box<dyn Workload> {
    descend_wide_on(47, 40, 2, 16)
}

/// The `descent-algebraic` oracle at four summands with exhaustive search:
/// descent, solve and lift for every target, as a relation phase runs it.
fn oracle_m4_n11_d3() -> Box<dyn Workload> {
    let inst = random_binary_instance(11, 3, 8).expect("a curve at n = 11");
    Box::new(Closure(move || {
        let group = BinaryGroup(&inst.fast);
        let mut ops = GroupOps::default();
        let ctx = InstanceCtx {
            group: &group,
            generator: inst.generator,
            target: inst.generator,
            r: inst.r,
            cofactor: inst.cofactor,
            group_order: inst.group_order,
            name: inst.name.clone(),
            field_degree: Some(inst.n),
        };
        let base = BinarySubspaceBase { instance: &inst };
        let mut params = Params::default();
        params.set("dimension", "3");
        let fb = base.build(&ctx, &params, &mut ops).expect("a base");
        let mut oracle = DescentAlgebraicOracle::new(
            4,
            &inst,
            solver_by_name("exhaustive").expect("exhaustive search"),
            Params::default(),
            None,
        );
        oracle
            .prepare(&ctx, &fb, &Params::default(), &mut ops)
            .expect("m = 4 is accepted");
        let mut ctr = OracleCounters::default();
        let mut fp = Fp::new();
        for k in 1..=48u64 {
            let point = group.mul(&mut ops, inst.generator, k);
            match oracle.decompose(&ctx, &fb, &mut ops, &mut ctr, point) {
                Some(idx) => {
                    fp = fp.usize(idx.len());
                    for i in idx {
                        fp = fp.usize(i);
                    }
                }
                None => fp = fp.u64(u64::MAX),
            }
        }
        fp.u64(ctr.lift_failures)
            .u64(ctr.unliftable_systems)
            .u64(oracle.unliftable)
            .u64(ops.adds)
            .u64(ops.doubles)
            .finish()
    }))
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
        "pdp/spec_descend_s5_n23_np4",
        "pq_descent_symbolic_wide S5 (4 summands), tensor engine (naive if generic), n=23 n'=4, 2 targets",
        Tier::Quick,
        s5_n23_np4,
    );
    add(
        "pdp/spec_descend_s6_n23_np3",
        "pq_descent_symbolic_wide S6 (5 summands), tensor engine (naive if generic), n=23 n'=3, 1 target",
        Tier::Quick,
        s6_n23_np3,
    );
    add(
        "pdp/spec_descend_s4_n23_np6",
        "S4 (3 summands), tensor engine (fast path if generic), inputs of pdp/descend_s4_n23_np6",
        Tier::Quick,
        s4_n23_np6,
    );
    add(
        "pdp/spec_descend_wide_s3_n47_np40",
        "S3 with a 128-bit mask, n=47 n'=40 (80 variables), 16 targets (no generic twin)",
        Tier::Quick,
        wide_s3_n47_np40,
    );
    add(
        "pdp/spec_oracle_m4_n11_d3",
        "descent-algebraic oracle m=4 (S5) + exhaustive, n=11 subspace dim 3, 48 targets",
        Tier::Quick,
        oracle_m4_n11_d3,
    );
}
