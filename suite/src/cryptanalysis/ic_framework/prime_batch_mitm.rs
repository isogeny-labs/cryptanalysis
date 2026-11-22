//! Prime-field MITM with batched preparation and batched three-summand
//! probes, charged natively.
//!
//! The same oracle as `mitm` on a prime-field curve — the same pair
//! table, entry for entry and witness for witness, probed the same way —
//! prepared and probed in batches (`ic_boundary::prime_batch`):
//!
//! * the table from one inversion per abscissa pair (`x(P ± Q)` share a
//!   denominator) and Montgomery's simultaneous inversion over a chunk,
//!   instead of one affine addition per entry;
//! * at `m = 3`, every `R ± P_i` of a chunk of abscissae from one
//!   batched inversion, in the scalar loop's index order, instead of one
//!   affine addition per signed base point.
//!
//! **Pricing.**  With `native_setup_pricing=1` (the default) the whole
//! preparation is charged as measured nanoseconds (`mitm_native_setup_ns`,
//! converted at this host's nanoseconds per addition), as the binary
//! `mitm-batched` oracle charges its own, and the additions a scalar
//! build would have counted are reported beside it
//! (`mitm_setup_observed_adds`).  With `native_probe_pricing=1` (the
//! default) the arithmetic of the three-summand candidates is charged
//! as measured nanoseconds (`mitm_native_probe_ns`); the table lookups
//! stay in `lookups`, priced per lookup as for every table oracle, and
//! the addition that verifies a hit stays a counted addition.  Setting
//! either to `0` charges exactly what the scalar oracle counts — one
//! addition per table entry, one per candidate point — so that arm
//! differs from `mitm` in wall time alone and is the control for the
//! pricing.

use std::collections::BTreeMap;
use std::time::Instant;

use super::stages::{DecompositionOracle, InstanceCtx, Params};
use crate::cryptanalysis::ic_boundary::prime_batch::{
    prime_probe_candidates, MontBase, PrimeBatchScratch,
};
use crate::cryptanalysis::ic_boundary::{
    FactorBase, GroupOps, OracleCounters, PairTable, PrimeCurve, PrimePoint,
};

pub struct PrimeBatchMitmOracle {
    m: u32,
    table: Option<PairTable>,
    base: Option<MontBase>,
    /// Point-index groups per abscissa, in abscissa order.
    groups: Vec<Vec<usize>>,
    scratch: PrimeBatchScratch,
    candidates: Vec<(usize, Option<PrimePoint>)>,
    native_setup: bool,
    native_probe: bool,
    probe_chunk: usize,
    setup_ns: u64,
    probe_ns: u64,
    probe_batches: u64,
    probe_points: u64,
    probe_lookups: u64,
}

impl PrimeBatchMitmOracle {
    pub fn new(m: u32) -> Self {
        Self {
            m,
            table: None,
            base: None,
            groups: Vec::new(),
            scratch: PrimeBatchScratch::default(),
            candidates: Vec::new(),
            native_setup: true,
            native_probe: true,
            probe_chunk: 16,
            setup_ns: 0,
            probe_ns: 0,
            probe_batches: 0,
            probe_points: 0,
            probe_lookups: 0,
        }
    }
}

fn flag01(params: &Params, key: &str, default: u64) -> Result<bool, String> {
    match params.u64_or(key, default)? {
        0 => Ok(false),
        1 => Ok(true),
        _ => Err(format!("{key} must be 0 or 1")),
    }
}

impl DecompositionOracle<PrimeCurve> for PrimeBatchMitmOracle {
    fn name(&self) -> &str {
        "mitm-prime-batched"
    }

    fn summands(&self) -> u32 {
        self.m
    }

    fn describe(&self, params: &Params) -> String {
        format!(
            "the mitm pair table of a prime-field base prepared in batches (one inversion per \
             abscissa pair, Montgomery batch inversion), {}; m = 3 probes {} per chunk of {} \
             abscissae{}",
            if params.u64_or("negation_folded", 1).unwrap_or(1) == 1 {
                "negation folded"
            } else {
                "charged as the full table"
            },
            if params.u64_or("native_probe_pricing", 1).unwrap_or(1) == 1 {
                "batched and charged natively"
            } else {
                "batched and charged as counted additions"
            },
            params.get("probe_chunk").unwrap_or("16"),
            if params.u64_or("native_setup_pricing", 1).unwrap_or(1) == 1 {
                "; preparation charged natively"
            } else {
                "; preparation charged as counted additions"
            },
        )
    }

