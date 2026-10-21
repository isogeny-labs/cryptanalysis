use super::*;
use std::collections::BTreeSet;

#[derive(Clone, Debug)]
pub(super) enum Expr {
    Constant(u32),
    Variable(String),
    Add(Box<Expr>, Box<Expr>),
    Mul(Box<Expr>, Box<Expr>),
    Div(Box<Expr>, Box<Expr>),
    Pow(Box<Expr>, u32),
}

impl Expr {
    pub(super) fn parse(s: &str) -> Result<Self> {
        let mut p = Parser {
            text: s.as_bytes(),
            pos: 0,
        };
        let e = p.sum()?;
        p.space();
        if p.pos != p.text.len() {
            return Err(EfdError::Syntax(s.into()));
        }
        Ok(e)
    }
    pub(super) fn eval(&self, field: &IrreduciblePoly, values: &Bindings) -> Result<F2mElement> {
        let m = field.degree;
        Ok(match self {
            Self::Constant(n) => {
                if n % 2 == 0 {
                    F2mElement::zero(m)
                } else {
                    F2mElement::one(m)
                }
            }
            Self::Variable(v) => values
                .get(v)
                .cloned()
                .ok_or_else(|| EfdError::MissingInput(v.clone()))?,
            Self::Add(a, b) => a.eval(field, values)?.add(&b.eval(field, values)?),
            Self::Mul(a, b) => a.eval(field, values)?.mul(&b.eval(field, values)?, field),
            Self::Div(a, b) => {
                let inverse = b
                    .eval(field, values)?
                    .flt_inverse(field)
                    .ok_or(EfdError::ZeroDenominator)?;
                if matches!(**a, Self::Constant(1)) {
                    inverse
                } else {
                    a.eval(field, values)?.mul(&inverse, field)
                }
            }
            Self::Pow(a, n) => {
                let base = a.eval(field, values)?;
                if *n == 0 {
                    F2mElement::one(m)
                } else {
                    let mut out = base.clone();
                    for bit in (0..31 - n.leading_zeros()).rev() {
                        out = out.square(field);
                        if n & (1 << bit) != 0 {
                            out = out.mul(&base, field);
                        }
                    }
                    out
                }
            }
        })
    }
    fn variables(&self, out: &mut BTreeSet<String>) {
        match self {
            Self::Variable(v) => {
                out.insert(v.clone());
            }
            Self::Add(a, b) | Self::Mul(a, b) | Self::Div(a, b) => {
                a.variables(out);
                b.variables(out);
            }
            Self::Pow(a, _) => a.variables(out),
            Self::Constant(_) => {}
        }
    }
    fn renamed(&self, suffix: u32) -> Self {
        match self {
            Self::Variable(v) => Self::Variable(format!("{v}{suffix}")),
            Self::Add(a, b) => Self::Add(Box::new(a.renamed(suffix)), Box::new(b.renamed(suffix))),
            Self::Mul(a, b) => Self::Mul(Box::new(a.renamed(suffix)), Box::new(b.renamed(suffix))),
            Self::Div(a, b) => Self::Div(Box::new(a.renamed(suffix)), Box::new(b.renamed(suffix))),
            Self::Pow(a, n) => Self::Pow(Box::new(a.renamed(suffix)), *n),
            Self::Constant(n) => Self::Constant(*n),
        }
    }
    fn count(&self, c: &mut OperationCounts) {
        match self {
            Self::Add(a, b) => {
                a.count(c);
                b.count(c);
                c.additions += 1;
            }
            Self::Mul(a, b) => {
                a.count(c);
                b.count(c);
                c.multiplications += 1;
            }
            Self::Div(a, b) => {
                a.count(c);
                b.count(c);
                c.inversions += 1;
                if !matches!(**a, Self::Constant(1)) {
                    c.multiplications += 1;
                }
            }
            Self::Pow(a, n) => {
                a.count(c);
                if *n > 0 {
                    c.squarings += 31 - n.leading_zeros();
                    c.multiplications += n.count_ones() - 1;
                }
            }
            _ => {}
        }
    }
}

