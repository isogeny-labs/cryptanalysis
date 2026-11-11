//! Fixed F17 Frobenius-stable Richelot kernel/codomain assessment.
//! Kernel/codomain construction; operational maps live in nonsplit_map.rs.
//! Base polynomial arithmetic is the pre-existing checked BigUint layer.
use super::balanced::Balanced;
use super::reference::{Fp2Ctx, FpPoly};
use num_bigint::BigUint;
use num_traits::{One, ToPrimitive, Zero};
use std::collections::BTreeSet;
type E = FpPoly;
type Poly = Vec<E>;
type Pairing = [(usize, usize); 3];

#[path = "nonsplit_map.rs"]
mod map;

struct CubicField {
    p: u64,
    q: FpPoly,
}
impl CubicField {
    fn with_cubic(p: u64, coefficients: [u64; 3]) -> Result<Self, String> {
        if !(5..=101).contains(&p) || coefficients.iter().any(|c| *c >= p) {
            return Err("cubic prototype requires canonical coefficients,prime5..101".into());
        }
        Fp2Ctx::try_new(p).map_err(|e| e.to_string())?;
        let q = FpPoly::from_coeffs(
            coefficients
                .into_iter()
                .chain([1])
                .map(BigUint::from)
                .collect(),
            BigUint::from(p),
        );
        if (0..p).any(|x| q.eval(&BigUint::from(x)).is_zero()) {
            return Err("reducible cubic modulus".into());
        }
        Ok(Self { p, q })
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
    fn encoding(&self, a: &E) -> u64 {
        (0..3)
            .map(|i| a.coeff(i).to_u64().unwrap() * self.p.pow(i as u32))
            .sum()
    }
    /// Deterministic Tonelli-Shanks in the checked cubic field. The
    /// smaller coefficient encoding preserves the old F17 root convention.
    fn sqrt(&self, a: &E) -> Option<E> {
        if a.is_zero() {
            return Some(self.z());
        }
        let cardinality = self.p.pow(3);
        if self.pow(a, (cardinality - 1) / 2) != self.c(1) {
            return None;
        }
        let (mut odd, mut power) = (cardinality - 1, 0_u32);
        while odd.is_multiple_of(2) {
            odd /= 2;
            power += 1;
        }
        let nr = Fp2Ctx::try_new(self.p).unwrap().nonresidue();
        let mut c = self.pow(&self.c(nr), odd);
        let mut t = self.pow(a, odd);
        let mut x = self.pow(a, odd.div_ceil(2));
        while t != self.c(1) {
            let mut i = 1_u32;
            let mut test = self.mul(&t, &t);
            while i < power && test != self.c(1) {
                test = self.mul(&test, &test);
                i += 1;
            }
            assert!(i < power, "Tonelli orbit failed in checked field");
            let b = self.pow(&c, 1_u64 << (power - i - 1));
            x = self.mul(&x, &b);
            c = self.mul(&b, &b);
            t = self.mul(&t, &c);
            power = i;
        }
        assert_eq!(self.mul(&x, &x), *a);
        let negative = x.neg();
        Some(if self.encoding(&negative) < self.encoding(&x) {
            negative
        } else {
            x
        })
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
    degenerate: usize,
}
fn construct_for(p: u64, coefficients: [u64; 3]) -> Result<Assessment, String> {
    let k = CubicField::with_cubic(p, coefficients)?;
    let alpha = FpPoly::x(k.q.p.clone());
    // Frozen selection rule: first root in c0+p*c1+p²*c2 encoding.
    let beta = k
        .sqrt(&alpha)
        .ok_or("cubic root nonsquare; no(3,3) branch presentation")?;
    let beta1 = k.pow(&beta, p);
    let beta2 = k.pow(&beta1, p);
    assert_eq!(k.pow(&beta2, p), beta);
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
            .position(|r| *r == k.pow(&roots[i], p))
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
    let source = vec![
        coefficients[0],
        0,
        coefficients[1],
        0,
        coefficients[2],
        0,
        1,
    ];
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
        assert!(
            matches!(target.len(), 6 | 7),
            "nondegenerate target must have genus2"
        );
        let f = FpPoly::from_coeffs(
            target.iter().copied().map(BigUint::from).collect(),
            k.q.p.clone(),
        );
        let df = FpPoly::from_coeffs(
            (1..target.len())
                .map(|i| f.coeff(i) * BigUint::from(i as u64) % &f.p)
                .collect(),
            f.p.clone(),
        );
        assert_eq!(f.gcd(&df), FpPoly::one(f.p.clone()));
        println!("stable pairing{pairing:?}, delta{d}, target{target:?}");
        targets.push(target);
    }
    Ok(Assessment {
        field: k,
        roots,
        pairs,
        source,
        targets,
        degenerate,
    })
}
fn construct() -> Assessment {
    let a = construct_for(17, [2, 2, 0]).unwrap();
    assert_eq!(a.degenerate, 1);
    assert_eq!(a.targets.len(), 2);
    assert_eq!(
        a.targets,
        vec![
            vec![10, 6, 14, 2, 12, 10, 9],
            vec![10, 11, 14, 15, 12, 7, 9]
        ]
    );
    assert!(a.targets[0]
        .iter()
        .enumerate()
        .all(|(i, c)| a.targets[1][i] == if i % 2 == 0 { *c } else { (17 - c) % 17 }));
    a
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

/// Genus2 order from direct base/quadratic-field curve counts, including
/// the actual infinity type. No unsupported odd-chart Curve is fabricated.
fn raw_curve_counts(p: u64, coefficients: &[u64]) -> (u64, u64, u64) {
    let modulus = BigUint::from(p);
    let f = FpPoly::from_coeffs(
        coefficients.iter().copied().map(BigUint::from).collect(),
        modulus.clone(),
    );
    let degree = f.degree().unwrap();
    assert!(matches!(degree, 5 | 6));
    let mut n1: u64 = if degree == 5 {
        1
    } else if f.lead().modpow(&BigUint::from((p - 1) / 2), &modulus) == BigUint::one() {
        2
    } else {
        0
    };
    for x in 0..p {
        let rhs = f.eval(&BigUint::from(x));
        n1 += if rhs.is_zero() {
            1
        } else if rhs.modpow(&BigUint::from((p - 1) / 2), &modulus) == BigUint::one() {
            2
        } else {
            0
        };
    }
    let ctx = Fp2Ctx::try_new(p).unwrap();
    let mut n2: u64 = if degree == 5 { 1 } else { 2 };
    for a in 0..p {
        for b in 0..p {
            let x = ctx.element(a, b);
            let rhs = f.coeffs.iter().rev().fold(ctx.zero(), |v, c| {
                ctx.add(ctx.mul(v, x), ctx.from_fp(c.to_u64().unwrap()))
            });
            n2 += if ctx.is_zero(rhs) {
                1
            } else if ctx.is_qr(rhs) == Some(true) {
                2
            } else {
                0
            };
        }
    }
    assert!((n1 * n1 + n2).is_multiple_of(2));
    (n1, n2, (n1 * n1 + n2) / 2 - p)
}

#[test]
fn checked_cubic_roots_and_frozen_shifted109_inventory() {
    use crate::balanced::QuadraticCover;
    use crate::reference::{
        count_points, HyperellipticCurveP as Curve, MumfordDivisorP as Divisor,
    };
    for (p, coefficients) in [(17, [2, 2, 0]), (101, [56, 13, 6])] {
        let k = CubicField::with_cubic(p, coefficients).unwrap();
        for n in 0..128 {
            let x = k.element((37 * n + 19) % p.pow(3));
            let square = k.mul(&x, &x);
            let root = k.sqrt(&square).unwrap();
            assert_eq!(k.mul(&root, &root), square);
        }
        let nr = Fp2Ctx::try_new(p).unwrap().nonresidue();
        assert!(k.sqrt(&k.c(nr)).is_none());
    }
    assert!(CubicField::with_cubic(9, [2, 2, 0]).is_err());
    assert!(CubicField::with_cubic(17, [0, 0, 0]).is_err());
    assert!(CubicField::with_cubic(17, [17, 2, 0]).is_err());
    assert!(construct_for(101, [46, 1, 0]).is_err());
    let a = construct_for(101, [56, 13, 6]).unwrap();
    assert_eq!(a.source, vec![56, 0, 13, 0, 6, 0, 1]);
    assert_eq!(a.degenerate + a.targets.len(), 3);
    let counts = raw_curve_counts(101, &a.source);
    let poly = |c: &[u64]| {
        FpPoly::from_coeffs(
            c.iter().copied().map(BigUint::from).collect(),
            BigUint::from(101_u64),
        )
    };
    let shifted = Curve::try_new(BigUint::from(101_u64), poly(&[56, 13, 6, 1]), 1).unwrap();
    let original = Curve::try_new(BigUint::from(101_u64), poly(&[46, 1, 0, 1]), 1).unwrap();
    let other = Curve::try_new(BigUint::from(101_u64), poly(&[5, 33, 13, 1]), 1).unwrap();
    assert_eq!(count_points(&shifted), BigUint::from(109_u64));
    let other_order = count_points(&other).to_u64().unwrap();
    assert_eq!(counts.2, 109 * other_order);
    let cover = QuadraticCover::with_cubic(101, [56, 13, 6]).unwrap();
    let g =
        Divisor::try_from_point(&shifted, &BigUint::from(0_u64), &BigUint::from(37_u64)).unwrap();
    let original_g =
        Divisor::try_from_point(&original, &BigUint::from(2_u64), &BigUint::from(37_u64)).unwrap();
    let first = cover.pull(&g).unwrap();
    for n in 0..109_u64 {
        let d = g.checked_scalar_mul(&BigUint::from(n), &shifted).unwrap();
        let bridge = if d.is_identity() {
            Divisor::identity(shifted.p.clone())
        } else {
            Divisor::try_from_polynomials(
                &original,
                poly(&[(d.u.coeff(0).to_u64().unwrap() + 99) % 101, 1]),
                d.v.clone(),
            )
            .unwrap()
        };
        assert_eq!(
            bridge,
            original_g
                .checked_scalar_mul(&BigUint::from(n), &original)
                .unwrap()
        );
        let pulled = cover.pull(&d).unwrap();
        assert_eq!(pulled, cover.balanced.mul(&first, n).unwrap());
        assert_eq!(
            cover.norm(&pulled).unwrap(),
            d.checked_scalar_mul(&BigUint::from(2_u64), &shifted)
                .unwrap()
        );
    }
    println!("shifted109 source counts{counts:?}, elliptic quotient orders109/{other_order}, stable{} degenerate{} targets{}",a.pairs.len(),a.degenerate,a.targets.len());
    for target in &a.targets {
        let target_counts = raw_curve_counts(101, target);
        assert_eq!(target_counts.2, counts.2);
        let leading = *target.last().unwrap();
        let square_root = (1..101).find(|y| y * y % 101 == leading);
        println!(
            "shifted109 target{target:?}, counts{target_counts:?}, leading_root{square_root:?}"
        );
        if let Some(root) = square_root {
            let inverse = BigUint::from(leading)
                .modpow(&BigUint::from(99_u64), &BigUint::from(101_u64))
                .to_u64()
                .unwrap();
            let normalized = target.iter().map(|c| c * inverse % 101).collect::<Vec<_>>();
            assert_eq!(
                Balanced::new(101, &normalized)
                    .unwrap()
                    .classes()
                    .unwrap()
                    .len() as u64,
                counts.2
            );
            println!("shifted109 supported monic target{normalized:?}, raw ordinate scale{root}");
        } else {
            println!("retained shifted109 nonsquare-leading boundary: explicit split-infinity chart required before map support");
        }
    }
    println!("PASS checked cubic square roots/invalid fields, frozen shift2 source all109 coordinate/pullback/norm controls and complete stable-kernel/codomain inventory; no shifted Richelot map evaluated");
}
