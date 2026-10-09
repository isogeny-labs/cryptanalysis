//! Area `sat`, specialised paths: `m = 4` decomposition through the
//! hardcoded symmetrised `S₅` encoder (`semaev_sat_s5`) against the generic
//! chained `S₃` system on the same instances.
//!
//! Each kernel enumerates **every** four-summand decomposition of a fixed
//! set of targets (up to two planted four-point sums, then random abscissae)
//! over a polynomial-basis factor base on a fixed random curve, and
//! fingerprints the returned decomposition lists, completeness, and the
//! work counters (models, chain rejections, conflicts, decisions,
//! propagations, encoding size).  The specialised and generic kernels of
//! one instance return the same decomposition lists (pinned by the
//! module's differential tests, and re-checked untimed in setup with
//! `PERFBENCH_SPEC_CROSSCHECK=1`); their counters differ, which is the
//! point.  Templates of both paths are memoised per thread and warmed in
//! the untimed setup, so the timed run is per-target encode + search.
//!
//! Generic kernels that take seconds are `Full` tier; their specialised
//! counterparts on the same instance are `Quick`.
//!
//! * `sat/spec_s5_native_*` — specialised, native XOR rows.
//! * `sat/spec_s5_cnf_*` — specialised, Tseitin-chained CNF parity.
//! * `sat/spec_s5_generic_native_*` — generic chain, native XOR rows.
//! * `sat/spec_s5_generic_cnf_*` — generic chain, CNF parity.
//! * `sat/spec_s5_pair_*` — one ID for both paths, selected by
//!   `PERFBENCH_SPEC_PATH=generic` (otherwise specialised), fingerprinting
//!   only the decomposition lists and completeness, so
//!   `perfindex.py compare` can pair generic (base) against specialised
//!   (candidate) on the same work.

use crate::harness::{Closure, Fp, Kernel, Tier, Workload};
use cryptanalysis_suite::binary_ecc::curve::point_add;
use cryptanalysis_suite::binary_ecc::{BinaryCurve, BinaryPoint, F2mElement, IrreduciblePoly};
use cryptanalysis_suite::cryptanalysis::binary_semaev::solve_artin_schreier;
use cryptanalysis_suite::cryptanalysis::semaev_sat::XorEncoding;
use cryptanalysis_suite::cryptanalysis::semaev_sat_s5::{
    sat_decompositions, DecompositionSet, SatEnumOptions, SatPath,
};

struct SplitMix(u64);

impl SplitMix {
    fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9e37_79b9_7f4a_7c15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
        z ^ (z >> 31)
    }
}

fn elem(w: u64, n: u32) -> F2mElement {
    let bits: Vec<u32> = (0..n).filter(|k| (w >> k) & 1 == 1).collect();
    F2mElement::from_bit_positions(&bits, n)
}

struct Instance {
    irr: IrreduciblePoly,
    basis: Vec<F2mElement>,
    b: F2mElement,
    targets: Vec<F2mElement>,
}

/// A polynomial-basis factor base `⟨1, z, …, z^{ℓ−1}⟩` on
/// `y² + xy = x³ + b` with seeded random `b`; two planted targets (sums of
/// four lifted factor-base points) and two random ones.
fn instance(n: u32, low: &[u32], l: usize, seed: u64, count: usize) -> Instance {
    let irr = IrreduciblePoly {
        degree: n,
        low_terms: low.to_vec(),
    };
    let mut rng = SplitMix(seed);
    let mask = (1u64 << n) - 1;
    let b = loop {
        let w = rng.next() & mask;
        if w != 0 {
            break elem(w, n);
        }
    };
    let curve = BinaryCurve {
        m: n,
        irreducible: irr.clone(),
        a: F2mElement::zero(n),
        b: b.clone(),
        generator: BinaryPoint::Infinity,
        order: 0u8.into(),
        cofactor: 1u8.into(),
    };
    let basis: Vec<F2mElement> = (0..l).map(|k| elem(1 << k, n)).collect();
    let mut targets = Vec::new();
    while targets.len() < count.min(2) {
        let mut sum = BinaryPoint::Infinity;
        let mut have = 0;
        while have < 4 {
            let x = elem(rng.next() & ((1 << l) - 1), n);
            if x.is_zero() {
                continue;
            }
            let x2inv = x.square(&irr).flt_inverse(&irr).expect("x ≠ 0");
            let rhs = x.add(&b.mul(&x2inv, &irr));
            if let Some(t) = solve_artin_schreier(&rhs, n, &irr) {
                let p = BinaryPoint::Affine {
                    y: x.mul(&t, &irr),
                    x,
                };
                sum = point_add(&curve, &sum, &p);
                have += 1;
            }
        }
        if let BinaryPoint::Affine { x, .. } = sum {
            targets.push(x);
        }
    }
    while targets.len() < count {
        targets.push(elem(rng.next() & mask, n));
    }
    Instance {
        irr,
        basis,
        b,
        targets,
    }
}

