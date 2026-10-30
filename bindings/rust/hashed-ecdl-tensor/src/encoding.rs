//! Linear-edge arithmetic and curve encodings from Bochum §2–3.

use crate::arithmetic::inverse;
use crate::curve::{Curve, Point};
use crate::finite::{Domain, PrimeDomain};
use crate::network::{
    Bit, FnPredicate, Network, Predicate, Program, Step, ValueFunction, Vertex, Word,
};
use crate::reduction::FactorBase;
use crate::{integrity, invalid, overflow, BigUint, Meter, Result};
use num_traits::{One, ToPrimitive, Zero};
use std::sync::Arc;

/// The explicit parameters of the two-stage Fourier multiplication gadget.
#[derive(Clone, Debug)]
pub struct MultiplicationParameters {
    /// Input integer width.
    pub d: usize,
    /// Power-of-two Fermat exponent; the ring modulus is 2^J+1.
    pub j: usize,
    /// Limb width J/4.
    pub k: usize,
    /// Number of unpadded limbs.
    pub n: usize,
    /// Power-of-two transform length.
    pub length: usize,
    /// First transform dimension.
    pub first: usize,
    /// Second transform dimension.
    pub second: usize,
}
impl MultiplicationParameters {
    /// Select parameters using integer inequalities only (Theorem 3).
    pub fn new(d: usize, meter: &Meter) -> Result<Self> {
        if d == 0 {
            return Err(invalid("zero multiplication width"));
        }
        meter.bits(d, "integer multiplication width")?;
        let bound = d
            .checked_add(1)
            .and_then(|n| n.checked_mul(64))
            .ok_or_else(|| overflow("Fourier parameters"))?;
        let mut j = 16usize;
        while j
            .checked_mul(j)
            .ok_or_else(|| overflow("Fourier exponent"))?
            < bound
        {
            j = j
                .checked_mul(2)
                .ok_or_else(|| overflow("Fourier exponent"))?;
        }
        let k = j / 4;
        let n = d.div_ceil(k);
        let length = n
            .checked_mul(2)
            .and_then(usize::checked_next_power_of_two)
            .ok_or_else(|| overflow("Fourier length"))?;
        let mu = length.trailing_zeros() as usize;
        let first = 1usize << (mu / 2);
        let second = length / first;
        if length > j / 2 || (2 * j) % length != 0 {
            return Err(integrity("Fourier parameter inequalities"));
        }
        meter.bits(j + 1, "Fourier ring width")?;
        meter.vector(length, "Fourier vector")?;
        Ok(Self {
            d,
            j,
            k,
            n,
            length,
            first,
            second,
        })
    }
}

/// Words representing a point: one identity bit and canonical coordinates.
#[derive(Clone, Debug)]
pub struct PointWords {
    /// Identity bit (one means the point at infinity).
    pub infinity: Word,
    /// Canonical abscissa, zero for infinity.
    pub x: Word,
    /// Canonical ordinate, zero for infinity.
    pub y: Word,
}

/// Builder for the built-in parsimonious encodings. Shared variables become
/// equality trees of maximum degree three, never hyperedges or self-loops.
#[derive(Default)]
pub struct Encoder {
    vertices: Vec<Vertex>,
    uses: Vec<Vec<(usize, usize)>>,
    free: Vec<usize>,
    steps: Vec<Step>,
    interface: Vec<usize>,
}
impl Encoder {
    /// Start an empty encoding.
    pub fn new() -> Self {
        Self::default()
    }

    fn fresh(&mut self, width: usize, free: bool, meter: &Meter) -> Result<Word> {
        meter.bits(width, "encoding word")?;
        meter.vector(
            self.uses
                .len()
                .checked_add(width)
                .ok_or_else(|| overflow("encoding signals"))?,
            "encoding signals",
        )?;
        let mut bits = Vec::with_capacity(width);
        for _ in 0..width {
            let signal = self.uses.len();
            self.uses.push(Vec::new());
            if free {
                self.free.push(signal);
            }
            bits.push(Bit::Signal(signal));
        }
        Ok(Word(bits))
    }

    /// Allocate a free input word, least-significant bit first.
    pub fn input_word(&mut self, width: usize, meter: &Meter) -> Result<Word> {
        if width == 0 {
            return Err(invalid("empty input word"));
        }
        self.fresh(width, true, meter)
    }
    /// A hardcoded public word; constants add no edge incidences.
    pub fn constant(width: usize, value: &BigUint) -> Result<Word> {
        if value.bits() > width as u64 {
            return Err(invalid("constant does not fit its word"));
        }
        Ok(Word(
            (0..width)
                .map(|i| Bit::Constant(value.bit(i as u64)))
                .collect(),
        ))
    }
    /// Zero-extend a word, rejecting truncation.
    pub fn pad(word: &Word, width: usize) -> Result<Word> {
        if width < word.width() {
            return Err(invalid("word padding would truncate"));
        }
        let mut bits = word.0.clone();
        bits.resize(width, Bit::Constant(false));
        Ok(Word(bits))
    }
    fn slice(word: &Word, start: usize, width: usize) -> Word {
        Word(
            (0..width)
                .map(|i| {
                    word.0
                        .get(start + i)
                        .copied()
                        .unwrap_or(Bit::Constant(false))
                })
                .collect(),
        )
    }

    fn constraint(
        &mut self,
        words: &[Word],
        function: impl Fn(&[BigUint], &mut Meter) -> Result<bool> + Send + Sync + 'static,
        meter: &Meter,
    ) -> Result<()> {
        let active: Vec<Bit> = words
            .iter()
            .flat_map(|w| w.0.iter().copied())
            .filter(|b| matches!(b, Bit::Signal(_)))
            .collect();
        meter.vector(self.vertices.len() + 1, "encoding vertices")?;
        let plan = words.to_vec();
        let predicate: Arc<dyn Predicate> =
            Arc::new(FnPredicate::new(active.len(), move |ports, work| {
                let mut cursor = 0;
                let mut values = Vec::with_capacity(plan.len());
                for word in &plan {
                    let mut value = BigUint::zero();
                    for (i, &bit) in word.0.iter().enumerate() {
                        let bit = match bit {
                            Bit::Constant(b) => b,
                            Bit::Signal(_) => {
                                let b = ports[cursor];
                                cursor += 1;
                                b
                            }
                        };
                        if bit {
                            value.set_bit(i as u64, true);
                        }
                    }
                    values.push(value);
                }
                function(&values, work)
            }));
        let vertex = self.vertices.len();
        self.vertices.push(Vertex {
            predicate,
            edges: vec![usize::MAX; active.len()],
        });
        for (port, bit) in active.iter().enumerate() {
            let Bit::Signal(signal) = *bit else {
                unreachable!()
            };
            self.uses[signal].push((vertex, port));
        }
        self.steps.push(Step::Check {
            vertex,
            ports: active,
        });
        Ok(())
    }

