//! A CNF encoder for the ARX fragment of the [`sym_ir`](crate::cryptanalysis::sym_ir)
//! IR, feeding the CDCL solver in [`cryptanalysis::sat`](crate::cryptanalysis::sat).
//!
//! [`CnfBuilder`] creates gates with structural hashing and constant folding
//! (so two circuits fed the same literals share their gates, which is how the
//! "equal prefix" of a collision instance costs nothing), and
//! [`encode_rounds`] interprets a [`Primitive`]: key schedule, `Layer::Arx`,
//! `Layer::Permute`, `Layer::AddConst`, `Layer::AddRoundKey` and
//! the feed-forward. S-box and dense linear layers are not supported (the
//! hash compression functions of this crate do not use them) and panic with a
//! message.
//!
//! Bit-vectors are `Vec<Lit>` in IR bit order (bit `i` of the state, see
//! `sym_ir`), words LSB first.

use crate::cryptanalysis::sat::{Lit, Solver};
use crate::cryptanalysis::sym_ir::{ArxOp, FeedForward, KeySchedule, Layer, Primitive};
use std::collections::HashMap;

/// The constant-true literal (variable 1, forced by a unit clause).
pub const TRUE: Lit = 1;
/// The constant-false literal.
pub const FALSE: Lit = -1;

/// Incremental CNF construction with gate caching.
pub struct CnfBuilder {
    n_vars: u32,
    /// All clauses added so far.
    pub clauses: Vec<Vec<Lit>>,
    and_cache: HashMap<(Lit, Lit), Lit>,
    xor_cache: HashMap<(Lit, Lit), Lit>,
    maj_cache: HashMap<(Lit, Lit, Lit), Lit>,
}

impl Default for CnfBuilder {
    fn default() -> Self {
        Self::new()
    }
}

impl CnfBuilder {
    /// A builder holding only the constant variable.
    pub fn new() -> Self {
        CnfBuilder {
            n_vars: 1,
            clauses: vec![vec![TRUE]],
            and_cache: HashMap::new(),
            xor_cache: HashMap::new(),
            maj_cache: HashMap::new(),
        }
    }

    /// Number of variables allocated so far.
    pub fn n_vars(&self) -> u32 {
        self.n_vars
    }

    /// A fresh unconstrained variable.
    pub fn fresh(&mut self) -> Lit {
        self.n_vars += 1;
        self.n_vars as Lit
    }

    /// `n` fresh variables as a bit-vector.
    pub fn fresh_vec(&mut self, n: usize) -> Vec<Lit> {
        (0..n).map(|_| self.fresh()).collect()
    }

    /// Constant bit-vector of the low `n` bits of `v`.
    pub fn constant(&self, v: u64, n: usize) -> Vec<Lit> {
        (0..n)
            .map(|i| if (v >> i) & 1 == 1 { TRUE } else { FALSE })
            .collect()
    }

    /// Add a clause.
    pub fn clause(&mut self, c: Vec<Lit>) {
        self.clauses.push(c);
    }

    /// `a AND b`.
    pub fn and(&mut self, a: Lit, b: Lit) -> Lit {
        if a == FALSE || b == FALSE || a == -b {
            return FALSE;
        }
        if a == TRUE {
            return b;
        }
        if b == TRUE || a == b {
            return a;
        }
        let key = (a.min(b), a.max(b));
        if let Some(&o) = self.and_cache.get(&key) {
            return o;
        }
        let o = self.fresh();
        self.clauses.push(vec![-o, a]);
        self.clauses.push(vec![-o, b]);
        self.clauses.push(vec![o, -a, -b]);
        self.and_cache.insert(key, o);
        o
    }

    /// `a OR b`.
    pub fn or(&mut self, a: Lit, b: Lit) -> Lit {
        -self.and(-a, -b)
    }

    /// `a XOR b`.
    pub fn xor(&mut self, a: Lit, b: Lit) -> Lit {
        if a == FALSE {
            return b;
        }
        if b == FALSE {
            return a;
        }
        if a == TRUE {
            return -b;
        }
        if b == TRUE {
            return -a;
        }
        if a == b {
            return FALSE;
        }
        if a == -b {
            return TRUE;
        }
        // Normalise signs: xor(-a, b) = -xor(a, b).
        let neg = (a < 0) ^ (b < 0);
        let (x, y) = (a.abs(), b.abs());
        let key = (x.min(y), x.max(y));
        let o = if let Some(&o) = self.xor_cache.get(&key) {
            o
        } else {
            let o = self.fresh();
            let (x, y) = key;
            self.clauses.push(vec![-o, x, y]);
            self.clauses.push(vec![-o, -x, -y]);
            self.clauses.push(vec![o, -x, y]);
            self.clauses.push(vec![o, x, -y]);
            self.xor_cache.insert(key, o);
            o
        };
        if neg {
            -o
        } else {
            o
        }
    }

