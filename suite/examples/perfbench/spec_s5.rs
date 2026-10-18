//! Area `pdp`, specialised `m = 4` descent: the hardcoded-`S₅` template of
//! `cryptanalysis::s5_weil_template` against the generic chain of `S₃`
//! links on the same instances.
//!
//! Instances are seeded: a Koblitz curve over `F_{2^n}`, a factor base over
//! a subspace `V` (a random non-invariant `V ∋ 1` from
//! `random_subspace_containing_one`, or a Frobenius-invariant one), and
//! `planted` sums of four base points plus `random` multiples of the
//! generator.  Curves, bases, templates and targets are built in the
//! untimed setup (the template memo is filled by the discarded warm-up, as
//! a decomposition run pays it once per base); the timed region is the
//! oracle.
//!
//! `pdp/spec_s5_paired_*` time [`decompose_all_m4`] on one arm chosen by
//! `PDP_SPEC_S5_ARM` (`chained`, `s5` — the default — or `s5sym`; with the
//! variable unset, by the binary's name suffix `-chained` / `-s5sym`), and
//! fingerprint only what every arm must agree on: the sorted set of
//! decompositions per target.  Run two copies of the same binary
//! (`perfbench-chained`, `perfbench-s5`) as baseline and candidate and
//! `perfindex.py compare`/`instr` pairs specialised against generic on
//! identical work, refusing the comparison if the sets differ.  The other
//! kernels fingerprint their arm's counters too.

use crate::harness::{Closure, Fp, Kernel, Tier, Workload};
use cryptanalysis_suite::binary_ecc::BinaryPoint;
use cryptanalysis_suite::cryptanalysis::koblitz_groebner::{
    FieldStructure, SolveStats, SolverEngine,
};
use cryptanalysis_suite::cryptanalysis::koblitz_index_calculus::{
    build_frobenius_factor_base_from_divisor, invariant_factors, FrobeniusFactorBase, KoblitzCurve,
};
use cryptanalysis_suite::cryptanalysis::koblitz_symmetrised::{
    plain_subspace_factor_base, random_subspace_containing_one,
};
use cryptanalysis_suite::cryptanalysis::s5_weil_template::{
    decompose_all_m4, groebner_decompose_m4, M4Descent, M4Outcome, S5Template,
};
use num_bigint::BigUint;
use rand::{rngs::StdRng, Rng, SeedableRng};
use std::collections::HashMap;

struct Instance {
    kc: KoblitzCurve,
    fb: FrobeniusFactorBase,
    index_of: HashMap<(BigUint, BigUint), usize>,
    st: FieldStructure,
    targets: Vec<BinaryPoint>,
}

