//! Prime-field encoding comparison. Producer experiments, no speedup claim.
mod poly;
mod solver;
#[cfg(test)]
mod tests;
mod up_to;
use cryptanalysis_suite::cryptanalysis::f4_fp::Poly;
use cryptanalysis_suite::cryptanalysis::ic_boundary::{
    CountedGroup, GroupOps, PrimeCurve, PrimePoint,
};
use poly::{mul, pow, s3, Ring, P};
use serde::{Deserialize, Serialize};
pub use solver::{run, Schedule};
use std::time::{Duration, Instant};
pub use up_to::run_up_to;

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Input {
    pub p: u64,
    pub a: u64,
    pub b: u64,
    pub base: Vec<[u64; 2]>,
    pub target: Option<[u64; 2]>,
}
impl Input {
    pub fn curve(&self) -> PrimeCurve {
        PrimeCurve {
            p: self.p,
            a: self.a,
            b: self.b,
        }
    }
    pub fn target_point(&self) -> PrimePoint {
        self.target
            .map(|q| PrimePoint::affine(q[0], q[1]))
            .unwrap_or(PrimePoint::INFINITY)
    }
    pub fn validate(&self) -> Result<(), String> {
        if self.p < 7
            || self.p >= 1u64 << 32
            || !cryptanalysis_suite::cryptanalysis::factoring::arith::is_prime_u64(self.p)
        {
            return Err("requires prime 7<=p<2^32".into());
        }
        if self.a >= self.p || self.b >= self.p {
            return Err("noncanonical curve".into());
        }
        let disc = (mul(4, pow(self.a, 3, self.p), self.p)
            + mul(27, pow(self.b, 2, self.p), self.p))
            % self.p;
        if disc == 0 {
            return Err("singular curve".into());
        }
        if self.base.is_empty() || self.base.len() > 16 {
            return Err("base size must be1..16".into());
        }
        let curve = self.curve();
        let mut xs = std::collections::BTreeSet::new();
        for &[x, y] in &self.base {
            if x >= self.p
                || y >= self.p
                || !curve.is_on_curve(PrimePoint::affine(x, y))
                || !xs.insert(x)
            {
                return Err("base must contain distinct canonical rational abscissae".into());
            }
        }
        if let Some([x, y]) = self.target {
            if x >= self.p || y >= self.p || !curve.is_on_curve(PrimePoint::affine(x, y)) {
                return Err("invalid target".into());
            }
        }
        Ok(())
    }
}
#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum Encoding {
    Monolithic,
    Serial,
    Balanced,
    Partial,
    Explicit,
}
impl Encoding {
    pub fn parse(s: &str) -> Result<Self, String> {
        match s {
            "monolithic" => Ok(Self::Monolithic),
            "serial" => Ok(Self::Serial),
            "balanced" => Ok(Self::Balanced),
            "partial" => Ok(Self::Partial),
            "explicit" => Ok(Self::Explicit),
            _ => Err(format!("unknown encoding {s}")),
        }
    }
}
#[derive(Clone, Debug)]
pub struct System {
    pub input: Input,
    pub m: usize,
    pub encoding: Encoding,
    pub names: Vec<String>,
    pub blocks: Vec<Vec<Poly>>,
    pub domains: Vec<Option<Vec<u64>>>,
    pub scope: &'static str,
    pub construction_ns: u64,
    pub degrees: Vec<u32>,
}
#[derive(Clone, Copy)]
struct Node {
    left: usize,
    right: usize,
    index: usize,
}
fn tree(m: usize, balanced: bool) -> Vec<Node> {
    fn rec(first: usize, end: usize, m: usize, balanced: bool, nodes: &mut Vec<Node>) -> usize {
        if end - first == 1 {
            return first;
        }
        let middle = if balanced {
            first + (end - first) / 2
        } else {
            end - 1
        };
        let left = rec(first, middle, m, balanced, nodes);
        let right = rec(middle, end, m, balanced, nodes);
        let index = m + nodes.len();
        nodes.push(Node { left, right, index });
        index
    }
    let mut nodes = Vec::new();
    rec(0, m, m, balanced, &mut nodes);
    nodes
}
#[derive(Clone)]
struct PointP {
    x: P,
    y: P,
    inf: P,
}
fn point_equations(r: &Ring, q: &PointP, a: u64, b: u64) -> Result<Vec<P>, String> {
    let finite = r.sub(&r.c(1), &q.inf);
    let rhs = r.add(
        &r.add(&r.product(&r.sq(&q.x)?, &q.x)?, &r.scale(&q.x, a)),
        &r.c(b),
    );
    Ok(vec![
        r.product(&q.inf, &r.sub(&q.inf, &r.c(1)))?,
        r.product(&q.inf, &q.x)?,
        r.product(&q.inf, &q.y)?,
        r.product(&finite, &r.sub(&r.sq(&q.y)?, &rhs))?,
    ])
}

