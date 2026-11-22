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
//! # Measured on the development host (one run each, not a benchmark)
//!
//! Route 1 uses the five-word support `{i, i+1, i+2, i+3, i+8}` with the
//! register value conditions of [`NB_CONDITIONS`]. Its placement analysis
//! (start, last step count it reaches) is `(0,16) (1,16) (2,17) (3,18) (4,19)
//! (5,20) (6,16) (7,16)`, the same for SHA-256 and SHA-512, and the route
//! produced checked pairs for every `n` in `9..=20` in under 50 ms each (the
//! SHA-256 20-step pair also through an independent `u32` reference). The
//! analysis gives no placement for `n = 21`; that is a limit of this method
//! (propagation on one local collision), not a statement about whether
//! 21-step pairs exist. An earlier version used the six-word support
//! `{i, i+1, i+2, i+3, i+5, i+8}` (what uniformly sampled register values
//! give) and stopped at 18.
//!
//! Unguided SAT (chaining value free, messages differing only in the words
//! the `n` steps read; seed 1, 1.5M-conflict budget; one run each) returned:
//! `n = 5` unsatisfiable (745k conflicts, 48 s), `n = 6` unsatisfiable (1.10M,
//! 90 s), `n = 7, 8` `Unknown`, then satisfiable for `n = 9..=18` (9: 246k
//! conflicts, 15 s; 10: 61k, 3.7 s; 11: 143k, 11 s; 12: 83k, 6 s; 13: 137k,
//! 11 s; 14: 156k, 15 s; 15: 85k, 8 s; 16: 82k, 9 s; 17: 194k, 23 s; 18: 695k,
//! 113 s; times were taken while other jobs shared the host). Earlier numbers
//! for `n < 16` allowed differences in words the steps never read and are
//! superseded. SAT guided by the route-1 word support plus a pinned `Delta W`
//! returned `Unknown` at `n = 9` (100k conflicts).

