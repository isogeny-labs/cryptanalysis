//! Demirci-Selcuk delta-set / multiset structure derived from the
//! [`sym_ir`](crate::cryptanalysis::sym_ir) IR, a runnable small instance,
//! and the Lambda-set (Square) last-round key recovery that shares the
//! same set machinery.
//!
//! References.
//!
//! * H. Demirci, A. A. Selcuk, "A meet-in-the-middle attack on 8-round
//!   AES", FSE 2008 (the ordered sequence of one byte after four rounds of
//!   a delta-set depends on 25 byte parameters in that paper).
//! * O. Dunkelman, N. Keller, A. Shamir, "Improved single-key attacks on
//!   8-round AES-192 and AES-256", ASIACRYPT 2010 (J. Cryptology 28, 2015):
//!   the *multiset* of the byte values, which no longer depends on the
//!   offset of the active cell, reduces the count to 24.
//! * J. Daemen, L. Knudsen, V. Rijmen, "The block cipher Square", FSE 1997
//!   (Lambda-sets and the Square attack).
//!
//! # Dependency model
//!
//! A *delta-set* is `2^w` states that take every value in one active cell
//! (the other cells constant); `w` is the S-box width. Following the
//! parameter count of Demirci-Selcuk, [`delta_set_dependencies`] tracks, for
//! each cell, whether it is a function of the active value (`varying`) and
//! the set of byte-sized *parameters* that determine that function:
//!
//! * between two S-box layers the layers form one affine map. Every
//!   varying output cell that receives a key addition or a contribution
//!   from a constant (key-dependent, unknown) cell gets **one** new offset
//!   parameter, however many constants were merged into it;
//! * a linear layer gives an output cell the union of the parameter sets of
//!   its varying inputs; S-box layers add no parameters;
//! * the offset added to the active cell before the first S-box is the
//!   *active offset*; it only relabels the active value and drops out of
//!   the multiset.
//!
//! The target cell is read before the final key addition of the last
//! counted round (its offset is a constant shift removed by comparing
//! sequences up to a constant), unless
//! [`DeltaSetSpec::include_final_offset`] is set.
//!
//! The model counts *cells*, not bits, and does not exploit any algebraic
//! relation inside a cell (e.g. that a ToySpn cell sees only one bit of an
//! S-box output); counts are therefore upper bounds on the true dimension
//! of the family.
//!
//! # Cost table
//!
//! [`delta_set_cost_table`] returns data, offline-table and online-guess
//! sizes in `log2` units from the same dependency analysis. It does **not**
//! run the attack, and its time and memory entries are model quantities
//! (one delta-set of `2^w` partial decryptions per key guess; table entries
//! not bytes), not a reproduction of the published totals, which also use
//! many delta-sets and key-schedule relations.

use super::impossible::{block_nonzero, parse_last_round, sub_rank, TechniqueError};
use crate::cryptanalysis::sym_ir::gf2::{get_bits, set_bits};
use crate::cryptanalysis::sym_ir::{
    eval, eval_rounds, expand_key, Codec, Gf2Matrix, KeySchedule, Layer, Primitive,
};
use std::collections::{BTreeSet, HashMap};

/// Parameter count of the ordered sequence after four rounds in
/// Demirci-Selcuk (FSE 2008).
pub const DEMIRCI_SELCUK_PARAMS: usize = 25;

/// Parameter count of the multiset after four rounds in
/// Dunkelman-Keller-Shamir (ASIACRYPT 2010).
pub const DUNKELMAN_KELLER_SHAMIR_PARAMS: usize = 24;

// ---------------------------------------------------------------------------
// Set construction (byte level helpers shared with the AES wrappers)
// ---------------------------------------------------------------------------

/// A delta-set (equally a Lambda-set): `2^cell_bits` blocks equal to `base`
/// except in cell `active_cell`, which takes every value once. Cell `c` is
/// block bits `c*cell_bits ..` in the primitive's block codec; the block is
/// given and returned as bytes.
pub fn delta_set(p: &Primitive, base: &[u8], active_cell: usize, cell_bits: usize) -> Vec<Vec<u8>> {
    let mut bits = p.block_codec.encode(base);
    (0..(1u64 << cell_bits))
        .map(|v| {
            set_bits(&mut bits, active_cell * cell_bits, cell_bits, v);
            p.block_codec.decode(&bits, p.block_bits)
        })
        .collect()
}

/// Ordered sequence of cell `cell` over a set of blocks (e.g. ciphertexts).
pub fn ordered_sequence(
    p: &Primitive,
    blocks: &[Vec<u8>],
    cell: usize,
    cell_bits: usize,
) -> Vec<u64> {
    blocks
        .iter()
        .map(|b| get_bits(&p.block_codec.encode(b), cell * cell_bits, cell_bits))
        .collect()
}

/// Histogram of the values of cell `cell` over a set of blocks.
pub fn multiset(p: &Primitive, blocks: &[Vec<u8>], cell: usize, cell_bits: usize) -> Vec<u32> {
    let mut h = vec![0u32; 1 << cell_bits];
    for v in ordered_sequence(p, blocks, cell, cell_bits) {
        h[v as usize] += 1;
    }
    h
}

