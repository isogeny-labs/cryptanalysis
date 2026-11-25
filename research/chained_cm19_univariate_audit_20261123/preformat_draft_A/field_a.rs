use crate::{need, AResult};

pub const Q: u32 = 117_649;
pub const ZERO: F = F([0; 6]);
pub const ONE: F = F([1, 0, 0, 0, 0, 0]);
const MODULUS: [u32; 6] = [3, 6, 3, 5, 2, 0];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct F(pub [u8; 6]);

impl F {
    pub fn prime(n: i64) -> Self {
        let mut value = ZERO;
        value.0[0] = n.rem_euclid(7) as u8;
        value
    }
    pub fn plus(self, rhs: Self) -> Self {
        Self(std::array::from_fn(|i| (self.0[i] + rhs.0[i]) % 7))
    }
    pub fn neg(self) -> Self {
        Self(self.0.map(|x| (7 - x) % 7))
    }
    pub fn minus(self, rhs: Self) -> Self {
        self.plus(rhs.neg())
    }
    pub fn scale(self, n: u8) -> Self {
        Self(self.0.map(|x| ((u16::from(x) * u16::from(n)) % 7) as u8))
    }
    pub fn times(self, rhs: Self) -> Self {
        let mut coefficients = [0_u32; 11];
        for (i, &a) in self.0.iter().enumerate() {
            for (j, &b) in rhs.0.iter().enumerate() {
                coefficients[i + j] =
                    (coefficients[i + j] + u32::from(a) * u32::from(b)) % 7;
            }
        }
        for k in (6..11).rev() {
            let leading = coefficients[k];
            for (j, &coefficient) in MODULUS.iter().enumerate() {
                coefficients[k - 6 + j] =
                    (coefficients[k - 6 + j] + 49 - leading * coefficient) % 7;
            }
            coefficients[k] = 0;
        }
        Self(std::array::from_fn(|i| coefficients[i] as u8))
    }
    pub fn pow(self, mut exponent: u32) -> Self {
        let mut result = ONE;
        let mut power = self;
        while exponent != 0 {
            if exponent & 1 == 1 {
                result = result.times(power);
            }
            power = power.times(power);
            exponent >>= 1;
        }
        result
    }
    pub fn inverse(self) -> Self {
        assert_ne!(self, ZERO, "field inverse requires nonzero input");
        let result = self.pow(Q - 2);
        assert_eq!(self.times(result), ONE);
        result
    }
    pub fn over(self, rhs: Self) -> Self {
        self.times(rhs.inverse())
    }
}

pub struct Encoding {
    pub basis: [F; 6],
}
impl Encoding {
    pub fn decode(&self, mut value: u32) -> AResult<F> {
        need(value < Q, "noncanonical tower encoding")?;
        let mut result = ZERO;
        for &base in &self.basis {
            result = result.plus(base.scale((value % 7) as u8));
            value /= 7;
        }
        Ok(result)
    }
}

pub fn qualify() -> AResult<Encoding> {
    let z = F([0, 1, 0, 0, 0, 0]);
    let a_numerator = z.pow(3).plus(z.scale(4)).plus(F::prime(6));
    let denominator = z.pow(2).scale(3).plus(F::prime(5));
    let inverse = z.pow(4).scale(2).plus(z.pow(2).scale(3)).plus(z.scale(3)).plus(ONE);
    need(denominator.times(inverse) == ONE, "D inverse polynomial identity")?;
    need(a_numerator.pow(2) == denominator.pow(2).scale(3), "norm polynomial identity")?;
    let b = a_numerator.times(inverse);
    let a = z.minus(b);
    need(b.pow(2) == F::prime(3), "new model square relation")?;
    need(a.pow(3).plus(a.scale(2)).plus(F::prime(6)) == ZERO, "new model cubic relation")?;
    need((0..7).all(|n| F::prime(n).pow(3).plus(F::prime(2 * n + 6)) != ZERO), "cubic irreducibility over F7")?;
    need(F::prime(3).pow(171) == F::prime(-1), "nonsquare in odd cubic extension")?;
    let basis = [ONE, a, a.pow(2), b, a.times(b), a.pow(2).times(b)];
    let mut matrix: [[u8; 6]; 6] = std::array::from_fn(|i| std::array::from_fn(|j| basis[j].0[i]));
    for column in 0..6 {
        let pivot = (column..6).find(|&row| matrix[row][column] != 0).ok_or("basis change rank less than6")?;
        matrix.swap(column, pivot);
        let inverse = (1..7).find(|&n| (u16::from(matrix[column][column]) * n) % 7 == 1).ok_or("prime pivot inverse")?;
        for value in &mut matrix[column] {
            *value = ((u16::from(*value) * inverse) % 7) as u8;
        }
        let pivot_row = matrix[column];
        for (row_index, row) in matrix.iter_mut().enumerate() {
            if row_index != column {
                let factor = u16::from(row[column]);
                for (entry, pivot_entry) in row.iter_mut().zip(pivot_row) {
                    *entry = ((u16::from(*entry) + 49 - factor * u16::from(pivot_entry)) % 7) as u8;
                }
            }
        }
    }
    need(matrix == std::array::from_fn(|i| std::array::from_fn(|j| u8::from(i == j))), "full basis change inverse")?;
    // The tower is a field and this is a unital full-rank algebra map. Only now
    // is Fermat inversion used in this six-dimensional quotient.
    need(z.times(z.inverse()) == ONE, "field inverse after algebra isomorphism")?;
    need(a.pow(343) == a && b.pow(7) == b.neg(), "field Frobenius bridge")?;
    println!("FIELD_MODEL\tmodulus=[3,6,3,5,2,0,1]\ta={a:?}\tb={b:?}\tfull_rank=6\tPASS");
    Ok(Encoding { basis })
}
