//! Specialised affine-factor-base kernels (`pdp/spec_affine_*`,
//! `sat/spec_affine_*`): the oracles of
//! `cryptanalysis_suite::cryptanalysis::affine_factor_base` against the
//! generic paths on the **same** base and targets.
//!
//! Every kernel returns the full decomposition set per target (sorted
//! index tuples) and the route's native counters, so a specialised and a
//! generic kernel of one instance compute the same sets (pinned by the
//! module's differential tests) and differ only in counters and time.
//!
//! Instances (built in the untimed setup, seeded):
//!
//! - `k15`: `K_a / GF(2^15)`, the first invariant affine base `V + c` of
//!   dimension 8 over a divisor of `x^15 − 1`, `m = 2`;
//! - `k7`: `K_1 / GF(2^7)`, the invariant affine base of dimension 3,
//!   `m = 3`, small enough for the chained descents to finish;
//! - `g18`: a seeded random curve over `GF(2^18)` with a random 6-dimensional
//!   coset and all points over it, `m = 3`.
//!
//! Targets: planted sums of `m` base points and random curve or subgroup
//! points, half and half.

use crate::harness::{Closure, Fp, Kernel, Tier, Workload};
use cryptanalysis_suite::binary_ecc::{BinaryCurve, BinaryPoint, F2mElement};
use cryptanalysis_suite::cryptanalysis::affine_factor_base::{
    affine_koblitz_decomposer, affine_points, build_affine_frobenius_factor_base,
    frobenius_invariant_shifts, AffineDecomposer, AffineDecompositions, AffineRoute,
    AffineSubspace,
};
use cryptanalysis_suite::cryptanalysis::koblitz_groebner::SolverEngine;
use cryptanalysis_suite::cryptanalysis::koblitz_index_calculus::{
    find_irreducible_sparse, invariant_factors, points_with_x, subspace_basis_for_factors,
    KoblitzCurve,
};
use num_bigint::BigUint;
use num_traits::{One, Zero};
use rand::{rngs::StdRng, Rng, SeedableRng};

fn fp_result(mut fp: Fp, r: &AffineDecompositions) -> Fp {
    fp = fp.usize(r.decompositions.len());
    for d in &r.decompositions {
        fp = fp.usize(d.len());
        for &i in d {
            fp = fp.usize(i);
        }
    }
    let s = &r.stats;
    fp.u64(s.quadratics)
        .u64(s.pairs)
        .u64(s.candidates)
        .u64(s.additions)
        .u64(s.reductions)
        .u64(s.conflicts)
        .bool(s.complete)
}

struct Instance {
    dec: AffineDecomposer,
    targets: Vec<BinaryPoint>,
    m: usize,
    /// Passes over the target list per run (sizes the cheap kernels into
    /// the Quick window without changing what one pass computes).
    reps: usize,
}

fn planted_and_random(
    curve: &BinaryCurve,
    points: &[BinaryPoint],
    m: usize,
    count: usize,
    rng: &mut StdRng,
    random: &mut dyn FnMut(&mut StdRng) -> BinaryPoint,
) -> Vec<BinaryPoint> {
    let mut out = Vec::new();
    for _ in 0..count {
        let mut s = BinaryPoint::Infinity;
        for _ in 0..m {
            let p = &points[rng.gen_range(0..points.len())];
            s = cryptanalysis_suite::binary_ecc::curve::point_add(curve, &s, p);
        }
        out.push(s);
        out.push(random(rng));
    }
    out
}

