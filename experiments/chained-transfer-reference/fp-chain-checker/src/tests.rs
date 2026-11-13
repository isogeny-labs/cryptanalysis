use super::*;
use isogeny_algos::field::Rng;
use isogeny_algos::fpr::{FpR, ER};
use std::collections::HashSet;

fn lift(f: &FpR, p: &[u64]) -> Vec<ER> {
    p.iter().map(|&x| f.from_u64(x)).collect()
}
fn point_lift(f: &FpR, p: Pt<u64>) -> Pt<ER> {
    match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => Pt::Aff(f.from_u64(x), f.from_u64(y)),
    }
}
fn signed(f: &FpR, e: &Curve<ER>, p: &Pt<ER>, k: i64) -> Pt<ER> {
    let r = curve::pmul(f, e, p, k.unsigned_abs() as u128);
    if k < 0 {
        curve::neg(f, &r)
    } else {
        r
    }
}
fn oracle(maps: &Maps, f: &FpR, input: &Divisor, translation: Pair) -> Pair {
    let c = maps.source.coordinates(input).unwrap();
    let degree = c.u.len() - 1;
    let mut roots = if degree == 0 {
        vec![]
    } else {
        poly::roots(f, &lift(f, &c.u), &mut Rng::new(0x5401))
    };
    if degree == 2 && roots.len() == 1 {
        roots.push(roots[0]);
    }
    assert_eq!(roots.len(), degree);
    for &z in &roots {
        assert!(roots.contains(&f.frobenius(z)));
        let y = poly::eval(f, &lift(f, &c.v), z);
        assert_eq!(f.sq(y), poly::eval(f, &lift(f, &C0), z));
        assert_eq!(
            poly::eval(f, &lift(f, &c.v), f.frobenius(z)),
            f.frobenius(y)
        );
    }
    std::array::from_fn(|i| {
        let cover = &maps.fixture.covers[i];
        let e = Curve::new(f.from_u64(cover.a), f.from_u64(cover.b));
        let shift = point_lift(f, translation[i]);
        let mut sum = Pt::Inf;
        for &z in &roots {
            let q = poly::eval(f, &lift(f, &cover.q), z);
            let n = poly::eval(f, &lift(f, &cover.n), z);
            let y = poly::eval(f, &lift(f, &c.v), z);
            let point = if f.is_zero(q) {
                assert!(!f.is_zero(n));
                Pt::Inf
            } else {
                Pt::Aff(
                    f.div(n, f.sq(q)),
                    f.div(
                        f.mul(y, poly::eval(f, &lift(f, &cover.m), z)),
                        f.mul(f.sq(q), q),
                    ),
                )
            };
            assert!(curve::on_curve(f, &e, &point));
            sum = curve::padd(f, &e, &sum, &curve::padd(f, &e, &point, &shift));
        }
        let positive = point_lift(f, cover.infinity_point());
        let negative = curve::neg(f, &positive);
        sum = curve::padd(
            f,
            &e,
            &sum,
            &signed(
                f,
                &e,
                &curve::padd(f, &e, &positive, &shift),
                i64::from(c.plus) - 1,
            ),
        );
        sum = curve::padd(
            f,
            &e,
            &sum,
            &signed(
                f,
                &e,
                &curve::padd(f, &e, &negative, &shift),
                1 - degree as i64 - i64::from(c.plus),
            ),
        );
        match sum {
            Pt::Inf => Pt::Inf,
            Pt::Aff(x, y) => {
                assert_eq!(f.frobenius(x), x);
                assert_eq!(f.frobenius(y), y);
                Pt::Aff(f.project(x).unwrap(), f.project(y).unwrap())
            }
        }
    })
}
fn frobenius_coordinates(model: &Model, f: &FpR, d: &Divisor) {
    let c = model.coordinates(d).unwrap();
    let mut changed = c.clone();
    for x in changed.u.iter_mut().chain(&mut changed.v) {
        *x = f.project(f.frobenius(f.from_u64(*x))).unwrap();
    }
    assert_eq!(c, changed);
    assert_eq!(model.from_coordinates(&changed).unwrap(), *d);
}

