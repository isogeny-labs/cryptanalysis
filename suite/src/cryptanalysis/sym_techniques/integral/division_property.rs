//! Division-property integral distinguishers.
//!
//! Two propagations over a [`Primitive`]:
//!
//! * **Bit-based** (conventional bit-based division property): Y. Todo,
//!   "Structural evaluation by generalized integral property" (EUROCRYPT
//!   2015) introduced the division property; Y. Todo and M. Morii,
//!   "Bit-based division property and application to Simon family" (FSE
//!   2016) made it bit-based; Z. Xiang, W. Zhang, Z. Bao and D. Lin,
//!   "Applying MILP method to searching integral distinguishers based on
//!   division property for 6 lightweight block ciphers" (ASIACRYPT 2016)
//!   cast the propagation as a trail search with COPY / XOR / AND rules and
//!   an S-box *division trail table*. Here the table of an S-box is computed
//!   from the algebraic normal forms of its output-coordinate products
//!   ([`division_trail_table`]): `k -> u` is a transition iff the product
//!   `prod_{i: u_i = 1} y_i(x)` contains a monomial `x^v` with `v >= k`
//!   (componentwise). The whole primitive is compiled to a netlist of S-box,
//!   XOR and AND gates (linear layers are XOR trees over copied wires; `Arx`
//!   layers with `Xor`, `And`, rotations, shifts and copies are supported,
//!   modular addition is not), and the question "is `e_i` reachable from the
//!   input division vector?" is a SAT instance for the repository's CDCL
//!   solver ([`crate::cryptanalysis::sat`]); unreachable means output bit
//!   `i` is balanced over the input set. Round-key and constant additions
//!   are ignored (the distinguishers are key independent).
//! * **Word-based** (conventional integral properties of J. Daemen, L.
//!   Knudsen and V. Rijmen, "The block cipher Square", FSE 1997, as used by
//!   Todo's word-based division property): every word of an S-box layer is
//!   CONST, ALL, BALANCED or UNKNOWN; S-boxes keep ALL and CONST and destroy
//!   BALANCED; a linear layer outputs ALL from one ALL word and constants,
//!   BALANCED when no input is UNKNOWN, CONST from constants.
//!
//! Both are sound over-approximations: a bit or word reported balanced is
//! balanced over the whole input set; failure to report one is not a proof
//! that it is unbalanced.

use crate::cryptanalysis::sat::{SolveResult, Solver};
use crate::cryptanalysis::sbox::Sbox;
use crate::cryptanalysis::sym_ir::{ArxOp, FeedForward, Gf2Matrix, Layer, Primitive};
use std::collections::HashMap;

/// Why a division-property computation could not be run or finished.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum IntegralError {
    /// The primitive has a structure the propagation cannot express.
    Unsupported(String),
    /// The SAT conflict budget ran out.
    BudgetExceeded,
}

impl std::fmt::Display for IntegralError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            IntegralError::Unsupported(s) => write!(f, "unsupported: {s}"),
            IntegralError::BudgetExceeded => write!(f, "budget exceeded"),
        }
    }
}

impl std::error::Error for IntegralError {}

// ── S-box division trail table ───────────────────────────────────────────

/// Division trail table of a square S-box of width at most 8: `dt[k][u]` is
/// true iff the division vector `k` on the input can propagate to the
/// vector `u` on the output.
///
/// Computed from the ANF of each product function
/// `f_u(x) = prod_{i: u_i = 1} y_i(x)`: `dt[k][u]` iff some monomial `x^v` of
/// `f_u` has `v >= k` (every bit of `k` set in `v`). The table is monotone
/// decreasing in `k`.
pub fn division_trail_table(sbox: &Sbox) -> Vec<Vec<bool>> {
    let n = sbox.n_in() as usize;
    assert_eq!(n, sbox.n_out() as usize, "square S-box expected");
    assert!(n <= 8, "division trail table needs width <= 8");
    let size = 1usize << n;
    let mut dt = vec![vec![false; size]; size];
    for u in 0..size {
        let mut anf: Vec<u8> = (0..size)
            .map(|x| u8::from((sbox.lookup(x as u32) as usize & u) == u))
            .collect();
        for i in 0..n {
            for x in 0..size {
                if x >> i & 1 == 1 {
                    anf[x] ^= anf[x ^ (1 << i)];
                }
            }
        }
        let mut cover: Vec<bool> = anf.iter().map(|&a| a == 1).collect();
        for i in 0..n {
            for k in 0..size {
                if k >> i & 1 == 0 && cover[k | (1 << i)] {
                    cover[k] = true;
                }
            }
        }
        for (k, row) in dt.iter_mut().enumerate() {
            row[u] = cover[k];
        }
    }
    dt
}

