//! Fixed F17 Frobenius-stable Richelot kernel/codomain assessment.
//! This module constructs factors and target models, not divisor maps.
//! Base polynomial arithmetic is the pre-existing checked BigUint layer.
use super::balanced::Balanced;
use super::reference::{Fp2Ctx, FpPoly};
use num_bigint::BigUint;
use num_traits::{One, ToPrimitive, Zero};
use std::collections::BTreeSet;
type E = FpPoly;
type Poly = Vec<E>;
type Pairing = [(usize, usize); 3];

struct CubicField {
    p: u64,
    q: FpPoly,
}
impl CubicField {
    fn new() -> Self {
        let p = 17;
        Fp2Ctx::try_new(p).unwrap();
        let q = FpPoly::from_coeffs(
            [2_u64, 2, 0, 1].into_iter().map(BigUint::from).collect(),
            BigUint::from(p),
        );
        assert!(
            (0..p).all(|x| !q.eval(&BigUint::from(x)).is_zero()),
            "cubic must be irreducible"
        );
        Self { p, q }
    }
    fn z(&self) -> E {
        FpPoly::zero(self.q.p.clone())
    }
    fn c(&self, n: u64) -> E {
        FpPoly::constant(BigUint::from(n % self.p), self.q.p.clone())
    }
    fn element(&self, n: u64) -> E {
        FpPoly::from_coeffs(
            [
                n % self.p,
                n / self.p % self.p,
                n / (self.p * self.p) % self.p,
            ]
            .into_iter()
            .map(BigUint::from)
            .collect(),
            self.q.p.clone(),
        )
    }
    fn mul(&self, a: &E, b: &E) -> E {
        a.mul(b).rem(&self.q)
    }
    fn pow(&self, a: &E, mut n: u64) -> E {
        let mut a = a.clone();
        let mut out = self.c(1);
        while n != 0 {
            if n & 1 != 0 {
                out = self.mul(&out, &a);
            }
            a = self.mul(&a, &a);
            n >>= 1;
        }
        out
    }
    fn inv(&self, a: &E) -> E {
        let (g, s, _) = a.ext_gcd(&self.q);
        assert_eq!(g, self.c(1), "zero/nonunit in cubic residue field");
        s.rem(&self.q)
    }
    fn base(&self, a: &E) -> u64 {
        assert!(
            a.degree().is_none_or(|d| d == 0),
            "coefficient did not descend"
        );
        a.coeff(0).to_u64().unwrap()
    }
    fn trim(&self, mut a: Poly) -> Poly {
        while a.last().is_some_and(FpPoly::is_zero) {
            a.pop();
        }
        a
    }
    fn add_poly(&self, a: &Poly, b: &Poly) -> Poly {
        self.trim(
            (0..a.len().max(b.len()))
                .map(|i| {
                    a.get(i)
                        .cloned()
                        .unwrap_or_else(|| self.z())
                        .add(&b.get(i).cloned().unwrap_or_else(|| self.z()))
                })
                .collect(),
        )
    }
    fn neg_poly(&self, a: &Poly) -> Poly {
        a.iter().map(FpPoly::neg).collect()
    }
    fn mul_poly(&self, a: &Poly, b: &Poly) -> Poly {
        if a.is_empty() || b.is_empty() {
            return vec![];
        }
        let mut out = vec![self.z(); a.len() + b.len() - 1];
        for (i, x) in a.iter().enumerate() {
            for (j, y) in b.iter().enumerate() {
                out[i + j] = out[i + j].add(&self.mul(x, y));
            }
        }
        self.trim(out)
    }
    fn derivative(&self, a: &Poly) -> Poly {
        self.trim(
            a.iter()
                .enumerate()
                .skip(1)
                .map(|(i, c)| self.mul(c, &self.c(i as u64)))
                .collect(),
        )
    }
    fn product(&self, g: &[Poly; 3]) -> Poly {
        self.mul_poly(&self.mul_poly(&g[0], &g[1]), &g[2])
    }
    fn determinant(&self, g: &[Poly; 3]) -> E {
        let mut out = self.z();
        for i in 0..3 {
            out = out.add(&self.mul(&self.mul(&g[0][i], &g[1][(i + 1) % 3]), &g[2][(i + 2) % 3]));
            out = out.sub(&self.mul(&self.mul(&g[0][i], &g[1][(i + 2) % 3]), &g[2][(i + 1) % 3]));
        }
        out
    }
    fn dual_factors(&self, g: &[Poly; 3], delta: &E) -> [Poly; 3] {
        let scale = self.inv(delta);
        std::array::from_fn(|i| {
            let a = &g[(i + 1) % 3];
            let b = &g[(i + 2) % 3];
            let bracket = self.add_poly(
                &self.mul_poly(&self.derivative(a), b),
                &self.neg_poly(&self.mul_poly(a, &self.derivative(b))),
            );
            bracket.iter().map(|c| self.mul(c, &scale)).collect()
        })
    }
}

