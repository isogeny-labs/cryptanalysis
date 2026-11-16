use cryptanalysis_suite::binary_ecc::{BinaryCurve, BinaryPoint, IrreduciblePoly};
use cryptanalysis_suite::cryptanalysis::ic_boundary::{
    binary_subspace_factor_base, ArtinSchreier, BinaryGroup, BinaryInstance, GroupOps,
    OracleCounters,
};
use cryptanalysis_suite::cryptanalysis::ic_framework::affine::AffineS3Oracle;
use cryptanalysis_suite::cryptanalysis::ic_framework::stages::{
    DecompositionOracle, InstanceCtx, Params,
};
use cryptanalysis_suite::cryptanalysis::koblitz_fast::{FastCurve, FastPoint};
use cryptanalysis_suite::cryptanalysis::semaev_decomp::Gf2;
use num_bigint::BigUint;
use serde_json::Value;
use std::collections::HashSet;
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

#[test]
fn complete_registered_curve_domains_match_signed_pair_enumeration() {
    let records: Vec<Value> = serde_json::from_str(include_str!(
        "../../experiments/ic-affine-native-20261115/instances.json"
    ))
    .unwrap();
    for record in records {
        let inst = instance(&record);
        let group = BinaryGroup(&inst.fast);
        let dimension = integer(&record["dimension"]);
        let basis: Vec<u64> = (0..dimension).map(|i| 1 << i).collect();
        let fb = binary_subspace_factor_base(&inst, &basis);
        let expected: HashSet<u64> = fb
            .points
            .iter()
            .flat_map(|&p| fb.points.iter().map(move |&q| (p, q)))
            .map(|(p, q)| inst.fast.add(p, q).pack())
            .collect();
        let ctx = InstanceCtx {
            group: &group,
            generator: inst.generator,
            target: inst.generator,
            r: inst.r,
            cofactor: inst.cofactor,
            group_order: inst.group_order,
            name: inst.name.clone(),
            field_degree: Some(inst.n),
        };
        for (cache, columns) in [(0, 0), (1, 0), (0, 1), (1, 1)] {
            let mut params = Params::default();
            params.set("inverse_cache", cache.to_string());
            params.set("column_solver", columns.to_string());
            let mut oracle = AffineS3Oracle::new(&inst);
            oracle
                .prepare(&ctx, &fb, &params, &mut GroupOps::default())
                .unwrap();
            let mut checked = 0u64;
            let mut accepted = 0u64;
            let mut check = |target: FastPoint| {
                let got = oracle.decompose(
                    &ctx,
                    &fb,
                    &mut GroupOps::default(),
                    &mut OracleCounters::default(),
                    target,
                );
                assert_eq!(
                    got.is_some(),
                    expected.contains(&target.pack()),
                    "curve={} cache={cache} columns={columns} target={target:?}",
                    inst.name
                );
                if let Some(pair) = got {
                    assert_eq!(
                        inst.fast.add(fb.points[pair[0]], fb.points[pair[1]]),
                        target
                    );
                    accepted += 1;
                }
                checked += 1;
            };
            check(FastPoint::INFINITY);
            for x in 0..1u64 << inst.n {
                for p in inst.points_with_x(x) {
                    check(p);
                }
            }
            assert_eq!(checked, inst.group_order);
            assert_eq!(accepted, expected.len() as u64);
            eprintln!(
                "curve={} cache={cache} columns={columns} full_targets={checked} decomposable={accepted}",
                inst.name
            );
        }
    }
}

#[test]
fn batched_mitm_preserves_all_registered_curve_witnesses() {
    use cryptanalysis_suite::cryptanalysis::ic_boundary::PairTable;
    let records: Vec<Value> = serde_json::from_str(include_str!(
        "../../experiments/ic-affine-native-20261115/instances.json"
    ))
    .unwrap();
    for record in records {
        let inst = instance(&record);
        let group = BinaryGroup(&inst.fast);
        let basis: Vec<_> = (0..integer(&record["dimension"])).map(|i| 1 << i).collect();
        let fb = binary_subspace_factor_base(&inst, &basis);
        let reference = PairTable::build_negation_folded(&group, &fb);
        for chunk in [1, 7, 1024] {
            let batch =
                PairTable::build_negation_folded_binary_batched(&inst.fast, &fb, chunk).unwrap();
            assert_eq!(batch.entries, reference.entries);
            assert_eq!(batch.build_ops.adds, 0);
            assert!(batch
                .cost()
                .native
                .iter()
                .any(|&(k, _)| k == "mitm_batch_setup_ns"));
            let mut checked = 0u64;
            let mut check = |p| {
                let a = reference.probe(&group, &fb, &mut GroupOps::default(), &mut 0, p);
                let b = batch.probe(&group, &fb, &mut GroupOps::default(), &mut 0, p);
                assert_eq!(a, b, "{} chunk={chunk} target={p:?}", inst.name);
                checked += 1;
            };
            check(FastPoint::INFINITY);
            for x in 0..1u64 << inst.n {
                for p in inst.points_with_x(x) {
                    check(p);
                }
            }
            assert_eq!(checked, inst.group_order);
            eprintln!(
                "batch curve={} chunk={chunk} full_targets={checked}",
                inst.name
            );
        }
        assert!(PairTable::build_negation_folded_binary_batched(&inst.fast, &fb, 0).is_err());
        assert!(PairTable::build_negation_folded_binary_batched(&inst.fast, &fb, 65537).is_err());
    }
}
