//! Prime-field second hop and compressed two-hop evaluation. Both use the
//! accepted direct norm/pullback engines; reference contexts occur in tests.
use super::SuccessorChain;
use crate::balanced::{Balanced, Class};
use crate::nonsplit::map::seven_glue::torsion::chain::{
    prime_field_psi::PrimeFieldPsi,
    quartic_norm::DirectQuartic,
    quartic_pullback::{rational_points, Pullback},
    SevenChain,
};
use isogeny_algos::curve::{self, Curve, Isogeny, RatIsogeny};
use isogeny_algos::field::Zp;
use isogeny_algos::kernel::kohel::kohel;
use num_traits::ToPrimitive;
use std::collections::{HashMap, HashSet};

pub(super) struct PrimeFieldPipeline {
    fp: Zp,
    source: Balanced,
    target: Balanced,
    norms: [DirectQuartic; 2],
    stages: Vec<[RatIsogeny<Zp>; 2]>,
    pulls: [Pullback; 2],
}

fn beta(fp: &Zp) -> [RatIsogeny<Zp>; 2] {
    let maps = [
        kohel(fp, &Curve::new(26, 58), &vec![99, 94, 75, 1], 7),
        kohel(fp, &Curve::new(69, 50), &vec![53, 19, 40, 1], 7),
    ];
    assert_eq!(maps[0].cod, Curve::new(59, 27));
    assert_eq!(maps[1].cod, Curve::new(23, 7));
    maps
}

impl PrimeFieldPipeline {
    pub(super) fn second() -> Self {
        let fp = Zp::new(101);
        let stages = vec![beta(&fp)];
        Self {
            fp,
            source: Balanced::new(101, &[95, 26, 19, 27, 94, 91, 1]).unwrap(),
            target: Balanced::new(101, &[95, 93, 43, 39, 92, 17, 1]).unwrap(),
            norms: [DirectQuartic::t1(0), DirectQuartic::t1(1)],
            stages,
            pulls: [Pullback::fixed(2, 0), Pullback::fixed(2, 1)],
        }
    }

    pub(super) fn two_hop() -> Self {
        let fp = Zp::new(101);
        let alpha = [
            kohel(&fp, &Curve::new(1, 46), &vec![72, 100, 35, 1], 7),
            kohel(&fp, &Curve::new(44, 21), &vec![59, 46, 8, 1], 7),
        ];
        let stages = vec![alpha, beta(&fp)];
        Self {
            fp,
            source: Balanced::new(101, &[31, 75, 74, 54, 71, 55, 1]).unwrap(),
            target: Balanced::new(101, &[95, 93, 43, 39, 92, 17, 1]).unwrap(),
            norms: [DirectQuartic::first(), DirectQuartic::second()],
            stages,
            pulls: [Pullback::fixed(2, 0), Pullback::fixed(2, 1)],
        }
    }

    pub(super) fn evaluate(&self, d: &Class) -> Result<Class, String> {
        self.source.check(d)?;
        let mut components = Vec::with_capacity(2);
        for i in 0..2 {
            let point = self.norms[i].norm(d)?.0;
            let mut current = curve::pmul(&self.fp, &self.stages[0][i].dom, &point, [82, 85][i]);
            for stage in &self.stages {
                current = stage[i].eval(&self.fp, &current);
            }
            components.push(self.pulls[i].pull(&current)?.0);
        }
        self.target.add(&components[0], &components[1])
    }
}

fn key(d: &Class) -> (Vec<u64>, Vec<u64>, u8) {
    let (u, v, n) = d.components();
    let coefficients =
        |p: &crate::reference::FpPoly| p.coeffs.iter().map(|c| c.to_u64().unwrap()).collect();
    (coefficients(u), coefficients(v), n)
}