// ---------------------------------------------------------------------------
// Dependency analysis
// ---------------------------------------------------------------------------

/// What a parameter is.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ParamKind {
    /// Offset added to the active value before the first S-box; removed in
    /// multiset mode.
    ActiveOffset,
    /// Offset of an affine map between S-box layers.
    Offset,
}

/// One byte-sized parameter of the ordered sequence.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DeltaSetParam {
    /// Kind of parameter.
    pub kind: ParamKind,
    /// Index of the affine segment (0 = before the first S-box layer).
    pub segment: usize,
    /// Cell the offset is applied to.
    pub cell: usize,
    /// Round key whose key addition covers this cell in the segment, if any
    /// (used by the runnable instance).
    pub round_key: Option<usize>,
}

/// Which window of rounds and which cells to analyse.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DeltaSetSpec {
    /// Index (0-based) of the first round of the window.
    pub first_round: usize,
    /// Number of rounds in the window.
    pub inner_rounds: usize,
    /// Cell that takes all values at the window input.
    pub active_cell: usize,
    /// Cell whose ordered sequence is analysed at the window output.
    pub target_cell: usize,
    /// Count the target cell's own final key-addition offset as a
    /// parameter.
    pub include_final_offset: bool,
}

/// Result of [`delta_set_dependencies`].
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DependencyReport {
    /// The analysed window.
    pub spec: DeltaSetSpec,
    /// Cell width in bits.
    pub cell_bits: usize,
    /// Whether the target is a function of the active value at all.
    pub target_varying: bool,
    /// Parameters of the ordered sequence of the target cell.
    pub params: Vec<DeltaSetParam>,
    /// `params.len()`: parameters of the ordered sequence.
    pub ordered_count: usize,
    /// Parameters of the multiset (the active offset removed).
    pub multiset_count: usize,
}

#[derive(Clone, Debug)]
struct Dep {
    varying: bool,
    off: bool,
    key: Option<usize>,
    params: BTreeSet<usize>,
}

fn cell_width(p: &Primitive) -> Result<usize, TechniqueError> {
    let mut w = 0;
    for r in &p.rounds {
        for l in &r.layers {
            match l {
                Layer::Arx { .. } => {
                    return Err(TechniqueError::Inapplicable(format!(
                        "{}: ARX layer",
                        p.name
                    )))
                }
                Layer::SboxParallel {
                    width_bits,
                    count,
                    bit_offset,
                    ..
                } => {
                    if w == 0 {
                        w = *width_bits;
                    }
                    if *width_bits != w || *bit_offset != 0 || width_bits * count != p.block_bits {
                        return Err(TechniqueError::Inapplicable(
                            "S-box layers must share one width and cover the block".into(),
                        ));
                    }
                }
                _ => {}
            }
        }
    }
    if w == 0 || p.scratch_bits != 0 {
        return Err(TechniqueError::Inapplicable("no word structure".into()));
    }
    Ok(w)
}

fn layer_matrix(l: &Layer) -> Option<Gf2Matrix> {
    match l {
        Layer::Permute { perm } => Some(Gf2Matrix::from_permutation(perm)),
        Layer::LinearGf2 { matrix } => Some(matrix.clone()),
        _ => None,
    }
}

fn finish_segment(
    state: &mut [Dep],
    table: &mut Vec<DeltaSetParam>,
    segment: usize,
    skip_cell: Option<usize>,
) {
    for (c, d) in state.iter_mut().enumerate() {
        if d.varying && d.off && Some(c) != skip_cell {
            let kind = if segment == 0 && d.params.is_empty() {
                ParamKind::ActiveOffset
            } else {
                ParamKind::Offset
            };
            table.push(DeltaSetParam {
                kind,
                segment,
                cell: c,
                round_key: d.key,
            });
            d.params.insert(table.len() - 1);
        }
        d.off = false;
    }
}

