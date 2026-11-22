//! A compiled word-level evaluator for key-free ARX primitives.
//!
//! [`ArxMachine::compile`] flattens a [`Primitive`] whose rounds consist only
//! of [`Layer::Arx`] layers (one word width, no round-key operands, such as
//! the ChaCha block function in `sym_ir::primitives::chacha`) into per-round
//! operation lists that run on a `&mut [u64]` register file with no
//! allocation. It also runs rounds **backwards** when every operation is
//! invertible in place, which the generic [`eval_rounds`](crate::cryptanalysis::sym_ir::eval_rounds) cannot do.
//!
//! # Conventions
//!
//! * The register file is the state of the primitive: register `j` is state
//!   bits `j*w .. (j+1)*w`; the block occupies the first `block_bits / w`
//!   registers and scratch registers (if any) follow, as in `sym_ir`.
//! * The block codec must be `Codec::little(w)`, so register `j` is the
//!   little-endian integer in bytes `j*w/8 .. (j+1)*w/8` of the block.
//! * "Round `i`" (0-based) is `p.rounds[i]`; [`ArxMachine::forward`] runs
//!   rounds `from..to` and [`ArxMachine::backward`] undoes rounds
//!   `to..from` in reverse order.
//! * The feed-forward of the primitive is *not* part of
//!   [`ArxMachine::forward`]; [`ArxMachine::add_feed_forward`] and
//!   [`ArxMachine::sub_feed_forward`] apply and remove it explicitly.

use crate::cryptanalysis::sym_ir::{ArxOp, Codec, FeedForward, Layer, Primitive};

/// Compiled key-free ARX primitive; see the [module docs](self).
#[derive(Clone, Debug)]
pub struct ArxMachine {
    /// Register width in bits.
    pub word_bits: usize,
    /// Number of registers (block plus scratch).
    pub regs: usize,
    /// Number of block registers.
    pub block_regs: usize,
    /// The primitive's feed-forward.
    pub feed_forward: FeedForward,
    rounds: Vec<Vec<ArxOp>>,
    invertible: bool,
    mask: u64,
}

fn mask_w(w: usize) -> u64 {
    if w == 64 {
        u64::MAX
    } else {
        (1u64 << w) - 1
    }
}

/// Rotate left within `w` bits.
#[inline]
pub fn rotl(x: u64, k: usize, w: usize) -> u64 {
    let k = k % w;
    if k == 0 {
        x
    } else {
        ((x << k) | (x >> (w - k))) & mask_w(w)
    }
}

fn op_invertible(op: &ArxOp) -> bool {
    match *op {
        ArxOp::Add { dst, a, b } | ArxOp::Xor { dst, a, b } => dst == a || dst == b,
        ArxOp::Rotl { dst, src, .. } => dst == src,
        ArxOp::XorConst { .. } | ArxOp::AddConst { .. } => true,
        _ => false,
    }
}

impl ArxMachine {
    /// Compile `p`. Fails (with the reason) if a round has a layer other
    /// than [`Layer::Arx`], the widths differ, a round-key operand occurs,
    /// or the block codec is not `Codec::little(w)`.
    pub fn compile(p: &Primitive) -> Result<Self, String> {
        let mut w = None;
        let mut rounds = Vec::new();
        let mut invertible = true;
        for (i, r) in p.rounds.iter().enumerate() {
            let mut ops = Vec::new();
            for l in &r.layers {
                match l {
                    Layer::Arx { word_bits, ops: o } => {
                        if *w.get_or_insert(*word_bits) != *word_bits {
                            return Err(format!("round {i}: mixed word widths"));
                        }
                        for op in o {
                            if matches!(op, ArxOp::XorKey { .. } | ArxOp::AddKey { .. }) {
                                return Err(format!("round {i}: round-key operand"));
                            }
                            invertible &= op_invertible(op);
                        }
                        ops.extend_from_slice(o);
                    }
                    _ => return Err(format!("round {i}: non-ARX layer")),
                }
            }
            rounds.push(ops);
        }
        let w = w.ok_or("no rounds")?;
        if p.block_codec != Codec::little(w) {
            return Err("block codec is not little-endian words of the ARX width".into());
        }
        Ok(ArxMachine {
            word_bits: w,
            regs: p.state_bits() / w,
            block_regs: p.block_bits / w,
            feed_forward: p.feed_forward,
            rounds,
            invertible,
            mask: mask_w(w),
        })
    }

    /// Number of rounds.
    pub fn num_rounds(&self) -> usize {
        self.rounds.len()
    }

