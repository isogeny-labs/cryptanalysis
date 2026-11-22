//! Probabilistic neutral bits (PNB) key-recovery framework for ChaCha-like
//! primitives.
//!
//! Follows Aumasson, Fischer, Khazaei, Meier and Rechberger, *New Features
//! of Latin Dances: Analysis of Salsa, ChaCha, and Rumba*, FSE 2008
//! (Section 3 and its complexity formula). Given a forward differential-linear
//! distinguisher `(ΔX⁰ = Δ, OD)` on the first `r` rounds of an `R`-round
//! primitive with bias `ε_d`:
//!
//! 1. the **neutrality measure** `γ_i = 2·p_i − 1` of key bit `i` is the
//!    probability `p_i` (over random key, nonce, counter, with the pair
//!    `X, X ⊕ Δ`) that flipping key bit `i` in the *guessed input state*
//!    leaves the OD bit unchanged when the OD bit is recomputed backwards
//!    from the keystream through rounds `R .. r` ([`PnbTarget::neutrality_measures`]);
//! 2. the PNB set is `{ i : γ_i ≥ γ }` for a threshold `γ`
//!    ([`select_pnb`]);
//! 3. with the PNBs set to wrong values and all other key bits right, the
//!    recomputed OD bit agrees with the true one with probability
//!    `½(1 + ε_a)`; the attack bias is `ε* ≈ ε_d · ε_a`
//!    ([`PnbTarget::backward_bias`]; the product is the paper's
//!    approximation, the directly measured `ε*` is reported next to it);
//! 4. the complexity ([`attack_complexity`]) uses the paper's formula
//!    `N = ( √(α ln 4) + 3 √(1 − ε*²) )² / ε*²` pairs and time
//!    `2^{n−m} · N + 2^{n−α}`, where `n` is the key size, `m = |PNB|` and
//!    `2^{-α}` the false-alarm probability; `α` is chosen to minimise the
//!    time (integer grid). The task statement writes the second term as
//!    `2^m`; the paper's second term is `2^{m} · 2^{n−m} · 2^{-α} = 2^{n−α}`
//!    (every surviving candidate costs a `2^m` search of the PNBs), which is
//!    what is implemented. Time is counted in the paper's unit (one
//!    candidate-key test of one pair is one unit, regardless of the number
//!    of rounds inverted).
//!
//! `ε_a` is a sampled quantity (standard error `1/√samples`). A threshold
//! row whose `ε̂_a` is not at least 3 standard errors from zero is noise and
//! is excluded by [`best_significant`]; the sweep still returns it.
//!
//! ## Conventions
//!
//! * The primitive is a key-free ARX permutation with an `AddWords`
//!   feed-forward whose block is the input state (the `sym_ir` ChaCha
//!   description). The key is injected by an *input-block constructor*
//!   `fn(word_bits, &[u64; 8], &[u64; 4]) -> Vec<u8>` (ChaCha:
//!   `chacha::input_block`): the block is `constants (key_word0 words),
//!   key (8 words), counter/nonce (4 words)`.
//! * Key bit `i` (`0 <= i < 8w`) is bit `i % w` of key word `i / w`, which is
//!   state word `key_word0 + i / w` (ChaCha: words 4..11) and block bit
//!   `(key_word0 + i / w) * w + i % w`.
//! * Input differences and output masks are block bit-vectors, as in
//!   [`diff_linear`](super::diff_linear). The input difference must lie in
//!   the counter/nonce words.
//! * `r` counts single rounds (one ChaCha round is a column or a diagonal
//!   round); the distinguisher is observed *before* the feed-forward; the
//!   attacker obtains the pre-feed-forward state at round `R` as
//!   `Z − X̃` (word-wise) from the keystream `Z` and the guessed input `X̃`.
//! * Time is not the wall-clock time of this crate: it is the formula above.

