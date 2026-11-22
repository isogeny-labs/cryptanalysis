//! # `s3chain-mp`: message passing on the S3 chain of `S_{m+1}`.
//!
//! The summation polynomial `S_{m+1}(x_1..x_m, x_R)` factors as a chain of
//! `S_3` factors joined by intermediate abscissae `u_1..u_{m-2}`:
//! `S_3(x_1,x_2,u_1)`, `S_3(u_{k-1},x_{k+1},u_k)`, `S_3(u_{m-2},x_m,x_R)`.
//! With every `x_i` an abscissa of the factor base, every `u_k` is the
//! abscissa of a signed `(k+1)`-sum of base points, so the *forward
//! message* on bond `u_k` is exactly the support
//! `mu_k = { x(±P_1 ± … ± P_{k+1}) }` and the *backward message* from the
//! target over the remaining leaves is `nu_k = { x(R ∓ …) }`.  A relation
//! for `R` exists iff `mu_k` and `nu_k` meet.
//!
//! This oracle fixes the bond `f - 1` (`forward = f` summands) at which the
//! two messages meet:
//!
//! - **prepare**: the forward message is built by depth-first search over
//!   non-decreasing `f`-tuples of base points (one counted addition per
//!   node of depth >= 2), keyed by the abscissa of the partial sum.  The
//!   *bond truncation* keeps, at the bond of `filter_depth` summands, only
//!   states whose abscissa hash lies in a `2^-d` subset and prunes the
//!   whole subtree below a rejected state;
//! - **decompose**: the backward message is the depth-first search over
//!   `(m-f)`-tuples `R - Σ P_i`, probed against the table.
//!
//! `forward = 2` and `filter_depth = 2` is `rep-join` (and, with `d = 0`,
//! plain MITM at `m`).  Other values differ from `rep-join` in two ways:
//! the meet bond moves, and truncation at a bond *before* the meet also
//! removes the forward additions below it (rep-join's filter only saves
//! lookups).  Every returned decomposition sums to the target.

use std::time::Instant;

use super::stages::{DecompositionOracle, InstanceCtx, Params};
use crate::cryptanalysis::ic_boundary::{
    fast_map, CountedGroup, FactorBase, FastMap, GroupOps, OracleCounters,
};

/// The largest `m` the oracle accepts.
pub const MAX_SUMMANDS: u32 = 9;
/// Largest number of forward search nodes `prepare` will visit.
const MAX_FORWARD_NODES: f64 = 6.0e7;

fn mix(mut z: u64) -> u64 {
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}

/// `C(n + k - 1, k)`: non-decreasing `k`-tuples over `n` symbols.
fn multisets(n: f64, k: u32) -> f64 {
    (0..k).fold(1.0, |acc, i| acc * (n + i as f64) / (i as f64 + 1.0))
}

pub struct S3ChainMpOracle {
    m: u32,
    forward: u32,
    filter_bits: u32,
    filter_depth: u32,
    filter_seed: u64,
    table: Option<FastMap<Box<[u32]>>>,
    /// Forward states reached per depth (index = summands), before the filter.
    reached: Vec<u64>,
    /// Forward states kept per depth, after the filter.
    kept: Vec<u64>,
    leaves: u64,
    filtered_out: u64,
    native_setup_ns: u64,
}

impl S3ChainMpOracle {
    pub fn new(m: u32) -> Self {
        Self {
            m,
            forward: m.saturating_sub(1),
            filter_bits: 0,
            filter_depth: 2,
            filter_seed: 1,
            table: None,
            reached: Vec::new(),
            kept: Vec::new(),
            leaves: 0,
            filtered_out: 0,
            native_setup_ns: 0,
        }
    }

    fn in_filter(&self, abscissa_key: u64) -> bool {
        self.filter_bits == 0
            || mix(abscissa_key ^ self.filter_seed) >> (64 - self.filter_bits) == 0
    }

