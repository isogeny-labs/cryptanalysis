//! Producer arithmetic uses Fermat inverses. The replayer has separate
//! arithmetic and Euclidean inverses and receives an external expected matrix.
use crate::{Certificate, Matrix, Operation};

#[derive(Clone, Copy)]
pub(crate) struct Field(pub u64);

impl Field {
    pub fn new(p: u64) -> Result<Self, String> {
        match p {
            101 | 2_773_073 => Ok(Self(p)),
            _ => Err(
                "only the declared development prime101 and frozen ell2773073 are admitted".into(),
            ),
        }
    }
    pub fn add(self, a: u64, b: u64) -> u64 {
        ((u128::from(a) + u128::from(b)) % u128::from(self.0)) as u64
    }
    pub fn mul(self, a: u64, b: u64) -> u64 {
        ((u128::from(a) * u128::from(b)) % u128::from(self.0)) as u64
    }
    pub fn neg(self, a: u64) -> u64 {
        if a == 0 {
            0
        } else {
            self.0 - a
        }
    }
    fn inverse(self, a: u64) -> u64 {
        let (mut power, mut exponent, mut result) = (a, self.0 - 2, 1);
        while exponent != 0 {
            if exponent & 1 != 0 {
                result = self.mul(result, power);
            }
            power = self.mul(power, power);
            exponent >>= 1;
        }
        result
    }
    pub fn dot(self, a: &[u64], b: &[u64]) -> Result<u64, String> {
        if a.len() != b.len() {
            return Err("dot length mismatch".into());
        }
        Ok(a.iter()
            .zip(b)
            .fold(0, |s, (&x, &y)| self.add(s, self.mul(x, y))))
    }
}

pub(crate) fn shape(matrix: &Matrix, f: Field) -> Result<(), String> {
    if matrix
        .rows
        .iter()
        .any(|r| r.len() != matrix.ncols || r.iter().any(|&x| x >= f.0))
    {
        return Err("matrix has ragged rows or noncanonical coefficients".into());
    }
    Ok(())
}

// Callers establish distinct in-range rows and equal widths before this helper.
fn add_scaled_row(f: Field, rows: &mut [Vec<u64>], dst: usize, src: usize, coefficient: u64) {
    let (destination, source) = if dst < src {
        let (before, after) = rows.split_at_mut(src);
        (&mut before[dst], &after[0])
    } else {
        let (before, after) = rows.split_at_mut(dst);
        (&mut after[0], &before[src])
    };
    for (value, &source_value) in destination.iter_mut().zip(source) {
        *value = f.add(*value, f.mul(coefficient, source_value));
    }
}

pub fn produce(p: u64, input: &Matrix) -> Result<Certificate, String> {
    let f = Field::new(p)?;
    shape(input, f)?;
    let mut rows = input.rows.clone();
    let mut operations = Vec::new();
    let mut pivots = Vec::new();
    for column in 0..input.ncols {
        let rank = pivots.len();
        let Some(found) = (rank..rows.len()).find(|&r| rows[r][column] != 0) else {
            continue;
        };
        if found != rank {
            rows.swap(found, rank);
            operations.push(Operation::Swap { a: found, b: rank });
        }
        let pivot = rows[rank][column];
        let coefficient = f.inverse(pivot);
        for x in &mut rows[rank] {
            *x = f.mul(*x, coefficient);
        }
        operations.push(Operation::Scale {
            row: rank,
            coefficient,
            inverse: pivot,
        });
        for row in 0..rows.len() {
            if row == rank || rows[row][column] == 0 {
                continue;
            }
            let coefficient = f.neg(rows[row][column]);
            add_scaled_row(f, &mut rows, row, rank, coefficient);
            operations.push(Operation::Add {
                dst: row,
                src: rank,
                coefficient,
            });
        }
        pivots.push(column);
    }
    let mut kernel = Vec::new();
    for free in 0..input.ncols {
        if pivots.contains(&free) {
            continue;
        }
        let mut v = vec![0; input.ncols];
        v[free] = 1;
        for (row, &pivot) in pivots.iter().enumerate() {
            v[pivot] = f.neg(rows[row][free]);
        }
        kernel.push(v);
    }
    Ok(Certificate {
        modulus: p,
        input: input.clone(),
        operations,
        rref: Matrix {
            ncols: input.ncols,
            rows,
        },
        pivots,
        kernel,
    })
}

/// Execute the produced operations on matching full lifts, without discarding
/// zero rows. The independent replayer implements this separately.
pub(crate) fn transport(
    f: Field,
    rows: &[Vec<u64>],
    operations: &[Operation],
) -> Result<Vec<Vec<u64>>, String> {
    let mut result = rows.to_vec();
    let width = result.first().map_or(0, Vec::len);
    if result.iter().any(|r| r.len() != width) {
        return Err("ragged lift rows".into());
    }
    for op in operations {
        match *op {
            Operation::Swap { a, b } => {
                if a >= result.len() || b >= result.len() {
                    return Err("lift swap bounds".into());
                }
                result.swap(a, b);
            }
            Operation::Scale {
                row, coefficient, ..
            } => {
                let r = result.get_mut(row).ok_or("lift scale bounds")?;
                for x in r {
                    *x = f.mul(*x, coefficient);
                }
            }
            Operation::Add {
                dst,
                src,
                coefficient,
            } => {
                if dst >= result.len() || src >= result.len() || dst == src {
                    return Err("lift add bounds/distinctness".into());
                }
                add_scaled_row(f, &mut result, dst, src, coefficient);
            }
        }
    }
    Ok(result)
}
