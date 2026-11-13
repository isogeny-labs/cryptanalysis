use super::*;
use isogeny_algos::field::Rng;
use isogeny_algos::fpr::{FpR, ER};
use std::collections::HashSet;

fn lift(f: &FpR, p: &[u64]) -> Vec<ER> {
    p.iter().map(|&c| f.from_u64(c)).collect()
}
fn lift_point(f: &FpR, p: Pt<u64>) -> Pt<ER> {
    match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => Pt::Aff(f.from_u64(x), f.from_u64(y)),
    }
}
fn signed_multiple(f: &FpR, e: &Curve<ER>, p: &Pt<ER>, k: i64) -> Pt<ER> {
    let r = curve::pmul(f, e, p, k.unsigned_abs() as u128);
    if k < 0 {
        curve::neg(f, &r)
    } else {
        r
    }
}

// A genuinely different evaluation route: split the source finite support in
// F101² and sum its point images, retaining every duplicate root. Optional
// translation includes BOTH signed infinities and the reference divisor K.
fn pointwise_oracle(maps: &Maps, extension: &FpR, input: &Divisor, translation: Pair) -> Pair {
    let c = maps.model.coordinates(input).unwrap();
    let u = lift(extension, &c.u);
    let v = lift(extension, &c.v);
    let degree = c.u.len() - 1;
    let mut roots = if degree == 0 {
        Vec::new()
    } else {
        poly::roots(extension, &u, &mut Rng::new(0x5343))
    };
    if degree == 2 && roots.len() == 1 {
        roots.push(roots[0]);
    }
    assert_eq!(
        roots.len(),
        degree,
        "support must split completely in F101²"
    );
    for &z in &roots {
        assert!(roots.contains(&extension.frobenius(z)));
        let y = poly::eval(extension, &v, z);
        assert_eq!(
            extension.sq(y),
            poly::eval(extension, &lift(extension, &SOURCE), z)
        );
        assert_eq!(
            poly::eval(extension, &v, extension.frobenius(z)),
            extension.frobenius(y)
        );
    }
    std::array::from_fn(|i| {
        let t = &maps.fixture.targets[i];
        let e = Curve::new(extension.from_u64(t.a), extension.from_u64(t.b));
        let shift = lift_point(extension, translation[i]);
        let mut sum = Pt::Inf;
        for &z in &roots {
            let y = poly::eval(extension, &v, z);
            let q = poly::eval(extension, &lift(extension, &t.q), z);
            let n = poly::eval(extension, &lift(extension, &t.n), z);
            let point = if extension.is_zero(q) {
                assert!(!extension.is_zero(n));
                Pt::Inf
            } else {
                Pt::Aff(
                    extension.div(n, extension.sq(q)),
                    extension.div(
                        extension.mul(y, poly::eval(extension, &lift(extension, &t.m), z)),
                        extension.mul(extension.sq(q), q),
                    ),
                )
            };
            assert!(curve::on_curve(extension, &e, &point));
            sum = curve::padd(
                extension,
                &e,
                &sum,
                &curve::padd(extension, &e, &point, &shift),
            );
        }
        let positive = lift_point(extension, t.infinity_point());
        let negative = curve::neg(extension, &positive);
        let positive = curve::padd(extension, &e, &positive, &shift);
        let negative = curve::padd(extension, &e, &negative, &shift);
        sum = curve::padd(
            extension,
            &e,
            &sum,
            &signed_multiple(extension, &e, &positive, i64::from(c.plus) - 1),
        );
        sum = curve::padd(
            extension,
            &e,
            &sum,
            &signed_multiple(
                extension,
                &e,
                &negative,
                1 - degree as i64 - i64::from(c.plus),
            ),
        );
        match sum {
            Pt::Inf => Pt::Inf,
            Pt::Aff(x, y) => {
                assert_eq!(extension.frobenius(x), x);
                assert_eq!(extension.frobenius(y), y);
                Pt::Aff(extension.project(x).unwrap(), extension.project(y).unwrap())
            }
        }
    })
}