    #[allow(clippy::too_many_arguments)]
    fn forward_dfs<G: CountedGroup>(
        &mut self,
        g: &G,
        fb: &FactorBase<G::Elt>,
        ops: &mut GroupOps,
        map: &mut FastMap<Box<[u32]>>,
        sum: G::Elt,
        start: usize,
        depth: u32,
        chosen: &mut Vec<u32>,
    ) {
        // `sum` is the partial sum of `depth` points (depth >= 1).
        self.reached[depth as usize] += 1;
        if depth >= 2 && g.is_identity(&sum) {
            return;
        }
        if depth >= 2 && depth == self.filter_depth && !self.in_filter(g.key(&sum) >> 1) {
            return;
        }
        self.kept[depth as usize] += 1;
        if depth == self.forward {
            map.entry(g.key(&sum) >> 1)
                .or_insert_with(|| chosen.clone().into_boxed_slice());
            return;
        }
        for i in start..fb.points.len() {
            let next = g.add(ops, sum, fb.points[i]);
            chosen.push(i as u32);
            self.forward_dfs(g, fb, ops, map, next, i, depth + 1, chosen);
            chosen.pop();
        }
    }

    #[allow(clippy::too_many_arguments)]
    fn backward_dfs<G: CountedGroup>(
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
            let key = g.key(&rest) >> 1;
            if self.filter_depth == self.forward && !self.in_filter(key) {
                self.filtered_out += 1;
                return None;
            }
            counters.lookups += 1;
            let stored = self.table.as_ref()?.get(&key)?.clone();
            // Rebuild the stored sum (forward - 1 counted additions) and
            // resolve the sign of the abscissa match.
            let mut s = fb.points[stored[0] as usize];
            for &i in &stored[1..] {
                s = g.add(ops, s, fb.points[i as usize]);
            }
            let mut out = chosen.clone();
            if s == rest {
                out.extend(stored.iter().map(|&i| i as usize));
            } else if s == g.neg(rest) {
                out.extend(stored.iter().map(|&i| fb.neg_index[i as usize]));
            } else {
                return None;
            }
            return Some(out);
        }
        for i in start..fb.points.len() {
            let next = g.add(ops, rest, g.neg(fb.points[i]));
            chosen.push(i);
            let found = self.backward_dfs(g, fb, ops, counters, next, i, depth - 1, chosen);
            chosen.pop();
            if found.is_some() {
                return found;
            }
        }
        None
    }
}

impl<G: CountedGroup> DecompositionOracle<G> for S3ChainMpOracle {
    fn name(&self) -> &str {
        "s3chain-mp"
    }

    fn summands(&self) -> u32 {
        self.m
    }

    fn describe(&self, _params: &Params) -> String {
        format!(
            "S3-chain message passing: forward support over {} summands (bond u_{}), backward {}-tuples from the target, bond truncated to abscissa density 2^-{} at {} summands",
            self.forward,
            self.forward.saturating_sub(1),
            self.m.saturating_sub(self.forward),
            self.filter_bits,
            self.filter_depth
        )
    }

    fn parameters(&self) -> &[(&str, &str)] {
        &[
            ("m", "summands, 3..=9"),
            (
                "forward",
                "summands in the forward message (the meet bond is u_{forward-1}); 2..=m-1, default m-1; 2 = rep-join",
            ),
            (
                "filter_bits",
                "d in 0..=32: truncate the bond at filter_depth summands to a 2^-d hashed subset; 0 = exact",
            ),
            (
                "filter_depth",
                "summands of the truncated bond, 2..=forward, default 2; forward = rep-join's filter",
            ),
            ("filter_seed", "seed of the truncation hash, default 1"),
        ]
    }

    fn prepare(
        &mut self,
        ctx: &InstanceCtx<G>,
        fb: &FactorBase<G::Elt>,
        params: &Params,
        ops: &mut GroupOps,
    ) -> Result<(), String> {
        if !(3..=MAX_SUMMANDS).contains(&self.m) {
            return Err(format!(
                "s3chain-mp takes m = 3..={MAX_SUMMANDS}, got {}",
                self.m
            ));
        }
        let f = params.u64_or("forward", (self.m - 1) as u64)? as u32;
        if !(2..self.m).contains(&f) {
            return Err(format!("forward must be 2..={}, got {f}", self.m - 1));
        }
        self.forward = f;
        let d = params.u64_or("filter_bits", 0)?;
        if d > 32 {
            return Err("filter_bits must be 0..=32".into());
        }
        self.filter_bits = d as u32;
        let t = params.u64_or("filter_depth", 2)? as u32;
        if !(2..=f).contains(&t) {
            return Err(format!("filter_depth must be 2..={f}, got {t}"));
        }
        self.filter_depth = t;
        self.filter_seed = params.u64_or("filter_seed", 1)?;
        let n = fb.points.len();
        let nodes: f64 = (2..=f).map(|k| multisets(n as f64, k)).sum();
        if nodes > MAX_FORWARD_NODES {
            return Err(format!(
                "resource limit: forward search would visit about {nodes:.2e} nodes (cap {MAX_FORWARD_NODES:.1e})"
            ));
        }
        let started = Instant::now();
        self.reached = vec![0; f as usize + 1];
        self.kept = vec![0; f as usize + 1];
        let mut map: FastMap<Box<[u32]>> = fast_map(1024);
        let mut chosen = Vec::with_capacity(f as usize);
        let g = ctx.group;
        for i in 0..n {
            chosen.push(i as u32);
            self.forward_dfs(g, fb, ops, &mut map, fb.points[i], i, 1, &mut chosen);
            chosen.pop();
        }
        self.table = Some(map);
        self.native_setup_ns = started.elapsed().as_nanos() as u64;
        Ok(())
    }

