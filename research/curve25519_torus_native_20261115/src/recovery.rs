//! Bounded finite-field roots and triangular-basis recovery for public inputs.
//! gcd(f, X^p-X) selects the distinct rational roots. Euler-character
//! partitions split that square-free part. A failed split is inconclusive.
use num_bigint::BigUint;
use std::collections::BTreeSet;
use torus_s4::{decimal, sha256, Case, Curve, Field, System};
pub type Result<T> = std::result::Result<T, String>;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Uni(pub Vec<BigUint>);
impl Uni {
    fn new(mut a: Vec<BigUint>) -> Self {
        while a.last().is_some_and(|x| *x == BigUint::from(0u32)) {
            a.pop();
        }
        Self(a)
    }
    fn constant(n: u32) -> Self {
        Self::new(vec![n.into()])
    }
    fn degree(&self) -> Option<usize> {
        self.0.len().checked_sub(1)
    }
    fn eval(&self, x: &BigUint, f: &Field) -> BigUint {
        self.0
            .iter()
            .rev()
            .fold(0u32.into(), |s, c| f.add(&f.mul(&s, x), c))
    }
    fn sub(&self, b: &Self, f: &Field) -> Self {
        Self::new(
            (0..self.0.len().max(b.0.len()))
                .map(|i| {
                    f.sub(
                        &self.0.get(i).cloned().unwrap_or_default(),
                        &b.0.get(i).cloned().unwrap_or_default(),
                    )
                })
                .collect(),
        )
    }
    fn mul(&self, b: &Self, f: &Field, w: &mut Limits) -> Result<Self> {
        if self.0.is_empty() || b.0.is_empty() {
            return Ok(Self(vec![]));
        }
        w.charge(self.0.len().checked_mul(b.0.len()).ok_or("work overflow")?)?;
        let mut r = vec![0u32.into(); self.0.len() + b.0.len() - 1];
        for (i, a) in self.0.iter().enumerate() {
            for (j, b) in b.0.iter().enumerate() {
                r[i + j] = f.add(&r[i + j], &f.mul(a, b));
            }
        }
        Ok(Self::new(r))
    }
    fn divrem(&self, b: &Self, f: &Field, w: &mut Limits) -> Result<(Self, Self)> {
        let db = b.degree().ok_or("polynomial division by zero")?;
        let inv = f.inv(&b.0[db])?;
        let mut r = self.clone();
        let mut q = vec![0u32.into(); self.0.len().saturating_sub(db)];
        while let Some(dr) = r.degree() {
            if dr < db {
                break;
            }
            w.charge(db + 1)?;
            let c = f.mul(&r.0[dr], &inv);
            let shift = dr - db;
            q[shift] = c.clone();
            for (j, b) in b.0.iter().enumerate() {
                r.0[j + shift] = f.sub(&r.0[j + shift], &f.mul(&c, b));
            }
            r = Self::new(r.0);
        }
        Ok((Self::new(q), r))
    }
    fn monic(&self, f: &Field) -> Result<Self> {
        let d = self.degree().ok_or("monic zero polynomial")?;
        let inv = f.inv(&self.0[d])?;
        Ok(Self::new(self.0.iter().map(|x| f.mul(x, &inv)).collect()))
    }
    fn gcd(&self, b: &Self, f: &Field, w: &mut Limits) -> Result<Self> {
        let (mut a, mut b) = (self.clone(), b.clone());
        while !b.0.is_empty() {
            let r = a.divrem(&b, f, w)?.1;
            a = b;
            b = r;
        }
        if a.0.is_empty() {
            Ok(a)
        } else {
            a.monic(f)
        }
    }
    fn powmod(&self, e: &BigUint, m: &Self, f: &Field, w: &mut Limits) -> Result<Self> {
        let mut a = self.divrem(m, f, w)?.1;
        let mut r = Self::constant(1);
        for bit in 0..e.bits() {
            if e.bit(bit) {
                r = r.mul(&a, f, w)?.divrem(m, f, w)?.1;
            }
            if bit + 1 < e.bits() {
                a = a.mul(&a, f, w)?.divrem(m, f, w)?.1;
            }
        }
        Ok(r)
    }
}
#[derive(Clone, Debug)]
pub struct Limits {
    pub max_degree: usize,
    pub max_work: usize,
    pub max_assignments: usize,
    pub split_attempts: usize,
    pub work: usize,
    pub branches: usize,
}
impl Default for Limits {
    fn default() -> Self {
        Self {
            max_degree: 4096,
            max_work: 10_000_000,
            max_assignments: 4096,
            split_attempts: 128,
            work: 0,
            branches: 0,
        }
    }
}
impl Limits {
    fn charge(&mut self, n: usize) -> Result<()> {
        self.work = self.work.checked_add(n).ok_or("work overflow")?;
        if self.work > self.max_work {
            Err("recovery work limit; inconclusive".into())
        } else {
            Ok(())
        }
    }
}

