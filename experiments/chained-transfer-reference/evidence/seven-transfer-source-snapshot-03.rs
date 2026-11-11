//! Fixed101 compatible elliptic7 images and HLP2-gluing.
//! This constructs/checks models; the global Jacobian factor proof is separate.
use crate::balanced::{Class, SplitQuotients};
use crate::reference::{FpPoly, HyperellipticCurveP, MumfordDivisorP};
use crate::seven::{checked_isomorphism, construct_edges, SevenEdge};
use isogeny_algos::curve::{self, Curve, Isogeny, Pt, RatIsogeny};
use isogeny_algos::field::{Field, Zp};
use isogeny_algos::fpr::{FpR, ER};
use isogeny_algos::{genus2, poly};
use num_bigint::BigUint;
use num_traits::ToPrimitive;
use std::collections::HashSet;

#[derive(Clone, Copy, Debug)]
struct QuotientChart {
    /// Index of the actual elliptic7 target; gluing can swap components.
    destination: usize,
    /// Internal long cubic x to internal short X=x+shift.
    shift: u64,
    /// Internal short (X,y) to actual target (scale²X,scale³y).
    scale: u64,
}

struct Gluing {
    choice: [usize; 2],
    coefficients: [u64; 7],
    raw_scale: u64,
    charts: [QuotientChart; 2],
}

fn lift_map(f: &FpR, edge: &SevenEdge) -> RatIsogeny<FpR> {
    let m = &edge.map;
    let lift = |x: &u64| f.from_u64(*x);
    RatIsogeny {
        dom: Curve::new(f.from_u64(m.dom.a), f.from_u64(m.dom.b)),
        cod: Curve::new(f.from_u64(m.cod.a), f.from_u64(m.cod.b)),
        deg: m.deg,
        ker: m.ker.iter().map(lift).collect(),
        num: m.num.iter().map(lift).collect(),
        den: m.den.iter().map(lift).collect(),
    }
}

fn image_two_torsion(f: &FpR, edge: &SevenEdge, xs: [ER; 3]) -> [ER; 3] {
    let m = lift_map(f, edge);
    let points = xs.map(|x| Pt::Aff(x, f.zero()));
    for i in 0..3 {
        assert!(curve::on_curve(f, &m.dom, &points[i]));
        assert_ne!(points[i], points[(i + 1) % 3]);
        assert_eq!(f.frobenius(xs[i]), xs[(i + 1) % 3]);
    }
    assert_eq!(curve::padd(f, &m.dom, &points[0], &points[1]), points[2]);
    let images = points.map(|p| m.eval(f, &p));
    let out = images.map(|p| {
        assert!(curve::on_curve(f, &m.cod, &p));
        let Pt::Aff(x, y) = p else {
            panic!("degree7 map killed nonzero2-torsion")
        };
        assert_eq!(y, f.zero());
        x
    });
    for i in 0..3 {
        assert_ne!(out[i], out[(i + 1) % 3]);
        assert_eq!(f.frobenius(out[i]), out[(i + 1) % 3]);
    }
    assert_eq!(curve::padd(f, &m.cod, &images[0], &images[1]), images[2]);
    out
}

fn points(f: &Zp, e: &Curve<u64>) -> Vec<Pt<u64>> {
    let mut out = vec![Pt::Inf];
    for x in 0..101 {
        for y in 0..101 {
            let p = Pt::Aff(x, y);
            if curve::on_curve(f, e, &p) {
                out.push(p);
            }
        }
    }
    out
}

fn scale_point(f: &Zp, p: Pt<u64>, u: u64) -> Pt<u64> {
    match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => Pt::Aff(f.mul(f.sq(u), x), f.mul(f.pow(u, 3), y)),
    }
}

