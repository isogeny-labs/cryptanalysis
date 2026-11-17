//! Fixed registered public instances through the actual IC framework.
use cryptanalysis_suite::binary_ecc::{BinaryCurve, BinaryPoint, IrreduciblePoly};
use cryptanalysis_suite::cryptanalysis::ic_boundary::{
    binary_subspace_factor_base, calibrate_binary_instance, rho_reference, rho_reference_negation,
    ArtinSchreier, BinaryGroup, BinaryInstance, Calibration, CountedGroup, GroupOps, PairTable,
};
use cryptanalysis_suite::cryptanalysis::ic_framework::affine::AffineS3Oracle;
use cryptanalysis_suite::cryptanalysis::ic_framework::batch_mitm::BinaryBatchMitmOracle;
use cryptanalysis_suite::cryptanalysis::ic_framework::plugins::{BinarySubspaceBase, MitmOracle};
use cryptanalysis_suite::cryptanalysis::ic_framework::stages::{
    DecompositionOracle, InstanceCtx, Targets,
};
use cryptanalysis_suite::cryptanalysis::ic_framework::{run_pipeline, PipelineSpec};
use cryptanalysis_suite::cryptanalysis::koblitz_fast::{FastCurve, FastPoint};
use cryptanalysis_suite::cryptanalysis::semaev_decomp::Gf2;
use num_bigint::BigUint;
use rand::{rngs::StdRng, Rng, SeedableRng};
use serde_json::{json, Value};
use std::time::Instant;

fn integer(v: &Value) -> u64 {
    v.as_u64().unwrap_or_else(|| {
        let s = v.as_str().unwrap();
        if let Some(s) = s.strip_prefix("0x") {
            u64::from_str_radix(s, 16).unwrap()
        } else {
            s.parse().unwrap()
        }
    })
}

fn instance(record: &Value) -> BinaryInstance {
    let field = &record["field"];
    let curve = &record["curve"];
    let n = integer(&field["degree"]) as u32;
    let irreducible = IrreduciblePoly {
        degree: n,
        low_terms: field["modulus_exponents"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| integer(v) as u32)
            .filter(|&e| e != n)
            .collect(),
    };
    let gf = Gf2::new(&irreducible);
    let ash = ArtinSchreier::new(&gf);
    let a = integer(&curve["coefficients"][1]);
    let b = integer(&curve["coefficients"][4]);
    let r = integer(&curve["subgroup_order"]);
    let cofactor = integer(&curve["cofactor"]);
    let generator = FastPoint::affine(
        integer(&curve["generator"][0]),
        integer(&curve["generator"][1]),
    );
    let slow = BinaryCurve {
        m: n,
        irreducible: irreducible.clone(),
        a: gf.to_element(a),
        b: gf.to_element(b),
        generator: BinaryPoint::Infinity,
        order: BigUint::from(r),
        cofactor: BigUint::from(cofactor),
    };
    let fast = FastCurve::new(&slow).unwrap();
    BinaryInstance {
        name: record["curve_id"].as_str().unwrap().into(),
        n,
        irreducible,
        fast,
        gf,
        artin_schreier: ash,
        a,
        b,
        group_order: r * cofactor,
        r,
        cofactor,
        generator,
        koblitz: None,
    }
}

