//! Boolean window-selector encodings for arity-three disjoint-window point decomposition:
//! 1. `CompactBinarySelector`: `s` binary radix-tree decision bits per window + compact
//!    zero-auxiliary unsigned comparator `0 <= idx_w < W_w` + 1 sign bit per window
//!    (`3s + 3` Boolean variables total at `W_w = 2^s`, eliminating the `8.05e8` Sinz blowup).
//! 2. `SinzOneHotSelector`: Sinz sequential at-most-one + at-least-one + sign bit per window,
//!    retained for exact small-cell model-set equivalence checks and structural sizing tables.

/// 1-based signed DIMACS literal (`|lit| - 1` is the 0-based variable index).
pub type Lit = i32;

#[inline]
pub const fn pos_lit(var_idx: usize) -> Lit {
    (var_idx as i32) + 1
}

#[inline]
pub const fn neg_lit(var_idx: usize) -> Lit {
    -((var_idx as i32) + 1)
}

#[inline]
pub const fn var_index(lit: Lit) -> usize {
    (lit.unsigned_abs() as usize) - 1
}

#[inline]
pub const fn lit_polarity(lit: Lit) -> bool {
    lit > 0
}

#[inline]
pub fn eval_lit(lit: Lit, assign: &[Option<bool>]) -> Option<bool> {
    let v = assign[var_index(lit)]?;
    Some(if lit > 0 { v } else { !v })
}

/// Bit width `max(1, ceil(log2(len)))` for representing `[0, len)` in binary.
#[inline]
pub const fn window_bit_width(len: usize) -> usize {
    assert!(len >= 1);
    if len <= 2 {
        1
    } else {
        (usize::BITS - (len - 1).leading_zeros()) as usize
    }
}

/// Zero-auxiliary-variable minimal unsigned range CNF enforcing `0 <= idx < domain`
/// on LSB-first Boolean variables `bits[0..k]` (`domain <= 2^k`).
pub fn unsigned_less_than_clauses(bits: &[usize], domain: usize) -> Vec<Vec<Lit>> {
    assert!(domain >= 1);
    let k = bits.len();
    assert!(k < 63 && domain <= (1usize << k));
    if domain == (1usize << k) {
        return Vec::new();
    }
    // Enforce `idx <= max_valid` where `max_valid = domain - 1`.
    let max_valid = domain - 1;
    let mut clauses = Vec::new();
    for j in 0..k {
        if ((max_valid >> j) & 1) == 0 {
            let mut clause = vec![neg_lit(bits[j])];
            for (r, &var_r) in bits.iter().enumerate().skip(j + 1) {
                if ((max_valid >> r) & 1) == 1 {
                    clause.push(neg_lit(var_r));
                }
            }
            clauses.push(clause);
        }
    }
    clauses
}

/// Compact binary / radix-tree selector for three disjoint windows (`3s + 3` Boolean variables).
#[derive(Debug, Clone)]
pub struct CompactBinarySelector {
    pub window_lens: [usize; 3],
    pub bit_widths: [usize; 3],
    pub index_bits: [Vec<usize>; 3],
    pub sign_vars: [usize; 3],
    pub total_vars: usize,
    pub range_clauses: Vec<Vec<Lit>>,
}

impl CompactBinarySelector {
    /// Construct the compact binary selector for three windows of sizes `window_lens`.
    pub fn new(window_lens: [usize; 3]) -> Self {
        let mut next_var = 0usize;
        let mut bit_widths = [0usize; 3];
        let mut index_bits: [Vec<usize>; 3] = [Vec::new(), Vec::new(), Vec::new()];
        for w in 0..3 {
            assert!(window_lens[w] >= 1, "empty window in CompactBinarySelector");
            let bw = window_bit_width(window_lens[w]);
            bit_widths[w] = bw;
            let vars: Vec<usize> = (next_var..next_var + bw).collect();
            next_var += bw;
            index_bits[w] = vars;
        }
        let mut sign_vars = [0usize; 3];
        for sign_var in &mut sign_vars {
            *sign_var = next_var;
            next_var += 1;
        }
        let mut range_clauses = Vec::new();
        for w in 0..3 {
            range_clauses.extend(unsigned_less_than_clauses(&index_bits[w], window_lens[w]));
        }
        Self {
            window_lens,
            bit_widths,
            index_bits,
            sign_vars,
            total_vars: next_var,
            range_clauses,
        }
    }

    /// Branch-priority order: MSB-to-LSB radix-tree bits of Window 0 and Window 1 first,
    /// followed by Window 0/1 sign bits, then Window 2 bits and sign bit.
    pub fn branch_priority_vars(&self) -> Vec<usize> {
        let mut order = Vec::with_capacity(self.total_vars);
        for w in [0usize, 1] {
            for &v in self.index_bits[w].iter().rev() {
                order.push(v);
            }
        }
        order.push(self.sign_vars[0]);
        order.push(self.sign_vars[1]);
        for &v in self.index_bits[2].iter().rev() {
            order.push(v);
        }
        order.push(self.sign_vars[2]);
        order
    }

