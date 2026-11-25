//! Differential-linear distinguishers, `xdp+`, and the correlation of
//! modular addition.
//!
//! # Differential-linear distinguishers
//!
//! A one-sided differential-linear (DL) distinguisher on `r` rounds of a
//! primitive `F` is a pair (input difference `Δ`, output mask `λ`) with
//! `Pr_x[ λ · (F(x) ⊕ F(x ⊕ Δ)) = 1 ] = ½(1 + ε)`; `ε` is the **bias**
//! reported here as [`BiasEstimate::eps`] (`ε = 2·p₁ − 1`, so `ε` is the
//! *correlation* of the event, and `p₁ − ½ = ε/2`). This is the `ε_d`
//! convention of Aumasson, Fischer, Khazaei, Meier and Rechberger, *New
//! Features of Latin Dances*, FSE 2008. Under the null hypothesis (no bias)
//! `ε̂ · √N` is approximately standard normal, which is the `z` reported.
//! [`DlTarget::estimate_bias`] measures one pair by sampling;
//! [`DlTarget::search_single_bit`] scans single-bit differences times
//! single-bit masks (the standard first step, ibid.; Langford–Hellman 1994
//! for the differential-linear idea).
//!
//! ## Indexing conventions
//!
//! * Differences and masks are GF(2) bit-vectors over the **block**
//!   (`sym_ir::gf2` convention: bit `i` is bit `i % 64` of word `i / 64`),
//!   and block bit `i` is state bit `i` of the primitive. For the ChaCha
//!   primitives, state bit `i` is bit `i % w` of state word `i / w` with the
//!   RFC 8439 word numbering (`x0..x3` constants, `x4..x11` key,
//!   `x12..x15` counter and nonce), so "bit 13 of word 13" is block bit
//!   `13 * w + 13`.
//! * Samples: the block is uniform except bits fixed with
//!   [`DlTarget::with_fixed_words`] (use it to pin the ChaCha constants).
//!   A primitive with a key gets a fresh uniform key per sample, shared by
//!   the two members of the pair.
//! * "`r` rounds" means [`eval_rounds`]
//!   with `n = r`. For a primitive with a feed-forward (ChaCha) the default
//!   is to observe the state **before** the feed-forward (the permutation
//!   output, which is what the published ChaCha distinguishers use); set
//!   [`DlTarget::with_feed_forward`] to observe the real output.
//! * Sample budgets are explicit; sampling is deterministic given the seed
//!   (chunked, one derived seed per chunk), independent of thread count.
//!
//! Searching many candidates and reporting the best is biased upward; the
//! search therefore re-estimates its top candidates with fresh samples and
//! reports both numbers.
//!
//! # `xdp+` and the correlation of addition
//!
//! * [`xdp_add`]: the differential probability of `z = x + y mod 2^w` for
//!   XOR differences `(α, β) → γ`, by the closed form of Lipmaa and Moriai
//!   (FSE 2001, Theorem 2), with [`xdp_add_brute`] as the exhaustive
//!   reference.
//! * [`lin_corr_add`]: the correlation
//!   `2^{-2w} Σ_{x,y} (-1)^{u·z ⊕ v·x ⊕ t·y}` of the same addition, computed
//!   exactly by the carry-state transducer of Wallén (FSE 2003) as used by
//!   Nyberg and Wallén (2006): one 2×2 integer matrix per bit position,
//!   indexed by the carry. [`lin_corr_add_brute`] is the exhaustive
//!   reference.

use crate::cryptanalysis::sym_ir::gf2::{get_bits, set_bits, words_for};
use crate::cryptanalysis::sym_ir::{eval_rounds, FeedForward, Primitive};
use crate::cryptanalysis::sym_techniques::arx::machine::ArxMachine;
use rand::rngs::SmallRng;
use rand::{Rng, SeedableRng};
use rayon::prelude::*;

// ---------------------------------------------------------------------------
// xdp+ and the correlation of addition
// ---------------------------------------------------------------------------

