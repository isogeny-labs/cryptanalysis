// Actual coordinate transport, using the literal original finite-space helpers.
pub fn audit_third(hop: &chained_n4_nondual13_next_preflight::ThirdHop, old_gold: u64) -> Value {
    let f = hop.field();
    let old2 = torsion(f, hop.source());
    let new2 = torsion(f, hop.target());
    let mut permutation = [0u8; 4];
    for (i, &p) in old2.iter().enumerate() {
        let q = hop.forward(p).unwrap();
        permutation[i] = new2.iter().position(|&x| x == q).unwrap() as u8;
        assert_eq!(hop.dual(q).unwrap(), p);
    }
    assert_eq!(permutation[0], 0);
    assert_eq!(
        permutation.iter().copied().collect::<BTreeSet<_>>().len(),
        4
    );
    for a in 0..4 {
        for b in 0..4 {
            assert_eq!(permutation[a ^ b], permutation[a] ^ permutation[b]);
        }
    }
    let h: Vec<[u64; 3]> =
        serde_json::from_value(hop.certificate["new_kernel"]["kernel"].clone()).unwrap();
    let num: Vec<[u64; 3]> =
        serde_json::from_value(hop.certificate["third_forward"]["x_num"].clone()).unwrap();
    let den: Vec<[u64; 3]> =
        serde_json::from_value(hop.certificate["third_forward"]["x_den"].clone()).unwrap();
    let mut maps = vec![];
    let mut conjugates = vec![];
    for power in 0..3 {
        let ec = Curve::new(fp(f, hop.source().a, power), fp(f, hop.source().b, power));
        let kernel = h.iter().map(|&x| fp(f, er(x), power)).collect();
        let m = kohel(f, &ec, &kernel, 13);
        assert_eq!(
            m.num,
            num.iter().map(|&x| fp(f, er(x), power)).collect::<Vec<_>>()
        );
        assert_eq!(
            m.den,
            den.iter().map(|&x| fp(f, er(x), power)).collect::<Vec<_>>()
        );
        assert_eq!(
            m.cod,
            Curve::new(fp(f, hop.target().a, power), fp(f, hop.target().b, power))
        );
        let mut rows = vec![];
        for i in 0..4 {
            let p = pp(f, old2[i], power);
            let q = m.eval(f, &p);
            assert_eq!(q, pp(f, new2[permutation[i] as usize], power));
            rows.push(json!({"source":point(p),"image":point(q)}));
        }
        conjugates.push(json!({"factor":power,"domain_a":three(ec.a),"domain_b":three(ec.b),"codomain_a":three(m.cod.a),"codomain_b":three(m.cod.b),"kernel":m.ker.iter().copied().map(three).collect::<Vec<_>>(),"num":m.num.iter().copied().map(three).collect::<Vec<_>>(),"den":m.den.iter().copied().map(three).collect::<Vec<_>>(),"all4_actual_points":rows}));
        maps.push(m);
    }
    let transport = |v: u8| {
        (0..3).fold(0, |out, i| {
            out | (permutation[((v >> (2 * i)) & 3) as usize] << (2 * i))
        })
    };
    let coords = |v: u8, new: bool| -> [Pt<ER>; 3] {
        std::array::from_fn(|i| {
            pp(
                f,
                if new {
                    new2[((v >> (2 * i)) & 3) as usize]
                } else {
                    old2[((v >> (2 * i)) & 3) as usize]
                },
                i,
            )
        })
    };
    let repr = |v: [Pt<ER>; 3]| v.into_iter().map(point).collect::<Vec<_>>();
    assert_eq!((0..64).map(transport).collect::<BTreeSet<_>>().len(), 64);
    let mut vectors = vec![];
    let mut pairs = vec![];
    for a in 0..64 {
        let source = coords(a, false);
        let image = coords(transport(a), true);
        for i in 0..3 {
            assert_eq!(maps[i].eval(f, &source[i]), image[i]);
            assert_eq!(pp(f, source[(i + 2) % 3], 1), coords(frob(a), false)[i]);
            assert_eq!(
                pp(f, image[(i + 2) % 3], 1),
                coords(frob(transport(a)), true)[i]
            );
        }
        assert_eq!(transport(frob(a)), frob(transport(a)));
        vectors.push(json!({"source_vector":a,"image_vector":transport(a),"source_actual_coordinates":repr(source),"image_actual_coordinates":repr(image),"Frobenius_source_vector":frob(a),"Frobenius_image_vector":frob(transport(a))}));
        for b in 0..64 {
            assert_eq!(transport(a ^ b), transport(a) ^ transport(b));
            assert_eq!(pairing(a, b), pairing(transport(a), transport(b)));
            let sum0: [Pt<ER>; 3] = std::array::from_fn(|i| {
                isogeny_algos::curve::padd(f, &maps[i].dom, &source[i], &coords(b, false)[i])
            });
            let sum1: [Pt<ER>; 3] = std::array::from_fn(|i| {
                isogeny_algos::curve::padd(
                    f,
                    &maps[i].cod,
                    &image[i],
                    &coords(transport(b), true)[i],
                )
            });
            assert_eq!(sum0, coords(a ^ b, false));
            assert_eq!(sum1, coords(transport(a ^ b), true));
            for i in 0..3 {
                assert_eq!(maps[i].eval(f, &sum0[i]), sum1[i]);
            }
            pairs.push(json!({"a":a,"b":b,"source_sum_actual":repr(sum0),"image_sum_actual":repr(sum1),"source_pairing":pairing(a,b),"image_pairing":pairing(transport(a),transport(b))}));
        }
    }
    let transported_gold = bits(&vs(old_gold).into_iter().map(transport).collect::<Vec<_>>());
    assert_eq!(dimension(transported_gold), 3);
    let all = original_all();
    assert!(all.contains(&transported_gold));
    let stable: Vec<_> = all
        .iter()
        .copied()
        .filter(|&g| vs(g).iter().all(|&v| g & (1u64 << frob(v)) != 0))
        .collect();
    assert!(stable.contains(&transported_gold));
    json!({"protocol":"23ab48","actual_basis_permutation":permutation,"all3_actual_coefficient_conjugate_maps":conjugates,"all64_actual_coordinate_transports":vectors,"all4096_actual_coordinate_addition_and_pairing_rows":pairs,"full_bijection_addition_pairing_Frobenius_checked":true,"literal_current_J1_HLP10_mask":old_gold,"actual_transported_mask":transported_gold,"actual_transported_vectors":vs(transported_gold),"unchanged_untransported_mask_control":old_gold,"untransported_control_same_as_actual":old_gold==transported_gold,"all135_independent_original_masks":all,"all_rational_masks":stable,"selection_scope":"actual transported mask fixed before E2 model builder is called; no D or smoothness observed for selection","pairing_scope":"unique alternating2torsion pairing in actual coordinate basis, original symplectic bit helpers and full actual addition checks; not a Miller pairing implementation"})
}
