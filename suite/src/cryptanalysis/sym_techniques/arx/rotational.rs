//! Rotational and rotational-XOR probability estimation for ARX
//! primitives.
//!
//! * **Rotational cryptanalysis** (Khovratovich and Nikolić, *Rotational
//!   Cryptanalysis of ARX*, FSE 2010; the addition probability is due to
//!   Daum, 2005): a pair of computations whose inputs are rotations of each
//!   other by `γ` bits stays a rotational pair through rotations and XORs
//!   with probability 1 and through each modular addition with probability
//!   `(1 + 2^{γ−w} + 2^{−γ} + 2^{−w}) / 4` ([`rot_add_prob`]); constants
//!   that are not rotation-invariant break the symmetry.
//! * **Rotational-XOR** (Ashur and Liu, *Rotational Cryptanalysis in the
//!   Presence of Constants*, FSE 2016): the second member of the pair is
//!   `(x <<< γ) ⊕ δ`; XOR with a constant `c` just moves the difference
//!   (`δ ← δ ⊕ c ⊕ (c <<< γ)`), so constants no longer break the property
//!   and only the additions cost probability ([`rx_add_prob`], computed
//!   exactly).
//!
//! # Conventions
//!
//! * A pair is `(S, S')` with `S' = rot_γ(S) ⊕ Δ`, where `rot_γ` rotates
//!   *each register (word)* of the state left by `γ` bits and `Δ` is a state
//!   bit-vector (`sym_ir::gf2` convention, state bit `i` is bit `i % w` of
//!   register `i / w`). Pure rotational is `Δ = 0` throughout.
//! * [`rx_add_prob`]`(w, γ, δx, δy, δz)` is
//!   `Pr_{x,y}[ ((x <<< γ) ⊕ δx) + ((y <<< γ) ⊕ δy) = ((x + y) <<< γ) ⊕ δz ]`,
//!   exact over all `2^{2w}` pairs, by a dynamic program over the bit
//!   positions with the two carry chains (the rotated chain starts at the
//!   rotated position `w − γ`; its wrap-around carry is guessed and
//!   checked).
//! * Chain estimates ([`rotational_chain`], [`rx_chain`]) walk the first
//!   `rounds` rounds of a primitive's [`Layer::Arx`] layers and, for
//!   [`KeySchedule::Nonlinear`], the key-schedule steps those rounds need
//!   (the key pair is `K' = rot_γ(K) ⊕ ΔK` word-wise). They multiply the
//!   exact per-addition probabilities **assuming independence between
//!   additions**. In RX mode the output difference of each addition is the
//!   most probable one (exact probability) among the four most frequent
//!   differences of a 2^14-sample histogram and all differences of weight
//!   at most 2, so the product is the probability of one trajectory (a lower bound on the probability of the
//!   final difference up to the independence assumption and the
//!   mode-selection noise). An empirical check against [`eval_rounds`] is
//!   [`empirical_rx`].
//! * Operations that do not commute with rotation (`Shr`, and `And` with a
//!   nonzero difference) are reported in [`RotChain::flags`] and clear
//!   [`RotChain::supported`]; layers other than ARX and AddRoundKey do the
//!   same.

use crate::cryptanalysis::sym_ir::gf2::{get_bits, set_bits, words_for};
use crate::cryptanalysis::sym_ir::{eval_rounds, ArxOp, KeySchedule, Layer, Primitive};
use crate::cryptanalysis::sym_techniques::arx::diff_linear::BiasEstimate;
use crate::cryptanalysis::sym_techniques::arx::machine::rotl;
use rand::rngs::SmallRng;
use rand::{Rng, SeedableRng};
use rayon::prelude::*;
use std::collections::HashMap;

fn mask_w(w: usize) -> u64 {
    if w >= 64 {
        u64::MAX
    } else {
        (1u64 << w) - 1
    }
}