fn mask_w(w: usize) -> u64 {
    if w >= 64 {
        u64::MAX
    } else {
        (1u64 << w) - 1
    }
}

/// `xdp+(α, β → γ)`: probability over uniform `x, y` in `Z_2^w` that
/// `((x ⊕ α) + (y ⊕ β)) ⊕ (x + y) = γ` (all sums modulo `2^w`), by the
/// Lipmaa–Moriai closed form: zero if
/// `eq(α<<1, β<<1, γ<<1) & (α ⊕ β ⊕ γ ⊕ (β<<1)) ≠ 0`, otherwise
/// `2^{-wt(¬eq(α,β,γ) & mask_{w-1})}` where `eq(x,y,z)` is 1 exactly where
/// the three bits agree. Inputs are taken modulo `2^w` (`w <= 64`).
pub fn xdp_add(w: usize, alpha: u64, beta: u64, gamma: u64) -> f64 {
    let m = mask_w(w);
    let (a, b, g) = (alpha & m, beta & m, gamma & m);
    let eq = |x: u64, y: u64, z: u64| !(x ^ y) & !(x ^ z) & m;
    let (a1, b1, g1) = ((a << 1) & m, (b << 1) & m, (g << 1) & m);
    if eq(a1, b1, g1) & (a ^ b ^ g ^ b1) & m != 0 {
        return 0.0;
    }
    let wt = (!eq(a, b, g) & mask_w(w - 1)).count_ones();
    0.5f64.powi(wt as i32)
}

/// Exhaustive `xdp+` for `w <= 12`: `#{(x,y)} / 2^{2w}` as an exact
/// `(count, 2w)` pair is returned as the `f64` ratio.
pub fn xdp_add_brute(w: usize, alpha: u64, beta: u64, gamma: u64) -> f64 {
    assert!(w <= 12);
    let m = mask_w(w);
    let mut cnt = 0u64;
    for x in 0..=m {
        for y in 0..=m {
            let d = (((x ^ alpha) + (y ^ beta)) & m) ^ ((x + y) & m);
            cnt += (d == gamma & m) as u64;
        }
    }
    cnt as f64 / (1u64 << (2 * w)) as f64
}

/// Exact correlation of modular addition:
/// `2^{-2w} Σ_{x,y ∈ Z_2^w} (-1)^{u·(x+y) ⊕ v·x ⊕ t·y}` (`u` masks the sum,
/// `v` and `t` the addends; `w <= 63`), by the carry transducer of Wallén
/// (2003). The value is `0` or `±2^{-k}` for an integer `k`.
pub fn lin_corr_add(w: usize, u: u64, v: u64, t: u64) -> f64 {
    assert!(w <= 63);
    // vec[c] = signed count of the processed prefix ending with carry c.
    let mut vec = [1i128, 0i128];
    for i in 0..w {
        let (ui, vi, ti) = ((u >> i) & 1, (v >> i) & 1, (t >> i) & 1);
        let mut next = [0i128, 0i128];
        for (c, &cnt) in vec.iter().enumerate() {
            if cnt == 0 {
                continue;
            }
            for x in 0..2u64 {
                for y in 0..2u64 {
                    let s = x ^ y ^ c as u64;
                    let cn = ((x & y) | (x & c as u64) | (y & c as u64)) as usize;
                    let sign = if (ui & s) ^ (vi & x) ^ (ti & y) == 1 {
                        -1
                    } else {
                        1
                    };
                    next[cn] += sign * cnt;
                }
            }
        }
        vec = next;
    }
    (vec[0] + vec[1]) as f64 * 0.5f64.powi(2 * w as i32)
}

/// Exhaustive reference for [`lin_corr_add`] (`w <= 12`).
pub fn lin_corr_add_brute(w: usize, u: u64, v: u64, t: u64) -> f64 {
    assert!(w <= 12);
    let m = mask_w(w);
    let mut acc = 0i64;
    for x in 0..=m {
        for y in 0..=m {
            let par = ((u & ((x + y) & m)) ^ (v & x) ^ (t & y)).count_ones() & 1;
            acc += if par == 1 { -1 } else { 1 };
        }
    }
    acc as f64 / (1u64 << (2 * w)) as f64
}

