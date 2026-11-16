//! Complete signed-point adapter for native two-summand affine S3 projection.
use std::collections::BTreeMap;
use std::time::Instant;

use super::stages::{DecompositionOracle, InstanceCtx, Params};
use crate::cryptanalysis::ic_boundary::{
    BinaryGroup, BinaryInstance, CountedGroup, FactorBase, GroupOps, OracleCounters,
};
use crate::cryptanalysis::koblitz_fast::FastPoint;
use crate::cryptanalysis::s3_affine_projection::{ProjectionError, S3AffineProjection};

pub struct AffineS3Oracle<'i> {
    instance: &'i BinaryInstance,
    plan: Option<S3AffineProjection>,
    max_residual: usize,
    setup_ns: u64,
    native_ns: u64,
    queries: u64,
    candidates: u64,
    capped_fallbacks: u64,
    zero_fallbacks: u64,
    lift_checks: u64,
    cache_bytes: u64,
}

impl<'i> AffineS3Oracle<'i> {
    pub fn new(instance: &'i BinaryInstance) -> Self {
        Self {
            instance,
            plan: None,
            max_residual: 12,
            setup_ns: 0,
            native_ns: 0,
            queries: 0,
            candidates: 0,
            capped_fallbacks: 0,
            zero_fallbacks: 0,
            lift_checks: 0,
            cache_bytes: 0,
        }
    }

    fn add(
        group: &BinaryGroup<'_>,
        ops: &mut GroupOps,
        a: FastPoint,
        b: FastPoint,
        group_ns: &mut u64,
    ) -> FastPoint {
        let started = Instant::now();
        let result = group.add(ops, a, b);
        *group_ns = group_ns.saturating_add(started.elapsed().as_nanos() as u64);
        result
    }

    /// Exhaustive linear subtraction is complete for every valid target,
    /// including identity/torsion and capped projection spaces.
    fn fallback(
        &self,
        ctx: &InstanceCtx<BinaryGroup<'_>>,
        fb: &FactorBase<FastPoint>,
        ops: &mut GroupOps,
        point: FastPoint,
        group_ns: &mut u64,
    ) -> Option<Vec<usize>> {
        for (i, &p) in fb.points.iter().enumerate() {
            let rest = Self::add(ctx.group, ops, point, ctx.group.neg(p), group_ns);
            if let Some(&j) = fb.point_index.get(&ctx.group.key(&rest)) {
                return Some(vec![i, j]);
            }
        }
        None
    }

    fn query(
        &mut self,
        ctx: &InstanceCtx<BinaryGroup<'_>>,
        fb: &FactorBase<FastPoint>,
        ops: &mut GroupOps,
        point: FastPoint,
        group_ns: &mut u64,
    ) -> Option<Vec<usize>> {
        if point.infinity || point.x == 0 {
            self.zero_fallbacks += 1;
            return self.fallback(ctx, fb, ops, point, group_ns);
        }
        let roots = match self
            .plan
            .as_ref()
            .expect("prepare precedes decomposition")
            .roots(point.x, self.max_residual)
        {
            Ok(roots) => roots,
            Err(ProjectionError::ResidualCap { .. }) => {
                self.capped_fallbacks += 1;
                return self.fallback(ctx, fb, ops, point, group_ns);
            }
            Err(ProjectionError::ZeroAbscissa | ProjectionError::OutsideField) => {
                return self.fallback(ctx, fb, ops, point, group_ns);
            }
        };
        self.candidates = self.candidates.saturating_add(roots.affine_candidates);
        for (x, y) in roots.pairs {
            let (Some(left), Some(right)) = (fb.x_index.get(&x), fb.x_index.get(&y)) else {
                continue;
            };
            for &i in left {
                for &j in right {
                    self.lift_checks += 1;
                    if Self::add(ctx.group, ops, fb.points[i], fb.points[j], group_ns) == point {
                        return Some(vec![i, j]);
                    }
                }
            }
        }
        None
    }
}