    /// Whether [`ArxMachine::backward`] is available.
    pub fn is_invertible(&self) -> bool {
        self.invertible
    }

    /// Run rounds `from..to` on `st` (`st.len() == regs`).
    pub fn forward(&self, st: &mut [u64], from: usize, to: usize) {
        let (w, m) = (self.word_bits, self.mask);
        for ops in &self.rounds[from..to] {
            for op in ops {
                match *op {
                    ArxOp::Add { dst, a, b } => st[dst] = st[a].wrapping_add(st[b]) & m,
                    ArxOp::Rotl { dst, src, k } => st[dst] = rotl(st[src], k, w),
                    ArxOp::Xor { dst, a, b } => st[dst] = st[a] ^ st[b],
                    ArxOp::And { dst, a, b } => st[dst] = st[a] & st[b],
                    ArxOp::Shr { dst, src, k } => st[dst] = if k >= w { 0 } else { st[src] >> k },
                    ArxOp::Copy { dst, src } => st[dst] = st[src],
                    ArxOp::XorConst { dst, value } => st[dst] = (st[dst] ^ value) & m,
                    ArxOp::AddConst { dst, value } => st[dst] = st[dst].wrapping_add(value) & m,
                    ArxOp::XorKey { .. } | ArxOp::AddKey { .. } => unreachable!(),
                }
            }
        }
    }

    /// Undo rounds `to..from` (last round first). Panics unless
    /// [`ArxMachine::is_invertible`].
    pub fn backward(&self, st: &mut [u64], from: usize, to: usize) {
        assert!(self.invertible, "ARX machine is not invertible in place");
        let (w, m) = (self.word_bits, self.mask);
        for ops in self.rounds[to..from].iter().rev() {
            for op in ops.iter().rev() {
                match *op {
                    ArxOp::Add { dst, a, b } => {
                        st[dst] = if dst == a {
                            st[dst].wrapping_sub(st[b])
                        } else {
                            st[dst].wrapping_sub(st[a])
                        } & m
                    }
                    ArxOp::Xor { dst, a, b } => {
                        st[dst] = if dst == a {
                            st[dst] ^ st[b]
                        } else {
                            st[dst] ^ st[a]
                        }
                    }
                    ArxOp::Rotl { dst, k, .. } => st[dst] = rotl(st[dst], w - (k % w), w),
                    ArxOp::XorConst { dst, value } => st[dst] = (st[dst] ^ value) & m,
                    ArxOp::AddConst { dst, value } => st[dst] = st[dst].wrapping_sub(value) & m,
                    _ => unreachable!(),
                }
            }
        }
    }

    /// `out[j] = st[j] (+|^) init[j]` for the block registers, per the
    /// primitive's feed-forward.
    pub fn add_feed_forward(&self, st: &mut [u64], init: &[u64]) {
        for (s, &i) in st.iter_mut().zip(init).take(self.block_regs) {
            *s = match self.feed_forward {
                FeedForward::None => *s,
                FeedForward::Xor => *s ^ i,
                FeedForward::AddWords { .. } => s.wrapping_add(i) & self.mask,
            };
        }
    }

    /// Inverse of [`ArxMachine::add_feed_forward`]: recover the final state
    /// from the output and the (possibly guessed) input.
    pub fn sub_feed_forward(&self, st: &mut [u64], init: &[u64]) {
        for (s, &i) in st.iter_mut().zip(init).take(self.block_regs) {
            *s = match self.feed_forward {
                FeedForward::None => *s,
                FeedForward::Xor => *s ^ i,
                FeedForward::AddWords { .. } => s.wrapping_sub(i) & self.mask,
            };
        }
    }

    /// Block bytes to a register file (scratch registers zero).
    pub fn load(&self, block: &[u8]) -> Vec<u64> {
        let nb = self.word_bits / 8;
        assert_eq!(block.len(), self.block_regs * nb);
        let mut st = vec![0u64; self.regs];
        for (j, c) in block.chunks(nb).enumerate() {
            let mut b = [0u8; 8];
            b[..nb].copy_from_slice(c);
            st[j] = u64::from_le_bytes(b);
        }
        st
    }

    /// Block registers to bytes.
    pub fn store(&self, st: &[u64]) -> Vec<u8> {
        let nb = self.word_bits / 8;
        st[..self.block_regs]
            .iter()
            .flat_map(|v| v.to_le_bytes()[..nb].to_vec())
            .collect()
    }
}