/// Rotational probability of `z = x + y mod 2^w` for rotation `γ`:
/// `Pr[(x<<<γ) + (y<<<γ) = (x+y)<<<γ] = (1 + 2^{γ−w} + 2^{−γ} + 2^{−w})/4`
/// (Daum 2005; Khovratovich–Nikolić 2010, Theorem 1). `γ = 0` gives 1.
pub fn rot_add_prob(w: usize, gamma: usize) -> f64 {
    let g = gamma % w;
    if g == 0 {
        return 1.0;
    }
    let (w, g) = (w as i32, g as i32);
    (1.0 + 0.5f64.powi(w - g) + 0.5f64.powi(g) + 0.5f64.powi(w)) / 4.0
}

/// Exhaustive [`rot_add_prob`] for `w <= 12`.
pub fn rot_add_prob_brute(w: usize, gamma: usize) -> f64 {
    assert!(w <= 12);
    let m = mask_w(w);
    let mut c = 0u64;
    for x in 0..=m {
        for y in 0..=m {
            let l = (rotl(x, gamma, w) + rotl(y, gamma, w)) & m;
            c += (l == rotl((x + y) & m, gamma, w)) as u64;
        }
    }
    c as f64 / (1u64 << (2 * w)) as f64
}

/// Second operand of an addition in the exact DP.
#[derive(Clone, Copy, Debug)]
pub enum Operand {
    /// Uniform random with RX difference `dy` (pair `y`, `(y<<<γ) ⊕ dy`).
    Random(u64),
    /// The same constant `c` on both members of the pair.
    Const(u64),
}

/// Exact `Pr[ (x' + y') = ((x + y) <<< γ) ⊕ dz ]` with `x' = (x<<<γ) ⊕ dx`
/// and the second operand as given; `x` (and `y` if random) uniform.
pub fn rx_add_dp(w: usize, gamma: usize, dx: u64, y: Operand, dz: u64) -> f64 {
    let g = gamma % w;
    let bit = |v: u64, i: usize| (v >> i) & 1;
    let mut total: u128 = 0;
    let guesses: &[usize] = if g == 0 { &[0] } else { &[0, 1] };
    for &guess in guesses {
        // state index = cz * 2 + cl
        let mut cnt = [0u128; 4];
        cnt[guess] = 1; // cz = 0, cl = guess
        for i in 0..w {
            let j = (i + g) % w;
            let mut nxt = [0u128; 4];
            for (st, &c) in cnt.iter().enumerate() {
                if c == 0 {
                    continue;
                }
                let (cz, cl) = ((st >> 1) as u64, (st & 1) as u64);
                for x in 0..2u64 {
                    let (ys, ny) = match y {
                        Operand::Random(_) => ([0u64, 1u64], 2),
                        Operand::Const(cc) => ([bit(cc, i), 0], 1),
                    };
                    for &yb in ys.iter().take(ny) {
                        let xl = x ^ bit(dx, j);
                        let yl = match y {
                            Operand::Random(dy) => yb ^ bit(dy, j),
                            Operand::Const(cc) => bit(cc, j),
                        };
                        let sl = xl ^ yl ^ cl;
                        let sz = x ^ yb ^ cz;
                        if sl != sz ^ bit(dz, j) {
                            continue;
                        }
                        let czn = (x & yb) | (x & cz) | (yb & cz);
                        let mut cln = (xl & yl) | (xl & cl) | (yl & cl);
                        if j == w - 1 {
                            cln = 0;
                        }
                        nxt[(czn * 2 + cln) as usize] += c;
                    }
                }
            }
            cnt = nxt;
        }
        // the wrapped carry of the rotated chain must equal the guess
        // (for γ = 0 the chain was reset to 0 = guess); cz is free.
        total += cnt[guess] + cnt[2 + guess];
    }
    let bits = match y {
        Operand::Random(_) => 2 * w,
        Operand::Const(_) => w,
    };
    total as f64 / 2f64.powi(bits as i32)
}

/// [`rx_add_dp`] with a random second operand: the rotational-XOR
/// probability of one modular addition (Ashur–Liu 2016, Section 4, computed
/// exactly rather than by their closed form).
pub fn rx_add_prob(w: usize, gamma: usize, dx: u64, dy: u64, dz: u64) -> f64 {
    rx_add_dp(w, gamma, dx, Operand::Random(dy), dz)
}