struct Parser<'a> {
    text: &'a [u8],
    pos: usize,
}
impl Parser<'_> {
    fn space(&mut self) {
        while self.text.get(self.pos).is_some_and(u8::is_ascii_whitespace) {
            self.pos += 1;
        }
    }
    fn take(&mut self, c: u8) -> bool {
        self.space();
        if self.text.get(self.pos) == Some(&c) {
            self.pos += 1;
            true
        } else {
            false
        }
    }
    fn sum(&mut self) -> Result<Expr> {
        let mut a = self.product()?;
        while self.take(b'+') || self.take(b'-') {
            a = Expr::Add(Box::new(a), Box::new(self.product()?));
        }
        Ok(a)
    }
    fn product(&mut self) -> Result<Expr> {
        let mut a = self.power()?;
        loop {
            if self.take(b'*') {
                a = Expr::Mul(Box::new(a), Box::new(self.power()?));
            } else if self.take(b'/') {
                a = Expr::Div(Box::new(a), Box::new(self.power()?));
            } else {
                self.space();
                if self
                    .text
                    .get(self.pos)
                    .is_some_and(|c| c.is_ascii_alphanumeric() || *c == b'(' || *c == b'_')
                {
                    a = Expr::Mul(Box::new(a), Box::new(self.power()?));
                } else {
                    break;
                }
            }
        }
        Ok(a)
    }
    fn power(&mut self) -> Result<Expr> {
        let a = self.atom()?;
        if self.take(b'^') {
            self.space();
            let start = self.pos;
            while self.text.get(self.pos).is_some_and(u8::is_ascii_digit) {
                self.pos += 1;
            }
            let n = std::str::from_utf8(&self.text[start..self.pos])
                .unwrap()
                .parse::<u32>()
                .map_err(|_| EfdError::Syntax("invalid exponent".into()))?;
            if n > 65536 {
                return Err(EfdError::Syntax("exponent limit".into()));
            }
            Ok(Expr::Pow(Box::new(a), n))
        } else {
            Ok(a)
        }
    }
    fn atom(&mut self) -> Result<Expr> {
        self.space();
        if self.take(b'(') {
            let e = self.sum()?;
            if !self.take(b')') {
                return Err(EfdError::Syntax("missing )".into()));
            }
            return Ok(e);
        }
        if self.take(b'-') {
            return self.atom();
        } // characteristic two
        let start = self.pos;
        if self.text.get(self.pos).is_some_and(u8::is_ascii_digit) {
            while self.text.get(self.pos).is_some_and(u8::is_ascii_digit) {
                self.pos += 1;
            }
            let n = std::str::from_utf8(&self.text[start..self.pos])
                .unwrap()
                .parse()
                .map_err(|_| EfdError::Syntax("integer overflow".into()))?;
            return Ok(Expr::Constant(n));
        }
        if self
            .text
            .get(self.pos)
            .is_some_and(|c| c.is_ascii_alphabetic() || *c == b'_')
        {
            while self
                .text
                .get(self.pos)
                .is_some_and(|c| c.is_ascii_alphanumeric() || *c == b'_')
            {
                self.pos += 1;
            }
            return Ok(Expr::Variable(
                std::str::from_utf8(&self.text[start..self.pos])
                    .unwrap()
                    .into(),
            ));
        }
        Err(EfdError::Syntax(format!(
            "expected expression at byte {}",
            self.pos
        )))
    }
}

/// Raw field operations in the straight-line program, including parameter
/// multiplications. Excludes parameter preparation, validation, point conversion
/// and walk selection. These counts are not timings or complete rho-step costs.
#[derive(Default, Debug, Clone, Copy, PartialEq, Eq)]
pub struct OperationCounts {
    pub multiplications: u32,
    pub squarings: u32,
    pub inversions: u32,
    pub additions: u32,
}

pub struct Program {
    instructions: Vec<(String, Expr)>,
    assumptions: Vec<(Expr, Expr)>,
    parameters: BTreeSet<String>,
    invariants: Vec<(Expr, Expr)>,
}

pub(super) fn equality(s: &str) -> Result<(Expr, Expr)> {
    let (a, b) = s
        .split_once('=')
        .ok_or_else(|| EfdError::Syntax(s.into()))?;
    Ok((Expr::parse(a)?, Expr::parse(b)?))
}