use crate::cryptanalysis::sym_ir::gf2::{get_bits, words_for};
use crate::cryptanalysis::sym_ir::primitives::chacha;
use crate::cryptanalysis::sym_ir::{eval_rounds, Primitive};
use crate::cryptanalysis::sym_techniques::arx::diff_linear::{
    bit_vector, BiasEstimate, DlCandidate, DlTarget,
};
use crate::cryptanalysis::sym_techniques::arx::machine::ArxMachine;
use rand::rngs::SmallRng;
use rand::{Rng, SeedableRng};
use rayon::prelude::*;

const MAXREGS: usize = 16;
type Regs = [u64; MAXREGS];

/// Key-injecting constructor: `(word_bits, key words, counter/nonce words)`
/// to the block bytes.
pub type InputBlockFn = fn(usize, &[u64; 8], &[u64; 4]) -> Vec<u8>;

/// A forward differential-linear distinguisher on `r` rounds.
#[derive(Clone, Debug)]
pub struct Distinguisher {
    /// Rounds covered by the distinguisher.
    pub r: usize,
    /// Input difference (block bit-vector; counter/nonce words only).
    pub in_diff: Vec<u64>,
    /// Output mask (block bit-vector), applied to the state after round `r`.
    pub out_mask: Vec<u64>,
    /// Measured bias `ε_d` (`2·Pr − 1` of the OD event), see
    /// [`BiasEstimate`].
    pub eps_d: f64,
}

/// Row of a threshold sweep.
#[derive(Clone, Debug)]
pub struct PnbRow {
    /// Threshold `γ`.
    pub gamma: f64,
    /// Number of PNBs `m`.
    pub m: usize,
    /// Backward-agreement and direct estimates.
    pub backward: BackwardEstimate,
    /// Complexity from `ε* = ε_d · ε_a` (the paper's formula).
    pub complexity: PnbComplexity,
    /// Complexity from the directly measured `ε*` (no product assumption),
    /// `None` unless the direct estimate is itself significant
    /// ([`PnbRow::significant_direct`]): an ungated direct `ε*` is sampling
    /// noise and its complexity would be meaningless.
    pub complexity_direct: Option<PnbComplexity>,
}

impl PnbRow {
    /// Whether `ε_a` is statistically nonzero (`z >= 3`, `z = ε̂_a √samples`).
    /// Rows below this are noise: their `ε*` (and so the complexity) is
    /// determined by the sampling error, not by the attack.
    pub fn significant(&self) -> bool {
        self.backward.eps_a.z >= 3.0
    }

    /// Whether the directly measured `ε*` is statistically nonzero (`z >= 3`,
    /// the same gate as [`PnbRow::significant`]). Only then is
    /// [`PnbRow::complexity_direct`] filled in.
    pub fn significant_direct(&self) -> bool {
        self.backward.eps_star_direct.z.abs() >= 3.0
    }
}

/// The significant row ([`PnbRow::significant`]) with the smallest
/// `complexity.log2_time`, if any.
pub fn best_significant(rows: &[PnbRow]) -> Option<&PnbRow> {
    rows.iter()
        .filter(|r| r.significant() && r.complexity.log2_time.is_finite())
        .min_by(|a, b| a.complexity.log2_time.total_cmp(&b.complexity.log2_time))
}

/// Result of [`PnbTarget::backward_bias`].
#[derive(Clone, Copy, Debug)]
pub struct BackwardEstimate {
    /// `ε_a`: agreement of the recomputed OD bit with the true one.
    pub eps_a: BiasEstimate,
    /// Bias of the *recomputed* OD bit itself (a direct measurement of
    /// `ε*`, no independence assumption).
    pub eps_star_direct: BiasEstimate,
}

/// Attack complexity from the paper's formula; see the [module docs](self).
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct PnbComplexity {
    /// Key bits `n`.
    pub n: usize,
    /// PNBs `m`.
    pub m: usize,
    /// `ε*` used (absolute value).
    pub eps_star: f64,
    /// Minimising `α` (false-alarm exponent).
    pub alpha: f64,
    /// Data: number of pairs `N` (each pair is two keystream blocks).
    pub pairs: f64,
    /// `log2(N)`.
    pub log2_data_pairs: f64,
    /// `log2` of `2^{n−m} · N`.
    pub log2_phase1: f64,
    /// `log2` of `2^{n−α}`.
    pub log2_phase2: f64,
    /// `log2` of the total time.
    pub log2_time: f64,
    /// Whether the time is below `2^n`.
    pub beats_brute_force: bool,
}