use super::cnf::{bits_to_words, encode_rounds, model_bits, CnfBuilder};
use super::local_collision::{
    embed, find_local_collision_conditioned, gc_expand, Gc, GcWord, LocalCollisionSpec, Sha2Params,
    LOCAL_COLLISION_STEPS, MIN_SUPPORT, NB_CONDITIONS,
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
/// different messages. Only message words that the first `c.steps` steps read
/// (`W_0..W_{min(steps,16)-1}`) count as a difference: a pair that differs
/// only in words never read is rejected.
pub fn verify(p: &Sha2Params, c: &SfsCollision) -> bool {
    let prim = reduced_primitive(p, c.steps);
    let read = c.steps.min(16) * p.w / 8;
    c.m1.len() >= read
        && c.m2.len() >= read
        && c.m1[..read] != c.m2[..read]
        && eval(&prim, &c.m1, &c.chaining) == eval(&prim, &c.m2, &c.chaining)
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
    let lc = find_local_collision_conditioned(p, spec, &NB_CONDITIONS, MIN_SUPPORT, seed, 1 << 10)?;
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
    /// Message words (indices `0..16`) forced equal in both messages. For
    /// `n < 16` steps the words `W_n..W_15` are always forced equal, since the
    /// compression function never reads them.
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
        // words W_n..W_15 are never read by n < 16 steps: keep them equal so
        // that every difference is one the compression function sees
        if word >= n || opts.equal_words.contains(&word) {
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
        assert!(!opts.equal_words.contains(&word) && word < n.min(16));
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

    /// Independent reduced-step SHA-256 with feed-forward: its own FIPS 180-4
    /// message schedule, `Sigma`, `sigma`, `Ch`, `Maj` and step on `u32`.
    /// Shares nothing with the attack code or the IR except the round-constant
    /// table `K`.
    fn sha256_steps_reference(n: usize, h: &[u8], block: &[u8]) -> Vec<u8> {
        use crate::hash::sha256::K;
        let h0: [u32; 8] =
            std::array::from_fn(|i| u32::from_be_bytes(h[4 * i..4 * i + 4].try_into().unwrap()));
        let mut w: Vec<u32> = (0..16)
            .map(|i| u32::from_be_bytes(block[4 * i..4 * i + 4].try_into().unwrap()))
            .collect();
        for t in 16..n {
            let s0 = w[t - 15].rotate_right(7) ^ w[t - 15].rotate_right(18) ^ (w[t - 15] >> 3);
            let s1 = w[t - 2].rotate_right(17) ^ w[t - 2].rotate_right(19) ^ (w[t - 2] >> 10);
            w.push(
                s1.wrapping_add(w[t - 7])
                    .wrapping_add(s0)
                    .wrapping_add(w[t - 16]),
            );
        }
        let [mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut hh] = h0;
        for t in 0..n {
            let big1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ (!e & g);
            let t1 = hh
                .wrapping_add(big1)
                .wrapping_add(ch)
                .wrapping_add(K[t])
                .wrapping_add(w[t]);
            let big0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let t2 = big0.wrapping_add(maj);
            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(t1);
            d = c;
            c = b;
            b = a;
            a = t1.wrapping_add(t2);
        }
        [a, b, c, d, e, f, g, hh]
            .iter()
            .zip(h0)
            .flat_map(|(x, y)| x.wrapping_add(y).to_be_bytes())
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

    fn pair(steps: usize, chaining: &str, m1: &str, m2: &str) -> SfsCollision {
        SfsCollision {
            steps,
            chaining: hex::decode(chaining).unwrap(),
            m1: hex::decode(m1).unwrap(),
            m2: hex::decode(m2).unwrap(),
            method: "pinned regression pair",
        }
    }

    /// Full 64-round reference against FIPS 180-4 `SHA-256("abc")` is covered
    /// by the crate's hash tests; here the reduced reference at 64 steps must
    /// reproduce the compression of the padded block "abc" from the IV.
    #[test]
    fn reference_matches_fips_compression_of_abc() {
        let iv: Vec<u8> = [
            0x6a09e667u32,
            0xbb67ae85,
            0x3c6ef372,
            0xa54ff53a,
            0x510e527f,
            0x9b05688c,
            0x1f83d9ab,
            0x5be0cd19,
        ]
        .iter()
        .flat_map(|x| x.to_be_bytes())
        .collect();
        let mut block = [0u8; 64];
        block[..3].copy_from_slice(b"abc");
        block[3] = 0x80;
        block[63] = 24;
        // SHA-256("abc") = ba7816bf 8f01cfea 414140de 5dae2223 b00361a3 96177a9c b410ff61 f20015ad
        assert_eq!(
            hex::encode(sha256_steps_reference(64, &iv, &block)),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
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
        // differing words {s, s+1, s+2, s+3, s+8}; the numbers below are what
        // the generalized-condition propagation returns
        assert_eq!(
            table,
            vec![
                (0, 16),
                (1, 16),
                (2, 17),
                (3, 18),
                (4, 19),
                (5, 20),
                (6, 16),
                (7, 16)
            ]
        );
        assert_eq!(placement_table(&Sha2Params::sha512()), table);
        assert_eq!(best_placement(&p), (5, 20));
        assert_eq!(placement_max_steps(&p, 8), None);
    }

    #[test]
    fn sha256_sfs_collisions_from_9_to_20_steps() {
        let p = Sha2Params::sha256();
        for n in 9..=20 {
            let t0 = Instant::now();
            let c = sfs_by_local_collision(&p, n, 100 + n as u64).expect("placement exists");
            let dt = t0.elapsed();
            assert_eq!(c.steps, n);
            check_both(&c);
            eprintln!("SFS n={n}: found and checked in {dt:?}");
        }
    }

    /// Pairs found by this crate's code are not collisions beyond the step
    /// counts the placement analysis gives: the 20-step pair stops colliding
    /// at 21 steps and no placement of the five-word support extends to 21.
    #[test]
    fn sha256_sfs_pair_at_20_steps_and_one_step_further() {
        let p = Sha2Params::sha256();
        let c = sfs_by_local_collision(&p, 20, 120).unwrap();
        eprintln!(
            "20-step SFS pair\n  chaining {}\n  m1 {}\n  m2 {}",
            hex::encode(&c.chaining),
            hex::encode(&c.m1),
            hex::encode(&c.m2)
        );
        check_both(&c);
        let longer = SfsCollision {
            steps: 21,
            ..c.clone()
        };
        assert!(!verify(&p, &longer));
        assert_ne!(
            sha256_steps_reference(21, &c.chaining, &c.m1),
            sha256_steps_reference(21, &c.chaining, &c.m2)
        );
        // placement start 5: the collision closes after step 13, so one step
        // fewer than 5 + 9 has not yet closed
        let short = SfsCollision {
            steps: 5 + 9 - 1,
            ..c
        };
        assert!(!verify(&p, &short));
        // limit of the method (propagation on five differing words), not a
        // statement about the existence of 21-step pairs
        assert!(sfs_by_local_collision(&p, 21, 1).is_none());
    }

    /// Pair from an independent Python implementation of the register
    /// conditions (reviewer), start 5, differing words {5, 6, 7, 8, 13}.
    const REVIEWER_20_CHAINING: &str =
        "8bb13444f3b871e92443c2524363d203c97d535be124ae770fc6d04aa5975bf7";
    const REVIEWER_20_M1: &str = "128b2f33d23f0824892f902b1818e8115d9dc9f84aa682261606086cc9326ce6c2e52e5bed7ca500dbce7a43aaf3823c33e546de1afd746911e20b8f3d9c1724";
    const REVIEWER_20_M2: &str = "128b2f33d23f0824892f902b1818e8115d9dc9f84aa68227547b22412e4593f5c2e52e5aed7ca500dbce7a43aaf3823c33e546de1afd746811e20b8f3d9c1724";

    #[test]
    fn pinned_reviewer_pair_collides_at_14_to_20_steps_not_21() {
        let p = Sha2Params::sha256();
        for n in 14..=20 {
            check_both(&pair(
                n,
                REVIEWER_20_CHAINING,
                REVIEWER_20_M1,
                REVIEWER_20_M2,
            ));
        }
        let c21 = pair(21, REVIEWER_20_CHAINING, REVIEWER_20_M1, REVIEWER_20_M2);
        assert!(!verify(&p, &c21));
    }

    /// Pair from the previous six-word support code (start 3): collides at 18
    /// steps and not at 19; kept as a regression constant.
    const OLD_18_CHAINING: &str =
        "b5fc2334cf27f2a3aab0bcad941228d723a27752008948d34a0787bb39912229";
    const OLD_18_M1: &str = "eb078f513817dfa17a2c2f8c5a571f851c690d58a4eb18abfa7439d2292afdd1dd98fefc6bd0cf4ed104e83b77d862cac3ecf6f487fce42bb5cf2819a8b76f5f";
    const OLD_18_M2: &str = "eb078f513817dfa17a2c2f8c5a571f86e04110d626213e393a7c31d3292afdd119c0fb7e6bd0cf4ed104e83b77d862c9c3ecf6f487fce42bb5cf2819a8b76f5f";

    #[test]
    fn pinned_six_word_pair_collides_at_18_not_19() {
        let p = Sha2Params::sha256();
        check_both(&pair(18, OLD_18_CHAINING, OLD_18_M1, OLD_18_M2));
        assert!(!verify(
            &p,
            &pair(19, OLD_18_CHAINING, OLD_18_M1, OLD_18_M2)
        ));
        assert!(!verify(
            &p,
            &pair(11, OLD_18_CHAINING, OLD_18_M1, OLD_18_M2)
        ));
    }

    /// The generator's own 20-step output for a fixed seed, pinned.
    #[test]
    fn generator_output_at_20_steps_is_pinned() {
        let p = Sha2Params::sha256();
        let c = sfs_by_local_collision(&p, 20, 120).unwrap();
        assert_eq!(hex::encode(&c.chaining), GEN_20_CHAINING);
        assert_eq!(hex::encode(&c.m1), GEN_20_M1);
        assert_eq!(hex::encode(&c.m2), GEN_20_M2);
    }
    const GEN_20_CHAINING: &str =
        "26954f657e357f5a306e7710eecbd92c04bda899836900baab839cf309c47380";
    const GEN_20_M1: &str = "9d398f9979b05b38c500dd9433d3a8dd6003da5ff81dfbe7978a5ded2e4e51c5cb776cf0ed7ca500dbce7a43aaf3823cdc4d646d41dc754bb69878179a10130e";
    const GEN_20_M2: &str = "9d398f9979b05b38c500dd9433d3a8dd6003da5ff81dfbe829f6df778acf3a3fcb776cefed7ca500dbce7a43aaf3823cdc4d646d41dc754ab69878179a10130e";

    /// `verify` rejects a pair whose messages differ only in words that the
    /// first `n < 16` steps never read.
    #[test]
    fn verify_rejects_differences_in_unread_words() {
        let p = Sha2Params::sha256();
        let c = sfs_by_local_collision(&p, 12, 4).unwrap();
        assert!(verify(&p, &c));
        // same chaining value, messages equal in W_0..W_11 and different in W_15
        let mut m2 = c.m1.clone();
        m2[63] ^= 1;
        let trivial = SfsCollision { m2, ..c.clone() };
        assert_ne!(trivial.m1, trivial.m2);
        assert!(!verify(&p, &trivial));
        // at 16 steps W_15 is read, so the same difference is judged by the IR
        // alone (and does not collide)
        let at16 = SfsCollision {
            steps: 16,
            ..trivial
        };
        assert!(!verify(&p, &at16));
    }

    #[test]
    fn sha512_sfs_collisions_through_the_ir() {
        let p = Sha2Params::sha512();
        for n in [18usize, 20] {
            let c = sfs_by_local_collision(&p, n, 5).unwrap();
            assert!(verify(&p, &c), "n={n}");
            let longer = SfsCollision { steps: n + 1, ..c };
            assert!(!verify(&p, &longer), "n={n} must not collide at n+1");
        }
        assert!(sfs_by_local_collision(&p, 21, 5).is_none());
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

    /// Conditions-guided SAT vs condition propagation. Heavy, run manually:
    /// `cargo test --release --lib sat_vs_condition -- --ignored --nocapture`.
    #[test]
    #[ignore]
    fn sat_vs_condition_propagation_comparison() {
        let p = Sha2Params::sha256();
        for n in [9usize, 10, 12, 14, 16, 18, 20] {
            let t0 = Instant::now();
            let c = sfs_by_local_collision(&p, n, 3).unwrap();
            eprintln!("CP  n={n}: collision in {:?}", t0.elapsed());
            assert!(verify(&p, &c));
        }
        for n in [9usize, 10, 12, 16, 18, 20] {
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

    /// Unguided SAT (chaining value free, messages differing only in words
    /// `W_0..W_{min(n,16)-1}`) for `n = 5..=18`, 1.5M-conflict budget, seed 1.
    /// Heavy, run manually:
    /// `cargo test --release --lib sat_unguided_frontier -- --ignored --nocapture`.
    #[test]
    #[ignore]
    fn sat_unguided_frontier() {
        let p = Sha2Params::sha256();
        for n in 5usize..=18 {
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

    /// SAT positive control: unguided, messages differing only in read words,
    /// 10 steps (61k conflicts when last run, budget 400k); the pair is
    /// checked through the IR and the independent reference.
    #[test]
    fn sat_unguided_n10_through_the_ir() {
        let r = sat_run(10, vec![], None, 400_000);
        assert_eq!(r.status, SolveResult::Sat);
        let c = r.collision.unwrap();
        assert_ne!(c.m1[..40], c.m2[..40], "difference in a read word");
    }

    /// SAT restricted to differences in the words read by `n` steps: for
    /// `n = 1, 2` the solver reports unsatisfiable (no pair).
    #[test]
    fn sat_unguided_small_n_only_counts_read_words() {
        for n in [1usize, 2] {
            let r = sat_run(n, vec![], None, 400_000);
            assert_eq!(r.status, SolveResult::Unsat, "n={n}");
            assert!(r.collision.is_none());
        }
    }

    /// Exploratory, not an assertion: SAT guided by the five-word
    /// local-collision support (start 0, `+1` pinned on `W_0`) at 9 steps with
    /// a 100k-conflict budget; it returned `Unknown` when last run. Run with
    /// `cargo test --release --lib sat_guided_exploratory -- --ignored --nocapture`.
    #[test]
    #[ignore]
    fn sat_guided_exploratory_n9() {
        let r = sat_run(9, equal_words_for_placement(0), Some((0, 0, true)), 100_000);
        eprintln!("guided n=9 status {:?}", r.status);
    }
}