    fn parameters(&self) -> &[(&str, &str)] {
        &[
            ("m", "summands, 2 or 3"),
            (
                "negation_folded",
                "1 (default) to charge the folded build's additions; 0 the full build's. The \
                 table is the same either way",
            ),
            (
                "native_setup_pricing",
                "1 (default) to charge the preparation as measured nanoseconds; 0 to charge the \
                 scalar build's additions",
            ),
            (
                "native_probe_pricing",
                "1 (default) to charge m = 3 candidate arithmetic as measured nanoseconds; 0 to \
                 charge one addition per candidate point",
            ),
            (
                "chunk",
                "pairs per batched inversion while preparing, 1..=1048576, default 1024",
            ),
            (
                "probe_chunk",
                "abscissae per batched inversion while probing at m = 3, 1..=4096, default 16: \
                 the early-exit granularity",
            ),
        ]
    }

    fn prepare(
        &mut self,
        ctx: &InstanceCtx<PrimeCurve>,
        fb: &FactorBase<PrimePoint>,
        params: &Params,
        ops: &mut GroupOps,
    ) -> Result<(), String> {
        if !matches!(self.m, 2 | 3) {
            return Err("mitm-prime-batched supports m = 2 or 3".into());
        }
        let folded = flag01(params, "negation_folded", 1)?;
        self.native_setup = flag01(params, "native_setup_pricing", 1)?;
        self.native_probe = flag01(params, "native_probe_pricing", 1)?;
        let chunk = params.u64_or("chunk", 1024)? as usize;
        let probe_chunk = params.u64_or("probe_chunk", 16)? as usize;
        if !(1..=4096).contains(&probe_chunk) {
            return Err("probe_chunk must be in 1..=4096".into());
        }
        self.probe_chunk = probe_chunk;
        let started = Instant::now();
        let table = PairTable::build_prime_batched(ctx.group, fb, folded, chunk)?;
        let base = MontBase::new(ctx.group, &fb.points)
            .ok_or("mitm-prime-batched needs an odd word prime below 2^63")?;
        self.groups = fb
            .abscissa_list
            .iter()
            .map(|x| fb.x_index.get(x).cloned().unwrap_or_default())
            .collect();
        self.setup_ns = started.elapsed().as_nanos() as u64;
        if !self.native_setup {
            // The counted convention: one addition per entry the scalar
            // build would have evaluated.
            ops.adds += table.build_ops.adds;
        }
        self.table = Some(table);
        self.base = Some(base);
        Ok(())
    }

    fn setup_native(&self) -> BTreeMap<String, u64> {
        let table = self.table.as_ref();
        let mut map = BTreeMap::from([
            (
                "mitm_setup_observed_adds".into(),
                table.map_or(0, |t| t.build_ops.adds),
            ),
            (
                "mitm_table_entries".into(),
                table.map_or(0, |t| t.entries),
            ),
            (
                "mitm_compact_map32_backend".into(),
                u64::from(table.is_some_and(PairTable::uses_compact_storage)),
            ),
            ("mitm_setup_wall_ns".into(), self.setup_ns),
        ]);
        if self.native_setup {
            map.insert("mitm_native_setup_ns".into(), self.setup_ns);
        }
        map
    }

    fn relation_counters(&self) -> BTreeMap<String, u64> {
        let mut map = BTreeMap::from([
            ("mitm_probe_batches".into(), self.probe_batches),
            ("mitm_probe_points".into(), self.probe_points),
            ("mitm_probe_wall_ns".into(), self.probe_ns),
        ]);
        if self.native_probe {
            map.insert("mitm_native_probe_ns".into(), self.probe_ns);
        }
        map
    }

    fn decompose(
        &mut self,
        ctx: &InstanceCtx<PrimeCurve>,
        fb: &FactorBase<PrimePoint>,
        ops: &mut GroupOps,
        counters: &mut OracleCounters,
        point: PrimePoint,
    ) -> Option<Vec<usize>> {
        let table = self.table.as_ref()?;
        let g = ctx.group;
        if self.m == 2 {
            return table
                .probe(g, fb, ops, &mut counters.lookups, point)
                .map(|(i, j)| vec![i, j]);
        }
        let base = self.base.as_ref()?;
        let groups: Vec<&Vec<usize>> = self.groups.iter().collect();
        for chunk in groups.chunks(self.probe_chunk) {
            let started = Instant::now();
            self.candidates.clear();
            let evaluated = prime_probe_candidates(
                base,
                chunk,
                point,
                &mut self.scratch,
                &mut self.candidates,
            );
            self.probe_ns += started.elapsed().as_nanos() as u64;
            self.probe_batches += 1;
            self.probe_points += evaluated;
            if !self.native_probe {
                ops.adds += evaluated;
            }
            for (i, candidate) in &self.candidates {
                let Some(s) = candidate else { continue };
                self.probe_lookups += 1;
                if let Some((j, k)) = table.probe(g, fb, ops, &mut counters.lookups, *s) {
                    return Some(vec![*i, j, k]);
                }
            }
        }
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::ic_boundary::{
        prime_factor_base, roster_prime_instance, CountedGroup,
    };
    use crate::cryptanalysis::ic_framework::plugins::MitmOracle;
    use rand::rngs::StdRng;
    use rand::{Rng, SeedableRng};

    fn ctx(inst: &crate::cryptanalysis::ic_boundary::PrimeInstance) -> InstanceCtx<'_, PrimeCurve> {
        let g = inst.generator_point();
        InstanceCtx {
            group: &inst.curve,
            generator: g,
            target: g,
            r: inst.r,
            cofactor: inst.cofactor,
            group_order: inst.group_order,
            name: inst.name.clone(),
            field_degree: None,
        }
    }