fn checked_quotient_chart(
    f: &Zp,
    cubic: &[u64; 4],
    destinations: [&Curve<u64>; 2],
) -> QuotientChart {
    let short = genus2::cubic_to_short(f, &cubic.to_vec());
    let candidates = destinations
        .iter()
        .enumerate()
        .filter_map(|(i, target)| checked_isomorphism(f, &short, target).map(|u| (i, u)))
        .collect::<Vec<_>>();
    assert_eq!(
        candidates.len(),
        1,
        "actual unique quotient/target isomorphism"
    );
    let (destination, u) = candidates[0];
    let target = destinations[destination];
    let source_points = points(f, &short);
    let target_points = points(f, target);
    assert_eq!(source_points.len(), [109, 113][destination]);
    assert_eq!(target_points.len(), source_points.len());
    let images = source_points
        .iter()
        .map(|p| {
            let q = scale_point(f, *p, u);
            assert!(curve::on_curve(f, target, &q));
            assert_eq!(scale_point(f, q, f.inv(u)), *p);
            q
        })
        .collect::<HashSet<_>>();
    assert_eq!(images, target_points.into_iter().collect());
    QuotientChart {
        destination,
        shift: f.div(cubic[2], 3),
        scale: u,
    }
}

fn construct_gluing(choice: [usize; 2], edges: [&SevenEdge; 2]) -> Option<Gluing> {
    let f = Zp::new(101);
    let k = FpR::from_modulus(101, &[56, 13, 6, 1]);
    let a0 = k.gen();
    let a1 = k.frobenius(a0);
    let a2 = k.frobenius(a1);
    assert_eq!(k.frobenius(a2), a0);
    let roots = [a0, a1, a2];
    let left = roots.map(|a| k.add(a, k.from_u64(2)));
    let right = roots.map(|a| k.add(k.div(k.from_u64(56), a), k.from_u64(38)));
    let images = [
        image_two_torsion(&k, edges[0], left),
        image_two_torsion(&k, edges[1], right),
    ];
    let raw3 = genus2::glue(&k, images[0], images[1])
        .expect("nonisomorphic elliptic factors with Galois-matched2-torsion");
    let raw = raw3
        .iter()
        .map(|c| {
            k.project(*c)
                .expect("HLP coefficients must descend to F101")
        })
        .collect::<Vec<_>>();
    // Independently published inventory crypto#3920 at cc3229d103638190a08d4948b103004cbd567768.
    // Its E2 A/B labels are reversed relative to our predeclared lexical kernel order.
    let expected = [
        [[38, 0, 48, 0, 9, 0, 46], [32, 0, 26, 0, 49, 0, 41]],
        [[19, 0, 86, 0, 34, 0, 79], [87, 0, 15, 0, 13, 0, 21]],
    ];
    assert_eq!(raw, expected[choice[0]][choice[1]]);
    assert_eq!(raw.len(), 7);
    assert_ne!(raw[0], 0);
    assert!([1, 3, 5].iter().all(|i| raw[*i] == 0));
    assert_eq!(poly::gcd(&f, &raw, &poly::derivative(&f, &raw)), vec![1]);
    let lpoly = genus2::lpoly(&f, &raw);
    assert_eq!(lpoly, genus2::LPoly::product(-7, -11, 101));
    assert_eq!(lpoly.jac_order(101), 12317);
    let Some(rho) = (1..101).find(|x| f.sq(*x) == raw[6]) else {
        println!("retained gluing{choice:?} raw{raw:?}:nonsquare leading unsupported,no retwist");
        return None;
    };
    let coefficients: [u64; 7] = raw
        .iter()
        .map(|x| f.div(*x, raw[6]))
        .collect::<Vec<_>>()
        .try_into()
        .unwrap();
    let [b, _, a4, _, a2, _, _] = coefficients;
    let splits = match SplitQuotients::new(101, [b, a4, a2]) {
        Ok(s) => s,
        Err(e) => {
            println!("retained gluing{choice:?} raw{raw:?},rho{rho},monic{coefficients:?}:unsupported {e};no model substitution");
            return None;
        }
    };
    let cubics = [[b, a4, a2, 1], [f.sq(b), f.mul(a2, b), a4, 1]];
    for (actual, expected) in [&splits.first.base.f, &splits.second.base.f]
        .into_iter()
        .zip(cubics)
    {
        assert_eq!(
            actual
                .coeffs
                .iter()
                .map(|c| c.to_u64().unwrap())
                .collect::<Vec<_>>(),
            expected
        );
    }
    let destinations = [&edges[0].map.cod, &edges[1].map.cod];
    let charts = cubics.map(|c| checked_quotient_chart(&f, &c, destinations));
    assert_eq!(
        charts.map(|c| c.destination),
        [1, 0],
        "HLP quotient component swap"
    );
    for i in 0..3 {
        let quotient_x: [ER; 2] = charts.map(|c| {
            k.sub(
                k.mul(images[c.destination][i], k.from_u64(f.inv(f.sq(c.scale)))),
                k.from_u64(c.shift),
            )
        });
        assert_eq!(
            k.mul(quotient_x[0], quotient_x[1]),
            k.from_u64(b),
            "actual paired2-torsion pullbacks have the SAME quadratic support"
        );
    }
    println!("gluing{choice:?} raw{raw:?},rho{rho},monic{coefficients:?},charts{charts:?},L{lpoly:?};descent,smoothness,actual quotient109/113 bijections,matched2-kernel support pass");
    Some(Gluing {
        choice,
        coefficients,
        raw_scale: rho,
        charts,
    })
}