/// `N = (√(α ln 4) + 3 √(1 − ε²))² / ε²` (FSE 2008, Section 3).
pub fn required_pairs(eps_star: f64, alpha: f64) -> f64 {
    let e = eps_star.abs().min(1.0 - 1e-12);
    let a = (alpha * 4f64.ln()).sqrt() + 3.0 * (1.0 - e * e).sqrt();
    a * a / (e * e)
}

fn log2_add(a: f64, b: f64) -> f64 {
    let (hi, lo) = if a >= b { (a, b) } else { (b, a) };
    hi + (1.0 + (lo - hi).exp2()).log2()
}

/// Complexity of a PNB attack on an `n`-bit key with `m` PNBs and attack
/// bias `eps_star`, minimising over the false-alarm exponent `α` on the
/// integer grid `1..=n`. Returns `log2_time = ∞` for `eps_star == 0`.
pub fn attack_complexity(n: usize, m: usize, eps_star: f64) -> PnbComplexity {
    let e = eps_star.abs();
    let mut best = PnbComplexity {
        n,
        m,
        eps_star: e,
        alpha: f64::NAN,
        pairs: f64::INFINITY,
        log2_data_pairs: f64::INFINITY,
        log2_phase1: f64::INFINITY,
        log2_phase2: f64::INFINITY,
        log2_time: f64::INFINITY,
        beats_brute_force: false,
    };
    if e == 0.0 {
        return best;
    }
    for a in 1..=n {
        let alpha = a as f64;
        let pairs = required_pairs(e, alpha);
        let p1 = (n - m) as f64 + pairs.log2();
        let p2 = (n as f64) - alpha;
        let t = log2_add(p1, p2);
        if t < best.log2_time {
            best = PnbComplexity {
                n,
                m,
                eps_star: e,
                alpha,
                pairs,
                log2_data_pairs: pairs.log2(),
                log2_phase1: p1,
                log2_phase2: p2,
                log2_time: t,
                beats_brute_force: t < n as f64,
            };
        }
    }
    best
}

/// PNB set: key bits with neutrality measure `>= gamma`.
pub fn select_pnb(gammas: &[f64], gamma: f64) -> Vec<usize> {
    (0..gammas.len()).filter(|&i| gammas[i] >= gamma).collect()
}

/// A ChaCha-like primitive prepared for PNB analysis.
pub struct PnbTarget<'a> {
    prim: &'a Primitive,
    machine: ArxMachine,
    /// Word width `w`.
    pub word_bits: usize,
    input_block: InputBlockFn,
    /// State index of the first key word (4 for ChaCha).
    pub key_word0: usize,
    /// Number of key words (8 for ChaCha).
    pub key_words: usize,
    template: Regs,
}

impl<'a> PnbTarget<'a> {
    /// `prim` is the full `R`-round primitive; `input_block` injects the key.
    /// Panics if the primitive is not a compilable, invertible ARX
    /// permutation with at most 16 registers, or if `input_block` does not
    /// lay the words out as `constants, key, counter/nonce`.
    pub fn new(
        prim: &'a Primitive,
        input_block: InputBlockFn,
        key_word0: usize,
        key_words: usize,
    ) -> Self {
        let machine =
            ArxMachine::compile(prim).expect("PNB target must be a key-free ARX permutation");
        assert!(machine.is_invertible() && machine.regs <= MAXREGS);
        assert_eq!(machine.regs, machine.block_regs);
        assert_eq!(key_word0 + key_words + 4, machine.block_regs);
        let w = machine.word_bits;
        let mut t = Self {
            prim,
            machine,
            word_bits: w,
            input_block,
            key_word0,
            key_words,
            template: [0; MAXREGS],
        };
        let zero = t.load_block(&[0; 8], &[0; 4]);
        t.template = zero;
        // consistency check of the assumed layout
        let (k, nn) = ([1, 2, 3, 4, 5, 6, 7, 8u64], [9, 10, 11, 12u64]);
        assert_eq!(
            t.assemble(&k, &nn),
            t.load_block(&k, &nn),
            "input_block layout"
        );
        t
    }

