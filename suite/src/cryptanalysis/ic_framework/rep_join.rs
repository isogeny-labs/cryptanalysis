//! # `rep-join`: the representation technique as a generic list join.
//!
//! Delaplace–May (NuTMiC 2019, ePrint 2019/800) and Delaplace–Fouque–
//! Kirchner–May (2020, hal-02427655) solve ECDLP over `F_{p^ℓ}` by a
//! four-list join: write the unknown as a sum, join two pairs of lists
//! and keep only the partial sums whose abscissa lies in a structured
//! subset `H` (there, the subfield `F_p`).  Many *representations* of
//! one solution exist, so discarding all but a `|H|/q` fraction of the
//! partial sums still leaves one.
//!
//! This oracle is that join stripped of its algebra, so the filter's
//! effect on index-calculus relation search can be measured on every
//! regime `ic bench` has.  A target `R` is written as
//!
//! ```text
//! R = P_{i_1} + … + P_{i_{m−2}} + (P_j + P_k),     P ∈ F (signed)
//! ```
//!
//! - **prepare**: the pair sums `P_j + P_k` (`j ≤ k`), keyed by
//!   abscissa, keeping only those whose abscissa passes the filter
//!   `H = { x : hash(x) < 2^{64−d} }` (density `2^{−d}`, `d =
//!   filter_bits`);
//! - **decompose**: enumerate the non-decreasing signed `(m−2)`-tuples
//!   by depth-first search (one counted addition per node), and probe
//!   the table with `R − Σ P_i` only when that point's abscissa passes
//!   the same filter.
//!
//! `filter_bits = 0` is plain meet in the middle at any `m` (the control
//! that isolates the filter).  What the filter cannot do generically is
//! the papers' actual step: enumerate *only* the partial sums inside `H`
//! in time near their number.  Without a summation-polynomial
//! enumeration, the depth-first search still visits every `(m−2)`-tuple,
//! so the filter saves table memory and lookups, never additions.  The
//! preregistered prediction (workspace PR #38, cryptanalysis PR #1877,
//! `[pcc:unverified]`) is therefore: counted cost per relation grows
//! like `m(m−1)·N/(2|F|)²` in `m`, and like `2^d / min(1, C(m,2)·2^{−d})`
//! in the filter.

use std::time::Instant;

use super::stages::{DecompositionOracle, InstanceCtx, Params};
use crate::cryptanalysis::ic_boundary::{
    fast_map, CountedGroup, FactorBase, FastMap, GroupOps, OracleCounters,
};

/// The largest `m` the oracle accepts: the lead-sweep ladder's top.
pub const MAX_SUMMANDS: u32 = 9;

/// SplitMix64 finaliser: the filter's hash on an abscissa key.
fn mix(mut z: u64) -> u64 {
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}

/// Generic filtered `m`-list join.
pub struct RepJoinOracle {
    m: u32,
    filter_bits: u32,
    filter_seed: u64,
    table: Option<FastMap<(u32, u32)>>,
    /// Pair sums built (every `j ≤ k`, identity excluded).
    pairs_built: u64,
    /// Pair sums kept after the filter.
    pairs_kept: u64,
    /// `(m−2)`-tuple sums whose abscissa failed the filter: probes saved.
    filtered_out: u64,
    /// `(m−2)`-tuple sums reached (leaves of the search).
    leaves: u64,
    native_setup_ns: u64,
}

impl RepJoinOracle {
    pub fn new(m: u32) -> Self {
        Self {
            m,
            filter_bits: 0,
            filter_seed: 1,
            table: None,
            pairs_built: 0,
            pairs_kept: 0,
            filtered_out: 0,
            leaves: 0,
            native_setup_ns: 0,
        }
    }

    /// Whether an abscissa key lies in `H`.
    fn in_filter(&self, abscissa_key: u64) -> bool {
        self.filter_bits == 0
            || mix(abscissa_key ^ self.filter_seed) >> (64 - self.filter_bits) == 0
    }

    /// Probe the table for `±target`, resolving the sign with one
    /// counted addition, exactly as `PairTable::probe` does.
    fn probe<G: CountedGroup>(
        &self,
        g: &G,
        fb: &FactorBase<G::Elt>,
        ops: &mut GroupOps,
        lookups: &mut u64,
        target: G::Elt,
    ) -> Option<(usize, usize)> {
        let table = self.table.as_ref()?;
        *lookups += 1;
        let &(i, j) = table.get(&(g.key(&target) >> 1))?;
        let (i, j) = (i as usize, j as usize);
        let s = g.add(ops, fb.points[i], fb.points[j]);
        if s == target {
            Some((i, j))
        } else if s == g.neg(target) {
            Some((fb.neg_index[i], fb.neg_index[j]))
        } else {
            None
        }
    }