fn gluing_inventory() -> Vec<Gluing> {
    let f = Zp::new(101);
    let first = construct_edges(&f, &Curve::new(1, 46));
    let second = construct_edges(&f, &Curve::new(44, 21));
    let mut out = vec![];
    for (i, a) in first.iter().enumerate() {
        for (j, b) in second.iter().enumerate() {
            if let Some(model) = construct_gluing([i, j], [a, b]) {
                out.push(model);
            }
        }
    }
    out
}

#[test]
fn actual_seven_image_gluing_inventory_and_kernel_support() {
    let models = gluing_inventory();
    assert_eq!(models.len(), 2);
    let m = &models[0];
    assert_eq!(m.choice, [1, 0]);
    assert_eq!(m.coefficients, [68, 0, 42, 0, 26, 0, 1]);
    assert_eq!(models[1].coefficients, [33, 0, 44, 0, 92, 0, 1]);
    println!("selected first supported choice{:?},monic{:?},raw scale{},charts{:?};{} supported models;global factor/actual Jacobian7/duals still next",m.choice,m.coefficients,m.raw_scale,m.charts,models.len());
}

fn short_point(f: &Zp, base: &HyperellipticCurveP, d: &MumfordDivisorP, shift: u64) -> Pt<u64> {
    d.validate(base).unwrap();
    if d.is_identity() {
        return Pt::Inf;
    }
    assert_eq!(d.u.degree(), Some(1));
    assert_eq!(d.u.coeff(1), BigUint::from(1_u64));
    Pt::Aff(
        f.add(f.neg(d.u.coeff(0).to_u64().unwrap()), shift),
        d.v.coeff(0).to_u64().unwrap(),
    )
}

fn long_point(f: &Zp, base: &HyperellipticCurveP, p: Pt<u64>, shift: u64) -> MumfordDivisorP {
    match p {
        Pt::Inf => MumfordDivisorP::identity(base.p.clone()),
        Pt::Aff(x, y) => MumfordDivisorP::try_from_point(
            base,
            &BigUint::from(f.sub(x, shift)),
            &BigUint::from(y),
        )
        .unwrap(),
    }
}