    /// ChaCha (`chacha::input_block`, key = state words 4..11).
    pub fn chacha(prim: &'a Primitive) -> Self {
        let w = prim.block_codec.word_bits;
        assert_eq!(prim.block_bits, 16 * w);
        let t = Self::new(prim, chacha::input_block, 4, 8);
        assert_eq!(t.word_bits, w);
        t
    }

    fn load_block(&self, key: &[u64; 8], nonce: &[u64; 4]) -> Regs {
        let bytes = (self.input_block)(self.word_bits, key, nonce);
        let v = self.machine.load(&bytes);
        let mut r = [0u64; MAXREGS];
        r[..v.len()].copy_from_slice(&v);
        r
    }

    fn assemble(&self, key: &[u64; 8], nonce: &[u64; 4]) -> Regs {
        let mut r = self.template;
        let m = self.mask();
        for (i, &k) in key.iter().enumerate().take(self.key_words) {
            r[self.key_word0 + i] = k & m;
        }
        for (j, &v) in nonce.iter().enumerate() {
            r[self.key_word0 + self.key_words + j] = v & m;
        }
        r
    }

    fn mask(&self) -> u64 {
        (1u64 << self.word_bits) - 1
    }

    /// Key size `n` in bits.
    pub fn key_bits(&self) -> usize {
        self.key_words * self.word_bits
    }

    /// Total rounds `R`.
    pub fn total_rounds(&self) -> usize {
        self.machine.num_rounds()
    }

    fn regs_of(&self, v: &[u64]) -> Regs {
        let mut r = [0u64; MAXREGS];
        for (j, x) in r.iter_mut().enumerate().take(self.machine.block_regs) {
            *x = get_bits(v, j * self.word_bits, self.word_bits);
        }
        r
    }

    fn random_key_nonce(&self, rng: &mut SmallRng) -> ([u64; 8], [u64; 4]) {
        let m = self.mask();
        let mut k = [0u64; 8];
        k.iter_mut().for_each(|x| *x = rng.gen::<u64>() & m);
        let mut nn = [0u64; 4];
        nn.iter_mut().for_each(|x| *x = rng.gen::<u64>() & m);
        (k, nn)
    }

    fn flip_key_bit(&self, x: &mut Regs, i: usize) {
        x[self.key_word0 + i / self.word_bits] ^= 1u64 << (i % self.word_bits);
    }

    /// Measure `ε_d` for `(in_diff, out_mask)` after `r` rounds (random key
    /// and counter/nonce, constants fixed, state before feed-forward) with
    /// `samples` pairs.
    pub fn measure_eps_d(
        &self,
        r: usize,
        in_diff: &[u64],
        out_mask: &[u64],
        samples: u64,
        seed: u64,
    ) -> BiasEstimate {
        self.dl_target(r)
            .estimate_bias(in_diff, out_mask, samples, seed)
    }