/// Complete affine/infinity addition relation as a union of five disjoint
/// guarded branches. Lambda and inverse witnesses are zero on inactive arms.
fn addition(
    r: &Ring,
    l: &PointP,
    q: &PointP,
    o: &PointP,
    selectors: &[P],
    lambda: &P,
    t: &P,
    a: u64,
) -> Result<Vec<P>, String> {
    let one = r.c(1);
    let zero = r.c(0);
    let mut eqs = Vec::new();
    let mut sum = zero;
    for s in selectors {
        eqs.push(r.product(s, &r.sub(s, &one))?);
        sum = r.add(&sum, s);
    }
    eqs.push(r.sub(&sum, &one));
    let mut guarded = |selector: usize, values: Vec<P>| -> Result<(), String> {
        for v in values {
            eqs.push(r.product(&selectors[selector], &v)?);
        }
        Ok(())
    };
    // Left infinity includes O+O. Right infinity requires finite left.
    guarded(
        0,
        vec![
            r.sub(&l.inf, &one),
            r.sub(&o.inf, &q.inf),
            r.sub(&o.x, &q.x),
            r.sub(&o.y, &q.y),
        ],
    )?;
    guarded(
        1,
        vec![
            l.inf.clone(),
            r.sub(&q.inf, &one),
            r.sub(&o.inf, &l.inf),
            r.sub(&o.x, &l.x),
            r.sub(&o.y, &l.y),
        ],
    )?;
    guarded(
        2,
        vec![
            l.inf.clone(),
            q.inf.clone(),
            r.sub(&l.x, &q.x),
            r.add(&l.y, &q.y),
            r.sub(&o.inf, &one),
        ],
    )?;
    let twice_y = r.scale(&l.y, 2);
    let tangent = r.add(&r.scale(&r.sq(&l.x)?, 3), &r.c(a));
    let output_y = r.add(&o.y, &r.sub(&l.y, &r.product(lambda, &r.sub(&l.x, &o.x))?));
    guarded(
        3,
        vec![
            l.inf.clone(),
            q.inf.clone(),
            o.inf.clone(),
            r.sub(&l.x, &q.x),
            r.sub(&l.y, &q.y),
            r.sub(&r.product(t, &twice_y)?, &one),
            r.sub(&r.product(lambda, &twice_y)?, &tangent),
            r.sub(&r.add(&o.x, &r.scale(&l.x, 2)), &r.sq(lambda)?),
            output_y.clone(),
        ],
    )?;
    let dx = r.sub(&q.x, &l.x);
    let dy = r.sub(&q.y, &l.y);
    guarded(
        4,
        vec![
            l.inf.clone(),
            q.inf.clone(),
            o.inf.clone(),
            r.sub(&r.product(t, &dx)?, &one),
            r.sub(&r.product(lambda, &dx)?, &dy),
            r.sub(&r.add(&r.add(&o.x, &l.x), &q.x), &r.sq(lambda)?),
            output_y,
        ],
    )?;
    let inactive = r.sub(&one, &r.add(&selectors[3], &selectors[4]));
    eqs.push(r.product(&inactive, lambda)?);
    eqs.push(r.product(&inactive, t)?);
    Ok(eqs)
}

fn padded_coefficients(r: &Ring, f: &P, v: usize, degree: usize) -> Vec<P> {
    let mut c = r.coefficient(f, v);
    c.resize(degree + 1, r.c(0));
    c
}
fn s4(r: &Ring, x: &[P], a: u64, b: u64, scratch: usize) -> Result<P, String> {
    let u = r.v(scratch);
    let left = s3(r, &x[0], &x[1], &u, a, b)?;
    let right = s3(r, &x[2], &x[3], &u, a, b)?;
    r.resultant(
        &padded_coefficients(r, &left, scratch, 2),
        &padded_coefficients(r, &right, scratch, 2),
    )
}