#[test]
fn complete_norm_pullback_group_recovery_and_dlp() {
    let maps = pinned().unwrap();
    let model = maps.model();
    let classes = model.classes().unwrap();
    assert_eq!(classes.len(), 12317);
    let extension = FpR::new(101, 2);
    let mut inputs = HashSet::new();
    let mut images = HashSet::new();
    let mut degrees = [0; 3];
    let mut repeated = 0;
    let mut nonsplit = 0;
    let mut poles = [0; 2];
    let mut values = Vec::with_capacity(classes.len());
    let generators: [Divisor; 2] = std::array::from_fn(|i| {
        maps.pull_component(i, &maps.target_points(i).unwrap()[1])
            .unwrap()
    });
    let generator_values: [Pair; 2] = std::array::from_fn(|i| maps.norm(&generators[i]).unwrap());
    assert_eq!(maps.norm(&model.identity()).unwrap(), [Pt::Inf; 2]);
    for (i, d) in classes.iter().enumerate() {
        let c = model.coordinates(d).unwrap();
        assert_eq!(model.from_coordinates(&c).unwrap(), *d);
        assert!(inputs.insert(c.clone()));
        degrees[c.u.len() - 1] += 1;
        repeated += usize::from(
            poly::gcd(maps.field(), &c.u, &poly::derivative(maps.field(), &c.u)).len() > 1,
        );
        if c.u.len() == 3 && poly::roots(maps.field(), &c.u, &mut Rng::new(0x5344)).is_empty() {
            nonsplit += 1;
        }
        for (j, t) in maps.fixture.targets.iter().enumerate() {
            poles[j] += usize::from(
                poly::gcd(maps.field(), &c.u, &poly::mul(maps.field(), &t.q, &t.q)).len() > 1,
            );
        }
        let value = maps.norm(d).unwrap();
        assert!(images.insert(value));
        assert_eq!(value, pointwise_oracle(&maps, &extension, d, [Pt::Inf; 2]));
        if i % 97 == 0 {
            let translation = std::array::from_fn(|j| maps.fixture.targets[j].infinity_point());
            assert_eq!(value, pointwise_oracle(&maps, &extension, d, translation));
        }
        let pulled = maps.pull(&value).unwrap();
        assert_eq!(pulled, model.mul(d, 4).unwrap());
        assert_eq!(maps.norm(&pulled).unwrap(), maps.scale_pair(&value, [4, 4]));
        assert_eq!(maps.recover(&value).unwrap(), *d);
        assert_eq!(maps.recover_components(&value).unwrap(), *d);
        let negative = model.neg(d).unwrap();
        assert_eq!(
            maps.norm(&negative).unwrap(),
            std::array::from_fn(|j| curve::neg(maps.field(), &value[j]))
        );
        assert_eq!(
            maps.norm(&model.add(d, d).unwrap()).unwrap(),
            maps.scale_pair(&value, [2, 2])
        );
        for j in 0..2 {
            assert_eq!(
                maps.norm(&model.add(d, &generators[j]).unwrap()).unwrap(),
                maps.add_pairs(&value, &generator_values[j])
            );
        }
        values.push(value);
    }
    for (i, d) in classes.iter().enumerate() {
        let j = (7919 * i + 104729) % classes.len();
        assert_eq!(
            maps.norm(&model.add(d, &classes[j]).unwrap()).unwrap(),
            maps.add_pairs(&values[i], &values[j])
        );
    }
    for i in 0..2 {
        let t = &maps.fixture.targets[i];
        let g = maps.target_points(i).unwrap()[1];
        let dg = maps.pull_component(i, &g).unwrap();
        assert_ne!(dg, model.identity());
        assert_eq!(model.mul(&dg, t.order).unwrap(), model.identity());
        let mut scalar_images = HashSet::new();
        for k in 0..t.order {
            let kg = curve::pmul(maps.field(), &t.curve(), &g, k as u128);
            let actual = maps.pull_component(i, &kg).unwrap();
            assert_eq!(actual, model.mul(&dg, k).unwrap());
            let mut expected = [Pt::Inf; 2];
            expected[i] = curve::pmul(maps.field(), &t.curve(), &kg, 4);
            assert_eq!(maps.norm(&actual).unwrap(), expected);
            assert!(scalar_images.insert(model.coordinates(&actual).unwrap()));
        }
        assert_eq!(scalar_images.len() as u64, t.order);
    }
    println!("PASS all12317 distinct balanced inputs/output pairs;F101 image-Mumford norm==F101² pointwise oracle;both actual[4],cross0,both public inverses9238/82/85,identity/negation/doubling/paired-additions/two-generator translations;all109+113scalarimages/exactorders,Frobenius;degrees={degrees:?},repeated={repeated},nonsplit={nonsplit},poles={poles:?};coherent translated-cover positive controls");
}

