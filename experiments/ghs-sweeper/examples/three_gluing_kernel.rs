//! Actual coordinate certificates for one binary cubic 3-gluing kernel type.
//! This constructs no quotient curve and evaluates no descent isogeny.
use anyhow::{ensure, Context, Result};
use clap::{Parser, Subcommand};
use ghs_sweeper::{field::Field, verify::RawField};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::{collections::BTreeSet, fs, path::PathBuf};

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
struct Z(u32, u32); // s+t*u, u^2+u+1=0
const ZERO: Z = Z(0, 0);
const ONE: Z = Z(1, 0);
type Point = Option<[Z; 2]>;
type Triple = [Point; 3];

#[derive(Parser)]
#[command(about = "Construct/replay a source 3-kernel; no Jacobian transfer or novelty claim")]
struct Args {
    #[command(subcommand)]
    command: Command,
}
#[derive(Subcommand)]
enum Command {
    Generate {
        #[arg(long)]
        base_degree: u32,
        #[arg(long, default_value_t = 0)]
        a: u32,
        #[arg(long)]
        b: u32,
    },
    Verify {
        #[arg(long)]
        certificate: PathBuf,
    },
    /// Transport the same kernel across y -> y+u*x, over the quadratic field.
    Twist {
        #[arg(long)]
        certificate: PathBuf,
    },
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct Certificate {
    kind: String,
    base_degree: u32,
    absolute_degree: u32,
    modulus: u32,
    quadratic_polynomial: [u8; 3],
    a: u32,
    b: u32,
    source_basis: [Point; 2],
    generators: [Triple; 3],
    kernel_points: Vec<Triple>,
}

#[derive(Clone, Copy)]
struct Arithmetic<'a> {
    field: &'a Field,
    raw: Option<&'a RawField>,
}
impl Arithmetic<'_> {
    fn base_mul(&self, a: u32, b: u32) -> u32 {
        self.raw
            .map_or_else(|| self.field.mul(a, b), |r| r.mul(a, b))
    }
    fn base_power(&self, mut a: u32, mut n: u32) -> u32 {
        let mut v = 1;
        while n != 0 {
            if n & 1 != 0 {
                v = self.base_mul(v, a);
            }
            a = self.base_mul(a, a);
            n >>= 1;
        }
        v
    }
    fn add(&self, a: Z, b: Z) -> Z {
        Z(a.0 ^ b.0, a.1 ^ b.1)
    }
    fn mul(&self, a: Z, b: Z) -> Z {
        let bd = self.base_mul(a.1, b.1);
        Z(
            self.base_mul(a.0, b.0) ^ bd,
            self.base_mul(a.0, b.1) ^ self.base_mul(a.1, b.0) ^ bd,
        )
    }
    fn square(&self, a: Z) -> Z {
        self.mul(a, a)
    }
    fn inverse(&self, a: Z) -> Result<Z> {
        ensure!(a != ZERO, "division by zero");
        let norm = self.base_mul(a.0, a.0) ^ self.base_mul(a.0, a.1) ^ self.base_mul(a.1, a.1);
        ensure!(norm != 0, "zero quadratic norm");
        let inv = if self.raw.is_some() {
            self.base_power(norm, self.field.size - 2)
        } else {
            self.field.inv(norm)
        };
        let result = Z(self.base_mul(a.0 ^ a.1, inv), self.base_mul(a.1, inv));
        ensure!(
            self.mul(a, result) == ONE,
            "quadratic inverse replay failed"
        );
        Ok(result)
    }
    fn divide(&self, a: Z, b: Z) -> Result<Z> {
        Ok(self.mul(a, self.inverse(b)?))
    }
    fn frobenius(&self, mut a: Z, degree: u32) -> Z {
        for _ in 0..degree {
            a = self.square(a);
        }
        a
    }
    fn trace(&self, a: u32) -> u32 {
        let (mut v, mut z) = (0, a);
        for _ in 0..self.field.degree {
            v ^= z;
            z = self.base_mul(z, z);
        }
        v
    }
    fn half_trace(&self, a: u32) -> u32 {
        let (mut v, mut z) = (0, a);
        for _ in 0..=self.field.degree / 2 {
            v ^= z;
            z = self.base_mul(z, z);
            z = self.base_mul(z, z);
        }
        v
    }
}

