//! Shared production integration controls; no timing windows.
use crate::binary_ecc::curve::point_add;
use crate::cryptanalysis::ic_boundary::{
    koblitz_instance, BinaryGroup, BinaryInstance, FactorBase, GroupOps, OracleCounters,
};
use crate::cryptanalysis::ic_framework::binary_subtract::BinarySubtractOracle;
use crate::cryptanalysis::ic_framework::plugins::{BinarySubspaceBase, SubtractOracle};
use crate::cryptanalysis::ic_framework::stages::{
    DecompositionOracle, FactorBaseBuilder, InstanceCtx, Params,
};
use crate::cryptanalysis::koblitz_fast::FastPoint;
use std::collections::HashMap;

fn ctx<'a>(inst: &'a BinaryInstance, g: &'a BinaryGroup<'a>) -> InstanceCtx<'a, BinaryGroup<'a>> {
    InstanceCtx {
        group: g,
        generator: inst.generator,
        target: inst.generator,
        r: inst.r,
        cofactor: inst.cofactor,
        group_order: inst.group_order,
        name: inst.name.clone(),
        field_degree: Some(inst.n),
    }
}
fn template(inst: &BinaryInstance, g: &BinaryGroup<'_>) -> FactorBase<FastPoint> {
    let mut params = Params::default();
    params.set("dimension", "3");
    BinarySubspaceBase { instance: inst }
        .build(&ctx(inst, g), &params, &mut GroupOps::default())
        .unwrap()
}
fn replace(base: &mut FactorBase<FastPoint>, points: Vec<FastPoint>) {
    base.points = points;
    base.point_index.clear();
    base.x_index.clear();
    for (i, p) in base.points.iter().enumerate() {
        base.point_index.insert(p.pack(), i);
        if !p.infinity {
            base.x_index.entry(p.x).or_default().push(i);
        }
    }
}
fn params(block: usize, lazy: bool) -> Params {
    let mut p = Params::default();
    p.set("block", block.to_string());
    p.set("lazy", if lazy { "1" } else { "0" });
    p
}

#[test]
fn first_witness_matches_independent_general_pair_enumeration() {
    let mut comparisons = 0u64;
    for a in [0, 1] {
        let inst = koblitz_instance(a, 7).unwrap();
        let g = BinaryGroup(&inst.fast);
        let context = ctx(&inst, &g);
        let mut all = vec![FastPoint::INFINITY];
        for x in 0..128 {
            for y in 0..128 {
                let p = FastPoint::affine(x, y);
                if inst.fast.is_on_curve(p) {
                    all.push(p);
                }
            }
        }
        assert!(all.iter().any(|p| !p.infinity && p.x == 0));
        let mut base = template(&inst, &g);
        for size in [0, 1, 2, 7, 33] {
            let mut points = all
                .iter()
                .step_by(2)
                .take(size)
                .copied()
                .collect::<Vec<_>>();
            if size > 2 {
                points.push(*all.iter().find(|p| !p.infinity && p.x == 0).unwrap());
                points.extend_from_within(1..3);
            }
            replace(&mut base, points);
            // Slow general curve arithmetic enumerates every ordered pair.
            // The j key follows the base index's duplicate-label convention.
            let general = &inst.koblitz.as_ref().unwrap().curve;
            let mut expected = HashMap::new();
            for (i, &p) in base.points.iter().enumerate() {
                for &q in &base.points {
                    let sum = point_add(general, &inst.fast.lower(p), &inst.fast.lower(q));
                    expected
                        .entry(inst.fast.lift(&sum).pack())
                        .or_insert_with(|| vec![i, base.index_of_key(q.pack()).unwrap()]);
                }
            }
            for block in [1, 2, 7, 32, 64] {
                for lazy in [false, true] {
                    let mut oracle = BinarySubtractOracle::new();
                    oracle
                        .prepare(
                            &context,
                            &base,
                            &params(block, lazy),
                            &mut GroupOps::default(),
                        )
                        .unwrap();
                    let mut scalar = SubtractOracle;
                    for &target in &all {
                        let mut ops = GroupOps::default();
                        let mut counters = OracleCounters::default();
                        let before = oracle.relation_counters()["binary_subtract_lanes"];
                        let got =
                            oracle.decompose(&context, &base, &mut ops, &mut counters, target);
                        let want = expected.get(&target.pack()).cloned();
                        assert_eq!(
                            got,
                            want,
                            "a={a} B={} block={block} lazy={lazy} T={target:?}",
                            base.points.len()
                        );
                        let reference = scalar.decompose(
                            &context,
                            &base,
                            &mut GroupOps::default(),
                            &mut OracleCounters::default(),
                            target,
                        );
                        assert_eq!(got, reference);
                        let scanned = got
                            .as_ref()
                            .map_or(base.points.len(), |v| (v[0] + 1).div_ceil(block) * block)
                            .min(base.points.len());
                        assert_eq!(ops.adds, scanned as u64);
                        assert_eq!(
                            oracle.relation_counters()["binary_subtract_lanes"] - before,
                            ops.adds
                        );
                        comparisons += 1;
                    }
                }
            }
        }
    }
    eprintln!(
        "production first-witness comparisons against general pair enumeration: {comparisons}"
    );
}