#[test]
fn complete_elliptic_fibres_multiplicity_and_domains() {
    let maps = pinned().unwrap();
    let mut all_strata = Vec::new();
    let mut repeats = [0; 2];
    let mut poles = [[0; 2]; 2];
    for i in 0..2 {
        let mut strata = [0; 5];
        let mut signs = [0; 2];
        for point in maps.target_points(i).unwrap() {
            let d = maps.pull_component(i, &point).unwrap();
            let mut expected = [Pt::Inf; 2];
            expected[i] = curve::pmul(maps.field(), &maps.fixture.targets[i].curve(), &point, 4);
            assert_eq!(maps.norm(&d).unwrap(), expected);
            match maps.fibre(i, &point).unwrap() {
                None => {
                    strata[0] += 1;
                    assert_eq!(d, maps.model.identity());
                }
                Some(fibre) => {
                    let degree = fibre.u.len() - 1;
                    strata[degree] += 1;
                    assert_eq!(degree + fibre.infinity_plus + fibre.infinity_minus, 4);
                    repeats[i] += usize::from(
                        poly::gcd(
                            maps.field(),
                            &fibre.u,
                            &poly::derivative(maps.field(), &fibre.u),
                        )
                        .len()
                            > 1,
                    );
                    for (j, t) in maps.fixture.targets.iter().enumerate() {
                        poles[i][j] +=
                            usize::from(poly::gcd(maps.field(), &fibre.u, &t.q).len() > 1);
                    }
                    if degree < 4 {
                        if fibre.infinity_plus > 0 {
                            signs[0] += 1;
                        } else {
                            signs[1] += 1;
                        }
                        assert_eq!(degree, if i == 0 { 2 } else { 3 });
                        assert_eq!(
                            fibre.infinity_plus + fibre.infinity_minus,
                            if i == 0 { 2 } else { 1 }
                        );
                        if i == 1 {
                            assert_eq!(&fibre.u[..2], &[0, 0]);
                        }
                    }
                }
            }
        }
        assert_eq!(signs, [1, 1]);
        assert_eq!(
            strata,
            if i == 0 {
                [1, 0, 2, 0, 106]
            } else {
                [1, 0, 0, 2, 110]
            }
        );
        all_strata.push(strata);
    }
    let malformed = [
        Coordinates {
            u: vec![],
            v: vec![],
            plus: 1,
        },
        Coordinates {
            u: vec![1, 0],
            v: vec![],
            plus: 1,
        },
        Coordinates {
            u: vec![1],
            v: vec![],
            plus: 3,
        },
        Coordinates {
            u: vec![101, 1],
            v: vec![],
            plus: 0,
        },
        Coordinates {
            u: vec![1, 2],
            v: vec![],
            plus: 0,
        },
        Coordinates {
            u: vec![1],
            v: vec![1],
            plus: 1,
        },
        Coordinates {
            u: vec![0, 1],
            v: vec![0],
            plus: 0,
        },
        Coordinates {
            u: vec![0, 1],
            v: vec![1],
            plus: 0,
        },
        Coordinates {
            u: vec![0, 0, 0, 1],
            v: vec![10],
            plus: 0,
        },
    ];
    for c in &malformed {
        assert!(maps.norm_coordinates(c).is_err(), "{c:?}");
    }
    assert!(maps.pull_component(2, &Pt::Inf).is_err());
    assert!(maps.pull_component(0, &Pt::Aff(101, 0)).is_err());
    assert!(maps.pull_component(0, &Pt::Aff(0, 0)).is_err());
    let oversized = vec![b' '; MAX_FIXTURE_BYTES + 1];
    assert!(Maps::load(&oversized).is_err());
    println!("PASS all109+113 complete rational elliptic fibres/O;strata={all_strata:?},repeated_fibres={repeats:?},finite_fibre_poles={poles:?};both infinity signs/drops with exact finite and infinite multiplicity;[4]/cross0;9 malformed balanced inputs,3 elliptic domain mutants,1MiB bound");
}