fn canonical_pairing(mut p: Pairing) -> Pairing {
    for pair in &mut p {
        if pair.0 > pair.1 {
            *pair = (pair.1, pair.0);
        }
    }
    p.sort_unstable();
    p
}
fn pairings() -> Vec<Pairing> {
    fn recurse(left: Vec<usize>, current: Vec<(usize, usize)>, out: &mut Vec<Pairing>) {
        if left.is_empty() {
            out.push(current.try_into().unwrap());
            return;
        }
        let a = left[0];
        for (i, b) in left.iter().copied().enumerate().skip(1) {
            let rest = left
                .iter()
                .copied()
                .enumerate()
                .filter_map(|(j, x)| (j != 0 && j != i).then_some(x))
                .collect();
            let mut next = current.clone();
            next.push((a, b));
            recurse(rest, next, out);
        }
    }
    let mut out = vec![];
    recurse((0..6).collect(), vec![], &mut out);
    out
}
fn stable(p: &Pairing, permutation: &[usize; 6]) -> bool {
    canonical_pairing(p.map(|(a, b)| (permutation[a], permutation[b]))) == *p
}

struct Assessment {
    field: CubicField,
    roots: Vec<E>,
    pairs: Vec<Pairing>,
    source: Vec<u64>,
    targets: Vec<Vec<u64>>,
}
fn construct() -> Assessment {
    let k = CubicField::new();
    let alpha = FpPoly::x(k.q.p.clone());
    // Frozen selection rule: first root in c0+p*c1+p²*c2 encoding.
    let beta = (0..17_u64.pow(3))
        .map(|n| k.element(n))
        .find(|v| k.mul(v, v) == alpha)
        .expect("norm(alpha)=-2=15 is square in F17");
    let beta1 = k.pow(&beta, 17);
    let beta2 = k.pow(&beta1, 17);
    assert_eq!(k.pow(&beta2, 17), beta);
    let roots = vec![
        beta.clone(),
        beta1.clone(),
        beta2.clone(),
        beta.neg(),
        beta1.neg(),
        beta2.neg(),
    ];
    for (i, a) in roots.iter().enumerate() {
        assert!(!roots[..i].contains(a));
    }
    let permutation = std::array::from_fn(|i| {
        roots
            .iter()
            .position(|r| *r == k.pow(&roots[i], 17))
            .unwrap()
    });
    assert_eq!(permutation, [1, 2, 0, 4, 5, 3]);
    let all = pairings();
    assert_eq!(all.len(), 15);
    assert_eq!(all.iter().copied().collect::<BTreeSet<_>>().len(), 15);
    let pairs = all
        .into_iter()
        .filter(|p| stable(p, &permutation))
        .collect::<Vec<_>>();
    assert_eq!(pairs.len(), 3);
    let source = vec![2, 0, 2, 0, 0, 0, 1];
    let expected = source.iter().map(|c| k.c(*c)).collect::<Poly>();
    let mut targets = vec![];
    let mut degenerate = 0;
    for pairing in &pairs {
        let g: [Poly; 3] = std::array::from_fn(|i| {
            let (a, b) = pairing[i];
            vec![
                k.mul(&roots[a], &roots[b]),
                roots[a].add(&roots[b]).neg(),
                k.c(1),
            ]
        });
        assert_eq!(k.product(&g), expected);
        let delta = k.determinant(&g);
        let d = k.base(&delta);
        if delta.is_zero() {
            degenerate += 1;
            println!("retained degenerate pairing{pairing:?}, delta0");
            continue;
        }
        let h = k.dual_factors(&g, &delta);
        let target = k.product(&h).iter().map(|c| k.base(c)).collect::<Vec<_>>();
        assert_eq!(target.len(), 7);
        let f = FpPoly::from_coeffs(
            target.iter().copied().map(BigUint::from).collect(),
            k.q.p.clone(),
        );
        let df = FpPoly::from_coeffs(
            (1..7)
                .map(|i| f.coeff(i) * BigUint::from(i as u64) % &f.p)
                .collect(),
            f.p.clone(),
        );
        assert_eq!(f.gcd(&df), FpPoly::one(f.p.clone()));
        println!("stable pairing{pairing:?}, delta{d}, target{target:?}");
        targets.push(target);
    }
    assert_eq!(degenerate, 1);
    assert_eq!(targets.len(), 2);
    assert_eq!(
        targets,
        vec![
            vec![10, 6, 14, 2, 12, 10, 9],
            vec![10, 11, 14, 15, 12, 7, 9]
        ]
    );
    assert!(targets[0]
        .iter()
        .enumerate()
        .all(|(i, c)| targets[1][i] == if i % 2 == 0 { *c } else { (17 - c) % 17 }));
    Assessment {
        field: k,
        roots,
        pairs,
        source,
        targets,
    }
}