    /// Literal asserting bit `b` of window `w` equals `bit_val`.
    #[inline]
    pub fn index_bit_lit(&self, w: usize, bit_pos: usize, bit_val: bool) -> Lit {
        let v = self.index_bits[w][bit_pos];
        if bit_val {
            pos_lit(v)
        } else {
            neg_lit(v)
        }
    }

    /// Literal asserting the rational-lift sign of window `w` equals `sign in {0, 1}`.
    #[inline]
    pub fn sign_lit(&self, w: usize, sign: u8) -> Lit {
        let v = self.sign_vars[w];
        if sign != 0 {
            pos_lit(v)
        } else {
            neg_lit(v)
        }
    }

    /// Decode `idx_w` if all index bits of window `w` are assigned and `< window_lens[w]`.
    #[inline]
    pub fn decode_index(&self, w: usize, assign: &[Option<bool>]) -> Option<usize> {
        let mut idx = 0usize;
        for (pos, &v) in self.index_bits[w].iter().enumerate() {
            let b = assign[v]?;
            if b {
                idx |= 1usize << pos;
            }
        }
        (idx < self.window_lens[w]).then_some(idx)
    }

    /// Decode `sign_w in {0, 1}` if assigned.
    #[inline]
    pub fn decode_sign(&self, w: usize, assign: &[Option<bool>]) -> Option<u8> {
        assign[self.sign_vars[w]].map(u8::from)
    }

    /// Negated guard literals falsified iff `idx_w == idx` (`\bigvee_j \neg lit(b_{w,j} == idx_j)`).
    pub fn guard_not_index(&self, w: usize, idx: usize) -> Vec<Lit> {
        let mut out = Vec::with_capacity(self.bit_widths[w]);
        for (pos, &v) in self.index_bits[w].iter().enumerate() {
            let bit = ((idx >> pos) & 1) != 0;
            out.push(if bit { neg_lit(v) } else { pos_lit(v) });
        }
        out
    }

    /// Append negated guard literals for `(idx_w == idx && sign_w == sign)` into `out`.
    pub fn push_guard_not_signed_index(&self, w: usize, idx: usize, sign: u8, out: &mut Vec<Lit>) {
        for (pos, &v) in self.index_bits[w].iter().enumerate() {
            let bit = ((idx >> pos) & 1) != 0;
            out.push(if bit { neg_lit(v) } else { pos_lit(v) });
        }
        out.push(self.sign_lit(w, 1 - sign));
    }

    /// Full blocking clause forbidding a complete signed model `([i0, i1, i2], [s0, s1, s2])`.
    pub fn model_blocking_clause(&self, indices: [usize; 3], signs: [u8; 3]) -> Vec<Lit> {
        let mut c = Vec::with_capacity(self.total_vars);
        for w in 0..3 {
            self.push_guard_not_signed_index(w, indices[w], signs[w], &mut c);
        }
        c
    }

    /// Enumerate all indices in `[0, window_lens[w])` consistent with the partial assignment `assign`,
    /// along with the negated literals of the assigned bits in window `w`.
    pub fn compatible_indices_and_guard(
        &self,
        w: usize,
        assign: &[Option<bool>],
        cap: usize,
    ) -> Option<(Vec<usize>, Vec<Lit>)> {
        let bw = self.bit_widths[w];
        let mut unassigned_positions = Vec::new();
        let mut base_idx = 0usize;
        let mut guard = Vec::with_capacity(bw);
        for (pos, &v) in self.index_bits[w].iter().enumerate() {
            match assign[v] {
                Some(true) => {
                    base_idx |= 1usize << pos;
                    guard.push(neg_lit(v));
                }
                Some(false) => {
                    guard.push(pos_lit(v));
                }
                None => unassigned_positions.push(pos),
            }
        }
        if unassigned_positions.len() >= 20 || (1usize << unassigned_positions.len()) > cap {
            return None;
        }
        let combos = 1usize << unassigned_positions.len();
        let mut indices = Vec::with_capacity(combos);
        for mask in 0..combos {
            let mut idx = base_idx;
            for (k, &pos) in unassigned_positions.iter().enumerate() {
                if ((mask >> k) & 1) != 0 {
                    idx |= 1usize << pos;
                }
            }
            if idx < self.window_lens[w] {
                indices.push(idx);
            }
        }
        Some((indices, guard))
    }
}

