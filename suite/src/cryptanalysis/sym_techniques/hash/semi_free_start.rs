//! Reduced-step semi-free-start (SFS) collisions for SHA-2, by two routes.
//!
//! A semi-free-start collision for a compression function `f` is a chaining
//! value `h` and two different message blocks `m != m'` with
//! `f(h, m) = f(h, m')`; `h` is chosen by the attacker. Here `f` is the
//! first `n` steps of SHA-256 (or SHA-512) with the Davies-Meyer
//! feed-forward, as described in `sym_ir::primitives::{sha256_compress,
//! sha512_compress}`; every result is checked by running both messages
//! through that IR description ([`verify`]).
//!
//! The best known step-reduced SHA-256 results (Mendel, Nad and Schlaeffer,
//! "Improving local collisions: new attacks on reduced SHA-256",
//! EUROCRYPT 2013) are 31 steps for collisions and 38 for SFS; nothing here
//! approaches that. The routes are:
//!
//! 1. **Condition propagation and placement**
//!    ([`sfs_by_local_collision`]). A [`local_collision`](super::local_collision)
//!    at step `i` uses message differences only in `W_i..W_{i+8}`; every later
//!    expanded word must carry no difference. Which `i` and how many steps are
//!    compatible with the message schedule is decided by propagating the
//!    generalized conditions "word differs" / "word equal" through the
//!    schedule ([`gc_expand`]) and requiring
//!    equality on every word after the collision closes
//!    ([`placement_max_steps`]); the free message words (the message
//!    modification) are simply the words `W_i..W_{i+8}` the collision
//!    prescribes plus the random common words, and the chaining value is
//!    obtained by running the steps before `i` backwards.
//! 2. **SAT** ([`sfs_by_sat`]). The two compressions are encoded as one CNF by
//!    [`cnf::encode_rounds`](super::cnf::encode_rounds) with the chaining
//!    value shared (so equal prefixes share gates), output bits constrained
//!    equal and the messages constrained to differ, and handed to the CDCL
//!    solver in `cryptanalysis::sat`. Optionally some message words are forced
//!    equal ([`SatOptions::equal_words`]), which is how the support found by
//!    route 1 can guide the solver.
//!
//! # Observed on the development host (one run each, not a benchmark)
//!
//! Route 1 produces a checked pair for every `n` in `9..=18` in under 50 ms
//! and has no pair for `n = 19` (placement analysis; the 18-step pair stops
//! colliding at 19). Unguided SAT (seed 1, 1.5M-conflict budget) found
//! pairs for `n = 5..=18` (about 1-12 s up to `n = 16`, 24 s at 17, 119 s at
//! 18) and returned `Unknown` at `n = 19` and `n = 20`. SAT guided by the
//! route-1 word support plus a pinned `Delta W` returned `Unknown` in the
//! tested configurations.

use super::cnf::{bits_to_words, encode_rounds, model_bits, CnfBuilder};
use super::local_collision::{
    embed, find_local_collision, gc_expand, Gc, GcWord, LocalCollisionSpec, Sha2Params,
    LOCAL_COLLISION_STEPS, MIN_SUPPORT,
};
use crate::cryptanalysis::sat::SolveResult;
use crate::cryptanalysis::sym_ir::primitives::{sha256_compress, sha512_compress};
use crate::cryptanalysis::sym_ir::{eval, Primitive};
use std::time::Instant;

/// A semi-free-start collision for the first `steps` steps.
#[derive(Clone, Debug)]
pub struct SfsCollision {
    /// Number of compression steps.
    pub steps: usize,
    /// Shared chaining value (big-endian words).
    pub chaining: Vec<u8>,
    /// First message block.
    pub m1: Vec<u8>,
    /// Second message block.
    pub m2: Vec<u8>,
    /// How it was found.
    pub method: &'static str,
}

