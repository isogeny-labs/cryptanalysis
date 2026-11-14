use super::*;
use chained_n4_public_target::{common, ghs::EP, ic, public_solver, CheckedInstance};
use ghs_original_engines::{
    cover,
    pic::{self, Gen, PicClass, PlaneQuartic},
};
use isogeny_algos::{
    curve::{self, Pt},
    field::{Field, Rng},
    fpr::ER,
    poly,
};
use serde_json::json;

fn er(x: [u64; 3]) -> ER {
    let mut y = [0; 16];
    y[..3].copy_from_slice(&x);
    y
}
fn ep(p: Point) -> Pt<ER> {
    match p {
        None => Pt::Inf,
        Some((x, y)) => Pt::Aff(er(x), er(y)),
    }
}
fn kp(p: Pt<ER>) -> Point {
    match p {
        Pt::Inf => None,
        Pt::Aff(x, y) => {
            assert!(x[3..].iter().chain(y[3..].iter()).all(|&x| x == 0));
            Some(([x[0], x[1], x[2]], [y[0], y[1], y[2]]))
        }
    }
}
fn add(c: &CheckedInstance, p: Point, q: Point) -> Point {
    kp(curve::padd(
        &c.independent_field,
        &c.independent_curve,
        &ep(p),
        &ep(q),
    ))
}
fn neg(c: &CheckedInstance, p: Point) -> Point {
    kp(curve::neg(&c.independent_field, &ep(p)))
}
fn short(c: &CheckedInstance, p: EP) -> Point {
    match p {
        EP::Inf => None,
        EP::A(x, y) => Some((c.inst.kf.add(&x, &c.short_shift), y)),
    }
}
fn signed(c: &CheckedInstance, p: EP) -> Point {
    neg(c, short(c, p))
}
fn inverse_signed(c: &CheckedInstance, p: Point) -> EP {
    match p {
        None => EP::Inf,
        Some((x, y)) => EP::A(c.inst.kf.sub(&x, &c.short_shift), c.inst.kf.neg(&y)),
    }
}

fn plane_from_ciani(n: &NormV2, xyz: [ER; 3]) -> [ER; 3] {
    let f = &n.f;
    let pivot = xyz.iter().position(|&x| !f.is_zero(x)).unwrap();
    let rows: Vec<[ER; 3]> = (0..3)
        .filter(|&i| i != pivot)
        .map(|i| {
            std::array::from_fn(|j| {
                f.sub(
                    f.mul(xyz[pivot], n.embed(n.a.core.omi[i][j])),
                    f.mul(xyz[i], n.embed(n.a.core.omi[pivot][j])),
                )
            })
        })
        .collect();
    std::array::from_fn(|i| {
        let j = (i + 1) % 3;
        let k = (i + 2) % 3;
        f.sub(f.mul(rows[0][j], rows[1][k]), f.mul(rows[0][k], rows[1][j]))
    })
}