    /// **Every decomposition the scalar oracle returns, this one returns,
    /// and the same one**, at both summand counts, on random targets and
    /// on planted sums.
    #[test]
    fn agrees_with_the_scalar_mitm_oracle() {
        let inst = roster_prime_instance(18).expect("roster instance");
        let ctx = ctx(&inst);
        let fb = prime_factor_base(&inst, 40);
        let mut rng = StdRng::seed_from_u64(20261121);
        let mut ops = GroupOps::default();
        let mut targets: Vec<PrimePoint> = (0..300)
            .map(|_| inst.curve.mul(&mut ops, ctx.generator, rng.gen_range(1..inst.r)))
            .collect();
        for _ in 0..40 {
            let (i, j, k) = (
                rng.gen_range(0..fb.points.len()),
                rng.gen_range(0..fb.points.len()),
                rng.gen_range(0..fb.points.len()),
            );
            let two = inst.curve.add_scalar(fb.points[i], fb.points[j]);
            targets.push(two);
            targets.push(inst.curve.add_scalar(two, fb.points[k]));
        }
        targets.push(fb.points[0]);
        targets.push(fb.points[1]);
        for m in [2u32, 3] {
            for (chunk, probe_chunk) in [("1", "1"), ("5", "3"), ("1024", "16")] {
                let mut params = Params::default();
                params.set("m", m.to_string());
                params.set("chunk", chunk);
                params.set("probe_chunk", probe_chunk);
                let mut scalar = MitmOracle::new(m);
                let mut batched = PrimeBatchMitmOracle::new(m);
                let mut o = GroupOps::default();
                scalar.prepare(&ctx, &fb, &Params::default(), &mut o).unwrap();
                batched.prepare(&ctx, &fb, &params, &mut o).unwrap();
                let mut hits = 0;
                for &t in &targets {
                    if t.infinity {
                        continue;
                    }
                    let mut c1 = OracleCounters::default();
                    let mut c2 = OracleCounters::default();
                    let a = scalar.decompose(&ctx, &fb, &mut o, &mut c1, t);
                    let b = batched.decompose(&ctx, &fb, &mut o, &mut c2, t);
                    assert_eq!(a, b, "m={m} chunk={chunk} probe_chunk={probe_chunk} target {t:?}");
                    if let Some(w) = &b {
                        hits += 1;
                        let sum = w.iter().fold(PrimePoint::INFINITY, |acc, &i| {
                            inst.curve.add_scalar(acc, fb.points[i])
                        });
                        assert_eq!(sum, t);
                    }
                }
                assert!(hits >= 40, "m={m}: the planted sums must decompose ({hits})");
            }
        }
    }

    /// With native pricing off the oracle charges exactly the scalar
    /// oracle's additions for the table, and for the probes the points
    /// it evaluated (whole chunks, so at least the scalar count).
    #[test]
    fn counted_pricing_matches_the_scalar_oracle() {
        let inst = roster_prime_instance(16).expect("roster instance");
        let ctx = ctx(&inst);
        let fb = prime_factor_base(&inst, 24);
        for (folded, scalar_folded) in [(1u64, true), (0u64, false)] {
            let mut params = Params::default();
            params.set("native_setup_pricing", "0");
            params.set("negation_folded", folded.to_string());
            let mut batched = PrimeBatchMitmOracle::new(2);
            let mut ob = GroupOps::default();
            batched.prepare(&ctx, &fb, &params, &mut ob).unwrap();
            let mut sp = Params::default();
            if scalar_folded {
                sp.set("negation_folded", "1");
            }
            let mut scalar = MitmOracle::new(2);
            let mut os = GroupOps::default();
            scalar.prepare(&ctx, &fb, &sp, &mut os).unwrap();
            assert_eq!(ob.adds, os.adds, "folded={folded}");
            assert!(batched.setup_native().contains_key("mitm_native_setup_ns") == false);
        }
    }
}