// ---------------------------------------------------------------------------
// Empirical differential-linear bias
// ---------------------------------------------------------------------------

/// Result of sampling one (difference, mask) pair.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct BiasEstimate {
    /// Number of samples (pairs).
    pub samples: u64,
    /// Samples with `λ · ΔOut = 1`.
    pub ones: u64,
    /// `ones / samples`.
    pub p1: f64,
    /// `ε̂ = 2·p1 − 1` (see the [module docs](self)).
    pub eps: f64,
    /// `ε̂ · √samples`: standard-normal under the null `ε = 0`.
    pub z: f64,
}

impl BiasEstimate {
    pub(crate) fn from_counts(samples: u64, ones: u64) -> Self {
        let p1 = ones as f64 / samples as f64;
        let eps = 2.0 * p1 - 1.0;
        BiasEstimate {
            samples,
            ones,
            p1,
            eps,
            z: eps * (samples as f64).sqrt(),
        }
    }

    /// Standard error of `eps` at the observed `p1` (binomial).
    pub fn eps_std_err(&self) -> f64 {
        2.0 * (self.p1 * (1.0 - self.p1) / self.samples as f64).sqrt()
    }
}

/// One entry of a [`DlTarget::search_single_bit`] result.
#[derive(Clone, Copy, Debug)]
pub struct DlCandidate {
    /// Block bit flipped in the input difference.
    pub in_bit: usize,
    /// Block bit observed in the output difference.
    pub out_bit: usize,
    /// Estimate from the search phase (selected as the maximum: biased up).
    pub search: BiasEstimate,
    /// Fresh-sample re-estimate (unbiased).
    pub confirm: BiasEstimate,
}

/// One entry of a [`DlTarget::search_two_bit_masks`] result.
#[derive(Clone, Copy, Debug)]
pub struct DlPairCandidate {
    /// Block bit flipped in the input difference.
    pub in_bit: usize,
    /// The two output block bits whose XOR is the mask (`u < v`).
    pub out_bits: (usize, usize),
    /// Search-phase estimate (selected as the maximum: biased up).
    pub search: BiasEstimate,
    /// Fresh-sample re-estimate (unbiased).
    pub confirm: BiasEstimate,
}

/// An `r`-round view of a primitive for differential-linear sampling; see
/// the [module docs](self).
pub struct DlTarget<'a> {
    prim: &'a Primitive,
    rounds: usize,
    with_ff: bool,
    fixed_mask: Vec<u64>,
    fixed_val: Vec<u64>,
    machine: Option<ArxMachine>,
}

const CHUNK: u64 = 1 << 12;

impl<'a> DlTarget<'a> {
    /// `rounds` rounds of `prim`, observing the state before the
    /// feed-forward, uniform random blocks. Uses the compiled evaluator when
    /// `prim` is a key-free ARX primitive, [`eval_rounds`] otherwise.
    pub fn new(prim: &'a Primitive, rounds: usize) -> Self {
        assert!(rounds <= prim.num_rounds());
        let machine = if prim.key_bits == 0 {
            ArxMachine::compile(prim).ok()
        } else {
            None
        };
        let n = words_for(prim.block_bits);
        DlTarget {
            prim,
            rounds,
            with_ff: false,
            fixed_mask: vec![0; n],
            fixed_val: vec![0; n],
            machine,
        }
    }

    /// Observe the real output (after the feed-forward) instead.
    pub fn with_feed_forward(mut self, yes: bool) -> Self {
        self.with_ff = yes;
        self
    }

    /// Pin whole block words (of the block codec's word width) to values,
    /// e.g. the ChaCha constants: `(word index, value)`.
    pub fn with_fixed_words(mut self, words: &[(usize, u64)]) -> Self {
        let w = self.prim.block_codec.word_bits;
        for &(j, v) in words {
            set_bits(&mut self.fixed_mask, j * w, w, mask_w(w));
            set_bits(&mut self.fixed_val, j * w, w, v);
        }
        self
    }

