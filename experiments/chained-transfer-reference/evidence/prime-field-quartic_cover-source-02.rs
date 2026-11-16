//! Bounded reconstruction of an existing fixed quotient, using only existing
//! field, polynomial, elliptic and Richelot arithmetic. No timing benchmark.
use super::SevenChain;
use isogeny_algos::curve::{self, Pt};
use isogeny_algos::field::{Field, Zp};
use isogeny_algos::poly;
use num_traits::ToPrimitive;
use std::collections::BTreeMap;
#[path = "quartic_lagrange.rs"]
mod existing_interpolation;

fn rational_reconstruction(f: &Zp, xs: &[u64], ys: &[u64]) -> (Vec<u64>, Vec<u64>) {
    let mut r0 = poly::from_roots(f, xs);
    let mut r1 = existing_interpolation::lagrange(f, xs, ys);
    poly::trim(f, &mut r1);
    let mut t0 = vec![f.zero()];
    let mut t1 = vec![f.one()];
    while poly::deg(f, &r1) > 4 {
        let (quotient, remainder) = poly::divrem(f, &r0, &r1);
        let t = poly::sub(f, &t0, &poly::mul(f, &quotient, &t1));
        (r0, r1) = (r1, remainder);
        (t0, t1) = (t1, t);
    }
    assert!(poly::deg(f, &r1) >= 0);
    assert!(poly::deg(f, &t1) <= 4);
    assert_eq!(poly::gcd(f, &r1, &t1), vec![f.one()]);
    let scale = f.inv(*t1.last().unwrap());
    (poly::scale(f, &r1, scale), poly::scale(f, &t1, scale))
}

fn square_denominator(f: &Zp, d: &[u64]) -> Vec<u64> {
    let half = f.inv(f.from_u64(2));
    let q = match d.len() {
        1 => vec![f.one()],
        3 => vec![f.mul(d[1], half), f.one()],
        5 => {
            let q1 = f.mul(d[3], half);
            let q0 = f.mul(f.sub(d[2], f.mul(q1, q1)), half);
            vec![q0, q1, f.one()]
        }
        _ => panic!("predicted degree0/2/4 monic square denominator failed: {d:?}"),
    };
    assert_eq!(poly::mul(f, &q, &q), d);
    q
}

struct Reconstructed {
    n: Vec<u64>,
    q: Vec<u64>,
    m: Vec<u64>,
    infinity: Pt<u64>,
}

fn reconstruct_t0_cover(component: usize) -> Reconstructed {
    reconstruct_cover(0, component)
}