/// The IR description of the first `n` steps of the hash selected by `p`.
pub fn reduced_primitive(p: &Sha2Params, n: usize) -> Primitive {
    match p.w {
        32 => sha256_compress::steps(n),
        64 => sha512_compress::steps(n),
        w => panic!("no IR description for word size {w}"),
    }
}

/// Run both messages through the IR and report whether they collide with
/// different messages.
pub fn verify(p: &Sha2Params, c: &SfsCollision) -> bool {
    let prim = reduced_primitive(p, c.steps);
    c.m1 != c.m2 && eval(&prim, &c.m1, &c.chaining) == eval(&prim, &c.m2, &c.chaining)
}

/// How many steps a local collision injected at step `start` can be extended
/// to: the largest `n` such that, with `Delta W` allowed exactly on
/// `W_start..W_{start+8}` (the [`MIN_SUPPORT`] words), propagation of the
/// generalized conditions through the message schedule leaves every word
/// `W_t`, `start + 9 <= t < n`, equal in both messages. `None` if the
/// collision words do not fit in `W_0..W_15` (the only words that can be
/// chosen freely).
pub fn placement_max_steps(p: &Sha2Params, start: usize) -> Option<usize> {
    if start + LOCAL_COLLISION_STEPS > 16 {
        return None;
    }
    let block: [GcWord; 16] = std::array::from_fn(|t| {
        if t >= start && t < start + LOCAL_COLLISION_STEPS && MIN_SUPPORT[t - start] {
            GcWord::any(p.w)
        } else {
            GcWord::equal(p.w)
        }
    });
    let total = p.k.len();
    let words = gc_expand(p, &block, total);
    let mut n = start + LOCAL_COLLISION_STEPS;
    while n < total && words[n].bits.iter().all(|g| g.subset_of(Gc::EQ)) {
        n += 1;
    }
    Some(n)
}

/// Table of `(start, max_steps)` over all placements that fit.
pub fn placement_table(p: &Sha2Params) -> Vec<(usize, usize)> {
    (0..=16 - LOCAL_COLLISION_STEPS)
        .filter_map(|s| placement_max_steps(p, s).map(|m| (s, m)))
        .collect()
}

/// The placement reaching the most steps (smallest `start` on ties).
pub fn best_placement(p: &Sha2Params) -> (usize, usize) {
    placement_table(p)
        .into_iter()
        .fold((0, 0), |best, c| if c.1 > best.1 { c } else { best })
}

/// An SFS collision for exactly `n` steps (`n >= 9`) from a local collision,
/// or `None` if no placement reaches `n`.
pub fn sfs_by_local_collision(p: &Sha2Params, n: usize, seed: u64) -> Option<SfsCollision> {
    let start = placement_table(p)
        .into_iter()
        .filter(|&(s, max)| s + LOCAL_COLLISION_STEPS <= n && n <= max)
        .map(|(s, _)| s)
        .next()?;
    let spec = LocalCollisionSpec {
        start,
        bit: 0,
        positive: true,
    };
    let lc = find_local_collision(p, spec, seed, 1 << 28)?;
    let e = embed(&lc, seed ^ 0x5eed);
    Some(SfsCollision {
        steps: n,
        chaining: e.chaining,
        m1: e.m1,
        m2: e.m2,
        method: "local collision + message-schedule placement",
    })
}

/// Options for the SAT backend.
#[derive(Clone, Debug)]
pub struct SatOptions {
    /// Message words (indices `0..16`) forced equal in both messages.
    pub equal_words: Vec<usize>,
    /// Conflict budget (`0` is replaced by no limit).
    pub conflict_budget: u64,
    /// Seed for the solver's initial phases.
    pub seed: u64,
    /// Pin the difference of one message word: `(word, bit, positive)`
    /// forces `m2[word] = m1[word] +- 2^bit`.
    pub first_diff: Option<(usize, usize, bool)>,
}