#[test]
fn sixteen_fixture_mutants_rejected() {
    let original: serde_json::Value =
        serde_json::from_slice(include_bytes!("../fixtures/t20-norms.json")).unwrap();
    let mut mutations = Vec::new();
    for (name, pointer, replacement) in [
        ("field", "/field", serde_json::json!(103)),
        ("source", "/monic_source/0", serde_json::json!(99)),
        ("source-range", "/raw_source/0", serde_json::json!(101)),
        ("target-a", "/targets/0/a", serde_json::json!(58)),
        ("target-b", "/targets/0/b", serde_json::json!(26)),
        ("order", "/targets/0/order", serde_json::json!(107)),
        ("q-constant", "/targets/0/q/0", serde_json::json!(39)),
        ("q-leading", "/targets/0/q/2", serde_json::json!(2)),
        ("n-constant", "/targets/0/n/0", serde_json::json!(54)),
        ("m-constant", "/targets/0/m/0", serde_json::json!(80)),
        (
            "omitted50",
            "/targets/0/m",
            serde_json::json!([44, 47, 55, 2]),
        ),
        ("infinity-y", "/targets/0/infinity/1", serde_json::json!(1)),
        ("infinity-x", "/targets/0/infinity/0", serde_json::json!(11)),
        (
            "overlong",
            "/targets/0/n",
            serde_json::json!([53, 52, 54, 0, 10, 1]),
        ),
        ("schema", "/schema", serde_json::json!("unbound")),
    ] {
        let mut value = original.clone();
        *value.pointer_mut(pointer).unwrap() = replacement;
        mutations.push((name, value));
    }
    let mut hidden = original.clone();
    hidden
        .as_object_mut()
        .unwrap()
        .insert("dlp_label".into(), serde_json::json!(1));
    mutations.push(("dlp-label", hidden));
    assert_eq!(mutations.len(), 16);
    for (name, value) in mutations {
        let bytes = serde_json::to_vec(&value).unwrap();
        let error = Maps::load(&bytes)
            .err()
            .unwrap_or_else(|| panic!("accepted mutant {name}"));
        println!("REJECT fixture mutant {name}: {error}");
    }
}

#[test]
fn wrong_recovery_sign_and_multiplicity_controls() {
    let maps = pinned().unwrap();
    let classes = maps.model.classes().unwrap();
    let mut wrong_half = [0; 2];
    let mut wrong_sign = [0; 2];
    for d in &classes {
        let pulled = maps.pull(&maps.norm(d).unwrap()).unwrap();
        let bad = maps.model.mul(&pulled, 6159).unwrap();
        wrong_half[usize::from(bad == *d)] += 1;
        let bad = maps
            .model
            .mul(&maps.model.neg(&pulled).unwrap(), 9238)
            .unwrap();
        wrong_sign[usize::from(bad == *d)] += 1;
    }
    assert_eq!(wrong_half, [12316, 1]);
    assert_eq!(wrong_sign, [12316, 1]);
    let mut infinity_controls = [0; 2];
    let mut repeated_controls = [0; 2];
    for i in 0..2 {
        let t = &maps.fixture.targets[i];
        for point in [
            t.infinity_point(),
            curve::neg(maps.field(), &t.infinity_point()),
        ] {
            let fibre = maps.fibre(i, &point).unwrap().unwrap();
            let correct = maps.pull_component(i, &point).unwrap();
            let wrong_plus = if fibre.infinity_plus > 0 { -1 } else { 0 };
            match maps.model.reduce_fibre(&fibre.u, &fibre.v, wrong_plus) {
                Err(_) => infinity_controls[0] += 1,
                Ok(bad) => {
                    assert_ne!(bad, correct);
                    infinity_controls[1] += 1;
                }
            }
            if i == 1 {
                let repeated = poly::gcd(
                    maps.field(),
                    &fibre.u,
                    &poly::derivative(maps.field(), &fibre.u),
                );
                assert!(repeated.len() > 1);
                let (squarefree, remainder) = poly::divrem(maps.field(), &fibre.u, &repeated);
                assert!(remainder.is_empty());
                let truncated_v = poly::rem(maps.field(), &fibre.v, &squarefree);
                match maps.model.reduce_fibre(
                    &squarefree,
                    &truncated_v,
                    fibre.infinity_plus as i64 - 1,
                ) {
                    Err(_) => repeated_controls[0] += 1,
                    Ok(bad) => {
                        assert_ne!(bad, correct);
                        assert_ne!(maps.norm(&bad).unwrap(), maps.norm(&correct).unwrap());
                        repeated_controls[1] += 1;
                    }
                }
            }
        }
    }
    assert_eq!(infinity_controls.iter().sum::<usize>(), 4);
    assert_eq!(repeated_controls.iter().sum::<usize>(), 2);
    assert!(balanced_source_engine::fibre_identity_mutant_rejected());
    println!("PASS wrong inverse2=6159 different/equal={wrong_half:?};wrong pullback sign={wrong_sign:?};infinity multiplicity reject/different={infinity_controls:?};squarefree repeated fibre reject/different={repeated_controls:?};universal identity RHS+1 rejected;coherent translations tested as positive controls in complete test");
}
