use super::*;
use chained_quadratic_picard_engine as ext;
use ghs_original_engines::pic as prime;
use std::collections::HashSet;

fn converted(x: &prime::PicClass) -> ext::PicClass {
    match x {
        prime::PicClass::Exc(p) => ext::PicClass::Exc(*p),
        prime::PicClass::Typ(m) => ext::PicClass::Typ(*m),
    }
}
fn ere(p: u32, x: u32) -> ER {
    let mut a = [0; 16];
    a[0] = (x % p) as u64;
    a[1] = (x / p) as u64;
    a
}
fn encoded(p: u32, a: ER) -> u32 {
    assert!(a[2..].iter().all(|&x| x == 0));
    a[0] as u32 + p * a[1] as u32
}
fn base_cases() -> Vec<(u32, [u32; 15], u64)> {
    let raw:Value=serde_json::from_str(include_str!("../../../../../crypto/research/chained_jacobian_transfers_20261110/evidence/genus3-primary-01/cases.json")).unwrap();
    raw["cases"]
        .as_array()
        .unwrap()
        .iter()
        .map(|row| {
            let p = row["q"].as_u64().unwrap() as u32;
            let mut f = [0; 15];
            let mon = prime::mons_of_degree(4);
            for t in row["quartic_Fq"].as_array().unwrap() {
                let e = (
                    t[0].as_u64().unwrap() as u8,
                    t[1].as_u64().unwrap() as u8,
                    t[2].as_u64().unwrap() as u8,
                );
                let pos = mon.iter().position(|x| *x == e).unwrap();
                f[pos] = t[3].as_u64().unwrap() as u32;
            }
            (p, f, row["order_E0"].as_u64().unwrap())
        })
        .collect()
}
#[test]
fn genuine_quadratic_fields_and_complete_picard_scalar_extension_controls() {
    let c = chained_n4_public_target::CheckedInstance::construct().unwrap();
    let mut cases = base_cases();
    cases.push((223, c.inst.f, c.inst.order as u64));
    let mut reports = vec![];
    for (p, f, written_order) in cases {
        let nu = match p {
            5 | 11 => 2,
            7 | 223 => 3,
            _ => unreachable!(),
        };
        let p0 = prime::first_rational_point_canonical(p, &f).unwrap();
        let old = prime::PlaneQuartic::new(p, f, p0).unwrap();
        let copied = ext::PlaneQuartic::new(p, f, p0).unwrap();
        let quadratic = ext::PlaneQuartic::base_change_quadratic(p, nu, f, p0).unwrap();
        assert_eq!(quadratic.q(), p * p);
        assert_eq!(quadratic.coefficients(), &f);
        assert_eq!(quadratic.base_point(), p0);
        assert!(ext::PlaneQuartic::base_change_quadratic(p, 1, f, p0).is_err());
        assert!(ext::PlaneQuartic::base_change_quadratic(p, 0, f, p0).is_err());
        assert!(ext::PlaneQuartic::base_change_quadratic(p, p, f, p0).is_err());
        assert!(ext::PlaneQuartic::new(p * p, f, p0).is_err());
        assert!(prime::PlaneQuartic::new(p * p, f, p0).is_err());
        let oracle = FpR::from_modulus(p as u64, &[(p - nu) as u64, 0, 1]);
        let q2 = p * p;
        assert_eq!(
            quadratic.coefficient_mul(p, p),
            nu,
            "encoded v squares to nu in true field"
        );
        assert_eq!(
            quadratic.coefficient_add(p - 1, 1),
            0,
            "prime characteristic, no base-p carry"
        );
        assert_eq!(
            (p as u64 * p as u64) % (q2 as u64),
            0,
            "wrong integer-ring mutation squares encoded v to0"
        );
        for a in 0..q2 {
            let ar = ere(p, a);
            assert_eq!(
                quadratic.coefficient_frobenius(a),
                encoded(p, oracle.frobenius(ar))
            );
            if a != 0 {
                let inv = quadratic.coefficient_inv(a);
                assert_eq!(inv, encoded(p, oracle.inv(ar)));
                assert_eq!(quadratic.coefficient_mul(a, inv), 1);
            }
        }
        let pairs = if p == 223 { 1024 } else { q2 * q2 };
        for i in 0..pairs {
            let (a, b) = if p == 223 {
                ((i * 47 + 11) % q2, (i * 251 + 223) % q2)
            } else {
                (i / q2, i % q2)
            };
            assert_eq!(
                quadratic.coefficient_add(a, b),
                encoded(p, oracle.add(ere(p, a), ere(p, b)))
            );
            assert_eq!(
                quadratic.coefficient_sub(a, b),
                encoded(p, oracle.sub(ere(p, a), ere(p, b)))
            );
            assert_eq!(
                quadratic.coefficient_mul(a, b),
                encoded(p, oracle.mul(ere(p, a), ere(p, b)))
            );
        }
        let old_points = old.rational_points_bruteforce();
        let mut base_classes = vec![old.zero()];
        let mut keys = HashSet::new();
        keys.insert(old.zero().key());
        let generators: Vec<_> = old_points.iter().map(|&x| old.point_class(x)).collect();
        let mut edges = 0;
        let mut cursor = 0;
        if p < 223 {
            while cursor < base_classes.len() {
                let x = base_classes[cursor].clone();
                for g in &generators {
                    let y = old.add(&x, g);
                    assert_eq!(copied.add(&converted(&x), &converted(g)).key().0, y.key().0);
                    assert_eq!(
                        quadratic.add(&converted(&x), &converted(g)).key().0,
                        y.key().0
                    );
                    edges += 1;
                    if keys.insert(y.key()) {
                        base_classes.push(y);
                    }
                    assert!(base_classes.len() <= written_order as usize);
                }
                cursor += 1;
            }
        } else {
            base_classes.extend(generators.iter().take(16).cloned());
            for x in &base_classes {
                for y in &base_classes {
                    let z = old.add(x, y);
                    assert_eq!(copied.add(&converted(x), &converted(y)).key().0, z.key().0);
                    assert_eq!(
                        quadratic.add(&converted(x), &converted(y)).key().0,
                        z.key().0
                    );
                    edges += 1;
                }
            }
        }
        for x in &base_classes {
            assert_eq!(quadratic.neg(&converted(x)).key().0, old.neg(x).key().0);
            assert_eq!(quadratic.frobenius_class(&converted(x)), converted(x));
        }
        let mut nonbase_points = vec![];
        let mut class_samples = vec![];
        let mut frobenius_pairs = 0;
        let mut associativity = 0;
        if p < 223 {
            let all = quadratic.rational_points_bruteforce();
            let independent_count = (0..q2)
                .flat_map(|x| (0..q2).map(move |y| [1, x, y]))
                .chain((0..q2).map(|y| [0, 1, y]))
                .chain(std::iter::once([0, 0, 1]))
                .filter(|pt| {
                    let mut sum = oracle.zero();
                    for (i, (a, b, d)) in prime::mons_of_degree(4).iter().copied().enumerate() {
                        let t = oracle.mul(
                            oracle.mul(
                                oracle.pow(ere(p, pt[0]), a as u128),
                                oracle.pow(ere(p, pt[1]), b as u128),
                            ),
                            oracle.pow(ere(p, pt[2]), d as u128),
                        );
                        sum = oracle.add(sum, oracle.mul(oracle.from_u64(f[i] as u64), t));
                    }
                    oracle.is_zero(sum)
                })
                .count();
            assert_eq!(all.len(), independent_count);
            nonbase_points = all
                .into_iter()
                .filter(|pt| pt.iter().any(|&a| a >= p))
                .collect();
            assert!(!nonbase_points.is_empty());
            class_samples.push(quadratic.zero());
            for pt in nonbase_points.iter().take(7) {
                let x = quadratic.point_class(*pt);
                let fp = pt.map(|a| quadratic.coefficient_frobenius(a));
                assert_eq!(quadratic.frobenius_class(&x), quadratic.point_class(fp));
                class_samples.push(x);
            }
            let zero = quadratic.zero();
            for x in &class_samples {
                assert_eq!(quadratic.add(x, &zero), *x);
                assert_eq!(quadratic.sub(x, x), zero);
                assert_eq!(quadratic.add(x, &quadratic.neg(x)), zero);
                assert_eq!(quadratic.frobenius_class(&quadratic.frobenius_class(x)), *x);
            }
            for x in &class_samples {
                for y in &class_samples {
                    let sum = quadratic.add(x, y);
                    assert_eq!(sum, quadratic.add(y, x));
                    assert_eq!(
                        quadratic.frobenius_class(&sum),
                        quadratic.add(&quadratic.frobenius_class(x), &quadratic.frobenius_class(y))
                    );
                    frobenius_pairs += 1;
                    for z in &class_samples {
                        assert_eq!(
                            quadratic.add(&sum, z),
                            quadratic.add(x, &quadratic.add(y, z))
                        );
                        associativity += 1;
                    }
                }
            }
        }
        reports.push(json!({"p":p,"nu":nu,"field_size":q2,"actual_quartic":f,"P0":p0,"all_nonzero_inverses_and_all_field_Frobenius_checked":q2-1,"oracle_pairs":pairs,"all_prime_curve_points":old_points,"prime_generated_classes":base_classes.len(),"written_J_order":written_order,"prime_closure_complete":p<223&&base_classes.len()==written_order as usize,"all_prime_generation_or_sample_edges":edges,"nonbase_curve_points":nonbase_points,"nonbase_class_keys":class_samples.iter().map(|x|x.key().0.to_vec()).collect::<Vec<_>>(),"all_sample_Frobenius_pairs":frobenius_pairs,"all_sample_associativity_triples":associativity,"original_and_derived_prime_constructor_reject_p_squared":true,"square_zero_noncanonical_nu_rejected":true,"integer_mod_p_squared_mutation_differs":true}));
    }
    println!(
        "N4_BETA_QUADRATIC_PICARD {}",
        json!({"fields":reports,"scope":"actual quadratic field and Picard scalar-extension correctness controls; prime closure scope reported, general geometry conditional; not fullbeta or cost"})
    );
}