/// `frobenius`: the first Frobenius-invariant base of dimension `ell`
/// (divisor order, `K_0` before `K_1`); otherwise a random non-invariant
/// `V ∋ 1` from `seed`.
fn instance(
    n: u32,
    ell: usize,
    frobenius: bool,
    planted: usize,
    random: usize,
    seed: u64,
) -> Instance {
    let mut rng = StdRng::seed_from_u64(seed ^ (u64::from(n) << 16) ^ ell as u64);
    let (kc, fb) = if frobenius {
        let mut found = None;
        'outer: for a in 0u8..=1 {
            let Some(kc) = KoblitzCurve::new(a, n) else {
                continue;
            };
            let degs: Vec<usize> = invariant_factors(&kc)
                .iter()
                .map(|f| f.degree().unwrap_or(0))
                .collect();
            let k = degs.len().min(12);
            for mask in 1u32..1 << k {
                let idx: Vec<usize> = (0..k).filter(|&i| mask >> i & 1 == 1).collect();
                if idx.iter().map(|&i| degs[i]).sum::<usize>() != ell {
                    continue;
                }
                if let Some(fb) = build_frobenius_factor_base_from_divisor(&kc, &idx) {
                    if !fb.points.is_empty() {
                        found = Some((kc, fb));
                        break 'outer;
                    }
                }
            }
        }
        found.expect("a Frobenius-invariant base")
    } else {
        let kc = KoblitzCurve::new(0, n)
            .or_else(|| KoblitzCurve::new(1, n))
            .expect("a Koblitz curve");
        let basis = random_subspace_containing_one(&kc, ell, &mut rng);
        let fb = plain_subspace_factor_base(&kc, &basis).expect("independent basis");
        (kc, fb)
    };
    let st = FieldStructure::new(n, &kc.curve.irreducible);
    let index_of = fb.index_map();
    let mut targets = Vec::new();
    while targets.len() < planted {
        let t = (0..4).fold(BinaryPoint::Infinity, |acc, _| {
            kc.add(&acc, &fb.points[rng.gen_range(0..fb.points.len())])
        });
        if matches!(t, BinaryPoint::Affine { .. }) {
            targets.push(t);
        }
    }
    while targets.len() < planted + random {
        let t = kc.mul(
            kc.generator(),
            &BigUint::from(rng.gen_range(1u64..u64::MAX)),
        );
        if matches!(t, BinaryPoint::Affine { .. }) {
            targets.push(t);
        }
    }
    Instance {
        kc,
        fb,
        index_of,
        st,
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

fn fp_set(mut fp: Fp, o: &M4Outcome) -> Fp {
    fp = fp.usize(o.decompositions.len());
    for d in &o.decompositions {
        for &i in d {
            fp = fp.usize(i);
        }
    }
    fp
}

const BUDGET: usize = 1 << 24;

/// The paired kernels' arm: `PDP_SPEC_S5_ARM`, or else the executable's
/// file name (`…-chained`, `…-s5sym`), so two copies of one binary can be
/// handed to `perfindex.py compare`/`instr` (callgrind cannot follow a
/// wrapper script); `s5` otherwise.
fn arm_from_env() -> M4Descent {
    let name = std::env::var("PDP_SPEC_S5_ARM").unwrap_or_else(|_| {
        std::env::args()
            .next()
            .and_then(|a| a.rsplit('-').next().map(str::to_owned))
            .unwrap_or_default()
    });
    match name.as_str() {
        "chained" => M4Descent::Chained,
        "s5sym" => M4Descent::S5Symmetrised,
        _ => M4Descent::S5Template,
    }
}

/// Every decomposition of every target, one arm; counters fingerprinted.
fn all_on(inst: Instance, arm: M4Descent) -> Box<dyn Workload> {
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for t in &inst.targets {
            let o = decompose_all_m4(
                &inst.kc,
                &inst.fb,
                &inst.index_of,
                &inst.st,
                t,
                arm,
                SolverEngine::default(),
                BUDGET,
            )
            .expect("affine target");
            assert_eq!(o.descent, Some(arm), "no fallback on a benchmark cell");
            fp = fp_stats(
                fp_set(fp, &o)
                    .usize(o.roots)
                    .usize(o.spurious)
                    .usize(o.n_vars),
                &o.stats,
            );
        }
        fp.finish()
    }))
}

/// As [`all_on`] with the arm from `PDP_SPEC_S5_ARM`, fingerprinting only
/// the decomposition sets (identical across arms).
fn paired_on(inst: Instance) -> Box<dyn Workload> {
    let arm = arm_from_env();
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for t in &inst.targets {
            let o = decompose_all_m4(
                &inst.kc,
                &inst.fb,
                &inst.index_of,
                &inst.st,
                t,
                arm,
                SolverEngine::default(),
                BUDGET,
            )
            .expect("affine target");
            assert!(!o.stats.exhausted);
            fp = fp_set(fp, &o);
        }
        fp.finish()
    }))
}

/// The first-found oracle on one arm: decomposition (or none) and counters.
fn first_on(inst: Instance, arm: M4Descent) -> Box<dyn Workload> {
    Box::new(Closure(move || {
        let mut fp = Fp::new();
        for t in &inst.targets {
            let (d, s, used) = groebner_decompose_m4(
                &inst.kc,
                &inst.fb,
                &inst.index_of,
                &inst.st,
                t,
                arm,
                SolverEngine::default(),
                BUDGET,
            );
            assert_eq!(used, arm);
            fp = match d {
                None => fp.u64(u64::MAX),
                Some(d) => d.iter().fold(fp.usize(d.len()), |fp, &i| fp.usize(i)),
            };
            fp = fp_stats(fp, &s);
        }
        fp.finish()
    }))
}

