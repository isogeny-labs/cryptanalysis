//! Miss-in-the-middle search for impossible differentials, and a
//! wrong-key-filtering key-recovery skeleton, over the
//! [`sym_ir`](crate::cryptanalysis::sym_ir) cipher IR.
//!
//! Impossible differentials: E. Biham, A. Biryukov, A. Shamir,
//! "Cryptanalysis of Skipjack reduced to 31 rounds using impossible
//! differentials", EUROCRYPT 1999 (J. Cryptology 18, 2005); the
//! truncated-state / miss-in-the-middle formulation for word-oriented SPNs
//! follows E. Biham, N. Keller, "Cryptanalysis of reduced variants of
//! Rijndael", 3rd AES Conference 2000, and J. Kim, S. Hong, J. Sung, C. Lee,
//! S. Lee, "Impossible differential cryptanalysis for block cipher
//! structures", INDOCRYPT 2003 (U-method). The dual linear-mask search that
//! reuses this engine is in
//! [`zero_correlation`](super::zero_correlation).
//!
//! # What is computed
//!
//! A *distinguisher* is a pair of truncated states `(input, output)` such
//! that no differential (or, in the dual, no linear hull) consistent with
//! both exists. The search propagates `input` forward through the layers of
//! the first `r` rounds of a [`Primitive`] and `output` backward through
//! the inverse layers, and looks for a layer boundary where the two
//! abstractions contradict each other. Propagation is a sound
//! over-approximation: a contradiction proves impossibility of the pattern
//! pair in the model; a failure to find one proves nothing, so
//! "not found" is never reported as "possible".
//!
//! Two abstract domains are implemented (see [`Model`]).
//!
//! * **Word model.** The cell is one S-box field (`width_bits` of the
//!   S-box layer). Each cell is `Zero`, `NonZero` or `Any`. S-box layers
//!   preserve activity for bijective S-boxes, so an 8-bit S-box is never
//!   enumerated. A linear layer is split into the connected components of
//!   its cell-dependency graph; for each component the exact set of
//!   reachable output activities is computed by inclusion-exclusion over
//!   the GF(2) sub-blocks (so an AES MixColumns column gives the branch
//!   number 5 behaviour without being hard-coded). Backward propagation
//!   uses [`Gf2Matrix::inverse`].
//! * **Bit model.** Each state bit is `0`, `1` or `?`. S-box layers are
//!   propagated through the exact difference (or, for masks,
//!   linear-approximation) relation of the S-box by set union, and
//!   a contradiction is also tested *across* an S-box layer. Applicable to
//!   S-boxes of width at most 4 bits (the pattern lists and relations are enumerated); used for bit-permutation SPNs such as
//!   PRESENT and ToySpn.
//!
//! The IR's `Arx` layers are rejected ([`TechniqueError::Inapplicable`]).
//!
//! # Round counting
//!
//! "`r` rounds" means the first `r` entries of [`Primitive::rounds`].
//! Because AES-like ciphers drop MixColumns in the last round, every prefix
//! is also tried in the [`FinalRound::DropTrailingLinear`] variant, which
//! removes the trailing non-permutation linear layer of round `r`
//! (matching `reduced(r, false)` of
//! [`aes128`](crate::cryptanalysis::sym_ir::primitives::aes128)).

use crate::cryptanalysis::sbox::Sbox;
use crate::cryptanalysis::sym_ir::gf2::{get_bits, set_bits, words_for};
use crate::cryptanalysis::sym_ir::{expand_key, Gf2Matrix, Layer, Primitive};
use std::fmt;
use std::rc::Rc;

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

/// Which relation is propagated through the layers.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum Propagation {
    /// XOR differences (impossible differentials).
    Differential,
    /// Linear masks (zero-correlation linear hulls).
    LinearMask,
}

/// Abstract domain used by the search; see the [module docs](self).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum Model {
    /// Per-cell `Zero` / `NonZero` / `Any`.
    Word,
    /// Per-bit `0` / `1` / `?`, exact S-box relations.
    Bit,
}

/// Variant of the last round of a prefix.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum FinalRound {
    /// Take the first `r` rounds exactly as described.
    AsGiven,
    /// Remove trailing key/constant additions and non-permutation linear
    /// layers of round `r` (the AES "no MixColumns in the last round"
    /// form).
    DropTrailingLinear,
}

/// Why a technique cannot be applied to a primitive.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum TechniqueError {
    /// The IR does not have the structure the technique needs.
    Inapplicable(String),
}

impl fmt::Display for TechniqueError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TechniqueError::Inapplicable(s) => write!(f, "technique inapplicable: {s}"),
        }
    }
}

impl std::error::Error for TechniqueError {}

pub(crate) fn inapplicable<T>(msg: impl Into<String>) -> Result<T, TechniqueError> {
    Err(TechniqueError::Inapplicable(msg.into()))
}

/// One active cell of a truncated pattern.
///
/// `value = None` means "any non-zero value" (word model); `Some(v)` is an
/// exact cell value, least-significant bit first (bit model).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct CellValue {
    /// Cell index: cell `c` is state bits `c*w .. (c+1)*w`, `w` the S-box
    /// width.
    pub cell: usize,
    /// Exact value, or `None` for "non-zero, unspecified".
    pub value: Option<u64>,
}

/// Where the two propagations disagree.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Meet {
    /// Index of the pipeline step (layer, key additions removed) at whose
    /// input the contradiction was found.
    pub step: usize,
    /// Cell (word model), bit (bit model) or S-box index (when
    /// `across_sbox`).
    pub position: usize,
    /// Contradiction found across an S-box layer rather than at a boundary.
    pub across_sbox: bool,
}

/// A miss-in-the-middle distinguisher found by the search.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MissInTheMiddle {
    /// Differential or linear-mask propagation.
    pub propagation: Propagation,
    /// Abstract domain in which the contradiction was derived.
    pub model: Model,
    /// Number of IR rounds covered.
    pub rounds: usize,
    /// Whether the trailing linear layer of the last round was dropped.
    pub final_linear_dropped: bool,
    /// Width of one cell in bits (the S-box width).
    pub cell_bits: usize,
    /// Active cells of the input pattern (all others zero).
    pub input: Vec<CellValue>,
    /// Active cells of the output pattern (all others zero).
    pub output: Vec<CellValue>,
    /// Where the contradiction was found.
    pub meet: Meet,
}

/// Limits on a search.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct SearchBudget {
    /// Largest number of rounds tried.
    pub max_rounds: usize,
    /// Largest number of active cells in an input or output pattern
    /// (word model; the bit model enumerates single-cell patterns).
    pub max_pattern_weight: usize,
    /// Cap on `(input, output)` pairs examined over the whole search.
    pub max_pair_checks: u64,
}

impl Default for SearchBudget {
    fn default() -> Self {
        SearchBudget {
            max_rounds: 12,
            max_pattern_weight: 2,
            max_pair_checks: 50_000_000,
        }
    }
}

