//! Actual second nondual seven-transfer on the accepted C1/C2 models.
//! Written global construction: upstream SUCCESSOR_GLOBAL_PROOF.md.
use super::super::direct_norms::DirectNorms;
use super::super::{
    checked_quotient_chart, long_point, points, scale_point, short_point, QuotientChart,
    SevenTransfer,
};
use crate::balanced::{Class, SplitQuotients};
use crate::reference::MumfordDivisorP;
use crate::seven::{construct_edges, SevenEdge};
use isogeny_algos::curve::{self, Isogeny, Pt};
use isogeny_algos::field::{Field, Zp};

type Result<T> = std::result::Result<T, String>;
#[path = "seven_successor_torsion.rs"]
mod geometric;

struct SevenSuccessor {
    old: SevenTransfer,
    target: SplitQuotients,
    norms: DirectNorms,
    beta: [SevenEdge; 2],
    charts: [QuotientChart; 2],
}

impl SevenSuccessor {
    fn new() -> Self {
        let old = SevenTransfer::new();
        let kernels = [vec![99, 94, 75, 1], vec![53, 19, 40, 1]];
        let beta: [SevenEdge; 2] = std::array::from_fn(|i| {
            let edge = construct_edges(&old.fp, &old.edges[i].map.cod)
                .into_iter()
                .find(|e| e.map.ker == kernels[i])
                .unwrap();
            assert_ne!(edge.map.ker, old.edges[i].dual.ker);
            edge
        });
        assert_eq!((beta[0].map.cod.a, beta[0].map.cod.b), (59, 27));
        assert_eq!((beta[1].map.cod.a, beta[1].map.cod.b), (23, 7));
        let target = SplitQuotients::new(101, [19, 10, 22]).unwrap();
        let norms = DirectNorms::successor().unwrap();
        let cubics = [[19, 10, 22, 1], [58, 14, 10, 1]];
        let destinations = [&beta[0].map.cod, &beta[1].map.cod];
        let charts = cubics.map(|c| checked_quotient_chart(&old.fp, &c, destinations));
        assert_eq!(
            charts.map(|c| (c.destination, c.shift, c.scale)),
            [(1, 41, 18), (0, 37, 18)]
        );
        Self {
            old,
            target,
            norms,
            beta,
            charts,
        }
    }

    fn pulls(
        f: &Zp,
        model: &SplitQuotients,
        charts: [QuotientChart; 2],
        actual: [Pt<u64>; 2],
    ) -> Result<Class> {
        let bases = [&model.first.base, &model.second.base];
        let components: [MumfordDivisorP; 2] = std::array::from_fn(|i| {
            let c = charts[i];
            long_point(
                f,
                bases[i],
                scale_point(f, actual[c.destination], f.inv(c.scale)),
                c.shift,
            )
        });
        model.pulls(&components[0], &components[1])
    }

    fn target_coordinates(&self, d: &Class) -> Result<[Pt<u64>; 2]> {
        let f = &self.old.fp;
        let mut out = [Pt::Inf; 2];
        for (c, p) in self.charts.into_iter().zip(self.norms.norms(d)?) {
            out[c.destination] = scale_point(f, p, c.scale);
            assert!(curve::on_curve(
                f,
                &self.beta[c.destination].map.cod,
                &out[c.destination]
            ));
        }
        Ok(out)
    }

    fn target_coordinates_generic(&self, d: &Class) -> Result<[Pt<u64>; 2]> {
        let f = &self.old.fp;
        let (a, b) = self.target.norms(d)?;
        let internal = [
            short_point(f, &self.target.first.base, &a, self.charts[0].shift),
            short_point(f, &self.target.second.base, &b, self.charts[1].shift),
        ];
        let mut out = [Pt::Inf; 2];
        for (c, p) in self.charts.into_iter().zip(internal) {
            out[c.destination] = scale_point(f, p, c.scale);
            assert!(curve::on_curve(
                f,
                &self.beta[c.destination].map.cod,
                &out[c.destination]
            ));
        }
        Ok(out)
    }

    fn forward(&self, d: &Class) -> Result<Class> {
        self.forward_points(self.old.target_coordinates(d)?)
    }

    fn forward_generic(&self, d: &Class) -> Result<Class> {
        self.forward_points(self.old.target_coordinates_generic(d)?)
    }

    fn forward_points(&self, coordinates: [Pt<u64>; 2]) -> Result<Class> {
        let f = &self.old.fp;
        let actual = std::array::from_fn(|i| {
            let e = &self.beta[i];
            let n = [109_u64, 113][i];
            assert_eq!(
                curve::pmul(f, &e.map.dom, &coordinates[i], u128::from(n)),
                Pt::Inf
            );
            let half = curve::pmul(f, &e.map.dom, &coordinates[i], u128::from(n.div_ceil(2)));
            e.map.eval(f, &half)
        });
        Self::pulls(f, &self.target, self.charts, actual)
    }