#[test]
fn complete_c0_norm_oracle_group_and_public_inverse() {
    let maps = pinned().unwrap();
    let classes = maps.source.classes().unwrap();
    assert_eq!(classes.len(), 12317);
    let extension = FpR::new(101, 2);
    let mut inputs = HashSet::new();
    let mut outputs = HashSet::new();
    let mut values = Vec::new();
    let mut degrees = [0; 3];
    let mut repeated = 0;
    let mut nonsplit = 0;
    let mut zero = 0;
    let mut poles = [0; 2];
    let generators: [Divisor; 2] = std::array::from_fn(|i| {
        maps.source_pull_component(i, &maps.points(i).unwrap()[1])
            .unwrap()
    });
    let generator_values: [Pair; 2] =
        std::array::from_fn(|i| maps.source_norm(&generators[i]).unwrap());
    assert_eq!(
        maps.source_norm(&maps.source.identity()).unwrap(),
        [Pt::Inf; 2]
    );
    for (i, d) in classes.iter().enumerate() {
        let c = maps.source.coordinates(d).unwrap();
        assert!(inputs.insert(c.clone()));
        assert_eq!(maps.source.from_coordinates(&c).unwrap(), *d);
        degrees[c.u.len() - 1] += 1;
        repeated += usize::from(
            poly::gcd(&maps.field, &c.u, &poly::derivative(&maps.field, &c.u)).len() > 1,
        );
        nonsplit += usize::from(
            c.u.len() == 3 && poly::roots(&maps.field, &c.u, &mut Rng::new(0x5402)).is_empty(),
        );
        zero += usize::from(c.u.first() == Some(&0));
        for (j, cover) in maps.fixture.covers.iter().enumerate() {
            poles[j] += usize::from(
                poly::gcd(
                    &maps.field,
                    &c.u,
                    &poly::mul(&maps.field, &cover.q, &cover.q),
                )
                .len()
                    > 1,
            );
        }
        let value = maps.source_norm(d).unwrap();
        assert!(outputs.insert(value));
        assert_eq!(value, oracle(&maps, &extension, d, [Pt::Inf; 2]));
        if i % 97 == 0 {
            let translation = std::array::from_fn(|j| maps.points(j).unwrap()[1]);
            assert_eq!(value, oracle(&maps, &extension, d, translation));
        }
        let pulled = maps.source_pull(&value).unwrap();
        assert_eq!(pulled, maps.source.mul(d, 2).unwrap());
        assert_eq!(
            maps.source_norm(&pulled).unwrap(),
            maps.source_pair_scale(&value, [2, 2])
        );
        assert_eq!(maps.source_recover(&value).unwrap(), *d);
        assert_eq!(maps.source_recover_components(&value).unwrap(), *d);
        assert_eq!(
            maps.source_norm(&maps.source.neg(d).unwrap()).unwrap(),
            std::array::from_fn(|j| curve::neg(&maps.field, &value[j]))
        );
        assert_eq!(
            maps.source_norm(&maps.source.add(d, d).unwrap()).unwrap(),
            maps.source_pair_scale(&value, [2, 2])
        );
        for j in 0..2 {
            assert_eq!(
                maps.source_norm(&maps.source.add(d, &generators[j]).unwrap())
                    .unwrap(),
                maps.source_pair_add(&value, &generator_values[j])
            );
        }
        frobenius_coordinates(&maps.source, &extension, d);
        values.push(value);
    }
    for (i, d) in classes.iter().enumerate() {
        let j = (7919 * i + 104729) % classes.len();
        assert_eq!(
            maps.source_norm(&maps.source.add(d, &classes[j]).unwrap())
                .unwrap(),
            maps.source_pair_add(&values[i], &values[j])
        );
    }
    for i in 0..2 {
        let c = &maps.fixture.covers[i];
        let g = maps.points(i).unwrap()[1];
        let dg = maps.source_pull_component(i, &g).unwrap();
        assert_ne!(dg, maps.source.identity());
        assert_eq!(
            maps.source.mul(&dg, c.order).unwrap(),
            maps.source.identity()
        );
        let mut seen = HashSet::new();
        for k in 0..c.order {
            let kg = curve::pmul(&maps.field, &c.curve(), &g, k as u128);
            let d = maps.source_pull_component(i, &kg).unwrap();
            assert_eq!(d, maps.source.mul(&dg, k).unwrap());
            let mut expected = [Pt::Inf; 2];
            expected[i] = curve::pmul(&maps.field, &c.curve(), &kg, 2);
            assert_eq!(maps.source_norm(&d).unwrap(), expected);
            assert!(seen.insert(maps.source.coordinates(&d).unwrap()));
        }
        assert_eq!(seen.len() as u64, c.order);
    }
    println!("PASS C0 all12317 valid distinct classes/normpairs;FpimageMumford==independentFp2pointwiseoracle/bothactual2/cross0/bothpublicinverse6159and55,57/group/Frob/all109+113scalarimages/exactorders/coherenttranslatedcoverpositivecontrols;degrees={degrees:?}/repeated={repeated}/nonsplit={nonsplit}/zero={zero}/poles={poles:?}");
}

