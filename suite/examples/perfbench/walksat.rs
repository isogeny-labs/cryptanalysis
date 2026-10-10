//! Area `sat`, `spec_walksat_*`: WalkSAT local search
//! (`cryptanalysis::walksat`) against the CDCL path on the same Koblitz
//! decomposition systems.
//!
//! * `spec_walksat_anf_*` — `walksat_decompose` with the ANF engine
//!   (search over the problem variables only).
//! * `spec_walksat_cnfxor_*` — the same with the CNF + native-parity
//!   engine (the instance the CDCL solver sees).
//! * `spec_walksat_cdcl_*` — the generic path, `sat_decompose_with`
//!   (native XOR, default options), on the identical targets: the paired
//!   comparison for the two kernels above.
//!
//! Targets are planted (a sum of `m` seeded base points), so every one
//! decomposes and the CDCL path always finds a decomposition; the walk may
//! miss.  Each fingerprint covers, per target, the returned decomposition
//! (or a miss marker) and the counters: flips, tries, noise steps, break
//! evaluations, models and rejected models for the walk; solver calls,
//! models and conflicts for CDCL.  Every decomposition is re-summed in
//! the group in `prepare`-independent code before it is fingerprinted.

use crate::harness::{Fp, Kernel, Tier, Workload};
use cryptanalysis_suite::binary_ecc::BinaryPoint;
use cryptanalysis_suite::cryptanalysis::koblitz_groebner::FieldStructure;
use cryptanalysis_suite::cryptanalysis::koblitz_index_calculus::{
    build_frobenius_factor_base, sat_decompose_with, FrobeniusFactorBase, KoblitzCurve,
    SatDecompositionOptions,
};
use cryptanalysis_suite::cryptanalysis::walksat::{
    walksat_decompose, WalkEncoding, WalkSatDecompositionOptions,
};
use num_bigint::BigUint;
use std::collections::HashMap;

struct Cell {
    kc: KoblitzCurve,
    fb: FrobeniusFactorBase,
    index_of: HashMap<(BigUint, BigUint), usize>,
    st: FieldStructure,
    m: usize,
    targets: Vec<BinaryPoint>,
}