impl Program {
    pub(super) fn compile(formula: &Formula) -> Result<Self> {
        let rep = catalogue()
            .representation(&formula.representation)
            .ok_or_else(|| EfdError::Unsupported(formula.representation.clone()))?;
        let model = catalogue()
            .models
            .iter()
            .find(|m| formula.representation.starts_with(&format!("{}/", m.id)))
            .unwrap();
        let parameters = model
            .source
            .text
            .lines()
            .chain(formula.record.text.lines())
            .filter_map(|l| l.strip_prefix("parameter "))
            .map(|s| s.trim().to_owned())
            .collect();
        let assumptions = rep
            .assumptions
            .iter()
            .chain(&formula.assumptions)
            .map(|s| equality(s))
            .collect::<Result<_>>()?;
        let mut instructions = Vec::new();
        for line in formula
            .program
            .text
            .lines()
            .filter(|l| !l.trim().is_empty())
        {
            let (a, b) = line
                .split_once('=')
                .ok_or_else(|| EfdError::Syntax(line.into()))?;
            let name = a.trim();
            if !matches!(Expr::parse(name)?, Expr::Variable(_)) {
                return Err(EfdError::Syntax(line.into()));
            }
            instructions.push((name.into(), Expr::parse(b)?));
        }
        let mut invariants = Vec::new();
        for relation in &rep.relations {
            let pair = equality(relation)?;
            let mut vars = BTreeSet::new();
            pair.0.variables(&mut vars);
            pair.1.variables(&mut vars);
            if vars.iter().all(|v| rep.variables.contains(v)) {
                invariants.push(pair);
            }
        }
        Ok(Self {
            instructions,
            assumptions,
            parameters,
            invariants,
        })
    }
    pub fn operation_counts(&self) -> OperationCounts {
        let mut c = OperationCounts::default();
        for (_, e) in &self.instructions {
            e.count(&mut c);
        }
        c
    }
    /// Names read before assignment, including parameters required by assumptions.
    /// Derived cache parameters may instead be prepared from their definitions.
    pub fn required_inputs(&self) -> BTreeSet<String> {
        let mut assigned = BTreeSet::new();
        let mut out = BTreeSet::new();
        for (a, b) in &self.assumptions {
            a.variables(&mut out);
            b.variables(&mut out);
        }
        for (name, e) in &self.instructions {
            let mut vars = BTreeSet::new();
            e.variables(&mut vars);
            out.extend(vars.difference(&assigned).cloned());
            assigned.insert(name.clone());
        }
        out
    }
    fn derive(&self, field: &IrreduciblePoly, values: &mut Bindings) -> Result<()> {
        // Only declared parameters are derived, never missing point coordinates.
        for _ in 0..self.assumptions.len() + 1 {
            let before = values.len();
            for (a, b) in &self.assumptions {
                for (left, right) in [(a, b), (b, a)] {
                    let (name, power) = match left {
                        Expr::Variable(v) => (v, 1),
                        Expr::Pow(v, n) if n.is_power_of_two() => match &**v {
                            Expr::Variable(v) => (v, *n),
                            _ => continue,
                        },
                        _ => continue,
                    };
                    if !self.parameters.contains(name) || values.contains_key(name) {
                        continue;
                    }
                    match right.eval(field, values) {
                        Ok(mut value) => {
                            let steps = power.trailing_zeros() % field.degree;
                            if steps > 0 {
                                value = value.square_k_times(field.degree - steps, field);
                            }
                            values.insert(name.clone(), value);
                        }
                        Err(EfdError::MissingInput(_)) => {}
                        Err(e) => return Err(e),
                    }
                }
            }
            if values.len() == before {
                break;
            }
        }
        Ok(())
    }
    pub fn evaluate(&self, field: &IrreduciblePoly, inputs: &Bindings) -> Result<Bindings> {
        check_field(field, inputs)?;
        let mut values = inputs.clone();
        self.derive(field, &mut values)?;
        for (a, b) in &self.assumptions {
            if a.eval(field, &values)? != b.eval(field, &values)? {
                return Err(EfdError::Assumption(format!("{a:?} = {b:?}")));
            }
        }
        for index in 1..=3 {
            for (a, b) in &self.invariants {
                let (a, b) = (a.renamed(index), b.renamed(index));
                let mut vars = BTreeSet::new();
                a.variables(&mut vars);
                b.variables(&mut vars);
                if vars.iter().all(|v| values.contains_key(v))
                    && a.eval(field, &values)? != b.eval(field, &values)?
                {
                    return Err(EfdError::Assumption(format!(
                        "inconsistent coordinate cache at input {index}"
                    )));
                }
            }
        }
        for (name, e) in &self.instructions {
            let v = e.eval(field, &values)?;
            values.insert(name.clone(), v);
        }
        Ok(values)
    }
}