#[test]
fn complete_both_domain_chain_roundtrips_diagram_and_dlp() {
    let maps = pinned().unwrap();
    let c0 = maps.source.classes().unwrap();
    let t20 = maps.target().classes().unwrap();
    assert_eq!((c0.len(), t20.len()), (12317, 12317));
    let extension = FpR::new(101, 2);
    let mut forward_images = HashSet::new();
    let mut reverse_images = HashSet::new();
    let mut forward = Vec::new();
    let generators: [Divisor; 2] = std::array::from_fn(|i| {
        maps.source_pull_component(i, &maps.points(i).unwrap()[1])
            .unwrap()
    });
    let gen_forward: [Divisor; 2] = std::array::from_fn(|i| maps.forward(&generators[i]).unwrap());
    assert_eq!(
        maps.forward(&maps.source.identity()).unwrap(),
        maps.target().identity()
    );
    assert_eq!(
        maps.inverse(&maps.target().identity()).unwrap(),
        maps.source.identity()
    );
    for d in &c0 {
        let f = maps.forward(d).unwrap();
        assert!(forward_images.insert(maps.target().coordinates(&f).unwrap()));
        assert_eq!(maps.forward_alternative(d).unwrap(), f);
        assert_eq!(
            maps.t20.norm(&f).unwrap(),
            maps.chain_norm_image(d).unwrap()
        );
        assert_eq!(maps.inverse(&f).unwrap(), *d);
        assert_eq!(maps.inverse_alternative(&f).unwrap(), *d);
        assert_eq!(
            maps.forward(&maps.source.neg(d).unwrap()).unwrap(),
            maps.target().neg(&f).unwrap()
        );
        assert_eq!(
            maps.forward(&maps.source.add(d, d).unwrap()).unwrap(),
            maps.target().add(&f, &f).unwrap()
        );
        for j in 0..2 {
            assert_eq!(
                maps.forward(&maps.source.add(d, &generators[j]).unwrap())
                    .unwrap(),
                maps.target().add(&f, &gen_forward[j]).unwrap()
            );
        }
        frobenius_coordinates(maps.target(), &extension, &f);
        forward.push(f);
    }
    for (i, d) in c0.iter().enumerate() {
        let j = (7919 * i + 104729) % c0.len();
        assert_eq!(
            maps.forward(&maps.source.add(d, &c0[j]).unwrap()).unwrap(),
            maps.target().add(&forward[i], &forward[j]).unwrap()
        );
    }
    for t in &t20 {
        let g = maps.inverse(t).unwrap();
        assert!(reverse_images.insert(maps.source.coordinates(&g).unwrap()));
        assert_eq!(maps.inverse_alternative(t).unwrap(), g);
        assert_eq!(maps.forward(&g).unwrap(), *t);
        assert_eq!(maps.forward_alternative(&g).unwrap(), *t);
        frobenius_coordinates(&maps.source, &extension, &g);
        assert_eq!(
            maps.inverse(&maps.target().neg(t).unwrap()).unwrap(),
            maps.source.neg(&g).unwrap()
        );
        assert_eq!(
            maps.inverse(&maps.target().add(t, t).unwrap()).unwrap(),
            maps.source.add(&g, &g).unwrap()
        );
        for j in 0..2 {
            assert_eq!(
                maps.inverse(&maps.target().add(t, &gen_forward[j]).unwrap())
                    .unwrap(),
                maps.source.add(&g, &generators[j]).unwrap()
            );
        }
    }
    for (i, d) in t20.iter().enumerate() {
        let j = (7919 * i + 104729) % t20.len();
        assert_eq!(
            maps.inverse(&maps.target().add(d, &t20[j]).unwrap())
                .unwrap(),
            maps.source
                .add(&maps.inverse(d).unwrap(), &maps.inverse(&t20[j]).unwrap())
                .unwrap()
        );
    }
    for i in 0..2 {
        let order = maps.fixture.covers[i].order;
        let g = &generators[i];
        let image = &gen_forward[i];
        assert_ne!(*image, maps.target().identity());
        assert_eq!(
            maps.target().mul(image, order).unwrap(),
            maps.target().identity()
        );
        let mut seen = HashSet::new();
        for k in 0..order {
            let kg = maps.source.mul(g, k).unwrap();
            let actual = maps.forward(&kg).unwrap();
            assert_eq!(actual, maps.target().mul(image, k).unwrap());
            assert_eq!(maps.inverse(&actual).unwrap(), kg);
            assert!(seen.insert(maps.target().coordinates(&actual).unwrap()));
        }
        assert_eq!(seen.len() as u64, order);
    }
    println!("PASS complete12317C0 AND12317T20 independent domains/both inverse directions/distinctvalidFpimages/both public evaluation routes/actualnormdiagram/group/Frob/all109+113embeddedDLPscalars/exactorders;acceptedglobaldegree196chain comparison via SAME normdiagram+injectivity,written bridge not a newR20implementation/globalinverseisogeny/costclaim");
}

