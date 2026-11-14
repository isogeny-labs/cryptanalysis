use super::*;

fn request(c: &CheckedInstance, targets: Vec<EncodedTarget>) -> Vec<u8> {
    serde_json::to_vec(&Request {
        schema: "chained-n4-public-target/v1".into(),
        q: 223,
        targets,
    })
    .unwrap()
}

#[test]
fn original_and_independent_field_model_subgroup_certificate() {
    let c = CheckedInstance::construct().unwrap();
    let mut rng = common::Rng::new(0x5731);
    let f = &c.independent_field;
    for _ in 0..64 {
        let a = c.inst.kf.rand(&mut rng);
        let b = c.inst.kf.rand(&mut rng);
        assert_eq!(er(c.inst.kf.mul(&a, &b)), f.mul(er(a), er(b)));
        assert_eq!(er(c.inst.kf.frob(&a)), f.pow(er(a), 223));
    }
    for k in [0, 1, 2, 17, c.inst.ell - 1, c.inst.ell] {
        let q = c.inst.ec.mul(&c.inst.g, k as u128);
        assert!(c.verify_recovered(q, k % c.inst.ell));
    }
    println!("N4_PUBLIC_IDENTITY {}", c.description());
}

#[test]
fn all_five_public_targets_and_literal_original_algorithm_controls() {
    let c = CheckedInstance::construct().unwrap();
    let witnesses = [1, 2, 17, c.inst.ell / 2, c.inst.ell - 1];
    let targets: Vec<_> = witnesses
        .iter()
        .map(|&k| c.inst.ec.mul(&c.inst.g, k as u128))
        .collect();
    // The witness stays in this harness. Actual public parsing receives only Q.
    let input = request(&c, targets.iter().map(|&p| c.encode(p)).collect());
    let public_targets = c.parse(&input).unwrap();
    assert_eq!(public_targets, targets);
    let mut successes = 0;
    for (index, (&target, &witness)) in public_targets.iter().zip(&witnesses).enumerate() {
        let mut cparam = 2.0;
        let mut accepted = false;
        for attempt in 1..=6 {
            let p = frozen_params(cparam);
            let lp = legacy_solver::Params {
                nfb: p.nfb,
                rows_mult: p.rows_mult,
                max_desc: p.max_desc,
                sge: p.sge,
                maxw: p.maxw,
                lp2: p.lp2,
            };
            let old = legacy_solver::ic_solve(&c.inst, &lp, witness, 100 + attempt, true);
            let new = public_solver::ic_solve_target(&c.inst, &p, target, 100 + attempt, true);
            let original_verified = old.k_found.is_some_and(|k| c.verify_recovered(target, k));
            let public_verified = new.k_found.is_some_and(|k| c.verify_recovered(target, k));
            println!(
                "N4_PUBLIC_ATTEMPT {}",
                json!({"target_index":index,"attempt":attempt,
                "c":cparam,"nfb":p.nfb,"public_request":c.encode(target),
                "legacy":{"ok":old.ok,"fail":old.fail,"k_found":old.k_found,"independent_check":original_verified},
                "public":report_json(&new),"independent_public_check":public_verified,
                "scope":"paired original/public algorithm control;witness not public input;no cost ratio"})
            );
            if old.ok {
                assert!(
                    original_verified,
                    "legacy success rejected by original independent engine"
                );
            }
            if new.ok {
                assert!(
                    public_verified,
                    "public success rejected by original independent engine"
                );
            }
            if new.ok && public_verified {
                assert_eq!(new.k_found, Some(witness));
                accepted = true;
                break;
            }
            cparam += 0.4;
        }
        if accepted {
            successes += 1;
        }
    }
    println!(
        "N4_PUBLIC_FIVE {}",
        json!({"required":5,"public_IC_successes":successes,
        "all_retries_retained":true,"known_witness_not_solver_input":true})
    );
    assert_eq!(
        successes, 5,
        "frozen five-target public IC smoke is incomplete"
    );
}

#[test]
fn strict_public_schema_coordinates_and_actual_subgroup_controls() {
    let c = CheckedInstance::construct().unwrap();
    let valid = request(&c, vec![c.encode(c.inst.g)]);
    let mut scalar: Value = serde_json::from_slice(&valid).unwrap();
    scalar["scalar"] = json!(1);
    assert!(c.parse(&serde_json::to_vec(&scalar).unwrap()).is_err());
    let mut witness: Value = serde_json::from_slice(&valid).unwrap();
    witness["targets"][0]["witness"] = json!(1);
    assert!(c.parse(&serde_json::to_vec(&witness).unwrap()).is_err());
    for tag in ["field", "model"] {
        let mut v: Value = serde_json::from_slice(&valid).unwrap();
        v["targets"][0][tag] = json!("wrong");
        assert!(c.parse(&serde_json::to_vec(&v).unwrap()).is_err());
    }
    let mut bad = c.encode(c.inst.g);
    bad.coordinates = Some([[223, 0, 0], [0, 0, 0]]);
    assert!(c.parse(&request(&c, vec![bad])).is_err());
    let mut off = c.encode(c.inst.g);
    if let EP::A(x, y) = c.inst.g {
        let bad = (1..223)
            .map(|d| {
                let mut z = y;
                z[0] = (z[0] + d) % 223;
                EP::A(x, z)
            })
            .find(|p| !c.inst.ec.on(p))
            .expect("actual offcurve control");
        off = c.encode(bad);
    }
    assert!(c.parse(&request(&c, vec![off])).is_err());
    assert!(c.parse(&request(&c, vec![])).is_err());
    assert!(c.parse(&request(&c, vec![c.encode(c.inst.g); 6])).is_err());
    assert!(c.parse(&vec![b' '; 65537]).is_err());
    let mut wrongq: Value = serde_json::from_slice(&valid).unwrap();
    wrongq["q"] = json!(7);
    assert!(c.parse(&serde_json::to_vec(&wrongq).unwrap()).is_err());
    let mut schema: Value = serde_json::from_slice(&valid).unwrap();
    schema["schema"] = json!("unknown");
    assert!(c.parse(&serde_json::to_vec(&schema).unwrap()).is_err());
    let mut rng = common::Rng::new(0x5732);
    let nonmember = (0..64)
        .map(|_| c.inst.ec.rand_point(&mut rng))
        .find(|p| c.inst.ec.mul(p, c.inst.ell as u128) != EP::Inf)
        .expect("actual nonmember control");
    assert!(c.parse(&request(&c, vec![c.encode(nonmember)])).is_err());
    assert!(std::panic::catch_unwind(|| common::Kf::new(5)).is_err());
    assert!(std::panic::catch_unwind(|| common::Kf::new(11)).is_err());
    println!(
        "N4_PUBLIC_ADMISSION {}",
        json!({"unknown_scalar":true,"unknown_witness":true,
        "wrong_tags":2,"noncanonical":true,"offcurve":true,"foreign_q":true,"schema":true,
        "empty_and_six_targets":true,"over65536":true,"actual_nonmember":encode_point(nonmember),
        "original_q5_q11_constructor_panics_observed":true})
    );
}
