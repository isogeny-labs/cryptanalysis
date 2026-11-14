//! Fixed101 degree7 construction using the unchanged existing Kohel engine.
//! Exact polynomial identities replace its heuristic kernel acceptance.
use isogeny_algos::curve::{self, Curve, Isogeny, Pt, RatIsogeny};
use isogeny_algos::field::{Field, Rng, Zp};
use isogeny_algos::find::divpoly::{division_poly, kernel_polys};
use isogeny_algos::kernel::kohel::kohel;
use isogeny_algos::poly;
use std::collections::HashSet;

type Polynomial = Vec<u64>;

/// A coordinate scale is accepted only after both coefficient equations.
/// The old iso_exists_over helper merely supplies an unchecked candidate.
pub(super) fn checked_isomorphism(f: &Zp, source: &Curve<u64>, target: &Curve<u64>) -> Option<u64> {
    assert_eq!(f.p, 101, "bounded coordinate normalization");
    (1..101).find(|u| {
        f.mul(f.pow(*u, 4), source.a) == target.a && f.mul(f.pow(*u, 6), source.b) == target.b
    })
}

pub(super) struct SevenEdge {
    pub(super) map: RatIsogeny<Zp>,
    pub(super) dual: RatIsogeny<Zp>,
    pub(super) dual_scale: u64,
}
impl SevenEdge {
    pub(super) fn reverse(&self, f: &Zp, point: &Pt<u64>) -> Pt<u64> {
        match self.dual.eval(f, point) {
            Pt::Inf => Pt::Inf,
            Pt::Aff(x, y) => {
                let u2 = f.sq(self.dual_scale);
                Pt::Aff(f.mul(u2, x), f.mul(f.mul(u2, self.dual_scale), y))
            }
        }
    }
}

fn cube(f: &Zp, a: &Polynomial) -> Polynomial {
    poly::mul(f, &poly::mul(f, a, a), a)
}

fn certify_curve_identity(f: &Zp, iso: &RatIsogeny<Zp>) {
    assert!(curve::is_smooth(f, &iso.dom) && curve::is_smooth(f, &iso.cod));
    let h = &iso.ker;
    assert_eq!(
        (iso.deg, h.len(), iso.num.len(), iso.den.len()),
        (7, 4, 8, 7)
    );
    assert_eq!(h.last(), Some(&1));
    assert_eq!(poly::gcd(f, h, &poly::derivative(f, h)), vec![1]);
    let source = vec![iso.dom.b, iso.dom.a, 0, 1];
    assert_eq!(poly::gcd(f, h, &source), vec![1]);
    assert_eq!(poly::gcd(f, &iso.num, &iso.den), vec![1]);
    assert_eq!(iso.den, poly::mul(f, h, h));
    assert_eq!(poly::rem(f, &division_poly(f, &iso.dom, 7), h), vec![]);
    let s = poly::sub(
        f,
        &poly::mul(f, &poly::derivative(f, &iso.num), &iso.den),
        &poly::mul(f, &iso.num, &poly::derivative(f, &iso.den)),
    );
    let d2 = poly::mul(f, &iso.den, &iso.den);
    let target = poly::add(
        f,
        &poly::add(
            f,
            &cube(f, &iso.num),
            &poly::scale(f, &poly::mul(f, &iso.num, &d2), iso.cod.a),
        ),
        &poly::scale(f, &cube(f, &iso.den), iso.cod.b),
    );
    assert_eq!(
        poly::mul(f, &source, &poly::mul(f, &s, &s)),
        poly::mul(f, &iso.den, &target),
        "exact denominator-cleared curve identity"
    );
}

fn homogeneous(f: &Zp, coefficients: &Polynomial, n: &Polynomial, d: &Polynomial) -> Polynomial {
    let degree = coefficients.len() - 1;
    let mut ns = vec![vec![1]];
    let mut ds = vec![vec![1]];
    for i in 0..degree {
        ns.push(poly::mul(f, &ns[i], n));
        ds.push(poly::mul(f, &ds[i], d));
    }
    let mut out = vec![];
    for (i, coefficient) in coefficients.iter().enumerate() {
        out = poly::add(
            f,
            &out,
            &poly::scale(f, &poly::mul(f, &ns[i], &ds[degree - i]), *coefficient),
        );
    }
    out
}