    /// Depth-first search over non-decreasing tuples `start ≤ i_1 ≤ …`
    /// of length `depth`, carrying `rest = R − Σ chosen`.
    #[allow(clippy::too_many_arguments)]
    fn search<G: CountedGroup>(
        &mut self,
        g: &G,
        fb: &FactorBase<G::Elt>,
        ops: &mut GroupOps,
        counters: &mut OracleCounters,
        rest: G::Elt,
        start: usize,
        depth: u32,
        chosen: &mut Vec<usize>,
    ) -> Option<Vec<usize>> {
        if depth == 0 {
            self.leaves += 1;
            if g.is_identity(&rest) {
                return None;
            }
            if !self.in_filter(g.key(&rest) >> 1) {
                self.filtered_out += 1;
                return None;
            }
            let (j, k) = self.probe(g, fb, ops, &mut counters.lookups, rest)?;
            let mut out = chosen.clone();
            out.push(j);
            out.push(k);
            return Some(out);
        }
        for i in start..fb.points.len() {
            let next = g.add(ops, rest, g.neg(fb.points[i]));
            chosen.push(i);
            let found = self.search(g, fb, ops, counters, next, i, depth - 1, chosen);
            chosen.pop();
            if found.is_some() {
                return found;
            }
        }
        None
    }
}

impl<G: CountedGroup> DecompositionOracle<G> for RepJoinOracle {
    fn name(&self) -> &str {
        "rep-join"
    }

    fn summands(&self) -> u32 {
        self.m
    }

    fn describe(&self, _params: &Params) -> String {
        format!(
            "generic {}-list join: signed ({})-tuples searched, pair sums filtered to abscissa density 2^-{}",
            self.m,
            self.m.saturating_sub(2),
            self.filter_bits
        )
    }

    fn parameters(&self) -> &[(&str, &str)] {
        &[
            ("m", "summands, 2..=9"),
            (
                "filter_bits",
                "d in 0..=32: keep pair sums whose abscissa hash lies in a 2^-d subset; 0 = plain MITM at m",
            ),
            ("filter_seed", "seed of the filter hash, default 1"),
        ]
    }

    fn prepare(
        &mut self,
        ctx: &InstanceCtx<G>,
        fb: &FactorBase<G::Elt>,
        params: &Params,
        ops: &mut GroupOps,
    ) -> Result<(), String> {
        if !(2..=MAX_SUMMANDS).contains(&self.m) {
            return Err(format!(
                "rep-join takes m = 2..={MAX_SUMMANDS}, got {}",
                self.m
            ));
        }
        let d = params.u64_or("filter_bits", 0)?;
        if d > 32 {
            return Err("filter_bits must be 0..=32".into());
        }
        self.filter_bits = d as u32;
        self.filter_seed = params.u64_or("filter_seed", 1)?;
        let started = Instant::now();
        let g = ctx.group;
        let n = fb.points.len();
        let mut map: FastMap<(u32, u32)> = fast_map(n * (n + 1) / 4 + 1);
        let mut built = 0u64;
        for i in 0..n {
            for j in i..n {
                let s = g.add(ops, fb.points[i], fb.points[j]);
                if g.is_identity(&s) {
                    continue;
                }
                built += 1;
                let key = g.key(&s) >> 1;
                if self.in_filter(key) {
                    map.entry(key).or_insert((i as u32, j as u32));
                }
            }
        }
        self.pairs_built = built;
        self.pairs_kept = map.len() as u64;
        self.table = Some(map);
        self.native_setup_ns = started.elapsed().as_nanos() as u64;
        Ok(())
    }

    fn setup_native(&self) -> std::collections::BTreeMap<String, u64> {
        std::collections::BTreeMap::from([
            ("rep_join_setup_ns".into(), self.native_setup_ns),
            ("rep_join_pairs_built".into(), self.pairs_built),
            ("rep_join_pairs_kept".into(), self.pairs_kept),
        ])
    }

    fn relation_counters(&self) -> std::collections::BTreeMap<String, u64> {
        std::collections::BTreeMap::from([
            ("rep_join_leaves".into(), self.leaves),
            ("rep_join_filtered_out".into(), self.filtered_out),
        ])
    }

    fn decompose(
        &mut self,
        ctx: &InstanceCtx<G>,
        fb: &FactorBase<G::Elt>,
        ops: &mut GroupOps,
        counters: &mut OracleCounters,
        point: G::Elt,
    ) -> Option<Vec<usize>> {
        let mut chosen = Vec::with_capacity(self.m as usize);
        self.search(
            ctx.group,
            fb,
            ops,
            counters,
            point,
            0,
            self.m - 2,
            &mut chosen,
        )
    }
}
