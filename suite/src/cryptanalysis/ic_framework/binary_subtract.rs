//! Production two-point subtraction on the native binary backend.
//!
//! Reuses the factor base's indexes and FastCurve's batch/lazy kernels.
//! Scalar first-witness order is preserved; every computed batch lane is
//! charged even if an earlier lane supplies the witness. No pair table.

use std::collections::BTreeMap;

use super::stages::{DecompositionOracle, InstanceCtx, Params};
use crate::cryptanalysis::ic_boundary::{
    BinaryGroup, CountedGroup, FactorBase, GroupOps, OracleCounters,
};
use crate::cryptanalysis::koblitz_fast::{BatchScratch, FastPoint};

/// A reusable native oracle. Call `prepare` for each factor base/run.
pub struct BinarySubtractOracle {
    minus: Vec<FastPoint>,
    sums: Vec<FastPoint>,
    slopes: Vec<u64>,
    scratch: BatchScratch,
    block: usize,
    lazy: bool,
    prepared: bool,
    blocks: u64,
    lanes: u64,
    x_tests: u64,
    completed: u64,
    point_tests: u64,
}

impl Default for BinarySubtractOracle {
    fn default() -> Self {
        Self::new()
    }
}

impl BinarySubtractOracle {
    pub fn new() -> Self {
        Self {
            minus: Vec::new(),
            sums: Vec::new(),
            slopes: Vec::new(),
            scratch: BatchScratch::default(),
            block: 32,
            lazy: true,
            prepared: false,
            blocks: 0,
            lanes: 0,
            x_tests: 0,
            completed: 0,
            point_tests: 0,
        }
    }
}

impl DecompositionOracle<BinaryGroup<'_>> for BinarySubtractOracle {
    fn name(&self) -> &str {
        "subtract-binary-batch"
    }
    fn summands(&self) -> u32 {
        2
    }
    fn describe(&self, _params: &Params) -> String {
        format!("native binary target subtraction, block={}, lazy={}, full-point witness confirmation; no pair table",self.block,self.lazy)
    }
    fn parameters(&self) -> &[(&str, &str)] {
        &[
            ("m", "exactly 2"),
            (
                "block",
                "1..4096, default 32; all computed lanes are charged",
            ),
            (
                "lazy",
                "0 or 1, default 1; finish ordinates only after an abscissa hit",
            ),
        ]
    }
    fn prepare(
        &mut self,
        ctx: &InstanceCtx<BinaryGroup<'_>>,
        fb: &FactorBase<FastPoint>,
        params: &Params,
        _ops: &mut GroupOps,
    ) -> Result<(), String> {
        // Failed preparation must not leave a previously prepared run usable.
        self.prepared = false;
        for key in params.0.keys() {
            if !matches!(key.as_str(), "m" | "block" | "lazy") {
                return Err(format!("subtract-binary-batch does not accept `{key}`"));
            }
        }
        if params.u64_or("m", 2)? != 2 {
            return Err("subtract-binary-batch requires m=2".into());
        }
        let block = params.u64_or("block", 32)?;
        if !(1..=4096).contains(&block) {
            return Err("subtract-binary-batch block must be in 1..4096".into());
        }
        let lazy = match params.get("lazy").unwrap_or("1") {
            "0" => false,
            "1" => true,
            _ => return Err("subtract-binary-batch lazy must be 0 or 1".into()),
        };
        self.block = block as usize;
        self.lazy = lazy;
        self.minus.clear();
        self.minus
            .extend(fb.points.iter().map(|&p| ctx.group.neg(p)));
        self.sums.clear();
        self.slopes.clear();
        // Capacity, not contents, is reusable across targets. First-use kernel
        // scratch growth still occurs inside the charged decomposition phase.
        self.sums.reserve(self.block.min(fb.points.len()));
        self.slopes.reserve(self.block.min(fb.points.len()));
        self.blocks = 0;
        self.lanes = 0;
        self.x_tests = 0;
        self.completed = 0;
        self.point_tests = 0;
        self.prepared = true;
        Ok(())
    }
    fn setup_native(&self) -> BTreeMap<String, u64> {
        BTreeMap::from([("negative_points_prepared".into(), self.minus.len() as u64)])
    }
    fn setup_work_native(&self) -> BTreeMap<String, u64> {
        BTreeMap::from([
            ("index_point_negations".into(), self.minus.len() as u64),
            ("counted:table_insert_attempts".into(), 1),
        ])
    }
    fn relation_counters(&self) -> BTreeMap<String, u64> {
        BTreeMap::from([
            ("binary_subtract_blocks".into(), self.blocks),
            ("binary_subtract_lanes".into(), self.lanes),
            ("binary_subtract_x_tests".into(), self.x_tests),
            ("binary_subtract_ordinates_completed".into(), self.completed),
            ("binary_subtract_point_tests".into(), self.point_tests),
        ])
    }
    fn decompose(
        &mut self,
        ctx: &InstanceCtx<BinaryGroup<'_>>,
        fb: &FactorBase<FastPoint>,
        ops: &mut GroupOps,
        counters: &mut OracleCounters,
        target: FastPoint,
    ) -> Option<Vec<usize>> {
        assert!(
            self.prepared,
            "subtract-binary-batch requires successful prepare"
        );
        assert_eq!(
            self.minus.len(),
            fb.points.len(),
            "prepare must bind the current base"
        );
        let curve = ctx.group.0;
        for from in (0..self.minus.len()).step_by(self.block) {
            let to = (from + self.block).min(self.minus.len());
            self.sums.clear();
            self.slopes.clear();
            if self.lazy {
                curve.add_many_lazy(
                    target,
                    &self.minus[from..to],
                    &mut self.sums,
                    &mut self.slopes,
                    &mut self.scratch,
                );
            } else {
                curve.add_many(
                    target,
                    &self.minus[from..to],
                    &mut self.sums,
                    &mut self.scratch,
                );
            }
            ops.adds += (to - from) as u64;
            self.blocks += 1;
            self.lanes += (to - from) as u64;
            for (offset, &sum) in self.sums.iter().enumerate() {
                let full = if self.lazy && !sum.infinity {
                    self.x_tests += 1;
                    counters.lookups += 1;
                    if !fb.x_index.contains_key(&sum.x) {
                        continue;
                    }
                    let slope = self.slopes[offset];
                    if slope != crate::cryptanalysis::koblitz_fast::FastCurve::LAZY_DONE {
                        self.completed += 1;
                    }
                    curve.finish_lazy(target, sum, slope)
                } else {
                    sum
                };
                self.point_tests += 1;
                counters.lookups += 1;
                if let Some(j) = fb.index_of_key(ctx.group.key(&full)) {
                    return Some(vec![from + offset, j]);
                }
            }
        }
        None
    }
}

#[cfg(test)]
#[path = "binary_subtract_tests.rs"]
mod production_controls;