    /// Number of block bits.
    pub fn block_bits(&self) -> usize {
        self.prim.block_bits
    }

    /// Whether the compiled evaluator is in use (otherwise [`eval_rounds`]).
    pub fn uses_compiled_evaluator(&self) -> bool {
        self.machine.is_some()
    }

    fn sample_block(&self, rng: &mut SmallRng) -> Vec<u64> {
        let n = self.fixed_mask.len();
        let mut b: Vec<u64> = (0..n)
            .map(|i| (rng.gen::<u64>() & !self.fixed_mask[i]) | self.fixed_val[i])
            .collect();
        let rem = self.prim.block_bits % 64;
        if rem != 0 {
            b[n - 1] &= (1u64 << rem) - 1;
        }
        b
    }

    /// Output difference (bit-vector over the block) of one random pair.
    fn pair_diff(&self, rng: &mut SmallRng, in_diff: &[u64], out: &mut [u64]) {
        let x = self.sample_block(rng);
        let y: Vec<u64> = x.iter().zip(in_diff).map(|(a, b)| a ^ b).collect();
        if let Some(mc) = &self.machine {
            let w = mc.word_bits;
            let run = |blk: &[u64]| -> Vec<u64> {
                let mut st = vec![0u64; mc.regs];
                for (j, s) in st.iter_mut().enumerate().take(mc.block_regs) {
                    *s = get_bits(blk, j * w, w);
                }
                let init = st.clone();
                mc.forward(&mut st, 0, self.rounds);
                if self.with_ff {
                    mc.add_feed_forward(&mut st, &init);
                }
                st
            };
            let (a, b) = (run(&x), run(&y));
            out.iter_mut().for_each(|o| *o = 0);
            for j in 0..mc.block_regs {
                set_bits(out, j * w, w, a[j] ^ b[j]);
            }
        } else {
            let p = self.prim;
            let key: Vec<u8> = (0..p.key_bytes()).map(|_| rng.gen()).collect();
            let run = |blk: &[u64]| -> Vec<u64> {
                let bytes = p.block_codec.decode(blk, p.block_bits);
                let o = eval_rounds(p, &key, &bytes, self.rounds);
                let mut ov = p.block_codec.encode(&o);
                if !self.with_ff {
                    // undo the feed-forward to expose the permutation output
                    match p.feed_forward {
                        FeedForward::None => {}
                        FeedForward::Xor => ov.iter_mut().zip(blk).for_each(|(a, b)| *a ^= b),
                        FeedForward::AddWords { word_bits: w } => {
                            for j in 0..p.block_bits / w {
                                let v =
                                    get_bits(&ov, j * w, w).wrapping_sub(get_bits(blk, j * w, w))
                                        & mask_w(w);
                                set_bits(&mut ov, j * w, w, v);
                            }
                        }
                    }
                }
                ov
            };
            let (a, b) = (run(&x), run(&y));
            for (o, (u, v)) in out.iter_mut().zip(a.iter().zip(&b)) {
                *o = u ^ v;
            }
        }
    }

    fn chunk_rng(seed: u64, chunk: u64) -> SmallRng {
        SmallRng::seed_from_u64(seed ^ chunk.wrapping_mul(0x9E37_79B9_7F4A_7C15).rotate_left(17))
    }

    /// Estimate the bias of `mask · ΔOut` for input difference `in_diff`
    /// with `samples` random pairs (both bit-vectors over the block).
    pub fn estimate_bias(
        &self,
        in_diff: &[u64],
        out_mask: &[u64],
        samples: u64,
        seed: u64,
    ) -> BiasEstimate {
        let nchunks = samples.div_ceil(CHUNK);
        let ones: u64 = (0..nchunks)
            .into_par_iter()
            .map(|c| {
                let cnt = CHUNK.min(samples - c * CHUNK);
                let mut rng = Self::chunk_rng(seed, c);
                let mut out = vec![0u64; in_diff.len()];
                let mut ones = 0u64;
                for _ in 0..cnt {
                    self.pair_diff(&mut rng, in_diff, &mut out);
                    let par: u32 = out
                        .iter()
                        .zip(out_mask)
                        .map(|(a, b)| (a & b).count_ones())
                        .sum();
                    ones += (par & 1) as u64;
                }
                ones
            })
            .sum();
        BiasEstimate::from_counts(samples, ones)
    }

