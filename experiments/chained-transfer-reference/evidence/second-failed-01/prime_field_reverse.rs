//! Reverse second hop/compressed adjoint, with existing engines and fixed
//! accepted covers. Old Richelot references occur only in acceptance tests.
use super::{key, DirectQuartic, PrimeFieldPipeline, Pullback, SuccessorChain};
use crate::balanced::{Balanced, Class};
use crate::nonsplit::map::seven_glue::torsion::chain::prime_field_adjoint::PrimeFieldAdjoint;
use isogeny_algos::curve::{self, Curve, Isogeny, Pt, RatIsogeny};
use isogeny_algos::field::{Field, Zp};
use isogeny_algos::kernel::kohel::kohel;
use std::collections::HashSet;

pub(crate) struct ReversePipeline {
    fp: Zp,
    source: Balanced,
    target: Balanced,
    norms: [DirectQuartic; 2],
    stages: Vec<[RatIsogeny<Zp>; 2]>,
    pulls: [Pullback; 2],
}

impl ReversePipeline {
    pub(crate) fn new(composite: bool) -> Self {
        let fp = Zp::new(101);
        let beta = [
            kohel(&fp, &Curve::new(59, 27), &vec![13, 62, 81, 1], 7),
            kohel(&fp, &Curve::new(23, 7), &vec![11, 64, 23, 1], 7),
        ];
        let mut stages = vec![beta];
        if composite {
            stages.push([
                kohel(&fp, &Curve::new(26, 58), &vec![58, 26, 58, 1], 7),
                kohel(&fp, &Curve::new(69, 50), &vec![29, 88, 45, 1], 7),
            ]);
        }
        for (index, stage) in stages.iter().enumerate() {
            let target = if index == 0 {
                [Curve::new(26, 58), Curve::new(69, 50)]
            } else {
                [Curve::new(1, 46), Curve::new(44, 21)]
            };
            for i in 0..2 {
                assert_eq!(fp.mul(fp.pow(29, 4), stage[i].cod.a), target[i].a);
                assert_eq!(fp.mul(fp.pow(29, 6), stage[i].cod.b), target[i].b);
                if index + 1 < stages.len() {
                    assert_eq!(stages[index + 1][i].dom, target[i]);
                }
            }
        }
        let model = if composite { 0 } else { 1 };
        let target = if composite {
            [31, 75, 74, 54, 71, 55, 1]
        } else {
            [95, 26, 19, 27, 94, 91, 1]
        };
        Self {
            fp,
            source: Balanced::new(101, &[95, 93, 43, 39, 92, 17, 1]).unwrap(),
            target: Balanced::new(101, &target).unwrap(),
            norms: [DirectQuartic::t2(0), DirectQuartic::t2(1)],
            stages,
            pulls: [Pullback::fixed(model, 0), Pullback::fixed(model, 1)],
        }
    }

    pub(crate) fn evaluate(&self, d: &Class) -> Result<Class, String> {
        self.source.check(d)?;
        let mut components = Vec::with_capacity(2);
        for i in 0..2 {
            let point = self.norms[i].norm(d)?.0;
            let mut current = curve::pmul(&self.fp, &self.stages[0][i].dom, &point, [82, 85][i]);
            for stage in &self.stages {
                current = match stage[i].eval(&self.fp, &current) {
                    Pt::Inf => Pt::Inf,
                    Pt::Aff(x, y) => Pt::Aff(
                        self.fp.mul(self.fp.sq(29), x),
                        self.fp.mul(self.fp.pow(29, 3), y),
                    ),
                };
            }
            components.push(self.pulls[i].pull(&current)?.0);
        }
        self.target.add(&components[0], &components[1])
    }
}