    fn define(
        &mut self,
        inputs: &[Word],
        widths: &[usize],
        function: ValueFunction,
        checked: bool,
        meter: &Meter,
    ) -> Result<Vec<Word>> {
        let outputs: Vec<_> = widths
            .iter()
            .map(|&width| self.fresh(width, false, meter))
            .collect::<Result<_>>()?;
        self.steps.push(Step::Define {
            inputs: inputs.to_vec(),
            outputs: outputs.clone(),
            function: function.clone(),
        });
        if checked {
            let mut ports = inputs.to_vec();
            ports.extend(outputs.clone());
            let count = inputs.len();
            self.constraint(
                &ports,
                move |values, work| Ok(function(&values[..count], work)? == values[count..]),
                meter,
            )?;
        }
        Ok(outputs)
    }

    /// Add a word's bits to the language interface. Repeated words get distinct
    /// equality-constrained interface edges, not duplicate edge identifiers.
    pub fn mark_interface(&mut self, word: &Word, meter: &Meter) -> Result<()> {
        for &bit in &word.0 {
            let signal = match bit {
                Bit::Signal(signal) => signal,
                Bit::Constant(value) => {
                    let out = self.define(
                        &[],
                        &[1],
                        Arc::new(move |_, _| Ok(vec![BigUint::from(u8::from(value))])),
                        true,
                        meter,
                    )?;
                    let Bit::Signal(signal) = out[0].0[0] else {
                        unreachable!()
                    };
                    signal
                }
            };
            self.interface.push(signal);
        }
        Ok(())
    }

    /// Assert bitwise equality, at constant-degree vertices.
    pub fn assert_equal(&mut self, left: &Word, right: &Word, meter: &Meter) -> Result<()> {
        if left.width() != right.width() {
            return Err(invalid("equality word widths"));
        }
        for i in 0..left.width() {
            self.constraint(
                &[Self::slice(left, i, 1), Self::slice(right, i, 1)],
                |v, _| Ok(v[0] == v[1]),
                meter,
            )?;
        }
        Ok(())
    }
    /// Assert gated equality; the selector is copied through equality trees.
    pub fn gated_equal(
        &mut self,
        selector: &Word,
        left: &Word,
        right: &Word,
        meter: &Meter,
    ) -> Result<()> {
        if selector.width() != 1 || left.width() != right.width() {
            return Err(invalid("gated equality widths"));
        }
        for i in 0..left.width() {
            self.constraint(
                &[
                    selector.clone(),
                    Self::slice(left, i, 1),
                    Self::slice(right, i, 1),
                ],
                |v, _| Ok(v[0].is_zero() || v[1] == v[2]),
                meter,
            )?;
        }
        Ok(())
    }
    /// Boolean negation.
    pub fn not(&mut self, bit: &Word, meter: &Meter) -> Result<Word> {
        if bit.width() != 1 {
            return Err(invalid("selector width"));
        }
        Ok(self
            .define(
                std::slice::from_ref(bit),
                &[1],
                Arc::new(|v, _| Ok(vec![BigUint::from(u8::from(v[0].is_zero()))])),
                true,
                meter,
            )?
            .remove(0))
    }
    /// Boolean conjunction.
    pub fn and(&mut self, a: &Word, b: &Word, meter: &Meter) -> Result<Word> {
        if a.width() != 1 || b.width() != 1 {
            return Err(invalid("selector width"));
        }
        Ok(self
            .define(
                &[a.clone(), b.clone()],
                &[1],
                Arc::new(|v, _| Ok(vec![&v[0] * &v[1]])),
                true,
                meter,
            )?
            .remove(0))
    }
    /// Boolean disjunction.
    pub fn or(&mut self, a: &Word, b: &Word, meter: &Meter) -> Result<Word> {
        if a.width() != 1 || b.width() != 1 {
            return Err(invalid("selector width"));
        }
        Ok(self
            .define(
                &[a.clone(), b.clone()],
                &[1],
                Arc::new(|v, _| {
                    Ok(vec![BigUint::from(u8::from(
                        !v[0].is_zero() || !v[1].is_zero(),
                    ))])
                }),
                true,
                meter,
            )?
            .remove(0))
    }
    /// Exact ripple zero test (Lemma 2), with uniquely determined state bits.
    pub fn zero_test(&mut self, word: &Word, meter: &Meter) -> Result<Word> {
        let mut seen = Self::constant(1, &BigUint::zero())?;
        for i in 0..word.width() {
            seen = self.or(&seen, &Self::slice(word, i, 1), meter)?;
        }
        self.not(&seen, meter)
    }
    /// Unsigned comparison, propagated from low to high bits.
    pub fn less_than(&mut self, a: &Word, b: &Word, meter: &Meter) -> Result<Word> {
        if a.width() != b.width() {
            return Err(invalid("comparison widths"));
        }
        let mut less = Self::constant(1, &BigUint::zero())?;
        for i in 0..a.width() {
            less = self
                .define(
                    &[Self::slice(a, i, 1), Self::slice(b, i, 1), less],
                    &[1],
                    Arc::new(|v, _| {
                        Ok(vec![if v[0] == v[1] {
                            v[2].clone()
                        } else {
                            BigUint::from(u8::from(v[0] < v[1]))
                        }])
                    }),
                    true,
                    meter,
                )?
                .remove(0);
        }
        Ok(less)
    }
    fn canonical(&mut self, word: &Word, modulus: &BigUint, meter: &Meter) -> Result<()> {
        let bound = Self::constant(word.width(), modulus)?;
        let lt = self.less_than(word, &bound, meter)?;
        self.assert_equal(&lt, &Self::constant(1, &BigUint::one())?, meter)
    }