    /// For one input difference, the number of samples (of `samples`) in
    /// which each output bit of the difference is 1: `counts[b]`.
    pub fn output_bit_counts(&self, in_diff: &[u64], samples: u64, seed: u64) -> Vec<u64> {
        let nb = self.prim.block_bits;
        let nchunks = samples.div_ceil(CHUNK);
        (0..nchunks)
            .into_par_iter()
            .map(|c| self.chunk_counts(in_diff, CHUNK.min(samples - c * CHUNK), seed, c, nb))
            .reduce(
                || vec![0u64; nb],
                |mut a, b| {
                    a.iter_mut().zip(b).for_each(|(x, y)| *x += y);
                    a
                },
            )
    }

    fn chunk_counts(&self, in_diff: &[u64], cnt: u64, seed: u64, c: u64, nb: usize) -> Vec<u64> {
        let mut rng = Self::chunk_rng(seed, c);
        let mut out = vec![0u64; in_diff.len()];
        let mut counts = vec![0u64; nb];
        for _ in 0..cnt {
            self.pair_diff(&mut rng, in_diff, &mut out);
            for (wi, &word) in out.iter().enumerate() {
                let mut v = word;
                while v != 0 {
                    counts[wi * 64 + v.trailing_zeros() as usize] += 1;
                    v &= v - 1;
                }
            }
        }
        counts
    }

    /// For one single-bit input difference, scan **all** two-bit output
    /// masks `u ⊕ v` (`u < v`): `n` pairs are sampled once, stored as bit
    /// columns (`block_bits · n / 8` bytes), and every column pair is
    /// compared by popcount. The `top_k` masks with the largest `|ε̂|` are
    /// re-estimated with `n_confirm` fresh pairs.
    pub fn search_two_bit_masks(
        &self,
        in_bit: usize,
        n: u64,
        top_k: usize,
        n_confirm: u64,
        seed: u64,
    ) -> Vec<DlPairCandidate> {
        assert!(n.is_multiple_of(64) && n >= CHUNK);
        let nb = self.prim.block_bits;
        let nw = words_for(nb);
        let mut d = vec![0u64; nw];
        d[in_bit / 64] |= 1u64 << (in_bit % 64);
        let cw = (CHUNK / 64) as usize;
        let nchunks = n.div_ceil(CHUNK);
        // cols[b] = bit column of output bit b, laid out chunk after chunk
        let parts: Vec<Vec<u64>> = (0..nchunks)
            .into_par_iter()
            .map(|c| {
                let mut rng = Self::chunk_rng(seed, c);
                let mut out = vec![0u64; nw];
                let mut cols = vec![0u64; nb * cw];
                for s in 0..(CHUNK.min(n - c * CHUNK) as usize) {
                    self.pair_diff(&mut rng, &d, &mut out);
                    for (wi, &word) in out.iter().enumerate() {
                        let mut v = word;
                        while v != 0 {
                            let b = wi * 64 + v.trailing_zeros() as usize;
                            cols[b * cw + s / 64] |= 1u64 << (s % 64);
                            v &= v - 1;
                        }
                    }
                }
                cols
            })
            .collect();
        let total_words = n as usize / 64;
        let mut cols = vec![0u64; nb * total_words];
        for (c, part) in parts.iter().enumerate() {
            for b in 0..nb {
                cols[b * total_words + c * cw..b * total_words + (c + 1) * cw]
                    .copy_from_slice(&part[b * cw..(b + 1) * cw]);
            }
        }
        drop(parts);
        let mut cands: Vec<(usize, usize, BiasEstimate)> = (0..nb)
            .into_par_iter()
            .flat_map_iter(|u| {
                let cu = &cols[u * total_words..(u + 1) * total_words];
                let mut v: Vec<(usize, usize, BiasEstimate)> = ((u + 1)..nb)
                    .map(|x| {
                        let cx = &cols[x * total_words..(x + 1) * total_words];
                        let ones: u64 = cu
                            .iter()
                            .zip(cx)
                            .map(|(a, b)| (a ^ b).count_ones() as u64)
                            .sum();
                        (u, x, BiasEstimate::from_counts(n, ones))
                    })
                    .collect();
                v.sort_by(|a, b| b.2.eps.abs().total_cmp(&a.2.eps.abs()));
                v.truncate(top_k);
                v
            })
            .collect();
        cands.sort_by(|a, b| b.2.eps.abs().total_cmp(&a.2.eps.abs()));
        cands.truncate(top_k);
        let mut res: Vec<DlPairCandidate> = cands
            .into_iter()
            .map(|(u, x, est)| {
                let mut m = vec![0u64; nw];
                m[u / 64] |= 1u64 << (u % 64);
                m[x / 64] ^= 1u64 << (x % 64);
                DlPairCandidate {
                    in_bit,
                    out_bits: (u, x),
                    search: est,
                    confirm: self.estimate_bias(&d, &m, n_confirm, seed ^ 0xC0FF_EE00_5EED_0002),
                }
            })
            .collect();
        res.sort_by(|a, b| b.confirm.eps.abs().total_cmp(&a.confirm.eps.abs()));
        res
    }