/// Count the parameters that determine the ordered sequence (and the
/// multiset) of `spec.target_cell` after the window of rounds, by
/// dependency propagation through the IR. See the [module docs](self) for
/// the model.
pub fn delta_set_dependencies(
    p: &Primitive,
    spec: &DeltaSetSpec,
) -> Result<DependencyReport, TechniqueError> {
    let w = cell_width(p)?;
    let ncell = p.block_bits / w;
    if spec.first_round + spec.inner_rounds > p.num_rounds()
        || spec.active_cell >= ncell
        || spec.target_cell >= ncell
        || spec.inner_rounds == 0
    {
        return Err(TechniqueError::Inapplicable("window out of range".into()));
    }
    let mut state: Vec<Dep> = (0..ncell)
        .map(|c| Dep {
            varying: c == spec.active_cell,
            off: true,
            key: None,
            params: BTreeSet::new(),
        })
        .collect();
    let mut table: Vec<DeltaSetParam> = Vec::new();
    let mut segment = 0usize;
    for r in &p.rounds[spec.first_round..spec.first_round + spec.inner_rounds] {
        for l in &r.layers {
            match l {
                Layer::SboxParallel { .. } => {
                    finish_segment(&mut state, &mut table, segment, None);
                    segment += 1;
                }
                Layer::Permute { .. } | Layer::LinearGf2 { .. } => {
                    let m = layer_matrix(l).expect("linear");
                    let next: Vec<Dep> = (0..ncell)
                        .map(|o| {
                            let contrib: Vec<&Dep> = (0..ncell)
                                .filter(|&c| block_nonzero(&m, w, o, c))
                                .map(|c| &state[c])
                                .collect();
                            let varying = contrib.iter().any(|d| d.varying);
                            let mut params = BTreeSet::new();
                            for d in contrib.iter().filter(|d| d.varying) {
                                params.extend(d.params.iter().copied());
                            }
                            let keys: BTreeSet<Option<usize>> =
                                contrib.iter().map(|d| d.key).collect();
                            Dep {
                                varying,
                                off: contrib.iter().any(|d| d.off || !d.varying),
                                key: if keys.len() == 1 {
                                    keys.into_iter().next().flatten()
                                } else {
                                    None
                                },
                                params,
                            }
                        })
                        .collect();
                    state = next;
                }
                Layer::AddRoundKey {
                    round_key,
                    bit_offset,
                } => {
                    let rkb = p.key_schedule.round_key_bits();
                    for (c, d) in state.iter_mut().enumerate() {
                        let (lo, hi) = (c * w, (c + 1) * w);
                        if lo < bit_offset + rkb && hi > *bit_offset {
                            d.off = true;
                            d.key = Some(*round_key);
                        }
                    }
                }
                Layer::AddConst { .. } => {}
                Layer::Arx { .. } => {
                    return Err(TechniqueError::Inapplicable("ARX layer".into()));
                }
            }
        }
    }
    let skip = (!spec.include_final_offset).then_some(spec.target_cell);
    finish_segment(&mut state, &mut table, segment, skip);
    let t = &state[spec.target_cell];
    let params: Vec<DeltaSetParam> = t.params.iter().map(|&i| table[i]).collect();
    let ordered_count = params.len();
    let multiset_count = params
        .iter()
        .filter(|q| q.kind != ParamKind::ActiveOffset)
        .count();
    Ok(DependencyReport {
        spec: *spec,
        cell_bits: w,
        target_varying: t.varying,
        params,
        ordered_count,
        multiset_count,
    })
}

// ---------------------------------------------------------------------------
// Cost table
// ---------------------------------------------------------------------------

/// Data / offline / online cost of a delta-set MITM, in `log2` units of the
/// model described in the [module docs](self).
#[derive(Clone, Debug, PartialEq)]
pub struct DeltaSetCostTable {
    /// Primitive name.
    pub primitive: String,
    /// Rounds before the window (data-side structure).
    pub front_rounds: usize,
    /// Rounds in the window.
    pub inner_rounds: usize,
    /// Rounds after the window (guessed from the ciphertext).
    pub back_rounds: usize,
    /// Cell width.
    pub cell_bits: usize,
    /// Parameters of the ordered sequence (Demirci-Selcuk style).
    pub params_ordered: usize,
    /// Parameters of the multiset (Dunkelman-Keller-Shamir style).
    pub params_multiset: usize,
    /// Plaintext cells that must range over all values for the front
    /// rounds to deliver a delta-set at the window input.
    pub data_cells: usize,
    /// `log2` of the number of chosen plaintexts: `cell_bits * data_cells`.
    pub data_log2: f64,
    /// `log2` of the offline table size, ordered sequences, in entries.
    pub table_ordered_log2: f64,
    /// `log2` of the offline table size for multisets, in entries.
    pub table_multiset_log2: f64,
    /// Key cells guessed in the front rounds (trailing key additions that
    /// only shift the active value are not guessed).
    pub front_key_cells: usize,
    /// Key cells guessed in the back rounds, key-schedule relations not
    /// used.
    pub back_key_cells: usize,
    /// Ciphertext cells the target depends on.
    pub ciphertext_cells: usize,
    /// `log2` of the number of raw key guesses.
    pub guesses_log2: f64,
    /// Model online time: one delta-set of `2^cell_bits` partial
    /// decryptions per guess.
    pub online_time_log2: f64,
    /// Model total time: `max(offline build, online)`, ordered sequences.
    pub time_ordered_log2: f64,
    /// Model memory in table entries, ordered sequences.
    pub memory_ordered_log2: f64,
}

/// Cells of a layer input needed to know the given output cells of the
/// layer's inverse (and vice versa), via the inverse matrix blocks.
fn need_through(l: &Layer, w: usize, ncell: usize, need: &BTreeSet<usize>) -> BTreeSet<usize> {
    let Some(m) = layer_matrix(l) else {
        return need.clone();
    };
    let inv = m.inverse().expect("invertible linear layer");
    let mut out = BTreeSet::new();
    for &s in need {
        for c in 0..ncell {
            if block_nonzero(&inv, w, c, s) {
                out.insert(c);
            }
        }
    }
    out
}