    /// Ripple integer addition, with a d+1-bit output and degree at most five.
    pub fn integer_add(&mut self, a: &Word, b: &Word, meter: &Meter) -> Result<Word> {
        if a.width() == 0 || a.width() != b.width() {
            return Err(invalid("integer addition widths"));
        }
        let mut carry = Self::constant(1, &BigUint::zero())?;
        let mut result = Vec::with_capacity(a.width() + 1);
        for i in 0..a.width() {
            let mut output = self.define(
                &[Self::slice(a, i, 1), Self::slice(b, i, 1), carry],
                &[1, 1],
                Arc::new(|v, _| {
                    let sum = v[0].to_u8().unwrap() + v[1].to_u8().unwrap() + v[2].to_u8().unwrap();
                    Ok(vec![BigUint::from(sum & 1), BigUint::from(sum >> 1)])
                }),
                true,
                meter,
            )?;
            result.push(output[0].0[0]);
            carry = output.remove(1);
        }
        result.push(carry.0[0]);
        Ok(Word(result))
    }

    fn transform(
        &mut self,
        input: &[Word],
        omega: &BigUint,
        modulus: &BigUint,
        params: &MultiplicationParameters,
        inverse_scale: bool,
        meter: &Meter,
    ) -> Result<Vec<Word>> {
        let width = params.j + 1;
        let mut middle = vec![Vec::<Word>::new(); params.second];
        for j2 in 0..params.second {
            let inputs: Vec<_> = (0..params.first)
                .map(|j1| input[params.second * j1 + j2].clone())
                .collect();
            let (omega, modulus, p) = (omega.clone(), modulus.clone(), params.clone());
            middle[j2] = self.define(
                &inputs,
                &vec![width; p.first],
                Arc::new(move |v, work| {
                    let mut out = Vec::with_capacity(p.first);
                    for t1 in 0..p.first {
                        let mut sum = BigUint::zero();
                        for j1 in 0..p.first {
                            work.charge(1, "Fourier column transform")?;
                            let exponent = BigUint::from(p.second * j1 * t1);
                            sum = (sum + &v[j1] * omega.modpow(&exponent, &modulus)) % &modulus;
                        }
                        out.push(sum * omega.modpow(&BigUint::from(j2 * t1), &modulus) % &modulus);
                    }
                    Ok(out)
                }),
                true,
                meter,
            )?;
        }
        let mut out: Vec<Option<Word>> = vec![None; params.length];
        for t1 in 0..params.first {
            let inputs: Vec<_> = (0..params.second)
                .map(|j2| middle[j2][t1].clone())
                .collect();
            let (omega, modulus, p) = (omega.clone(), modulus.clone(), params.clone());
            let scale = if inverse_scale {
                inverse(&BigUint::from(params.length), &modulus)?
            } else {
                BigUint::one()
            };
            let result = self.define(
                &inputs,
                &vec![width; p.second],
                Arc::new(move |v, work| {
                    let mut out = Vec::with_capacity(p.second);
                    for t2 in 0..p.second {
                        let mut sum = BigUint::zero();
                        for j2 in 0..p.second {
                            work.charge(1, "Fourier row transform")?;
                            let exponent = BigUint::from(p.first * j2 * t2);
                            sum = (sum + &v[j2] * omega.modpow(&exponent, &modulus)) % &modulus;
                        }
                        out.push(sum * &scale % &modulus);
                    }
                    Ok(out)
                }),
                true,
                meter,
            )?;
            for t2 in 0..params.second {
                out[t1 + params.first * t2] = Some(result[t2].clone());
            }
        }
        out.into_iter()
            .map(|w| w.ok_or_else(|| integrity("Fourier output permutation")))
            .collect()
    }

    /// Theorem 3's two-stage Fourier encoding, not a single high-degree multiply
    /// vertex and not a conventional O(d log d)-edge multiplication circuit.
    pub fn integer_multiply(&mut self, a: &Word, b: &Word, meter: &Meter) -> Result<Word> {
        if a.width() != b.width() {
            return Err(invalid("integer multiplication widths"));
        }
        let p = MultiplicationParameters::new(a.width(), meter)?;
        let modulus = (BigUint::one() << p.j) + BigUint::one();
        let omega = BigUint::one() << (2 * p.j / p.length);
        let padded = |word: &Word| -> Result<Vec<Word>> {
            (0..p.length)
                .map(|i| {
                    if i < p.n {
                        Ok(Self::slice(word, i * p.k, p.k))
                    } else {
                        Self::constant(p.k, &BigUint::zero())
                    }
                })
                .collect()
        };
        let fa = self.transform(&padded(a)?, &omega, &modulus, &p, false, meter)?;
        let fb = self.transform(&padded(b)?, &omega, &modulus, &p, false, meter)?;
        let mut products = Vec::with_capacity(p.length);
        for i in 0..p.length {
            let modulus = modulus.clone();
            products.push(
                self.define(
                    &[fa[i].clone(), fb[i].clone()],
                    &[p.j + 1],
                    Arc::new(move |v, work| {
                        work.charge(1, "Fourier pointwise product")?;
                        Ok(vec![&v[0] * &v[1] % &modulus])
                    }),
                    true,
                    meter,
                )?
                .remove(0),
            );
        }
        let coefficients = self.transform(
            &products,
            &inverse(&omega, &modulus)?,
            &modulus,
            &p,
            true,
            meter,
        )?;
        for coefficient in coefficients.iter().skip(2 * p.n - 1) {
            self.assert_equal(
                coefficient,
                &Self::constant(p.j + 1, &BigUint::zero())?,
                meter,
            )?;
        }
        let mut carry = Self::constant(p.j + 1, &BigUint::zero())?;
        let mut output = Vec::with_capacity(2 * p.n * p.k);
        for i in 0..2 * p.n {
            let coefficient = if i < 2 * p.n - 1 {
                coefficients[i].clone()
            } else {
                Self::constant(p.j + 1, &BigUint::zero())?
            };
            let k = p.k;
            let mut result = self.define(
                &[coefficient, carry],
                &[p.k, p.j + 1],
                Arc::new(move |v, work| {
                    work.charge(1, "integer product carries")?;
                    let sum = &v[0] + &v[1];
                    Ok(vec![
                        &sum & ((BigUint::one() << k) - BigUint::one()),
                        sum >> k,
                    ])
                }),
                true,
                meter,
            )?;
            output.extend(result[0].0.iter().copied());
            carry = result.remove(1);
        }
        self.assert_equal(&carry, &Self::constant(p.j + 1, &BigUint::zero())?, meter)?;
        let result = Word(output);
        for i in 2 * p.d..result.width() {
            self.assert_equal(
                &Self::slice(&result, i, 1),
                &Self::constant(1, &BigUint::zero())?,
                meter,
            )?;
        }
        Ok(Self::slice(&result, 0, 2 * p.d))
    }

