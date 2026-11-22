use crate::{producer::{self, Field}, replay, Lift, Matrix, ProjectionCertificate};

fn includes(f: Field, constraints: &Matrix, vectors: &[Vec<u64>]) -> Result<(), String> {
    for row in &constraints.rows { for v in vectors { if f.dot(row, v)? != 0 { return Err("producer inclusion residual: missing or inconsistent constraint".into()); } } }
    Ok(())
}

pub fn produce(prime: u64, full: &Matrix, lp_columns: usize, baseline: &Matrix, uncapped: &Matrix) -> Result<ProjectionCertificate, String> {
    let f = Field::new(prime)?;
    if lp_columns > full.ncols { return Err("LP prefix exceeds full width".into()); }
    let width = full.ncols - lp_columns;
    if baseline.ncols != width || uncapped.ncols != width || !uncapped.rows.starts_with(&baseline.rows) { return Err("baseline/uncapped shape or prefix mismatch".into()); }
    producer::shape(baseline, f)?;
    let a = producer::produce(prime, full)?;
    let projected = Matrix { ncols: width, rows: a.kernel.iter().map(|v| v[lp_columns..].to_vec()).collect() };
    let p = producer::produce(prime, &projected)?;
    let c = producer::produce(prime, &Matrix { ncols: width, rows: p.kernel.clone() })?;
    let u = producer::produce(prime, uncapped)?;
    includes(f, baseline, &projected.rows)?;
    includes(f, uncapped, &projected.rows)?;
    includes(f, baseline, &u.kernel)?;
    let transformed_full_lifts = producer::transport(f, &a.kernel, &p.operations)?;
    let mut constraint_kernel_lifts = Vec::new();
    for vector in &c.kernel {
        let image_coefficients: Vec<_> = p.pivots.iter().map(|&pivot| vector[pivot]).collect();
        let mut full_vector = vec![0; full.ncols];
        for (coefficient, lift) in image_coefficients.iter().zip(&transformed_full_lifts) {
            for j in 0..full.ncols { full_vector[j] = f.add(full_vector[j], f.mul(*coefficient, lift[j])); }
        }
        if full_vector[lp_columns..] != vector[..] { return Err("producer lift section mismatch".into()); }
        for row in &full.rows { if f.dot(row, &full_vector)? != 0 { return Err("producer full lift residual".into()); } }
        constraint_kernel_lifts.push(Lift { vector: vector.clone(), image_coefficients, full_vector });
    }
    Ok(ProjectionCertificate { lp_columns, a, p, c, u, transformed_full_lifts, constraint_kernel_lifts })
}

/// Reconstruct every projection and lift independently of producer arithmetic.
pub fn verify(prime: u64, full: &Matrix, lp_columns: usize, baseline: &Matrix, uncapped: &Matrix, cert: &ProjectionCertificate) -> Result<(), String> {
    if cert.lp_columns != lp_columns || lp_columns > full.ncols { return Err("projection LP binding mismatch".into()); }
    let width = full.ncols - lp_columns;
    if baseline.ncols != width || uncapped.ncols != width || !uncapped.rows.starts_with(&baseline.rows) { return Err("replay baseline/uncapped prefix binding mismatch".into()); }
    replay::verify(prime, full, &cert.a)?;
    let mut rows = Vec::new();
    for v in &cert.a.kernel { rows.push(v[lp_columns..].to_vec()); }
    let projected = Matrix { ncols: width, rows };
    replay::verify(prime, &projected, &cert.p)?;
    replay::verify(prime, &Matrix { ncols: width, rows: cert.p.kernel.clone() }, &cert.c)?;
    replay::verify(prime, uncapped, &cert.u)?;
    let transported = replay::apply_recorded(prime, &Matrix { ncols: full.ncols, rows: cert.a.kernel.clone() }, &cert.p.operations)?;
    if transported.rows != cert.transformed_full_lifts { return Err("full lift operation trace mismatch".into()); }
    for (i, vector) in transported.rows.iter().enumerate() {
        if vector[lp_columns..] != cert.p.rref.rows[i][..] { return Err("transformed full vector does not project to P row".into()); }
        for row in &full.rows { if replay::residue(row, vector, prime)? != 0 { return Err("transported full lift is not in A kernel".into()); } }
    }
    if cert.constraint_kernel_lifts.len() != cert.c.kernel.len() { return Err("missing constraint-kernel lift".into()); }
    let rank = cert.p.pivots.len();
    if cert.c.kernel.len() != rank { return Err("projected rank/constraint nullity mismatch".into()); }
    for (vector, lift) in cert.c.kernel.iter().zip(&cert.constraint_kernel_lifts) {
        if lift.vector != *vector || lift.image_coefficients.len() != rank || lift.full_vector.len() != full.ncols || lift.image_coefficients.iter().any(|&c| c >= prime) { return Err("lift width/canonical vector mismatch".into()); }
        let mut reconstructed = vec![0_u64; full.ncols];
        for (i, &coefficient) in lift.image_coefficients.iter().enumerate() {
            for (j, entry) in reconstructed.iter_mut().enumerate() {
                let value = u128::from(*entry) + u128::from(coefficient) * u128::from(transported.rows[i][j]);
                *entry = (value % u128::from(prime)) as u64;
            }
        }
        if reconstructed != lift.full_vector || reconstructed[lp_columns..] != vector[..] { return Err("lift combination or projection section mismatch".into()); }
        for row in &full.rows { if replay::residue(row, &lift.full_vector, prime)? != 0 { return Err("C-kernel full lift residual".into()); } }
    }
    for constraint in [&baseline.rows, &uncapped.rows] {
        for row in constraint {
            if row.len() != width || row.iter().any(|&c| c >= prime) { return Err("noncanonical constraint input".into()); }
            for projected_vector in &projected.rows {
                if replay::residue(row, projected_vector, prime)? != 0 { return Err("baseline/U does not annihilate full kernel projection".into()); }
            }
        }
    }
    for row in &baseline.rows { for vector in &cert.u.kernel { if replay::residue(row, vector, prime)? != 0 { return Err("baseline does not annihilate U kernel".into()); } } }
    Ok(())
}
