//! Independent replay: separate control flow, Euclidean inverse arithmetic,
//! complete RREF/free-column basis reconstruction and original-row residuals.
use crate::{Certificate, Matrix, Operation};

fn inverse(value: u64, prime: u64) -> Option<u64> {
    let (mut r0, mut r1) = (i128::from(prime), i128::from(value));
    let (mut t0, mut t1) = (0_i128, 1_i128);
    while r1 != 0 {
        let q = r0 / r1;
        (r0, r1) = (r1, r0 - q * r1);
        (t0, t1) = (t1, t0 - q * t1);
    }
    if r0 != 1 { None } else { Some(t0.rem_euclid(i128::from(prime)) as u64) }
}

pub(crate) fn residue(row: &[u64], vector: &[u64], prime: u64) -> Result<u64, String> {
    if row.len() != vector.len() { return Err("independent residual shape mismatch".into()); }
    let mut value = 0_u128;
    for k in 0..row.len() { value = (value + u128::from(row[k]) * u128::from(vector[k])) % u128::from(prime); }
    Ok(value as u64)
}

fn check_matrix(input: &Matrix, prime: u64) -> Result<(), String> {
    for row in &input.rows {
        if row.len() != input.ncols { return Err("independent matrix width mismatch".into()); }
        for &v in row { if v >= prime { return Err("independent noncanonical matrix entry".into()); } }
    }
    Ok(())
}

pub(crate) fn apply_recorded(prime: u64, input: &Matrix, operations: &[Operation]) -> Result<Matrix, String> {
    check_matrix(input, prime)?;
    let mut output = input.clone();
    let nrows = output.rows.len();
    for op in operations {
        match *op {
            Operation::Swap { a, b } => {
                if a >= nrows || b >= nrows || a == b { return Err("invalid independent swap".into()); }
                output.rows.swap(a, b);
            }
            Operation::Scale { row, coefficient, inverse: witness } => {
                if row >= nrows || coefficient >= prime || witness >= prime || inverse(coefficient, prime) != Some(witness) {
                    return Err("invalid independent scale/inverse".into());
                }
                for k in 0..output.ncols { output.rows[row][k] = (u128::from(output.rows[row][k]) * u128::from(coefficient) % u128::from(prime)) as u64; }
            }
            Operation::Add { dst, src, coefficient } => {
                if dst >= nrows || src >= nrows || dst == src || coefficient >= prime { return Err("invalid independent row addition".into()); }
                for k in 0..output.ncols {
                    let sum = u128::from(output.rows[dst][k]) + u128::from(coefficient) * u128::from(output.rows[src][k]);
                    output.rows[dst][k] = (sum % u128::from(prime)) as u64;
                }
            }
        }
    }
    Ok(output)
}

pub fn verify(prime: u64, expected: &Matrix, cert: &Certificate) -> Result<(), String> {
    if prime != 101 && prime != 2_773_073 { return Err("undeclared replay modulus".into()); }
    if cert.modulus != prime || cert.input != *expected { return Err("certificate source matrix/modulus binding mismatch".into()); }
    check_matrix(expected, prime)?;
    let got = apply_recorded(prime, expected, &cert.operations)?;
    if got != cert.rref { return Err("recorded RREF differs from independent row replay".into()); }
    let mut pivots = Vec::new();
    let mut seen_zero = false;
    for row in &got.rows {
        let Some(column) = row.iter().position(|&v| v != 0) else { seen_zero = true; continue; };
        if seen_zero || row[column] != 1 || pivots.last().is_some_and(|&old| old >= column) { return Err("not an ordered normalized RREF".into()); }
        pivots.push(column);
    }
    for (i, &pivot) in pivots.iter().enumerate() {
        for (j, row) in got.rows.iter().enumerate() {
            if i != j && row[pivot] != 0 { return Err("pivot column is not reduced".into()); }
        }
    }
    if pivots != cert.pivots { return Err("pivot list mismatch".into()); }
    let mut complete_basis = Vec::new();
    for column in 0..expected.ncols {
        if pivots.binary_search(&column).is_ok() { continue; }
        let mut vector = vec![0; expected.ncols];
        vector[column] = 1;
        for (r, &pivot) in pivots.iter().enumerate() {
            let value = got.rows[r][column];
            vector[pivot] = if value == 0 { 0 } else { prime - value };
        }
        complete_basis.push(vector);
    }
    if cert.kernel != complete_basis { return Err("incomplete or changed canonical kernel basis".into()); }
    for vector in &cert.kernel {
        for original in &expected.rows { if residue(original, vector, prime)? != 0 { return Err("original matrix kernel residual is nonzero".into()); } }
    }
    Ok(())
}