/// Outcome and cost of one SAT run.
#[derive(Clone, Debug)]
pub struct SatReport {
    /// Steps encoded.
    pub steps: usize,
    /// Solver verdict (`Unknown` when the budget ran out).
    pub status: SolveResult,
    /// CNF variables.
    pub vars: u32,
    /// CNF clauses before solving.
    pub clauses: usize,
    /// Conflicts used.
    pub conflicts: u64,
    /// Wall-clock seconds for encoding and solving.
    pub seconds: f64,
    /// The collision, when satisfiable.
    pub collision: Option<SfsCollision>,
}

/// SAT search for an SFS collision on `n` steps.
pub fn sfs_by_sat(p: &Sha2Params, n: usize, opts: &SatOptions) -> SatReport {
    let t0 = Instant::now();
    let prim = reduced_primitive(p, n);
    let w = p.w;
    let mut b = CnfBuilder::new();
    let h = b.fresh_vec(prim.block_bits);
    let m1 = b.fresh_vec(prim.key_bits);
    let mut m2 = m1.clone();
    let mut diff_bits = Vec::new();
    for word in 0..16 {
        if opts.equal_words.contains(&word) {
            continue;
        }
        let fresh = b.fresh_vec(w);
        for i in 0..w {
            let x = b.xor(m1[word * w + i], fresh[i]);
            diff_bits.push(x);
        }
        m2[word * w..(word + 1) * w].copy_from_slice(&fresh);
    }
    if let Some((word, bit, positive)) = opts.first_diff {
        assert!(!opts.equal_words.contains(&word));
        let a = m1[word * w..(word + 1) * w].to_vec();
        let d = b.constant(
            if positive {
                1u64 << bit
            } else {
                (1u64 << bit).wrapping_neg() & p.mask()
            },
            w,
        );
        let sum = b.add_word(&a, &d);
        for i in 0..w {
            b.assert_eq(sum[i], m2[word * w + i]);
        }
    }
    assert!(!diff_bits.is_empty(), "all message words forced equal");
    b.clause(diff_bits);
    let o1 = encode_rounds(&mut b, &prim, n, &m1, &h);
    let o2 = encode_rounds(&mut b, &prim, n, &m2, &h);
    for (x, y) in o1.iter().zip(&o2) {
        b.assert_eq(*x, *y);
    }
    let vars = b.n_vars();
    let clauses = b.clauses.len();
    let Some(mut solver) = b.into_solver() else {
        return SatReport {
            steps: n,
            status: SolveResult::Unsat,
            vars,
            clauses,
            conflicts: 0,
            seconds: t0.elapsed().as_secs_f64(),
            collision: None,
        };
    };
    if opts.conflict_budget > 0 {
        solver.conflict_budget = opts.conflict_budget;
    }
    solver.scramble_saved_phases(opts.seed);
    let status = solver.solve();
    let collision = (status == SolveResult::Sat).then(|| {
        let model = solver.model();
        let decode = |lits: &[i32], codec: &crate::cryptanalysis::sym_ir::Codec, bits: usize| {
            codec.decode(&bits_to_words(&model_bits(&model, lits)), bits)
        };
        SfsCollision {
            steps: n,
            chaining: decode(&h, &prim.block_codec, prim.block_bits),
            m1: decode(&m1, &prim.key_codec, prim.key_bits),
            m2: decode(&m2, &prim.key_codec, prim.key_bits),
            method: "SAT (CDCL on IR-derived CNF)",
        }
    });
    SatReport {
        steps: n,
        status,
        vars,
        clauses,
        conflicts: solver.conflicts(),
        seconds: t0.elapsed().as_secs_f64(),
        collision,
    }
}