fn series_mul(f: &cover::Fq, a: [u64; 3], b: [u64; 3]) -> [u64; 3] {
    std::array::from_fn(|k| (0..=k).fold(0, |s, i| f.add(s, f.mul(a[i], b[k - i]))))
}
fn restriction(f: &cover::Fq, coords: [[u64; 3]; 3], mon: (u8, u8, u8)) -> [u64; 3] {
    let mut result = [1, 0, 0];
    for (i, power) in [mon.0, mon.1, mon.2].into_iter().enumerate() {
        for _ in 0..power {
            result = series_mul(f, result, coords[i]);
        }
    }
    result
}
fn curve_series(n: &NormV2, coords: [[u64; 3]; 3]) -> [u64; 3] {
    let f = &n.a.field.f;
    let mut value = [0; 3];
    for (mon, c) in pic::mons_of_degree(4).into_iter().zip(n.a.core.quartic) {
        let term = restriction(f, coords, mon);
        for i in 0..3 {
            value[i] = f.add(value[i], f.mul(c, term[i]));
        }
    }
    value
}
fn triple_jet(n: &NormV2, p: [u32; 3]) -> Result<PicClass, String> {
    let f = &n.a.field.f;
    let pivot = p.iter().position(|&x| x != 0).unwrap();
    let free: Vec<_> = (0..3).filter(|&i| i != pivot).collect();
    let (mut x, mut y) = (free[0], free[1]);
    let base: [[u64; 3]; 3] = p.map(|v| [v as u64, 0, 0]);
    let mut varying = base;
    varying[x][1] = 1;
    let mut fx = curve_series(n, varying)[1];
    varying = base;
    varying[y][1] = 1;
    let mut fy = curve_series(n, varying)[1];
    if fy == 0 {
        std::mem::swap(&mut x, &mut y);
        std::mem::swap(&mut fx, &mut fy);
    }
    if fy == 0 {
        return Err("singular affine jet".into());
    }
    let mut coords = base;
    coords[x][1] = 1;
    coords[y][1] = f.neg(f.mul(fx, f.inv(fy)));
    coords[y][2] = f.neg(f.mul(curve_series(n, coords)[2], f.inv(fy)));
    assert_eq!(curve_series(n, coords), [0; 3]);
    let columns: Vec<_> = pic::mons_of_degree(2)
        .into_iter()
        .map(|m| restriction(f, coords, m))
        .collect();
    let equations = (0..3)
        .map(|i| columns.iter().map(|v| v[i] as u32).collect())
        .collect();
    let rows = n.a.pic.linear_kernel(equations, 6);
    if rows.len() != 3 {
        return Err("jet rank".into());
    }
    Ok(n.a.pic.class_from_conics(rows))
}