pub fn build(
    input: &Input,
    m: usize,
    encoding: Encoding,
    construction_budget: Duration,
) -> Result<System, String> {
    input.validate()?;
    if !(2..=4).contains(&m) {
        return Err("m must be2..4".into());
    }
    if encoding != Encoding::Explicit && input.target.is_none() {
        return Err("affine_target_identity_outside_chart".into());
    }
    let started = Instant::now();
    let mut names: Vec<String> = (0..m).map(|i| format!("x{i}")).collect();
    let xs: Vec<u64> = input.base.iter().map(|p| p[0]).collect();
    let mut domains = vec![Some(xs.clone()); m];
    let nodes = tree(m, encoding == Encoding::Balanced);
    let mut point_indices = vec![None; 2 * m - 1];
    let mut branch_indices = Vec::new();
    let mut new_var = |name: String, domain: Option<Vec<u64>>| {
        let i = names.len();
        names.push(name);
        domains.push(domain);
        i
    };
    if encoding == Encoding::Explicit {
        let mut ys: Vec<u64> = input
            .base
            .iter()
            .flat_map(|p| [p[1], (input.p - p[1]) % input.p])
            .collect();
        ys.sort_unstable();
        ys.dedup();
        for (i, slot) in point_indices.iter_mut().enumerate().take(m) {
            let y = new_var(format!("y{i}"), Some(ys.clone()));
            *slot = Some((i, y, None));
        }
        for node in &nodes {
            if node.index != 2 * m - 2 {
                let x = new_var(format!("u{}_x", node.index), None);
                let y = new_var(format!("u{}_y", node.index), None);
                let inf = new_var(format!("u{}_infinity", node.index), Some(vec![0, 1]));
                point_indices[node.index] = Some((x, y, Some(inf)));
            }
            let sels: Vec<usize> = (0..5)
                .map(|b| new_var(format!("branch{}_{}", node.index, b), Some(vec![0, 1])))
                .collect();
            let lambda = new_var(format!("lambda{}", node.index), None);
            let inverse = new_var(format!("inverse{}", node.index), None);
            branch_indices.push((sels, lambda, inverse));
        }
    } else {
        let count = if encoding == Encoding::Monolithic {
            0
        } else if encoding == Encoding::Partial {
            usize::from(m == 4)
        } else {
            m - 2
        };
        for i in 0..count {
            new_var(format!("u{i}"), None);
        }
    }
    let n = names.len();
    let mut quotient_domains = vec![None; n + 2];
    for d in quotient_domains.iter_mut().take(m) {
        *d = Some(xs.clone());
    }
    let ring = Ring {
        p: input.p,
        n: n + 2,
        domains: quotient_domains,
        deadline: started + construction_budget,
        term_cap: 50_000,
    };
    let mut blocks: Vec<Vec<P>> = vec![(0..m)
        .map(|i| ring.membership(&ring.v(i), &xs))
        .collect::<Result<_, _>>()?];
    let target_x = ring.c(input.target.map_or(0, |p| p[0]));
    let construction_encoding = if encoding == Encoding::Partial && m <= 3 {
        Encoding::Monolithic
    } else {
        encoding
    };
    match construction_encoding {
        Encoding::Monolithic => {
            let x: Vec<P> = (0..m)
                .map(|i| ring.v(i))
                .chain(std::iter::once(target_x))
                .collect();
            let value = match m {
                2 => s3(&ring, &x[0], &x[1], &x[2], input.a, input.b)?,
                3 => s4(&ring, &x, input.a, input.b, n + 1)?,
                _ => {
                    let u = ring.v(n);
                    let first = s4(
                        &ring,
                        &[x[0].clone(), x[1].clone(), x[2].clone(), u.clone()],
                        input.a,
                        input.b,
                        n + 1,
                    )?;
                    let second = s3(&ring, &x[3], &x[4], &u, input.a, input.b)?;
                    ring.resultant(
                        &padded_coefficients(&ring, &first, n, 4),
                        &padded_coefficients(&ring, &second, n, 2),
                    )?
                }
            };
            blocks.push(vec![value]);
        }
        Encoding::Partial => {
            let u = ring.v(m);
            blocks.push(vec![s3(
                &ring,
                &ring.v(0),
                &ring.v(1),
                &u,
                input.a,
                input.b,
            )?]);
            blocks.push(vec![s4(
                &ring,
                &[u, ring.v(2), ring.v(3), target_x],
                input.a,
                input.b,
                n + 1,
            )?]);
        }
        Encoding::Serial | Encoding::Balanced => {
            for node in &nodes {
                let value = |index| {
                    if index == 2 * m - 2 {
                        target_x.clone()
                    } else {
                        ring.v(index)
                    }
                };
                blocks.push(vec![s3(
                    &ring,
                    &value(node.left),
                    &value(node.right),
                    &value(node.index),
                    input.a,
                    input.b,
                )?]);
            }
        }
        Encoding::Explicit => {
            let root = PointP {
                x: target_x,
                y: ring.c(input.target.map_or(0, |p| p[1])),
                inf: ring.c(u64::from(input.target.is_none())),
            };
            let points: Vec<PointP> = point_indices
                .iter()
                .map(|opt| match opt {
                    Some((x, y, inf)) => PointP {
                        x: ring.v(*x),
                        y: ring.v(*y),
                        inf: inf.map_or_else(|| ring.c(0), |i| ring.v(i)),
                    },
                    None => root.clone(),
                })
                .collect();
            for point in &points {
                blocks[0].extend(point_equations(&ring, point, input.a, input.b)?);
            }
            for (node, (selectors, lambda, inverse)) in nodes.iter().zip(branch_indices) {
                let selectors: Vec<_> = selectors.iter().map(|&i| ring.v(i)).collect();
                blocks.push(addition(
                    &ring,
                    &points[node.left],
                    &points[node.right],
                    &points[node.index],
                    &selectors,
                    &ring.v(lambda),
                    &ring.v(inverse),
                    input.a,
                )?);
            }
        }
    }
    let blocks: Vec<Vec<Poly>> = blocks
        .iter()
        .map(|b| {
            b.iter()
                .map(|p| ring.export(p, n))
                .filter(|p| !p.is_empty())
                .collect()
        })
        .collect();
    let degrees = blocks
        .iter()
        .flatten()
        .map(|p| p.iter().map(|(e, _)| e.iter().sum()).max().unwrap_or(0))
        .collect();
    Ok(System {
        input: input.clone(),
        m,
        encoding,
        names,
        blocks,
        domains,
        scope: if encoding == Encoding::Explicit {
            "complete_group_addition_branch_cover"
        } else {
            "affine_summation_chart; identity_intermediates_or_nonrational_witnesses_may_be_absent; unsat_is_chart_scoped"
        },
        construction_ns: started.elapsed().as_nanos().min(u64::MAX as u128) as u64,
        degrees,
    })
}