/// Minimal infeasible input vectors `k0` for each output pattern `u`: the
/// clause "not (output = u and input >= k0)" for each pair is exactly the
/// complement of the division trail table.
fn minimal_forbidden(dt: &[Vec<bool>], n: usize) -> Vec<(usize, usize)> {
    let size = 1usize << n;
    let mut out = Vec::new();
    for u in 0..size {
        for k in 0..size {
            if dt[k][u] {
                continue;
            }
            let minimal = (0..n).all(|i| k >> i & 1 == 0 || dt[k & !(1 << i)][u]);
            if minimal {
                out.push((u, k));
            }
        }
    }
    out
}

// ── Netlist ──────────────────────────────────────────────────────────────

enum Gate {
    Sbox {
        ins: Vec<usize>,
        outs: Vec<usize>,
        table: usize,
    },
    Xor {
        ins: Vec<usize>,
        out: usize,
    },
    And {
        a: usize,
        b: usize,
        out: usize,
    },
}

struct Netlist {
    n_wires: usize,
    gates: Vec<Gate>,
    inputs: Vec<usize>,
    outputs: Vec<Option<usize>>,
    /// Minimal forbidden `(u, k)` pairs of the S-boxes used (by
    /// `Gate::Sbox::table`).
    tables: Vec<Vec<(usize, usize)>>,
    widths: Vec<usize>,
}

impl Netlist {
    fn new_wire(&mut self) -> usize {
        self.n_wires += 1;
        self.n_wires - 1
    }

    fn xor(&mut self, ins: Vec<usize>) -> Option<usize> {
        match ins.len() {
            0 => None,
            1 => Some(ins[0]),
            _ => {
                let out = self.new_wire();
                self.gates.push(Gate::Xor { ins, out });
                Some(out)
            }
        }
    }
}