    /// The differential-linear sampling target matching this PNB target
    /// (constants fixed).
    pub fn dl_target(&self, r: usize) -> DlTarget<'a> {
        let consts: Vec<(usize, u64)> =
            (0..self.key_word0).map(|j| (j, self.template[j])).collect();
        DlTarget::new(self.prim, r).with_fixed_words(&consts)
    }

    /// Build a [`Distinguisher`] measuring `ε_d` with `samples` pairs.
    pub fn distinguisher(
        &self,
        r: usize,
        in_diff: Vec<u64>,
        out_mask: Vec<u64>,
        samples: u64,
        seed: u64,
    ) -> (Distinguisher, BiasEstimate) {
        for b in 0..self.key_word0 * self.word_bits {
            assert!(
                in_diff[b / 64] >> (b % 64) & 1 == 0,
                "difference in constants"
            );
        }
        let kb = self.key_word0 * self.word_bits;
        for b in kb..kb + self.key_bits() {
            assert!(
                in_diff[b / 64] >> (b % 64) & 1 == 0,
                "difference in key bits"
            );
        }
        let est = self.measure_eps_d(r, &in_diff, &out_mask, samples, seed);
        (
            Distinguisher {
                r,
                in_diff,
                out_mask,
                eps_d: est.eps,
            },
            est,
        )
    }

    /// Search single-bit differences `in_bits` (counter/nonce words) times
    /// all single-bit output masks after `r` rounds
    /// ([`DlTarget::search_single_bit`]) and return the best candidate as a
    /// [`Distinguisher`] whose `eps_d` is the fresh-sample (unbiased)
    /// re-estimate, together with that candidate.
    pub fn find_distinguisher(
        &self,
        r: usize,
        in_bits: &[usize],
        n_search: u64,
        top_k: usize,
        n_confirm: u64,
        seed: u64,
    ) -> (Distinguisher, DlCandidate) {
        let cands = self
            .dl_target(r)
            .search_single_bit(in_bits, n_search, top_k, n_confirm, seed);
        let c = cands[0];
        let nb = self.prim.block_bits;
        let d = Distinguisher {
            r,
            in_diff: bit_vector(nb, &[c.in_bit]),
            out_mask: bit_vector(nb, &[c.out_bit]),
            eps_d: c.confirm.eps,
        };
        (d, c)
    }

    fn od(&self, d: &RegDist, a: &Regs, b: &Regs) -> u64 {
        let n = self.machine.block_regs;
        let p: u32 = (0..n)
            .map(|j| (d.mask[j] & (a[j] ^ b[j])).count_ones())
            .sum();
        (p & 1) as u64
    }

    /// Keystream pair for the base states `x` and `x ⊕ Δ`, plus the true
    /// round-`r` OD bit.
    fn keystream_pair(&self, d: &RegDist, r: usize, x: &Regs) -> (Regs, Regs, u64) {
        let big_r = self.machine.num_rounds();
        let mut xp = *x;
        xp.iter_mut().zip(&d.diff).for_each(|(a, b)| *a ^= b);
        let (mut a, mut b) = (*x, xp);
        let nr = self.machine.regs;
        self.machine.forward(&mut a[..nr], 0, r);
        self.machine.forward(&mut b[..nr], 0, r);
        let od = self.od(d, &a, &b);
        self.machine.forward(&mut a[..nr], r, big_r);
        self.machine.forward(&mut b[..nr], r, big_r);
        self.machine.add_feed_forward(&mut a[..nr], &x[..nr]);
        self.machine.add_feed_forward(&mut b[..nr], &xp[..nr]);
        (a, b, od)
    }

    /// Recomputed OD bit from keystream `(z, zp)` and guessed base state
    /// `xg` (the guessed `X̃`; the partner is `X̃ ⊕ Δ`).
    fn backward_od(&self, d: &RegDist, r: usize, z: &Regs, zp: &Regs, xg: &Regs) -> u64 {
        let nr = self.machine.regs;
        let mut a = *z;
        let mut b = *zp;
        let mut xgp = *xg;
        xgp.iter_mut().zip(&d.diff).for_each(|(a, b)| *a ^= b);
        self.machine.sub_feed_forward(&mut a[..nr], &xg[..nr]);
        self.machine.sub_feed_forward(&mut b[..nr], &xgp[..nr]);
        self.machine
            .backward(&mut a[..nr], self.machine.num_rounds(), r);
        self.machine
            .backward(&mut b[..nr], self.machine.num_rounds(), r);
        self.od(d, &a, &b)
    }

    /// Neutrality measure `γ_i` of every key bit (see the module docs) from
    /// `samples` random (key, counter/nonce, pair) draws.
    pub fn neutrality_measures(&self, dist: &Distinguisher, samples: u64, seed: u64) -> Vec<f64> {
        let d = RegDist::new(self, dist);
        let n = self.key_bits();
        let chunk = 1u64 << 10;
        let agree: Vec<u64> = (0..samples.div_ceil(chunk))
            .into_par_iter()
            .map(|c| {
                let mut rng = SmallRng::seed_from_u64(seed ^ c.wrapping_mul(0x9E37_79B9_7F4A_7C15));
                let mut cnt = vec![0u64; n];
                for _ in 0..chunk.min(samples - c * chunk) {
                    let (k, nn) = self.random_key_nonce(&mut rng);
                    let x = self.assemble(&k, &nn);
                    let (z, zp, od) = self.keystream_pair(&d, dist.r, &x);
                    for (i, c) in cnt.iter_mut().enumerate() {
                        let mut xg = x;
                        self.flip_key_bit(&mut xg, i);
                        *c += (self.backward_od(&d, dist.r, &z, &zp, &xg) == od) as u64;
                    }
                }
                cnt
            })
            .reduce(
                || vec![0u64; n],
                |mut a, b| {
                    a.iter_mut().zip(b).for_each(|(x, y)| *x += y);
                    a
                },
            );
        agree
            .iter()
            .map(|&a| 2.0 * a as f64 / samples as f64 - 1.0)
            .collect()
    }

    /// Estimate `ε_a` (and the direct `ε*`) for the PNB set `pnb`: all other
    /// key bits right, PNBs replaced by uniformly random values.
    pub fn backward_bias(
        &self,
        dist: &Distinguisher,
        pnb: &[usize],
        samples: u64,
        seed: u64,
    ) -> BackwardEstimate {
        let d = RegDist::new(self, dist);
        let chunk = 1u64 << 12;
        let (agree, ones) = (0..samples.div_ceil(chunk))
            .into_par_iter()
            .map(|c| {
                let mut rng = SmallRng::seed_from_u64(seed ^ c.wrapping_mul(0x9E37_79B9_7F4A_7C15));
                let (mut ag, mut on) = (0u64, 0u64);
                for _ in 0..chunk.min(samples - c * chunk) {
                    let (k, nn) = self.random_key_nonce(&mut rng);
                    let x = self.assemble(&k, &nn);
                    let (z, zp, od) = self.keystream_pair(&d, dist.r, &x);
                    let mut xg = x;
                    for &i in pnb {
                        if rng.gen::<bool>() {
                            self.flip_key_bit(&mut xg, i);
                        }
                    }
                    let g = self.backward_od(&d, dist.r, &z, &zp, &xg);
                    ag += (g == od) as u64;
                    on += g;
                }
                (ag, on)
            })
            .reduce(|| (0, 0), |a, b| (a.0 + b.0, a.1 + b.1));
        BackwardEstimate {
            eps_a: BiasEstimate::from_counts(samples, agree),
            eps_star_direct: BiasEstimate::from_counts(samples, ones),
        }
    }

    /// Sweep thresholds: for each `γ` select the PNBs, estimate the backward
    /// bias with `samples` draws and compute the complexity from
    /// `ε* = ε_d · ε_a`.
    pub fn sweep(
        &self,
        dist: &Distinguisher,
        gammas_measured: &[f64],
        thresholds: &[f64],
        samples: u64,
        seed: u64,
    ) -> Vec<PnbRow> {
        let n = self.key_bits();
        thresholds
            .iter()
            .map(|&g| {
                let pnb = select_pnb(gammas_measured, g);
                let b = self.backward_bias(dist, &pnb, samples, seed);
                let eps_star = dist.eps_d * b.eps_a.eps;
                let direct_ok = b.eps_star_direct.z.abs() >= 3.0;
                PnbRow {
                    gamma: g,
                    m: pnb.len(),
                    backward: b,
                    complexity: attack_complexity(n, pnb.len(), eps_star),
                    complexity_direct: direct_ok
                        .then(|| attack_complexity(n, pnb.len(), b.eps_star_direct.eps)),
                }
            })
            .collect()
    }

    /// Run the attack end to end on a **key-space-reduced instance**.
    ///
    /// Data: `pairs` random counter/nonce pairs `(X, X ⊕ Δ)` are encrypted
    /// through the IR ([`eval_rounds`] with the full `R` rounds and
    /// feed-forward) under `true_key`. The attacker knows every key bit
    /// outside `unknown` (taken from `true_key`); phase 1 enumerates all
    /// assignments of `unknown \ pnb`, scoring each by `|Σ (-1)^{OD}|` of
    /// the recomputed OD bit, PNB bits inside `unknown` fixed to 0; phase 2
    /// takes the `top` best-scoring assignments, enumerates the
    /// `unknown ∩ pnb` bits and accepts a full key that reproduces the first
    /// keystream block. Cost: `2^{|unknown \ pnb|} · pairs` backward
    /// evaluations plus `top · 2^{|unknown ∩ pnb|}` block evaluations.
    #[allow(clippy::too_many_arguments)]
    pub fn recover_key(
        &self,
        dist: &Distinguisher,
        pnb: &[usize],
        unknown: &[usize],
        true_key: &[u64; 8],
        pairs: usize,
        top: usize,
        seed: u64,
    ) -> KeyRecoveryResult {
        let d = RegDist::new(self, dist);
        let w = self.word_bits;
        let mut rng = SmallRng::seed_from_u64(seed);
        let r = dist.r;
        let is_pnb = |i: usize| pnb.contains(&i);
        let u_np: Vec<usize> = unknown.iter().copied().filter(|&i| !is_pnb(i)).collect();
        let u_p: Vec<usize> = unknown.iter().copied().filter(|&i| is_pnb(i)).collect();
        assert!(u_np.len() <= 28 && u_p.len() <= 28);

        // data through the IR
        struct Pair {
            x: Regs,
            z: Regs,
            zp: Regs,
        }
        let m = self.mask();
        let data: Vec<Pair> = (0..pairs)
            .map(|_| {
                let nn = [(); 4].map(|_| rng.gen::<u64>() & m);
                let x = self.assemble(true_key, &nn);
                let xb = self.machine.store(&x[..self.machine.regs]);
                let mut xpb = xb.clone();
                for (b, byte) in xpb.iter_mut().enumerate() {
                    for bit in 0..8 {
                        let pos = b * 8 + bit;
                        if dist.in_diff[pos / 64] >> (pos % 64) & 1 == 1 {
                            *byte ^= 1 << bit;
                        }
                    }
                }
                let z =
                    self.machine
                        .load(&eval_rounds(self.prim, &[], &xb, self.prim.num_rounds()));
                let zp =
                    self.machine
                        .load(&eval_rounds(self.prim, &[], &xpb, self.prim.num_rounds()));
                let (mut zr, mut zpr) = ([0u64; MAXREGS], [0u64; MAXREGS]);
                zr[..z.len()].copy_from_slice(&z);
                zpr[..z.len()].copy_from_slice(&zp);
                Pair { x, z: zr, zp: zpr }
            })
            .collect();

        let set_bits_of = |base: &Regs, bits: &[usize], val: u64| -> Regs {
            let mut x = *base;
            for (j, &i) in bits.iter().enumerate() {
                let (wd, bt) = (self.key_word0 + i / w, i % w);
                x[wd] = (x[wd] & !(1u64 << bt)) | (((val >> j) & 1) << bt);
            }
            x
        };
        // attacker's base key: true bits outside `unknown`, zeros inside.
        let mut base_key = *true_key;
        for &i in unknown {
            base_key[i / w] &= !(1u64 << (i % w));
        }
        let base = self.assemble(&base_key, &[0; 4]);

        let truth_np: u64 = u_np
            .iter()
            .enumerate()
            .map(|(j, &i)| ((true_key[i / w] >> (i % w)) & 1) << j)
            .sum();
        let total = 1u64 << u_np.len();
        let score = |g: u64| -> i64 {
            let kx = set_bits_of(&base, &u_np, g);
            let mut s = 0i64;
            for p in &data {
                let mut xg = kx;
                for j in 0..4 {
                    xg[self.key_word0 + self.key_words + j] =
                        p.x[self.key_word0 + self.key_words + j];
                }
                s += 1 - 2 * self.backward_od(&d, r, &p.z, &p.zp, &xg) as i64;
            }
            s.abs()
        };
        let mut scores: Vec<(i64, u64)> = (0..total.div_ceil(1 << 12))
            .into_par_iter()
            .flat_map_iter(|c| {
                let lo = c << 12;
                let hi = (lo + (1 << 12)).min(total);
                let mut local: Vec<(i64, u64)> = (lo..hi).map(|g| (score(g), g)).collect();
                local.sort_by(|a, b| b.cmp(a));
                local.truncate(top.max(1) + 64);
                local
            })
            .collect();
        scores.sort_by(|a, b| b.cmp(a));
        let true_score = score(truth_np);
        let true_rank = scores.iter().position(|&(_, g)| g == truth_np);

        // phase 2: brute-force the PNB-unknown bits against the keystream
        let mut recovered = None;
        let p0 = &data[0];
        let mut trials = 0u64;
        'outer: for &(_, g) in scores.iter().take(top) {
            let kx = set_bits_of(&base, &u_np, g);
            for h in 0..(1u64 << u_p.len()) {
                trials += 1;
                let mut cand = set_bits_of(&kx, &u_p, h);
                for j in 0..4 {
                    cand[self.key_word0 + self.key_words + j] =
                        p0.x[self.key_word0 + self.key_words + j];
                }
                let nr = self.machine.regs;
                let mut s = cand;
                self.machine
                    .forward(&mut s[..nr], 0, self.machine.num_rounds());
                self.machine.add_feed_forward(&mut s[..nr], &cand[..nr]);
                if s[..nr] == p0.z[..nr] {
                    let mut key = [0u64; 8];
                    for (i, k) in key.iter_mut().enumerate().take(self.key_words) {
                        *k = cand[self.key_word0 + i];
                    }
                    recovered = Some(key);
                    break 'outer;
                }
            }
        }
        KeyRecoveryResult {
            recovered,
            unknown_bits: unknown.len(),
            phase1_guesses: total,
            pairs,
            true_score: true_score as f64 / pairs as f64,
            true_rank,
            top_score: scores.first().map_or(0.0, |s| s.0 as f64 / pairs as f64),
            phase2_trials: trials,
        }
    }
}