/// Sinz sequential exactly-one CNF on 0-based `selector_vars` using `aux_vars` (`aux_vars.len() == n - 1`).
pub fn sinz_exactly_one_clauses(selector_vars: &[usize], aux_vars: &[usize]) -> Vec<Vec<Lit>> {
    let n = selector_vars.len();
    assert!(n >= 1);
    if n == 1 {
        assert!(aux_vars.is_empty());
        return vec![vec![pos_lit(selector_vars[0])]];
    }
    assert_eq!(aux_vars.len(), n - 1);
    let mut clauses = Vec::with_capacity(3 * n - 3);
    // At-least-one clause.
    clauses.push(selector_vars.iter().map(|&v| pos_lit(v)).collect());
    // Sequential at-most-one ladder.
    clauses.push(vec![neg_lit(selector_vars[0]), pos_lit(aux_vars[0])]);
    for i in 1..(n - 1) {
        clauses.push(vec![neg_lit(selector_vars[i]), pos_lit(aux_vars[i])]);
        clauses.push(vec![neg_lit(aux_vars[i - 1]), pos_lit(aux_vars[i])]);
        clauses.push(vec![neg_lit(selector_vars[i]), neg_lit(aux_vars[i - 1])]);
    }
    clauses.push(vec![
        neg_lit(selector_vars[n - 1]),
        neg_lit(aux_vars[n - 2]),
    ]);
    clauses
}

/// Legacy Sinz sequential one-hot window selector (from `PDP_ARITY_CORRECTION.md` / `#1347`),
/// retained for small-cell model-set equivalence tests and exact `s = 5..27` blowup comparison.
#[derive(Debug, Clone)]
pub struct SinzOneHotSelector {
    pub window_lens: [usize; 3],
    pub selector_vars: [Vec<usize>; 3],
    pub aux_vars: [Vec<usize>; 3],
    pub sign_vars: [usize; 3],
    pub total_vars: usize,
    pub clauses: Vec<Vec<Lit>>,
}

impl SinzOneHotSelector {
    pub fn new(window_lens: [usize; 3]) -> Self {
        let mut next_var = 0usize;
        let mut selector_vars: [Vec<usize>; 3] = [Vec::new(), Vec::new(), Vec::new()];
        let mut aux_vars: [Vec<usize>; 3] = [Vec::new(), Vec::new(), Vec::new()];
        let mut clauses = Vec::new();
        for w in 0..3 {
            let n = window_lens[w];
            assert!(n >= 1);
            let sels: Vec<usize> = (next_var..next_var + n).collect();
            next_var += n;
            let aux_len = n.saturating_sub(1);
            let auxs: Vec<usize> = (next_var..next_var + aux_len).collect();
            next_var += aux_len;
            clauses.extend(sinz_exactly_one_clauses(&sels, &auxs));
            selector_vars[w] = sels;
            aux_vars[w] = auxs;
        }
        let mut sign_vars = [0usize; 3];
        for sv in &mut sign_vars {
            *sv = next_var;
            next_var += 1;
        }
        Self {
            window_lens,
            selector_vars,
            aux_vars,
            sign_vars,
            total_vars: next_var,
            clauses,
        }
    }

    pub fn decode_index(&self, w: usize, assign: &[Option<bool>]) -> Option<usize> {
        let mut chosen = None;
        for (i, &v) in self.selector_vars[w].iter().enumerate() {
            match assign[v] {
                Some(true) => {
                    if chosen.is_some() {
                        return None;
                    }
                    chosen = Some(i);
                }
                Some(false) => {}
                None => return None,
            }
        }
        chosen
    }

    pub fn decode_sign(&self, w: usize, assign: &[Option<bool>]) -> Option<u8> {
        assign[self.sign_vars[w]].map(u8::from)
    }
}

/// Structural representation comparison row between Sinz one-hot and compact binary selector at `W = 2^s`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SizingComparisonRow {
    pub s: u32,
    pub window_cardinality: u64,
    pub sinz_selector_vars: u64,
    pub sinz_aux_vars: u64,
    pub sinz_total_vars_no_sign: u64,
    pub sinz_exactly_one_clauses: u64,
    pub compact_index_vars: u64,
    pub compact_sign_vars: u64,
    pub compact_total_vars: u64,
    pub compact_range_clauses: u64,
}

/// Compute exact structural counts at `W = 2^s` (`s >= 1`), matching `development_oracle.cpp --sizing`
/// (`805,306,365` Sinz Boolean vars at `s = 27` vs `81` index / `84` signed compact binary vars).
pub fn sizing_comparison_row(s: u32) -> SizingComparisonRow {
    assert!((1..=30).contains(&s));
    let n = 1u64 << s;
    let sinz_sel = 3 * n;
    let sinz_aux = 3 * (n - 1);
    let sinz_clauses = 3 * (3 * n - 3);
    SizingComparisonRow {
        s,
        window_cardinality: n,
        sinz_selector_vars: sinz_sel,
        sinz_aux_vars: sinz_aux,
        sinz_total_vars_no_sign: sinz_sel + sinz_aux,
        sinz_exactly_one_clauses: sinz_clauses,
        compact_index_vars: 3 * (s as u64),
        compact_sign_vars: 3,
        compact_total_vars: 3 * (s as u64) + 3,
        compact_range_clauses: 0,
    }
}