fn build_netlist(p: &Primitive, rounds: usize) -> Result<Netlist, IntegralError> {
    if rounds == 0 || rounds > p.num_rounds() {
        return Err(IntegralError::Unsupported(
            "round count out of range".into(),
        ));
    }
    if p.feed_forward != FeedForward::None {
        return Err(IntegralError::Unsupported("feed-forward".into()));
    }
    let sb = p.state_bits();
    let mut net = Netlist {
        n_wires: 0,
        gates: Vec::new(),
        inputs: Vec::new(),
        outputs: Vec::new(),
        tables: vec![Vec::new(); p.sboxes.len()],
        widths: vec![0; p.sboxes.len()],
    };
    let mut have_table = vec![false; p.sboxes.len()];
    let mut st: Vec<Option<usize>> = vec![None; sb];
    for slot in st.iter_mut().take(p.block_bits) {
        let w = net.new_wire();
        net.inputs.push(w);
        *slot = Some(w);
    }
    for r in &p.rounds[..rounds] {
        for l in &r.layers {
            match l {
                Layer::AddRoundKey { .. } | Layer::AddConst { .. } => {}
                Layer::Permute { perm } => {
                    st = perm.iter().map(|&q| st[q]).collect();
                }
                Layer::LinearGf2 { matrix } => {
                    let old = st.clone();
                    for (i, slot) in st.iter_mut().enumerate() {
                        let ins: Vec<usize> = (0..sb)
                            .filter(|&j| matrix.get(i, j))
                            .filter_map(|j| old[j])
                            .collect();
                        *slot = net.xor(ins);
                    }
                }
                Layer::SboxParallel {
                    sbox,
                    width_bits,
                    count,
                    bit_offset,
                } => {
                    let id = sbox.0;
                    if !have_table[id] {
                        let dt = division_trail_table(&p.sboxes[id]);
                        net.tables[id] = minimal_forbidden(&dt, *width_bits);
                        net.widths[id] = *width_bits;
                        have_table[id] = true;
                    }
                    for j in 0..*count {
                        let off = bit_offset + j * width_bits;
                        let ins: Option<Vec<usize>> =
                            (0..*width_bits).map(|i| st[off + i]).collect();
                        let ins = ins.ok_or_else(|| {
                            IntegralError::Unsupported("S-box input is a constant wire".into())
                        })?;
                        let outs: Vec<usize> = (0..*width_bits).map(|_| net.new_wire()).collect();
                        for (i, &o) in outs.iter().enumerate() {
                            st[off + i] = Some(o);
                        }
                        net.gates.push(Gate::Sbox {
                            ins,
                            outs,
                            table: id,
                        });
                    }
                }
                Layer::Arx { word_bits, ops } => {
                    let w = *word_bits;
                    let regs = sb / w;
                    let mut rg: Vec<Vec<Option<usize>>> =
                        (0..regs).map(|r| st[r * w..(r + 1) * w].to_vec()).collect();
                    for op in ops {
                        let (dst, val): (usize, Vec<Option<usize>>) = match *op {
                            ArxOp::Rotl { dst, src, k } => {
                                (dst, (0..w).map(|b| rg[src][(b + w - k % w) % w]).collect())
                            }
                            ArxOp::Shr { dst, src, k } => (
                                dst,
                                (0..w)
                                    .map(|b| if b + k < w { rg[src][b + k] } else { None })
                                    .collect(),
                            ),
                            ArxOp::Copy { dst, src } => (dst, rg[src].clone()),
                            ArxOp::Xor { dst, a, b } => {
                                let v = (0..w)
                                    .map(|i| {
                                        let ins: Vec<usize> =
                                            [rg[a][i], rg[b][i]].into_iter().flatten().collect();
                                        net.xor(ins)
                                    })
                                    .collect();
                                (dst, v)
                            }
                            ArxOp::And { dst, a, b } => {
                                let v = (0..w)
                                    .map(|i| match (rg[a][i], rg[b][i]) {
                                        (Some(x), Some(y)) => {
                                            let out = net.new_wire();
                                            net.gates.push(Gate::And { a: x, b: y, out });
                                            Some(out)
                                        }
                                        _ => None,
                                    })
                                    .collect();
                                (dst, v)
                            }
                            ArxOp::XorConst { .. } | ArxOp::XorKey { .. } => continue,
                            ArxOp::Add { .. } | ArxOp::AddConst { .. } | ArxOp::AddKey { .. } => {
                                return Err(IntegralError::Unsupported(
                                    "modular addition has no bit-based rule here".into(),
                                ));
                            }
                        };
                        rg[dst] = val;
                    }
                    st = rg.into_iter().flatten().collect();
                }
            }
        }
    }
    net.outputs = st[..p.block_bits].to_vec();
    Ok(net)
}

/// Outputs that depend on at least one input in `active` through gates.
fn dependent_outputs(net: &Netlist, active: &[bool]) -> Vec<bool> {
    let mut dep = vec![false; net.n_wires];
    for (i, &w) in net.inputs.iter().enumerate() {
        dep[w] = active[i];
    }
    for g in &net.gates {
        match g {
            Gate::Sbox { ins, outs, .. } => {
                let d = ins.iter().any(|&w| dep[w]);
                for &o in outs {
                    dep[o] = d;
                }
            }
            Gate::Xor { ins, out } => dep[*out] = ins.iter().any(|&w| dep[w]),
            Gate::And { a, b, out } => dep[*out] = dep[*a] || dep[*b],
        }
    }
    net.outputs
        .iter()
        .map(|o| o.is_some_and(|w| dep[w]))
        .collect()
}

