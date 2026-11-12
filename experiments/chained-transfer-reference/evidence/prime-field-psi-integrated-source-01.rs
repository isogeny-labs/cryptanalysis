//! Complete fixed forward Psi evaluation with F101 operations only. Retained
//! SevenChain is imported solely in the test; the new constructor/evaluator
//! uses fixed accepted coefficients and existing prime-field engines.
use super::quartic_norm::DirectQuartic;
use super::quartic_pullback::Pullback;
use crate::balanced::{Balanced, Class};
use isogeny_algos::curve;
use isogeny_algos::curve::{Curve, Isogeny, RatIsogeny};
use isogeny_algos::field::Zp;
use isogeny_algos::kernel::kohel::kohel;
use num_traits::ToPrimitive;
use std::collections::HashSet;

struct PrimeFieldPsi {
    fp: Zp,
    source: Balanced,
    target: Balanced,
    norms: [DirectQuartic; 2],
    alpha: [RatIsogeny<Zp>; 2],
    pulls: [Pullback; 2],
}
impl PrimeFieldPsi {
    fn new() -> Self {
        let fp = Zp::new(101);
        let alpha = [
            kohel(&fp, &Curve::new(1, 46), &vec![72, 100, 35, 1], 7),
            kohel(&fp, &Curve::new(44, 21), &vec![59, 46, 8, 1], 7),
        ];
        assert_eq!(alpha[0].cod, Curve::new(26, 58));
        assert_eq!(alpha[1].cod, Curve::new(69, 50));
        Self {
            fp,
            source: Balanced::new(101, &[31, 75, 74, 54, 71, 55, 1]).unwrap(),
            target: Balanced::new(101, &[95, 26, 19, 27, 94, 91, 1]).unwrap(),
            norms: [DirectQuartic::first(), DirectQuartic::second()],
            alpha,
            pulls: [Pullback::fixed(1, 0), Pullback::fixed(1, 1)],
        }
    }
    fn forward(&self, d: &Class) -> Result<Class, String> {
        self.source.check(d)?;
        let mut components = Vec::with_capacity(2);
        for i in 0..2 {
            let point = self.norms[i].norm(d)?.0;
            let quarter = curve::pmul(&self.fp, &self.alpha[i].dom, &point, [82, 85][i]);
            let transported = self.alpha[i].eval(&self.fp, &quarter);
            components.push(self.pulls[i].pull(&transported)?.0);
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

#[test]
fn complete_forward_psi_using_only_prime_field_evaluation() {
    let direct = PrimeFieldPsi::new();
    let old = super::SevenChain::new();
    for i in 0..2 {
        assert_eq!(direct.alpha[i].dom, old.t.edges[i].map.dom);
        assert_eq!(direct.alpha[i].cod, old.t.edges[i].map.cod);
        assert_eq!(direct.alpha[i].num, old.t.edges[i].map.num);
        assert_eq!(direct.alpha[i].den, old.t.edges[i].map.den);
        assert_eq!(direct.alpha[i].ker, old.t.edges[i].map.ker);
    }
    let all = direct.source.classes().unwrap();
    assert_eq!(all.len(), 12317);
    let mut images = Vec::new();
    let mut distinct = HashSet::new();
    for (i, d) in all.iter().enumerate() {
        let result = direct.forward(d).unwrap();
        assert_eq!(
            result,
            old.forward(d).unwrap(),
            "whole prime-field Psi class{i}"
        );
        assert!(
            distinct.insert(key(&result)),
            "whole prime-field bijection{i}"
        );
        images.push(result);
    }
    assert_eq!(distinct.len(), 12317);
    for (i, d) in all.iter().enumerate() {
        let j = (37 * i + 7) % all.len();
        let sum = direct.source.add(d, &all[j]).unwrap();
        assert_eq!(
            direct.forward(&sum).unwrap(),
            direct.target.add(&images[i], &images[j]).unwrap(),
            "whole prime-field paired addition{i}"
        );
        assert_eq!(
            direct.forward(&direct.source.neg(d).unwrap()).unwrap(),
            direct.target.neg(&images[i]).unwrap(),
            "whole prime-field negation{i}"
        );
    }
    assert_eq!(
        direct.forward(&direct.source.zero()).unwrap(),
        direct.target.zero()
    );
    assert!(direct.forward(&direct.target.zero()).is_err());
    assert!(direct.alpha.iter().all(|map| map.degree() == 7));
    println!("PASS whole forward Psi(T0→T1) pure F101 constructor/evaluation with accepted fixed kernels/covers;all12317 exact old outputs/bijection/paired sums/negations/identity/wrong-model,coefficient-identical selected alpha maps. API calls no Richelot/extension-field evaluator;test enumeration/reference remain separate. Existing arithmetic/reduction bodies retained;global old-map identification and matched costs are separate,no timing claim");
}