/// The delta-set MITM cost table for `p` with `front_rounds` rounds before
/// the window, `inner_rounds` in it (starting at round `front_rounds`) and
/// the remaining rounds after it; `active_cell` is the cell at the window
/// input and `target_cell` the cell at its output. Runs only the
/// dependency analysis and cone counts, never the attack.
///
/// For AES-128 with 7 rounds (`front_rounds = 1`, `inner_rounds = 4`,
/// `active_cell = target_cell = 0`) the window has 25 ordered parameters
/// (Demirci-Selcuk) and 24 multiset parameters (Dunkelman-Keller-Shamir).
pub fn delta_set_cost_table(
    p: &Primitive,
    front_rounds: usize,
    inner_rounds: usize,
    active_cell: usize,
    target_cell: usize,
) -> Result<DeltaSetCostTable, TechniqueError> {
    let w = cell_width(p)?;
    let ncell = p.block_bits / w;
    if front_rounds + inner_rounds > p.num_rounds() {
        return Err(TechniqueError::Inapplicable("window out of range".into()));
    }
    let back_rounds = p.num_rounds() - front_rounds - inner_rounds;
    let dep = delta_set_dependencies(
        p,
        &DeltaSetSpec {
            first_round: front_rounds,
            inner_rounds,
            active_cell,
            target_cell,
            include_final_offset: false,
        },
    )?;
    // Front cone: plaintext cells needed so that the window input varies in
    // the active cell only. Walk the front layers backwards.
    let mut need: BTreeSet<usize> = [active_cell].into();
    let mut front_keys = 0usize;
    let front_layers: Vec<&Layer> = p.rounds[..front_rounds]
        .iter()
        .flat_map(|r| r.layers.iter())
        .collect();
    let last_sbox = front_layers
        .iter()
        .rposition(|l| matches!(l, Layer::SboxParallel { .. }));
    for (i, l) in front_layers.iter().enumerate().rev() {
        match l {
            Layer::AddRoundKey { .. } => {
                if last_sbox.is_some_and(|ls| i < ls) {
                    front_keys += need.len();
                }
            }
            Layer::Permute { .. } | Layer::LinearGf2 { .. } => {
                need = need_through(l, w, ncell, &need);
            }
            _ => {}
        }
    }
    let data_cells = need.len();
    // Back cone: walk the back layers forwards from the target.
    let mut need: BTreeSet<usize> = [target_cell].into();
    let mut back_keys = 0usize;
    for l in p.rounds[front_rounds + inner_rounds..]
        .iter()
        .flat_map(|r| r.layers.iter())
    {
        match l {
            Layer::AddRoundKey { .. } => back_keys += need.len(),
            Layer::Permute { .. } | Layer::LinearGf2 { .. } => {
                need = need_through(l, w, ncell, &need);
            }
            _ => {}
        }
    }
    let wf = w as f64;
    let table_ordered = wf * dep.ordered_count as f64;
    let table_multiset = wf * dep.multiset_count as f64;
    let guesses = wf * (front_keys + back_keys) as f64;
    let online = guesses + wf;
    Ok(DeltaSetCostTable {
        primitive: p.name.clone(),
        front_rounds,
        inner_rounds,
        back_rounds,
        cell_bits: w,
        params_ordered: dep.ordered_count,
        params_multiset: dep.multiset_count,
        data_cells,
        data_log2: wf * data_cells as f64,
        table_ordered_log2: table_ordered,
        table_multiset_log2: table_multiset,
        front_key_cells: front_keys,
        back_key_cells: back_keys,
        ciphertext_cells: need.len(),
        guesses_log2: guesses,
        online_time_log2: online,
        time_ordered_log2: (table_ordered + wf).max(online),
        memory_ordered_log2: table_ordered,
    })
}

// ---------------------------------------------------------------------------
// Runnable instance
// ---------------------------------------------------------------------------

/// Result of [`delta_set_mitm_demo`].
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DemoReport {
    /// Parameters of the ordered sequence (from the dependency analysis).
    pub params: usize,
    /// Parameter assignments enumerated for the offline table.
    pub table_assignments: usize,
    /// Distinct normalised sequences stored.
    pub table_distinct: usize,
    /// Last-round key guesses tried online.
    pub guesses: usize,
    /// Guesses whose sequence is in the table.
    pub survivors: Vec<u64>,
    /// The true last-round-key value of the guessed cell.
    pub true_key_cell: u64,
    /// Ciphertext cell guessed.
    pub ciphertext_cell: usize,
}