/// Outcome of [`PnbTarget::recover_key`].
#[derive(Clone, Debug)]
pub struct KeyRecoveryResult {
    /// The recovered key words, if phase 2 accepted a candidate.
    pub recovered: Option<[u64; 8]>,
    /// Number of unknown key bits in the instance.
    pub unknown_bits: usize,
    /// Phase-1 guesses `2^{|unknown \ pnb|}`.
    pub phase1_guesses: u64,
    /// Pairs used.
    pub pairs: usize,
    /// `|score| / pairs` of the true assignment (an estimate of `|ε*|`).
    pub true_score: f64,
    /// Rank (0 = best) of the true assignment if it is among the kept best
    /// phase-1 scores (`top + 64` per chunk), else `None`.
    pub true_rank: Option<usize>,
    /// Best `|score| / pairs` over all guesses.
    pub top_score: f64,
    /// Candidate keys tested in phase 2.
    pub phase2_trials: u64,
}

/// Distinguisher converted to register vectors.
struct RegDist {
    diff: Regs,
    mask: Regs,
}

impl RegDist {
    fn new(t: &PnbTarget<'_>, d: &Distinguisher) -> Self {
        assert!(d.r <= t.machine.num_rounds());
        assert_eq!(d.in_diff.len(), words_for(t.prim.block_bits));
        RegDist {
            diff: t.regs_of(&d.in_diff),
            mask: t.regs_of(&d.out_mask),
        }
    }
}