fn complete(
    reverse: &ReversePipeline,
    forward: &PrimeFieldPipeline,
    norm: u64,
    expected: impl Fn(&Class) -> Class,
) {
    let all = reverse.source.classes().unwrap();
    assert_eq!(all.len(), 12317);
    let mut images = Vec::with_capacity(all.len());
    let mut distinct = HashSet::new();
    for (i, d) in all.iter().enumerate() {
        let image = reverse.evaluate(d).unwrap();
        assert_eq!(
            image,
            expected(d),
            "reverse stages{} output{i}",
            reverse.stages.len()
        );
        assert!(distinct.insert(key(&image)));
        assert_eq!(
            forward.evaluate(&image).unwrap(),
            reverse.source.mul(d, norm).unwrap()
        );
        images.push(image);
    }
    assert_eq!(distinct.len(), 12317);
    for (i, d) in all.iter().enumerate() {
        let j = (37 * i + 7) % all.len();
        assert_eq!(
            reverse
                .evaluate(&reverse.source.add(d, &all[j]).unwrap())
                .unwrap(),
            reverse.target.add(&images[i], &images[j]).unwrap()
        );
        assert_eq!(
            reverse.evaluate(&reverse.source.neg(d).unwrap()).unwrap(),
            reverse.target.neg(&images[i]).unwrap()
        );
        if *d != reverse.source.zero() {
            assert_ne!(reverse.target.mul(&images[i], 4).unwrap(), images[i]);
        }
    }
    for d in reverse.target.classes().unwrap() {
        assert_eq!(
            reverse.evaluate(&forward.evaluate(&d).unwrap()).unwrap(),
            reverse.target.mul(&d, norm).unwrap()
        );
    }
    assert_eq!(
        reverse.evaluate(&reverse.source.zero()).unwrap(),
        reverse.target.zero()
    );
    assert!(reverse.evaluate(&reverse.target.zero()).is_err());
    assert!(reverse.stages.iter().flatten().all(|map| map.degree() == 7));
}

#[test]
fn prime_reverse_pipeline_second_adjoint_all_classes_and_both_norm7() {
    let reverse = ReversePipeline::new(false);
    let forward = PrimeFieldPipeline::second();
    let old = SuccessorChain::new();
    for i in 0..2 {
        let a = &reverse.stages[0][i];
        let b = &old.s.beta[i].dual;
        assert_eq!(
            (&a.dom, &a.cod, &a.ker, &a.num, &a.den),
            (&b.dom, &b.cod, &b.ker, &b.num, &b.den)
        );
        assert_eq!(old.s.beta[i].dual_scale, 29);
    }
    complete(&reverse, &forward, 7, |d| old.dual_reference(d).unwrap());
    println!("PASS pure F101 second adjoint:all12317 exact oldseconddual outputs/bijection/paired sums/negations/identity/model/wrongquarter,both complete norm7 compositions,coefficient-identical betaHat and checked scale29. Existing T2norm/T1pull/Kohel/Balanced engines;no timing claim");
}

#[test]
fn prime_reverse_pipeline_compressed_adjoint_all_classes_and_both_norm49() {
    let reverse = ReversePipeline::new(true);
    let forward = PrimeFieldPipeline::two_hop();
    let second_reverse = ReversePipeline::new(false);
    let first_reverse = PrimeFieldAdjoint::new();
    let old = SuccessorChain::new();
    complete(&reverse, &forward, 49, |d| {
        let retained = first_reverse.evaluate(&old.dual_reference(d).unwrap()).unwrap();
        assert_eq!(
            first_reverse
                .evaluate(&second_reverse.evaluate(d).unwrap())
                .unwrap(),
            retained
        );
        retained
    });
    for component in 0..2 {
        let source = Pullback::fixed(0, component);
        let e = &forward.stages[0][component].dom;
        let points = super::rational_points(&forward.fp, e);
        let order = [109_u128, 113][component];
        let inverse = [104_u128, 64][component];
        assert_eq!(196 * inverse % order, 1);
        assert_eq!(u128::try_from(points.len()).unwrap(), order);
        for p in points {
            let endpoint = forward.evaluate(&source.pull(&p).unwrap().0).unwrap();
            let recovered = reverse.evaluate(&endpoint).unwrap();
            let norm = [DirectQuartic::first(), DirectQuartic::second()][component]
                .norm(&recovered)
                .unwrap()
                .0;
            assert_eq!(norm, curve::pmul(&forward.fp, e, &p, 196));
            assert_eq!(curve::pmul(&forward.fp, e, &norm, inverse), p);
        }
    }
    println!("PASS compressed pure F101 whole adjoint:all12317 equals acceptedpurefirstadjoint after oldseconddual and separately stagedpure reverse,group/bijection/model/wrongquarter,all12317 both norm49 compositions,every109/113 original source reverse196/recovery104or64. Only outerT2norms/one quarter/betaHat then alphaHat/outerT0pulls;firstdcbb58/global factorization dependencies explicit,no independent kernel or timing claim");
}