/// Full PGL2(F17) binary-sextic audit. Leading coefficient ratio must be
/// a nonzero square for an F17 curve isomorphism. No Jacobian-isomorphism
/// inference is made solely from this curve-level computation.
fn curve_isomorphisms(a: &[u64], b: &[u64]) -> usize {
    let p = BigUint::from(17_u64);
    let poly =
        |c: &[u64]| FpPoly::from_coeffs(c.iter().copied().map(BigUint::from).collect(), p.clone());
    let b = poly(b);
    let mut count = 0;
    let mut matrices = 0;
    for aa in 0..17 {
        for bb in 0..17 {
            for cc in 0..17 {
                for dd in 0..17 {
                    let entries = [aa, bb, cc, dd];
                    if entries.iter().copied().find(|x| *x != 0) != Some(1)
                        || (aa * dd + 17 * 17 - bb * cc) % 17 == 0
                    {
                        continue;
                    }
                    matrices += 1;
                    let numerator = poly(&[bb, aa]);
                    let denominator = poly(&[dd, cc]);
                    let mut np = vec![poly(&[1])];
                    let mut dp = vec![poly(&[1])];
                    for i in 0..6 {
                        np.push(np[i].mul(&numerator));
                        dp.push(dp[i].mul(&denominator));
                    }
                    let mut transformed = poly(&[]);
                    for (i, c) in a.iter().enumerate() {
                        transformed =
                            transformed.add(&np[i].mul(&dp[6 - i]).scalar_mul(&BigUint::from(*c)));
                    }
                    let Some(pivot) = b.coeffs.iter().position(|c| !c.is_zero()) else {
                        panic!("zero sextic");
                    };
                    let ratio = transformed.coeff(pivot)
                        * b.coeff(pivot).modpow(&BigUint::from(15_u64), &p)
                        % &p;
                    if !ratio.is_zero()
                        && ratio.modpow(&BigUint::from(8_u64), &p) == BigUint::one()
                        && transformed == b.scalar_mul(&ratio)
                    {
                        count += 1;
                    }
                }
            }
        }
    }
    assert_eq!(matrices, 4896);
    count
}

#[test]
fn complete_stable_pairings_and_descended_targets() {
    let a = construct();
    let k = &a.field;
    let source = Balanced::new(17, &a.source).unwrap();
    let size = source.classes().unwrap().len();
    assert_eq!(size, 285);
    for target in &a.targets {
        let leading = target[6];
        let square = (1..17).find(|y| y * y % 17 == leading);
        let Some(root) = square else {
            panic!("inert codomain retained as unsupported target{target:?}");
        };
        let inverse = k
            .c(leading)
            .coeff(0)
            .modpow(&BigUint::from(15_u64), &k.q.p)
            .to_u64()
            .unwrap();
        let normalized = target.iter().map(|c| c * inverse % 17).collect::<Vec<_>>();
        let curve = Balanced::new(17, &normalized).unwrap();
        assert_eq!(curve.classes().unwrap().len(), size);
        println!("target split infinity sqrt{root}; monic{normalized:?}, rationalJac{size}");
    }
    assert_eq!(a.roots.len(), 6);
    assert_eq!(a.pairs.len(), 3);
    println!("PASS15 complete pairings,3 Frobenius-stable,1 degenerate/2 smooth base-field targets, shared rationalJac{size}; divisor correspondence is not implemented");
}
#[test]
fn full_curve_equivalence_audit() {
    let a = construct();
    let models = [a.source, a.targets[0].clone(), a.targets[1].clone()];
    for (i, source) in models.iter().enumerate() {
        for (j, target) in models.iter().enumerate().skip(i) {
            let count = curve_isomorphisms(source, target);
            if i == j {
                assert!(count > 0);
            }
            assert_eq!(count, [[2, 0, 0], [0, 1, 1], [0, 0, 1]][i][j]);
            println!("PGL2 curve audit{i}->{j}: {count} base-field quotient maps with square y-scale (4896 matrices checked)");
        }
    }
}
#[test]
fn prime109_cycle_and_unique_degenerate_control() {
    let p = BigUint::from(101_u64);
    let f = FpPoly::from_coeffs(
        [46_u64, 1, 0, 1].into_iter().map(BigUint::from).collect(),
        p.clone(),
    );
    assert!((0_u64..101).all(|x| !f.eval(&BigUint::from(x)).is_zero()));
    // Norm of a cubic root is -46=55, nonsquare. Over the odd-degree
    // cubic field the root is therefore nonsquare too. Its square roots
    // give a6-cycle: Frobenius³ exchanges their signs.
    assert_eq!(
        BigUint::from(55_u64).modpow(&BigUint::from(50_u64), &p),
        BigUint::from(100_u64)
    );
    let stable = pairings()
        .into_iter()
        .filter(|p| stable(p, &[1, 2, 3, 4, 5, 0]))
        .collect::<Vec<_>>();
    assert_eq!(stable, vec![[(0, 3), (1, 4), (2, 5)]]);
    // Opposite roots give x²-alpha_i: the linear coefficient column is
    // zero, so the Richelot determinant vanishes identically.
    println!("PASS E109 quadratic sextic irreducible6-cycle and unique stable opposite pairing; its zero linear column is degenerate. This is a fixture-specific control, not a universal obstruction");
}