fn cell(a: u8, n: u32, m: usize, count: usize, seed: u64) -> Cell {
    let kc = KoblitzCurve::new(a, n).expect("Koblitz curve exists");
    let fb = build_frobenius_factor_base(&kc, 0).expect("factor base exists");
    let index_of = fb.index_map();
    let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
    let mut s = seed;
    let mut next = move || {
        s = s.wrapping_add(0x9e37_79b9_7f4a_7c15);
        let mut z = s;
        z = (z ^ (z >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
        z ^ (z >> 31)
    };
    let mut targets = Vec::with_capacity(count);
    while targets.len() < count {
        let t = (0..m).fold(BinaryPoint::Infinity, |acc, _| {
            kc.add(&acc, &fb.points[(next() % fb.points.len() as u64) as usize])
        });
        if t != BinaryPoint::Infinity {
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

fn fp_decomposition(fp: Fp, c: &Cell, t: &BinaryPoint, idxs: &Option<Vec<usize>>) -> Fp {
    match idxs {
        None => fp.u64(u64::MAX),
        Some(idxs) => {
            let sum = idxs.iter().fold(BinaryPoint::Infinity, |acc, &i| {
                c.kc.add(&acc, &c.fb.points[i])
            });
            assert_eq!(&sum, t, "decomposition does not sum to the target");
            idxs.iter().fold(fp.usize(idxs.len()), |f, &i| f.usize(i))
        }
    }
}

struct Walk {
    c: Cell,
    o: WalkSatDecompositionOptions,
}

impl Workload for Walk {
    fn run(&mut self) -> u64 {
        let c = &self.c;
        let mut fp = Fp::new();
        for t in &c.targets {
            let (r, s) = walksat_decompose(&c.kc, &c.fb, &c.index_of, &c.st, t, c.m, &self.o);
            assert_eq!(s.spurious, 0, "walk model violates the system");
            fp = fp_decomposition(fp, c, t, &r)
                .u64(s.walk.flips)
                .u64(s.walk.tries)
                .u64(s.walk.noise_steps)
                .u64(s.walk.break_evals)
                .usize(s.models)
                .usize(s.rejected)
                .usize(s.solver_calls);
        }
        fp.finish()
    }
}

struct Cdcl {
    c: Cell,
}

impl Workload for Cdcl {
    fn run(&mut self) -> u64 {
        let c = &self.c;
        let mut fp = Fp::new();
        for t in &c.targets {
            let (r, s) = sat_decompose_with(
                &c.kc,
                &c.fb,
                &c.index_of,
                &c.st,
                t,
                c.m,
                4096,
                None,
                SatDecompositionOptions::default(),
            );
            assert_eq!(s.spurious, 0);
            assert!(r.is_some(), "planted target must decompose");
            fp = fp_decomposition(fp, c, t, &r)
                .usize(s.solver_calls)
                .usize(s.models)
                .u64(s.conflicts);
        }
        fp.finish()
    }
}

fn walk(c: Cell, encoding: WalkEncoding) -> Box<dyn Workload> {
    Box::new(Walk {
        c,
        o: WalkSatDecompositionOptions {
            encoding,
            ..WalkSatDecompositionOptions::default()
        },
    })
}

// Cells: (a, n, m, targets, seed).
const M2: (u8, u32, usize, usize, u64) = (0, 13, 2, 12, 0x5a17);
const M3: (u8, u32, usize, usize, u64) = (0, 9, 3, 12, 0x5a19);

fn c(p: (u8, u32, usize, usize, u64)) -> Cell {
    cell(p.0, p.1, p.2, p.3, p.4)
}

fn anf_m2() -> Box<dyn Workload> {
    walk(c(M2), WalkEncoding::Anf)
}
fn cnfxor_m2() -> Box<dyn Workload> {
    walk(c(M2), WalkEncoding::CnfXor)
}
fn cdcl_m2() -> Box<dyn Workload> {
    Box::new(Cdcl { c: c(M2) })
}
fn anf_m3() -> Box<dyn Workload> {
    walk(c(M3), WalkEncoding::Anf)
}
fn cnfxor_m3() -> Box<dyn Workload> {
    walk(c(M3), WalkEncoding::CnfXor)
}
fn cdcl_m3() -> Box<dyn Workload> {
    Box::new(Cdcl { c: c(M3) })
}

pub fn register(kernels: &mut Vec<Kernel>) {
    let mut add = |id, desc, setup| {
        kernels.push(Kernel {
            id,
            area: "sat",
            desc,
            tier: Tier::Quick,
            setup,
        })
    };
    add(
        "sat/spec_walksat_anf_k0n13_m2",
        "walksat_decompose (ANF engine) on planted m=2 targets, K_0/2^13",
        anf_m2 as fn() -> Box<dyn Workload>,
    );
    add(
        "sat/spec_walksat_cnfxor_k0n13_m2",
        "walksat_decompose (CNF+XOR engine) on planted m=2 targets, K_0/2^13",
        cnfxor_m2,
    );
    add(
        "sat/spec_walksat_cdcl_k0n13_m2",
        "sat_decompose_with (CDCL, generic path) on the same planted m=2 targets",
        cdcl_m2,
    );
    add(
        "sat/spec_walksat_anf_k0n9_m3",
        "walksat_decompose (ANF engine) on planted m=3 targets, K_0/2^9 chained system",
        anf_m3,
    );
    add(
        "sat/spec_walksat_cnfxor_k0n9_m3",
        "walksat_decompose (CNF+XOR engine) on planted m=3 targets, K_0/2^9",
        cnfxor_m3,
    );
    add(
        "sat/spec_walksat_cdcl_k0n9_m3",
        "sat_decompose_with (CDCL, generic path) on the same planted m=3 targets",
        cdcl_m3,
    );
}
