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
    let mode = args[3].as_str();
    let record = &records[index];
    let started = Instant::now();
    let inst = instance(record);
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
    if mode == "verify-xonly" {
        let basis: Vec<_> = (0..dimension).map(|i| 1 << i).collect();
        let fb = binary_subspace_factor_base(&inst, &basis);
        let reference = PairTable::build_negation_folded(&group, &fb);
        let mut checked = 0u64;
        for chunk in [1, 7, 1024] {
            let batch =
                PairTable::build_negation_folded_binary_abscissae(&inst.fast, &fb, chunk).unwrap();
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
    let calibration = if mode == "workload" {
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
        "mitm" | "mitm-batched" | "mitm-xonly" | "affine" | "affine-cached" | "affine-columns"
    ));
    let mut spec = PipelineSpec {
        factor_base: "binary-subspace".into(),
        oracle: match mode {
            "mitm" => "mitm",
            "mitm-batched" | "mitm-xonly" => "mitm-batched",
            _ => "affine-s3",
        }
        .into(),
        targets: Targets::Walk,
        max_trials: 50_000,
        seed: target_seed,
        ..Default::default()
    };
    spec.factor_base_params
        .set("dimension", dimension.to_string());
    spec.oracle_params.set("m", "2");
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
    spec.oracle_params
        .set("x_only", if mode == "mitm-xonly" { "1" } else { "0" });
    let mut oracle: Box<dyn DecompositionOracle<BinaryGroup<'_>> + '_> = if mode == "mitm" {
        Box::new(MitmOracle::new(2))
    } else if matches!(mode, "mitm-batched" | "mitm-xonly") {
        Box::new(BinaryBatchMitmOracle::default())
    } else {
        Box::new(AffineS3Oracle::new(&inst))
    };
    let report = run_pipeline(
        &ctx,
        &spec,
        &BinarySubspaceBase { instance: &inst },
        oracle.as_mut(),
        planted,
        &calibration,
        None,
    );
    println!(
        "{}",
        json!({"curve_id":inst.name,"fixture":fixture,"planted":planted,"target":[target.x,target.y],
        "target_seed":target_seed,"context_ns":context_ns,"calibration_ns":calibration_ns,
        "calibration":calibration,"mode":mode,"report":report})
    );
}