    /// `a XOR b XOR c`.
    pub fn xor3(&mut self, a: Lit, b: Lit, c: Lit) -> Lit {
        let t = self.xor(a, b);
        self.xor(t, c)
    }

    /// Majority of three literals.
    pub fn maj(&mut self, a: Lit, b: Lit, c: Lit) -> Lit {
        // Constant / equal-input folding.
        if a == b || a == c {
            return a;
        }
        if b == c {
            return b;
        }
        for (x, y, z) in [(a, b, c), (b, a, c), (c, a, b)] {
            if x == FALSE {
                return self.and(y, z);
            }
            if x == TRUE {
                return self.or(y, z);
            }
            if x == -y {
                return z;
            }
        }
        let mut sorted = [a, b, c];
        sorted.sort_unstable();
        let key = (sorted[0], sorted[1], sorted[2]);
        if let Some(&o) = self.maj_cache.get(&key) {
            return o;
        }
        let o = self.fresh();
        self.maj_cache.insert(key, o);
        self.clauses.push(vec![-o, a, b]);
        self.clauses.push(vec![-o, a, c]);
        self.clauses.push(vec![-o, b, c]);
        self.clauses.push(vec![o, -a, -b]);
        self.clauses.push(vec![o, -a, -c]);
        self.clauses.push(vec![o, -b, -c]);
        o
    }

    /// `if s then t else e`.
    pub fn mux(&mut self, s: Lit, t: Lit, e: Lit) -> Lit {
        if t == e {
            return t;
        }
        if s == TRUE {
            return t;
        }
        if s == FALSE {
            return e;
        }
        let a = self.and(s, t);
        let b = self.and(-s, e);
        self.or(a, b)
    }

    /// Bitwise XOR of two words.
    pub fn xor_word(&mut self, a: &[Lit], b: &[Lit]) -> Vec<Lit> {
        a.iter().zip(b).map(|(&x, &y)| self.xor(x, y)).collect()
    }

    /// Bitwise AND of two words.
    pub fn and_word(&mut self, a: &[Lit], b: &[Lit]) -> Vec<Lit> {
        a.iter().zip(b).map(|(&x, &y)| self.and(x, y)).collect()
    }

    /// Modular addition of two equal-width words (ripple-carry).
    pub fn add_word(&mut self, a: &[Lit], b: &[Lit]) -> Vec<Lit> {
        let mut carry = FALSE;
        let mut out = Vec::with_capacity(a.len());
        for (&x, &y) in a.iter().zip(b) {
            out.push(self.xor3(x, y, carry));
            carry = self.maj(x, y, carry);
        }
        out
    }

    /// Constrain two literals to be equal.
    pub fn assert_eq(&mut self, a: Lit, b: Lit) {
        if a == b {
            return;
        }
        self.clauses.push(vec![-a, b]);
        self.clauses.push(vec![a, -b]);
    }

    /// Constrain a literal to the constant `v`.
    pub fn assert_const(&mut self, a: Lit, v: bool) {
        self.clauses.push(vec![if v { a } else { -a }]);
    }

    /// Load the formula into a fresh [`Solver`]. Returns `None` if a clause
    /// is trivially empty.
    pub fn into_solver(self) -> Option<Solver> {
        let mut s = Solver::new(self.n_vars);
        for c in self.clauses {
            if !s.add_clause(c) {
                return None;
            }
        }
        Some(s)
    }
}

type Regs = Vec<Vec<Lit>>;

fn read(state: &[Lit], r: usize, w: usize) -> Vec<Lit> {
    state[r * w..(r + 1) * w].to_vec()
}

fn write(state: &mut [Lit], r: usize, w: usize, v: &[Lit]) {
    state[r * w..(r + 1) * w].copy_from_slice(v);
}