    /// Find masks that *extend* a known biased bit by one round.
    ///
    /// For input difference `in_bit` the pair is run to round
    /// `target_round` (`< rounds`), where `target_bit` of the difference is
    /// the known biased bit `t`, and on to the target's `rounds`. Every XOR
    /// of at most `max_weight` (1 to 4) bits taken from `window` (block bits of the
    /// final difference) is scored by its correlation with `t`,
    /// `corr = 1 − 2·Pr[t ≠ λ·ΔOut]`, estimated from `n` pairs. By the
    /// piling-up heuristic a mask with correlation `c` onto a bit of bias
    /// `ε_t` gives a differential-linear bias `ε_t · c` over the longer
    /// run; callers must confirm that with [`DlTarget::estimate_bias`].
    /// Returns the `top_k` masks by `|corr|` as `(bits, corr)`. Requires the
    /// compiled evaluator. The cost is `C(|window|, max_weight)` passes over
    /// `n / 64` words: weight 4 over a 128-bit window is 10.6 million
    /// subsets, which is seconds at `n = 2^12` and minutes at `2^17`.
    #[allow(clippy::too_many_arguments)]
    pub fn search_extension_masks(
        &self,
        in_bit: usize,
        target_round: usize,
        target_bit: usize,
        window: &[usize],
        max_weight: usize,
        n: u64,
        top_k: usize,
        seed: u64,
    ) -> Vec<(Vec<usize>, f64)> {
        let mc = self.machine.as_ref().expect("compiled evaluator required");
        assert!(target_round < self.rounds && (1..=4).contains(&max_weight));
        assert!(n.is_multiple_of(CHUNK));
        let w = mc.word_bits;
        let nw = words_for(self.prim.block_bits);
        let mut d = vec![0u64; nw];
        d[in_bit / 64] |= 1u64 << (in_bit % 64);
        let nwin = window.len();
        let cw = (CHUNK / 64) as usize;
        let total_words = (n / 64) as usize;
        let parts: Vec<Vec<u64>> = (0..n / CHUNK)
            .into_par_iter()
            .map(|c| {
                let mut rng = Self::chunk_rng(seed, c);
                // column 0 is the target bit, columns 1.. the window
                let mut cols = vec![0u64; (nwin + 1) * cw];
                for s in 0..CHUNK as usize {
                    let x = self.sample_block(&mut rng);
                    let run = |blk: &[u64]| -> (Vec<u64>, Vec<u64>) {
                        let mut st = vec![0u64; mc.regs];
                        for (j, v) in st.iter_mut().enumerate().take(mc.block_regs) {
                            *v = get_bits(blk, j * w, w);
                        }
                        let init = st.clone();
                        mc.forward(&mut st, 0, target_round);
                        let mid = st.clone();
                        mc.forward(&mut st, target_round, self.rounds);
                        if self.with_ff {
                            mc.add_feed_forward(&mut st, &init);
                        }
                        (mid, st)
                    };
                    let y: Vec<u64> = x.iter().zip(&d).map(|(a, b)| a ^ b).collect();
                    let ((ma, a), (mb, b)) = (run(&x), run(&y));
                    if (ma[target_bit / w] ^ mb[target_bit / w]) >> (target_bit % w) & 1 == 1 {
                        cols[s / 64] |= 1u64 << (s % 64);
                    }
                    for (i, &wb) in window.iter().enumerate() {
                        if (a[wb / w] ^ b[wb / w]) >> (wb % w) & 1 == 1 {
                            cols[(i + 1) * cw + s / 64] |= 1u64 << (s % 64);
                        }
                    }
                }
                cols
            })
            .collect();
        let mut cols = vec![0u64; (nwin + 1) * total_words];
        for (c, part) in parts.iter().enumerate() {
            for b in 0..=nwin {
                cols[b * total_words + c * cw..b * total_words + (c + 1) * cw]
                    .copy_from_slice(&part[b * cw..(b + 1) * cw]);
            }
        }
        drop(parts);
        let col = |i: usize| &cols[(i + 1) * total_words..(i + 2) * total_words];
        let t = &cols[..total_words];
        let score_of = |v: &[u64]| -> f64 {
            let mism: u64 = v.iter().map(|x| x.count_ones() as u64).sum();
            1.0 - 2.0 * mism as f64 / n as f64
        };
        // Depth-first enumeration of the subsets in increasing index order
        // with the running XOR kept per depth, so a leaf costs one pass over
        // `total_words`. Each worker keeps a bounded candidate list.
        #[allow(clippy::too_many_arguments)]
        fn walk(
            cols: &[u64],
            total_words: usize,
            score_of: &dyn Fn(&[u64]) -> f64,
            nwin: usize,
            max_weight: usize,
            top_k: usize,
            ids: &mut Vec<usize>,
            acc: &[u64],
            out: &mut Vec<(Vec<usize>, f64)>,
        ) {
            let start = ids.last().map_or(0, |&l| l + 1);
            for i in start..nwin {
                let c = &cols[(i + 1) * total_words..(i + 2) * total_words];
                let next: Vec<u64> = acc.iter().zip(c).map(|(a, b)| a ^ b).collect();
                ids.push(i);
                out.push((ids.clone(), score_of(&next)));
                if out.len() >= 8 * top_k.max(16) {
                    out.sort_by(|a, b| b.1.abs().total_cmp(&a.1.abs()));
                    out.truncate(top_k);
                }
                if ids.len() < max_weight {
                    walk(
                        cols,
                        total_words,
                        score_of,
                        nwin,
                        max_weight,
                        top_k,
                        ids,
                        &next,
                        out,
                    );
                }
                ids.pop();
            }
        }
        let mut all: Vec<(Vec<usize>, f64)> = (0..nwin)
            .into_par_iter()
            .flat_map_iter(|i| {
                let mut v = Vec::new();
                let next: Vec<u64> = t.iter().zip(col(i)).map(|(a, b)| a ^ b).collect();
                let mut ids = vec![i];
                v.push((ids.clone(), score_of(&next)));
                if max_weight >= 2 {
                    walk(
                        &cols,
                        total_words,
                        &score_of,
                        nwin,
                        max_weight,
                        top_k,
                        &mut ids,
                        &next,
                        &mut v,
                    );
                }
                v.sort_by(|a, b| b.1.abs().total_cmp(&a.1.abs()));
                v.truncate(top_k);
                v
            })
            .collect();
        all.sort_by(|a, b| b.1.abs().total_cmp(&a.1.abs()));
        all.truncate(top_k);
        all.into_iter()
            .map(|(ids, c)| (ids.into_iter().map(|i| window[i]).collect(), c))
            .collect()
    }