/// Exhaustive reference for [`rx_add_dp`] (`w <= 10`).
pub fn rx_add_brute(w: usize, gamma: usize, dx: u64, y: Operand, dz: u64) -> f64 {
    assert!(w <= 10);
    let m = mask_w(w);
    let mut c = 0u64;
    let mut n = 0u64;
    for x in 0..=m {
        let ys: Vec<u64> = match y {
            Operand::Random(_) => (0..=m).collect(),
            Operand::Const(cc) => vec![cc & m],
        };
        for yv in ys {
            let xl = rotl(x, gamma, w) ^ dx;
            let yl = match y {
                Operand::Random(dy) => rotl(yv, gamma, w) ^ dy,
                Operand::Const(cc) => cc & m,
            };
            let lhs = (xl + yl) & m;
            let rhs = rotl((x + yv) & m, gamma, w) ^ dz;
            c += (lhs == rhs & m) as u64;
            n += 1;
        }
    }
    c as f64 / n as f64
}

/// Kinds of events reported by a chain walk.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum FlagKind {
    /// `XorConst` with value `c`; `invariant` is `c == rot_γ(c)`.
    XorConst {
        /// The constant.
        value: u64,
        /// Whether it is rotation-invariant.
        invariant: bool,
    },
    /// `AddConst` with a nonzero constant (costs probability in both modes).
    AddConst {
        /// The constant.
        value: u64,
    },
    /// An operation or layer the analysis does not model.
    Unsupported(String),
}

/// One flagged event: where it happened and what it was.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Flag {
    /// 0-based round (data path) or key-schedule step.
    pub index: usize,
    /// Whether it occurred in the key schedule.
    pub in_key_schedule: bool,
    /// What happened.
    pub kind: FlagKind,
}

/// Result of a chain walk; see the [module docs](self).
#[derive(Clone, Debug)]
pub struct RotChain {
    /// Rotation amount `γ`.
    pub gamma: usize,
    /// Additions on the data path (`Add`, `AddKey`).
    pub data_adds: usize,
    /// Additions in the key schedule.
    pub key_schedule_adds: usize,
    /// Constant additions (data path and key schedule).
    pub const_adds: usize,
    /// `log2` of the product of per-addition probabilities (`-∞` if the
    /// symmetry is broken in pure rotational mode).
    pub log2_prob: f64,
    /// Whether everything encountered was modelled.
    pub supported: bool,
    /// Constants and unsupported operations encountered.
    pub flags: Vec<Flag>,
    /// Predicted output difference `Δ_out` (state bit-vector, block bits);
    /// all-zero in pure rotational mode.
    pub out_delta: Vec<u64>,
}

impl RotChain {
    /// Probability estimate `2^{log2_prob}`.
    pub fn prob(&self) -> f64 {
        self.log2_prob.exp2()
    }
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Mode {
    Rot,
    Rx,
}

struct Walk {
    mode: Mode,
    gamma: usize,
    log2: f64,
    data_adds: usize,
    ks_adds: usize,
    const_adds: usize,
    supported: bool,
    flags: Vec<Flag>,
    rng: SmallRng,
}

impl Walk {
    fn flag(&mut self, index: usize, ks: bool, kind: FlagKind) {
        self.flags.push(Flag {
            index,
            in_key_schedule: ks,
            kind,
        });
    }