#[test]
fn native_fields_and_preparation_reuse_keep_scalar_answers() {
    let mut comparisons = 0;
    for (a, n) in [(1, 11), (1, 17), (0, 31)] {
        let inst = koblitz_instance(a, n)
            .unwrap_or_else(|| panic!("unavailable explicit fixture K{a}/n{n}"));
        let g = BinaryGroup(&inst.fast);
        let context = ctx(&inst, &g);
        let mut base = template(&inst, &g);
        let mut oracle = BinarySubtractOracle::new();
        for block in [1, 8, 32, 128] {
            for lazy in [false, true] {
                oracle
                    .prepare(
                        &context,
                        &base,
                        &params(block, lazy),
                        &mut GroupOps::default(),
                    )
                    .unwrap();
                let mut targets = (0..32)
                    .map(|k| inst.fast.mul_u64(inst.generator, k))
                    .collect::<Vec<_>>();
                targets.extend(base.points.iter().take(8).map(|&p| inst.fast.add(p, p)));
                for target in targets {
                    let got = oracle.decompose(
                        &context,
                        &base,
                        &mut GroupOps::default(),
                        &mut OracleCounters::default(),
                        target,
                    );
                    let want = SubtractOracle.decompose(
                        &context,
                        &base,
                        &mut GroupOps::default(),
                        &mut OracleCounters::default(),
                        target,
                    );
                    assert_eq!(got, want);
                    if let Some(pair) = got {
                        let sum = point_add(
                            &inst.koblitz.as_ref().unwrap().curve,
                            &inst.fast.lower(base.points[pair[0]]),
                            &inst.fast.lower(base.points[pair[1]]),
                        );
                        assert_eq!(sum, inst.fast.lower(target));
                    }
                    comparisons += 1;
                }
                // Same length, different contents: re-prepare must rebuild all
                // operands, not key a cache solely by the length.
                let mut reversed = base.points.clone();
                reversed.reverse();
                replace(&mut base, reversed);
            }
        }
    }
    eprintln!("production native-field/reprepare comparisons at n=11,17,31: {comparisons}");
}

#[test]
fn early_hit_charges_the_computed_block_and_failed_prepare_invalidates() {
    let inst = koblitz_instance(0, 7).unwrap();
    let g = BinaryGroup(&inst.fast);
    let context = ctx(&inst, &g);
    let mut base = template(&inst, &g);
    replace(
        &mut base,
        (1..9)
            .map(|k| inst.fast.mul_u64(inst.generator, k))
            .collect(),
    );
    assert!(base.points.len() > 2);
    let target = inst.fast.add(base.points[0], base.points[0]);
    let mut oracle = BinarySubtractOracle::new();
    oracle
        .prepare(&context, &base, &params(32, true), &mut GroupOps::default())
        .unwrap();
    let mut ops = GroupOps::default();
    let got = oracle
        .decompose(
            &context,
            &base,
            &mut ops,
            &mut OracleCounters::default(),
            target,
        )
        .unwrap();
    assert_eq!(got[0], 0);
    assert_eq!(ops.adds, base.points.len().min(32) as u64);
    assert!(ops.adds > 1);
    for (key, value) in [
        ("block", "0"),
        ("block", "4097"),
        ("m", "3"),
        ("lazy", "maybe"),
        ("unused", "1"),
    ] {
        let mut bad = Params::default();
        bad.set(key, value);
        assert!(oracle
            .prepare(&context, &base, &bad, &mut GroupOps::default())
            .is_err());
        assert!(
            std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| oracle.decompose(
                &context,
                &base,
                &mut GroupOps::default(),
                &mut OracleCounters::default(),
                target
            )))
            .is_err()
        );
    }
    oracle
        .prepare(
            &context,
            &base,
            &Params::default(),
            &mut GroupOps::default(),
        )
        .unwrap();
    assert!(oracle
        .decompose(
            &context,
            &base,
            &mut GroupOps::default(),
            &mut OracleCounters::default(),
            target
        )
        .is_some());
}

