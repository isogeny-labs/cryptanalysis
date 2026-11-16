//! Opt-in binary MITM with complete native batch preparation accounting.
use super::stages::{DecompositionOracle, InstanceCtx, Params};
use crate::cryptanalysis::ic_boundary::{
    decompose_mitm, BinaryGroup, FactorBase, GroupOps, OracleCounters, PairTable,
};
use crate::cryptanalysis::koblitz_fast::FastPoint;
use std::collections::BTreeMap;
use std::time::Instant;

#[derive(Default)]
pub struct BinaryBatchMitmOracle {
    table: Option<PairTable>,
    setup_ns: u64,
}

impl<'a> DecompositionOracle<BinaryGroup<'a>> for BinaryBatchMitmOracle {
    fn name(&self) -> &str {
        "mitm-batched"
    }
    fn summands(&self) -> u32 {
        2
    }
    fn describe(&self, _params: &Params) -> String {
        "ordered negation-folded binary pair table with bounded batch inversions; complete native setup charged".into()
    }
    fn parameters(&self) -> &[(&str, &str)] {
        &[
            (
                "batch_size",
                "bounded ordered preparation chunk (1..=65536, default1024)",
            ),
            ("prefix_inverse_cache", "0 or1, default0; implies x-only, bounded prefix inverse reuse or complete generic fallback"),
            (
                "x_only",
                "0 or1, default0; omit unused ordinates during preparation",
            ),
        ]
    }
    fn prepare(
        &mut self,
        ctx: &InstanceCtx<BinaryGroup<'a>>,
        fb: &FactorBase<FastPoint>,
        params: &Params,
        _ops: &mut GroupOps,
    ) -> Result<(), String> {
        if params.u64_or("m", 2)? != 2 {
            return Err("mitm-batched supports exactly two summands".into());
        }
        let size = params.u64_or("batch_size", 1024)?;
        if !(1..=65536).contains(&size) {
            return Err("batch_size must be in1..=65536".into());
        }
        let x_only = params.u64_or("x_only", 0)?;
        if x_only > 1 {
            return Err("x_only must be0 or1".into());
        }
        let prefix_cache = params.u64_or("prefix_inverse_cache", 0)?;
        if prefix_cache > 1 {
            return Err("prefix_inverse_cache must be0 or1".into());
        }
        let start = Instant::now();
        self.table = Some(
            (if prefix_cache == 1 {
                PairTable::build_negation_folded_binary_prefix_cached(
                    ctx.group.0,
                    fb,
                    size as usize,
                )
            } else if x_only == 1 {
                PairTable::build_negation_folded_binary_abscissae(ctx.group.0, fb, size as usize)
            } else {
                PairTable::build_negation_folded_binary_batched(ctx.group.0, fb, size as usize)
            })
            .map_err(str::to_string)?,
        );
        self.setup_ns = self
            .setup_ns
            .saturating_add(start.elapsed().as_nanos() as u64);
        Ok(())
    }
    fn setup_native(&self) -> BTreeMap<String, u64> {
        BTreeMap::from([
            ("mitm_batch_setup_ns".into(), self.setup_ns),
            (
                "mitm_prefix_inverse_bytes".into(),
                self.table
                    .as_ref()
                    .map_or(0, |t| t.prefix_inverse_bytes as u64),
            ),
        ])
    }
    fn decompose(
        &mut self,
        ctx: &InstanceCtx<BinaryGroup<'a>>,
        fb: &FactorBase<FastPoint>,
        ops: &mut GroupOps,
        counters: &mut OracleCounters,
        point: FastPoint,
    ) -> Option<Vec<usize>> {
        decompose_mitm(ctx.group, fb, self.table.as_ref()?, 2, ops, counters, point)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::ic_boundary::{random_binary_instance, Calibration, CountedGroup};
    use crate::cryptanalysis::ic_framework::plugins::BinarySubspaceBase;
    use crate::cryptanalysis::ic_framework::stages::Targets;
    use crate::cryptanalysis::ic_framework::{run_pipeline, PipelineSpec};

    #[test]
    fn complete_pipeline_prices_native_preparation_without_individual_adds() {
        let inst = random_binary_instance(11, 3, 8).unwrap();
        let group = BinaryGroup(&inst.fast);
        let planted = 1 + 30_011 % (inst.r - 1);
        let target = group.mul(&mut GroupOps::default(), inst.generator, planted);
        let ctx = InstanceCtx {
            group: &group,
            generator: inst.generator,
            target,
            r: inst.r,
            cofactor: inst.cofactor,
            group_order: inst.group_order,
            name: inst.name.clone(),
            field_degree: Some(inst.n),
        };
        let mut spec = PipelineSpec {
            factor_base: "binary-subspace".into(),
            oracle: "mitm-batched".into(),
            targets: Targets::Walk,
            seed: 7,
            max_trials: 200_000,
            ..Default::default()
        };
        spec.factor_base_params.set("dimension", "5");
        let calib = Calibration {
            ns_per_add: 1.0,
            ..Default::default()
        };
        let report = run_pipeline(
            &ctx,
            &spec,
            &BinarySubspaceBase { instance: &inst },
            &mut BinaryBatchMitmOracle::default(),
            planted,
            &calib,
            None,
        )
        .unwrap();
        assert!(report.verified);
        assert_eq!(report.recovered, Some(planted));
        let setup = &report.decomposition.setup;
        assert!(setup.get("mitm_batch_setup_ns") > 0);
        assert_eq!(setup.group_ops, GroupOps::default());
        assert_eq!(setup.gae, setup.get("mitm_batch_setup_ns") as f64);
        spec.oracle_params.set("x_only", "1");
        let x_report = run_pipeline(
            &ctx,
            &spec,
            &BinarySubspaceBase { instance: &inst },
            &mut BinaryBatchMitmOracle::default(),
            planted,
            &calib,
            None,
        )
        .unwrap();
        assert!(x_report.verified);
        assert_eq!(x_report.recovered, Some(planted));
        assert_eq!(
            x_report.decomposition.targets_tried,
            report.decomposition.targets_tried
        );
        assert_eq!(
            x_report.decomposition.relations_found,
            report.decomposition.relations_found
        );
        assert_eq!(x_report.linear_algebra.rank, report.linear_algebra.rank);
        assert_eq!(x_report.decomposition.setup.group_ops, GroupOps::default());
        assert_eq!(
            x_report.decomposition.setup.gae,
            x_report.decomposition.setup.get("mitm_batch_setup_ns") as f64
        );
        spec.oracle_params.set("prefix_inverse_cache", "1");
        let cached_report = run_pipeline(
            &ctx,
            &spec,
            &BinarySubspaceBase { instance: &inst },
            &mut BinaryBatchMitmOracle::default(),
            planted,
            &calib,
            None,
        )
        .unwrap();
        assert!(cached_report.verified);
        assert_eq!(cached_report.recovered, Some(planted));
        assert_eq!(
            cached_report
                .decomposition
                .setup
                .get("mitm_prefix_inverse_bytes"),
            256
        );
        assert_eq!(
            cached_report.decomposition.setup.group_ops,
            GroupOps::default()
        );
        assert_eq!(
            cached_report.decomposition.setup.gae,
            cached_report.decomposition.setup.get("mitm_batch_setup_ns") as f64
        );
        assert_eq!(
            cached_report.decomposition.targets_tried,
            report.decomposition.targets_tried
        );
        assert_eq!(
            cached_report.linear_algebra.rank,
            report.linear_algebra.rank
        );
        spec.oracle = "mitm".into();
        spec.oracle_params.set("negation_folded", "1");
        spec.oracle_params.set("native_setup_pricing", "1");
        let reference = run_pipeline(
            &ctx,
            &spec,
            &BinarySubspaceBase { instance: &inst },
            &mut crate::cryptanalysis::ic_framework::plugins::MitmOracle::new(2),
            planted,
            &calib,
            None,
        )
        .unwrap();
        assert!(reference.verified);
        let setup = &reference.decomposition.setup;
        assert_eq!(setup.group_ops, GroupOps::default());
        assert_eq!(setup.gae, setup.get("mitm_native_setup_ns") as f64);
        assert!(setup.get("mitm_setup_observed_adds") > 0);
        assert_eq!(
            reference.decomposition.targets_tried,
            cached_report.decomposition.targets_tried
        );
        assert_eq!(
            reference.linear_algebra.rank,
            cached_report.linear_algebra.rank
        );
        let empty = FactorBase::<FastPoint>::empty("empty validation base".into());
        let table = PairTable::build_negation_folded_binary_batched(&inst.fast, &empty, 7).unwrap();
        assert_eq!(table.entries, 0);
        assert!(table
            .probe(
                &group,
                &empty,
                &mut GroupOps::default(),
                &mut 0,
                inst.generator
            )
            .is_none());
        for (key, value) in [
            ("m", "3"),
            ("batch_size", "0"),
            ("batch_size", "65537"),
            ("x_only", "2"),
            ("prefix_inverse_cache", "2"),
        ] {
            let mut params = Params::default();
            params.set(key, value);
            assert!(BinaryBatchMitmOracle::default()
                .prepare(&ctx, &empty, &params, &mut GroupOps::default())
                .is_err());
        }
    }
}