#[derive(Clone, Copy, Debug, Serialize)]
struct Curve {
    a: Z,
    b: Z,
}
impl Curve {
    fn on_curve(&self, p: Point, f: Arithmetic<'_>) -> bool {
        let Some([x, y]) = p else {
            return true;
        };
        [x.0, x.1, y.0, y.1].iter().all(|&z| z < f.field.size)
            && f.add(f.square(y), f.mul(x, y))
                == f.add(
                    f.add(f.mul(f.square(x), x), f.mul(self.a, f.square(x))),
                    self.b,
                )
    }
    fn neg(&self, p: Point, f: Arithmetic<'_>) -> Point {
        p.map(|[x, y]| [x, f.add(x, y)])
    }
    fn plus(&self, p: Point, q: Point, f: Arithmetic<'_>) -> Result<Point> {
        let (Some([x1, y1]), Some([x2, y2])) = (p, q) else {
            return Ok(p.or(q));
        };
        if x1 == x2 {
            if y1 != y2 || x1 == ZERO {
                return Ok(None);
            }
            let lambda = f.add(x1, f.divide(y1, x1)?);
            let x3 = f.add(f.add(f.square(lambda), lambda), self.a);
            let y3 = f.add(f.square(x1), f.mul(f.add(lambda, ONE), x3));
            Ok(Some([x3, y3]))
        } else {
            let lambda = f.divide(f.add(y1, y2), f.add(x1, x2))?;
            let x3 = f.add(
                f.add(f.add(f.add(f.square(lambda), lambda), x1), x2),
                self.a,
            );
            let y3 = f.add(f.add(f.mul(lambda, f.add(x1, x3)), x3), y1);
            Ok(Some([x3, y3]))
        }
    }
    fn scalar(&self, mut p: Point, mut n: u32, f: Arithmetic<'_>) -> Result<Point> {
        let mut r = None;
        while n != 0 {
            if n & 1 != 0 {
                r = self.plus(r, p, f)?;
            }
            p = self.plus(p, p, f)?;
            n >>= 1;
        }
        Ok(r)
    }
    fn tangent(&self, p: Point, q: Point, f: Arithmetic<'_>) -> Result<Z> {
        let [x, y] = p.context("tangent at infinity")?;
        let [v, w] = q.context("tangent evaluated at infinity")?;
        let slope = f.add(x, f.divide(y, x)?);
        Ok(f.add(f.add(w, y), f.mul(slope, f.add(v, x))))
    }
    // For nonzero 3-torsion, the monic tangent has divisor 3(P)-3(O).
    fn pairing(&self, p: Point, q: Point, f: Arithmetic<'_>) -> Result<Z> {
        if p.is_none() || q.is_none() || p == q {
            return Ok(ONE);
        }
        f.divide(self.tangent(p, q, f)?, self.tangent(q, p, f)?)
    }
    fn auxiliary_pairing(&self, p: Point, q: Point, f: Arithmetic<'_>) -> Result<Z> {
        let s = self.plus(p, q, f)?;
        let first = f.divide(
            self.tangent(p, self.plus(q, s, f)?, f)?,
            self.tangent(p, s, f)?,
        )?;
        let second = f.divide(
            self.tangent(q, self.neg(s, f), f)?,
            self.tangent(q, self.plus(p, self.neg(s, f), f)?, f)?,
        )?;
        Ok(f.mul(first, second))
    }
}

fn point_frobenius(p: Point, degree: u32, f: Arithmetic<'_>) -> Point {
    p.map(|v| v.map(|z| f.frobenius(z, degree)))
}
fn tuple_frobenius(p: Triple, degree: u32, f: Arithmetic<'_>) -> Triple {
    [
        point_frobenius(p[2], degree, f),
        point_frobenius(p[0], degree, f),
        point_frobenius(p[1], degree, f),
    ]
}
fn tuple_plus(p: Triple, q: Triple, curves: &[Curve; 3], f: Arithmetic<'_>) -> Result<Triple> {
    Ok([
        curves[0].plus(p[0], q[0], f)?,
        curves[1].plus(p[1], q[1], f)?,
        curves[2].plus(p[2], q[2], f)?,
    ])
}
fn combinations(
    generators: &[Triple; 3],
    curves: &[Curve; 3],
    f: Arithmetic<'_>,
) -> Result<BTreeSet<Triple>> {
    let mut points = BTreeSet::new();
    for a in 0..3 {
        for b in 0..3 {
            for c in 0..3 {
                let mut r = [None; 3];
                for (i, n) in [a, b, c].into_iter().enumerate() {
                    for _ in 0..n {
                        r = tuple_plus(r, generators[i], curves, f)?;
                    }
                }
                points.insert(r);
            }
        }
    }
    Ok(points)
}
fn curves(cert: &Certificate, f: Arithmetic<'_>) -> [Curve; 3] {
    std::array::from_fn(|i| Curve {
        a: f.frobenius(Z(cert.a, 0), i as u32 * cert.base_degree),
        b: f.frobenius(Z(cert.b, 0), i as u32 * cert.base_degree),
    })
}