/// The first invariant affine base of dimension `l` on `K_a / GF(2^n)`
/// (single factors first, then pairs of factors).
fn koblitz_instance(a: u8, n: u32, l: usize, m: usize, count: usize, seed: u64) -> Instance {
    let kc = KoblitzCurve::new(a, n).expect("curve");
    let f = invariant_factors(&kc).len();
    let mut divisors: Vec<Vec<usize>> = (0..f).map(|i| vec![i]).collect();
    divisors.extend((0..f).flat_map(|i| (i + 1..f).map(move |j| vec![i, j])));
    let afb = divisors
        .iter()
        .filter_map(|d| subspace_basis_for_factors(&kc, d))
        .filter(|(basis, _)| basis.len() == l)
        .find_map(|(basis, _)| {
            frobenius_invariant_shifts(&kc, &basis)
                .iter()
                .find_map(|c| build_affine_frobenius_factor_base(&kc, &basis, c))
        })
        .expect("an invariant affine base");
    let dec = affine_koblitz_decomposer(&kc, &afb).expect("decomposer");
    let mut rng = StdRng::seed_from_u64(seed);
    let order = kc.subgroup_order.clone();
    let targets = planted_and_random(&kc.curve, &afb.fb.points, m, count, &mut rng, &mut |r| {
        let k = BigUint::from(r.gen::<u64>()) % &order;
        kc.mul(kc.generator(), &k)
    });
    Instance {
        dec,
        targets,
        m,
        reps: 1,
    }
}

fn generic_instance(n: u32, l: u32, m: usize, count: usize, seed: u64) -> Instance {
    let mut rng = StdRng::seed_from_u64(seed);
    let mask = (1u64 << n) - 1;
    let curve = BinaryCurve {
        m: n,
        irreducible: find_irreducible_sparse(n).expect("irreducible"),
        a: F2mElement::from_biguint(&BigUint::from(1u32), n),
        b: F2mElement::from_biguint(&BigUint::from((rng.gen::<u64>() & mask).max(1)), n),
        generator: BinaryPoint::Infinity,
        order: BigUint::zero(),
        cofactor: BigUint::one(),
    };
    let coset = loop {
        let basis: Vec<u64> = (0..l).map(|_| rng.gen::<u64>() & mask).collect();
        if let Some(c) = AffineSubspace::new(&basis, rng.gen::<u64>() & mask) {
            if !c.is_linear() {
                break c;
            }
        }
    };
    let points = affine_points(&curve, &coset).expect("single-word field");
    let dec = AffineDecomposer::new(&curve, &coset, &points).expect("decomposer");
    let c2 = curve.clone();
    let targets = planted_and_random(&curve, &points, m, count, &mut rng, &mut |r| loop {
        let x = F2mElement::from_biguint(&BigUint::from(r.gen::<u64>() & mask), n);
        if let Some(p) = points_with_x(&c2, &x).into_iter().next() {
            return p;
        }
    });
    Instance {
        dec,
        targets,
        m,
        reps: 1,
    }
}

fn run(inst: Instance, route: AffineRoute) -> Box<dyn Workload> {
    Box::new(Closure(move || {
        let mut fp = Fp::new().usize(inst.reps);
        for _ in 0..inst.reps {
            for t in &inst.targets {
                let r = inst.dec.decompositions(t, inst.m, route);
                fp = fp_result(fp, &r);
            }
        }
        fp.finish()
    }))
}

const ALG: AffineRoute = AffineRoute::Algebraic {
    engine: SolverEngine::MatrixF4 { max_degree: 3 },
    node_budget: usize::MAX,
};
const HULL: AffineRoute = AffineRoute::GenericAlgebraic {
    engine: SolverEngine::MatrixF4 { max_degree: 3 },
    node_budget: usize::MAX,
};

/// `count` planted + `count` random targets, the list passed `reps` times.
fn k15(count: usize, reps: usize) -> Instance {
    Instance {
        reps,
        ..koblitz_instance(1, 15, 8, 2, count, 0xAFF1_0015)
    }
}
fn k7(reps: usize) -> Instance {
    Instance {
        reps,
        ..koblitz_instance(1, 7, 3, 3, 4, 0xAFF1_0007)
    }
}
fn g18() -> Instance {
    generic_instance(18, 6, 3, 8, 0xAFF1_0018)
}