    fn enforce_modular_add(
        &mut self,
        x: &Word,
        y: &Word,
        z: &Word,
        q: &BigUint,
        meter: &Meter,
    ) -> Result<()> {
        if x.width() != y.width() || x.width() != z.width() || q <= &BigUint::one() {
            return Err(invalid("modular addition shape"));
        }
        self.canonical(x, q, meter)?;
        self.canonical(y, q, meter)?;
        self.canonical(z, q, meter)?;
        let modulus = q.clone();
        let beta = self
            .define(
                &[x.clone(), y.clone()],
                &[1],
                Arc::new(move |v, _| Ok(vec![BigUint::from(u8::from(&v[0] + &v[1] >= modulus))])),
                false,
                meter,
            )?
            .remove(0);
        let scaled = Word(
            (0..x.width())
                .map(|i| {
                    if q.bit(i as u64) {
                        beta.0[0]
                    } else {
                        Bit::Constant(false)
                    }
                })
                .collect(),
        );
        let sum = self.integer_add(x, y, meter)?;
        let other = self.integer_add(z, &scaled, meter)?;
        self.assert_equal(&sum, &other, meter)
    }
    /// Canonical modular addition via the two integer identities of Lemma 8.
    pub fn modular_add(&mut self, x: &Word, y: &Word, q: &BigUint, meter: &Meter) -> Result<Word> {
        if x.width() != y.width() || q <= &BigUint::one() {
            return Err(invalid("modular addition shape"));
        }
        let modulus = q.clone();
        let z = self
            .define(
                &[x.clone(), y.clone()],
                &[x.width()],
                Arc::new(move |v, _| Ok(vec![(&v[0] + &v[1]) % &modulus])),
                false,
                meter,
            )?
            .remove(0);
        self.enforce_modular_add(x, y, &z, q, meter)?;
        Ok(z)
    }
    /// Canonical modular subtraction by checking `y+z=x`.
    pub fn modular_subtract(
        &mut self,
        x: &Word,
        y: &Word,
        q: &BigUint,
        meter: &Meter,
    ) -> Result<Word> {
        if x.width() != y.width() || q <= &BigUint::one() {
            return Err(invalid("modular subtraction shape"));
        }
        self.canonical(x, q, meter)?;
        self.canonical(y, q, meter)?;
        let modulus = q.clone();
        let z = self
            .define(
                &[x.clone(), y.clone()],
                &[x.width()],
                Arc::new(move |v, _| Ok(vec![(&v[0] + &modulus - &v[1]) % &modulus])),
                false,
                meter,
            )?
            .remove(0);
        self.enforce_modular_add(y, &z, x, q, meter)?;
        Ok(z)
    }
    /// Canonical modular multiplication, with compact integer products and the
    /// unique quotient witness in `xy = theta*q + z`.
    pub fn modular_multiply(
        &mut self,
        x: &Word,
        y: &Word,
        q: &BigUint,
        meter: &Meter,
    ) -> Result<Word> {
        if x.width() != y.width() || q <= &BigUint::one() {
            return Err(invalid("modular multiplication shape"));
        }
        self.canonical(x, q, meter)?;
        self.canonical(y, q, meter)?;
        let modulus = q.clone();
        let mut witnesses = self.define(
            &[x.clone(), y.clone()],
            &[x.width(), x.width()],
            Arc::new(move |v, _| {
                let product = &v[0] * &v[1];
                Ok(vec![&product % &modulus, product / &modulus])
            }),
            false,
            meter,
        )?;
        let z = witnesses.remove(0);
        let theta = witnesses.remove(0);
        self.canonical(&z, q, meter)?;
        let product = self.integer_multiply(x, y, meter)?;
        let quotient_product =
            self.integer_multiply(&theta, &Self::constant(x.width(), q)?, meter)?;
        let sum = self.integer_add(&quotient_product, &Self::pad(&z, 2 * x.width())?, meter)?;
        self.assert_equal(&Self::pad(&product, sum.width())?, &sum, meter)?;
        Ok(z)
    }

    /// Optional quadratic-edge schoolbook product with local ripple gates.
    /// Useful for comparing finite contraction width; the Fourier default stays
    /// unchanged. The output has the full sum of input widths, without truncation.
    pub fn schoolbook_multiply(&mut self, a: &Word, b: &Word, meter: &Meter) -> Result<Word> {
        if a.width() == 0 || b.width() == 0 {
            return Err(invalid("schoolbook input width"));
        }
        let width = a
            .width()
            .checked_add(b.width())
            .ok_or_else(|| overflow("schoolbook product"))?;
        meter.bits(width, "schoolbook output")?;
        meter.vector(width, "schoolbook row")?;
        let mut sum = Self::constant(width, &BigUint::zero())?;
        for j in 0..b.width() {
            let mut row = vec![Bit::Constant(false); width];
            for i in 0..a.width() {
                row[i + j] = self
                    .and(&Self::slice(a, i, 1), &Self::slice(b, j, 1), meter)?
                    .0[0];
            }
            let next = self.integer_add(&sum, &Word(row), meter)?;
            self.assert_equal(
                &Self::slice(&next, width, 1),
                &Self::constant(1, &BigUint::zero())?,
                meter,
            )?;
            sum = Self::slice(&next, 0, width);
        }
        Ok(sum)
    }

    /// Free inverse-hash selector with a uniquely derived canonical point.
    /// Invalid codes produce a rejected identity sentinel, not a false UNSAT.
    /// This finite decoder predicate has polynomial arithmetic cost; no small
    /// factor-rank promise or source assignment-count equivalence is asserted.
    pub fn selector_point(
        &mut self,
        curve: &Curve,
        base: &FactorBase,
        meter: &mut Meter,
    ) -> Result<PointWords> {
        let domain = PrimeDomain::new(base.clone(), meter)?;
        domain.validate(curve, meter)?;
        let input_width = (base.threshold() - BigUint::one()).bits().max(1) as usize;
        let input = self.input_word(input_width, meter)?;
        let width = curve.modulus().bits() as usize;
        let curve = curve.clone();
        let output = self.define(
            &[input],
            &[1, width, width],
            Arc::new(move |values, work| {
                let point = if &values[0] >= domain.limit() {
                    None
                } else {
                    domain.decode(&curve, &values[0], work)?
                };
                Ok(match point {
                    Some(Point::Affine { x, y }) => vec![BigUint::zero(), x, y],
                    _ => vec![BigUint::one(), BigUint::zero(), BigUint::zero()],
                })
            }),
            true,
            meter,
        )?;
        let point = PointWords {
            infinity: output[0].clone(),
            x: output[1].clone(),
            y: output[2].clone(),
        };
        self.assert_equal(
            &point.infinity,
            &Self::constant(1, &BigUint::zero())?,
            meter,
        )?;
        Ok(point)
    }