#[derive(Debug, PartialEq, Eq, Serialize)]
struct Checks {
    accepted: bool,
    source_basis_pairing: Z,
    conjugate_basis_pairings: [Z; 3],
    auxiliary_pairing_agrees: bool,
    kernel_cardinality: usize,
    closed_under_addition: bool,
    frobenius_stable: bool,
    individually_rational_points: usize,
    coordinate_intersection_sizes: [usize; 3],
    ordered_pairings_evaluated: usize,
    nontrivial_product_pairings: usize,
}

fn check(cert: &Certificate, f: Arithmetic<'_>) -> Result<Checks> {
    let factors = curves(cert, f);
    let [p, q] = cert.source_basis;
    ensure!(p.is_some() && q.is_some(), "source basis contains infinity");
    for r in [p, q] {
        ensure!(
            factors[0].on_curve(r, f),
            "source basis is off curve or out of field"
        );
        ensure!(
            factors[0].scalar(r, 3, f)?.is_none(),
            "source basis is not three-torsion"
        );
    }
    ensure!(
        point_frobenius(p, cert.absolute_degree, f) == p,
        "P is not the +1 eigenvector"
    );
    ensure!(
        point_frobenius(q, cert.absolute_degree, f) == factors[0].neg(q, f),
        "Q is not the -1 eigenvector"
    );
    let pairing = factors[0].pairing(p, q, f)?;
    ensure!(
        pairing != ONE && f.mul(f.square(pairing), pairing) == ONE,
        "source pairing is not primitive"
    );
    let auxiliary = factors[0].auxiliary_pairing(p, q, f)? == pairing;
    ensure!(auxiliary, "normalized and auxiliary Weil formulas disagree");
    let mut conjugate = [ZERO; 3];
    for i in 0..3 {
        let pi = point_frobenius(p, i as u32 * cert.base_degree, f);
        let qi = point_frobenius(q, i as u32 * cert.base_degree, f);
        ensure!(
            factors[i].on_curve(pi, f) && factors[i].on_curve(qi, f),
            "conjugate basis is off curve"
        );
        conjugate[i] = factors[i].pairing(pi, qi, f)?;
        ensure!(
            conjugate[i] == f.frobenius(pairing, i as u32 * cert.base_degree),
            "pairing/Frobenius incompatibility"
        );
    }
    for g in &cert.generators {
        for i in 0..3 {
            ensure!(
                factors[i].on_curve(g[i], f),
                "generator coordinate is off curve or out of field"
            );
            ensure!(
                factors[i].scalar(g[i], 3, f)?.is_none(),
                "generator is not three-torsion"
            );
        }
    }
    let points = combinations(&cert.generators, &factors, f)?;
    let supplied: BTreeSet<_> = cert.kernel_points.iter().copied().collect();
    ensure!(
        supplied.len() == cert.kernel_points.len(),
        "duplicate supplied kernel points"
    );
    ensure!(
        supplied == points,
        "supplied kernel set does not match its generators"
    );
    for g in &points {
        for i in 0..3 {
            ensure!(factors[i].on_curve(g[i], f), "kernel point is off curve");
            ensure!(
                factors[i].scalar(g[i], 3, f)?.is_none(),
                "kernel point is not three-torsion"
            );
        }
    }
    let mut closed = true;
    let mut nontrivial = 0;
    let mut count = 0;
    for &g in &points {
        for &h in &points {
            closed &= points.contains(&tuple_plus(g, h, &factors, f)?);
            let mut value = ONE;
            for i in 0..3 {
                value = f.mul(value, factors[i].pairing(g[i], h[i], f)?);
            }
            nontrivial += usize::from(value != ONE);
            count += 1;
        }
    }
    let stable = points
        .iter()
        .all(|&p| points.contains(&tuple_frobenius(p, cert.base_degree, f)));
    let rational = points
        .iter()
        .filter(|&&p| tuple_frobenius(p, cert.base_degree, f) == p)
        .count();
    let intersections = std::array::from_fn(|i| {
        points
            .iter()
            .filter(|p| (0..3).all(|j| j == i || p[j].is_none()))
            .count()
    });
    Ok(Checks {
        accepted: points.len() == 27
            && closed
            && stable
            && nontrivial == 0
            && intersections == [1; 3]
            && rational == 3,
        source_basis_pairing: pairing,
        conjugate_basis_pairings: conjugate,
        auxiliary_pairing_agrees: auxiliary,
        kernel_cardinality: points.len(),
        closed_under_addition: closed,
        frobenius_stable: stable,
        individually_rational_points: rational,
        coordinate_intersection_sizes: intersections,
        ordered_pairings_evaluated: count,
        nontrivial_product_pairings: nontrivial,
    })
}