/// Which output bits are reachable as a unit division vector from the input
/// vector `k0`, by SAT enumeration. Returns the per-output flags and the
/// conflicts used.
fn reachable_outputs(
    net: &Netlist,
    k0: &[bool],
    budget: u64,
) -> Result<(Vec<bool>, u64), IntegralError> {
    let mut next = net.n_wires as u32;
    let mut clauses: Vec<Vec<i32>> = Vec::new();
    // Consumers of each wire.
    let mut consumers: Vec<Vec<(usize, usize)>> = vec![Vec::new(); net.n_wires];
    for (gi, g) in net.gates.iter().enumerate() {
        match g {
            Gate::Sbox { ins, .. } | Gate::Xor { ins, .. } => {
                for (pos, &w) in ins.iter().enumerate() {
                    consumers[w].push((gi, pos));
                }
            }
            Gate::And { a, b, .. } => {
                consumers[*a].push((gi, 0));
                consumers[*b].push((gi, 1));
            }
        }
    }
    let og = net.gates.len();
    for (i, o) in net.outputs.iter().enumerate() {
        if let Some(w) = o {
            consumers[*w].push((og, i));
        }
    }
    let kv = |w: usize| (w + 1) as i32;
    let mut use_var: HashMap<(usize, usize), i32> = HashMap::new();
    for (w, cs) in consumers.iter().enumerate() {
        match cs.len() {
            0 => clauses.push(vec![-kv(w)]),
            1 => {
                use_var.insert(cs[0], kv(w));
            }
            _ => {
                let zs: Vec<i32> = cs
                    .iter()
                    .map(|&c| {
                        next += 1;
                        use_var.insert(c, next as i32);
                        next as i32
                    })
                    .collect();
                let mut c = vec![-kv(w)];
                c.extend(zs.iter().copied());
                clauses.push(c);
                for (i, &a) in zs.iter().enumerate() {
                    clauses.push(vec![-a, kv(w)]);
                    for &b in &zs[i + 1..] {
                        clauses.push(vec![-a, -b]);
                    }
                }
            }
        }
    }
    for (i, &w) in net.inputs.iter().enumerate() {
        clauses.push(vec![if k0[i] { kv(w) } else { -kv(w) }]);
    }
    for (gi, g) in net.gates.iter().enumerate() {
        match g {
            Gate::Xor { ins, out } => {
                let zs: Vec<i32> = (0..ins.len()).map(|p| use_var[&(gi, p)]).collect();
                let o = kv(*out);
                for (i, &a) in zs.iter().enumerate() {
                    clauses.push(vec![-a, o]);
                    for &b in &zs[i + 1..] {
                        clauses.push(vec![-a, -b]);
                    }
                }
                let mut c = vec![-o];
                c.extend(zs.iter().copied());
                clauses.push(c);
            }
            Gate::And { out, .. } => {
                let (a, b, o) = (use_var[&(gi, 0)], use_var[&(gi, 1)], kv(*out));
                clauses.push(vec![-a, o]);
                clauses.push(vec![-b, o]);
                clauses.push(vec![-o, a, b]);
            }
            Gate::Sbox { ins, outs, table } => {
                let w = net.widths[*table];
                let ks: Vec<i32> = (0..ins.len()).map(|p| use_var[&(gi, p)]).collect();
                let us: Vec<i32> = outs.iter().map(|&o| kv(o)).collect();
                for &(u, k0m) in &net.tables[*table] {
                    let mut c = Vec::new();
                    for (i, &uv) in us.iter().enumerate().take(w) {
                        c.push(if u >> i & 1 == 1 { -uv } else { uv });
                    }
                    for (i, &kvar) in ks.iter().enumerate().take(w) {
                        if k0m >> i & 1 == 1 {
                            c.push(-kvar);
                        }
                    }
                    clauses.push(c);
                }
            }
        }
    }
    let out_vars: Vec<(usize, i32)> = net
        .outputs
        .iter()
        .enumerate()
        .filter_map(|(i, o)| o.map(|_| (i, use_var[&(og, i)])))
        .collect();
    clauses.push(out_vars.iter().map(|&(_, v)| v).collect());
    for (a, &(_, va)) in out_vars.iter().enumerate() {
        for &(_, vb) in &out_vars[a + 1..] {
            clauses.push(vec![-va, -vb]);
        }
    }
    let mut solver = Solver::new(next);
    solver.conflict_budget = budget;
    let mut ok = true;
    for c in clauses {
        ok &= solver.add_clause(c);
    }
    let mut reach = vec![false; net.outputs.len()];
    if ok {
        loop {
            match solver.solve() {
                SolveResult::Sat => {
                    let m = solver.model();
                    let hit = out_vars
                        .iter()
                        .find(|&&(_, v)| m[(v - 1) as usize])
                        .copied()
                        .expect("exactly one output is set");
                    reach[hit.0] = true;
                    solver.reset_search();
                    if !solver.add_clause(vec![-hit.1]) {
                        break;
                    }
                }
                SolveResult::Unsat => break,
                SolveResult::Unknown => return Err(IntegralError::BudgetExceeded),
            }
        }
    }
    Ok((reach, solver.conflicts()))
}