pub fn roots(poly: &Uni, f: &Field, w: &mut Limits) -> Result<Vec<BigUint>> {
    let normalized = Uni::new(poly.0.iter().map(|c| c % &f.p).collect());
    let poly = &normalized;
    let degree = poly
        .degree()
        .ok_or("zero polynomial does not constrain a variable")?;
    if degree > w.max_degree {
        return Err("recovery degree limit; inconclusive".into());
    }
    if degree == 0 {
        return Ok(vec![]);
    }
    let x = Uni(vec![0u32.into(), 1u32.into()]);
    let rational = poly.gcd(&x.powmod(&f.p, poly, f, w)?.sub(&x, f), f, w)?;
    let mut stack = vec![rational];
    let mut out = vec![];
    let mut draw = 0u64;
    while let Some(g) = stack.pop() {
        let Some(d) = g.degree() else {
            return Err("invalid zero rational factor".into());
        };
        if d == 0 {
            continue;
        }
        if d == 1 {
            out.push(f.mul(&f.sub(&0u32.into(), &g.0[0]), &f.inv(&g.0[1])?));
            continue;
        }
        let mut split = None;
        for _ in 0..w.split_attempts {
            let mut coeffs = vec![];
            for _ in 0..d {
                draw = draw.checked_add(1).ok_or("draw overflow")?;
                let hex = sha256(&draw.to_le_bytes());
                coeffs
                    .push(BigUint::parse_bytes(hex.as_bytes(), 16).ok_or("invalid digest")? % &f.p);
            }
            let a = Uni::new(coeffs);
            let zero = a.gcd(&g, f, w)?;
            let h = if zero.degree().is_some_and(|n| n > 0 && n < d) {
                zero
            } else {
                a.powmod(&((&f.p - 1u32) >> 1), &g, f, w)?
                    .sub(&Uni::constant(1), f)
                    .gcd(&g, f, w)?
            };
            if h.degree().is_some_and(|n| n > 0 && n < d) {
                split = Some(h);
                break;
            }
        }
        let h = split.ok_or("finite splitting attempt limit; inconclusive")?;
        let (q, r) = g.divrem(&h, f, w)?;
        if !r.0.is_empty() {
            return Err("inexact factor split".into());
        }
        stack.push(h);
        stack.push(q);
    }
    out.sort();
    out.dedup();
    if out.iter().any(|x| poly.eval(x, f) != BigUint::from(0u32)) {
        return Err("root substitution failed".into());
    }
    Ok(out)
}