/// Rational evaluation of the prospective globally factored map.
/// The written full geometric2-kernel inclusion is an additional obligation;
/// finite-group halving by itself does not construct an algebraic isogeny.
struct SevenTransfer {
    fp: Zp,
    model: Gluing,
    source: SplitQuotients,
    target: SplitQuotients,
    edges: [SevenEdge; 2],
}
impl SevenTransfer {
    fn new() -> Self {
        let model = gluing_inventory().into_iter().next().unwrap();
        assert_eq!(model.choice, [1, 0]);
        assert_eq!(model.coefficients, [68, 0, 42, 0, 26, 0, 1]);
        let fp = Zp::new(101);
        let first = construct_edges(&fp, &Curve::new(1, 46))
            .into_iter()
            .nth(model.choice[0])
            .unwrap();
        let second = construct_edges(&fp, &Curve::new(44, 21))
            .into_iter()
            .nth(model.choice[1])
            .unwrap();
        let source = SplitQuotients::new(101, [56, 13, 6]).unwrap();
        let target = SplitQuotients::new(
            101,
            [
                model.coefficients[0],
                model.coefficients[2],
                model.coefficients[4],
            ],
        )
        .unwrap();
        Self {
            fp,
            model,
            source,
            target,
            edges: [first, second],
        }
    }

    /// Coordinates ordered by the original elliptic factors109,113.
    fn source_coordinates(&self, d: &Class) -> super::Result<[Pt<u64>; 2]> {
        let (a, b) = self.source.norms(d)?;
        Ok([
            short_point(&self.fp, &self.source.first.base, &a, 2),
            short_point(&self.fp, &self.source.second.base, &b, 38),
        ])
    }

    /// Actual Kohel target coordinates,ordered by109,113 despite quotient swap.
    fn target_coordinates(&self, d: &Class) -> super::Result<[Pt<u64>; 2]> {
        let (a, b) = self.target.norms(d)?;
        let ds = [a, b];
        let bases = [&self.target.first.base, &self.target.second.base];
        let mut out = [Pt::Inf; 2];
        for i in 0..2 {
            let c = self.model.charts[i];
            let p = short_point(&self.fp, bases[i], &ds[i], c.shift);
            out[c.destination] = scale_point(&self.fp, p, c.scale);
            assert!(curve::on_curve(
                &self.fp,
                &self.edges[c.destination].map.cod,
                &out[c.destination]
            ));
        }
        Ok(out)
    }

    fn forward(&self, d: &Class) -> super::Result<Class> {
        let f = &self.fp;
        let points = self.source_coordinates(d)?;
        let images: [Pt<u64>; 2] = std::array::from_fn(|i| {
            let n = [109_u64, 113][i];
            let e = &self.edges[i];
            assert_eq!(
                curve::pmul(f, &e.map.dom, &points[i], u128::from(n)),
                Pt::Inf
            );
            let half = curve::pmul(f, &e.map.dom, &points[i], u128::from(n.div_ceil(2)));
            e.map.eval(f, &half)
        });
        let bases = [&self.target.first.base, &self.target.second.base];
        let components: [MumfordDivisorP; 2] = std::array::from_fn(|i| {
            let c = self.model.charts[i];
            let internal = scale_point(f, images[c.destination], f.inv(c.scale));
            long_point(f, bases[i], internal, c.shift)
        });
        self.target.pulls(&components[0], &components[1])
    }

    fn dual(&self, d: &Class) -> super::Result<Class> {
        let f = &self.fp;
        let points = self.target_coordinates(d)?;
        let images: [Pt<u64>; 2] = std::array::from_fn(|i| {
            let n = [109_u64, 113][i];
            let e = &self.edges[i];
            assert_eq!(
                curve::pmul(f, &e.map.cod, &points[i], u128::from(n)),
                Pt::Inf
            );
            let half = curve::pmul(f, &e.map.cod, &points[i], u128::from(n.div_ceil(2)));
            e.reverse(f, &half)
        });
        self.source.pulls(
            &long_point(f, &self.source.first.base, images[0], 2),
            &long_point(f, &self.source.second.base, images[1], 38),
        )
    }
}

