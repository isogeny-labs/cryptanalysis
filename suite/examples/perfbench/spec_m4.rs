//! `pdp/spec_m4_*`: the `m = 4` linearised triples oracle
//! (`semaev_decomp::linearised_m4`) against the generic chained-`S₃`
//! path on the same instance.
//!
//! The `linearised` and `generic` kernels fingerprint the returned
//! decompositions plus their own route's counters, so their fingerprints
//! differ from each other.  The `dispatch` kernel runs
//! [`decompose_all_m4`] with the route taken from `PERFBENCH_M4_PATH`
//! (`auto`, default; `linearised`; `generic`) and fingerprints the
//! decompositions alone, which both routes return identically: two
//! wrappers of one binary that differ only in that variable give
//! `perfindex.py compare` a paired specialised-versus-generic wall time.
//! The generic kernel is `Full` tier: on the shared instance it takes
//! about 0.4 s, above the `Quick` band, where the linearised one takes
//! about 6 ms.

use crate::harness::{Closure, Fp, Kernel, Tier, Workload};
use cryptanalysis_suite::cryptanalysis::koblitz_index_calculus::find_irreducible_sparse;
use cryptanalysis_suite::cryptanalysis::semaev_decomp::linearised_m4::{
    decompose_all_generic, decompose_all_m4, M4Path, TripleOracle,
};
use cryptanalysis_suite::cryptanalysis::semaev_decomp::Gf2;
use rand::{rngs::StdRng, Rng, SeedableRng};

/// A seeded instance: field, independent basis, curve constant, targets.
/// Half the targets are planted (pushed through a rational chain from
/// four random subspace abscissae by `TripleOracle::chain_target`), half
/// random.
struct Instance {
    gf: Gf2,
    basis: Vec<u64>,
    b: u64,
    targets: Vec<u64>,
}

fn instance(n: u32, l: u32, targets: usize, seed: u64) -> Instance {
    let gf = Gf2::new(&find_irreducible_sparse(n).expect("irreducible exists"));
    let mask = (1u64 << n) - 1;
    let mut rng = StdRng::seed_from_u64(seed);
    let basis: Vec<u64> = (0..l).map(|i| 1u64 << ((3 * i) % n)).collect();
    let b = (rng.gen::<u64>() & mask) | 1;
    let oracle = TripleOracle::new(&basis, b, &gf);
    let mut ts = Vec::with_capacity(targets);
    while ts.len() < targets / 2 {
        let xs: [u64; 4] =
            std::array::from_fn(|_| oracle.span[rng.gen_range(0..oracle.span.len())]);
        if let Some(xr) = oracle.chain_target(xs, &gf) {
            ts.push(xr);
        }
    }
    while ts.len() < targets {
        ts.push(rng.gen::<u64>() & mask);
    }
    Instance {
        gf,
        basis,
        b,
        targets: ts,
    }
}

fn fp_decomps(mut fp: Fp, ds: &[[u64; 4]]) -> Fp {
    fp = fp.usize(ds.len());
    for d in ds {
        fp = fp.words(d);
    }
    fp
}

fn linearised(n: u32, l: u32, targets: usize, seed: u64) -> Box<dyn Workload> {
    let inst = instance(n, l, targets, seed);
    let oracle = TripleOracle::new(&inst.basis, inst.b, &inst.gf);
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for &xr in &inst.targets {
            let (ds, c) = oracle.decompose_all(xr, &inst.gf);
            fp = fp_decomps(fp, &ds)
                .u64(c.triples)
                .u64(c.gcd_hits)
                .u64(c.low_degree)
                .u64(c.candidates)
                .u64(c.chain_rejected);
        }
        fp.finish()
    }))
}

fn generic(n: u32, l: u32, targets: usize, seed: u64) -> Box<dyn Workload> {
    let inst = instance(n, l, targets, seed);
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for &xr in &inst.targets {
            match decompose_all_generic(&inst.basis, xr, inst.b, &inst.gf, usize::MAX) {
                None => fp = fp.u64(u64::MAX),
                Some((ds, st)) => {
                    fp = fp_decomps(fp, &ds)
                        .usize(st.reductions)
                        .usize(st.splits)
                        .usize(st.propagations)
                        .usize(st.infeasible_branches)
                }
            }
        }
        fp.finish()
    }))
}

fn dispatch(n: u32, l: u32, targets: usize, seed: u64) -> Box<dyn Workload> {
    let inst = instance(n, l, targets, seed);
    let path = match std::env::var("PERFBENCH_M4_PATH").as_deref() {
        Ok("generic") => M4Path::Generic,
        Ok("linearised") => M4Path::Linearised,
        _ => M4Path::Auto,
    };
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for &xr in &inst.targets {
            let o = decompose_all_m4(&inst.basis, xr, inst.b, &inst.gf, path, usize::MAX);
            fp = match o.decompositions {
                None => fp.u64(u64::MAX),
                Some(ds) => fp_decomps(fp, &ds),
            };
        }
        fp.finish()
    }))
}

const SMALL: (u32, u32, usize, u64) = (10, 4, 8, 0x4D34_5350_0000_0009);
const LARGE: (u32, u32, usize, u64) = (20, 6, 2, 0x4D34_5350_0000_0014);

fn lin_small() -> Box<dyn Workload> {
    let (n, l, t, s) = SMALL;
    linearised(n, l, t, s)
}
fn gen_small() -> Box<dyn Workload> {
    let (n, l, t, s) = SMALL;
    generic(n, l, t, s)
}
fn dispatch_small() -> Box<dyn Workload> {
    let (n, l, t, s) = SMALL;
    dispatch(n, l, t, s)
}
fn lin_large() -> Box<dyn Workload> {
    let (n, l, t, s) = LARGE;
    linearised(n, l, t, s)
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
        "pdp/spec_m4_linearised_n10_l4",
        "linearised_m4::TripleOracle::decompose_all (triples + octic gcd), n=10 l=4 m=4, 4 planted + 4 random",
        Tier::Quick,
        lin_small,
    );
    add(
        "pdp/spec_m4_generic_n10_l4",
        "linearised_m4::decompose_all_generic (chained S3, all roots), same instance as spec_m4_linearised_n10_l4",
        Tier::Full,
        gen_small,
    );
    add(
        "pdp/spec_m4_dispatch_n10_l4",
        "linearised_m4::decompose_all_m4, route from PERFBENCH_M4_PATH, same instance; fingerprint = decompositions only",
        Tier::Quick,
        dispatch_small,
    );
    add(
        "pdp/spec_m4_linearised_n20_l6",
        "linearised_m4::TripleOracle::decompose_all, n=20 l=6 m=4 (generic chain: 64 unknowns), 1 planted + 1 random",
        Tier::Quick,
        lin_large,
    );
}