/// Run a delta-set meet-in-the-middle on a small primitive.
///
/// `p` must have `inner_rounds + 1` rounds, the last of the form
/// `[SboxParallel, Permute?, AddRoundKey]`, and every offset of the
/// dependency analysis must sit on a round-key addition. Offline, all
/// assignments of the parameters found by [`delta_set_dependencies`] are
/// enumerated; each is realised by evaluating the primitive over the
/// delta-set with *independent* round keys equal to the parameter values
/// (all other key cells and the constant cells zero) and the sequence at
/// `target_cell` is stored normalised by its first element (the final
/// offset is a shift). Online, the delta-set is encrypted under `key`, the
/// last round is peeled by each guess of the one key cell the target
/// depends on, and the normalised sequence is looked up. The table covers a
/// superset of the sequences the real key can produce, so the true guess
/// always survives; wrong guesses survive only by sequence collision.
///
/// At most 20 table-index bits are supported.
pub fn delta_set_mitm_demo(
    p: &Primitive,
    key: &[u8],
    inner_rounds: usize,
    active_cell: usize,
    target_cell: usize,
) -> Result<DemoReport, TechniqueError> {
    if p.num_rounds() != inner_rounds + 1 {
        return Err(TechniqueError::Inapplicable(
            "primitive must have exactly one round after the window".into(),
        ));
    }
    let lr = parse_last_round(p)?;
    let w = lr.w;
    let dep = delta_set_dependencies(
        p,
        &DeltaSetSpec {
            first_round: 0,
            inner_rounds,
            active_cell,
            target_cell,
            include_final_offset: false,
        },
    )?;
    if !dep.target_varying {
        return Err(TechniqueError::Inapplicable("target does not vary".into()));
    }
    let nparams = dep.params.len();
    if w * nparams > 20 {
        return Err(TechniqueError::Inapplicable(
            "table too large to enumerate".into(),
        ));
    }
    let rkb = p.key_schedule.round_key_bits();
    let nrk = p.key_schedule.num_round_keys();
    let free = with_independent_round_keys(p)?;
    // Parameter -> bit offset in the independent key.
    let mut slots = Vec::new();
    for q in &dep.params {
        let Some(rk) = q.round_key else {
            return Err(TechniqueError::Inapplicable(
                "an offset has no round-key addition to realise it".into(),
            ));
        };
        let off = first_key_bit(p, rk, q.cell, w)?;
        slots.push(rk * rkb + off);
    }
    let nb = p.block_bytes();
    let seq_of = |assign: u64| -> Vec<u8> {
        let mut kbits = vec![0u64; (nrk * rkb).div_ceil(64)];
        for (i, &s) in slots.iter().enumerate() {
            set_bits(&mut kbits, s, w, assign >> (w * i));
        }
        let kb = free.key_codec.decode(&kbits, free.key_bits);
        let mut bits = vec![0u64; p.block_bits.div_ceil(64)];
        let mut seq = Vec::with_capacity(1 << w);
        for v in 0..(1u64 << w) {
            set_bits(&mut bits, active_cell * w, w, v);
            let pt = p.block_codec.decode(&bits, p.block_bits);
            debug_assert_eq!(pt.len(), nb);
            let ct = eval_rounds(&free, &kb, &pt, inner_rounds);
            seq.push(get_bits(&p.block_codec.encode(&ct), target_cell * w, w) as u8);
        }
        let z = seq[0];
        seq.iter().map(|x| x ^ z).collect()
    };
    let assignments = 1usize << (w * nparams);
    let mut table: HashMap<Vec<u8>, u32> = HashMap::new();
    for a in 0..assignments as u64 {
        *table.entry(seq_of(a)).or_insert(0) += 1;
    }
    // Online.
    let base = vec![0u8; nb];
    let cts: Vec<Vec<u8>> = delta_set(p, &base, active_cell, w)
        .iter()
        .map(|pt| eval(p, key, pt))
        .collect();
    let j = lr
        .src
        .iter()
        .position(|&s| s == target_cell)
        .expect("bijective");
    let ct_vals = ordered_sequence(p, &cts, j, w);
    let mut survivors = Vec::new();
    for g in 0..(1u64 << w) {
        let s: Vec<u8> = ct_vals
            .iter()
            .map(|&c| lr.inv_sbox[(c ^ g) as usize] as u8)
            .collect();
        let z = s[0];
        let norm: Vec<u8> = s.iter().map(|x| x ^ z).collect();
        if table.contains_key(&norm) {
            survivors.push(g);
        }
    }
    let rks = expand_key(p, key);
    Ok(DemoReport {
        params: nparams,
        table_assignments: assignments,
        table_distinct: table.len(),
        guesses: 1 << w,
        survivors,
        true_key_cell: get_bits(&rks[lr.round_key], j * w, w),
        ciphertext_cell: j,
    })
}

/// Clone of `p` whose key schedule is replaced by independent round keys:
/// its key is the byte concatenation of all round keys (byte codec). Lets a
/// caller evaluate the round function under arbitrary round keys.
/// Fails if the total round-key width is not a whole number of bytes.
pub fn with_independent_round_keys(p: &Primitive) -> Result<Primitive, TechniqueError> {
    let nrk = p.key_schedule.num_round_keys();
    let rkb = p.key_schedule.round_key_bits();
    if !(nrk * rkb).is_multiple_of(8) {
        return Err(TechniqueError::Inapplicable(
            "independent key not byte-sized".into(),
        ));
    }
    let mut free = p.clone();
    free.key_bits = nrk * rkb;
    free.key_codec = Codec::BYTES;
    free.key_schedule = KeySchedule::Independent {
        round_keys: nrk,
        round_key_bits: rkb,
    };
    Ok(free)
}

/// Bit position inside round key `rk` that is added to state cell `cell`
/// by the first covering `AddRoundKey` layer.
fn first_key_bit(p: &Primitive, rk: usize, cell: usize, w: usize) -> Result<usize, TechniqueError> {
    for r in &p.rounds {
        for l in &r.layers {
            if let Layer::AddRoundKey {
                round_key,
                bit_offset,
            } = l
            {
                if *round_key == rk && cell * w >= *bit_offset {
                    return Ok(cell * w - bit_offset);
                }
            }
        }
    }
    Err(TechniqueError::Inapplicable(
        "no AddRoundKey for cell".into(),
    ))
}