fn class_key(d: &Class) -> (Vec<u64>, Vec<u64>, u8) {
    let (u, v, plus) = d.components();
    let c = |p: &FpPoly| p.coeffs.iter().map(|c| c.to_u64().unwrap()).collect();
    (c(u), c(v), plus)
}

#[test]
fn seven_transfer_complete_prime109_source_and_direct_coordinates() {
    let t = SevenTransfer::new();
    let base = &t.source.first.base;
    let g = MumfordDivisorP::try_from_point(base, &BigUint::from(0_u64), &BigUint::from(37_u64))
        .unwrap();
    let generator = t.forward(&t.source.first.pull(&g).unwrap()).unwrap();
    assert_ne!(generator, t.target.first.balanced.zero());
    for n in 0..109_u64 {
        let point = g.checked_scalar_mul(&BigUint::from(n), base).unwrap();
        let d = t.source.first.pull(&point).unwrap();
        let image = t.forward(&d).unwrap();
        assert_eq!(image, t.target.first.balanced.mul(&generator, n).unwrap());
        let reversed = t.dual(&image).unwrap();
        assert_eq!(reversed, t.source.first.balanced.mul(&d, 7).unwrap());
        assert_eq!(t.source.first.balanced.mul(&reversed, 78).unwrap(), d);
        let (a, b) = t.source.norms(&reversed).unwrap();
        assert!(b.is_identity());
        assert_eq!(
            a,
            point
                .checked_scalar_mul(&BigUint::from(14_u64), base)
                .unwrap()
        );
        assert_eq!(
            a.checked_scalar_mul(&BigUint::from(39_u64), base).unwrap(),
            point
        );
        let p = short_point(&t.fp, base, &point, 2);
        let alpha = t.edges[0].map.eval(&t.fp, &p);
        assert_eq!(
            t.target_coordinates(&image).unwrap(),
            [curve::pmul(&t.fp, &t.edges[0].map.cod, &alpha, 2), Pt::Inf]
        );
    }
    println!("PASS all109 source scalars,nonzero image,Jacobian dual[7]/inverse78,source norm[14]/inverse39 and actual target coordinates([2]alpha(P),0);global geometric factor remains separately checked");
}

#[test]
fn seven_transfer_both_full_rational_domains_duals_and_additions() {
    let t = SevenTransfer::new();
    let source = &t.source.first.balanced;
    let target = &t.target.first.balanced;
    let xs = source.classes().unwrap();
    let ys = target.classes().unwrap();
    assert_eq!((xs.len(), ys.len()), (12317, 12317));
    let images = xs.iter().map(|d| t.forward(d).unwrap()).collect::<Vec<_>>();
    let duals = ys.iter().map(|d| t.dual(d).unwrap()).collect::<Vec<_>>();
    assert_eq!(
        images.iter().map(class_key).collect::<HashSet<_>>(),
        ys.iter().map(class_key).collect()
    );
    assert_eq!(
        duals.iter().map(class_key).collect::<HashSet<_>>(),
        xs.iter().map(class_key).collect()
    );
    for i in 0..xs.len() {
        let j = (7919 * i + 37) % xs.len();
        assert_eq!(t.dual(&images[i]).unwrap(), source.mul(&xs[i], 7).unwrap());
        assert_eq!(
            t.forward(&duals[i]).unwrap(),
            target.mul(&ys[i], 7).unwrap()
        );
        assert_eq!(
            t.forward(&source.add(&xs[i], &xs[j]).unwrap()).unwrap(),
            target.add(&images[i], &images[j]).unwrap()
        );
        assert_eq!(
            t.dual(&target.add(&ys[i], &ys[j]).unwrap()).unwrap(),
            source.add(&duals[i], &duals[j]).unwrap()
        );
    }
    println!("PASS both complete12317 rational domains,actual forward/dual maps,full bijections,paired additivity,both signed dual[7],canonical prime-field outputs;not a benchmark or a global-geometric proof by enumeration");
}