/// One `(rounds, variant, model)` attempt made by a search.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Attempt {
    /// Rounds covered.
    pub rounds: usize,
    /// Final-round variant tried.
    pub final_round: FinalRound,
    /// Model used.
    pub model: Model,
    /// Whether a contradicting pattern pair was found.
    pub found: bool,
}

/// Outcome of a `longest_*` search.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SearchReport {
    /// The distinguisher covering the most rounds (first found among
    /// equals), if any.
    pub best: Option<MissInTheMiddle>,
    /// Every attempt, in the order made.
    pub attempts: Vec<Attempt>,
    /// `(input, output)` pairs examined.
    pub pair_checks: u64,
    /// Whether the pair budget stopped the search early.
    pub budget_exhausted: bool,
}

// ---------------------------------------------------------------------------
// Abstract values
// ---------------------------------------------------------------------------

/// Word model: cell is zero. Bit model: bit is 0.
const Z: u8 = 0;
/// Word model: cell is non-zero. Bit model: bit is 1.
const N: u8 = 1;
/// Unknown.
const ANY: u8 = 2;

// ---------------------------------------------------------------------------
// Word-level linear layers
// ---------------------------------------------------------------------------

/// Largest component (in input cells) for which exact reachability tables
/// are built; larger components fall back to a structural rule.
const MAX_EXACT_COMPONENT: usize = 8;

/// One connected component of a linear layer's cell-dependency graph.
#[derive(Clone, Debug)]
pub(crate) struct Component {
    pub ins: Vec<usize>,
    pub outs: Vec<usize>,
}

/// Connected components of the cell-dependency graph of a square GF(2)
/// matrix acting on `m.cols() / w` cells of `w` bits.
pub(crate) fn components(m: &Gf2Matrix, w: usize) -> Vec<Component> {
    let n = m.cols() / w;
    let mut parent: Vec<usize> = (0..2 * n).collect();
    fn find(p: &mut [usize], x: usize) -> usize {
        let mut r = x;
        while p[r] != r {
            r = p[r];
        }
        let mut c = x;
        while p[c] != r {
            let nx = p[c];
            p[c] = r;
            c = nx;
        }
        r
    }
    for o in 0..n {
        for c in 0..n {
            if block_nonzero(m, w, o, c) {
                let (a, b) = (find(&mut parent, c), find(&mut parent, n + o));
                if a != b {
                    parent[a] = b;
                }
            }
        }
    }
    let mut groups: std::collections::BTreeMap<usize, Component> = Default::default();
    for c in 0..n {
        let r = find(&mut parent, c);
        groups
            .entry(r)
            .or_insert_with(|| Component {
                ins: vec![],
                outs: vec![],
            })
            .ins
            .push(c);
    }
    for o in 0..n {
        let r = find(&mut parent, n + o);
        groups
            .entry(r)
            .or_insert_with(|| Component {
                ins: vec![],
                outs: vec![],
            })
            .outs
            .push(o);
    }
    groups.into_values().collect()
}

pub(crate) fn block_nonzero(m: &Gf2Matrix, w: usize, o: usize, c: usize) -> bool {
    (0..w).any(|i| (0..w).any(|j| m.get(o * w + i, c * w + j)))
}

/// Rank of the sub-matrix of `m` with the rows of the cells `rows` and the
/// columns of the cells `cols`.
pub(crate) fn sub_rank(m: &Gf2Matrix, w: usize, rows: &[usize], cols: &[usize]) -> usize {
    if rows.is_empty() || cols.is_empty() {
        return 0;
    }
    let mut s = Gf2Matrix::zero(rows.len() * w, cols.len() * w);
    for (ri, &r) in rows.iter().enumerate() {
        for (ci, &c) in cols.iter().enumerate() {
            for i in 0..w {
                for j in 0..w {
                    if m.get(r * w + i, c * w + j) {
                        s.set(ri * w + i, ci * w + j, true);
                    }
                }
            }
        }
    }
    s.rank()
}

/// Number of inputs `x`, supported exactly on the cells `p` (every cell in
/// `p` non-zero, all other cells zero), whose image `y = m x` is zero on
/// the cells in `all_outs` but not in `q` and non-zero on every cell of
/// `q`. Inclusion-exclusion over the sub-blocks; no value is enumerated.
pub(crate) fn pattern_count(
    m: &Gf2Matrix,
    w: usize,
    p: &[usize],
    q: &[usize],
    all_outs: &[usize],
) -> i128 {
    let zero_rows: Vec<usize> = all_outs
        .iter()
        .copied()
        .filter(|o| !q.contains(o))
        .collect();
    let mut total: i128 = 0;
    for t in 0..(1u32 << p.len()) {
        let rest: Vec<usize> = p
            .iter()
            .enumerate()
            .filter(|(i, _)| t >> i & 1 == 0)
            .map(|(_, &c)| c)
            .collect();
        for r in 0..(1u32 << q.len()) {
            let mut rows = zero_rows.clone();
            rows.extend(
                q.iter()
                    .enumerate()
                    .filter(|(i, _)| r >> i & 1 == 1)
                    .map(|(_, &o)| o),
            );
            let rank = sub_rank(m, w, &rows, &rest);
            let dim = (rest.len() * w) as i64 - rank as i64;
            let sign = if (t.count_ones() + r.count_ones()) % 2 == 0 {
                1
            } else {
                -1
            };
            total += sign * (1i128 << dim);
        }
    }
    total
}

/// Activity of output cell `o` over all inputs supported exactly on `s`.
fn exact_cell_status(m: &Gf2Matrix, w: usize, s: &[usize], o: usize) -> u8 {
    if s.is_empty() {
        return Z;
    }
    let total: i128 = ((1i128 << w) - 1).pow(s.len() as u32);
    let mut zero_cnt: i128 = 0;
    for t in 0..(1u32 << s.len()) {
        let rest: Vec<usize> = s
            .iter()
            .enumerate()
            .filter(|(i, _)| t >> i & 1 == 0)
            .map(|(_, &c)| c)
            .collect();
        let rank = sub_rank(m, w, &[o], &rest);
        let dim = (rest.len() * w) as i64 - rank as i64;
        let sign = if t.count_ones() % 2 == 0 { 1 } else { -1 };
        zero_cnt += sign * (1i128 << dim);
    }
    if zero_cnt == 0 {
        N
    } else if zero_cnt == total {
        Z
    } else {
        ANY
    }
}

/// A linear layer prepared for word-level propagation.
#[derive(Clone, Debug)]
struct WordLinear {
    n: usize,
    comps: Vec<WordComp>,
}

#[derive(Clone, Debug)]
struct WordComp {
    ins: Vec<usize>,
    outs: Vec<usize>,
    /// `table[mask][k]`: status of `outs[k]` when exactly the input cells
    /// `ins[i]` with bit `i` of `mask` set are non-zero. `None` for
    /// components too large for exact tables.
    table: Option<Vec<Vec<u8>>>,
    /// Structural dependency: `dep[k]` is the mask of `ins` feeding
    /// `outs[k]`.
    dep: Vec<u64>,
}