    /// Free point coordinates with an optional identity bit, followed by exact
    /// point-validity constraints. Nonidentity factor-base inputs hardcode zero.
    pub fn input_point(
        &mut self,
        curve: &Curve,
        allow_identity: bool,
        meter: &Meter,
    ) -> Result<PointWords> {
        let width = curve.modulus().bits() as usize;
        let infinity = if allow_identity {
            self.input_word(1, meter)?
        } else {
            Self::constant(1, &BigUint::zero())?
        };
        let x = self.input_word(width, meter)?;
        let y = self.input_word(width, meter)?;
        let point = PointWords { infinity, x, y };
        self.valid_point(curve, &point, meter)?;
        Ok(point)
    }

    /// Hardcode a canonical curve point.
    pub fn constant_point(curve: &Curve, point: &Point) -> Result<PointWords> {
        if !curve.contains(point) {
            return Err(invalid("constant point"));
        }
        let width = curve.modulus().bits() as usize;
        let (infinity, x, y) = match point {
            Point::Infinity => (BigUint::one(), BigUint::zero(), BigUint::zero()),
            Point::Affine { x, y } => (BigUint::zero(), x.clone(), y.clone()),
        };
        Ok(PointWords {
            infinity: Self::constant(1, &infinity)?,
            x: Self::constant(width, &x)?,
            y: Self::constant(width, &y)?,
        })
    }

    /// Add a point's flag and coordinate bits to the interface in that order.
    pub fn mark_point_interface(&mut self, point: &PointWords, meter: &Meter) -> Result<()> {
        self.mark_interface(&point.infinity, meter)?;
        self.mark_interface(&point.x, meter)?;
        self.mark_interface(&point.y, meter)
    }

    /// Assert equality of full canonical point encodings.
    pub fn assert_point_equal(
        &mut self,
        a: &PointWords,
        b: &PointWords,
        meter: &Meter,
    ) -> Result<()> {
        self.assert_equal(&a.infinity, &b.infinity, meter)?;
        self.assert_equal(&a.x, &b.x, meter)?;
        self.assert_equal(&a.y, &b.y, meter)
    }

    fn gated_point_equal(
        &mut self,
        selector: &Word,
        a: &PointWords,
        b: &PointWords,
        meter: &Meter,
    ) -> Result<()> {
        self.gated_equal(selector, &a.infinity, &b.infinity, meter)?;
        self.gated_equal(selector, &a.x, &b.x, meter)?;
        self.gated_equal(selector, &a.y, &b.y, meter)
    }

    fn valid_point(&mut self, curve: &Curve, point: &PointWords, meter: &Meter) -> Result<()> {
        let p = curve.modulus();
        let width = p.bits() as usize;
        if point.infinity.width() != 1 || point.x.width() != width || point.y.width() != width {
            return Err(invalid("point word widths"));
        }
        self.canonical(&point.x, p, meter)?;
        self.canonical(&point.y, p, meter)?;
        let zero = Self::constant(width, &BigUint::zero())?;
        self.gated_equal(&point.infinity, &point.x, &zero, meter)?;
        self.gated_equal(&point.infinity, &point.y, &zero, meter)?;
        let xx = self.modular_multiply(&point.x, &point.x, p, meter)?;
        let xxx = self.modular_multiply(&xx, &point.x, p, meter)?;
        let ax = self.modular_multiply(&point.x, &Self::constant(width, curve.a())?, p, meter)?;
        let rhs = self.modular_add(&xxx, &ax, p, meter)?;
        let rhs = self.modular_add(&rhs, &Self::constant(width, curve.b())?, p, meter)?;
        let yy = self.modular_multiply(&point.y, &point.y, p, meter)?;
        let finite = self.not(&point.infinity, meter)?;
        self.gated_equal(&finite, &yy, &rhs, meter)
    }

