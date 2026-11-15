//! Adjoint of the fixed first transfer, using the accepted direct norms and
//! pullbacks and existing prime-field Kohel evaluation. Reference only in test.
use super::prime_field_psi::{key, PrimeFieldPsi};
use super::quartic_norm::DirectQuartic;
use super::quartic_pullback::{rational_points, Pullback};
use crate::balanced::{Balanced, Class};
use isogeny_algos::curve::{self, Curve, Isogeny, Pt, RatIsogeny};
use isogeny_algos::field::{Field, Zp};
use isogeny_algos::kernel::kohel::kohel;
use std::collections::HashSet;

pub(super) struct PrimeFieldAdjoint {
    fp: Zp,
    source: Balanced,
    target: Balanced,
    norms: [DirectQuartic; 2],
    dual: [RatIsogeny<Zp>; 2],
    pulls: [Pullback; 2],
}

impl PrimeFieldAdjoint {
    pub(super) fn new() -> Self {
        let fp = Zp::new(101);
        let dual = [
            kohel(&fp, &Curve::new(26, 58), &vec![58, 26, 58, 1], 7),
            kohel(&fp, &Curve::new(69, 50), &vec![29, 88, 45, 1], 7),
        ];
        let destinations = [Curve::new(1, 46), Curve::new(44, 21)];
        assert_eq!(dual[0].cod, Curve::new(78, 72));
        assert_eq!(dual[1].cod, Curve::new(99, 68));
        for i in 0..2 {
            assert_eq!(fp.mul(fp.pow(29, 4), dual[i].cod.a), destinations[i].a);
            assert_eq!(fp.mul(fp.pow(29, 6), dual[i].cod.b), destinations[i].b);
        }
        Self {
            fp,
            source: Balanced::new(101, &[95, 26, 19, 27, 94, 91, 1]).unwrap(),
            target: Balanced::new(101, &[31, 75, 74, 54, 71, 55, 1]).unwrap(),
            norms: [DirectQuartic::t1(0), DirectQuartic::t1(1)],
            dual,
            pulls: [Pullback::fixed(0, 0), Pullback::fixed(0, 1)],
        }
    }

    pub(super) fn evaluate(&self, d: &Class) -> Result<Class, String> {
        self.source.check(d)?;
        let mut components = Vec::with_capacity(2);
        for i in 0..2 {
            let point = self.norms[i].norm(d)?.0;
            let quarter = curve::pmul(&self.fp, &self.dual[i].dom, &point, [82, 85][i]);
            let transported = match self.dual[i].eval(&self.fp, &quarter) {
                Pt::Inf => Pt::Inf,
                Pt::Aff(x, y) => Pt::Aff(
                    self.fp.mul(self.fp.sq(29), x),
                    self.fp.mul(self.fp.pow(29, 3), y),
                ),
            };
            components.push(self.pulls[i].pull(&transported)?.0);
        }
        self.target.add(&components[0], &components[1])
    }
}

#[test]
fn complete_adjoint_and_both_norms_using_only_prime_field_evaluation() {
    let direct = PrimeFieldAdjoint::new();
    let forward = PrimeFieldPsi::new();
    let old = super::SevenChain::new();
    for i in 0..2 {
        let reference = &old.t.edges[i];
        assert_eq!(direct.dual[i].dom, reference.dual.dom);
        assert_eq!(direct.dual[i].cod, reference.dual.cod);
        assert_eq!(direct.dual[i].num, reference.dual.num);
        assert_eq!(direct.dual[i].den, reference.dual.den);
        assert_eq!(direct.dual[i].ker, reference.dual.ker);
        assert_eq!(reference.dual_scale, 29);
        let points = rational_points(&direct.fp, &direct.dual[i].dom);
        assert_eq!(points.len(), [109, 113][i]);
        let embedded_pull = Pullback::fixed(1, i);
        for p in points {
            let embedded = embedded_pull.pull(&p).unwrap().0;
            let endpoint = direct.pulls[i]
                .pull(&reference.reverse(&direct.fp, &p))
                .unwrap()
                .0;
            assert_eq!(
                direct.evaluate(&embedded).unwrap(),
                endpoint,
                "reverse embedded source{i}/{p:?}"
            );
        }
    }
    let all = direct.source.classes().unwrap();
    assert_eq!(all.len(), 12317);
    let mut images = Vec::with_capacity(all.len());
    let mut distinct = HashSet::new();
    for (i, d) in all.iter().enumerate() {
        let result = direct.evaluate(d).unwrap();
        assert_eq!(
            result,
            old.dual_reference(d).unwrap(),
            "adjoint old output{i}"
        );
        assert!(distinct.insert(key(&result)), "adjoint bijection{i}");
        assert_eq!(
            forward.forward(&result).unwrap(),
            direct.source.mul(d, 7).unwrap(),
            "forward after adjoint norm7 target{i}"
        );
        images.push(result);
    }
    assert_eq!(distinct.len(), 12317);
    for (i, d) in all.iter().enumerate() {
        let j = (37 * i + 7) % all.len();
        assert_eq!(
            direct
                .evaluate(&direct.source.add(d, &all[j]).unwrap())
                .unwrap(),
            direct.target.add(&images[i], &images[j]).unwrap(),
            "adjoint paired sum{i}"
        );
        assert_eq!(
            direct.evaluate(&direct.source.neg(d).unwrap()).unwrap(),
            direct.target.neg(&images[i]).unwrap(),
            "adjoint negation{i}"
        );
    }
    let sources = direct.target.classes().unwrap();
    assert_eq!(sources.len(), 12317);
    for (i, d) in sources.iter().enumerate() {
        assert_eq!(
            direct.evaluate(&forward.forward(d).unwrap()).unwrap(),
            direct.target.mul(d, 7).unwrap(),
            "adjoint after forward norm7 source{i}"
        );
    }
    assert_eq!(
        direct.evaluate(&direct.source.zero()).unwrap(),
        direct.target.zero()
    );
    assert!(direct.evaluate(&direct.target.zero()).is_err());
    assert!(direct.dual.iter().all(|map| map.degree() == 7));
    println!("PASS pure F101 adjoint:first-transfer all12317 exact olddual outputs/bijection/paired sums/negations/identity/model controls;both domains all12317 forward-adjoint norm7 identities;selected dual coefficient identity and checked scale29. Existing T1norm/T0pullback/Kohel/Balanced engines reused;API constructor/evaluator no Richelot or extension field. Rational-point quarter formula,global geometry remains written;no timing claim");
}