// A benchmark unit receipt, checked before reuse by every arm on this curve.
fn frozen_calibration(path: &str, curve_id: &str) -> Calibration {
    let receipt: Value = serde_json::from_slice(&std::fs::read(path).unwrap()).unwrap();
    assert_eq!(receipt["curve_id"], curve_id);
    let r = &receipt["calibration"];
    let required = |key: &str| {
        let x = r[key].as_f64().expect("missing calibration unit");
        assert!(x.is_finite() && x > 0.0);
        x
    };
    let optional = |key: &str| {
        let value = r[key].as_f64();
        if let Some(x) = value {
            assert!(x.is_finite() && x >= 0.0);
        }
        value
    };
    Calibration {
        ns_per_add: required("ns_per_add"),
        ns_per_double: required("ns_per_double"),
        ns_per_lookup: required("ns_per_lookup"),
        ns_per_row_op: required("ns_per_row_op"),
        ns_per_sqrt: optional("ns_per_sqrt"),
        ns_per_as_solve: optional("ns_per_as_solve"),
        ns_per_s4_pair: optional("ns_per_s4_pair"),
        ns_per_word_xor: optional("ns_per_word_xor"),
        ns_per_legendre: optional("ns_per_legendre"),
        ns_per_inversion: optional("ns_per_inversion"),
        ns_per_frobenius: optional("ns_per_frobenius"),
        ns_per_canon: optional("ns_per_canon"),
        pinned_units: serde_json::from_value(r["pinned_units"].clone()).unwrap(),
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let records: Vec<Value> = serde_json::from_slice(&std::fs::read(&args[1]).unwrap()).unwrap();
    let index: usize = args[2].parse().unwrap();
    let requested_mode = args[3].as_str();
    let euclidean = matches!(
        requested_mode,
        "mitm-euclid"
            | "mitm-euclid-u32"
            | "rho-plain-euclid"
            | "rho-negation-euclid"
            | "verify-table-euclid"
    );
    let mode = match requested_mode {
        "mitm-euclid"
        | "mitm-euclid-u32"
        | "mitm-prefix-u32"
        | "mitm-vector"
        | "mitm-vector64"
        | "mitm-vector4096"
        | "mitm-prefix64"
        | "mitm-vector-packed"
        | "mitm-vector-packed64" => "mitm-prefix",
        "mitm-walk-incumbent"
        | "mitm-walk16-scalar"
        | "mitm-walk16-native"
        | "mitm-walk16-vector"
        | "mitm-walk16-vector-const"
        | "mitm-walk16-vector-narrow"
        | "mitm-walk16-vector-inverse" => "mitm-prefix",
        "rho-plain-euclid" => "rho-plain",
        "rho-negation-euclid" => "rho-negation",
        "verify-table-euclid" => "verify-table",
        other => other,
    };
    let record = &records[index];
    let started = Instant::now();
    let mut inst = instance(record);
    inst.gf.set_euclidean_inverse(euclidean);
    inst.fast.field.set_euclidean_inverse(euclidean);
    let context_ns = started.elapsed().as_nanos() as u64;
    let group = BinaryGroup(&inst.fast);
    let dimension = integer(&record["dimension"]) as u32;
    if mode == "manifest" {
        let basis: Vec<u64> = (0..dimension).map(|i| 1 << i).collect();
        let fb = binary_subspace_factor_base(&inst, &basis);
        let mut ops = GroupOps::default();
        assert!(!inst.generator.infinity);
        assert!(group.mul(&mut ops, inst.generator, inst.r).infinity);
        assert!(inst
            .points_with_x(inst.generator.x)
            .contains(&inst.generator));
        let mut rows: Vec<_> = fb
            .points
            .iter()
            .enumerate()
            .map(|(i, p)| {
                json!({"point":[p.x,p.y],"column":fb.col_of[i],"coefficient":fb.coef_of[i],
                   "strict_subgroup":group.mul(&mut ops,*p,inst.r).infinity,
                   "quotient_nonzero":!group.mul(&mut ops,*p,inst.cofactor).infinity})
            })
            .collect();
        rows.sort_by_key(|p| {
            (
                p["point"][0].as_u64().unwrap(),
                p["point"][1].as_u64().unwrap(),
            )
        });
        println!(
            "{}",
            json!({"record":record,"basis":basis,"columns":fb.columns,"rows":rows})
        );
        return;
    }
    if matches!(mode, "verify-xonly" | "verify-prefix") {
        let basis: Vec<_> = (0..dimension).map(|i| 1 << i).collect();
        let fb = binary_subspace_factor_base(&inst, &basis);
        let reference = PairTable::build_negation_folded(&group, &fb);
        let mut checked = 0u64;
        for chunk in [1, 7, 1024] {
            let batch = if mode == "verify-prefix" {
                PairTable::build_negation_folded_binary_prefix_cached(&inst.fast, &fb, chunk)
            } else {
                PairTable::build_negation_folded_binary_abscissae(&inst.fast, &fb, chunk)
            }
            .unwrap();
            if mode == "verify-prefix" {
                assert_eq!(batch.prefix_inverse_bytes, (1usize << dimension) * 8);
            }
            assert_eq!(reference.entries, batch.entries);
            let mut check = |p| {
                assert_eq!(
                    reference.probe(&group, &fb, &mut GroupOps::default(), &mut 0, p),
                    batch.probe(&group, &fb, &mut GroupOps::default(), &mut 0, p)
                );
                checked += 1;
            };
            check(FastPoint::INFINITY);
            for x in 0..1u64 << inst.n {
                for p in inst.points_with_x(x) {
                    check(p);
                }
            }
        }
        assert_eq!(checked, inst.group_order * 3);
        println!(
            "{}",
            json!({"curve_id":inst.name,"status":"pass","checks":checked,"has_clmul":inst.gf.has_clmul()})
        );
        return;
    }
    if mode == "verify-table" {
        let basis: Vec<_> = (0..dimension).map(|i| 1 << i).collect();
        let fb = binary_subspace_factor_base(&inst, &basis);
        let reference = PairTable::build_negation_folded(&group, &fb);
        if euclidean {
            let original = instance(record);
            let original_group = BinaryGroup(&original.fast);
            let original_fb = binary_subspace_factor_base(&original, &basis);
            assert_eq!(fb.points, original_fb.points);
            assert!(
                reference.same_witness_map(&PairTable::build_negation_folded(
                    &original_group,
                    &original_fb,
                ))
            );
        }
        let mut comparisons = 0;
        let mut vector_pairs = 0;
        let mut vector_pclmul128_pairs = 0;
        let mut vector_packed_square_pairs = 0;
        let mut vector_const_pairs = 0;
        let mut vector_const_packed_square_pairs = 0;
        let mut vector_const_validated_pairs = 0;
        let mut indexed_prepare_pairs = 0;
        let mut static_map_comparisons = 0;
        let mut compact_map_comparisons = 0;
        let mut compact_entry_payload_bytes = 0;
        for chunk in [1, 7, 64, 1024, 4096] {
            for candidate in [
                PairTable::build_negation_folded_binary_vector_narrow_cached(
                    &inst.fast, &fb, chunk,
                )
                .unwrap(),
                PairTable::build_negation_folded_binary_vector_const_cached(&inst.fast, &fb, chunk)
                    .unwrap(),
                PairTable::build_negation_folded_binary_batched(&inst.fast, &fb, chunk).unwrap(),
                PairTable::build_negation_folded_binary_abscissae(&inst.fast, &fb, chunk).unwrap(),
                PairTable::build_negation_folded_binary_prefix_cached(&inst.fast, &fb, chunk)
                    .unwrap(),
                PairTable::build_negation_folded_binary_vector_cached(&inst.fast, &fb, chunk)
                    .unwrap(),
                PairTable::build_negation_folded_binary_vector_packed_cached(
                    &inst.fast, &fb, chunk,
                )
                .unwrap(),
            ] {
                vector_const_pairs += candidate.vector_const_pairs;
                indexed_prepare_pairs += candidate.indexed_prepare_pairs;
                static_map_comparisons += usize::from(candidate.uses_static_storage());
                if candidate.vector_const_pairs != 0 {
                    assert_eq!(
                        candidate.vector_packed_square_pairs,
                        candidate.vector_const_pairs
                    );
                    vector_const_packed_square_pairs += candidate.vector_packed_square_pairs;
                }
                vector_pairs += candidate.vector_pairs;
                vector_pclmul128_pairs += candidate.vector_pclmul128_pairs;
                vector_packed_square_pairs += candidate.vector_packed_square_pairs;
                if candidate.uses_compact_storage() {
                    compact_map_comparisons += 1;
                    vector_const_validated_pairs += candidate.vector_const_pairs;
                    compact_entry_payload_bytes = candidate.witness_entry_payload_bytes();
                    assert_eq!(compact_entry_payload_bytes, 8);
                } else {
                    assert_eq!(candidate.witness_entry_payload_bytes(), 16);
                }
                assert!(reference.same_witness_map(&candidate));
                comparisons += 1;
            }
        }
        println!(
            "{}",
            json!({"curve_id":inst.name,"status":"pass","euclidean_inverse":inst.gf.uses_euclidean_inverse(),"vector_const_pairs":vector_const_pairs,"vector_const_packed_square_pairs":vector_const_packed_square_pairs,"vector_const_validated_pairs":vector_const_validated_pairs,"indexed_prepare_pairs":indexed_prepare_pairs,"static_map_comparisons":static_map_comparisons,"vector_packed_square_pairs":vector_packed_square_pairs,"vector_pclmul128_pairs":vector_pclmul128_pairs,"vector_backend":inst.fast.cached_vector_backend(),"vector_pairs":vector_pairs,"complete_map_comparisons":comparisons,"compact_map_comparisons":compact_map_comparisons,"compact_entry_payload_bytes":compact_entry_payload_bytes,"entries":reference.entries,"has_clmul":inst.gf.has_clmul()})
        );
        return;
    }
    let fixture: u64 = args[4].parse().unwrap();
    let mut rng =
        StdRng::seed_from_u64(0x5333_5049_5045 ^ fixture.wrapping_mul(0x9e37_79b9_7f4a_7c15));
    let planted = rng.gen_range(1..inst.r);
    let target = group.mul(&mut GroupOps::default(), inst.generator, planted);
    let target_seed = rng.gen::<u64>();
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
    let started = Instant::now();
    let calibration = if matches!(mode, "workload" | "verify-walkbatch") {
        Default::default()
    } else if let Some(path) = args.get(5) {
        frozen_calibration(path, &inst.name)
    } else {
        let mut units = calibrate_binary_instance(&inst);
        let basis: Vec<_> = (0..dimension).map(|i| 1 << i).collect();
        let fb = binary_subspace_factor_base(&inst, &basis);
        let table = PairTable::build_negation_folded(&group, &fb);
        units.ns_per_lookup = table.calibrate_lookup(1_000_000);
        assert!(units.ns_per_lookup.is_finite() && units.ns_per_lookup > 0.0);
        units
    };
    let calibration_ns = started.elapsed().as_nanos() as u64;
    if mode == "workload" {
        println!(
            "{}",
            json!({"curve_id":inst.name,"fixture":fixture,"planted":planted,"target":[target.x,target.y],"target_seed":target_seed})
        );
        return;
    }
    if mode == "calibration" {
        println!(
            "{}",
            json!({"curve_id":inst.name,"calibration":calibration,"calibration_ns":calibration_ns})
        );
        return;
    }
    if mode == "verify-walkbatch" {
        use cryptanalysis_suite::cryptanalysis::ic_boundary::{
            trace_batched_walk, trace_batched_walk_vector, trace_batched_walk_vector_inverse,
            RestartPool,
        };
        let native = trace_batched_walk(
            &group,
            inst.generator,
            target,
            inst.r,
            target_seed,
            512,
            true,
            RestartPool::Lazy,
            11,
        );
        let scalar = trace_batched_walk(
            &group,
            inst.generator,
            target,
            inst.r,
            target_seed,
            512,
            false,
            RestartPool::Lazy,
            11,
        );
        let eager = trace_batched_walk(
            &group,
            inst.generator,
            target,
            inst.r,
            target_seed,
            512,
            true,
            RestartPool::Eager,
            11,
        );
        let vector = trace_batched_walk_vector(
            &group,
            inst.generator,
            target,
            inst.r,
            target_seed,
            512,
            RestartPool::Lazy,
            11,
        );
        let inverse_vector = trace_batched_walk_vector_inverse(
            &group,
            inst.generator,
            target,
            inst.r,
            target_seed,
            512,
            RestartPool::Lazy,
            11,
        );
        assert_eq!(native.frames, inverse_vector.frames);
        assert_eq!(native.group_ops, inverse_vector.group_ops);
        assert_eq!(native.frames, vector.frames);
        assert_eq!(native.group_ops, vector.group_ops);
        assert_eq!(native.frames, scalar.frames);
        assert_eq!(native.frames, eager.frames);
        assert_eq!(native.group_ops, scalar.group_ops);
        for frame in &native.frames {
            let mut ops = GroupOps::default();
            let ag = group.mul(&mut ops, inst.generator, frame.a);
            let bq = group.mul(&mut ops, target, frame.b);
            assert_eq!(frame.point, group.add(&mut ops, ag, bq));
        }
        let frames: Vec<_> = native.frames.iter().map(|f|json!({"infinity":f.point.infinity,"x":f.point.x,"y":f.point.y,"a":f.a,"b":f.b,"lane":f.lane,"identity":f.identity,"repeated":f.repeated,"forced_restart":f.forced_restart})).collect();
        println!(
            "{}",
            json!({"status":"pass","curve_id":inst.name,"fixture":fixture,"target":[target.x,target.y],"planted":planted,"target_seed":target_seed,"checks":frames.len(),"complete_stream_comparisons":4,"inverse_vector_counters":inverse_vector.counters,"forced_restart_every":11,"vector_counters":vector.counters,"native_counters":native.counters,"scalar_counters":scalar.counters,"group_ops":native.group_ops,"has_clmul":inst.gf.has_clmul(),"frames":frames})
        );
        return;
    }
    if matches!(mode, "rho-plain" | "rho-negation") {
        let reference_started = Instant::now();
        let result = if mode == "rho-plain" {
            rho_reference(
                &group,
                inst.generator,
                target,
                inst.r,
                target_seed,
                2_000_000,
            )
        } else {
            rho_reference_negation(
                &group,
                inst.generator,
                target,
                inst.r,
                target_seed,
                2_000_000,
            )
        };
        let reference_compute_through_cleanup_ns = reference_started.elapsed().as_nanos() as u64;
        println!(
            "{}",
            json!({"curve_id":inst.name,"fixture":fixture,"planted":planted,"target":[target.x,target.y],"target_seed":target_seed,"context_ns":context_ns,"calibration_ns":calibration_ns,"calibration":calibration,"reference_compute_through_cleanup_ns":reference_compute_through_cleanup_ns,"solver":result,"rho_kind":mode,"euclidean_inverse":inst.gf.uses_euclidean_inverse()})
        );
        return;
    }
    if mode == "rho" {
        let plain = rho_reference(
            &group,
            inst.generator,
            target,
            inst.r,
            target_seed,
            2_000_000,
        );
        let negation = rho_reference_negation(
            &group,
            inst.generator,
            target,
            inst.r,
            target_seed,
            2_000_000,
        );
        println!(
            "{}",
            json!({"curve_id":inst.name,"fixture":fixture,"planted":planted,"target":[target.x,target.y],
            "target_seed":target_seed,"context_ns":context_ns,"calibration_ns":calibration_ns,
            "calibration":calibration,"plain":plain,"matched":negation})
        );
        return;
    }
    assert!(matches!(
        mode,
        "mitm"
            | "mitm-native"
            | "mitm-batched"
            | "mitm-xonly"
            | "mitm-prefix"
            | "mitm-scalar"
            | "mitm-auto"
            | "affine"
            | "affine-cached"
            | "affine-columns"
    ));
    let mut spec = PipelineSpec {
        factor_base: "binary-subspace".into(),
        oracle: match mode {
            "mitm" | "mitm-native" => "mitm",
            "mitm-batched" | "mitm-xonly" | "mitm-prefix" | "mitm-scalar" | "mitm-auto" => {
                "mitm-batched"
            }
            _ => "affine-s3",
        }
        .into(),
        targets: match requested_mode {
            "mitm-walk16-native" => Targets::WalkBatch,
            "mitm-walk16-vector-inverse" => Targets::WalkBatchVectorInverse,
            "mitm-walk16-vector" | "mitm-walk16-vector-const" | "mitm-walk16-vector-narrow" => {
                Targets::WalkBatchVector
            }
            "mitm-walk16-scalar" => Targets::WalkBatchScalar,
            _ => Targets::Walk,
        },
        max_trials: record.get("max_trials").map(integer).unwrap_or(50_000),
        seed: target_seed,
        linalg: if matches!(requested_mode, "mitm-prefix-u32" | "mitm-euclid-u32") {
            "incremental-gauss-u32".into()
        } else {
            "incremental-gauss".into()
        },
        ..Default::default()
    };
    spec.factor_base_params
        .set("dimension", dimension.to_string());
    spec.oracle_params.set(
        "batch_size",
        match requested_mode {
            "mitm-walk-incumbent"
            | "mitm-walk16-scalar"
            | "mitm-walk16-native"
            | "mitm-walk16-vector"
            | "mitm-walk16-vector-const"
            | "mitm-walk16-vector-narrow"
            | "mitm-walk16-vector-inverse" => {
                if inst.n <= 21 {
                    "64"
                } else {
                    "1024"
                }
            }
            "mitm-vector64" | "mitm-prefix64" | "mitm-vector-packed64" => "64",
            "mitm-vector4096" => "4096",
            _ => "1024",
        },
    );
    spec.oracle_params.set("m", "2");
    spec.oracle_params.set(
        "vector_prepare",
        if matches!(
            requested_mode,
            "mitm-walk16-vector-const" | "mitm-walk16-vector-inverse"
        ) {
            "3"
        } else if requested_mode == "mitm-walk16-vector-narrow" {
            "4"
        } else if matches!(
            requested_mode,
            "mitm-vector"
                | "mitm-vector64"
                | "mitm-vector4096"
                | "mitm-walk-incumbent"
                | "mitm-walk16-scalar"
                | "mitm-walk16-native"
                | "mitm-walk16-vector"
                | "mitm-walk16-vector-const"
                | "mitm-walk16-vector-narrow"
        ) {
            "1"
        } else if matches!(
            requested_mode,
            "mitm-vector-packed" | "mitm-vector-packed64"
        ) {
            "2"
        } else {
            "0"
        },
    );
    spec.oracle_params.set("negation_folded", "1");
    spec.oracle_params.set("max_residual", "12");
    spec.oracle_params.set(
        "inverse_cache",
        if matches!(mode, "affine-cached" | "affine-columns") {
            "1"
        } else {
            "0"
        },
    );
    spec.oracle_params.set(
        "column_solver",
        if mode == "affine-columns" { "1" } else { "0" },
    );
    spec.oracle_params.set(
        "x_only",
        if matches!(mode, "mitm-xonly" | "mitm-prefix") {
            "1"
        } else {
            "0"
        },
    );
    spec.oracle_params.set(
        "prefix_inverse_cache",
        if mode == "mitm-prefix" { "1" } else { "0" },
    );
    spec.oracle_params.set(
        "native_setup_pricing",
        if mode == "mitm-native" { "1" } else { "0" },
    );
    spec.oracle_params.set(
        "scalar_prepare",
        if mode == "mitm-scalar" { "1" } else { "0" },
    );
    spec.oracle_params.set(
        "adaptive_prepare",
        if mode == "mitm-auto" { "1" } else { "0" },
    );
    let mut oracle: Box<dyn DecompositionOracle<BinaryGroup<'_>> + '_> =
        if matches!(mode, "mitm" | "mitm-native") {
            Box::new(MitmOracle::new(2))
        } else if matches!(
            mode,
            "mitm-batched" | "mitm-xonly" | "mitm-prefix" | "mitm-scalar" | "mitm-auto"
        ) {
            Box::new(BinaryBatchMitmOracle::default())
        } else {
            Box::new(AffineS3Oracle::new(&inst))
        };
    let computation_started = Instant::now();
    let report = run_pipeline(
        &ctx,
        &spec,
        &BinarySubspaceBase { instance: &inst },
        oracle.as_mut(),
        planted,
        &calibration,
        None,
    );
    drop(oracle);
    let computation_through_cleanup_ns = computation_started.elapsed().as_nanos() as u64;
    println!(
        "{}",
        json!({"curve_id":inst.name,"fixture":fixture,"planted":planted,"target":[target.x,target.y],
        "target_seed":target_seed,"context_ns":context_ns,"calibration_ns":calibration_ns,"computation_through_cleanup_ns":computation_through_cleanup_ns,
        "calibration":calibration,"mode":requested_mode,"euclidean_inverse":inst.gf.uses_euclidean_inverse(),"report":report})
    );
}