impl WordLinear {
    fn build(m: &Gf2Matrix, w: usize) -> WordLinear {
        let n = m.cols() / w;
        let comps = components(m, w)
            .into_iter()
            .map(|c| {
                let dep: Vec<u64> = c
                    .outs
                    .iter()
                    .map(|&o| {
                        c.ins
                            .iter()
                            .enumerate()
                            .filter(|(_, &i)| block_nonzero(m, w, o, i))
                            .fold(0u64, |a, (k, _)| a | 1 << k)
                    })
                    .collect();
                let table = (c.ins.len() <= MAX_EXACT_COMPONENT).then(|| {
                    (0..(1usize << c.ins.len()))
                        .map(|mask| {
                            let s: Vec<usize> = c
                                .ins
                                .iter()
                                .enumerate()
                                .filter(|(k, _)| mask >> k & 1 == 1)
                                .map(|(_, &i)| i)
                                .collect();
                            c.outs
                                .iter()
                                .map(|&o| exact_cell_status(m, w, &s, o))
                                .collect()
                        })
                        .collect()
                });
                WordComp {
                    ins: c.ins,
                    outs: c.outs,
                    table,
                    dep,
                }
            })
            .collect();
        WordLinear { n, comps }
    }

    fn apply(&self, st: &[u8]) -> Vec<u8> {
        let mut out = vec![Z; self.n];
        for c in &self.comps {
            let (mut forced, mut free) = (0u64, 0u64);
            for (k, &i) in c.ins.iter().enumerate() {
                match st[i] {
                    N => forced |= 1 << k,
                    ANY => free |= 1 << k,
                    _ => {}
                }
            }
            for (k, &o) in c.outs.iter().enumerate() {
                out[o] = match &c.table {
                    Some(tab) => {
                        // enumerate sub-masks of `free`
                        let mut sub = free;
                        let (mut all_z, mut all_n) = (true, true);
                        loop {
                            let v = tab[(forced | sub) as usize][k];
                            all_z &= v == Z;
                            all_n &= v == N;
                            if sub == 0 {
                                break;
                            }
                            sub = (sub - 1) & free;
                        }
                        if all_z {
                            Z
                        } else if all_n {
                            N
                        } else {
                            ANY
                        }
                    }
                    None => {
                        if c.dep[k] & (forced | free) == 0 {
                            Z
                        } else {
                            ANY
                        }
                    }
                };
            }
        }
        out
    }
}

// ---------------------------------------------------------------------------
// S-box relations (bit model)
// ---------------------------------------------------------------------------

#[derive(Debug)]
struct Rel {
    n: usize,
    /// `fwd[x]` is the bitset of `y` with `x -> y` possible.
    fwd: Vec<Vec<u64>>,
    /// `bwd[y]` is the bitset of `x` with `x -> y` possible.
    bwd: Vec<Vec<u64>>,
}

impl Rel {
    fn build(sbox: &Sbox, mode: Propagation) -> Rel {
        let n = 1usize << sbox.n_in();
        let words = words_for(n).max(1);
        let mut fwd = vec![vec![0u64; words]; n];
        let mut bwd = vec![vec![0u64; words]; n];
        let possible: Vec<Vec<bool>> = match mode {
            Propagation::Differential => sbox
                .ddt()
                .iter()
                .map(|r| r.iter().map(|&v| v > 0).collect())
                .collect(),
            Propagation::LinearMask => sbox
                .lat()
                .iter()
                .map(|r| r.iter().map(|&v| v != 0).collect())
                .collect(),
        };
        for (a, row) in possible.iter().enumerate() {
            for (b, &ok) in row.iter().enumerate() {
                if ok {
                    fwd[a][b / 64] |= 1 << (b % 64);
                    bwd[b][a / 64] |= 1 << (a % 64);
                }
            }
        }
        Rel { n, fwd, bwd }
    }
}

// ---------------------------------------------------------------------------
// Pipeline
// ---------------------------------------------------------------------------

#[derive(Debug)]
struct SboxStep {
    off: usize,
    width: usize,
    count: usize,
    injective: bool,
    balanced: bool,
    rel: Option<Rc<Rel>>,
}

#[derive(Debug)]
struct LinDir {
    /// Bit model: for each output bit the input bits XORed into it.
    rows: Vec<Vec<usize>>,
    /// Word model: component structure.
    word: Option<WordLinear>,
}

#[derive(Debug)]
enum Step {
    Sbox(SboxStep),
    Lin { fwd: LinDir, bwd: LinDir },
}

/// A prefix of a primitive prepared for one propagation and one model.
#[derive(Debug)]
pub(crate) struct Pipeline {
    model: Model,
    w: usize,
    ncell: usize,
    nbits: usize,
    steps: Vec<Step>,
}

fn rows_of(m: &Gf2Matrix) -> Vec<Vec<usize>> {
    (0..m.rows())
        .map(|i| (0..m.cols()).filter(|&j| m.get(i, j)).collect())
        .collect()
}

fn lin_dir(m: &Gf2Matrix, model: Model, w: usize) -> LinDir {
    match model {
        Model::Bit => LinDir {
            rows: rows_of(m),
            word: None,
        },
        Model::Word => LinDir {
            rows: vec![],
            word: Some(WordLinear::build(m, w)),
        },
    }
}

/// Flatten the first `rounds` rounds of `p` into layers, applying the
/// final-round variant. Returns the layers and whether anything was
/// dropped.
fn prefix_layers(p: &Primitive, rounds: usize, fr: FinalRound) -> (Vec<&Layer>, bool) {
    let mut layers: Vec<&Layer> = p.rounds[..rounds]
        .iter()
        .flat_map(|r| r.layers.iter())
        .collect();
    let mut dropped = false;
    if fr == FinalRound::DropTrailingLinear {
        loop {
            match layers.last() {
                Some(Layer::AddRoundKey { .. }) | Some(Layer::AddConst { .. }) => {
                    layers.pop();
                }
                Some(Layer::LinearGf2 { matrix }) if matrix.as_permutation().is_none() => {
                    layers.pop();
                    dropped = true;
                }
                _ => break,
            }
        }
    }
    (layers, dropped)
}