#[test]
fn all_c0_fibres_alpha_dual_and_domain_mutants() {
    let maps = pinned().unwrap();
    let mut observed = Vec::new();
    for i in 0..2 {
        let mut strata = [0; 3];
        let mut identity = 0;
        let mut repeated = 0;
        let mut infinities = [0; 2];
        for p in maps.points(i).unwrap() {
            let d = maps.source_pull_component(i, &p).unwrap();
            let mut expected = [Pt::Inf; 2];
            expected[i] = curve::pmul(&maps.field, &maps.fixture.covers[i].curve(), &p, 2);
            assert_eq!(maps.source_norm(&d).unwrap(), expected);
            match maps.fibre(i, &p).unwrap() {
                None => {
                    identity += 1;
                    assert_eq!(d, maps.source.identity());
                }
                Some(f) => {
                    let degree = f.u.len() - 1;
                    strata[degree] += 1;
                    assert_eq!(degree + f.infinity_plus + f.infinity_minus, 2);
                    repeated += usize::from(
                        poly::gcd(&maps.field, &f.u, &poly::derivative(&maps.field, &f.u)).len()
                            > 1,
                    );
                    infinities[0] += f.infinity_plus;
                    infinities[1] += f.infinity_minus;
                    if i == 0
                        && poly::gcd(&maps.field, &f.u, &poly::derivative(&maps.field, &f.u)).len()
                            > 1
                    {
                        assert_eq!(f.u, vec![0, 0, 1]);
                    }
                    if i == 1 && degree == 0 {
                        assert_eq!(f.u, vec![1]);
                        assert!(f.v.is_empty());
                        assert_eq!(
                            maps.source.coordinates(&d).unwrap().plus,
                            if f.infinity_plus == 2 { 2 } else { 0 }
                        );
                    }
                }
            }
        }
        assert_eq!(identity, 1);
        assert_eq!(strata, if i == 0 { [0, 0, 108] } else { [2, 0, 110] });
        assert_eq!(repeated, if i == 0 { 2 } else { 0 });
        assert_eq!(infinities, if i == 0 { [0, 0] } else { [2, 2] });
        observed.push((identity, strata, repeated, infinities));
    }
    let e0 = Curve::new(1, 46);
    let e2 = Curve::new(59, 27);
    for p in original_points::points(&maps.field, &e0) {
        assert_eq!(
            maps.alpha
                .reverse(&maps.alpha.forward(&p).unwrap())
                .unwrap(),
            curve::pmul(&maps.field, &e0, &p, 49)
        );
        assert_eq!(
            maps.alpha.first_roundtrip_control(&p).unwrap(),
            curve::pmul(&maps.field, &e0, &p, 7)
        );
    }
    for p in original_points::points(&maps.field, &e2) {
        assert_eq!(
            maps.alpha
                .forward(&maps.alpha.reverse(&p).unwrap())
                .unwrap(),
            curve::pmul(&maps.field, &e2, &p, 49)
        );
    }
    let original: serde_json::Value =
        serde_json::from_slice(include_bytes!("../fixtures/c0-t20.json")).unwrap();
    let mut mutants = Vec::new();
    for (name, path, value) in [
        ("field", "/field", serde_json::json!(103)),
        ("source", "/source/0", serde_json::json!(55)),
        ("source-range", "/source/0", serde_json::json!(101)),
        ("E0-a", "/covers/0/a", serde_json::json!(2)),
        ("E0-b", "/covers/0/b", serde_json::json!(45)),
        ("F0-a", "/covers/1/a", serde_json::json!(45)),
        ("F0-b", "/covers/1/b", serde_json::json!(20)),
        ("E2-a", "/alpha49/target/0", serde_json::json!(58)),
        ("E2-b", "/alpha49/target/1", serde_json::json!(26)),
        ("middle", "/alpha49/middle/0", serde_json::json!(25)),
        ("order", "/covers/0/order", serde_json::json!(107)),
        ("shift", "/covers/0/n/0", serde_json::json!(3)),
        ("lead", "/covers/1/n/0", serde_json::json!(55)),
        ("infinity", "/covers/1/infinity/1", serde_json::json!(45)),
        (
            "old-fixture-hash",
            "/t20_fixture_sha256",
            serde_json::json!("unbound"),
        ),
        ("schema", "/schema", serde_json::json!("unbound")),
        (
            "normalization",
            "/inverse_components/1",
            serde_json::json!(104),
        ),
        (
            "backtrack-tag",
            "/alpha49/target",
            serde_json::json!([1, 46]),
        ),
        (
            "reciprocal-sign-tag",
            "/covers/1/m/0",
            serde_json::json!(45),
        ),
    ] {
        let mut x = original.clone();
        *x.pointer_mut(path).unwrap() = value;
        mutants.push((name, x));
    }
    let mut x = original;
    x.as_object_mut()
        .unwrap()
        .insert("dlp_label".into(), serde_json::json!(1));
    mutants.push(("hidden-dlp-label", x));
    assert!(mutants.len() >= 16);
    let mutant_count = mutants.len();
    for (name, x) in mutants {
        let error = Maps::load(&serde_json::to_vec(&x).unwrap())
            .err()
            .unwrap_or_else(|| panic!("accepted {name}"));
        println!("REJECT C0 fixture {name}: {error}");
    }
    assert!(Maps::load(&vec![b' '; MAX_BYTES + 1]).is_err());
    assert!(maps.source_pull_component(2, &Pt::Inf).is_err());
    assert!(maps.source_pull_component(0, &Pt::Aff(101, 37)).is_err());
    assert!(maps.source_pull_component(0, &Pt::Aff(0, 0)).is_err());
    assert!(maps.alpha.forward(&Pt::Aff(101, 37)).is_err());
    assert!(maps.alpha.reverse(&Pt::Aff(0, 0)).is_err());
    assert!(maps.forward(&maps.target().identity()).is_err());
    assert!(maps.inverse(&maps.source.identity()).is_err());
    for c in [
        Coordinates {
            u: vec![],
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
            u: vec![0, 1],
            v: vec![0],
            plus: 0,
        },
        Coordinates {
            u: vec![1],
            v: vec![1],
            plus: 1,
        },
    ] {
        assert!(maps.source_norm_coordinates(&c).is_err());
    }
    println!("PASS all222 C0 rational elliptic fibres/O/norm2cross0;strata(identity,degrees,repeated,signed∞)={observed:?};both109-pointalpha49/beta49compositions49 andactualfirst7backtrack;{mutant_count}fixturemutants/domain/foreignmodel/canonical/size controlsreject");
}