fn s3_m2_k15() -> Box<dyn Workload> {
    run(k15(4, 12), AffineRoute::S3Solve)
}
fn desc_m2_k15() -> Box<dyn Workload> {
    run(k15(4, 1), ALG)
}
fn hull_m2_k15() -> Box<dyn Workload> {
    run(k15(4, 1), HULL)
}
fn enum_m2_k15() -> Box<dyn Workload> {
    run(k15(4, 12), AffineRoute::Enumerate)
}
fn sat_m2_k15() -> Box<dyn Workload> {
    run(
        k15(4, 1),
        AffineRoute::Sat {
            conflict_budget: u64::MAX,
        },
    )
}
fn s4_m3_k7() -> Box<dyn Workload> {
    run(k7(64), AffineRoute::S4PairsAndSolve)
}
fn desc_m3_k7() -> Box<dyn Workload> {
    run(k7(1), ALG)
}
fn hull_m3_k7() -> Box<dyn Workload> {
    run(k7(1), HULL)
}
fn enum_m3_k7() -> Box<dyn Workload> {
    run(k7(64), AffineRoute::Enumerate)
}
fn s4_m3_g18() -> Box<dyn Workload> {
    run(g18(), AffineRoute::S4PairsAndSolve)
}
fn enum_m3_g18() -> Box<dyn Workload> {
    run(g18(), AffineRoute::Enumerate)
}

pub fn register(kernels: &mut Vec<Kernel>) {
    let mut add = |id: &'static str,
                   area: &'static str,
                   desc: &'static str,
                   setup: fn() -> Box<dyn Workload>| {
        kernels.push(Kernel {
            id,
            area,
            desc,
            tier: Tier::Quick,
            setup,
        });
    };
    add(
        "pdp/spec_affine_s3_m2_k15",
        "pdp",
        "affine base K_1/2^15 l=8 m=2: S3Solve (quadratic per coset x1), all decompositions, 4+4 targets x12 passes",
        s3_m2_k15,
    );
    add(
        "pdp/spec_affine_desc_m2_k15",
        "pdp",
        "affine base K_1/2^15 l=8 m=2: affine descent (2l vars, MatrixF4 d3), all roots, 4+4 targets",
        desc_m2_k15,
    );
    add(
        "pdp/spec_affine_hull_m2_k15",
        "pdp",
        "affine base K_1/2^15 l=8 m=2: GENERIC hull descent (2l+2 vars, MatrixF4 d3), all roots, 4+4 targets",
        hull_m2_k15,
    );
    add(
        "pdp/spec_affine_enum_m2_k15",
        "pdp",
        "affine base K_1/2^15 l=8 m=2: reference enumeration over the points, 4+4 targets x12 passes",
        enum_m2_k15,
    );
    add(
        "sat/spec_affine_sat_m2_k15",
        "sat",
        "affine base K_1/2^15 l=8 m=2: affine SAT (native XOR, shifted trace row, domain trie), all models, 4+4 targets",
        sat_m2_k15,
    );
    add(
        "pdp/spec_affine_s4_m3_k7",
        "pdp",
        "affine base K_1/2^7 l=3 m=3: S4 pairs-and-solve over the coset, all decompositions, 4+4 targets x64 passes",
        s4_m3_k7,
    );
    add(
        "pdp/spec_affine_desc_m3_k7",
        "pdp",
        "affine base K_1/2^7 l=3 m=3: affine chained descent (3l+n vars), all roots, 4+4 targets",
        desc_m3_k7,
    );
    add(
        "pdp/spec_affine_hull_m3_k7",
        "pdp",
        "affine base K_1/2^7 l=3 m=3: GENERIC hull chained descent (3l+3+n vars), all roots, 4+4 targets",
        hull_m3_k7,
    );
    add(
        "pdp/spec_affine_enum_m3_k7",
        "pdp",
        "affine base K_1/2^7 l=3 m=3: reference enumeration, 4+4 targets x64 passes",
        enum_m3_k7,
    );
    add(
        "pdp/spec_affine_s4_m3_g18",
        "pdp",
        "random curve 2^18, coset l=6 m=3: S4 pairs-and-solve, all decompositions, 8+8 targets",
        s4_m3_g18,
    );
    add(
        "pdp/spec_affine_enum_m3_g18",
        "pdp",
        "random curve 2^18, coset l=6 m=3: reference enumeration, 8+8 targets",
        enum_m3_g18,
    );
}