fn reconstruct_cover(model: usize, component: usize) -> Reconstructed {
    assert!(model < 2 && component < 2);
    let c = SevenChain::new();
    let f = &c.t.fp;
    let r = if model == 0 { &c.r0 } else { &c.r1 };
    let e = if model == 0 {
        &c.t.edges[component].map.dom
    } else {
        &c.t.edges[component].map.cod
    };
    let all = r.target.classes().unwrap();
    let coordinates = |d: &crate::balanced::Class| {
        let old = r.dual_closed(d).unwrap();
        if model == 0 {
            c.t.source_coordinates(&old).unwrap()
        } else {
            c.t.target_coordinates(&old).unwrap()
        }
    };
    assert_eq!(all.len(), 12317);
    let delta = all
        .iter()
        .find(|d| {
            let (u, _, n) = d.components();
            u.degree() == Some(0) && n == 2
        })
        .unwrap();
    let delta_image = coordinates(delta)[component];
    let q = curve::pmul(f, e, &delta_image, [55, 57][component]);
    assert_eq!(curve::pmul(f, e, &q, 2), delta_image);
    let minus_q = curve::neg(f, &q);
    let mut samples = BTreeMap::new();
    let mut finite = Vec::new();
    let mut poles = Vec::new();
    for d in &all {
        let (u, v, n) = d.components();
        if u.degree() != Some(1) || n != 1 {
            continue;
        }
        let x = f.neg(u.coeffs[0].to_u64().unwrap());
        let y = v.coeffs[0].to_u64().unwrap();
        assert_ne!(y, 0);
        let h = coordinates(d)[component];
        let centred = curve::padd(f, e, &h, &minus_q);
        assert!(curve::on_curve(f, e, &centred));
        match centred {
            Pt::Inf => poles.push((x, y)),
            Pt::Aff(xe, ye) => {
                let ratio = f.div(ye, y);
                if let Some(prior) = samples.insert(x, (xe, ratio)) {
                    assert_eq!(prior, (xe, ratio), "hyperelliptic involution at x{x}");
                }
                finite.push((x, y, xe, ye));
            }
        }
    }
    assert_eq!(finite.len() + poles.len(), 118);
    let xs: Vec<_> = samples.keys().copied().collect();
    let ys: Vec<_> = samples.values().map(|s| s.0).collect();
    assert!(xs.len() > 16);
    let (n, denominator) = rational_reconstruction(f, &xs, &ys);
    let qpoly = square_denominator(f, &denominator);
    let ms: Vec<_> = samples
        .iter()
        .map(|(&x, &(_, ratio))| f.mul(ratio, f.pow(poly::eval(f, &qpoly, x), 3)))
        .collect();
    let mut m = existing_interpolation::lagrange(f, &xs, &ms);
    poly::trim(f, &mut m);
    assert!(poly::deg(f, &n) <= 4 && poly::deg(f, &qpoly) <= 2);
    assert!(
        (0..=3).contains(&poly::deg(f, &m)),
        "predicted ordinate degree failed: {m:?}"
    );
    let sextic = if model == 0 {
        vec![31, 75, 74, 54, 71, 55, 1]
    } else {
        vec![95, 26, 19, 27, 94, 91, 1]
    };
    let q2 = poly::mul(f, &qpoly, &qpoly);
    let q4 = poly::mul(f, &q2, &q2);
    let q6 = poly::mul(f, &q4, &q2);
    let n2 = poly::mul(f, &n, &n);
    let rhs = poly::add(
        f,
        &poly::add(
            f,
            &poly::mul(f, &n2, &n),
            &poly::scale(f, &poly::mul(f, &n, &q4), e.a),
        ),
        &poly::scale(f, &q6, e.b),
    );
    let lhs = poly::mul(f, &sextic, &poly::mul(f, &m, &m));
    assert_eq!(lhs, rhs, "exact polynomial curve identity");
    assert_eq!(poly::gcd(f, &n, &qpoly), vec![1]);
    assert_eq!(
        poly::gcd(f, &sextic, &poly::derivative(f, &sextic)),
        vec![1]
    );
    assert!(curve::is_smooth(f, e));
    assert_eq!(poly::deg(f, &n).max(poly::deg(f, &denominator)), 4);
    let derivative_numerator = poly::sub(
        f,
        &poly::mul(f, &poly::derivative(f, &n), &denominator),
        &poly::mul(f, &n, &poly::derivative(f, &denominator)),
    );
    assert!(poly::deg(f, &derivative_numerator) >= 0);
    for &(x, y, xe, ye) in &finite {
        let qx = poly::eval(f, &qpoly, x);
        assert_ne!(qx, 0);
        assert_eq!(f.div(poly::eval(f, &n, x), f.pow(qx, 2)), xe);
        assert_eq!(f.div(f.mul(y, poly::eval(f, &m, x)), f.pow(qx, 3)), ye);
        println!("certificate {model} {component} {x} {y} {xe} {ye}");
    }
    for &(x, _) in &poles {
        assert_eq!(poly::eval(f, &qpoly, x), 0);
    }
    println!("PASS T{model}/component{component} quartic exactidentity/degree4/separable/gcd/smoothness;N{n:?},Q{qpoly:?},M{m:?},infinity+{q:?},finite{},poles{:?}. Global identification still requires the separate degree certificate and independent replay;no timing claim", finite.len(),poles);
    Reconstructed {
        n,
        q: qpoly,
        m,
        infinity: q,
    }
}

#[test]
fn reconstruct_first_t0_e109_quartic_cover() {
    let result = reconstruct_t0_cover(0);
    assert_eq!(result.n, [14, 0, 88, 97, 14]);
    assert_eq!(result.q, [63, 0, 1]);
    assert_eq!(result.m, [41, 40, 69, 73]);
    assert_eq!(result.infinity, Pt::Aff(14, 73));
}

#[test]
fn reconstruct_second_t0_e113_quartic_cover() {
    let result = reconstruct_t0_cover(1);
    println!(
        "second cover frozen candidate N{:?} Q{:?} M{:?} infinity{:?}",
        result.n, result.q, result.m, result.infinity
    );
}

#[test]
fn reconstruct_both_t1_elliptic_quartic_covers() {
    for component in 0..2 {
        let result = reconstruct_cover(1, component);
        println!(
            "T1 component{component} frozen candidate N{:?} Q{:?} M{:?} infinity{:?}",
            result.n, result.q, result.m, result.infinity
        );
    }
}