impl<'a> DecompositionOracle<BinaryGroup<'a>> for AffineS3Oracle<'_> {
    fn name(&self) -> &str {
        "affine-s3"
    }
    fn summands(&self) -> u32 {
        2
    }
    fn describe(&self, _params: &Params) -> String {
        "native affine S3 projection with exact signed lifts; complete subtraction fallback for zero targets and residual caps".into()
    }
    fn parameters(&self) -> &[(&str, &str)] {
        &[("max_residual","maximum affine free dimension (0..=20, default12); larger spaces use complete subtraction")]
    }
    fn prepare(
        &mut self,
        ctx: &InstanceCtx<BinaryGroup<'a>>,
        fb: &FactorBase<FastPoint>,
        params: &Params,
        _ops: &mut GroupOps,
    ) -> Result<(), String> {
        if params.u64_or("m", 2)? != 2 {
            return Err("affine-s3 supports exactly two summands".into());
        }
        self.max_residual = params.u64_or("max_residual", 12)? as usize;
        if self.max_residual > 20 {
            return Err("max_residual must be in0..=20".into());
        }
        if ctx.group.0.field.irr != self.instance.gf.irr
            || ctx.group.0.a != self.instance.a
            || ctx.group.0.b != self.instance.b
            || ctx.r != self.instance.r
        {
            return Err("affine-s3 context differs from the declared instance".into());
        }
        let basis = fb
            .subspace_basis
            .as_deref()
            .ok_or("affine-s3 requires a subspace factor base")?;
        let started = Instant::now();
        self.plan = Some(
            S3AffineProjection::new(&self.instance.gf, self.instance.b, basis)
                .map_err(str::to_string)?,
        );
        let column_solver = params.u64_or("column_solver", 0)?;
        if column_solver > 1 {
            return Err("column_solver must be0 or1".into());
        }
        self.plan
            .as_mut()
            .unwrap()
            .set_column_solver(column_solver == 1);
        if params.u64_or("inverse_cache", 0)? > 1 {
            return Err("inverse_cache must be0 or1".into());
        }
        if params.u64_or("inverse_cache", 0)? == 1 {
            self.plan
                .as_mut()
                .unwrap()
                .prepare_prefix_inverse_cache()
                .map_err(str::to_string)?;
        }
        self.cache_bytes = self.plan.as_ref().unwrap().inverse_cache_bytes() as u64;
        self.setup_ns = self
            .setup_ns
            .saturating_add(started.elapsed().as_nanos() as u64);
        Ok(())
    }
    fn setup_native(&self) -> BTreeMap<String, u64> {
        BTreeMap::from([
            ("affine_s3_ns".into(), self.setup_ns),
            ("affine_s3_cache_bytes".into(), self.cache_bytes),
        ])
    }
    fn relation_counters(&self) -> BTreeMap<String, u64> {
        BTreeMap::from([
            ("affine_s3_ns".into(), self.native_ns),
            ("affine_s3_queries".into(), self.queries),
            ("affine_s3_candidates".into(), self.candidates),
            ("affine_s3_cap_fallbacks".into(), self.capped_fallbacks),
            ("affine_s3_zero_fallbacks".into(), self.zero_fallbacks),
            ("affine_s3_lift_checks".into(), self.lift_checks),
        ])
    }
    fn decompose(
        &mut self,
        ctx: &InstanceCtx<BinaryGroup<'a>>,
        fb: &FactorBase<FastPoint>,
        ops: &mut GroupOps,
        _counters: &mut OracleCounters,
        point: FastPoint,
    ) -> Option<Vec<usize>> {
        let started = Instant::now();
        let mut group_ns = 0;
        self.queries += 1;
        let result = self.query(ctx, fb, ops, point, &mut group_ns);
        // Every native query, including failures/fallbacks, is charged. Actual
        // group-add intervals are removed because GroupOps prices them already.
        let native = (started.elapsed().as_nanos() as u64).saturating_sub(group_ns);
        self.native_ns = self.native_ns.saturating_add(native);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::ic_boundary::{
        binary_subspace_factor_base, random_binary_instance, Calibration,
    };
    use crate::cryptanalysis::ic_framework::plugins::BinarySubspaceBase;
    use crate::cryptanalysis::ic_framework::stages::Targets;
    use crate::cryptanalysis::ic_framework::{run_pipeline, PipelineSpec};
    use std::collections::BTreeSet;

    #[test]
    fn every_curve_target_matches_complete_signed_pair_enumeration() {
        for n in [5, 6, 7, 8] {
            let inst = random_binary_instance(n, 3, 8).unwrap();
            let group = BinaryGroup(&inst.fast);
            let ctx = InstanceCtx {
                group: &group,
                generator: inst.generator,
                target: inst.generator,
                r: inst.r,
                cofactor: inst.cofactor,
                group_order: inst.group_order,
                name: inst.name.clone(),
                field_degree: Some(n),
            };
            let fb = binary_subspace_factor_base(&inst, &[1, 2, 4]);
            let mut sums = BTreeSet::new();
            for &p in &fb.points {
                for &q in &fb.points {
                    sums.insert(inst.fast.add(p, q).pack());
                }
            }
            let mut targets = vec![FastPoint::INFINITY];
            for x in 0..1 << n {
                targets.extend(inst.points_with_x(x));
            }
            for (limit, cache) in [(0, 0), (12, 0), (12, 1)] {
                let mut oracle = AffineS3Oracle::new(&inst);
                let mut params = Params::default();
                params.set("max_residual", limit.to_string());
                params.set("inverse_cache", cache.to_string());
                oracle
                    .prepare(&ctx, &fb, &params, &mut GroupOps::default())
                    .unwrap();
                for &target in &targets {
                    let got = oracle.decompose(
                        &ctx,
                        &fb,
                        &mut GroupOps::default(),
                        &mut OracleCounters::default(),
                        target,
                    );
                    assert_eq!(
                        got.is_some(),
                        sums.contains(&target.pack()),
                        "n={n} limit={limit} target={target:?}"
                    );
                    if let Some(pair) = got {
                        assert_eq!(
                            inst.fast.add(fb.points[pair[0]], fb.points[pair[1]]),
                            target
                        );
                    }
                }
                assert!(oracle.zero_fallbacks > 0);
                if limit == 0 && n == 5 {
                    assert!(oracle.capped_fallbacks > 0);
                }
            }
        }
    }

    #[test]
    fn pipeline_recovers_the_scalar_with_setup_and_query_charges() {
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
            oracle: "affine-s3".into(),
            targets: Targets::Walk,
            seed: 7,
            max_trials: 200_000,
            ..Default::default()
        };
        spec.factor_base_params.set("dimension", "5");
        spec.oracle_params.set("inverse_cache", "1");
        let mut oracle = AffineS3Oracle::new(&inst);
        let calib = Calibration {
            ns_per_add: 1.0,
            ..Default::default()
        };
        let report = run_pipeline(
            &ctx,
            &spec,
            &BinarySubspaceBase { instance: &inst },
            &mut oracle,
            planted,
            &calib,
            None,
        )
        .unwrap();
        assert_eq!(report.decomposition.setup.get("affine_s3_cache_bytes"), 256);
        assert!(report.verified);
        assert_eq!(report.recovered, Some(planted));
        for phase in [&report.decomposition.setup, &report.decomposition.cost] {
            assert!(phase.get("affine_s3_ns") > 0);
            assert!(phase.gae >= phase.get("affine_s3_ns") as f64);
        }
        assert!(report.decomposition.cost.get("affine_s3_queries") > 0);
    }
}