    fn setup_native(&self) -> std::collections::BTreeMap<String, u64> {
        let mut out = std::collections::BTreeMap::from([(
            "s3chain_setup_ns".to_string(),
            self.native_setup_ns,
        )]);
        for k in 2..=self.forward as usize {
            out.insert(format!("s3chain_reached_{k}"), self.reached[k]);
            out.insert(format!("s3chain_kept_{k}"), self.kept[k]);
        }
        out.insert(
            "s3chain_table_states".into(),
            self.table.as_ref().map_or(0, |t| t.len() as u64),
        );
        out
    }

    fn relation_counters(&self) -> std::collections::BTreeMap<String, u64> {
        std::collections::BTreeMap::from([
            ("s3chain_leaves".into(), self.leaves),
            ("s3chain_filtered_out".into(), self.filtered_out),
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
        self.backward_dfs(
            ctx.group,
            fb,
            ops,
            counters,
            point,
            0,
            self.m - self.forward,
            &mut chosen,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::ic_boundary::{
        prime_factor_base, roster_prime_instance, CountedGroup, OracleCounters,
    };

    /// Every decomposition returned, for several `(m, forward, d, t)`,
    /// sums to its target, and the unfiltered chain finds some.
    #[test]
    fn every_decomposition_sums_to_the_target() {
        let inst = roster_prime_instance(14).unwrap();
        let g0 = inst.generator_point();
        let fb = prime_factor_base(&inst, 14);
        let mut total_found = 0;
        for &(m, f, d, t) in &[
            (3u32, 2u32, 0u64, 2u64),
            (3, 2, 2, 2),
            (4, 3, 0, 2),
            (4, 3, 1, 2),
            (4, 3, 2, 3),
            (4, 2, 0, 2),
            (5, 3, 0, 2),
        ] {
            let ctx = InstanceCtx {
                group: &inst.curve,
                generator: g0,
                target: g0,
                r: inst.r,
                cofactor: inst.cofactor,
                group_order: inst.group_order,
                name: inst.name.clone(),
                field_degree: None,
            };
            let mut params = Params::default();
            params.set("forward", f.to_string());
            params.set("filter_bits", d.to_string());
            params.set("filter_depth", t.to_string());
            let mut oracle = S3ChainMpOracle::new(m);
            let mut ops = GroupOps::default();
            DecompositionOracle::prepare(&mut oracle, &ctx, &fb, &params, &mut ops).unwrap();
            let mut counters = OracleCounters::default();
            for k in 1..400u64 {
                let mut o = GroupOps::default();
                let target = CountedGroup::mul(&inst.curve, &mut o, g0, (k * 7919) % inst.r);
                if let Some(idx) = DecompositionOracle::decompose(
                    &mut oracle,
                    &ctx,
                    &fb,
                    &mut o,
                    &mut counters,
                    target,
                ) {
                    assert_eq!(idx.len() as u32, m, "m={m} f={f} d={d} t={t}");
                    let mut s = fb.points[idx[0]];
                    for &i in &idx[1..] {
                        s = inst.curve.add(&mut o, s, fb.points[i]);
                    }
                    assert!(s == target, "decomposition does not sum to target (m={m} f={f} d={d} t={t})");
                    total_found += 1;
                }
            }
        }
        assert!(total_found > 0, "no decomposition found at all");
    }
}