fn complete(pipe: &PrimeFieldPipeline, expected: impl Fn(&Class) -> Class) {
    let all = pipe.source.classes().unwrap();
    assert_eq!(all.len(), 12317);
    let mut images = Vec::with_capacity(all.len());
    let mut distinct = HashSet::new();
    for (i, d) in all.iter().enumerate() {
        let image = pipe.evaluate(d).unwrap();
        assert_eq!(
            image,
            expected(d),
            "stages{} concrete output{i}",
            pipe.stages.len()
        );
        assert!(distinct.insert(key(&image)));
        images.push(image);
    }
    assert_eq!(distinct.len(), 12317);
    for (i, d) in all.iter().enumerate() {
        let j = (37 * i + 7) % all.len();
        assert_eq!(
            pipe.evaluate(&pipe.source.add(d, &all[j]).unwrap())
                .unwrap(),
            pipe.target.add(&images[i], &images[j]).unwrap()
        );
        assert_eq!(
            pipe.evaluate(&pipe.source.neg(d).unwrap()).unwrap(),
            pipe.target.neg(&images[i]).unwrap()
        );
        if *d != pipe.source.zero() {
            assert_ne!(
                pipe.target.mul(&images[i], 4).unwrap(),
                images[i],
                "wrong quarter must reject"
            );
        }
    }
    assert_eq!(
        pipe.evaluate(&pipe.source.zero()).unwrap(),
        pipe.target.zero()
    );
    assert!(pipe.evaluate(&pipe.target.zero()).is_err());
    assert!(pipe.stages.iter().flatten().all(|map| map.degree() == 7));
}

#[test]
fn prime_field_pipeline_second_hop_all_classes_match_old_second() {
    let pipe = PrimeFieldPipeline::second();
    let old = SuccessorChain::new();
    for i in 0..2 {
        let a = &pipe.stages[0][i];
        let b = &old.s.beta[i].map;
        assert_eq!(
            (&a.dom, &a.cod, &a.ker, &a.num, &a.den),
            (&b.dom, &b.cod, &b.ker, &b.num, &b.den)
        );
    }
    complete(&pipe, |d| old.forward_reference(d).unwrap());
    println!("PASS pure F101 second Jacobian hop:all12317 exact oldsecond outputs/bijection/paired sums/negations/identity/model/wrongquarter controls;actual beta coefficient identity;one pair T1norms/public quarters/T2pulls,existing engines,no Richelot or extension field in API,no timing claim");
}

#[test]
fn prime_field_pipeline_compressed_two_hop_all_classes_and_source_controls() {
    let pipe = PrimeFieldPipeline::two_hop();
    let first = PrimeFieldPsi::new();
    let second = PrimeFieldPipeline::second();
    let old = SuccessorChain::new();
    let old_first = SevenChain::new();
    complete(&pipe, |d| {
        let middle = first.forward(d).unwrap();
        let retained = old.forward_reference(&middle).unwrap();
        assert_eq!(second.evaluate(&middle).unwrap(), retained);
        retained
    });
    for component in 0..2 {
        let source = Pullback::fixed(0, component);
        let e = &pipe.stages[0][component].dom;
        let points = rational_points(&pipe.fp, e);
        let order = [109_u64, 113][component];
        assert_eq!(points.len(), usize::try_from(order).unwrap());
        let inverse = [104_u128, 64][component];
        assert_eq!(196 * inverse % u128::from(order), 1);
        let mut outputs = Vec::new();
        for p in &points {
            let embedded = source.pull(p).unwrap().0;
            let endpoint = pipe.evaluate(&embedded).unwrap();
            let alpha = pipe.stages[0][component].eval(&pipe.fp, p);
            let beta_alpha = pipe.stages[1][component].eval(&pipe.fp, &alpha);
            assert_eq!(endpoint, pipe.pulls[component].pull(&beta_alpha).unwrap().0);
            let reversed = old_first
                .dual(&old.dual_reference(&endpoint).unwrap())
                .unwrap();
            let norm = [DirectQuartic::first(), DirectQuartic::second()][component]
                .norm(&reversed)
                .unwrap()
                .0;
            assert_eq!(norm, curve::pmul(&pipe.fp, e, p, 196));
            assert_eq!(curve::pmul(&pipe.fp, e, &norm, inverse), *p);
            outputs.push(endpoint);
        }
        let indices: HashMap<_, _> = points.iter().enumerate().map(|(i, p)| (*p, i)).collect();
        for k in 0..order {
            let p = curve::pmul(&pipe.fp, e, &points[1], u128::from(k));
            assert_eq!(
                outputs[indices[&p]],
                pipe.target.mul(&outputs[1], k).unwrap()
            );
        }
    }
    println!("PASS compressed pure F101 whole twohop:all12317 equals oldsecond after accepted purefirst and staged puresecond-after-purefirst,bijection/paired sums/negations/identity/model/wrongquarter;every109/113 source scalar/directK2 beta alpha endpoint/fullreverse196/recovery104or64. Only outerT0norms/one quarter/alpha then beta/outerT2pulls in evaluator;existing engines,oldfirst72e1d8/global factorization explicit dependencies,no independent kernel or timing claim");
}
