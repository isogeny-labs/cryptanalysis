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
        &[(
            "batch_size",
            "bounded ordered preparation chunk (1..=65536, default1024)",
        )]
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
        let start = Instant::now();
        self.table = Some(
            PairTable::build_negation_folded_binary_batched(ctx.group.0, fb, size as usize)
                .map_err(str::to_string)?,
        );
        self.setup_ns = self
            .setup_ns
            .saturating_add(start.elapsed().as_nanos() as u64);
        Ok(())
    }
    fn setup_native(&self) -> BTreeMap<String, u64> {
        BTreeMap::from([("mitm_batch_setup_ns".into(), self.setup_ns)])
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
        for (key, value) in [("m", "3"), ("batch_size", "0"), ("batch_size", "65537")] {
            let mut params = Params::default();
            params.set(key, value);
            assert!(BinaryBatchMitmOracle::default()
                .prepare(&ctx, &empty, &params, &mut GroupOps::default())
                .is_err());
        }
    }
}