    /// Corollary 2's point-addition network. All expressions are evaluated
    /// unconditionally, including inactive branches. The inactive slope is zero,
    /// so auxiliary assignments remain unique in identity and inverse cases.
    pub fn point_add(
        &mut self,
        curve: &Curve,
        a: &PointWords,
        b: &PointWords,
        meter: &Meter,
    ) -> Result<PointWords> {
        self.valid_point(curve, a, meter)?;
        self.valid_point(curve, b, meter)?;
        let inputs = vec![
            a.infinity.clone(),
            a.x.clone(),
            a.y.clone(),
            b.infinity.clone(),
            b.x.clone(),
            b.y.clone(),
        ];
        let width = curve.modulus().bits() as usize;
        let c = curve.clone();
        let mut output = self.define(
            &inputs,
            &[1, width, width],
            Arc::new(move |v, work| {
                let point = |at: usize| {
                    if v[at].is_zero() {
                        Point::Affine {
                            x: v[at + 1].clone(),
                            y: v[at + 2].clone(),
                        }
                    } else {
                        Point::Infinity
                    }
                };
                match c.add(&point(0), &point(3), work)? {
                    Point::Infinity => Ok(vec![BigUint::one(), BigUint::zero(), BigUint::zero()]),
                    Point::Affine { x, y } => Ok(vec![BigUint::zero(), x, y]),
                }
            }),
            false,
            meter,
        )?;
        let infinity = output.remove(0);
        let x = output.remove(0);
        let y = output.remove(0);
        let result = PointWords { infinity, x, y };
        self.valid_point(curve, &result, meter)?;
        let c = curve.clone();
        let slope = self
            .define(
                &inputs,
                &[width],
                Arc::new(move |v, work| {
                    work.charge(1, "point slope witness")?;
                    let p = c.modulus();
                    if !v[0].is_zero()
                        || !v[3].is_zero()
                        || (v[1] == v[4] && (&v[2] + &v[5]) % p == BigUint::zero())
                    {
                        return Ok(vec![BigUint::zero()]);
                    }
                    let (num, den) = if v[1] == v[4] {
                        (
                            (BigUint::from(3u8) * &v[1] * &v[1] + c.a()) % p,
                            (&v[2] << 1) % p,
                        )
                    } else {
                        (c.sub(&v[5], &v[2]), c.sub(&v[4], &v[1]))
                    };
                    Ok(vec![num * inverse(&den, p)? % p])
                }),
                false,
                meter,
            )?
            .remove(0);
        let p = curve.modulus();
        self.canonical(&slope, p, meter)?;
        let dx = self.modular_subtract(&a.x, &b.x, p, meter)?;
        let sy = self.modular_add(&a.y, &b.y, p, meter)?;
        let same_x = self.zero_test(&dx, meter)?;
        let inverse_y = self.zero_test(&sy, meter)?;
        let finite_a = self.not(&a.infinity, meter)?;
        let finite_b = self.not(&b.infinity, meter)?;
        let both_finite = self.and(&finite_a, &finite_b, meter)?;
        let sigma2 = self.and(&finite_a, &b.infinity, meter)?;
        let same_x_finite = self.and(&both_finite, &same_x, meter)?;
        let sigma3 = self.and(&same_x_finite, &inverse_y, meter)?;
        let different_x = self.not(&same_x, meter)?;
        let sigma4 = self.and(&both_finite, &different_x, meter)?;
        let not_inverse = self.not(&inverse_y, meter)?;
        let sigma5 = self.and(&same_x_finite, &not_inverse, meter)?;
        let active = self.or(&sigma4, &sigma5, meter)?;
        self.gated_point_equal(&a.infinity, &result, b, meter)?;
        self.gated_point_equal(&sigma2, &result, a, meter)?;
        self.gated_point_equal(
            &sigma3,
            &result,
            &Self::constant_point(curve, &Point::Infinity)?,
            meter,
        )?;
        let x2_x1 = self.modular_subtract(&b.x, &a.x, p, meter)?;
        let y2_y1 = self.modular_subtract(&b.y, &a.y, p, meter)?;
        let generic_slope = self.modular_multiply(&slope, &x2_x1, p, meter)?;
        self.gated_equal(&sigma4, &generic_slope, &y2_y1, meter)?;
        let two_y = self.modular_add(&a.y, &a.y, p, meter)?;
        let square = self.modular_multiply(&a.x, &a.x, p, meter)?;
        let three_square = self.modular_multiply(
            &square,
            &Self::constant(width, &(BigUint::from(3u8) % p))?,
            p,
            meter,
        )?;
        let tangent =
            self.modular_add(&three_square, &Self::constant(width, curve.a())?, p, meter)?;
        let doubling_slope = self.modular_multiply(&slope, &two_y, p, meter)?;
        self.gated_equal(&sigma5, &doubling_slope, &tangent, meter)?;
        self.gated_equal(
            &active,
            &result.infinity,
            &Self::constant(1, &BigUint::zero())?,
            meter,
        )?;
        let slope_square = self.modular_multiply(&slope, &slope, p, meter)?;
        let expected_x = self.modular_subtract(&slope_square, &a.x, p, meter)?;
        let expected_x = self.modular_subtract(&expected_x, &b.x, p, meter)?;
        self.gated_equal(&active, &result.x, &expected_x, meter)?;
        let x_difference = self.modular_subtract(&a.x, &result.x, p, meter)?;
        let expected_y = self.modular_multiply(&slope, &x_difference, p, meter)?;
        let expected_y = self.modular_subtract(&expected_y, &a.y, p, meter)?;
        self.gated_equal(&active, &result.y, &expected_y, meter)?;
        let inactive = self.not(&active, meter)?;
        self.gated_equal(
            &inactive,
            &slope,
            &Self::constant(width, &BigUint::zero())?,
            meter,
        )?;
        Ok(result)
    }

    /// Fixed-cofactor membership certificate `A=[c]S`, costing O(log c) additions.
    /// Free S witnesses may project nonuniquely to A; the full network still
    /// counts every satisfying edge assignment exactly.
    pub fn clear_cofactor(
        &mut self,
        curve: &Curve,
        source: &PointWords,
        meter: &Meter,
    ) -> Result<PointWords> {
        let mut out = Self::constant_point(curve, &Point::Infinity)?;
        let mut base = source.clone();
        let mut c = curve.cofactor().clone();
        while !c.is_zero() {
            if c.bit(0) {
                out = self.point_add(curve, &out, &base, meter)?;
            }
            c >>= 1;
            if !c.is_zero() {
                base = self.point_add(curve, &base, &base, meter)?;
            }
        }
        Ok(out)
    }

    /// Encode the affine hash membership predicate for a certified public prime
    /// `2p <= s <= 4p`. Constants and coordinate bit copies do not use a list.
    pub fn hash_member(
        &mut self,
        curve: &Curve,
        point: &PointWords,
        s: &BigUint,
        alpha: &BigUint,
        beta: &BigUint,
        tau: &BigUint,
        meter: &Meter,
    ) -> Result<()> {
        if s < &(curve.modulus() << 1)
            || s > &(curve.modulus() << 2)
            || alpha.is_zero()
            || alpha >= s
            || beta >= s
            || tau.is_zero()
            || tau > s
        {
            return Err(invalid("hash membership parameters"));
        }
        self.assert_equal(
            &point.infinity,
            &Self::constant(1, &BigUint::zero())?,
            meter,
        )?;
        let mut bits = vec![point.y.0[0]];
        bits.extend(point.x.0.iter().copied());
        let width = s.bits() as usize;
        let encoded = Self::pad(&Word(bits), width)?;
        let multiplied =
            self.modular_multiply(&encoded, &Self::constant(width, alpha)?, s, meter)?;
        let hashed = self.modular_add(&multiplied, &Self::constant(width, beta)?, s, meter)?;
        let accepted = self.less_than(&hashed, &Self::constant(width, tau)?, meter)?;
        self.assert_equal(&accepted, &Self::constant(1, &BigUint::one())?, meter)
    }