// Cells.  n = 13, ℓ = 3: chain 38 unknowns, template 12.
fn n13() -> Instance {
    instance(13, 3, false, 6, 6, 0x5355_0001)
}
// n = 17, ℓ = 3: chain 46 unknowns, template 12.
fn n17() -> Instance {
    instance(17, 3, false, 4, 4, 0x5355_0002)
}
// n = 15, ℓ = 3 over the subfield F_8 (Frobenius-invariant): W dims 3,3,3,3.
fn n15_subfield() -> Instance {
    instance(15, 3, true, 8, 8, 0x5355_0003)
}

// n = 23, ℓ = 3: chain 58 unknowns, template 12.
fn n23() -> Instance {
    instance(23, 3, false, 2, 2, 0x5355_0005)
}
// n = 17, ℓ = 4: chain 50 unknowns, template 16.
fn n17_l4() -> Instance {
    instance(17, 4, false, 2, 2, 0x5355_0006)
}

fn s5_all_m4_n23() -> Box<dyn Workload> {
    all_on(n23(), M4Descent::S5Template)
}
fn chain_all_m4_n23() -> Box<dyn Workload> {
    all_on(n23(), M4Descent::Chained)
}
fn s5_all_m4_n17_l4() -> Box<dyn Workload> {
    all_on(n17_l4(), M4Descent::S5Template)
}
fn chain_all_m4_n17_l4() -> Box<dyn Workload> {
    all_on(n17_l4(), M4Descent::Chained)
}

fn s5_all_m4_n13() -> Box<dyn Workload> {
    all_on(n13(), M4Descent::S5Template)
}
fn chain_all_m4_n13() -> Box<dyn Workload> {
    all_on(n13(), M4Descent::Chained)
}
fn s5_all_m4_n17() -> Box<dyn Workload> {
    all_on(n17(), M4Descent::S5Template)
}
fn chain_all_m4_n17() -> Box<dyn Workload> {
    all_on(n17(), M4Descent::Chained)
}
fn s5sym_all_m4_n15() -> Box<dyn Workload> {
    all_on(n15_subfield(), M4Descent::S5Symmetrised)
}
fn s5_all_m4_n15() -> Box<dyn Workload> {
    all_on(n15_subfield(), M4Descent::S5Template)
}
fn chain_all_m4_n15() -> Box<dyn Workload> {
    all_on(n15_subfield(), M4Descent::Chained)
}
fn s5_first_m4_n17() -> Box<dyn Workload> {
    first_on(n17(), M4Descent::S5Template)
}
fn chain_first_m4_n17() -> Box<dyn Workload> {
    first_on(n17(), M4Descent::Chained)
}
fn paired_m4_n13() -> Box<dyn Workload> {
    paired_on(n13())
}
fn paired_m4_n17() -> Box<dyn Workload> {
    paired_on(n17())
}
fn paired_m4_n23() -> Box<dyn Workload> {
    paired_on(n23())
}
fn paired_m4_n17_l4() -> Box<dyn Workload> {
    paired_on(n17_l4())
}
fn paired_m4_n15() -> Box<dyn Workload> {
    paired_on(n15_subfield())
}