#[test]
fn nonuniform_scalar_infinity_and_ramification_negative_controls() {
    let maps = pinned().unwrap();
    let classes = maps.source.classes().unwrap();
    let mut omitted_half = [0; 2];
    let mut uniform104 = [0; 2];
    let mut uniform85 = [0; 2];
    for d in &classes {
        let n = maps.source_norm(d).unwrap();
        let a = [maps.alpha.forward(&n[0]).unwrap(), n[1]];
        let correct = maps.forward(d).unwrap();
        let bad = maps.t20.pull(&a).unwrap();
        assert_eq!(bad, maps.target().mul(&correct, 2).unwrap());
        omitted_half[usize::from(bad == correct)] += 1;
        let t = maps.t20.norm(&correct).unwrap();
        let back = [maps.alpha.reverse(&t[0]).unwrap(), t[1]];
        let bad = maps
            .source_pull(&maps.source_pair_scale(&back, [104, 104]))
            .unwrap();
        uniform104[usize::from(bad == *d)] += 1;
        let bad = maps
            .source_pull(&maps.source_pair_scale(&back, [85, 85]))
            .unwrap();
        uniform85[usize::from(bad == *d)] += 1;
    }
    assert_eq!(omitted_half, [12316, 1]);
    assert_eq!(uniform104, [12208, 109]);
    assert_eq!(uniform85, [12204, 113]);
    let mut infinity = [0; 2];
    let mut squarefree = [0; 2];
    for point in [Pt::Aff(38, 56), Pt::Aff(38, 45)] {
        let fibre = maps.fibre(1, &point).unwrap().unwrap();
        let correct = maps.source_pull_component(1, &point).unwrap();
        match maps.source.reduce_fibre(&fibre.u, &fibre.v, 1) {
            Err(_) => infinity[0] += 1,
            Ok(bad) => {
                assert_ne!(bad, correct);
                infinity[1] += 1;
            }
        }
    }
    for point in [Pt::Aff(2, 37), Pt::Aff(2, 64)] {
        let fibre = maps.fibre(0, &point).unwrap().unwrap();
        let correct = maps.source_pull_component(0, &point).unwrap();
        let derivative = poly::derivative(&maps.field, &fibre.u);
        let repeated = poly::gcd(&maps.field, &fibre.u, &derivative);
        assert!(repeated.len() > 1);
        let (u, r) = poly::divrem(&maps.field, &fibre.u, &repeated);
        assert!(r.is_empty());
        let v = poly::rem(&maps.field, &fibre.v, &u);
        match maps.source.reduce_fibre(&u, &v, 0) {
            Err(_) => squarefree[0] += 1,
            Ok(bad) => {
                assert_ne!(bad, correct);
                assert_ne!(
                    maps.source_norm(&bad).unwrap(),
                    maps.source_norm(&correct).unwrap()
                );
                squarefree[1] += 1;
            }
        }
    }
    assert_eq!(infinity.iter().sum::<usize>(), 2);
    assert_eq!(squarefree.iter().sum::<usize>(), 2);
    let mut backtrack = [0; 2];
    for p in maps.points(0).unwrap().into_iter().skip(1) {
        let wrong = maps.alpha.first_roundtrip_control(&p).unwrap();
        let expected = maps
            .t20
            .pull(&[maps.alpha.forward(&p).unwrap(), Pt::Inf])
            .unwrap();
        // Admit the actual wrong endpoint before any target-group scalar work.
        match maps.t20.pull(&[wrong, Pt::Inf]) {
            Err(_) => backtrack[0] += 1,
            Ok(bad) => {
                if bad != expected {
                    backtrack[1] += 1;
                }
            }
        }
    }
    assert!(backtrack.iter().sum::<usize>() > 0);
    let d = maps
        .source_pull_component(1, &maps.points(1).unwrap()[1])
        .unwrap();
    let n = maps.source_norm(&d).unwrap();
    assert_ne!(n[1], Pt::Inf);
    let wrong = [
        maps.alpha.forward(&n[0]).unwrap(),
        curve::neg(&maps.field, &n[1]),
    ];
    let bad = maps
        .t20
        .pull(&maps.t20.scale_pair(&wrong, [55, 57]))
        .unwrap();
    assert_ne!(bad, maps.forward(&d).unwrap());
    assert_ne!(maps.inverse(&bad).unwrap(), d);
    println!("PASS negativeomittedforwardhalf different/equal={omitted_half:?};WRONGuniform104={uniform104:?};WRONGuniform85={uniform85:?};wrong∞reject/different={infinity:?};squarefreefinitefibrereject/different={squarefree:?};actualbacktracking7wrongE2route reject/different={backtrack:?};wrongreciprocalordinatesign actualvalidbutdifferent/roundtripfails;coherenttranslationsremainpositiveoraclecontrols");
}