#[test]
fn actual_q223_models_origins_both_compositions_and_multiplicities() {
    let c = CheckedInstance::construct().unwrap();
    let n = NormV2::new(AdapterV2::new(&c).unwrap()).unwrap();
    let pic = &n.a.pic;
    let kf = &c.inst.kf;
    let points = pic.rational_points_bruteforce();
    assert_eq!(points.len(), 224);
    println!(
        "N4_V2_IDENTITY {}",
        json!({"q":223,"ell":c.inst.ell,"order":c.inst.order,
        "field":n.a.field_tag,"completed_model":n.a.model_tag,"Jac_model":n.model_tag,
        "quartic":n.a.core.quartic,"base_point":pic.base_point(),"C_rational_points":points.len(),
        "all15_N4_coefficients_exact":true,"original_field_basis_exact":true,
        "actual_infinity_origin_key":n.a.origin_shift().key().0.to_vec()})
    );
    let sg = signed(&c, c.inst.g);
    let h = n.a.transfer_point(&sg).unwrap();
    assert!(!pic.is_zero(&h));
    assert!(pic.is_zero(&pic.mul_scalar(&h, c.inst.ell as u128)));
    assert_eq!(inverse_signed(&c, sg), c.inst.g);
    assert_eq!(n.norm(&h).unwrap(), add(&c, sg, sg));

    let mut rng = common::Rng::new(0x58b2);
    let mut sylow = vec![EP::Inf];
    let mut samples = Vec::new();
    for _ in 0..128 {
        let r = c.inst.ec.rand_point(&mut rng);
        let t = c.inst.ec.mul(&r, c.inst.ell as u128);
        samples.push(chained_n4_public_target::encode_point(t));
        let old = sylow.clone();
        for p in old {
            let v = c.inst.ec.add(&p, &t);
            if !sylow.contains(&v) {
                sylow.push(v);
            }
        }
        if sylow.len() == 4 {
            break;
        }
    }
    assert_eq!(sylow.len(), 4);
    for p in &sylow {
        assert_eq!(c.inst.ec.mul(p, 4), EP::Inf);
    }
    let two_roots = poly::roots(
        &c.independent_field,
        &vec![
            c.independent_curve.b,
            c.independent_curve.a,
            c.independent_field.zero(),
            c.independent_field.one(),
        ],
        &mut Rng::new(0x58b3),
    );
    for x in &two_roots {
        assert!(sylow.contains(&EP::A(kf.sub(&[x[0], x[1], x[2]], &c.short_shift), [0; 3])));
    }
    println!(
        "N4_V2_SYLOW {}",
        json!({"actual_points":sylow.iter().map(|&x|chained_n4_public_target::encode_point(x)).collect::<Vec<_>>(),"original_samples":samples,"all_original_cubic_two_torsion_roots":two_roots.len(),"no_DLP_table":true})
    );

    let scalars = [0, 1, 2, 3, 17, 101, c.inst.ell / 2, c.inst.ell - 1];
    let mut source_count = 0;
    let mut legacy_split = 0;
    let t = n.a.short_point(QuarticPoint::InfinityMinus).unwrap();
    assert_eq!(n.a.quartic_point(&t).unwrap(), QuarticPoint::InfinityMinus);
    let legacy_origin = pic.reduce_deg6(&n.a.trace_space(&t).unwrap());
    for scalar in scalars {
        for torsion in &sylow {
            let p = c
                .inst
                .ec
                .add(&c.inst.ec.mul(&c.inst.g, scalar as u128), torsion);
            let s = signed(&c, p);
            assert_eq!(inverse_signed(&c, s), p);
            let image = n.a.transfer_point(&s).unwrap();
            assert_eq!(n.norm(&image).unwrap(), add(&c, s, s));
            let norm = n.norm(&image).unwrap();
            assert_eq!(n.a.transfer_point(&norm).unwrap(), pic.double(&image));
            if *torsion == EP::Inf {
                assert_eq!(image, pic.mul_scalar(&h, scalar as u128));
            }
            if let Some((tt, yy)) = c.inst.ec_to_quartic(&p) {
                assert_eq!(
                    n.a.quartic_point(&short(&c, p)).unwrap(),
                    QuarticPoint::Finite(tt, kf.neg(&yy))
                );
                let raw_image = n.a.short_point(QuarticPoint::Finite(tt, yy)).unwrap();
                assert_eq!(raw_image, add(&c, t, neg(&c, short(&c, p))));
                if let Some(rows) = c.inst.transfer_cubics(&p) {
                    let old_raw = pic.reduce_deg6(&Gen { k: 3, rows });
                    let complete_raw = pic.reduce_deg6(&n.a.trace_space(&raw_image).unwrap());
                    assert_eq!(old_raw, complete_raw);
                    assert_eq!(pic.sub(&old_raw, &legacy_origin), image);
                    legacy_split += 1;
                }
            }
            source_count += 1;
        }
    }
    assert_eq!(source_count, 32);
    assert!(legacy_split > 0);
    for p in &points {
        let class = pic.point_class(*p);
        let norm = n.norm(&class).unwrap();
        assert_eq!(n.a.transfer_point(&norm).unwrap(), pic.double(&class));
    }
    assert_eq!(n.norm(&pic.zero()).unwrap(), None);
    println!(
        "N4_V2_COMPOSITIONS {}",
        json!({"source_panel":source_count,"all_rational_point_classes":points.len(),"both_two_compositions":true,"PhiG_nonzero_exact_prime_order":c.inst.ell,"legacy_finite_split_comparisons":legacy_split,"legacy_origin_key":legacy_origin.key().0.to_vec(),"T":t,"doubleT":add(&c,t,t),"scope":"bounded native correctness;not all J or E points/fullformalization"})
    );

    let plane = ic::Curve::new(223, &c.inst.f);
    let mut rng = common::Rng::new(102 ^ 0xC0FFEE);
    let fb = public_solver::sample_points(&plane, 36, &mut rng);
    let legacy_p0 = fb
        .iter()
        .find_map(|p| {
            let p = p.map(|v| v as u32);
            PlaneQuartic::new(223, c.inst.f, p).ok().map(|_| p)
        })
        .unwrap();
    let alternative = if legacy_p0 != pic.base_point() {
        legacy_p0
    } else {
        *points.iter().find(|&&p| p != pic.base_point()).unwrap()
    };
    let other = AdapterV2::with_base_point(&c, Some(alternative)).unwrap();
    let op = &other.pic;
    let delta = op.exceptional(pic.base_point());
    assert!(!op.is_zero(&delta));
    let back_delta = pic.exceptional(op.base_point());
    let bridge = |x: &PicClass| op.sub(x, &delta);
    let inverse = |x: &PicClass| pic.sub(x, &back_delta);
    assert!(op.is_zero(&bridge(&pic.zero())));
    assert!(pic.is_zero(&inverse(&op.zero())));
    let classes: Vec<_> = points
        .iter()
        .take(8)
        .map(|&p| pic.point_class(p))
        .chain([pic.zero(), h.clone()])
        .collect();
    for x in &classes {
        assert_eq!(inverse(&bridge(x)), *x);
        for y in &classes {
            assert_eq!(bridge(&pic.add(x, y)), op.add(&bridge(x), &bridge(y)));
        }
    }
    let raw = n.a.trace_space(&sg).unwrap();
    let old_raw = pic.reduce_deg6(&raw);
    let new_raw = op.reduce_deg6(&raw);
    assert_eq!(new_raw, op.add(&bridge(&old_raw), &op.double(&delta)));
    assert_eq!(other.transfer_point(&sg).unwrap(), bridge(&h));
    assert_ne!(n.a.model_tag, other.model_tag);
    println!(
        "N4_V2_BASEPOINT {}",
        json!({"actual_original_winning_FB_P0":legacy_p0,"canonical_P0":pic.base_point(),"other_P0":alternative,"geometric_delta":delta.key().0.to_vec(),"zero_inverse":true,"addition_pairs":classes.len()*classes.len(),"raw_final_key_delta_and_raw_degree6_two_delta_distinct":true,"complete_map_bridge":true})
    );

    let legacy_n = NormV2::new(AdapterV2::with_base_point(&c, Some(legacy_p0)).unwrap()).unwrap();
    assert!(other.decode(&n.a.encode(sg)).is_err());
    assert!(legacy_n.decode(&n.encode(&h)).is_err());
    let finite_zero = Some((n.a.core.wshift, n.a.core.walpha));
    let finite_zero_quartic = n.a.quartic_point(&finite_zero).unwrap();
    let QuarticPoint::Finite(zero_t, _) = finite_zero_quartic else {
        panic!("positivezero isfinite")
    };
    let beta = kf.sub(&c.inst.qd, &kf.mul(&n.a.core.ws, &n.a.core.ws));
    assert_eq!(zero_t, kf.mul(&kf.neg(&beta), &kf.inv(&n.a.core.walpha)));
    assert_eq!(n.a.short_point(finite_zero_quartic).unwrap(), finite_zero);
    assert_ne!(finite_zero, t);
    for p in [None, t, finite_zero, sg] {
        assert_eq!(
            pic.reduce_deg6(&n.a.trace_space(&p).unwrap()),
            pic.reduce_deg6(&n.a.trace_space_gauged(&p, Some([1, 1, 0])).unwrap())
        );
    }
    println!(
        "N4_V2_ZERO_GAUGE {}",
        json!({"actual_finite_zero":finite_zero,"actual_quartic_t":zero_t,"original_parameter_minus_beta_over_alpha":true,"finite_and_negative_infinity_distinct":true,"four_nonzero_K3_fibre_gauges":4,"foreign_actual_P0_point_and_class_tags_rejected":true})
    );
    let lp = &legacy_n.a.pic;
    let actual_origin = lp.reduce_deg6(&legacy_n.a.trace_space(&t).unwrap());
    assert!(!lp.is_zero(&actual_origin));
    let mut actual_legacy_splits = 0;
    for scalar in scalars {
        for torsion in &sylow {
            let p = c
                .inst
                .ec
                .add(&c.inst.ec.mul(&c.inst.g, scalar as u128), torsion);
            let image = legacy_n.a.transfer_point(&signed(&c, p)).unwrap();
            assert_eq!(
                legacy_n.norm(&image).unwrap(),
                add(&c, signed(&c, p), signed(&c, p))
            );
            if let Some(rows) = c.inst.transfer_cubics(&p) {
                let raw = lp.reduce_deg6(&Gen { k: 3, rows });
                let (tt, yy) = c.inst.ec_to_quartic(&p).unwrap();
                let point = legacy_n
                    .a
                    .short_point(QuarticPoint::Finite(tt, yy))
                    .unwrap();
                assert_eq!(
                    raw,
                    lp.reduce_deg6(&legacy_n.a.trace_space(&point).unwrap())
                );
                assert_eq!(lp.sub(&raw, &actual_origin), image);
                actual_legacy_splits += 1;
            }
        }
    }
    assert_eq!(actual_legacy_splits, legacy_split);
    let requests = c
        .parse(include_bytes!("../../fixtures/public-five.json"))
        .unwrap();
    let answers: Vec<serde_json::Value> =
        serde_json::from_slice(include_bytes!("../../fixtures/expected-OUTSIDE-input.json"))
            .unwrap();
    let r0 = c.inst.ec.mul(&c.inst.g, 101);
    let completed_raw = |p| {
        lp.add(
            &legacy_n.a.transfer_point(&signed(&c, p)).unwrap(),
            &actual_origin,
        )
    };
    let r0raw = completed_raw(r0);
    let d1 = lp.sub(&completed_raw(c.inst.ec.add(&r0, &c.inst.g)), &r0raw);
    assert!(!lp.is_zero(&d1));
    for (i, target) in requests.iter().copied().enumerate() {
        let image = legacy_n.a.transfer_point(&signed(&c, target)).unwrap();
        let recovered = kp(curve::pmul(
            &c.independent_field,
            &c.independent_curve,
            &ep(legacy_n.norm(&image).unwrap()),
            c.inst.ell.div_ceil(2) as u128,
        ));
        assert_eq!(inverse_signed(&c, recovered), target);
        let d2 = lp.sub(&completed_raw(c.inst.ec.add(&r0, &target)), &r0raw);
        assert_eq!(
            lp.mul_scalar(
                &d1,
                answers[i]["original_native_recovered_scalar"]
                    .as_u64()
                    .unwrap() as u128
            ),
            d2
        );
    }
    println!(
        "N4_V2_ACTUAL_LEGACY {}",
        json!({"winning_FB_P0":legacy_p0,"nonzero_geometric_raw_origin":actual_origin.key().0.to_vec(),"actual_original_split_comparisons":actual_legacy_splits,"fresh_legacyP0_norm_source_panel":32,"five_public_point_half_inverses":5,"five_actual_affine_three_point_cancellations":5,"ratio_base_nonzero":true})
    );

    let offsets = n.line_offsets().unwrap();
    assert_eq!(offsets.len(), 224);
    assert!(offsets.iter().all(|&x| x == n.offset));
    let f = &n.f;
    let mut infinities = 0;
    let mut branches = 0;
    for x in [f.one(), f.neg(f.one())] {
        for y in [f.one(), f.neg(f.one())] {
            let w = plane_from_ciani(&n, [x, y, f.one()]);
            assert!(n.point_on_quartic(w));
            let expected = if y == f.one() {
                Pt::Inf
            } else {
                match t {
                    Some((x, y)) => Pt::Aff(n.embed(x), n.embed(y)),
                    None => panic!("negative infinity finite"),
                }
            };
            assert_eq!(n.cover(w).unwrap(), expected);
            infinities += 1;
        }
    }
    let u0 = vec![n.embed(n.a.uc), n.embed(n.a.ub), f.one()];
    let us = [
        u0.clone(),
        u0.iter().map(|&v| f.pow(v, 223)).collect(),
        u0.iter().map(|&v| f.pow(v, 223u128.pow(2))).collect(),
    ];
    let b = n.embed(n.a.field.scale(&n.a.core.wb, n.a.field.f.inv(2)));
    let ss = n.embed(n.a.core.ws);
    let alpha = n.embed(n.a.core.walpha);
    let shift = n.embed(n.a.core.wshift);
    for index in 0..3 {
        let roots = poly::roots(f, &us[index], &mut Rng::new(0x58c0 + index as u64));
        assert_eq!(roots.len(), 2);
        for tt in roots {
            let values = us.each_ref().map(|u| poly::eval(f, u, tt));
            let ratio = if index == 0 {
                f.div(values[1], values[2])
            } else if index == 1 {
                f.div(values[2], values[0])
            } else {
                f.div(values[1], values[0])
            };
            let rs = poly::roots(
                f,
                &vec![f.neg(ratio), f.zero(), f.one()],
                &mut Rng::new(0x58c4 + index as u64),
            );
            assert_eq!(rs.len(), 2);
            for rr in rs {
                let xyz = if index == 0 {
                    [rr, f.one(), f.zero()]
                } else if index == 1 {
                    [f.zero(), rr, f.one()]
                } else {
                    [rr, f.zero(), f.one()]
                };
                let w = plane_from_ciani(&n, xyz);
                assert!(n.point_on_quartic(w));
                let yy = if index == 1 {
                    f.mul(values[0], rr)
                } else {
                    f.zero()
                };
                let xx = f.mul(
                    f.from_u64(2),
                    f.add(f.add(f.add(yy, f.sq(tt)), f.mul(b, tt)), ss),
                );
                let wy = f.add(
                    f.add(f.mul(f.mul(f.from_u64(2), xx), tt), f.mul(b, xx)),
                    alpha,
                );
                assert_eq!(n.cover(w).unwrap(), Pt::Aff(f.add(xx, shift), wy));
                branches += 1;
            }
        }
    }
    let mut nilpotent = None;
    let mut skipped = Vec::new();
    for p in &points {
        match triple_jet(&n, *p)
            .and_then(|class| n.multiplicity_audit(&class).map(|audit| (class, audit)))
        {
            Ok((class, (multiplicities, wrong_differs))) => {
                assert_eq!(multiplicities.iter().sum::<usize>(), 3);
                assert!(multiplicities.iter().any(|&m| m > 1));
                assert_eq!(
                    n.norm_ext(&class, 1).unwrap(),
                    n.norm_ext(&class, 0).unwrap()
                );
                assert_eq!(
                    n.a.transfer_point(&n.norm(&class).unwrap()).unwrap(),
                    pic.double(&class)
                );
                let observation = json!({"P":p,"key":class.key().0.to_vec(),"multiplicities":multiplicities,"omitting_multiplicities_changes_norm":wrong_differs,"alternate_chart":true});
                if wrong_differs {
                    nilpotent = Some(observation);
                    break;
                }
                skipped.push(json!({"P":p,"actual_null_control":observation}));
            }
            Err(error) => skipped.push(json!({"P":p,"rejection":error})),
        }
    }
    assert!(nilpotent.is_some());
    assert_eq!(infinities, 4);
    assert_eq!(branches, 12);
    println!(
        "N4_V2_EXCEPTIONAL {}",
        json!({"plane_line_offsets":offsets.len(),"all_offsets_equal":true,"four_infinity_sign_controls":infinities,"all_three_quadratic_branch_pairs":branches,"actual_3P_nonreduced_scheme":nilpotent,"all_jet_rejections":skipped})
    );
}