fn fp_set(fp: Fp, d: &DecompositionSet) -> Fp {
    let c = &d.counters;
    let mut fp = fp
        .bool(d.complete)
        .usize(d.decompositions.len())
        .u64(c.solver_calls)
        .u64(c.models)
        .u64(c.rejected_by_chain)
        .u64(c.spurious)
        .u64(c.conflicts)
        .u64(c.decisions)
        .u64(c.propagations)
        .u64(c.vars)
        .u64(c.clauses)
        .u64(c.xor_rows);
    for t in &d.decompositions {
        fp = fp.words(t);
    }
    fp
}

fn enumerate(
    n: u32,
    low: &'static [u32],
    l: usize,
    seed: u64,
    count: usize,
    path: SatPath,
    encoding: XorEncoding,
) -> Box<dyn Workload> {
    // `Auto` marks a paired kernel: the path comes from the environment
    // and only the path-independent output is fingerprinted.
    let paired = path == SatPath::Auto;
    let path = match (paired, std::env::var("PERFBENCH_SPEC_PATH").as_deref()) {
        (true, Ok("generic")) => SatPath::Generic,
        (true, _) => SatPath::Specialised,
        (false, _) => path,
    };
    let inst = instance(n, low, l, seed, count);
    let opts = SatEnumOptions {
        path,
        encoding,
        ..Default::default()
    };
    if std::env::var("PERFBENCH_SPEC_CROSSCHECK").as_deref() == Ok("1") {
        // Untimed: the other path must return the same lists.
        let other = SatEnumOptions {
            path: match path {
                SatPath::Generic => SatPath::Specialised,
                _ => SatPath::Generic,
            },
            ..opts
        };
        for x_r in &inst.targets {
            let a = sat_decompositions(&inst.basis, x_r, &inst.b, 4, &inst.irr, opts).unwrap();
            let b = sat_decompositions(&inst.basis, x_r, &inst.b, 4, &inst.irr, other).unwrap();
            assert_eq!(a.0.decompositions, b.0.decompositions, "paths disagree");
            eprintln!("crosscheck ok: {} decompositions", a.0.decompositions.len());
        }
    }
    let run = move || {
        let mut fp = Fp::new();
        for x_r in &inst.targets {
            let (set, _) = sat_decompositions(&inst.basis, x_r, &inst.b, 4, &inst.irr, opts)
                .expect("the requested path encodes the instance");
            assert!(set.complete && set.counters.spurious == 0);
            fp = if paired {
                set.decompositions
                    .iter()
                    .fold(fp.bool(set.complete), |fp, t| fp.words(t))
            } else {
                fp_set(fp, &set)
            };
        }
        fp.finish()
    };
    let mut w = Closure(run);
    // Warm both template memos outside the timed region.
    w.run();
    Box::new(w)
}

const LOW_8: &[u32] = &[0, 2, 3, 4];
const LOW_9: &[u32] = &[0, 4];
const LOW_11: &[u32] = &[0, 2];

macro_rules! kernel {
    ($add:ident, $id:literal, $desc:literal, $tier:expr, $n:expr, $low:expr, $l:expr, $seed:expr, $count:expr, $path:expr, $enc:expr) => {
        $add($id, $desc, $tier, || {
            enumerate($n, $low, $l, $seed, $count, $path, $enc)
        });
    };
}