/// Independent group validation of recovered x leaves. At m<=4 only sixteen
/// signs are checked; this is validation, never the polynomial solver.
#[allow(dead_code)] // Convenience API also used by the independent controls.
pub fn verify_leaves(input: &Input, xs: &[u64]) -> Option<Vec<i8>> {
    verify_leaves_with_work(input, xs).0
}
pub fn verify_leaves_with_work(input: &Input, xs: &[u64]) -> (Option<Vec<i8>>, u64) {
    let curve = input.curve();
    let points: Option<Vec<_>> = xs
        .iter()
        .map(|x| {
            input
                .base
                .iter()
                .find(|p| p[0] == *x)
                .map(|p| PrimePoint::affine(p[0], p[1]))
        })
        .collect::<Option<_>>();
    let Some(points) = points else {
        return (None, 0);
    };
    let mut ops = GroupOps::default();
    for mask in 0usize..1usize << xs.len() {
        let mut sum = curve.identity();
        let mut signs = Vec::new();
        for (i, &point) in points.iter().enumerate() {
            let sign = if mask >> i & 1 == 0 { 1 } else { -1 };
            signs.push(sign);
            sum = curve.add(
                &mut ops,
                sum,
                if sign == 1 { point } else { curve.neg(point) },
            );
        }
        if sum == input.target_point() {
            return (Some(signs), ops.adds);
        }
    }
    (None, ops.adds)
}

/// Evaluate the actual S2..S5 polynomial on raw field abscissae, without
/// assuming their lifts are rational. Useful for independent Fp2 controls.
#[allow(dead_code)] // Shared with the separate target/salvage example.
pub fn numeric_summation_root(
    p: u64,
    a: u64,
    b: u64,
    xs: &[u64],
    budget: Duration,
) -> Result<bool, String> {
    if p < 7
        || p >= 1u64 << 32
        || !cryptanalysis_suite::cryptanalysis::factoring::arith::is_prime_u64(p)
        || a >= p
        || b >= p
        || xs.iter().any(|&x| x >= p)
    {
        return Err("noncanonical prime-field arguments".into());
    }
    if (mul(4, pow(a, 3, p), p) + mul(27, pow(b, 2, p), p)) % p == 0 {
        return Err("singular curve".into());
    }
    if !(2..=5).contains(&xs.len()) {
        return Err("numeric summation arity must be2..5".into());
    }
    let r = Ring {
        p,
        n: 2,
        domains: vec![None; 2],
        deadline: Instant::now() + budget,
        term_cap: 50000,
    };
    let x: Vec<_> = xs.iter().map(|&x| r.c(x)).collect();
    let value = match x.len() {
        2 => r.sub(&x[0], &x[1]),
        3 => s3(&r, &x[0], &x[1], &x[2], a, b)?,
        4 => s4(&r, &x, a, b, 1)?,
        _ => {
            let u = r.v(0);
            let first = s4(
                &r,
                &[x[0].clone(), x[1].clone(), x[2].clone(), u.clone()],
                a,
                b,
                1,
            )?;
            let second = s3(&r, &x[3], &x[4], &u, a, b)?;
            r.resultant(
                &padded_coefficients(&r, &first, 0, 4),
                &padded_coefficients(&r, &second, 0, 2),
            )?
        }
    };
    if value.0.keys().any(|e| e.iter().any(|&k| k != 0)) {
        return Err("resultant retained a symbolic variable".into());
    }
    Ok(value.0.is_empty())
}