fn compose_x(
    f: &Zp,
    outer: (&Polynomial, &Polynomial),
    inner: (&Polynomial, &Polynomial),
) -> (Polynomial, Polynomial) {
    assert_eq!(outer.0.len(), outer.1.len() + 1);
    (
        homogeneous(f, outer.0, inner.0, inner.1),
        poly::mul(f, inner.1, &homogeneous(f, outer.1, inner.0, inner.1)),
    )
}

fn multiply_seven_x(f: &Zp, e: &Curve<u64>) -> (Polynomial, Polynomial) {
    let psi = division_poly(f, e, 7);
    let d = poly::mul(f, &psi, &psi);
    let product = poly::mul(f, &division_poly(f, e, 6), &division_poly(f, e, 8));
    let correction = poly::scale(f, &poly::mul(f, &vec![e.b, e.a, 0, 1], &product), 4);
    (poly::sub(f, &poly::mul(f, &vec![0, 1], &d), &correction), d)
}

pub(super) fn construct_edges(f: &Zp, e: &Curve<u64>) -> Vec<SevenEdge> {
    assert_eq!(f.p, 101, "fixed correctness constructor");
    let mut rng = Rng::new(0x19_101);
    let mut kernels = kernel_polys(f, e, 7, &mut rng);
    kernels.sort();
    assert_eq!(kernels.len(), 2, "fixed split degree7 module control");
    let u = f.inv(7);
    let u2 = f.sq(u);
    let mut out = vec![];
    for h in kernels {
        let map = kohel(f, e, &h, 7);
        certify_curve_identity(f, &map);
        let candidates = kernel_polys(f, &map.cod, 7, &mut rng)
            .into_iter()
            .map(|h| kohel(f, &map.cod, &h, 7))
            .filter(|d| {
                f.mul(f.sq(u2), d.cod.a) == e.a && f.mul(f.mul(f.sq(u2), u2), d.cod.b) == e.b
            })
            .collect::<Vec<_>>();
        assert_eq!(
            candidates.len(),
            1,
            "unique normalized dual with source scaling"
        );
        let dual = candidates.into_iter().next().unwrap();
        certify_curve_identity(f, &dual);
        let scaled = poly::scale(f, &dual.num, u2);
        let c = compose_x(f, (&scaled, &dual.den), (&map.num, &map.den));
        let expected = multiply_seven_x(f, e);
        assert_eq!(
            poly::mul(f, &c.0, &expected.1),
            poly::mul(f, &expected.0, &c.1),
            "global source dual-x identity[7]"
        );
        let c = compose_x(f, (&map.num, &map.den), (&scaled, &dual.den));
        let expected = multiply_seven_x(f, &map.cod);
        assert_eq!(
            poly::mul(f, &c.0, &expected.1),
            poly::mul(f, &expected.0, &c.1),
            "global target dual-x identity[7]"
        );
        out.push(SevenEdge {
            map,
            dual,
            dual_scale: u,
        });
    }
    out
}

fn points(f: &Zp, e: &Curve<u64>) -> Vec<Pt<u64>> {
    let mut out = vec![Pt::Inf];
    for x in 0..f.p {
        for y in 0..f.p {
            if curve::on_curve(f, e, &Pt::Aff(x, y)) {
                out.push(Pt::Aff(x, y));
            }
        }
    }
    out
}