pub fn register(kernels: &mut Vec<Kernel>) {
    let mut add = |id: &'static str, desc: &'static str, tier: Tier, setup| {
        kernels.push(Kernel {
            id,
            area: "sat",
            desc,
            tier,
            setup,
        })
    };
    use SatPath::{Generic, Specialised};
    use XorEncoding::{Cnf, Native};
    // Paired: same ID on both sides of `perfindex.py compare`, the path
    // chosen by PERFBENCH_SPEC_PATH=generic|specialised (default).
    kernel!(
        add,
        "sat/spec_s5_pair_native_n8l2",
        "m=4 decompositions, path from PERFBENCH_SPEC_PATH, native XOR, n=8 l=2, 4 targets",
        Tier::Quick,
        8,
        LOW_8,
        2,
        0x5508,
        4,
        SatPath::Auto,
        Native
    );
    kernel!(
        add,
        "sat/spec_s5_pair_cnf_n8l2",
        "m=4 decompositions, path from PERFBENCH_SPEC_PATH, CNF parity, n=8 l=2, 4 targets",
        Tier::Full,
        8,
        LOW_8,
        2,
        0x5508,
        4,
        SatPath::Auto,
        Cnf
    );
    kernel!(
        add,
        "sat/spec_s5_pair_native_n9l3",
        "m=4 decompositions, path from PERFBENCH_SPEC_PATH, native XOR, n=9 l=3, 2 planted targets",
        Tier::Full,
        9,
        LOW_9,
        3,
        0x5509,
        2,
        SatPath::Auto,
        Native
    );
    kernel!(add, "sat/spec_s5_pair_native_n11l3", "m=4 decompositions, path from PERFBENCH_SPEC_PATH, native XOR, n=11 l=3, 2 planted targets", Tier::Full, 11, LOW_11, 3, 0x5511, 2, SatPath::Auto, Native);
    kernel!(
        add,
        "sat/spec_s5_native_n8l2",
        "m=4 all decompositions, symmetrised S5 SAT, native XOR, n=8 l=2, 4 targets",
        Tier::Quick,
        8,
        LOW_8,
        2,
        0x5508,
        4,
        Specialised,
        Native
    );
    kernel!(
        add,
        "sat/spec_s5_cnf_n8l2",
        "m=4 all decompositions, symmetrised S5 SAT, CNF parity, n=8 l=2, 4 targets",
        Tier::Quick,
        8,
        LOW_8,
        2,
        0x5508,
        4,
        Specialised,
        Cnf
    );
    kernel!(
        add,
        "sat/spec_s5_generic_native_n8l2",
        "m=4 all decompositions, generic S3 chain SAT, native XOR, n=8 l=2, 4 targets",
        Tier::Quick,
        8,
        LOW_8,
        2,
        0x5508,
        4,
        Generic,
        Native
    );
    kernel!(
        add,
        "sat/spec_s5_generic_cnf_n8l2",
        "m=4 all decompositions, generic S3 chain SAT, CNF parity, n=8 l=2, 4 targets",
        Tier::Full,
        8,
        LOW_8,
        2,
        0x5508,
        4,
        Generic,
        Cnf
    );
    kernel!(
        add,
        "sat/spec_s5_native_n9l3",
        "m=4 all decompositions, symmetrised S5 SAT, native XOR, n=9 l=3, 2 planted targets",
        Tier::Quick,
        9,
        LOW_9,
        3,
        0x5509,
        2,
        Specialised,
        Native
    );
    kernel!(
        add,
        "sat/spec_s5_generic_native_n9l3",
        "m=4 all decompositions, generic S3 chain SAT, native XOR, n=9 l=3, 2 planted targets",
        Tier::Full,
        9,
        LOW_9,
        3,
        0x5509,
        2,
        Generic,
        Native
    );
    kernel!(
        add,
        "sat/spec_s5_native_n11l3",
        "m=4 all decompositions, symmetrised S5 SAT, native XOR, n=11 l=3, 2 planted targets",
        Tier::Quick,
        11,
        LOW_11,
        3,
        0x5511,
        2,
        Specialised,
        Native
    );
    kernel!(
        add,
        "sat/spec_s5_generic_native_n11l3",
        "m=4 all decompositions, generic S3 chain SAT, native XOR, n=11 l=3, 2 planted targets",
        Tier::Full,
        11,
        LOW_11,
        3,
        0x5511,
        2,
        Generic,
        Native
    );
}