/// Build the pipeline for the first `rounds` rounds.
pub(crate) fn build_pipeline(
    p: &Primitive,
    rounds: usize,
    fr: FinalRound,
    mode: Propagation,
    model: Model,
) -> Result<(Pipeline, bool), TechniqueError> {
    if rounds == 0 || rounds > p.num_rounds() {
        return inapplicable(format!(
            "{}: {rounds} rounds requested, {} described",
            p.name,
            p.num_rounds()
        ));
    }
    if p.scratch_bits != 0 {
        return inapplicable(format!("{}: scratch state bits (ARX temporaries)", p.name));
    }
    let (layers, dropped) = prefix_layers(p, rounds, fr);
    let mut w = 0usize;
    for l in &layers {
        match l {
            Layer::Arx { .. } => return inapplicable(format!("{}: ARX layer", p.name)),
            Layer::SboxParallel { width_bits, .. } if w == 0 => w = *width_bits,
            _ => {}
        }
    }
    if w == 0 {
        return inapplicable(format!(
            "{}: no S-box layer in the first {rounds} rounds",
            p.name
        ));
    }
    let nbits = p.block_bits;
    if !nbits.is_multiple_of(w) {
        return inapplicable("S-box width does not tile the block");
    }
    if model == Model::Bit && w > 4 {
        return inapplicable("bit model enumerates S-box values; limited to 4-bit S-boxes");
    }
    let mut rels: std::collections::HashMap<usize, Rc<Rel>> = Default::default();
    let mut steps = Vec::new();
    for l in layers {
        match l {
            Layer::AddRoundKey { .. } | Layer::AddConst { .. } => {}
            Layer::Arx { .. } => unreachable!(),
            Layer::SboxParallel {
                sbox,
                width_bits,
                count,
                bit_offset,
            } => {
                if model == Model::Word
                    && (*width_bits != w || *bit_offset != 0 || width_bits * count != nbits)
                {
                    return inapplicable(
                        "word model needs S-box layers of one width covering the whole state",
                    );
                }
                let s = &p.sboxes[sbox.0];
                let rel = (model == Model::Bit).then(|| {
                    rels.entry(sbox.0)
                        .or_insert_with(|| Rc::new(Rel::build(s, mode)))
                        .clone()
                });
                steps.push(Step::Sbox(SboxStep {
                    off: *bit_offset,
                    width: *width_bits,
                    count: *count,
                    injective: s.is_bijective(),
                    balanced: s.is_balanced(),
                    rel,
                }));
            }
            Layer::Permute { perm } => {
                let mut inv = vec![0usize; perm.len()];
                for (i, &q) in perm.iter().enumerate() {
                    inv[q] = i;
                }
                let f = Gf2Matrix::from_permutation(perm);
                let b = Gf2Matrix::from_permutation(&inv);
                steps.push(Step::Lin {
                    fwd: lin_dir(&f, model, w),
                    bwd: lin_dir(&b, model, w),
                });
            }
            Layer::LinearGf2 { matrix } => {
                let (f, b) = if let Some(perm) = matrix.as_permutation() {
                    let mut inv = vec![0usize; perm.len()];
                    for (i, &q) in perm.iter().enumerate() {
                        inv[q] = i;
                    }
                    (matrix.clone(), Gf2Matrix::from_permutation(&inv))
                } else {
                    let Some(minv) = matrix.inverse() else {
                        return inapplicable("singular linear layer");
                    };
                    match mode {
                        Propagation::Differential => (matrix.clone(), minv),
                        Propagation::LinearMask => (minv.transpose(), matrix.transpose()),
                    }
                };
                steps.push(Step::Lin {
                    fwd: lin_dir(&f, model, w),
                    bwd: lin_dir(&b, model, w),
                });
            }
        }
    }
    Ok((
        Pipeline {
            model,
            w,
            ncell: nbits / w,
            nbits,
            steps,
        },
        dropped,
    ))
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Dir {
    Fwd,
    Bwd,
}

impl Pipeline {
    fn apply(&self, k: usize, dir: Dir, st: &[u8], mode: Propagation) -> Vec<u8> {
        match &self.steps[k] {
            Step::Lin { fwd, bwd } => {
                let d = if dir == Dir::Fwd { fwd } else { bwd };
                match self.model {
                    Model::Word => d.word.as_ref().expect("word layer").apply(st),
                    Model::Bit => d
                        .rows
                        .iter()
                        .map(|r| {
                            let mut par = 0u8;
                            for &j in r {
                                match st[j] {
                                    ANY => return ANY,
                                    v => par ^= v,
                                }
                            }
                            par
                        })
                        .collect(),
                }
            }
            Step::Sbox(s) => match self.model {
                Model::Word => st
                    .iter()
                    .map(|&v| match (mode, dir, v) {
                        (_, _, ANY) => ANY,
                        (Propagation::Differential, Dir::Fwd, N) => {
                            if s.injective {
                                N
                            } else {
                                ANY
                            }
                        }
                        (Propagation::Differential, Dir::Bwd, Z) => {
                            if s.injective {
                                Z
                            } else {
                                ANY
                            }
                        }
                        (Propagation::LinearMask, Dir::Bwd, N) => {
                            if s.balanced {
                                N
                            } else {
                                ANY
                            }
                        }
                        (_, _, v) => v,
                    })
                    .collect(),
                Model::Bit => {
                    let rel = s.rel.as_ref().expect("bit relation");
                    let mut out = st.to_vec();
                    for j in 0..s.count {
                        let off = s.off + j * s.width;
                        let set = consistent(st, off, s.width);
                        let mut u = vec![0u64; words_for(rel.n).max(1)];
                        for x in bits_of(&set) {
                            let row = if dir == Dir::Fwd {
                                &rel.fwd[x]
                            } else {
                                &rel.bwd[x]
                            };
                            for (a, b) in u.iter_mut().zip(row) {
                                *a |= b;
                            }
                        }
                        let (mut seen0, mut seen1) = (0u32, 0u32);
                        for y in bits_of(&u) {
                            seen1 |= y as u32;
                            seen0 |= !(y as u32);
                        }
                        let any = u.iter().any(|&x| x != 0);
                        for b in 0..s.width {
                            out[off + b] = if !any {
                                ANY
                            } else if seen1 >> b & 1 == 0 {
                                Z
                            } else if seen0 >> b & 1 == 0 {
                                N
                            } else {
                                ANY
                            };
                        }
                    }
                    out
                }
            },
        }
    }

    fn forward(&self, input: &[u8], mode: Propagation) -> Vec<Vec<u8>> {
        let mut v = vec![input.to_vec()];
        for k in 0..self.steps.len() {
            let nx = self.apply(k, Dir::Fwd, &v[k], mode);
            v.push(nx);
        }
        v
    }

    fn backward(&self, output: &[u8], mode: Propagation) -> Vec<Vec<u8>> {
        let n = self.steps.len();
        let mut v = vec![Vec::new(); n + 1];
        v[n] = output.to_vec();
        for k in (0..n).rev() {
            v[k] = self.apply(k, Dir::Bwd, &v[k + 1], mode);
        }
        v
    }

    /// First contradiction between forward states `f` and backward states
    /// `b` (both indexed by step).
    fn conflict(&self, f: &[Vec<u8>], b: &[Vec<u8>]) -> Option<Meet> {
        for k in 0..=self.steps.len() {
            if self.model == Model::Bit && k < self.steps.len() {
                if let Step::Sbox(s) = &self.steps[k] {
                    let rel = s.rel.as_ref().expect("bit relation");
                    for j in 0..s.count {
                        let off = s.off + j * s.width;
                        let din = consistent(&f[k], off, s.width);
                        let dout = consistent(&b[k + 1], off, s.width);
                        let ok = bits_of(&din)
                            .any(|x| rel.fwd[x].iter().zip(&dout).any(|(a, c)| a & c != 0));
                        if !ok {
                            return Some(Meet {
                                step: k,
                                position: j,
                                across_sbox: true,
                            });
                        }
                    }
                }
            }
            for (pos, (&x, &y)) in f[k].iter().zip(&b[k]).enumerate() {
                if x != ANY && y != ANY && x != y {
                    return Some(Meet {
                        step: k,
                        position: pos,
                        across_sbox: false,
                    });
                }
            }
        }
        None
    }

    fn state_of(&self, pat: &[CellValue]) -> Result<Vec<u8>, TechniqueError> {
        let mut st = vec![Z; self.nbits];
        match self.model {
            Model::Word => {
                let mut cells = vec![Z; self.ncell];
                for c in pat {
                    if c.cell >= self.ncell {
                        return inapplicable("cell index out of range");
                    }
                    cells[c.cell] = N;
                }
                Ok(cells)
            }
            Model::Bit => {
                for c in pat {
                    let Some(v) = c.value else {
                        return inapplicable("bit model needs exact cell values");
                    };
                    if c.cell >= self.ncell {
                        return inapplicable("cell index out of range");
                    }
                    for b in 0..self.w {
                        st[c.cell * self.w + b] = (v >> b & 1) as u8;
                    }
                }
                Ok(st)
            }
        }
    }
}

/// Bitset of the `w`-bit values consistent with the known bits of `st`
/// starting at `off`.
fn consistent(st: &[u8], off: usize, w: usize) -> Vec<u64> {
    let n = 1usize << w;
    let mut out = vec![0u64; words_for(n).max(1)];
    let (mut mask, mut val) = (0usize, 0usize);
    for b in 0..w {
        match st[off + b] {
            ANY => {}
            v => {
                mask |= 1 << b;
                val |= (v as usize) << b;
            }
        }
    }
    for x in 0..n {
        if x & mask == val {
            out[x / 64] |= 1 << (x % 64);
        }
    }
    out
}

fn bits_of(set: &[u64]) -> impl Iterator<Item = usize> + '_ {
    set.iter().enumerate().flat_map(|(i, &w)| {
        (0..64)
            .filter(move |b| w >> b & 1 == 1)
            .map(move |b| i * 64 + b)
    })
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

fn combos(n: usize, k: usize) -> Vec<Vec<usize>> {
    fn rec(start: usize, n: usize, k: usize, cur: &mut Vec<usize>, out: &mut Vec<Vec<usize>>) {
        if cur.len() == k {
            out.push(cur.clone());
            return;
        }
        for i in start..n {
            cur.push(i);
            rec(i + 1, n, k, cur, out);
            cur.pop();
        }
    }
    let mut out = Vec::new();
    rec(0, n, k, &mut Vec::new(), &mut out);
    out
}

fn patterns(pipe: &Pipeline, max_weight: usize) -> Vec<Vec<CellValue>> {
    match pipe.model {
        Model::Word => (1..=max_weight.min(pipe.ncell))
            .flat_map(|k| combos(pipe.ncell, k))
            .map(|cs| {
                cs.into_iter()
                    .map(|cell| CellValue { cell, value: None })
                    .collect()
            })
            .collect(),
        Model::Bit => (0..pipe.ncell)
            .flat_map(|cell| {
                (1..(1u64 << pipe.w)).map(move |v| {
                    vec![CellValue {
                        cell,
                        value: Some(v),
                    }]
                })
            })
            .collect(),
    }
}

/// Search one prefix for a contradicting pattern pair.
fn search_prefix(
    pipe: &Pipeline,
    mode: Propagation,
    budget: &SearchBudget,
    checks: &mut u64,
) -> Option<(Vec<CellValue>, Vec<CellValue>, Meet)> {
    let pats = patterns(pipe, budget.max_pattern_weight);
    let fwd: Vec<Vec<Vec<u8>>> = pats
        .iter()
        .map(|p| pipe.forward(&pipe.state_of(p).expect("pattern"), mode))
        .collect();
    let bwd: Vec<Vec<Vec<u8>>> = pats
        .iter()
        .map(|p| pipe.backward(&pipe.state_of(p).expect("pattern"), mode))
        .collect();
    for (i, f) in fwd.iter().enumerate() {
        for (o, b) in bwd.iter().enumerate() {
            if *checks >= budget.max_pair_checks {
                return None;
            }
            *checks += 1;
            if let Some(m) = pipe.conflict(f, b) {
                return Some((pats[i].clone(), pats[o].clone(), m));
            }
        }
    }
    None
}

/// Search the first `rounds` rounds of `p` for a miss-in-the-middle
/// distinguisher of the given propagation, trying both models. Shared by
/// the differential and zero-correlation front ends.
pub(crate) fn find_in_prefix(
    p: &Primitive,
    mode: Propagation,
    rounds: usize,
    fr: FinalRound,
    budget: &SearchBudget,
    checks: &mut u64,
    attempts: &mut Vec<Attempt>,
) -> Result<Option<MissInTheMiddle>, TechniqueError> {
    let mut last_err = None;
    let mut any_ok = false;
    for model in [Model::Word, Model::Bit] {
        let built = build_pipeline(p, rounds, fr, mode, model);
        let (pipe, dropped) = match built {
            Ok(x) => x,
            Err(e) => {
                last_err = Some(e);
                continue;
            }
        };
        any_ok = true;
        if fr == FinalRound::DropTrailingLinear && !dropped {
            // identical to AsGiven; do not repeat
            continue;
        }
        let found = search_prefix(&pipe, mode, budget, checks);
        attempts.push(Attempt {
            rounds,
            final_round: fr,
            model,
            found: found.is_some(),
        });
        if let Some((input, output, meet)) = found {
            return Ok(Some(MissInTheMiddle {
                propagation: mode,
                model,
                rounds,
                final_linear_dropped: dropped,
                cell_bits: pipe.w,
                input,
                output,
                meet,
            }));
        }
        if *checks >= budget.max_pair_checks {
            break;
        }
    }
    if !any_ok {
        return Err(last_err.unwrap_or_else(|| TechniqueError::Inapplicable("no model".into())));
    }
    Ok(None)
}

/// Longest-prefix search shared by both front ends.
pub(crate) fn longest(
    p: &Primitive,
    mode: Propagation,
    budget: &SearchBudget,
) -> Result<SearchReport, TechniqueError> {
    let mut report = SearchReport {
        best: None,
        attempts: vec![],
        pair_checks: 0,
        budget_exhausted: false,
    };
    let mut checks = 0u64;
    let top = budget.max_rounds.min(p.num_rounds());
    let mut first_err = None;
    let mut any_ok = false;
    for r in 1..=top {
        for fr in [FinalRound::AsGiven, FinalRound::DropTrailingLinear] {
            match find_in_prefix(p, mode, r, fr, budget, &mut checks, &mut report.attempts) {
                Ok(found) => {
                    any_ok = true;
                    if let Some(d) = found {
                        let better = report.best.as_ref().is_none_or(|b| d.rounds > b.rounds);
                        if better {
                            report.best = Some(d);
                        }
                    }
                }
                Err(e) => {
                    first_err.get_or_insert(e);
                }
            }
            if checks >= budget.max_pair_checks {
                report.budget_exhausted = true;
                report.pair_checks = checks;
                return Ok(report);
            }
        }
    }
    report.pair_checks = checks;
    if !any_ok {
        return Err(first_err.unwrap_or_else(|| TechniqueError::Inapplicable("no rounds".into())));
    }
    Ok(report)
}

/// Check one specific `(input, output)` pattern pair over the first
/// `rounds` rounds. Returns the contradiction if the pair is excluded by
/// the model, `None` if the model cannot exclude it (which does **not**
/// show the differential exists).
pub(crate) fn check_pair(
    p: &Primitive,
    mode: Propagation,
    rounds: usize,
    fr: FinalRound,
    model: Model,
    input: &[CellValue],
    output: &[CellValue],
) -> Result<Option<Meet>, TechniqueError> {
    let (pipe, _) = build_pipeline(p, rounds, fr, mode, model)?;
    let f = pipe.forward(&pipe.state_of(input)?, mode);
    let b = pipe.backward(&pipe.state_of(output)?, mode);
    Ok(pipe.conflict(&f, &b))
}

// ---------------------------------------------------------------------------
// Public entry points
// ---------------------------------------------------------------------------

/// Search `p` for the longest impossible differential reachable inside
/// `budget`, over prefixes of 1..=`budget.max_rounds` rounds in both
/// [`FinalRound`] variants and both [`Model`]s.
///
/// Returns [`TechniqueError::Inapplicable`] if no prefix can be modelled
/// (for instance an ARX primitive). `report.best` is `None` when no
/// contradiction was found within the budget; that is a statement about the
/// search, not about the cipher.
pub fn longest_impossible_differential(
    p: &Primitive,
    budget: &SearchBudget,
) -> Result<SearchReport, TechniqueError> {
    longest(p, Propagation::Differential, budget)
}

/// Search the first `rounds` rounds for an impossible differential in the
/// given final-round variant.
pub fn find_impossible_differential(
    p: &Primitive,
    rounds: usize,
    final_round: FinalRound,
    budget: &SearchBudget,
) -> Result<Option<MissInTheMiddle>, TechniqueError> {
    let mut checks = 0;
    find_in_prefix(
        p,
        Propagation::Differential,
        rounds,
        final_round,
        budget,
        &mut checks,
        &mut Vec::new(),
    )
}

/// Test whether the truncated differential `input -> output` over the first
/// `rounds` rounds is excluded by the miss-in-the-middle argument in
/// `model`. `Ok(Some(meet))` means excluded; `Ok(None)` means the model
/// does not exclude it.
pub fn check_impossible_differential(
    p: &Primitive,
    rounds: usize,
    final_round: FinalRound,
    model: Model,
    input: &[CellValue],
    output: &[CellValue],
) -> Result<Option<Meet>, TechniqueError> {
    check_pair(
        p,
        Propagation::Differential,
        rounds,
        final_round,
        model,
        input,
        output,
    )
}

// ---------------------------------------------------------------------------
// Wrong-key filtering
// ---------------------------------------------------------------------------

/// Result of [`impossible_key_recovery`].
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct KeyRecoveryReport {
    /// Ciphertext (= last-round-key) cells that were guessed.
    pub guessed_cells: Vec<usize>,
    /// Plaintext pairs queried from the oracle.
    pub pairs_queried: u64,
    /// Pairs whose ciphertext difference passed the key-independent filter.
    pub pairs_after_filter: u64,
    /// Number of guesses tested (`2^(cell_bits * guessed cells)`).
    pub guesses_total: u64,
    /// Guesses that no filtered pair contradicted. The true key is always
    /// among them if the distinguisher holds.
    pub survivors: Vec<Vec<u64>>,
}

/// The shape of a last round `[SboxParallel, Permute?, AddRoundKey]`.
pub(crate) struct LastRound {
    pub w: usize,
    pub inv_sbox: Vec<u32>,
    /// `src[j]` is the pre-round cell feeding ciphertext cell `j`.
    pub src: Vec<usize>,
    pub round_key: usize,
}

/// Parse the last round of `p`; fail unless it is a cell-aligned S-box
/// layer, an optional cell permutation and a full-width key addition.
pub(crate) fn parse_last_round(p: &Primitive) -> Result<LastRound, TechniqueError> {
    let last = p
        .rounds
        .last()
        .ok_or_else(|| TechniqueError::Inapplicable("no rounds".into()))?;
    let mut it = last.layers.iter();
    let Some(Layer::SboxParallel {
        sbox,
        width_bits,
        count,
        bit_offset: 0,
    }) = it.next()
    else {
        return inapplicable("last round must start with a full S-box layer");
    };
    let w = *width_bits;
    if w * count != p.block_bits || p.scratch_bits != 0 {
        return inapplicable("last S-box layer does not cover the block");
    }
    let s = &p.sboxes[sbox.0];
    let Some(inv) = s.inverse_table() else {
        return inapplicable("last S-box layer is not invertible");
    };
    let ncell = p.block_bits / w;
    let mut src: Vec<usize> = (0..ncell).collect();
    let mut next = it.next();
    if let Some(Layer::Permute { perm }) = next {
        for (j, sj) in src.iter_mut().enumerate() {
            let first = perm[j * w];
            let c = first / w;
            for b in 0..w {
                if perm[j * w + b] != c * w + b {
                    return inapplicable("last-round permutation is not cell-aligned");
                }
            }
            *sj = c;
        }
        next = it.next();
    }
    let Some(Layer::AddRoundKey {
        round_key,
        bit_offset: 0,
    }) = next
    else {
        return inapplicable("last round must end with a full-width AddRoundKey");
    };
    if p.key_schedule.round_key_bits() != p.block_bits || it.next().is_some() {
        return inapplicable("last round has unexpected layers");
    }
    Ok(LastRound {
        w,
        inv_sbox: inv,
        src,
        round_key: *round_key,
    })
}

/// Wrong-key-filtering key recovery for one appended round.
///
/// `p` must end with a round `[SboxParallel, Permute?, AddRoundKey]` (cell
/// aligned; see [`parse_last_round`]). `d` must be a [`Model::Word`]
/// distinguisher with `final_linear_dropped` found on exactly the first
/// `p.num_rounds() - 1` rounds, so the pattern lives in the state *before*
/// the linear layer(s) `D` that close round `p.num_rounds() - 1` (MixColumns
/// for AES). `guess_cells` are ciphertext cells (= cells of the last round
/// key) whose key values are guessed, at most 24 key bits in total.
///
/// Pairs `(P, P xor delta)` with `delta` taken from the input pattern of
/// `d` are queried. A pair is kept if the ciphertext difference is zero on
/// every non-guessed cell; the difference of the state before the last
/// round is then zero there too (the key cancels and the S-box is
/// bijective) and, on the guessed cells, equals
/// `S^-1(c ^ k) ^ S^-1(c' ^ k)` for the guessed `k`. That difference is
/// mapped through `D^-1` and compared with the output pattern: a guess for
/// which it is non-zero exactly on the output cells would exhibit the
/// impossible differential and is discarded. Under the distinguisher the
/// true key is never discarded; the report lists the guesses that survive.
/// This is the wrong-key-filtering step of impossible-differential attacks
/// (Biham-Biryukov-Shamir 1999). The filter only discriminates keys when
/// two or more guessed cells feed one cell of `D^-1` (otherwise the
/// zero/non-zero pattern does not depend on the key); choose `guess_cells`
/// accordingly.
///
/// `oracle` encrypts one block with the secret key.
pub fn impossible_key_recovery<F>(
    p: &Primitive,
    d: &MissInTheMiddle,
    guess_cells: &[usize],
    mut oracle: F,
    max_pairs: u64,
    seed: u64,
) -> Result<KeyRecoveryReport, TechniqueError>
where
    F: FnMut(&[u8]) -> Vec<u8>,
{
    if d.propagation != Propagation::Differential || d.model != Model::Word {
        return inapplicable("needs a word-model impossible differential");
    }
    if !d.final_linear_dropped || d.rounds + 1 != p.num_rounds() {
        return inapplicable(
            "distinguisher must cover all rounds but the last, with its closing linear layer dropped",
        );
    }
    let lr = parse_last_round(p)?;
    let w = lr.w;
    let ncell = p.block_bits / w;
    if w != d.cell_bits {
        return inapplicable("cell width mismatch");
    }
    if guess_cells.is_empty() || guess_cells.iter().any(|&j| j >= ncell) {
        return inapplicable("bad guess cells");
    }
    let gbits = w * guess_cells.len();
    if gbits > 24 {
        return inapplicable("more than 24 guessed key bits");
    }
    if d.output.iter().any(|c| c.value.is_some()) {
        return inapplicable("output pattern with exact values is not supported");
    }
    // D: the linear layers dropped from round d.rounds, in order.
    let mut dropped: Vec<&Gf2Matrix> = Vec::new();
    for l in p.rounds[d.rounds - 1].layers.iter().rev() {
        match l {
            Layer::AddRoundKey { .. } | Layer::AddConst { .. } => {}
            Layer::LinearGf2 { matrix } if matrix.as_permutation().is_none() => {
                dropped.push(matrix)
            }
            _ => break,
        }
    }
    let mut dm = Gf2Matrix::identity(p.block_bits);
    for m in dropped.iter().rev() {
        dm = m.mul(&dm);
    }
    let Some(dinv) = dm.inverse() else {
        return inapplicable("singular dropped layer");
    };
    let out_pre: Vec<usize> = d.output.iter().map(|c| c.cell).collect();
    let nonguessed: Vec<usize> = (0..ncell).filter(|j| !guess_cells.contains(j)).collect();

    let mut rng = seed;
    let mut next_u64 = || {
        rng = rng
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        rng >> 17
    };
    let nbytes = p.block_bytes();
    let guesses_total = 1u64 << gbits;
    let mut alive = vec![true; guesses_total as usize];
    let (mut queried, mut passed) = (0u64, 0u64);
    let mask = (1u64 << w) - 1;
    while queried < max_pairs {
        queried += 1;
        let pt: Vec<u8> = (0..nbytes).map(|_| next_u64() as u8).collect();
        let mut bits = p.block_codec.encode(&pt);
        for c in &d.input {
            let mut v = 0;
            while v == 0 {
                v = next_u64() & mask;
            }
            let cur = get_bits(&bits, c.cell * w, w);
            set_bits(&mut bits, c.cell * w, w, cur ^ v);
        }
        let pt2 = p.block_codec.decode(&bits, p.block_bits);
        let (b1, b2) = (
            p.block_codec.encode(&oracle(&pt)),
            p.block_codec.encode(&oracle(&pt2)),
        );
        if nonguessed
            .iter()
            .any(|&j| get_bits(&b1, j * w, w) != get_bits(&b2, j * w, w))
        {
            continue;
        }
        passed += 1;
        for g in 0..guesses_total {
            if !alive[g as usize] {
                continue;
            }
            let mut x = vec![0u64; words_for(p.block_bits)];
            for (gi, &j) in guess_cells.iter().enumerate() {
                let k = g >> (w * gi) & mask;
                let a = lr.inv_sbox[(get_bits(&b1, j * w, w) ^ k) as usize] as u64;
                let b = lr.inv_sbox[(get_bits(&b2, j * w, w) ^ k) as usize] as u64;
                set_bits(&mut x, lr.src[j] * w, w, a ^ b);
            }
            let z = dinv.mul_vec(&x);
            let nonzero: Vec<usize> = (0..ncell)
                .filter(|&i| get_bits(&z, i * w, w) != 0)
                .collect();
            if nonzero == out_pre {
                alive[g as usize] = false;
            }
        }
    }
    let survivors = (0..guesses_total)
        .filter(|&g| alive[g as usize])
        .map(|g| {
            (0..guess_cells.len())
                .map(|gi| g >> (w * gi) & mask)
                .collect()
        })
        .collect();
    Ok(KeyRecoveryReport {
        guessed_cells: guess_cells.to_vec(),
        pairs_queried: queried,
        pairs_after_filter: passed,
        guesses_total,
        survivors,
    })
}

/// True last-round-key cell values of `p` under `key` for the ciphertext
/// cells `cells` (helper for tests and callers that hold the key).
pub fn last_round_key_cells(
    p: &Primitive,
    key: &[u8],
    cells: &[usize],
) -> Result<Vec<u64>, TechniqueError> {
    let lr = parse_last_round(p)?;
    let rk = expand_key(p, key);
    Ok(cells
        .iter()
        .map(|&j| get_bits(&rk[lr.round_key], j * lr.w, lr.w))
        .collect())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::sym_ir::eval;
    use crate::cryptanalysis::sym_ir::primitives::{
        aes128, present80, sbox_from_u8, speck, toyspn,
    };
    use crate::cryptanalysis::sym_techniques::zero_correlation::encryption_table;

    fn cell(c: usize) -> Vec<CellValue> {
        vec![CellValue {
            cell: c,
            value: None,
        }]
    }

    fn pairs_excluded(p: &Primitive, rounds: usize, fr: FinalRound) -> usize {
        let mut n = 0;
        for i in 0..16 {
            for j in 0..16 {
                if check_impossible_differential(p, rounds, fr, Model::Word, &cell(i), &cell(j))
                    .unwrap()
                    .is_some()
                {
                    n += 1;
                }
            }
        }
        n
    }

    /// Positive control: the AES 1-active-byte to 1-active-byte impossible
    /// differential (Biham-Keller; Knudsen), found generically from the IR.
    /// Length 4 is `reduced(4, false)` (FIPS last round, "3.5 rounds" in
    /// Biham-Keller counting). The same pair is also excluded at 3 rounds
    /// (which the model finds as a shorter, FIPS-form distinguisher), is
    /// not excluded with a kept final MixColumns at 4 rounds, and not at 5.
    #[test]
    fn aes_one_to_one_impossible_differential() {
        let p4 = aes128::reduced(4, false);
        assert_eq!(pairs_excluded(&p4, 4, FinalRound::AsGiven), 256);
        let d = find_impossible_differential(&p4, 4, FinalRound::AsGiven, &SearchBudget::default())
            .unwrap()
            .expect("found");
        assert_eq!((d.rounds, d.input.len(), d.output.len()), (4, 1, 1));
        assert_eq!(d.model, Model::Word);
        assert_eq!(
            pairs_excluded(&aes128::reduced(3, false), 3, FinalRound::AsGiven),
            256
        );
        assert_eq!(
            pairs_excluded(&aes128::reduced(4, true), 4, FinalRound::AsGiven),
            0
        );
        assert_eq!(
            pairs_excluded(&aes128::reduced(5, false), 5, FinalRound::AsGiven),
            0
        );
        // Dropping the last MixColumns of the 4-round prefix recovers it.
        let p4mc = aes128::reduced(4, true);
        let d = find_impossible_differential(
            &p4mc,
            4,
            FinalRound::DropTrailingLinear,
            &SearchBudget::default(),
        )
        .unwrap()
        .expect("found");
        assert!(d.final_linear_dropped);
    }

    /// The longest search on full AES-128 stops at 4 rounds.
    #[test]
    fn aes_longest_is_four_rounds() {
        let b = SearchBudget {
            max_rounds: 8,
            ..SearchBudget::default()
        };
        let r = longest_impossible_differential(&aes128::aes128(), &b).unwrap();
        let best = r.best.expect("found");
        assert_eq!(best.rounds, 4);
        assert!(best.final_linear_dropped);
        assert!(!r.budget_exhausted);
        assert!(!r.attempts.iter().any(|a| a.found && a.rounds >= 5));
    }

    /// PRESENT-80: the bit-model search reaches a 6-round impossible
    /// differential (single-cell input to single-cell output) and nothing
    /// longer within the default budget. The published impossible
    /// differential for PRESENT is also 6 rounds, so the search matches,
    /// not exceeds, it.
    #[test]
    fn present_reaches_six_rounds() {
        let b = SearchBudget {
            max_rounds: 9,
            ..SearchBudget::default()
        };
        let r = longest_impossible_differential(&present80::present80(), &b).unwrap();
        let best = r.best.expect("found");
        assert_eq!(best.rounds, 6);
        assert_eq!(best.model, Model::Bit);
    }

    #[test]
    fn arx_is_rejected() {
        let r = longest_impossible_differential(&speck::speck64_128(), &SearchBudget::default());
        assert!(matches!(r, Err(TechniqueError::Inapplicable(_))));
    }

    /// Independent numerical check of the word-model claim on small-scale
    /// AES SR(4,2,2,4): for several keys, no plaintext pair with a
    /// difference active only in the input cell yields a ciphertext
    /// difference active only in the output cell (all 2^16 plaintexts).
    #[test]
    fn small_scale_exhaustive_agrees() {
        let p = aes128::small_scale(4);
        let d = find_impossible_differential(&p, 4, FinalRound::AsGiven, &SearchBudget::default())
            .unwrap()
            .expect("found");
        let (ci, co) = (d.input[0].cell, d.output[0].cell);
        for key in [[0x12u8, 0x34], [0xa5, 0x5a], [0x00, 0x00]] {
            let t = encryption_table(&p, &key, 4);
            for v in 1u32..16 {
                for x in 0..(1u32 << 16) {
                    let dd = t[x as usize] ^ t[(x ^ (v << (4 * ci))) as usize];
                    let only_out = dd != 0 && dd & !(0xf << (4 * co)) == 0;
                    assert!(!only_out, "witness found: key {key:?} x {x:#x} v {v}");
                }
            }
        }
    }

    /// Same for ToySpn through the bit model with exact differences.
    #[test]
    fn toyspn_bit_model_exhaustive_agrees() {
        let sb = sbox_from_u8(4, &crate::symmetric::present::SBOX);
        let p = toyspn::toyspn(&sb, 5);
        let r = longest_impossible_differential(&p, &SearchBudget::default()).unwrap();
        let d = r.best.expect("found");
        assert!(d.rounds >= 2);
        assert_eq!((d.input.len(), d.output.len()), (1, 1));
        let (ci, vi) = (d.input[0].cell, d.input[0].value.unwrap_or(0));
        let (co, vo) = (d.output[0].cell, d.output[0].value.unwrap_or(0));
        for key in [
            [1u8, 2, 3, 4, 5, 6, 7, 8],
            [0xff, 0, 0xaa, 0x55, 9, 8, 7, 6],
        ] {
            let t = encryption_table(&p, &key, d.rounds);
            for x in 0..(1u32 << 16) {
                let dd = t[x as usize] ^ t[(x ^ (vi as u32) << (4 * ci)) as usize];
                if d.model == Model::Bit {
                    assert_ne!(dd, (vo as u32) << (4 * co), "witness for exact difference");
                } else {
                    assert!(!(dd != 0 && dd & !(0xf << (4 * co)) == 0));
                }
            }
        }
    }

    /// Wrong-key filtering on SR(5,2,2,4): the 4-round distinguisher with
    /// its closing MixColumns dropped plus one appended round, guessing the
    /// two last-round key cells that feed one MixColumns column, leaves
    /// exactly the true key.
    #[test]
    fn key_recovery_on_small_scale() {
        let p = aes128::small_scale(5);
        let d = find_impossible_differential(
            &p,
            4,
            FinalRound::DropTrailingLinear,
            &SearchBudget::default(),
        )
        .unwrap()
        .expect("found");
        assert_eq!((d.input[0].cell, d.output[0].cell), (0, 0));
        let key = [0x3cu8, 0xa7];
        let cells = [0usize, 3];
        let rep =
            impossible_key_recovery(&p, &d, &cells, |b| eval(&p, &key, b), 600_000, 7).unwrap();
        let truth = last_round_key_cells(&p, &key, &cells).unwrap();
        assert!(rep.survivors.contains(&truth));
        assert_eq!(rep.survivors.len(), 1, "report: {rep:?}");
        assert!(rep.pairs_after_filter > 100);
        // wrong structure is refused: as-given distinguisher, wrong rounds
        let d3 = find_impossible_differential(&p, 3, FinalRound::AsGiven, &SearchBudget::default())
            .unwrap()
            .expect("found");
        assert!(impossible_key_recovery(&p, &d3, &cells, |b| eval(&p, &key, b), 10, 1).is_err());
    }
}