/// Building the `x`-template (evaluation + Möbius) at `n = 23`, `ℓ = 4`:
/// 16 unknowns, no memo.
fn s5_build_x_n23_l4() -> Box<dyn Workload> {
    let inst = instance(23, 4, false, 0, 0, 0x5355_0004);
    Box::new(Closure(move || {
        let t = S5Template::build_x(&inst.fb.subspace_basis, &inst.kc.curve.b, &inst.st)
            .expect("16 unknowns fit");
        let sys = t.instantiate(&inst.kc.curve.b);
        let mut fp = Fp::new().usize(t.support_len()).usize(t.n_vars());
        for e in &sys.equations {
            fp = fp.usize(e.terms.len());
            for m in &e.terms {
                fp = fp.u64(m.mask);
            }
        }
        fp.finish()
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
        "pdp/spec_s5_all_m4_n13",
        "decompose_all_m4 S5 x-template (12 vars), K/2^13 random V l=3, 6 planted + 6 random",
        Tier::Quick,
        s5_all_m4_n13,
    );
    add(
        "pdp/spec_s5_chain_all_m4_n13",
        "decompose_all_m4 generic chain (38 vars), same cell as spec_s5_all_m4_n13",
        Tier::Quick,
        chain_all_m4_n13,
    );
    add(
        "pdp/spec_s5_all_m4_n17",
        "decompose_all_m4 S5 x-template (12 vars), K/2^17 random V l=3, 4 planted + 4 random",
        Tier::Quick,
        s5_all_m4_n17,
    );
    add(
        "pdp/spec_s5_chain_all_m4_n17",
        "decompose_all_m4 generic chain (46 vars), same cell as spec_s5_all_m4_n17",
        Tier::Full,
        chain_all_m4_n17,
    );
    add("pdp/spec_s5sym_all_m4_n15", "decompose_all_m4 symmetrised e1..e4 template (12 vars), K/2^15 subfield V=F_8, 8 planted + 8 random", Tier::Quick, s5sym_all_m4_n15);
    add(
        "pdp/spec_s5_all_m4_n15",
        "decompose_all_m4 S5 x-template (12 vars), same cell as spec_s5sym_all_m4_n15",
        Tier::Full,
        s5_all_m4_n15,
    );
    add(
        "pdp/spec_s5_chain_all_m4_n15",
        "decompose_all_m4 generic chain (42 vars), same cell as spec_s5sym_all_m4_n15",
        Tier::Quick,
        chain_all_m4_n15,
    );
    add(
        "pdp/spec_s5_first_m4_n17",
        "groebner_decompose_m4 first-found, S5 x-template, cell of spec_s5_all_m4_n17",
        Tier::Quick,
        s5_first_m4_n17,
    );
    add(
        "pdp/spec_s5_chain_first_m4_n17",
        "groebner_decompose_m4 first-found, generic chain, cell of spec_s5_all_m4_n17",
        Tier::Quick,
        chain_first_m4_n17,
    );
    add("pdp/spec_s5_paired_m4_n13", "decompose_all_m4 on the PDP_SPEC_S5_ARM arm (default s5), sets only; cell of spec_s5_all_m4_n13", Tier::Full, paired_m4_n13);
    add("pdp/spec_s5_paired_m4_n17", "decompose_all_m4 on the PDP_SPEC_S5_ARM arm (default s5), sets only; cell of spec_s5_all_m4_n17", Tier::Full, paired_m4_n17);
    add("pdp/spec_s5_paired_m4_n15", "decompose_all_m4 on the PDP_SPEC_S5_ARM arm (default s5), sets only; cell of spec_s5sym_all_m4_n15", Tier::Full, paired_m4_n15);
    add(
        "pdp/spec_s5_all_m4_n23",
        "decompose_all_m4 S5 x-template (12 vars), K/2^23 random V l=3, 2 planted + 2 random",
        Tier::Quick,
        s5_all_m4_n23,
    );
    add(
        "pdp/spec_s5_chain_all_m4_n23",
        "decompose_all_m4 generic chain (58 vars), same cell as spec_s5_all_m4_n23",
        Tier::Quick,
        chain_all_m4_n23,
    );
    add(
        "pdp/spec_s5_all_m4_n17_l4",
        "decompose_all_m4 S5 x-template (16 vars), K/2^17 random V l=4, 2 planted + 2 random",
        Tier::Full,
        s5_all_m4_n17_l4,
    );
    add(
        "pdp/spec_s5_chain_all_m4_n17_l4",
        "decompose_all_m4 generic chain (50 vars), same cell as spec_s5_all_m4_n17_l4",
        Tier::Full,
        chain_all_m4_n17_l4,
    );
    add("pdp/spec_s5_paired_m4_n23", "decompose_all_m4 on the PDP_SPEC_S5_ARM arm (default s5), sets only; cell of spec_s5_all_m4_n23", Tier::Full, paired_m4_n23);
    add("pdp/spec_s5_paired_m4_n17_l4", "decompose_all_m4 on the PDP_SPEC_S5_ARM arm (default s5), sets only; cell of spec_s5_all_m4_n17_l4", Tier::Full, paired_m4_n17_l4);
    add("pdp/spec_s5_build_x_n23_l4", "S5Template::build_x (dense evaluation + Moebius, 16 vars) + one instantiate, K/2^23 random V l=4", Tier::Quick, s5_build_x_n23_l4);
}