// ---------------------------------------------------------------------------
// Integral (Lambda-set) property propagation and Square key recovery
// ---------------------------------------------------------------------------

/// Word-level integral property of a cell over a Lambda-set.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Integral {
    /// Constant over the set.
    Const,
    /// Takes every value equally often.
    All,
    /// XOR-sum over the set is zero.
    Balanced,
    /// Nothing known.
    Unknown,
}

/// Propagate the Lambda-set property (one active cell taking all values)
/// through the first `rounds` rounds of `p` and return the property of each
/// cell. Rules: an S-box layer keeps `Const` and `All` (bijective S-box)
/// and loses `Balanced`; a linear layer gives `All` to an output with
/// exactly one non-constant contribution that is `All` through an
/// invertible block, `Balanced` if every non-constant contribution is
/// `All` or `Balanced` (the XOR-sum is linear), and `Unknown` otherwise.
/// Key and constant additions do not change the property.
pub fn integral_propagate(
    p: &Primitive,
    rounds: usize,
    active_cell: usize,
) -> Result<Vec<Integral>, TechniqueError> {
    let w = cell_width(p)?;
    let ncell = p.block_bits / w;
    if rounds > p.num_rounds() || active_cell >= ncell {
        return Err(TechniqueError::Inapplicable(
            "rounds or cell out of range".into(),
        ));
    }
    let mut st: Vec<Integral> = (0..ncell)
        .map(|c| {
            if c == active_cell {
                Integral::All
            } else {
                Integral::Const
            }
        })
        .collect();
    for r in &p.rounds[..rounds] {
        for l in &r.layers {
            match l {
                Layer::SboxParallel { sbox, .. } => {
                    let bij = p.sboxes[sbox.0].is_bijective();
                    for s in st.iter_mut() {
                        *s = match *s {
                            Integral::Const => Integral::Const,
                            Integral::All if bij => Integral::All,
                            _ => Integral::Unknown,
                        };
                    }
                }
                Layer::Permute { .. } | Layer::LinearGf2 { .. } => {
                    let m = layer_matrix(l).expect("linear");
                    st = (0..ncell)
                        .map(|o| {
                            let contrib: Vec<(usize, Integral)> = (0..ncell)
                                .filter(|&c| block_nonzero(&m, w, o, c))
                                .map(|c| (c, st[c]))
                                .collect();
                            let nonconst: Vec<&(usize, Integral)> = contrib
                                .iter()
                                .filter(|(_, s)| *s != Integral::Const)
                                .collect();
                            if nonconst.is_empty() {
                                Integral::Const
                            } else if nonconst.len() == 1
                                && nonconst[0].1 == Integral::All
                                && sub_rank(&m, w, &[o], &[nonconst[0].0]) == w
                            {
                                Integral::All
                            } else if nonconst
                                .iter()
                                .all(|(_, s)| matches!(s, Integral::All | Integral::Balanced))
                            {
                                Integral::Balanced
                            } else {
                                Integral::Unknown
                            }
                        })
                        .collect();
                }
                Layer::AddRoundKey { .. } | Layer::AddConst { .. } => {}
                Layer::Arx { .. } => {
                    return Err(TechniqueError::Inapplicable("ARX layer".into()));
                }
            }
        }
    }
    Ok(st)
}

/// Result of a Lambda-set last-round key recovery.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LastRoundKeyReport {
    /// Lambda-sets consumed.
    pub sets_used: usize,
    /// Rough work estimate in S-box lookups (accounting as in the AES
    /// module this generalises).
    pub sbox_lookups: usize,
    /// Recovered last-round-key cells, indexed by ciphertext cell.
    pub last_round_key_cells: Vec<u32>,
}

struct SquarePlan {
    w: usize,
    ncell: usize,
    inv_sbox: Vec<u32>,
}

/// Check the structure and the integral property needed by the Square key
/// recovery: every ciphertext cell's pre-round cell must be `All` or
/// `Balanced` after `rounds - 1` rounds.
fn square_plan(p: &Primitive, active_cell: usize) -> Result<SquarePlan, String> {
    let lr = parse_last_round(p).map_err(|e| e.to_string())?;
    let st = integral_propagate(p, p.num_rounds() - 1, active_cell).map_err(|e| e.to_string())?;
    for (j, &i) in lr.src.iter().enumerate() {
        if !matches!(st[i], Integral::All | Integral::Balanced) {
            return Err(format!(
                "technique inapplicable: ciphertext cell {j} has no balanced pre-image cell"
            ));
        }
    }
    Ok(SquarePlan {
        w: lr.w,
        ncell: lr.src.len(),
        inv_sbox: lr.inv_sbox,
    })
}