    fn dual(&self, d: &Class) -> Result<Class> {
        self.dual_points(self.target_coordinates(d)?)
    }

    fn dual_generic(&self, d: &Class) -> Result<Class> {
        self.dual_points(self.target_coordinates_generic(d)?)
    }

    fn dual_points(&self, coordinates: [Pt<u64>; 2]) -> Result<Class> {
        let f = &self.old.fp;
        let actual = std::array::from_fn(|i| {
            let e = &self.beta[i];
            let n = [109_u64, 113][i];
            assert_eq!(
                curve::pmul(f, &e.map.cod, &coordinates[i], u128::from(n)),
                Pt::Inf
            );
            let half = curve::pmul(f, &e.map.cod, &coordinates[i], u128::from(n.div_ceil(2)));
            e.reverse(f, &half)
        });
        Self::pulls(f, &self.old.target, self.old.model.charts, actual)
    }

    fn original_pull(&self, actual: [Pt<u64>; 2]) -> Result<Class> {
        let f = &self.old.fp;
        self.old.source.pulls(
            &long_point(f, &self.old.source.first.base, actual[0], 2),
            &long_point(f, &self.old.source.second.base, actual[1], 38),
        )
    }
}

#[test]
fn successor_seven_source_components_and_direct_two_hop() {
    let s = SevenSuccessor::new();
    let f = &s.old.fp;
    for component in 0..2 {
        let n = [109_u64, 113][component];
        let e0 = &s.old.edges[component].map.dom;
        let generator = points(f, e0)[1];
        let mut product = [Pt::Inf; 2];
        product[component] = generator;
        let first = s.old.forward(&s.original_pull(product).unwrap()).unwrap();
        let target_generator = s.forward(&first).unwrap();
        assert_ne!(target_generator, s.target.first.balanced.zero());
        assert_eq!(
            s.target.first.balanced.mul(&target_generator, n).unwrap(),
            s.target.first.balanced.zero()
        );
        let inverse98 = (1..n).find(|k| 98 * k % n == 1).unwrap();
        for k in 0..n {
            let p = curve::pmul(f, e0, &generator, u128::from(k));
            product[component] = p;
            let original = s.original_pull(product).unwrap();
            let start = s.old.forward(&original).unwrap();
            let end = s.forward(&start).unwrap();
            assert_eq!(
                end,
                s.target.first.balanced.mul(&target_generator, k).unwrap()
            );
            let reversed = s.dual(&end).unwrap();
            assert_eq!(
                reversed,
                s.old.target.first.balanced.mul(&start, 7).unwrap()
            );
            let source = s.old.dual(&reversed).unwrap();
            assert_eq!(
                source,
                s.old.source.first.balanced.mul(&original, 49).unwrap()
            );
            let norms = s.old.source_coordinates_generic(&source).unwrap();
            assert_eq!(norms[component], curve::pmul(f, e0, &p, 98));
            assert_eq!(norms[1 - component], Pt::Inf);
            assert_eq!(
                curve::pmul(f, e0, &norms[component], u128::from(inverse98)),
                p
            );
            let alpha = s.old.edges[component].map.eval(f, &p);
            let beta_alpha = s.beta[component].map.eval(f, &alpha);
            let mut expected = [Pt::Inf; 2];
            expected[component] = curve::pmul(f, &s.beta[component].map.cod, &beta_alpha, 2);
            assert_eq!(s.target_coordinates(&end).unwrap(), expected);
        }
        println!("PASS successor Phi2 all{n} originalsource component{component},nonzero order/scalars,dual7/two-hopJacobian norm49,fullreverse norm98/inverse{inverse98},direct target2 beta alpha;no scalar labels or benchmark");
    }
}

#[test]
fn successor_seven_both_full_domains_duals_and_additions() {
    let s = SevenSuccessor::new();
    super::chain::assert_full_graph_pair(
        &s.old.target.first.balanced,
        &s.target.first.balanced,
        |d| {
            let image = s.forward(d)?;
            assert_eq!(
                image,
                s.forward_generic(d)?,
                "Phi2 direct/generic all-source"
            );
            Ok(image)
        },
        |d| {
            let image = s.dual(d)?;
            assert_eq!(
                image,
                s.dual_generic(d)?,
                "Phi2Hat direct/generic all-target"
            );
            Ok(image)
        },
        7,
    );
    assert!(s.forward(&s.target.first.balanced.zero()).is_err());
    assert!(s.dual(&s.old.target.first.balanced.zero()).is_err());
    println!("PASS actual second nondual Phi2 BOTH complete12317-class C1/C2 domains,dual7/bijections/allpaired additions/descent/wrong-model rejection;global quotient/noniso/composite Fp42 boundary have separate written proof");
}