    /// Choose the output difference of a (constant or random) addition and
    /// return it with its exact probability.
    fn add_step(&mut self, w: usize, dx: u64, y: Operand) -> (u64, f64) {
        if self.mode == Mode::Rot {
            let p = match y {
                Operand::Random(_) => rot_add_prob(w, self.gamma),
                Operand::Const(_) => rx_add_dp(w, self.gamma, 0, y, 0),
            };
            return (0, p);
        }
        let m = mask_w(w);
        let g = self.gamma;
        let mut hist: HashMap<u64, u32> = HashMap::new();
        for _ in 0..(1u32 << 14) {
            let x = self.rng.gen::<u64>() & m;
            let (yv, yl) = match y {
                Operand::Random(dy) => {
                    let yv = self.rng.gen::<u64>() & m;
                    (yv, rotl(yv, g, w) ^ dy)
                }
                Operand::Const(c) => (c & m, c & m),
            };
            let lhs = (rotl(x, g, w) ^ dx).wrapping_add(yl) & m;
            let rhs = rotl(x.wrapping_add(yv) & m, g, w);
            *hist.entry(lhs ^ rhs).or_insert(0) += 1;
        }
        // Candidates: the four most frequent sampled differences and every
        // difference of Hamming weight <= 2; the winner is chosen by the
        // *exact* probability (ties: the numerically smallest difference),
        // so sampling noise cannot change the choice between equally
        // probable outputs.
        let mut top: Vec<(u32, u64)> = hist.into_iter().map(|(d, c)| (c, d)).collect();
        top.sort_by(|a, b| b.cmp(a));
        let mut cands: Vec<u64> = top.iter().take(4).map(|&(_, d)| d).collect();
        cands.push(0);
        for i in 0..w {
            cands.push(1u64 << i);
            for j in (i + 1)..w {
                cands.push((1u64 << i) | (1u64 << j));
            }
        }
        cands.sort_unstable();
        cands.dedup();
        let mut best = (0u64, -1.0f64);
        for dz in cands {
            let p = rx_add_dp(w, g, dx, y, dz);
            if p > best.1 {
                best = (dz, p);
            }
        }
        best
    }

    fn ops(
        &mut self,
        w: usize,
        ops: &[ArxOp],
        regs: &mut [u64],
        rk: &[Vec<u64>],
        index: usize,
        ks: bool,
    ) {
        let m = mask_w(w);
        let g = self.gamma;
        for op in ops {
            match *op {
                ArxOp::Add { dst, a, b } => {
                    let (dz, p) = self.add_step(w, regs[a], Operand::Random(regs[b]));
                    self.account(p, ks);
                    regs[dst] = dz;
                }
                ArxOp::AddKey {
                    dst,
                    round_key,
                    word,
                } => {
                    let dk = rk.get(round_key).map_or(0, |v| v[word]);
                    let (dz, p) = self.add_step(w, regs[dst], Operand::Random(dk));
                    self.account(p, ks);
                    regs[dst] = dz;
                }
                ArxOp::XorKey {
                    dst,
                    round_key,
                    word,
                } => regs[dst] ^= rk.get(round_key).map_or(0, |v| v[word]),
                ArxOp::Rotl { dst, src, k } => regs[dst] = rotl(regs[src], k, w),
                ArxOp::Xor { dst, a, b } => regs[dst] = regs[a] ^ regs[b],
                ArxOp::Copy { dst, src } => regs[dst] = regs[src],
                ArxOp::And { dst, a, b } => {
                    if regs[a] != 0 || regs[b] != 0 {
                        self.supported = false;
                        self.flag(
                            index,
                            ks,
                            FlagKind::Unsupported("And with a difference".into()),
                        );
                    }
                    regs[dst] = 0;
                }
                ArxOp::Shr { dst, .. } => {
                    self.supported = false;
                    self.flag(index, ks, FlagKind::Unsupported("Shr".into()));
                    regs[dst] = 0;
                }
                ArxOp::XorConst { dst, value } => {
                    let c = value & m;
                    let inv = rotl(c, g, w) == c;
                    self.flag(
                        index,
                        ks,
                        FlagKind::XorConst {
                            value: c,
                            invariant: inv,
                        },
                    );
                    match self.mode {
                        Mode::Rot => {
                            if !inv {
                                self.log2 = f64::NEG_INFINITY;
                            }
                        }
                        Mode::Rx => regs[dst] ^= c ^ rotl(c, g, w),
                    }
                }
                ArxOp::AddConst { dst, value } => {
                    let c = value & m;
                    if c != 0 {
                        self.flag(index, ks, FlagKind::AddConst { value: c });
                        let (dz, p) = self.add_step(w, regs[dst], Operand::Const(c));
                        self.const_adds += 1;
                        self.log2 += p.log2();
                        regs[dst] = dz;
                    }
                }
            }
        }
    }