    /// Estimate the bias of the XOR of the listed output block bits.
    pub fn estimate_bias_bits(
        &self,
        in_bits: &[usize],
        out_bits: &[usize],
        samples: u64,
        seed: u64,
    ) -> BiasEstimate {
        let nb = self.prim.block_bits;
        let mut m = vec![0u64; words_for(nb)];
        for &b in out_bits {
            m[b / 64] ^= 1u64 << (b % 64);
        }
        self.estimate_bias(&bit_vector(nb, in_bits), &m, samples, seed)
    }

    /// Scan single-bit input differences `in_bits` against **all** single-bit
    /// output masks with `n_search` pairs per input bit, keep the `top_k`
    /// pairs with the largest `|ε̂|`, and re-estimate each with `n_confirm`
    /// fresh pairs. Sorted by `|confirm.eps|` descending.
    pub fn search_single_bit(
        &self,
        in_bits: &[usize],
        n_search: u64,
        top_k: usize,
        n_confirm: u64,
        seed: u64,
    ) -> Vec<DlCandidate> {
        let nb = self.prim.block_bits;
        let nw = words_for(nb);
        let mut cands: Vec<(usize, usize, BiasEstimate)> = in_bits
            .par_iter()
            .flat_map_iter(|&ib| {
                let mut d = vec![0u64; nw];
                d[ib / 64] |= 1u64 << (ib % 64);
                let nchunks = n_search.div_ceil(CHUNK);
                let mut counts = vec![0u64; nb];
                for c in 0..nchunks {
                    let cc = self.chunk_counts(
                        &d,
                        CHUNK.min(n_search - c * CHUNK),
                        seed ^ (ib as u64).wrapping_mul(0xD6E8_FEB8_6659_FD93),
                        c,
                        nb,
                    );
                    counts.iter_mut().zip(cc).for_each(|(x, y)| *x += y);
                }
                let mut v: Vec<(usize, usize, BiasEstimate)> = counts
                    .iter()
                    .enumerate()
                    .map(|(ob, &k)| (ib, ob, BiasEstimate::from_counts(n_search, k)))
                    .collect();
                v.sort_by(|a, b| b.2.eps.abs().total_cmp(&a.2.eps.abs()));
                v.truncate(top_k);
                v
            })
            .collect();
        cands.sort_by(|a, b| b.2.eps.abs().total_cmp(&a.2.eps.abs()));
        cands.truncate(top_k);
        let mut res: Vec<DlCandidate> = cands
            .into_iter()
            .map(|(ib, ob, est)| {
                let mut d = vec![0u64; nw];
                d[ib / 64] |= 1u64 << (ib % 64);
                let mut m = vec![0u64; nw];
                m[ob / 64] |= 1u64 << (ob % 64);
                DlCandidate {
                    in_bit: ib,
                    out_bit: ob,
                    search: est,
                    confirm: self.estimate_bias(&d, &m, n_confirm, seed ^ 0xC0FF_EE00_5EED_0001),
                }
            })
            .collect();
        res.sort_by(|a, b| b.confirm.eps.abs().total_cmp(&a.confirm.eps.abs()));
        res
    }
}

/// A bit-vector over `bits` bits with the listed bits set.
pub fn bit_vector(bits: usize, set: &[usize]) -> Vec<u64> {
    let mut v = vec![0u64; words_for(bits)];
    for &b in set {
        assert!(b < bits);
        v[b / 64] |= 1u64 << (b % 64);
    }
    v
}

/// Block bits of the attacker-controlled ChaCha input words 12..15
/// (counter and nonce), for a word width `w`: the documented input-bit
/// subset used for the ChaCha differential searches (the key words and
/// constants are not attacker-controlled).
pub fn chacha_nonce_counter_bits(w: usize) -> std::ops::Range<usize> {
    12 * w..16 * w
}