#[test]
fn composed_pipeline_recovers_the_same_public_known_answer() {
    use crate::cryptanalysis::ic_boundary::Calibration;
    use crate::cryptanalysis::ic_framework::stages::Targets;
    use crate::cryptanalysis::ic_framework::{run_pipeline, PipelineSpec};
    let inst = koblitz_instance(1, 11).unwrap();
    let g = BinaryGroup(&inst.fast);
    let mut context = ctx(&inst, &g);
    let planted = 17;
    context.target = inst.fast.mul_u64(inst.generator, planted);
    let base = BinarySubspaceBase { instance: &inst };
    let mut spec = PipelineSpec {
        factor_base: "binary-subspace".into(),
        oracle: "subtract".into(),
        targets: Targets::Walk,
        max_trials: 200_000,
        seed: 7,
        ..Default::default()
    };
    spec.factor_base_params.set("dimension", "5");
    let scalar = run_pipeline(
        &context,
        &spec,
        &base,
        &mut SubtractOracle,
        planted,
        &Calibration::default(),
        None,
    )
    .unwrap();
    spec.oracle = "subtract-binary-batch".into();
    let batch = run_pipeline(
        &context,
        &spec,
        &base,
        &mut BinarySubtractOracle::new(),
        planted,
        &Calibration::default(),
        None,
    )
    .unwrap();
    assert!(scalar.verified && batch.verified);
    assert_eq!(scalar.recovered, Some(planted));
    assert_eq!(batch.recovered, scalar.recovered);
    assert_eq!(
        batch.decomposition.targets_tried,
        scalar.decomposition.targets_tried
    );
}

#[test]
fn openssl_independent_binary_group_control_matches_first_witnesses() {
    use std::io::Write;
    use std::process::{Command, Stdio};
    let manifest = std::path::Path::new(env!("CARGO_MANIFEST_DIR"));
    let directory = [
        manifest.join("research/binary_subtract_frontier_20261115"),
        manifest
            .parent()
            .unwrap()
            .join("research/binary_subtract_frontier_20261115"),
        manifest.parent().unwrap().to_path_buf(),
    ]
    .into_iter()
    .find(|p| p.join("openssl_control.cpp").is_file())
    .expect("OpenSSL control source must be present");
    let binary =
        std::env::temp_dir().join(format!("binary-subtract-openssl-{}", std::process::id()));
    let build = Command::new("c++")
        .args(["-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror"])
        .arg(directory.join("openssl_control.cpp"))
        .arg("-lcrypto")
        .arg("-o")
        .arg(&binary)
        .output()
        .expect("C++ compiler is required for the external control");
    assert!(
        build.status.success(),
        "external control build: {}",
        String::from_utf8_lossy(&build.stderr)
    );
    let mut checked = 0;
    for (a, n) in [(0, 7), (1, 11), (0, 31)] {
        let inst = koblitz_instance(a, n).unwrap();
        let g = BinaryGroup(&inst.fast);
        let context = ctx(&inst, &g);
        let mut base = template(&inst, &g);
        let mut points = base.points.iter().step_by(2).copied().collect::<Vec<_>>();
        points.extend([FastPoint::INFINITY, FastPoint::affine(0, 1), points[0]]);
        replace(&mut base, points);
        let mut targets = vec![FastPoint::INFINITY, FastPoint::affine(0, 1)];
        targets.extend((0..24).map(|k| inst.fast.mul_u64(inst.generator, k)));
        targets.extend(base.points.iter().take(4).map(|&p| inst.fast.add(p, p)));
        let mut input = format!(
            "{} {} {} {} {} {}\n",
            n,
            inst.fast.field.irr,
            inst.a,
            inst.b,
            base.points.len(),
            targets.len()
        );
        for p in base.points.iter().chain(&targets) {
            input.push_str(&format!(
                "{} {} {}\n",
                u8::from(p.infinity),
                if p.infinity { 0 } else { p.x },
                if p.infinity { 0 } else { p.y }
            ));
        }
        let mut expected = String::new();
        let mut oracle = BinarySubtractOracle::new();
        oracle
            .prepare(
                &context,
                &base,
                &Params::default(),
                &mut GroupOps::default(),
            )
            .unwrap();
        for (i, &target) in targets.iter().enumerate() {
            match oracle.decompose(
                &context,
                &base,
                &mut GroupOps::default(),
                &mut OracleCounters::default(),
                target,
            ) {
                Some(v) => expected.push_str(&format!("{i} {} {}\n", v[0], v[1])),
                None => expected.push_str(&format!("{i} none\n")),
            }
        }
        let mut child = Command::new(&binary)
            .arg("--check")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        child
            .stdin
            .take()
            .unwrap()
            .write_all(input.as_bytes())
            .unwrap();
        let out = child.wait_with_output().unwrap();
        assert!(
            out.status.success(),
            "OpenSSL control n={n}: {}",
            String::from_utf8_lossy(&out.stderr)
        );
        assert_eq!(
            String::from_utf8(out.stdout).unwrap(),
            expected,
            "OpenSSL first-witness parity n={n}"
        );
        checked += targets.len();
    }
    std::fs::remove_file(binary).unwrap();
    eprintln!("independent OpenSSL binary-curve first-witness controls: {checked}");
}