fn apply_arx(b: &mut CnfBuilder, state: &mut [Lit], w: usize, ops: &[ArxOp], rks: &Regs) {
    for op in ops {
        let (dst, v): (usize, Vec<Lit>) = match *op {
            ArxOp::Add { dst, a, b: bb } => {
                let (x, y) = (read(state, a, w), read(state, bb, w));
                (dst, b.add_word(&x, &y))
            }
            ArxOp::Rotl { dst, src, k } => {
                let x = read(state, src, w);
                let k = k % w;
                // rotl: out[i] = in[(i - k) mod w]
                (dst, (0..w).map(|i| x[(i + w - k) % w]).collect())
            }
            ArxOp::Xor { dst, a, b: bb } => {
                let (x, y) = (read(state, a, w), read(state, bb, w));
                (dst, b.xor_word(&x, &y))
            }
            ArxOp::And { dst, a, b: bb } => {
                let (x, y) = (read(state, a, w), read(state, bb, w));
                (dst, b.and_word(&x, &y))
            }
            ArxOp::Shr { dst, src, k } => {
                let x = read(state, src, w);
                (
                    dst,
                    (0..w)
                        .map(|i| if i + k < w { x[i + k] } else { FALSE })
                        .collect(),
                )
            }
            ArxOp::Copy { dst, src } => (dst, read(state, src, w)),
            ArxOp::XorConst { dst, value } => {
                let x = read(state, dst, w);
                let c = b.constant(value, w);
                (dst, b.xor_word(&x, &c))
            }
            ArxOp::AddConst { dst, value } => {
                let x = read(state, dst, w);
                let c = b.constant(value, w);
                (dst, b.add_word(&x, &c))
            }
            ArxOp::XorKey {
                dst,
                round_key,
                word,
            } => {
                let x = read(state, dst, w);
                let k = rks[round_key][word * w..(word + 1) * w].to_vec();
                (dst, b.xor_word(&x, &k))
            }
            ArxOp::AddKey {
                dst,
                round_key,
                word,
            } => {
                let x = read(state, dst, w);
                let k = rks[round_key][word * w..(word + 1) * w].to_vec();
                (dst, b.add_word(&x, &k))
            }
        };
        write(state, dst, w, &v);
    }
}

fn apply_layer(b: &mut CnfBuilder, layer: &Layer, state: &mut [Lit], rks: &Regs) {
    match layer {
        Layer::Arx { word_bits, ops } => apply_arx(b, state, *word_bits, ops, rks),
        Layer::Permute { perm } => {
            let old = state.to_vec();
            for (i, &p) in perm.iter().enumerate() {
                state[i] = old[p];
            }
        }
        Layer::AddConst {
            bit_offset,
            bits,
            value,
        } => {
            for i in 0..*bits {
                if (value >> i) & 1 == 1 {
                    state[bit_offset + i] = -state[bit_offset + i];
                }
            }
        }
        Layer::AddRoundKey {
            round_key,
            bit_offset,
        } => {
            for (i, &k) in rks[*round_key].iter().enumerate() {
                let cur = state[bit_offset + i];
                state[bit_offset + i] = b.xor(cur, k);
            }
        }
        other => panic!("cnf encoder: unsupported layer {other:?}"),
    }
}

/// Symbolically expand the round keys of `p` (the first `count`).
pub fn encode_key_schedule(b: &mut CnfBuilder, p: &Primitive, key: &[Lit], count: usize) -> Regs {
    assert_eq!(key.len(), p.key_bits);
    let rkb = p.key_schedule.round_key_bits();
    match &p.key_schedule {
        KeySchedule::Independent { .. } => (0..count)
            .map(|i| key[i * rkb..(i + 1) * rkb].to_vec())
            .collect(),
        KeySchedule::Nonlinear {
            state_bits,
            steps,
            extract_offset,
            ..
        } => {
            let mut st = vec![FALSE; *state_bits];
            st[..key.len()].copy_from_slice(key);
            let mut out = Vec::with_capacity(count);
            for i in 0..count {
                if i > 0 {
                    for l in &steps[i - 1] {
                        apply_layer(b, l, &mut st, &Vec::new());
                    }
                }
                out.push(st[*extract_offset..extract_offset + rkb].to_vec());
            }
            out
        }
        KeySchedule::Linear { .. } => panic!("cnf encoder: linear key schedule unsupported"),
    }
}