/// Result of a bit-based division-property run.
#[derive(Clone, Debug)]
pub struct BitIntegral {
    /// Output bits proven balanced that depend on the active input bits.
    pub balanced: Vec<usize>,
    /// Output bits for which a division trail from the input vector exists
    /// (not proven balanced).
    pub unproven: Vec<usize>,
    /// Solver conflicts used.
    pub conflicts: u64,
}

/// Bit-based division property of the first `rounds` rounds of `p`: input
/// bits in `active_bits` take all values (the others are constant), `budget`
/// is the SAT conflict budget. Returns the output bits proven balanced.
pub fn bit_division_property(
    p: &Primitive,
    rounds: usize,
    active_bits: &[usize],
    budget: u64,
) -> Result<BitIntegral, IntegralError> {
    let net = build_netlist(p, rounds)?;
    let mut k0 = vec![false; p.block_bits];
    for &b in active_bits {
        k0[b] = true;
    }
    let dep = dependent_outputs(&net, &k0);
    let (reach, conflicts) = reachable_outputs(&net, &k0, budget)?;
    let mut balanced = Vec::new();
    let mut unproven = Vec::new();
    for i in 0..net.outputs.len() {
        if reach[i] {
            unproven.push(i);
        } else if dep[i] {
            balanced.push(i);
        }
    }
    Ok(BitIntegral {
        balanced,
        unproven,
        conflicts,
    })
}

// ── Word-based propagation ───────────────────────────────────────────────

/// Conventional integral property of one word over the input set.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WordProp {
    /// Constant over the set.
    Const,
    /// Takes every value equally often.
    All,
    /// XOR over the set is zero.
    Balanced,
    /// Nothing is known.
    Unknown,
}

fn word_linear(m: &Gf2Matrix, w: usize, st: &[WordProp]) -> Vec<WordProp> {
    let n = st.len();
    (0..n)
        .map(|j| {
            let mut involved: Vec<(usize, bool)> = Vec::new();
            for i in 0..n {
                let mut sub = Gf2Matrix::zero(w, w);
                let mut any = false;
                for r in 0..w {
                    for c in 0..w {
                        if m.get(j * w + r, i * w + c) {
                            sub.set(r, c, true);
                            any = true;
                        }
                    }
                }
                if any {
                    involved.push((i, sub.rank() == w));
                }
            }
            if involved.iter().any(|&(i, _)| st[i] == WordProp::Unknown) {
                return WordProp::Unknown;
            }
            let nonconst: Vec<&(usize, bool)> = involved
                .iter()
                .filter(|&&(i, _)| st[i] != WordProp::Const)
                .collect();
            match nonconst.as_slice() {
                [] => WordProp::Const,
                [&(i, inv)] if st[i] == WordProp::All && inv => WordProp::All,
                _ => WordProp::Balanced,
            }
        })
        .collect()
}