#[derive(Clone, Debug)]
pub struct Term {
    pub coefficient: BigUint,
    pub exponents: Vec<u32>,
}
#[derive(Clone, Debug)]
pub struct Basis {
    pub equations: Vec<Vec<Term>>,
    pub variables: usize,
    pub engine_reported_unit: bool,
}
fn coefficient(s: &str, f: &Field) -> Result<BigUint> {
    if let Some(a) = s.strip_prefix('-') {
        Ok(f.sub(&0u32.into(), &decimal(a)?))
    } else {
        Ok(decimal(s)? % &f.p)
    }
}
/// Read only the delimited, term-by-term protocol, never human-formatted monomials.
pub fn parse_basis(text: &str, variables: usize, f: &Field) -> Result<Basis> {
    if text.len() > 64 * 1024 * 1024 {
        return Err("native transcript size limit".into());
    }
    if variables == 0 || variables > 4096 {
        return Err("invalid variable count".into());
    }
    if text.lines().any(|l| l.trim_start().starts_with('?')) {
        return Err("native engine reported an error".into());
    }
    let lines: Vec<_> = text
        .lines()
        .map(str::trim)
        .filter(|l| !l.is_empty())
        .collect();
    let start = lines
        .iter()
        .position(|l| l.starts_with("ROOTS_"))
        .ok_or("missing protocol frame")?;
    let frame = &lines[start..];
    if frame.last() != Some(&"ROOTS_DONE") {
        return Err("incomplete native transcript or trailing data".into());
    }
    if frame.first() == Some(&"ROOTS_UNIT") {
        if frame != ["ROOTS_UNIT", "ROOTS_DONE"] {
            return Err("mixed or repeated native protocol frames".into());
        }
        return Ok(Basis {
            equations: vec![vec![Term {
                coefficient: 1u32.into(),
                exponents: vec![0; variables],
            }]],
            variables,
            engine_reported_unit: true,
        });
    }
    let mut it = frame[..frame.len() - 1].iter().copied();
    if it.next() != Some("ROOTS_BEGIN") {
        return Err("missing basis start".into());
    }
    let mut equations = vec![];
    let mut exponent_cells = 0usize;
    let mut ended = false;
    while let Some(line) = it.next() {
        match line.trim() {
            "ROOTS_END" => {
                ended = true;
                break;
            }
            "ROOTS_POLY" => {
                let mut terms = vec![];
                let mut complete = false;
                while let Some(line) = it.next() {
                    if line.trim() == "ROOTS_END_POLY" {
                        complete = true;
                        break;
                    }
                    if line.trim() != "ROOTS_TERM" {
                        return Err("unexpected basis protocol token".into());
                    }
                    let c = coefficient(it.next().ok_or("missing coefficient")?.trim(), f)?;
                    let e: Vec<u32> = it
                        .next()
                        .ok_or("missing exponents")?
                        .trim()
                        .split(',')
                        .map(|v| v.trim().parse().map_err(|_| "invalid exponent".to_string()))
                        .collect::<Result<_>>()?;
                    exponent_cells = exponent_cells
                        .checked_add(e.len())
                        .ok_or("protocol size overflow")?;
                    if e.len() != variables
                        || exponent_cells > 2_000_000
                        || e.iter().any(|v| *v > 4096)
                    {
                        return Err("basis protocol shape/size limit".into());
                    }
                    terms.push(Term {
                        coefficient: c,
                        exponents: e,
                    });
                }
                if !complete {
                    return Err("incomplete polynomial".into());
                }
                equations.push(terms);
            }
            _ => return Err("unexpected basis protocol token".into()),
        }
    }
    if !ended || equations.is_empty() || it.next().is_some() {
        return Err("incomplete/empty basis".into());
    }
    Ok(Basis {
        equations,
        variables,
        engine_reported_unit: false,
    })
}
fn specialize(
    poly: &[Term],
    j: usize,
    values: &[BigUint],
    f: &Field,
    w: &mut Limits,
) -> Result<Option<Uni>> {
    if poly.iter().any(|t| t.exponents[..j].iter().any(|e| *e > 0)) {
        return Ok(None);
    }
    let degree = poly
        .iter()
        .map(|t| t.exponents[j] as usize)
        .max()
        .unwrap_or(0);
    if degree > w.max_degree {
        return Err("specialization degree limit; inconclusive".into());
    }
    let mut out = vec![0u32.into(); degree + 1];
    for t in poly {
        w.charge(1 + t.exponents[j + 1..].iter().filter(|e| **e > 0).count())?;
        let mut c = t.coefficient.clone();
        for (i, e) in t.exponents.iter().enumerate().skip(j + 1) {
            if *e > 0 {
                c = f.mul(&c, &values[i].modpow(&BigUint::from(*e), &f.p));
            }
        }
        let d = t.exponents[j] as usize;
        out[d] = f.add(&out[d], &c);
    }
    Ok(Some(Uni::new(out)))
}
impl Basis {
    pub fn assignments(&self, f: &Field, w: &mut Limits) -> Result<Vec<Vec<BigUint>>> {
        fn visit(
            b: &Basis,
            j: usize,
            values: &mut Vec<BigUint>,
            f: &Field,
            w: &mut Limits,
            out: &mut Vec<Vec<BigUint>>,
        ) -> Result<()> {
            let mut q: Option<Uni> = None;
            for poly in &b.equations {
                if let Some(p) = specialize(poly, j, values, f, w)? {
                    match p.degree() {
                        None => {}
                        Some(0) => return Ok(()),
                        Some(_) => q = Some(if let Some(q) = q { q.gcd(&p, f, w)? } else { p }),
                    }
                }
            }
            let q = q.ok_or("basis is not a complete triangular constraint; inconclusive")?;
            for x in roots(&q, f, w)? {
                w.branches += 1;
                if w.branches > w.max_assignments {
                    return Err("recovery branch limit; inconclusive".into());
                }
                values[j] = x;
                if j == 0 {
                    out.push(values.clone());
                } else {
                    visit(b, j - 1, values, f, w, out)?;
                }
            }
            Ok(())
        }
        let mut out = vec![];
        if self.variables == 0 {
            return Err("empty variable set".into());
        }
        visit(
            self,
            self.variables - 1,
            &mut vec![0u32.into(); self.variables],
            f,
            w,
            &mut out,
        )?;
        for values in &out {
            for p in &self.equations {
                let mut sum = BigUint::from(0u32);
                for t in p {
                    let mut c = t.coefficient.clone();
                    for (x, e) in values.iter().zip(&t.exponents) {
                        c = f.mul(&c, &x.modpow(&BigUint::from(*e), &f.p));
                    }
                    sum = f.add(&sum, &c);
                }
                if sum != BigUint::from(0u32) {
                    return Err("basis assignment substitution failed".into());
                }
            }
        }
        Ok(out)
    }
}
/// Valid triples are positive evidence only; an empty result is not an absence proof.
pub fn checked_triples(
    case: &Case,
    system: &System,
    basis: &Basis,
    w: &mut Limits,
) -> Result<(usize, Vec<Vec<BigUint>>)> {
    if basis.variables != system.variables.len() {
        return Err("basis/system variable mismatch".into());
    }
    let f = case.field()?;
    let curve = Curve::from_case(case)?;
    let assignments = basis.assignments(&f, w)?;
    let count = assignments.len();
    let mut triples = BTreeSet::new();
    for values in assignments {
        system.check(&values)?;
        let mut us = vec![];
        for y in &values[..3] {
            let den = f.sub(&1u32.into(), y);
            let Ok(inv) = f.inv(&den) else {
                break;
            };
            us.push(f.mul(&f.add(&1u32.into(), y), &inv));
        }
        if us.len() != 3 {
            continue;
        }
        let array: [BigUint; 3] = us.clone().try_into().map_err(|_| "bad triple")?;
        if curve.verify_triple(case, &array).is_ok() {
            us.sort();
            triples.insert(us);
        }
    }
    Ok((count, triples.into_iter().collect()))
}

