fn tuple(f: &FpR, base: &[Pt<ER>], v: u8) -> [Pt<ER>; 3] {
    std::array::from_fn(|i| pp(f, base[((v >> (2 * i)) & 3) as usize], i))
}
fn encoded(permutation: &[u8; 4], v: u8) -> u8 {
    (0..3).fold(0, |a, i| {
        a | (permutation[((v >> (2 * i)) & 3) as usize] << (2 * i))
    })
}
fn tuple_json(points: [Pt<ER>; 3]) -> Value {
    json!(points.map(point))
}
fn actual_frob(f: &FpR, points: [Pt<ER>; 3]) -> [Pt<ER>; 3] {
    [
        pp(f, points[2], 1),
        pp(f, points[0], 1),
        pp(f, points[1], 1),
    ]
}
fn rescale_endpoint(f: &FpR, old: &Curve<ER>, new: &Curve<ER>, gold: u64) -> (u64, Value) {
    let old2 = torsion(f, old);
    let new2 = torsion(f, new);
    let v = f.from_u64(12);
    let rescale = |p: Pt<ER>| match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => {
            assert!(f.is_zero(y));
            Pt::Aff(f.mul(v, x), f.zero())
        }
    };
    let permutation: [u8; 4] =
        std::array::from_fn(|i| new2.iter().position(|&p| p == rescale(old2[i])).unwrap() as u8);
    assert_eq!(permutation[0], 0);
    assert_eq!(
        permutation.iter().copied().collect::<BTreeSet<_>>().len(),
        4
    );
    let mut rows = vec![];
    let mut pairs = vec![];
    for a in 0..64u8 {
        let old_points = tuple(f, &old2, a);
        let new_index = encoded(&permutation, a);
        let new_points = tuple(f, &new2, new_index);
        assert_eq!(old_points.map(rescale), new_points);
        assert_eq!(actual_frob(f, old_points), tuple(f, &old2, frob(a)));
        assert_eq!(actual_frob(f, new_points), tuple(f, &new2, frob(new_index)));
        assert_eq!(encoded(&permutation, frob(a)), frob(new_index));
        for power in 0..3 {
            assert!(isogeny_algos::curve::on_curve(
                f,
                &Curve::new(fp(f, new.a, power), fp(f, new.b, power)),
                &new_points[power]
            ));
        }
        rows.push(json!({"old_index":a,"new_index":new_index,"all_old_coordinates":tuple_json(old_points),"all_new_coordinates":tuple_json(new_points),"actual_frobenius":tuple_json(actual_frob(f,new_points))}));
        for b in 0..64u8 {
            let bi = encoded(&permutation, b);
            let sum = encoded(&permutation, a ^ b);
            assert_eq!(sum, new_index ^ bi);
            let other = tuple(f, &new2, bi);
            let wanted = tuple(f, &new2, sum);
            for power in 0..3 {
                let ec = Curve::new(fp(f, new.a, power), fp(f, new.b, power));
                assert_eq!(
                    isogeny_algos::curve::padd(f, &ec, &new_points[power], &other[power]),
                    wanted[power]
                );
                let old_ec = Curve::new(fp(f, old.a, power), fp(f, old.b, power));
                let old_b = tuple(f, &old2, b);
                let old_sum =
                    isogeny_algos::curve::padd(f, &old_ec, &old_points[power], &old_b[power]);
                assert_eq!(rescale(old_sum), wanted[power]);
            }
            assert_eq!(pairing(a, b), pairing(new_index, bi));
            pairs.push(json!({"a":a,"b":b,"actual_new_a":new_index,"actual_new_b":bi,"actual_new_sum":sum,"original_alternating_pairing":pairing(a,b),"new_alternating_pairing":pairing(new_index,bi)}));
        }
    }
    let all = original_all();
    let transformed = all
        .iter()
        .map(|&h| {
            bits(
                &vs(h)
                    .into_iter()
                    .map(|a| encoded(&permutation, a))
                    .collect::<Vec<_>>(),
            )
        })
        .collect::<BTreeSet<_>>();
    assert_eq!(transformed, all);
    let new_gold = bits(
        &vs(gold)
            .into_iter()
            .map(|a| encoded(&permutation, a))
            .collect::<Vec<_>>(),
    );
    assert!(all.contains(&new_gold));
    assert_eq!(dimension(new_gold), 3);
    (
        new_gold,
        json!({"old_equation":[three(old.a),three(old.b)],"new_equation":[three(new.a),three(new.b)],"actual_2torsion_permutation":permutation,"all64_coordinate_and_frobenius_rows":rows,"all4096_addition_and_original_pairing_rows":pairs,"all135_original_masks":all,"all135_actual_transported_masks":transformed,"old_fixed_mask":gold,"new_fixed_mask":new_gold,"scope":"actual coordinate addition and original alternating2-torsion form; not a new Miller implementation"}),
    )
}
pub fn audit_twist(pair: &crate::TwistedPair) -> (u64, u64, Value) {
    let f = pair.field();
    let (g2, source) = rescale_endpoint(f, pair.old_source(), pair.source(), 1155175778390933505);
    let (g3, target) = rescale_endpoint(f, pair.old_target(), pair.target(), 9511681577844867105);
    let source2 = torsion(f, pair.source());
    let target2 = torsion(f, pair.target());
    let permutation: [u8; 4] = std::array::from_fn(|i| {
        target2
            .iter()
            .position(|&p| p == pair.forward(source2[i]))
            .unwrap() as u8
    });
    assert_eq!(permutation[0], 0);
    assert_eq!(
        permutation.iter().copied().collect::<BTreeSet<_>>().len(),
        4
    );
    for &p in &source2 {
        assert_eq!(pair.dual(pair.forward(p)), p);
    }
    let mut conjugates = vec![];
    for power in 0..3 {
        let dom = Curve::new(fp(f, pair.source().a, power), fp(f, pair.source().b, power));
        let cod = Curve::new(fp(f, pair.target().a, power), fp(f, pair.target().b, power));
        let m = &pair.forward_map;
        let cp = |p: &Vec<ER>| p.iter().copied().map(|x| fp(f, x, power)).collect();
        let map = crate::Rational {
            xn: cp(&m.xn),
            xd: cp(&m.xd),
            yn: cp(&m.yn),
            yd: cp(&m.yd),
        };
        let residual = crate::rational_curve_residual(f, &dom, &cod, &map);
        assert!(residual.is_empty());
        let points = (0..4)
            .map(|i| {
                let p = pp(f, source2[i], power);
                let q = crate::eval_rational(f, &dom, &cod, &map, p);
                assert_eq!(q, pp(f, target2[permutation[i] as usize], power));
                json!({"source":point(p),"actual_image":point(q)})
            })
            .collect::<Vec<_>>();
        conjugates.push(json!({"power":power,"domain":[three(dom.a),three(dom.b)],"codomain":[three(cod.a),three(cod.b)],"whole_curve_residual":crate::coefficients(&residual),"all_actual_torsion_images":points}));
    }
    let mut products = vec![];
    let mut pairs = vec![];
    for a in 0..64u8 {
        let image = encoded(&permutation, a);
        assert_eq!(encoded(&permutation, frob(a)), frob(image));
        products.push(json!({"source_index":a,"image_index":image,"actual_source_coordinates":tuple_json(tuple(f,&source2,a)),"actual_target_coordinates":tuple_json(tuple(f,&target2,image)),"Frobenius_source":frob(a),"Frobenius_target":frob(image)}));
        for b in 0..64u8 {
            let ib = encoded(&permutation, b);
            assert_eq!(encoded(&permutation, a ^ b), image ^ ib);
            assert_eq!(pairing(a, b), pairing(image, ib));
            pairs.push(json!({"a":a,"b":b,"image_a":image,"image_b":ib,"image_sum":image^ib,"source_pairing":pairing(a,b),"target_pairing":pairing(image,ib)}));
        }
    }
    let images = bits(
        &vs(g2)
            .into_iter()
            .map(|a| encoded(&permutation, a))
            .collect::<Vec<_>>(),
    );
    assert_eq!(images, g3);
    let all = original_all();
    let all_images = all
        .iter()
        .map(|&h| {
            bits(
                &vs(h)
                    .into_iter()
                    .map(|a| encoded(&permutation, a))
                    .collect::<Vec<_>>(),
            )
        })
        .collect::<BTreeSet<_>>();
    assert_eq!(all_images, all);
    let data = json!({"source_rescaling":source,"target_rescaling":target,"all3_actual_conjugate_maps":conjugates,"all64_product_images":products,"all4096_product_addition_and_original_pairing_rows":pairs,"all135_image_masks":all_images,"fixed_G2_before_models":g2,"fixed_G3_before_models":g3,"actual_gamma_G2_equals_G3":images==g3,"selection":"complete actual coordinate transport before ANY new HLP model admissibility"});
    println!("N4_TWIST_FIXED_KERNELS {}", data);
    (g2, g3, data)
}