fn round_keys_needed(p: &Primitive, n: usize) -> usize {
    let mut need = 0;
    for r in &p.rounds[..n] {
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

/// Encode the first `n` rounds of `p` plus its feed-forward, as a circuit
/// from `key` and `block` bit-vectors (IR bit order) to the output block.
pub fn encode_rounds(
    b: &mut CnfBuilder,
    p: &Primitive,
    n: usize,
    key: &[Lit],
    block: &[Lit],
) -> Vec<Lit> {
    assert_eq!(block.len(), p.block_bits);
    let rks = encode_key_schedule(b, p, key, round_keys_needed(p, n));
    let mut state = vec![FALSE; p.state_bits()];
    state[..block.len()].copy_from_slice(block);
    for r in &p.rounds[..n] {
        for l in &r.layers {
            apply_layer(b, l, &mut state, &rks);
        }
    }
    match p.feed_forward {
        FeedForward::None => {}
        FeedForward::Xor => {
            for i in 0..p.block_bits {
                state[i] = b.xor(state[i], block[i]);
            }
        }
        FeedForward::AddWords { word_bits: w } => {
            for j in 0..p.block_bits / w {
                let s = state[j * w..(j + 1) * w].to_vec();
                let i = block[j * w..(j + 1) * w].to_vec();
                let sum = b.add_word(&s, &i);
                state[j * w..(j + 1) * w].copy_from_slice(&sum);
            }
        }
    }
    state[..p.block_bits].to_vec()
}

/// Pack a bit-vector of values (IR bit order) into `u64` words.
pub fn bits_to_words(bits: &[bool]) -> Vec<u64> {
    let mut out = vec![0u64; bits.len().div_ceil(64)];
    for (i, &v) in bits.iter().enumerate() {
        if v {
            out[i / 64] |= 1 << (i % 64);
        }
    }
    out
}

/// Read the value of a literal vector from a solver model (`model[v - 1]`
/// is variable `v`).
pub fn model_bits(model: &[bool], lits: &[Lit]) -> Vec<bool> {
    lits.iter()
        .map(|&l| {
            let v = model[l.unsigned_abs() as usize - 1];
            if l < 0 {
                !v
            } else {
                v
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::sat::SolveResult;
    use crate::cryptanalysis::sym_ir::eval;
    use crate::cryptanalysis::sym_ir::primitives::{md5_compress, sha256_compress};
    use rand::rngs::SmallRng;
    use rand::{Rng, SeedableRng};

    fn bits_of(p: &Primitive, codec_key: bool, bytes: &[u8]) -> Vec<bool> {
        let c = if codec_key {
            p.key_codec
        } else {
            p.block_codec
        };
        let v = c.encode(bytes);
        (0..bytes.len() * 8)
            .map(|i| (v[i / 64] >> (i % 64)) & 1 == 1)
            .collect()
    }

    /// The CNF circuit agrees with `eval` on random inputs: fix the inputs by
    /// unit clauses, solve, read the output block.
    fn gate(p: &Primitive, n: usize, seed: u64, trials: usize) {
        let mut r = SmallRng::seed_from_u64(seed);
        for _ in 0..trials {
            let mut key = vec![0u8; p.key_bytes()];
            let mut blk = vec![0u8; p.block_bytes()];
            r.fill(&mut key[..]);
            r.fill(&mut blk[..]);
            let mut b = CnfBuilder::new();
            let kl = b.fresh_vec(p.key_bits);
            let bl = b.fresh_vec(p.block_bits);
            let out = encode_rounds(&mut b, p, n, &kl, &bl);
            for (l, v) in kl.iter().zip(bits_of(p, true, &key)) {
                b.assert_const(*l, v);
            }
            for (l, v) in bl.iter().zip(bits_of(p, false, &blk)) {
                b.assert_const(*l, v);
            }
            let mut s = b.into_solver().expect("trivially unsat");
            assert_eq!(s.solve(), SolveResult::Sat);
            let got = bits_to_words(&model_bits(&s.model(), &out));
            let want = crate::cryptanalysis::sym_ir::eval_rounds(p, &key, &blk, n);
            assert_eq!(p.block_codec.decode(&got, p.block_bits), want);
        }
    }

    #[test]
    fn cnf_matches_eval_sha256_reduced_and_full() {
        gate(&sha256_compress::steps(5), 5, 1, 4);
        gate(&sha256_compress::steps(20), 20, 2, 3);
        gate(&sha256_compress::sha256_compress(), 64, 3, 2);
    }

    #[test]
    fn cnf_matches_eval_md5() {
        gate(&md5_compress::steps(20), 20, 4, 3);
        gate(&md5_compress::md5_compress(), 64, 5, 2);
    }

    #[test]
    fn gate_cache_shares_identical_circuits() {
        let p = sha256_compress::steps(8);
        let mut b = CnfBuilder::new();
        let kl = b.fresh_vec(p.key_bits);
        let bl = b.fresh_vec(p.block_bits);
        let o1 = encode_rounds(&mut b, &p, 8, &kl, &bl);
        let v1 = b.n_vars();
        let o2 = encode_rounds(&mut b, &p, 8, &kl, &bl);
        assert_eq!(o1, o2);
        assert_eq!(v1, b.n_vars(), "second copy must add no variables");
        // sanity: eval is deterministic
        let _ = eval(&p, &[0u8; 64], &[0u8; 32]);
    }
}