/// Key-recovery from captured Lambda-sets, no oracle. Each entry of `sets`
/// holds the `2^w` ciphertexts of one Lambda-set in plaintext order. For
/// each ciphertext cell the candidates `k` with
/// `XOR_x S^-1(c_x ^ k) = 0` are intersected over the sets. Generalises the
/// Square attack of Daemen-Knudsen-Rijmen (FSE 1997) to any primitive whose
/// last round is `[SboxParallel, Permute?, AddRoundKey]` and whose
/// Lambda-set property reaches every cell one round earlier (checked with
/// [`integral_propagate`] for active cell 0).
pub fn balanced_key_recovery_from_sets(
    p: &Primitive,
    sets: &[Vec<Vec<u8>>],
) -> Result<LastRoundKeyReport, String> {
    let plan = square_plan(p, 0)?;
    let n = 1usize << plan.w;
    if !(1..=6).contains(&sets.len()) || sets.iter().any(|s| s.len() != n) {
        return Err("Square recovery requires 1..=6 complete 256-ciphertext lambda sets".into());
    }
    let mut cands: Vec<Vec<u32>> = vec![(0..n as u32).collect(); plan.ncell];
    let mut lookups = 0usize;
    let encoded: Vec<Vec<Vec<u64>>> = sets
        .iter()
        .map(|s| s.iter().map(|c| p.block_codec.encode(c)).collect())
        .collect();
    for set in &encoded {
        for flat in 0..plan.ncell {
            if cands[flat].len() == 1 {
                continue;
            }
            let before = cands[flat].len();
            let cvals: Vec<u64> = set
                .iter()
                .map(|c| get_bits(c, flat * plan.w, plan.w))
                .collect();
            cands[flat].retain(|&k| {
                cvals
                    .iter()
                    .fold(0u32, |s, &c| s ^ plan.inv_sbox[(c as u32 ^ k) as usize])
                    == 0
            });
            lookups += before * set.len();
            if cands[flat].is_empty() {
                return Err(format!(
                    "Square corpus has no last-round key candidate at byte {flat}"
                ));
            }
        }
    }
    if cands.iter().any(|v| v.len() != 1) {
        return Err("Square corpus leaves ambiguous last-round key bytes; supply another complete lambda set".into());
    }
    Ok(LastRoundKeyReport {
        sets_used: sets.len(),
        sbox_lookups: lookups,
        last_round_key_cells: cands.iter().map(|v| v[0]).collect(),
    })
}