/// Word-based propagation through the first `rounds` rounds of `p`; the
/// words of `active_words` start ALL, the rest CONST. One entry per word of
/// the state after every round is returned (`result[r - 1]` after round
/// `r`). The word width is the S-box width, which must be the same in every
/// S-box layer and tile the block.
pub fn word_division_property(
    p: &Primitive,
    rounds: usize,
    active_words: &[usize],
) -> Result<Vec<Vec<WordProp>>, IntegralError> {
    let mut width = None;
    for r in &p.rounds[..rounds.min(p.num_rounds())] {
        for l in &r.layers {
            match l {
                Layer::Arx { .. } => {
                    return Err(IntegralError::Unsupported("ARX in word-based model".into()))
                }
                Layer::SboxParallel {
                    width_bits,
                    count,
                    bit_offset,
                    ..
                } => {
                    if *bit_offset != 0 || width_bits * count != p.state_bits() {
                        return Err(IntegralError::Unsupported(
                            "S-box layer does not cover the state".into(),
                        ));
                    }
                    if *width.get_or_insert(*width_bits) != *width_bits {
                        return Err(IntegralError::Unsupported("mixed S-box widths".into()));
                    }
                }
                _ => {}
            }
        }
    }
    let w = width.ok_or_else(|| IntegralError::Unsupported("no S-box layer".into()))?;
    let words = p.state_bits() / w;
    let mut st = vec![WordProp::Const; words];
    for &a in active_words {
        st[a] = WordProp::All;
    }
    let mut trace = Vec::new();
    for r in &p.rounds[..rounds] {
        for l in &r.layers {
            match l {
                Layer::SboxParallel { .. } => {
                    for s in st.iter_mut() {
                        *s = match *s {
                            WordProp::All => WordProp::All,
                            WordProp::Const => WordProp::Const,
                            _ => WordProp::Unknown,
                        };
                    }
                }
                Layer::Permute { perm } => {
                    st = word_linear(&Gf2Matrix::from_permutation(perm), w, &st);
                }
                Layer::LinearGf2 { matrix } => st = word_linear(matrix, w, &st),
                _ => {}
            }
        }
        trace.push(st.clone());
    }
    Ok(trace)
}

// ── Longest distinguisher ────────────────────────────────────────────────

/// Granularity of the propagation that produced a distinguisher.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DpLevel {
    /// Word-based ALL / BALANCED / CONST.
    Word,
    /// Bit-based division property.
    Bit,
}

/// An integral distinguisher: over all plaintexts that take every value on
/// the active bits (others fixed), the listed output bits XOR to zero.
#[derive(Clone, Debug)]
pub struct IntegralDistinguisher {
    /// Number of rounds covered.
    pub rounds: usize,
    /// Propagation that proved it.
    pub level: DpLevel,
    /// Active input bit indices (block bit numbering of the IR).
    pub active_bits: Vec<usize>,
    /// Output bits proven balanced (and dependent on the active bits).
    pub balanced_bits: Vec<usize>,
    /// `log2` of the number of chosen plaintexts (`active_bits.len()`).
    pub log2_data: usize,
}

/// Outcome of [`longest_integral_distinguisher`].
#[derive(Clone, Debug, Default)]
pub struct IntegralSearch {
    /// The longest distinguisher found (most rounds; fewest data among
    /// equals), if any round count at least 1 works.
    pub best: Option<IntegralDistinguisher>,
    /// The word-based result alone (when supported).
    pub best_word: Option<IntegralDistinguisher>,
    /// Number of input sets tried at bit level.
    pub bit_candidates_tried: usize,
    /// True if some bit-level query hit the conflict budget.
    pub budget_exhausted: bool,
}