pub fn engine_script(system: &System) -> Result<String> {
    let raw = system.singular();
    let prefix = raw
        .split_once("print(\"TORUS_STD_BEGIN\");")
        .ok_or("serializer protocol changed")?
        .0;
    Ok(format!("{prefix}\nideal G=std(I);\nif(size(G)==1 && G[1]==1){{print(\"ROOTS_UNIT\");}}\nelse{{\nring q=(integer,{}),({}),lp;\nshort=0;\nideal H=imap(r,G);\nideal L=std(H);\nprint(\"ROOTS_BEGIN\");\npoly rp;\nint gi;\nfor(gi=1;gi<=size(L);gi++){{\nprint(\"ROOTS_POLY\");\nrp=L[gi];\nwhile(rp!=0){{print(\"ROOTS_TERM\");print(string(leadcoef(rp)));print(string(leadexp(rp)));rp=rp-lead(rp);}}\nprint(\"ROOTS_END_POLY\");\n}}\nprint(\"ROOTS_END\");\n}}\nprint(\"ROOTS_DONE\");\nquit;\n",system.p,system.variables.join(",")))
}

#[cfg(test)]
mod tests {
    use super::*;
    fn uni(a: &[u32]) -> Uni {
        Uni::new(a.iter().map(|x| (*x).into()).collect())
    }
    #[test]
    fn exhaustive_cubic_roots_match_direct_evaluation() {
        let f = Field::new(5u32.into()).unwrap();
        for degree in 0..=3 {
            for n in 0..5usize.pow(degree as u32) {
                let mut k = n;
                let mut a = vec![];
                for _ in 0..degree {
                    a.push(BigUint::from(k % 5));
                    k /= 5;
                }
                a.push(1u32.into());
                let p = Uni(a);
                let expected: Vec<_> = (0u32..5)
                    .map(BigUint::from)
                    .filter(|x| p.eval(x, &f) == BigUint::from(0u32))
                    .collect();
                assert_eq!(roots(&p, &f, &mut Limits::default()).unwrap(), expected);
            }
        }
    }
    #[test]
    fn actual_prime_repeated_and_nonrational_factors() {
        let f = Field::new(torus_s4::curve25519_prime()).unwrap();
        let mut w = Limits::default();
        let mut p = Uni::constant(1);
        for r in [2u32, 17, 17, 29] {
            p = p
                .mul(
                    &Uni(vec![f.sub(&0u32.into(), &r.into()), 1u32.into()]),
                    &f,
                    &mut w,
                )
                .unwrap();
        }
        assert_eq!(
            roots(&p, &f, &mut Limits::default()).unwrap(),
            [2u32, 17, 29].map(BigUint::from)
        );
        let f = Field::new(13u32.into()).unwrap();
        assert!(roots(&uni(&[11, 0, 1]), &f, &mut Limits::default())
            .unwrap()
            .is_empty());
    }
    #[test]
    fn limits_and_zero_are_inconclusive() {
        let f = Field::new(13u32.into()).unwrap();
        assert!(roots(&Uni(vec![]), &f, &mut Limits::default()).is_err());
        let mut w = Limits {
            max_work: 0,
            ..Limits::default()
        };
        assert!(roots(&uni(&[12, 0, 1]), &f, &mut w).is_err());
        let mut w = Limits {
            split_attempts: 0,
            ..Limits::default()
        };
        assert!(roots(&uni(&[12, 0, 1]), &f, &mut w).is_err());
        assert_eq!(
            roots(&uni(&[13, 13, 1]), &f, &mut Limits::default()).unwrap(),
            vec![0u32.into()]
        );
    }
    #[test]
    fn triangular_assignments_and_missing_constraint() {
        let f = Field::new(13u32.into()).unwrap();
        let b = Basis {
            variables: 2,
            engine_reported_unit: false,
            equations: vec![
                vec![
                    Term {
                        coefficient: 1u32.into(),
                        exponents: vec![0, 2],
                    },
                    Term {
                        coefficient: 12u32.into(),
                        exponents: vec![0, 0],
                    },
                ],
                vec![
                    Term {
                        coefficient: 1u32.into(),
                        exponents: vec![1, 0],
                    },
                    Term {
                        coefficient: 12u32.into(),
                        exponents: vec![0, 1],
                    },
                ],
            ],
        };
        assert_eq!(
            b.assignments(&f, &mut Limits::default()).unwrap(),
            vec![
                vec![1u32.into(), 1u32.into()],
                vec![12u32.into(), 12u32.into()]
            ]
        );
        let bad = Basis {
            equations: vec![b.equations[1].clone()],
            ..b
        };
        assert!(bad.assignments(&f, &mut Limits::default()).is_err());
    }
    #[test]
    fn protocol_rejects_incomplete_and_invalid_shapes() {
        let f = Field::new(13u32.into()).unwrap();
        assert!(parse_basis(
            "ROOTS_BEGIN\nROOTS_POLY\nROOTS_TERM\n1\n0,1\nROOTS_END_POLY\nROOTS_END\nROOTS_DONE\n",
            1,
            &f
        )
        .is_err());
        assert!(parse_basis("ROOTS_UNIT\n", 1, &f).is_err());
        for mixed in [
            "ROOTS_UNIT\nROOTS_UNIT\nROOTS_DONE\n",
            "ROOTS_UNIT\nROOTS_BEGIN\nROOTS_END\nROOTS_DONE\n",
            "ROOTS_UNIT\nROOTS_DONE\nROOTS_DONE\n",
            "ROOTS_UNIT\nROOTS_DONE\ntrailing data\n",
            "ROOTS_BEGIN\nROOTS_POLY\nROOTS_TERM\n1\n1\nROOTS_END_POLY\nROOTS_END\nROOTS_UNIT\nROOTS_DONE\n",
        ] {
            assert!(parse_basis(mixed, 1, &f).is_err());
        }
        assert!(parse_basis("   ? engine error\nROOTS_UNIT\nROOTS_DONE\n", 1, &f).is_err());
        let good=parse_basis("ROOTS_BEGIN\nROOTS_POLY\nROOTS_TERM\n1\n1\nROOTS_TERM\n-2\n0\nROOTS_END_POLY\nROOTS_END\nROOTS_DONE\n",1,&f).unwrap();
        assert_eq!(
            good.assignments(&f, &mut Limits::default()).unwrap(),
            vec![vec![2u32.into()]]
        );
    }
}
