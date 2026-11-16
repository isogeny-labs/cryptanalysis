mod third_hop_tests {
    use super::*;
    fn short(c: &CheckedInstance, p: EP) -> Pt<ER> {
        match p {
            EP::Inf => Pt::Inf,
            EP::A(x, y) => Pt::Aff(c.independent_field.add(er(x), er(c.short_shift)), er(y)),
        }
    }
    fn torsion(f: &FpR, ec: &Curve<ER>) -> Vec<Pt<ER>> {
        let mut roots = poly::roots(f, &cubic(f, ec), &mut Rng::new(0x2d13));
        roots.sort();
        let mut out = vec![Pt::Inf];
        out.extend(roots.into_iter().map(|x| Pt::Aff(x, f.zero())));
        assert_eq!(out.len(), 4);
        out
    }
    #[test]
    fn all_actual_fixed_third_elliptic_edge() {
        let c = CheckedInstance::construct().unwrap();
        let hop = ThirdHop::construct(&c);
        let f = hop.field();
        println!("N4_NEXT13_MAPS {}", hop.certificate);
        let e0 = hop.previous.first.source();
        let e1 = hop.previous.source();
        let e2 = hop.source();
        let e3 = hop.target();
        let g0 = short(&c, c.inst.g);
        let g2 = hop.original_to_source(g0).unwrap();
        let g3 = hop.forward(g2).unwrap();
        assert_ne!(g3, Pt::Inf);
        assert_eq!(curve::pmul(f, e3, &g3, c.inst.ell as u128), Pt::Inf);
        let t0 = torsion(f, e0);
        let t2 = torsion(f, e2);
        let t3 = torsion(f, e3);
        let images = t2
            .iter()
            .map(|&p| {
                assert_eq!(curve::pmul(f, e2, &p, 2), Pt::Inf);
                let q = hop.forward(p).unwrap();
                assert!(t3.contains(&q));
                assert_eq!(hop.dual(q).unwrap(), p);
                q
            })
            .collect::<Vec<_>>();
        for (i, image) in images.iter().enumerate() {
            assert!(!images[..i].contains(image));
        }
        let mut source = vec![];
        for k in [1, 3, 5, 7, 17, 31, 101, c.inst.ell - 2] {
            let kg = curve::pmul(f, e0, &g0, k as u128);
            for t in &t0 {
                source.push(hop.original_to_source(curve::padd(f, e0, &kg, t)).unwrap());
            }
        }
        source.extend(&t2);
        assert_eq!(source.len(), 36);
        let mut source_rows = vec![];
        for &p in &source {
            let q = hop.forward(p).unwrap();
            let back = hop.dual(q).unwrap();
            assert_eq!(back, curve::pmul(f, e2, &p, 13));
            source_rows.push(json!({"source":point(p),"image":point(q),"dual_image":point(back)}));
        }
        let mut rng = Rng::new(0x313169);
        let mut targets = vec![Pt::Inf];
        for _ in 0..31 {
            targets.push(curve::random_point_f(f, e3, &mut rng));
        }
        targets.extend(&t3);
        assert_eq!(targets.len(), 36);
        let mut target_rows = vec![];
        for &p in &targets {
            let q = hop.dual(p).unwrap();
            let back = hop.forward(q).unwrap();
            assert_eq!(back, curve::pmul(f, e3, &p, 13));
            target_rows.push(
                json!({"target":point(p),"dual_image":point(q),"forward_dual_image":point(back)}),
            );
        }
        let mut addition_rows = vec![];
        for i in 0..32 {
            for j in 0..32 {
                let source_sum = curve::padd(f, e2, &source[i], &source[j]);
                let image = hop.forward(source_sum).unwrap();
                assert_eq!(
                    image,
                    curve::padd(
                        f,
                        e3,
                        &hop.forward(source[i]).unwrap(),
                        &hop.forward(source[j]).unwrap()
                    )
                );
                let target_sum = curve::padd(f, e3, &targets[i], &targets[j]);
                let dual_image = hop.dual(target_sum).unwrap();
                assert_eq!(
                    dual_image,
                    curve::padd(
                        f,
                        e2,
                        &hop.dual(targets[i]).unwrap(),
                        &hop.dual(targets[j]).unwrap()
                    )
                );
                addition_rows.push(json!({"i":i,"j":j,"source_sum":point(source_sum),"forward_sum":point(image),"target_sum":point(target_sum),"dual_sum":point(dual_image)}));
            }
        }
        println!(
            "N4_NEXT13_POINTS {}",
            json!({"all36_source":source_rows,"all36_target":target_rows,"all1024_each_addition_pairs":addition_rows,"source2":t2.iter().copied().map(point).collect::<Vec<_>>(),"target2":t3.iter().copied().map(point).collect::<Vec<_>>(),"actual_gamma3_torsion_images":images.iter().copied().map(point).collect::<Vec<_>>(),"nonzero_prime_ell_image":point(g3),"scope":"third elliptic edge; full64 product/conjugate transport remains new model phase"})
        );
        let public = c
            .parse(include_bytes!("../../fixtures/public-five.json"))
            .unwrap();
        assert_eq!(public.len(), 5);
        let expected: Value =
            serde_json::from_slice(include_bytes!("../../fixtures/expected-OUTSIDE-input.json"))
                .unwrap();
        let mut rows = vec![];
        for (i, p) in public.into_iter().enumerate() {
            let k = expected[i]["original_native_recovered_scalar"]
                .as_u64()
                .unwrap();
            assert!(c.verify_recovered(p, k));
            let p0 = short(&c, p);
            let p1 = hop.previous.first.forward(p0).unwrap();
            let p2 = hop.previous.forward(p1).unwrap();
            let p3 = hop.forward(p2).unwrap();
            assert_ne!(p3, Pt::Inf);
            assert_eq!(p3, curve::pmul(f, e3, &g3, k as u128));
            assert_eq!(curve::pmul(f, e3, &p3, c.inst.ell as u128), Pt::Inf);
            let d3 = hop.dual(p3).unwrap();
            assert_eq!(d3, curve::pmul(f, e2, &p2, 13));
            let d2 = hop.previous.dual(d3).unwrap();
            assert_eq!(d2, curve::pmul(f, e1, &p1, 169));
            let d1 = hop.previous.first.dual(d2).unwrap();
            assert_eq!(d1, curve::pmul(f, e0, &p0, 2197));
            rows.push(json!({"index":i,"E0":point(p0),"E1":point(p1),"E2":point(p2),"E3":point(p3),"reversed_three_hops":point(d1),"outside_runtime_test_scalar":k}));
        }
        println!(
            "N4_NEXT13_PUBLIC {}",
            json!({"all_five":rows,"runtime":"coordinates only, no scalar witness or odd DLP table","elliptic_phase_only":true,"full2197_rational_expansion":"outside bounded phase; sequential group roundtrip only","matched_prime_field_J3":"not constructed"})
        );
    }
}