#[test]
fn actual_seven_kernels_duals_global_identities_and_full_groups() {
    let f = Zp::new(101);
    let second = isogeny_algos::genus2::cubic_to_short(&f, &vec![5, 33, 13, 1]);
    let shift = f.div(13, 3);
    let long = isogeny_algos::weier::GWCurve::new([0, 13, 0, 33, 5]);
    for x in 0..101 {
        for y in 0..101 {
            assert_eq!(
                long.on_curve(&f, &Pt::Aff(x, y)),
                curve::on_curve(&f, &second, &Pt::Aff(f.add(x, shift), y))
            );
        }
    }
    let mut witness = String::from("# chained-elliptic-seven/v1;p101;existing Kohel;short models;dual_scale=1/7\na\tb\torder\tkernel\tcod_a\tcod_b\tnum\tden\tdual_kernel\tdual_num\tdual_den\tdual_cod_a\tdual_cod_b\tdual_scale\n");
    for (source, order) in [(Curve::new(1, 46), 109_u64), (second, 113)] {
        let source_points = points(&f, &source);
        assert_eq!(source_points.len() as u64, order);
        let inverse_seven = (1..order).find(|k| 7 * k % order == 1).unwrap();
        let edges = construct_edges(&f, &source);
        let source_j = curve::jinv(&f, &source);
        let target_j = edges
            .iter()
            .map(|e| curve::jinv(&f, &e.map.cod))
            .collect::<Vec<_>>();
        assert_ne!(target_j[0], target_j[1]);
        for edge in &edges {
            assert_ne!(source_j, curve::jinv(&f, &edge.map.cod));
            assert_eq!(checked_isomorphism(&f, &source, &edge.map.cod), None);
        }
        assert_eq!(
            checked_isomorphism(&f, &edges[0].map.cod, &edges[1].map.cod),
            None
        );
        assert_eq!(checked_isomorphism(&f, &source, &source), Some(1));
        println!("Eorder{order} checked coordinate-isomorphism control:sourcej{source_j},targetj{target_j:?},both source-target and cross-target coefficient-scale tests reject;unchecked legacy scale candidates are not isomorphism verdicts");
        for edge in edges {
            let target_points = points(&f, &edge.map.cod);
            assert_eq!(target_points.len() as u64, order);
            let mut seen = HashSet::new();
            let g = source_points[1];
            let image = edge.map.eval(&f, &g);
            assert_ne!(image, Pt::Inf);
            for point in &source_points {
                let mapped = edge.map.eval(&f, point);
                assert!(curve::on_curve(&f, &edge.map.cod, &mapped));
                seen.insert(mapped);
                assert_eq!(
                    edge.reverse(&f, &mapped),
                    curve::pmul(&f, &source, point, 7)
                );
                assert_eq!(
                    curve::pmul(
                        &f,
                        &source,
                        &edge.reverse(&f, &mapped),
                        u128::from(inverse_seven)
                    ),
                    *point
                );
                for q in &source_points {
                    assert_eq!(
                        edge.map.eval(&f, &curve::padd(&f, &source, point, q)),
                        curve::padd(&f, &edge.map.cod, &mapped, &edge.map.eval(&f, q))
                    );
                }
            }
            assert_eq!(seen, target_points.iter().copied().collect::<HashSet<_>>());
            for point in &target_points {
                let reversed = edge.reverse(&f, point);
                assert_eq!(
                    edge.map.eval(&f, &reversed),
                    curve::pmul(&f, &edge.map.cod, point, 7)
                );
                for q in &target_points {
                    assert_eq!(
                        edge.reverse(&f, &curve::padd(&f, &edge.map.cod, point, q)),
                        curve::padd(&f, &source, &reversed, &edge.reverse(&f, q))
                    );
                }
            }
            for n in 0..order {
                assert_eq!(
                    edge.map
                        .eval(&f, &curve::pmul(&f, &source, &g, u128::from(n))),
                    curve::pmul(&f, &edge.map.cod, &image, u128::from(n))
                );
            }
            println!("F101 Eorder{order},short({},{}),kernel{:?},codomain({},{}) dual{:?},scale{},inverse7={inverse_seven};exact cleared curve/both globalx[7],all source/target points,bijection,all pair additions/scalars/dual norms/recovery pass",source.a,source.b,edge.map.ker,edge.map.cod.a,edge.map.cod.b,edge.dual.ker,edge.dual_scale);
            witness.push_str(&format!(
                "{}\t{}\t{order}\t{:?}\t{}\t{}\t{:?}\t{:?}\t{:?}\t{:?}\t{:?}\t{}\t{}\t{}\n",
                source.a,
                source.b,
                edge.map.ker,
                edge.map.cod.a,
                edge.map.cod.b,
                edge.map.num,
                edge.map.den,
                edge.dual.ker,
                edge.dual.num,
                edge.dual.den,
                edge.dual.cod.a,
                edge.dual.cod.b,
                edge.dual_scale
            ));
        }
    }
    println!(
        "E113 long-to-short x shift={shift},short coefficients({},{})",
        second.a, second.b
    );
    if let Ok(path) = std::env::var("CHAINED_SEVEN_WITNESS_OUT") {
        std::fs::write(path, witness).unwrap();
    }
}