    /// Freeze shared signals into ordinary edges and constant-degree equality
    /// trees. The optional witness metadata contains no user-supplied hints.
    pub fn finish(mut self, meter: &Meter) -> Result<Network> {
        fn vertex(vertices: &mut Vec<Vertex>, arity: usize, equality: bool) -> usize {
            let id = vertices.len();
            vertices.push(Vertex {
                predicate: Arc::new(FnPredicate::new(arity, move |bits, _| {
                    Ok(!equality || bits.windows(2).all(|w| w[0] == w[1]))
                })),
                edges: vec![usize::MAX; arity],
            });
            id
        }
        fn connect(
            vertices: &mut [Vertex],
            edges: &mut Vec<(usize, usize)>,
            edge_signals: &mut Vec<usize>,
            a: (usize, usize),
            b: (usize, usize),
            signal: usize,
            meter: &Meter,
        ) -> Result<()> {
            if a.0 == b.0
                || vertices[a.0].edges[a.1] != usize::MAX
                || vertices[b.0].edges[b.1] != usize::MAX
            {
                return Err(integrity("encoding edge attachment"));
            }
            meter.vector(edges.len() + 1, "encoding edge count")?;
            let edge = edges.len();
            edges.push((a.0, b.0));
            edge_signals.push(signal);
            vertices[a.0].edges[a.1] = edge;
            vertices[b.0].edges[b.1] = edge;
            Ok(())
        }
        let mut interface_vertices = Vec::new();
        for &signal in &self.interface {
            let endpoint = vertex(&mut self.vertices, 1, false);
            self.uses[signal].push((endpoint, 0));
            interface_vertices.push(endpoint);
        }
        let mut edges = Vec::new();
        let mut edge_signals = Vec::new();
        for (signal, uses) in self.uses.iter_mut().enumerate() {
            while uses.len() < 2 {
                let endpoint = vertex(&mut self.vertices, 1, false);
                uses.push((endpoint, 0));
            }
            if uses.len() == 2 {
                if uses[0].0 != uses[1].0 {
                    connect(
                        &mut self.vertices,
                        &mut edges,
                        &mut edge_signals,
                        uses[0],
                        uses[1],
                        signal,
                        meter,
                    )?;
                } else {
                    let copy = vertex(&mut self.vertices, 2, true);
                    connect(
                        &mut self.vertices,
                        &mut edges,
                        &mut edge_signals,
                        uses[0],
                        (copy, 0),
                        signal,
                        meter,
                    )?;
                    connect(
                        &mut self.vertices,
                        &mut edges,
                        &mut edge_signals,
                        uses[1],
                        (copy, 1),
                        signal,
                        meter,
                    )?;
                }
            } else {
                let mut copy = vertex(&mut self.vertices, 3, true);
                connect(
                    &mut self.vertices,
                    &mut edges,
                    &mut edge_signals,
                    uses[0],
                    (copy, 0),
                    signal,
                    meter,
                )?;
                connect(
                    &mut self.vertices,
                    &mut edges,
                    &mut edge_signals,
                    uses[1],
                    (copy, 1),
                    signal,
                    meter,
                )?;
                for (i, &endpoint) in uses.iter().enumerate().skip(2) {
                    if i == uses.len() - 1 {
                        connect(
                            &mut self.vertices,
                            &mut edges,
                            &mut edge_signals,
                            endpoint,
                            (copy, 2),
                            signal,
                            meter,
                        )?;
                    } else {
                        let next = vertex(&mut self.vertices, 3, true);
                        connect(
                            &mut self.vertices,
                            &mut edges,
                            &mut edge_signals,
                            (copy, 2),
                            (next, 0),
                            signal,
                            meter,
                        )?;
                        connect(
                            &mut self.vertices,
                            &mut edges,
                            &mut edge_signals,
                            endpoint,
                            (next, 1),
                            signal,
                            meter,
                        )?;
                        copy = next;
                    }
                }
            }
        }
        meter.vector(self.vertices.len(), "encoding vertex count")?;
        let interface = interface_vertices
            .iter()
            .map(|&v| self.vertices[v].edges[0])
            .collect();
        if self.vertices.iter().any(|v| v.edges.contains(&usize::MAX)) {
            return Err(integrity("unattached encoding port"));
        }
        let program = Program {
            free: self.free,
            signals: self.uses.len(),
            steps: self.steps,
            edge_signals,
        };
        Ok(Network {
            vertices: self.vertices,
            edges,
            interface,
            model: Some(Arc::new(program)),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::Limits;
    fn bits(value: &BigUint, width: usize) -> Vec<bool> {
        (0..width).map(|i| value.bit(i as u64)).collect()
    }
    fn read(graph: &Network, assignment: &[bool], offset: usize, width: usize) -> BigUint {
        let mut out = BigUint::zero();
        for i in 0..width {
            if assignment[graph.interface()[offset + i]] {
                out.set_bit(i as u64, true);
            }
        }
        out
    }
    #[test]
    fn ripple_arithmetic_and_shared_word_copies() {
        let mut meter = Meter::new(Limits::default());
        let mut b = Encoder::new();
        let a = b.input_word(4, &meter).unwrap();
        let c = b.input_word(4, &meter).unwrap();
        let sum = b.integer_add(&a, &c, &meter).unwrap();
        let lt = b.less_than(&a, &c, &meter).unwrap();
        let zero = b.zero_test(&sum, &meter).unwrap();
        b.mark_interface(&sum, &meter).unwrap();
        b.mark_interface(&lt, &meter).unwrap();
        b.mark_interface(&zero, &meter).unwrap();
        let graph = b.finish(&meter).unwrap();
        for a in 0..16u8 {
            for c in 0..16u8 {
                let input = [bits(&a.into(), 4), bits(&c.into(), 4)].concat();
                let witness = graph
                    .witness_from_input_bits(&input, &mut meter)
                    .unwrap()
                    .unwrap();
                assert_eq!(read(&graph, &witness, 0, 5), BigUint::from(a + c));
                assert_eq!(read(&graph, &witness, 5, 1), BigUint::from(u8::from(a < c)));
                assert_eq!(
                    read(&graph, &witness, 6, 1),
                    BigUint::from(u8::from(a + c == 0))
                );
            }
        }
        assert!(graph.maximum_degree() <= 5);
    }
    #[test]
    fn fourier_products_match_independent_integer_products_and_size_bounds() {
        let mut meter = Meter::new(Limits {
            steps: 500_000_000,
            ..Limits::default()
        });
        for d in [1usize, 3, 4, 7, 16, 33, 65, 129, 257, 513] {
            let mut b = Encoder::new();
            let a = b.input_word(d, &meter).unwrap();
            let c = b.input_word(d, &meter).unwrap();
            let product = b.integer_multiply(&a, &c, &meter).unwrap();
            b.mark_interface(&a, &meter).unwrap();
            b.mark_interface(&c, &meter).unwrap();
            b.mark_interface(&product, &meter).unwrap();
            let graph = b.finish(&meter).unwrap();
            assert!(
                graph.edge_count() < 1100 * (d + 1),
                "d={d}, edges={}",
                graph.edge_count()
            );
            assert!(
                (graph.maximum_degree() as u128).pow(4) < 136u128.pow(4) * (d as u128 + 1).pow(3)
            );
            let mask = (BigUint::one() << d) - BigUint::one();
            let values = [BigUint::zero(), BigUint::one(), &mask >> 1, mask];
            for a in &values {
                for c in &values {
                    let input = [bits(a, d), bits(c, d)].concat();
                    let witness = graph
                        .witness_from_input_bits(&input, &mut meter)
                        .unwrap()
                        .unwrap();
                    assert_eq!(read(&graph, &witness, 2 * d, 2 * d), a * c, "d={d}");
                }
            }
        }
    }
    #[test]
    fn modular_words_are_canonical_and_invalid_inputs_have_no_witness() {
        let mut meter = Meter::new(Limits::default());
        let mut b = Encoder::new();
        let a = b.input_word(3, &meter).unwrap();
        let c = b.input_word(3, &meter).unwrap();
        let sum = b.modular_add(&a, &c, &BigUint::from(5u8), &meter).unwrap();
        let product = b
            .modular_multiply(&a, &c, &BigUint::from(5u8), &meter)
            .unwrap();
        b.mark_interface(&sum, &meter).unwrap();
        b.mark_interface(&product, &meter).unwrap();
        let graph = b.finish(&meter).unwrap();
        for a in 0..8u8 {
            for c in 0..8u8 {
                let input = [bits(&a.into(), 3), bits(&c.into(), 3)].concat();
                let witness = graph.witness_from_input_bits(&input, &mut meter).unwrap();
                if a >= 5 || c >= 5 {
                    assert!(witness.is_none());
                } else {
                    let witness = witness.unwrap();
                    assert_eq!(read(&graph, &witness, 0, 3), BigUint::from((a + c) % 5));
                    assert_eq!(read(&graph, &witness, 3, 3), BigUint::from(a * c % 5));
                }
            }
        }
    }

    fn point_bits(point: &Point, width: usize) -> Vec<bool> {
        match point {
            Point::Infinity => [vec![true], vec![false; 2 * width]].concat(),
            Point::Affine { x, y } => [vec![false], bits(x, width), bits(y, width)].concat(),
        }
    }
    fn read_point(graph: &Network, witness: &[bool], width: usize) -> Point {
        if !read(graph, witness, 0, 1).is_zero() {
            Point::Infinity
        } else {
            Point::Affine {
                x: read(graph, witness, 1, width),
                y: read(graph, witness, 1 + width, width),
            }
        }
    }
    #[test]
    fn point_network_handles_every_pair_and_rejects_counterfeit_outputs() {
        let mut meter = Meter::new(Limits {
            steps: 500_000_000,
            ..Limits::default()
        });
        let curves = [
            crate::curve::tiny(&mut meter),
            Curve::with_cofactor(
                5u8.into(),
                0u8.into(),
                1u8.into(),
                3u8.into(),
                2u8.into(),
                Point::Affine {
                    x: 0u8.into(),
                    y: 1u8.into(),
                },
                &mut meter,
            )
            .unwrap(),
        ];
        for curve in curves {
            let mut builder = Encoder::new();
            let a = builder.input_point(&curve, true, &meter).unwrap();
            let b = builder.input_point(&curve, true, &meter).unwrap();
            let output = builder.point_add(&curve, &a, &b, &meter).unwrap();
            builder.mark_point_interface(&output, &meter).unwrap();
            let graph = builder.finish(&meter).unwrap();
            let mut points = vec![Point::Infinity];
            for x in 0..5u8 {
                for y in 0..5u8 {
                    let point = Point::Affine {
                        x: x.into(),
                        y: y.into(),
                    };
                    if curve.contains(&point) {
                        points.push(point);
                    }
                }
            }
            for a in &points {
                for b in &points {
                    let inputs = [point_bits(a, 3), point_bits(b, 3)].concat();
                    let witness = graph
                        .witness_from_input_bits(&inputs, &mut meter)
                        .unwrap()
                        .unwrap();
                    assert_eq!(
                        read_point(&graph, &witness, 3),
                        curve.add(a, b, &mut meter).unwrap()
                    );
                    let signal = graph.model.as_ref().unwrap().edge_signals[graph.interface()[0]];
                    let mut counterfeit = witness;
                    for (edge, &which) in graph
                        .model
                        .as_ref()
                        .unwrap()
                        .edge_signals
                        .iter()
                        .enumerate()
                    {
                        if which == signal {
                            counterfeit[edge] = !counterfeit[edge];
                        }
                    }
                    assert!(!graph.evaluate(&counterfeit, &mut meter).unwrap());
                }
            }
        }
    }
    #[test]
    fn hash_membership_and_cofactor_clear_are_coordinate_predicates() {
        let mut meter = Meter::new(Limits {
            steps: 500_000_000,
            ..Limits::default()
        });
        let curve = crate::curve::tiny(&mut meter);
        let mut builder = Encoder::new();
        let a = builder.input_point(&curve, true, &meter).unwrap();
        builder
            .hash_member(
                &curve,
                &a,
                &11u8.into(),
                &7u8.into(),
                &3u8.into(),
                &5u8.into(),
                &meter,
            )
            .unwrap();
        let graph = builder.finish(&meter).unwrap();
        for k in 0..7u8 {
            let point = curve.mul(curve.generator(), &k.into(), &mut meter).unwrap();
            let witness = graph
                .witness_from_input_bits(&point_bits(&point, 3), &mut meter)
                .unwrap();
            let expected = point != Point::Infinity
                && (BigUint::from(7u8) * curve.encode(&point).unwrap() + BigUint::from(3u8)) % 11u8
                    < 5u8.into();
            assert_eq!(witness.is_some(), expected);
        }
        let curve = Curve::with_cofactor(
            5u8.into(),
            0u8.into(),
            1u8.into(),
            3u8.into(),
            2u8.into(),
            Point::Affine {
                x: 0u8.into(),
                y: 1u8.into(),
            },
            &mut meter,
        )
        .unwrap();
        let mut builder = Encoder::new();
        let source = builder.input_point(&curve, true, &meter).unwrap();
        let cleared = builder.clear_cofactor(&curve, &source, &meter).unwrap();
        builder.mark_point_interface(&cleared, &meter).unwrap();
        let graph = builder.finish(&meter).unwrap();
        for x in 0..5u8 {
            for y in 0..5u8 {
                let point = Point::Affine {
                    x: x.into(),
                    y: y.into(),
                };
                if !curve.contains(&point) {
                    continue;
                }
                let witness = graph
                    .witness_from_input_bits(&point_bits(&point, 3), &mut meter)
                    .unwrap()
                    .unwrap();
                let got = read_point(&graph, &witness, 3);
                assert_eq!(got, curve.mul(&point, &2u8.into(), &mut meter).unwrap());
                assert!(curve.in_subgroup(&got, &mut meter).unwrap());
            }
        }
    }
}