fn field(d: u32, a: u32, b: u32) -> Result<Field> {
    ensure!(
        d == 3 || d == 5,
        "coordinate checker supports odd base degrees 3 or 5"
    );
    let f = Field::new(3 * d)?;
    ensure!(
        b != 0 && b < f.size && a < f.size,
        "singular b=0 or invalid coefficient"
    );
    let c = f.power(b, ((1_u64 << (f.degree + 1)) - 1) / 3);
    ensure!(
        f.trace[c as usize] == 0,
        "cube-root trace is one: this kernel type is absent"
    );
    let mut z = b;
    let mut degree = 0;
    for i in 1..=f.degree {
        z = f.mul(z, z);
        if z == b {
            degree = i;
            break;
        }
    }
    ensure!(
        degree == f.degree,
        "full absolute coefficient degree is required"
    );
    Ok(f)
}

fn generate(d: u32, a: u32, b: u32) -> Result<Certificate> {
    let f = field(d, a, b)?;
    let ar = Arithmetic {
        field: &f,
        raw: None,
    };
    let c = f.power(b, ((1_u64 << (f.degree + 1)) - 1) / 3);
    let (mut u, mut z) = (0, c);
    for _ in 0..=f.degree / 2 {
        u ^= z;
        for _ in 0..4 {
            z = f.mul(z, z);
        }
    }
    let mut basis = [None; 2];
    for t in [u, u ^ 1] {
        let x = f.mul(f.mul(t, t), t) ^ 1;
        let rhs = f.mul(x, x) ^ a;
        let bit = ar.trace(rhs);
        ensure!(bit < 2, "trace escaped F2");
        let y = ar.mul(Z(x, 0), Z(ar.half_trace(rhs), bit));
        basis[bit as usize] = Some([Z(x, 0), y]);
    }
    ensure!(
        basis.iter().all(Option::is_some),
        "division roots did not give both Frobenius lines"
    );
    let p: [Point; 3] = std::array::from_fn(|i| point_frobenius(basis[0], i as u32 * d, ar));
    let q: [Point; 3] = std::array::from_fn(|i| point_frobenius(basis[1], i as u32 * d, ar));
    let mut cert = Certificate {
        kind: "binary-cubic-3-kernel/v1".into(),
        base_degree: d,
        absolute_degree: f.degree,
        modulus: f.modulus,
        quadratic_polynomial: [1, 1, 1],
        a,
        b,
        source_basis: basis,
        generators: [p, [q[0], q[1], None], [None, q[1], q[2]]],
        kernel_points: Vec::new(),
    };
    cert.kernel_points = combinations(&cert.generators, &curves(&cert, ar), ar)?
        .into_iter()
        .collect();
    Ok(cert)
}

fn verify(cert: &Certificate) -> Result<Checks> {
    ensure!(
        cert.kind == "binary-cubic-3-kernel/v1",
        "unsupported certificate kind"
    );
    let f = field(cert.base_degree, cert.a, cert.b)?;
    ensure!(
        cert.absolute_degree == f.degree
            && cert.modulus == f.modulus
            && cert.quadratic_polynomial == [1, 1, 1],
        "field binding mismatch"
    );
    let raw = RawField {
        degree: f.degree,
        size: f.size,
        modulus: f.modulus,
        traces: Vec::new(),
        inverses: Vec::new(),
    };
    let fast = check(
        cert,
        Arithmetic {
            field: &f,
            raw: None,
        },
    )?;
    let replay = check(
        cert,
        Arithmetic {
            field: &f,
            raw: Some(&raw),
        },
    )?;
    ensure!(fast == replay, "fast and raw arithmetic disagree");
    ensure!(
        fast.accepted,
        "kernel failed a structural predicate: {fast:?}"
    );
    Ok(fast)
}