/// Chosen-plaintext Square key recovery through an encryption oracle:
/// builds Lambda-sets on cell 0 over pseudo-random bases (a 64-bit LCG
/// seeded by `seed`, one byte per base byte), narrows the per-cell
/// candidates after each set, and stops when every cell has one candidate.
/// Fails after 6 sets. The base generator and accounting match the AES
/// routine this generalises.
pub fn square_last_round_key_recovery<F>(
    p: &Primitive,
    mut oracle: F,
    seed: u64,
) -> Result<LastRoundKeyReport, String>
where
    F: FnMut(&[u8]) -> Vec<u8>,
{
    let plan = square_plan(p, 0)?;
    let n = 1usize << plan.w;
    let mut cands: Vec<Vec<u32>> = vec![(0..n as u32).collect(); plan.ncell];
    let mut used = 0usize;
    let mut lookups = 0usize;
    let mut rng = seed;
    loop {
        let mut base = vec![0u8; p.block_bytes()];
        for b in base.iter_mut() {
            rng = rng
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            *b = (rng >> 33) as u8;
        }
        let pts = delta_set(p, &base, 0, plan.w);
        let cts: Vec<Vec<u64>> = pts
            .iter()
            .map(|pt| p.block_codec.encode(&oracle(pt)))
            .collect();
        used += 1;
        for flat in 0..plan.ncell {
            if cands[flat].len() == 1 {
                continue;
            }
            let cvals: Vec<u64> = cts
                .iter()
                .map(|c| get_bits(c, flat * plan.w, plan.w))
                .collect();
            cands[flat].retain(|&k| {
                cvals
                    .iter()
                    .fold(0u32, |s, &c| s ^ plan.inv_sbox[(c as u32 ^ k) as usize])
                    == 0
            });
            lookups += n * cands[flat].len().max(1);
        }
        if cands.iter().all(|c| c.len() == 1) {
            break;
        }
        if used >= 6 {
            return Err(format!(
                "Square attack failed to converge after {used} Λ-sets — \
                 this should not happen for correctly-implemented 4-round AES"
            ));
        }
    }
    Ok(LastRoundKeyReport {
        sets_used: used,
        sbox_lookups: lookups,
        last_round_key_cells: cands.iter().map(|v| v[0]).collect(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::aes::reduced::ReducedAes128;
    use crate::cryptanalysis::sym_ir::primitives::aes128;

    const KEY: [u8; 16] = [
        0x0f, 0x15, 0x71, 0xc9, 0x47, 0xd9, 0xe8, 0x59, 0x0c, 0xb7, 0xad, 0xd6, 0xaf, 0x7f, 0x67,
        0x98,
    ];

    /// Positive control: the four-round window of AES depends on 25 byte
    /// parameters for the ordered sequence (Demirci-Selcuk, FSE 2008) and
    /// on 24 for the multiset (Dunkelman-Keller-Shamir, ASIACRYPT 2010).
    /// Both counts come out of the same dependency analysis; the ordered
    /// count matches Demirci-Selcuk and the multiset count matches DKS.
    #[test]
    fn aes_parameter_counts() {
        assert_eq!(DEMIRCI_SELCUK_PARAMS, 25);
        let p7 = aes128::reduced(7, false);
        let spec = DeltaSetSpec {
            first_round: 1,
            inner_rounds: 4,
            active_cell: 0,
            target_cell: 0,
            include_final_offset: false,
        };
        let r = delta_set_dependencies(&p7, &spec).unwrap();
        assert_eq!(r.ordered_count, 25);
        assert_eq!(r.multiset_count, 24);
        assert_eq!(r.ordered_count, DEMIRCI_SELCUK_PARAMS);
        assert_eq!(r.multiset_count, DUNKELMAN_KELLER_SHAMIR_PARAMS);
        // the same window taken from round 1 with the initial AddRoundKey
        let p4 = aes128::reduced(4, true);
        let r4 = delta_set_dependencies(
            &p4,
            &DeltaSetSpec {
                first_round: 0,
                ..spec
            },
        )
        .unwrap();
        assert_eq!((r4.ordered_count, r4.multiset_count), (25, 24));
        // counting the final offset adds one parameter
        let r5 = delta_set_dependencies(
            &p7,
            &DeltaSetSpec {
                include_final_offset: true,
                ..spec
            },
        )
        .unwrap();
        assert_eq!(r5.ordered_count, 26);
        // fewer rounds, fewer parameters
        let r3 = delta_set_dependencies(
            &p7,
            &DeltaSetSpec {
                inner_rounds: 3,
                ..spec
            },
        )
        .unwrap();
        assert!(r3.ordered_count < 25);
    }

    #[test]
    fn aes_seven_round_cost_table() {
        let t = delta_set_cost_table(&aes128::reduced(7, false), 1, 4, 0, 0).unwrap();
        assert_eq!((t.params_ordered, t.params_multiset), (25, 24));
        assert_eq!((t.front_rounds, t.inner_rounds, t.back_rounds), (1, 4, 2));
        assert_eq!(t.data_cells, 4);
        assert_eq!(t.data_log2, 32.0);
        assert_eq!(t.table_ordered_log2, 200.0);
        assert_eq!(t.table_multiset_log2, 192.0);
        assert_eq!(
            (t.front_key_cells, t.back_key_cells, t.ciphertext_cells),
            (4, 8, 4)
        );
        println!("{t:#?}");
    }

    /// Runnable instance on small-scale AES: the offline table over the
    /// parameter space and an online last-round-key guess; the true guess
    /// survives and nearly nothing else.
    #[test]
    fn small_scale_demo_runs() {
        let p = aes128::small_scale(3);
        for key in [[0x3cu8, 0xa7], [0x91, 0x0e], [0x00, 0x00]] {
            let r = delta_set_mitm_demo(&p, &key, 2, 0, 0).unwrap();
            println!("{r:?}");
            assert!(r.survivors.contains(&r.true_key_cell));
            assert!(r.params >= 2 && r.params <= 4);
            assert!(r.survivors.len() <= 3);
            assert_eq!(r.table_assignments, 1 << (4 * r.params));
        }
    }

    #[test]
    fn integral_properties_of_aes() {
        let p = aes128::reduced(4, false);
        assert!(integral_propagate(&p, 2, 0)
            .unwrap()
            .iter()
            .all(|s| *s == Integral::All));
        assert!(integral_propagate(&p, 3, 0)
            .unwrap()
            .iter()
            .all(|s| *s == Integral::Balanced));
    }

    /// Positive control: the generic Lambda-set path recovers the same
    /// last-round key as the existing `aes::square` test key, from an
    /// oracle and from captured sets.
    #[test]
    fn generic_square_recovers_last_round_key() {
        let p = aes128::reduced(4, false);
        let reference = ReducedAes128::new(&KEY, 4, false).round_key(4);
        let rep = square_last_round_key_recovery(
            &p,
            |b| crate::cryptanalysis::sym_ir::eval(&p, &KEY, b),
            0xa5a5_a5a5_a5a5_a5a5,
        )
        .unwrap();
        assert!(rep.sets_used <= 2);
        for c in 0..4 {
            for r in 0..4 {
                assert_eq!(rep.last_round_key_cells[4 * c + r] as u8, reference[c][r]);
            }
        }
        let base = [7u8; 16];
        let set: Vec<Vec<u8>> = delta_set(&p, &base, 0, 8)
            .iter()
            .map(|b| crate::cryptanalysis::sym_ir::eval(&p, &KEY, b))
            .collect();
        let base2 = [0x5au8; 16];
        let set2: Vec<Vec<u8>> = delta_set(&p, &base2, 0, 8)
            .iter()
            .map(|b| crate::cryptanalysis::sym_ir::eval(&p, &KEY, b))
            .collect();
        let rep2 = balanced_key_recovery_from_sets(&p, &[set, set2]).unwrap();
        assert_eq!(rep2.last_round_key_cells, rep.last_round_key_cells);
        // the final-MixColumns variant has no balanced pre-image
        assert!(
            square_last_round_key_recovery(&aes128::reduced(4, true), |b| b.to_vec(), 1).is_err()
        );
    }
}