    fn account(&mut self, p: f64, ks: bool) {
        if ks {
            self.ks_adds += 1;
        } else {
            self.data_adds += 1;
        }
        self.log2 += p.log2();
    }
}

fn round_keys_used(p: &Primitive, rounds: usize) -> usize {
    let mut need = 0;
    for r in &p.rounds[..rounds] {
        for l in &r.layers {
            match l {
                Layer::AddRoundKey { round_key, .. } => need = need.max(round_key + 1),
                Layer::Arx { ops, .. } => {
                    for op in ops {
                        if let ArxOp::XorKey { round_key, .. } | ArxOp::AddKey { round_key, .. } =
                            op
                        {
                            need = need.max(round_key + 1);
                        }
                    }
                }
                _ => {}
            }
        }
    }
    need
}

fn to_regs(v: &[u64], bits: usize, w: usize) -> Vec<u64> {
    (0..bits / w).map(|j| get_bits(v, j * w, w)).collect()
}

fn from_regs(regs: &[u64], w: usize) -> Vec<u64> {
    let mut v = vec![0u64; words_for(regs.len() * w)];
    for (j, &r) in regs.iter().enumerate() {
        set_bits(&mut v, j * w, w, r);
    }
    v
}

fn walk(
    p: &Primitive,
    rounds: usize,
    gamma: usize,
    mode: Mode,
    in_delta: &[u64],
    key_delta: &[u64],
) -> RotChain {
    assert!(rounds <= p.num_rounds());
    let mut wk = Walk {
        mode,
        gamma,
        log2: 0.0,
        data_adds: 0,
        ks_adds: 0,
        const_adds: 0,
        supported: true,
        flags: vec![],
        rng: SmallRng::seed_from_u64(0x5EED_0042),
    };
    // round-key differences
    let nrk = round_keys_used(p, rounds);
    let rkb = p.key_schedule.round_key_bits();
    let kw = p.key_codec.word_bits;
    let mut rk: Vec<Vec<u64>> = vec![];
    if nrk > 0 {
        match &p.key_schedule {
            KeySchedule::Independent { .. } => {
                let mut kd = key_delta.to_vec();
                kd.resize(words_for(p.key_bits).max(kd.len()), 0);
                for i in 0..nrk {
                    rk.push(
                        (0..rkb / kw)
                            .map(|j| get_bits(&kd, i * rkb + j * kw, kw))
                            .collect(),
                    );
                }
            }
            KeySchedule::Nonlinear {
                state_bits,
                steps,
                extract_offset,
                round_key_bits,
            } => {
                let w = kw;
                let mut kd = key_delta.to_vec();
                kd.resize(words_for(*state_bits), 0);
                let mut regs = to_regs(&kd, *state_bits, w);
                for i in 0..nrk {
                    if i > 0 {
                        for l in &steps[i - 1] {
                            match l {
                                Layer::Arx { word_bits, ops } if *word_bits == w => {
                                    wk.ops(w, ops, &mut regs, &[], i - 1, true)
                                }
                                _ => {
                                    wk.supported = false;
                                    wk.flag(
                                        i - 1,
                                        true,
                                        FlagKind::Unsupported("key-schedule layer".into()),
                                    );
                                }
                            }
                        }
                    }
                    let v = from_regs(&regs, w);
                    rk.push(
                        (0..round_key_bits / w)
                            .map(|j| get_bits(&v, extract_offset + j * w, w))
                            .collect(),
                    );
                }
            }
            KeySchedule::Linear { .. } => {
                wk.supported = false;
                wk.flag(0, true, FlagKind::Unsupported("linear key schedule".into()));
            }
        }
    }
    // data path
    let mut w = 0;
    for r in &p.rounds[..rounds] {
        for l in &r.layers {
            if let Layer::Arx { word_bits, .. } = l {
                w = *word_bits;
            }
        }
    }
    assert!(w > 0, "no ARX layer in the first rounds");
    let mut ind = in_delta.to_vec();
    ind.resize(words_for(p.state_bits()).max(ind.len()), 0);
    let mut regs = to_regs(&ind, p.state_bits(), w);
    for (ri, r) in p.rounds[..rounds].iter().enumerate() {
        for l in &r.layers {
            match l {
                Layer::Arx { word_bits, ops } if *word_bits == w => {
                    wk.ops(w, ops, &mut regs, &rk, ri, false)
                }
                Layer::AddRoundKey {
                    round_key,
                    bit_offset,
                } if bit_offset.is_multiple_of(w) && rkb.is_multiple_of(w) => {
                    for (j, &d) in rk[*round_key].iter().enumerate() {
                        regs[bit_offset / w + j] ^= d;
                    }
                }
                _ => {
                    wk.supported = false;
                    wk.flag(
                        ri,
                        false,
                        FlagKind::Unsupported(format!("{l:?}").chars().take(40).collect()),
                    );
                }
            }
        }
    }
    let mut out = from_regs(&regs[..p.block_bits / w], w);
    out.resize(words_for(p.block_bits), 0);
    RotChain {
        gamma,
        data_adds: wk.data_adds,
        key_schedule_adds: wk.ks_adds,
        const_adds: wk.const_adds,
        log2_prob: wk.log2,
        supported: wk.supported,
        flags: wk.flags,
        out_delta: out,
    }
}

/// Pure rotational estimate for the first `rounds` rounds (inputs and key
/// are exact rotations by `gamma` of each other, word-wise). Additions cost
/// [`rot_add_prob`]; a rotation-variant `XorConst` makes the probability
/// zero (`log2_prob = -∞`) and is listed in the flags.
pub fn rotational_chain(p: &Primitive, rounds: usize, gamma: usize) -> RotChain {
    walk(p, rounds, gamma, Mode::Rot, &[], &[])
}

/// Rotational-XOR estimate with input difference `in_delta` (block
/// bit-vector) and key difference `key_delta` (key bit-vector, key codec
/// words); see the [module docs](self).
pub fn rx_chain(
    p: &Primitive,
    rounds: usize,
    gamma: usize,
    in_delta: &[u64],
    key_delta: &[u64],
) -> RotChain {
    walk(p, rounds, gamma, Mode::Rx, in_delta, key_delta)
}

/// Structural reason the rotational / RX walk cannot model `p`, if any:
/// an operation that does not commute with rotation (`Shr`, `And`), a layer
/// other than ARX and AddRoundKey on the data path, a linear key schedule,
/// or a non-ARX key-schedule step. This is the condition under which
/// [`rotational_chain`] and [`rx_chain`] clear [`RotChain::supported`],
/// stated on the IR so applicability can use it without running a walk.
pub fn rotational_structure_gap(p: &Primitive) -> Option<String> {
    fn ops_gap(ops: &[ArxOp]) -> Option<&'static str> {
        ops.iter().find_map(|op| match op {
            ArxOp::Shr { .. } => Some("Shr (logical shift) does not commute with rotation"),
            ArxOp::And { .. } => Some("And (Ch/Maj-style choice) does not commute with rotation"),
            _ => None,
        })
    }
    let rounds = p.num_rounds();
    let mut w = 0;
    for r in &p.rounds[..rounds] {
        for l in &r.layers {
            match l {
                Layer::Arx { word_bits, ops } => {
                    if let Some(g) = ops_gap(ops) {
                        return Some(g.into());
                    }
                    if w != 0 && w != *word_bits {
                        return Some("ARX layers of different word widths".into());
                    }
                    w = *word_bits;
                }
                Layer::AddRoundKey { .. } => {}
                other => {
                    let name: String = format!("{other:?}").chars().take(24).collect();
                    return Some(format!("non-ARX layer on the data path ({name})"));
                }
            }
        }
    }
    if w == 0 {
        return Some("no ARX layer in the first rounds".into());
    }
    match &p.key_schedule {
        KeySchedule::Linear { .. } => Some("linear key schedule is not modelled".into()),
        KeySchedule::Nonlinear { steps, .. } => steps.iter().flatten().find_map(|l| match l {
            Layer::Arx { ops, .. } => ops_gap(ops).map(String::from),
            _ => Some("non-ARX key-schedule layer".into()),
        }),
        _ => None,
    }
}