fn read_certificate(path: PathBuf) -> Result<Certificate> {
    let value: serde_json::Value = serde_json::from_slice(&fs::read(path)?)?;
    Ok(serde_json::from_value(
        value.get("certificate").unwrap_or(&value).clone(),
    )?)
}

fn twist_point(p: Point, f: Arithmetic<'_>) -> Point {
    p.map(|[x, y]| [x, f.add(y, f.mul(Z(0, 1), x))])
}

fn twist_kernel(cert: &Certificate) -> Result<Certificate> {
    verify(cert)?;
    let f = field(cert.base_degree, cert.a, cert.b)?;
    let ar = Arithmetic {
        field: &f,
        raw: None,
    };
    let mut target = cert.clone();
    target.a ^= 1;
    target.source_basis = [
        twist_point(cert.source_basis[1], ar),
        twist_point(cert.source_basis[0], ar),
    ];
    target.generators = cert.generators.map(|g| g.map(|p| twist_point(p, ar)));
    target.kernel_points = cert
        .kernel_points
        .iter()
        .map(|g| g.map(|p| twist_point(p, ar)))
        .collect();
    target.kernel_points.sort();
    verify(&target)?;
    Ok(target)
}

fn main() -> Result<()> {
    let cert = match Args::parse().command {
        Command::Generate { base_degree, a, b } => generate(base_degree, a, b)?,
        Command::Verify { certificate } => read_certificate(certificate)?,
        Command::Twist { certificate } => twist_kernel(&read_certificate(certificate)?)?,
    };
    let checks = verify(&cert)?;
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "certificate":cert,"checks":checks,"raw_arithmetic_agrees":true,
            "target_curve_constructed":false,"arithmetic_torelli_twist_selected":false,
            "isogeny_evaluated":false,"planted_log_verified":false,
            "publication_novelty_established":false,"weak_catalogue_promotion":false,
            "curve_id":null,"candidate_id":null,"subgroup_order":null,
            "costs":{"construction":null,"transfer":null,"solve":null,"rho":null}
        }))?
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quadratic_twist_transports_the_same_kernel() -> Result<()> {
        let cert = generate(3, 0, 24)?;
        let target = twist_kernel(&cert)?;
        assert_eq!(target.a, 1);
        let f = field(3, 0, 24)?;
        let raw = RawField {
            degree: f.degree,
            size: f.size,
            modulus: f.modulus,
            traces: Vec::new(),
            inverses: Vec::new(),
        };
        for ar in [
            Arithmetic {
                field: &f,
                raw: None,
            },
            Arithmetic {
                field: &f,
                raw: Some(&raw),
            },
        ] {
            let source_curves = curves(&cert, ar);
            let target_curves = curves(&target, ar);
            for &g in &cert.kernel_points {
                let image = g.map(|p| twist_point(p, ar));
                let left = tuple_frobenius(image, 3, ar);
                let right = tuple_frobenius(g, 3, ar).map(|p| twist_point(p, ar));
                assert_eq!(
                    left,
                    std::array::from_fn(|i| target_curves[i].neg(right[i], ar))
                );
                for &h in &cert.kernel_points {
                    let mapped_sum =
                        tuple_plus(g, h, &source_curves, ar)?.map(|p| twist_point(p, ar));
                    assert_eq!(
                        mapped_sum,
                        tuple_plus(image, h.map(|p| twist_point(p, ar)), &target_curves, ar)?
                    );
                }
            }
        }
        let restored = twist_kernel(&target)?;
        assert_eq!(restored.a, cert.a);
        assert_eq!(restored.source_basis, cert.source_basis);
        assert_eq!(restored.generators, cert.generators);
        assert_eq!(restored.kernel_points, cert.kernel_points);
        Ok(())
    }

    fn exact_control_order(f: Arithmetic<'_>, a: u32, b: u32) -> u64 {
        let mut count = 2;
        for x in 1..f.field.size {
            let inverse_x2 = f.base_power(f.base_mul(x, x), f.field.size - 2);
            let h = x ^ a ^ f.base_mul(b, inverse_x2);
            if f.trace(h) == 0 {
                count += 2;
            }
        }
        count
    }

    #[test]
    fn fixed_source_orders_for_historical_overlap_check() -> Result<()> {
        let f = Field::new(9)?;
        let raw = RawField {
            degree: f.degree,
            size: f.size,
            modulus: f.modulus,
            traces: Vec::new(),
            inverses: Vec::new(),
        };
        let mut orders = Vec::new();
        for a in [0, 1] {
            let fast = exact_control_order(
                Arithmetic {
                    field: &f,
                    raw: None,
                },
                a,
                24,
            );
            let replay = exact_control_order(
                Arithmetic {
                    field: &f,
                    raw: Some(&raw),
                },
                a,
                24,
            );
            assert_eq!(fast, replay);
            assert_eq!(fast % 3, 0);
            println!(
                "fixed_control a={a} b=24 modulus=515 order={fast} trace={}",
                513 - fast as i64
            );
            orders.push(fast);
        }
        assert_eq!(orders[0] + orders[1], 1026);
        Ok(())
    }

    #[test]
    fn actual_kernel_on_both_fixed_twists() -> Result<()> {
        for a in [0, 1] {
            let cert = generate(3, a, 24)?;
            let result = verify(&cert)?;
            assert_eq!(
                cert.source_basis
                    .map(|p| p.unwrap()[0].0)
                    .into_iter()
                    .collect::<BTreeSet<_>>(),
                BTreeSet::from([2, 75])
            );
            assert_eq!(result.kernel_cardinality, 27);
            assert_eq!(result.ordered_pairings_evaluated, 729);
            assert_eq!(result.nontrivial_product_pairings, 0);
            assert_eq!(result.individually_rational_points, 3);
            let decoded: Certificate = serde_json::from_str(&serde_json::to_string(&cert)?)?;
            assert_eq!(verify(&decoded)?, result);
        }
        Ok(())
    }

    #[test]
    fn structural_negative_controls_do_not_pass() -> Result<()> {
        let cert = generate(3, 0, 24)?;
        let f = field(3, 0, 24)?;
        let ar = Arithmetic {
            field: &f,
            raw: None,
        };
        let factors = curves(&cert, ar);
        let p = cert.generators[0];
        let mut decomposable = cert.clone();
        decomposable.generators = [[p[0], None, None], [None, p[1], None], [None, None, p[2]]];
        decomposable.kernel_points = combinations(&decomposable.generators, &factors, ar)?
            .into_iter()
            .collect();
        let result = check(&decomposable, ar)?;
        println!(
            "negative_control decomposable {}",
            serde_json::to_string(&result)?
        );
        assert_eq!(result.nontrivial_product_pairings, 0);
        assert_eq!(result.coordinate_intersection_sizes, [3; 3]);
        assert!(result.frobenius_stable && !result.accepted);
        assert!(verify(&decomposable).is_err());
        let mut nonisotropic = cert;
        nonisotropic.generators[1][1] = factors[1].neg(nonisotropic.generators[1][1], ar);
        nonisotropic.kernel_points = combinations(&nonisotropic.generators, &factors, ar)?
            .into_iter()
            .collect();
        let result = check(&nonisotropic, ar)?;
        println!(
            "negative_control nonisotropic {}",
            serde_json::to_string(&result)?
        );
        assert_eq!(result.coordinate_intersection_sizes, [1; 3]);
        assert!(result.nontrivial_product_pairings > 0 && !result.accepted);
        assert!(verify(&nonisotropic).is_err());
        Ok(())
    }

    #[test]
    fn altered_certificates_and_bad_inputs_are_rejected() -> Result<()> {
        let original = generate(3, 0, 24)?;
        let mut cert = original.clone();
        cert.source_basis[0].as_mut().unwrap()[0].0 ^= 1;
        assert!(verify(&cert).is_err());
        cert = original.clone();
        cert.modulus ^= 2;
        assert!(verify(&cert).is_err());
        cert = original.clone();
        cert.kernel_points.push(cert.kernel_points[0]);
        assert!(verify(&cert).is_err());
        cert = original;
        cert.kernel_points.pop();
        assert!(verify(&cert).is_err());
        for (d, a, b) in [
            (0, 0, 24),
            (1, 0, 2),
            (2, 0, 2),
            (3, 0, 0),
            (3, 0, 1),
            (3, 512, 24),
            (3, 0, 512),
        ] {
            assert!(generate(d, a, b).is_err());
        }
        let f = Field::new(9)?;
        let trace_one_b = f.mul(f.mul(19, 19), 19);
        assert!(generate(3, 0, trace_one_b).is_err());
        Ok(())
    }
}