/// The message words that may differ for a local collision at `start`
/// (absolute indices); every other word of `W_0..W_15` can be forced equal
/// for [`SatOptions::equal_words`].
pub fn equal_words_for_placement(start: usize) -> Vec<usize> {
    (0..16)
        .filter(|&t| !(t >= start && t < start + LOCAL_COLLISION_STEPS && MIN_SUPPORT[t - start]))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Independent reduced-step SHA-256 with feed-forward, not using the IR.
    fn sha256_steps_reference(n: usize, h: &[u8], block: &[u8]) -> Vec<u8> {
        let p = Sha2Params::sha256();
        let st: [u64; 8] = std::array::from_fn(|i| {
            u32::from_be_bytes(h[4 * i..4 * i + 4].try_into().unwrap()) as u64
        });
        let blk: [u64; 16] = std::array::from_fn(|i| {
            u32::from_be_bytes(block[4 * i..4 * i + 4].try_into().unwrap()) as u64
        });
        let w = p.expand(&blk, n);
        let mut s = st;
        for t in 0..n {
            s = p.step(&s, w[t], p.k[t]);
        }
        (0..8)
            .flat_map(|i| (((s[i] + st[i]) & 0xffff_ffff) as u32).to_be_bytes())
            .collect()
    }

    fn check_both(c: &SfsCollision) {
        let p = Sha2Params::sha256();
        assert!(verify(&p, c), "IR must show the collision");
        assert_ne!(c.m1, c.m2);
        let r1 = sha256_steps_reference(c.steps, &c.chaining, &c.m1);
        let r2 = sha256_steps_reference(c.steps, &c.chaining, &c.m2);
        assert_eq!(r1, r2, "independent reference must show the collision");
        assert_eq!(
            r1,
            eval(&sha256_compress::steps(c.steps), &c.m1, &c.chaining),
            "reference and IR agree"
        );
    }

    #[test]
    fn placement_table_by_condition_propagation() {
        let p = Sha2Params::sha256();
        let table = placement_table(&p);
        eprintln!("SHA-256 placement table (start, max steps): {table:?}");
        eprintln!(
            "SHA-512 placement table: {:?}",
            placement_table(&Sha2Params::sha512())
        );
        // collisions placed at start 0 extend to 16 steps (free words only),
        // start 3 reaches the schedule's first dependence at W_18.
        assert_eq!(table[0], (0, 16));
        assert_eq!(placement_max_steps(&p, 3), Some(18));
        assert_eq!(best_placement(&p), (3, 18));
        assert_eq!(placement_max_steps(&p, 8), None);
    }

    #[test]
    fn sha256_sfs_collisions_from_9_to_18_steps() {
        let p = Sha2Params::sha256();
        let mut longest = 0;
        for n in 9..=18 {
            let t0 = Instant::now();
            let c = sfs_by_local_collision(&p, n, 100 + n as u64).expect("placement exists");
            let dt = t0.elapsed();
            check_both(&c);
            longest = n;
            eprintln!("SFS n={n}: found and checked in {dt:?}");
        }
        assert_eq!(longest, 18);
    }

    #[test]
    fn sha256_sfs_pair_at_18_steps_is_pinned_and_stops_at_19() {
        let p = Sha2Params::sha256();
        let c = sfs_by_local_collision(&p, 18, 118).unwrap();
        eprintln!(
            "18-step SFS pair\n  chaining {}\n  m1 {}\n  m2 {}",
            hex::encode(&c.chaining),
            hex::encode(&c.m1),
            hex::encode(&c.m2)
        );
        check_both(&c);
        // one step further the extra expanded word carries a difference
        let longer = SfsCollision {
            steps: 19,
            ..c.clone()
        };
        assert!(
            !verify(&p, &longer),
            "the same pair does not collide at 19 steps"
        );
        assert!(sfs_by_local_collision(&p, 19, 1).is_none());
        // and one step fewer than the collision length it has not yet closed
        let short = SfsCollision {
            steps: 3 + 9 - 1,
            ..c
        };
        assert!(!verify(&p, &short));
    }

    #[test]
    fn sha512_sfs_collision_at_18_steps_through_the_ir() {
        let p = Sha2Params::sha512();
        let c = sfs_by_local_collision(&p, 18, 5).unwrap();
        assert!(verify(&p, &c));
    }

    fn sat_run(
        n: usize,
        equal_words: Vec<usize>,
        first_diff: Option<(usize, usize, bool)>,
        budget: u64,
    ) -> SatReport {
        let r = sfs_by_sat(
            &Sha2Params::sha256(),
            n,
            &SatOptions {
                equal_words,
                conflict_budget: budget,
                seed: 1,
                first_diff,
            },
        );
        eprintln!(
            "SAT n={n}: {:?} vars={} clauses={} conflicts={} {:.2}s",
            r.status, r.vars, r.clauses, r.conflicts, r.seconds
        );
        if let Some(c) = &r.collision {
            check_both(c);
        }
        r
    }

    /// SAT vs condition propagation, one line per configuration. Heavy,
    /// run manually: `cargo test --release --lib sat_vs_condition -- --ignored --nocapture`.
    #[test]
    #[ignore]
    fn sat_vs_condition_propagation_comparison() {
        let p = Sha2Params::sha256();
        for n in [9usize, 10, 12, 14, 16, 17, 18] {
            let t0 = Instant::now();
            let c = sfs_by_local_collision(&p, n, 3).unwrap();
            eprintln!("CP  n={n}: collision in {:?}", t0.elapsed());
            assert!(verify(&p, &c));
        }
        for n in [5usize, 6, 7, 8, 9] {
            sat_run(n, vec![], None, 300_000);
        }
        for n in [10usize, 11, 12, 13] {
            for seed in 1..=2u64 {
                let r = sfs_by_sat(
                    &p,
                    n,
                    &SatOptions {
                        equal_words: vec![],
                        conflict_budget: 600_000,
                        seed,
                        first_diff: None,
                    },
                );
                eprintln!(
                    "SAT unguided n={n} seed={seed}: {:?} conflicts={} {:.1}s",
                    r.status, r.conflicts, r.seconds
                );
                if let Some(c) = &r.collision {
                    check_both(c);
                }
            }
        }
        for n in [9usize, 10, 12, 16, 18] {
            // guided by the placement the propagation chose, difference pinned
            let start = (0..=7)
                .find(|&s| placement_max_steps(&p, s).unwrap() >= n && s + 9 <= n)
                .unwrap();
            sat_run(
                n,
                equal_words_for_placement(start),
                Some((start, 0, true)),
                300_000,
            );
        }
    }

    /// How far unguided SAT gets within a 1.5M-conflict budget per step
    /// count. Heavy, run manually:
    /// `cargo test --release --lib sat_unguided_frontier -- --ignored --nocapture`.
    #[test]
    #[ignore]
    fn sat_unguided_frontier() {
        let p = Sha2Params::sha256();
        for n in 14usize..=20 {
            let r = sfs_by_sat(
                &p,
                n,
                &SatOptions {
                    equal_words: vec![],
                    conflict_budget: 1_500_000,
                    seed: 1,
                    first_diff: None,
                },
            );
            eprintln!(
                "SAT frontier n={n}: {:?} vars={} clauses={} conflicts={} {:.1}s",
                r.status, r.vars, r.clauses, r.conflicts, r.seconds
            );
            if let Some(c) = &r.collision {
                check_both(c);
            }
        }
    }

    /// Unguided SAT (chaining value and both messages free) finds
    /// collisions for 5 and 6 steps; each is re-checked through the IR and
    /// the independent reference.
    #[test]
    fn sat_unguided_small_collisions_through_the_ir() {
        for n in [5usize, 6] {
            let r = sat_run(n, vec![], None, 400_000);
            assert_eq!(r.status, SolveResult::Sat, "n={n}");
            assert!(verify(&Sha2Params::sha256(), r.collision.as_ref().unwrap()));
        }
    }

    /// SAT guided by the local-collision support and a pinned difference.
    #[test]
    fn sat_guided_by_placement_n9() {
        let r = sat_run(9, equal_words_for_placement(0), Some((0, 0, true)), 100_000);
        assert!(matches!(r.status, SolveResult::Sat | SolveResult::Unknown));
    }
}