/// Whether the pure rotational estimate of `p` is meaningful: the walk
/// models the structure ([`rotational_structure_gap`]) and some rotation
/// amount `gamma = 1..w-1` leaves every constant rotation-invariant (a
/// rotation-variant constant makes the estimate zero, `log2 = -inf`). `Err`
/// carries the reason.
pub fn rotational_applicable(p: &Primitive) -> Result<(), String> {
    if let Some(g) = rotational_structure_gap(p) {
        return Err(g);
    }
    let rounds = p.num_rounds();
    let w = p
        .rounds
        .iter()
        .take(rounds)
        .flat_map(|r| r.layers.iter())
        .find_map(|l| match l {
            Layer::Arx { word_bits, .. } => Some(*word_bits),
            _ => None,
        })
        .unwrap_or(0);
    if (1..w).any(|g| rotational_chain(p, rounds, g).log2_prob.is_finite()) {
        Ok(())
    } else {
        Err(
            "rotation-variant constant: no rotation amount keeps every constant invariant, \
             so the pure rotational probability is zero"
                .into(),
        )
    }
}

/// Empirical probability that `rounds` rounds of `p` map a rotational-XOR
/// pair to one: for random `K, B`, with `K' = rot_γ(K) ⊕ ΔK` (key-codec
/// words), `B' = rot_γ(B) ⊕ Δ` (block words), check
/// `E(K', B') = rot_γ(E(K, B)) ⊕ out_delta`. The output is the real output
/// ([`eval_rounds`], including any feed-forward).
#[allow(clippy::too_many_arguments)]
pub fn empirical_rx(
    p: &Primitive,
    rounds: usize,
    gamma: usize,
    in_delta: &[u64],
    key_delta: &[u64],
    out_delta: &[u64],
    samples: u64,
    seed: u64,
) -> BiasEstimate {
    let (bw, kw) = (p.block_codec.word_bits, p.key_codec.word_bits);
    let rot_words = |v: &[u64], bits: usize, w: usize| -> Vec<u64> {
        let mut o = vec![0u64; v.len()];
        for j in 0..bits / w {
            set_bits(&mut o, j * w, w, rotl(get_bits(v, j * w, w), gamma, w));
        }
        o
    };
    let chunk = 1u64 << 10;
    let hits: u64 = (0..samples.div_ceil(chunk))
        .into_par_iter()
        .map(|c| {
            let mut rng = SmallRng::seed_from_u64(seed ^ c.wrapping_mul(0x9E37_79B9_7F4A_7C15));
            let mut h = 0u64;
            for _ in 0..chunk.min(samples - c * chunk) {
                let key: Vec<u8> = (0..p.key_bytes()).map(|_| rng.gen()).collect();
                let blk: Vec<u8> = (0..p.block_bytes()).map(|_| rng.gen()).collect();
                let kv = p.key_codec.encode(&key);
                let bv = p.block_codec.encode(&blk);
                let mut kv2 = rot_words(&kv, p.key_bits, kw);
                kv2.iter_mut().zip(key_delta).for_each(|(a, b)| *a ^= b);
                let mut bv2 = rot_words(&bv, p.block_bits, bw);
                bv2.iter_mut().zip(in_delta).for_each(|(a, b)| *a ^= b);
                let key2 = p.key_codec.decode(&kv2, p.key_bits);
                let blk2 = p.block_codec.decode(&bv2, p.block_bits);
                let o1 = p.block_codec.encode(&eval_rounds(p, &key, &blk, rounds));
                let o2 = p.block_codec.encode(&eval_rounds(p, &key2, &blk2, rounds));
                let mut want = rot_words(&o1, p.block_bits, bw);
                want.iter_mut().zip(out_delta).for_each(|(a, b)| *a ^= b);
                h += (want == o2) as u64;
            }
            h
        })
        .sum();
    BiasEstimate::from_counts(samples, hits)
}