fn better(a: &IntegralDistinguisher, b: &Option<IntegralDistinguisher>) -> bool {
    match b {
        None => true,
        Some(b) => {
            (a.rounds, std::cmp::Reverse(a.log2_data)) > (b.rounds, std::cmp::Reverse(b.log2_data))
        }
    }
}

/// Most input sets the bit-level driver tries (the single-word families
/// first, then the all-but-one-bit families in bit order).
const MAX_BIT_FAMILIES: usize = 96;

/// Longest integral distinguisher of `p` over at most `max_rounds` rounds
/// that the division-property code finds, trying:
///
/// 1. word-based propagation from every single active word;
/// 2. bit-based propagation (when the primitive compiles to the netlist
///    model) from every S-box word fully active, and from all block bits
///    active except one (each tried only at a round count that would beat
///    the best so far).
///
/// `budget` is the SAT conflict budget of each bit-based query; queries
/// that exceed it are skipped and flagged in
/// [`IntegralSearch::budget_exhausted`]. The result is a lower bound on what
/// the division property can show, not on what exists.
pub fn longest_integral_distinguisher(
    p: &Primitive,
    max_rounds: usize,
    budget: u64,
) -> Result<IntegralSearch, IntegralError> {
    let max_rounds = max_rounds.min(p.num_rounds());
    let mut out = IntegralSearch::default();
    // Word level.
    if let Ok(first) = word_division_property(p, 1, &[0]) {
        let words = first[0].len();
        let w = p.state_bits() / words;
        for a in 0..words {
            let Ok(trace) = word_division_property(p, max_rounds, &[a]) else {
                break;
            };
            for (r, st) in trace.iter().enumerate() {
                let bal: Vec<usize> = st
                    .iter()
                    .enumerate()
                    .filter(|(_, &s)| s == WordProp::All || s == WordProp::Balanced)
                    .flat_map(|(j, _)| (0..w).map(move |b| j * w + b))
                    .collect();
                if bal.is_empty() {
                    continue;
                }
                let d = IntegralDistinguisher {
                    rounds: r + 1,
                    level: DpLevel::Word,
                    active_bits: (0..w).map(|b| a * w + b).collect(),
                    balanced_bits: bal,
                    log2_data: w,
                };
                if better(&d, &out.best_word) {
                    out.best_word = Some(d);
                }
            }
        }
        out.best.clone_from(&out.best_word);
    }
    // Bit level.
    if build_netlist(p, 1).is_err() {
        return Ok(out);
    }
    let mut families: Vec<Vec<usize>> = Vec::new();
    let mut widths: Vec<usize> = Vec::new();
    for r in &p.rounds {
        for l in &r.layers {
            if let Layer::SboxParallel { width_bits, .. } = l {
                if !widths.contains(width_bits) {
                    widths.push(*width_bits);
                }
            }
        }
    }
    if widths.len() == 1 {
        let w = widths[0];
        for j in 0..p.block_bits / w {
            families.push((j * w..(j + 1) * w).collect());
        }
    }
    for c in 0..p.block_bits {
        families.push((0..p.block_bits).filter(|&b| b != c).collect());
    }
    families.truncate(MAX_BIT_FAMILIES);
    for fam in families {
        out.bit_candidates_tried += 1;
        let mut r = out.best.as_ref().map_or(1, |b| b.rounds + 1);
        while r <= max_rounds {
            match bit_division_property(p, r, &fam, budget) {
                Ok(res) if !res.balanced.is_empty() => {
                    let d = IntegralDistinguisher {
                        rounds: r,
                        level: DpLevel::Bit,
                        active_bits: fam.clone(),
                        balanced_bits: res.balanced,
                        log2_data: fam.len(),
                    };
                    if better(&d, &out.best) {
                        out.best = Some(d);
                    }
                    r += 1;
                }
                Ok(_) => break,
                Err(IntegralError::BudgetExceeded) => {
                    out.budget_exhausted = true;
                    break;
                }
                Err(e) => return Err(e),
            }
        }
    }
    Ok(out)
}
