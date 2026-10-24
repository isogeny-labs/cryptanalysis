//! Cubic 3-gluing recognition: module certificates, not an evaluated attack.
//! Kept outside the frozen sweeper engine and checkpoint fingerprint.
use anyhow::{ensure, Result};
use clap::{Parser, Subcommand};
use ghs_sweeper::{field::Field, verify::RawField};
use serde_json::{json, Value};

type Vector = [u8; 6];
type Matrix = [[u8; 2]; 2];

#[derive(Parser)]
#[command(about = "Check cubic 3-gluing conditions; no target or explicit transfer is constructed")]
struct Args {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Matrix of q^3-Frobenius on E[3], row-major, over F3.
    Matrix {
        #[arg(long, num_args = 4)]
        entries: Vec<u8>,
        #[arg(long)]
        q_mod_3: u8,
    },
    /// One ordinary normalized curve over F_(2^(3d)).
    Curve {
        #[arg(long)]
        base_degree: u32,
        #[arg(long, default_value_t = 0)]
        a: u32,
        #[arg(long)]
        b: u32,
    },
}

fn sub(a: u8, b: u8) -> u8 {
    (a + 3 - b) % 3
}

fn determinant(m: Matrix) -> u8 {
    sub(m[0][0] * m[1][1] % 3, m[0][1] * m[1][0] % 3)
}

fn rank(mut rows: Vec<Vec<u8>>) -> usize {
    if rows.is_empty() {
        return 0;
    }
    let mut pivot = 0;
    for col in 0..rows[0].len() {
        let Some(found) = (pivot..rows.len()).find(|&r| rows[r][col] != 0) else {
            continue;
        };
        rows.swap(pivot, found);
        let inverse = rows[pivot][col]; // 1 and 2 are their own inverses.
        for c in &mut rows[pivot] {
            *c = *c * inverse % 3;
        }
        for r in 0..rows.len() {
            if r == pivot {
                continue;
            }
            let factor = rows[r][col];
            for c in col..rows[r].len() {
                rows[r][c] = sub(rows[r][c], factor * rows[pivot][c] % 3);
            }
        }
        pivot += 1;
        if pivot == rows.len() {
            break;
        }
    }
    pivot
}

fn pairing(v: &Vector, w: &Vector, q: u8) -> u8 {
    (0..3).fold(0, |sum, i| {
        let weight = if i == 1 { q } else { 1 };
        (sum + weight * sub(v[2 * i] * w[2 * i + 1] % 3, v[2 * i + 1] * w[2 * i] % 3)) % 3
    })
}

fn frobenius(v: &Vector, m: Matrix) -> Vector {
    [
        (m[0][0] * v[4] + m[0][1] * v[5]) % 3,
        (m[1][0] * v[4] + m[1][1] * v[5]) % 3,
        v[0],
        v[1],
        v[2],
        v[3],
    ]
}

fn isotropic(basis: &[Vector], q: u8) -> bool {
    basis
        .iter()
        .all(|v| basis.iter().all(|w| pairing(v, w, q) == 0))
}

fn transverse(basis: &[Vector]) -> bool {
    (0..3).all(|i| {
        rank(
            basis
                .iter()
                .map(|v| (0..6).filter(|c| c / 2 != i).map(|c| v[c]).collect())
                .collect(),
        ) == 3
    })
}

fn stable(basis: &[Vector], m: Matrix) -> bool {
    basis.iter().all(|v| {
        let mut rows: Vec<_> = basis.iter().map(|row| row.to_vec()).collect();
        rows.push(frobenius(v, m).to_vec());
        rank(rows) == 3
    })
}

fn validate_matrix(m: Matrix, q: u8) -> Result<()> {
    ensure!(q == 1 || q == 2, "q mod 3 must be 1 or 2");
    ensure!(
        m.iter().flatten().all(|&x| x < 3),
        "matrix entries must be 0, 1 or 2"
    );
    ensure!(
        determinant(m) == q,
        "matrix must have determinant q^3 = q mod 3"
    );
    for i in 0..6 {
        for j in 0..6 {
            let (mut v, mut w) = ([0; 6], [0; 6]);
            v[i] = 1;
            w[j] = 1;
            ensure!(
                pairing(&frobenius(&v, m), &frobenius(&w, m), q) == q * pairing(&v, &w, q) % 3,
                "weighted Frobenius similitude failed"
            );
        }
    }
    Ok(())
}

fn condition(m: Matrix, q: u8) -> bool {
    if q == 2 {
        (m[0][0] + m[1][1]).is_multiple_of(3)
    } else {
        m[0][1] == 0 && m[1][0] == 0 && m[0][0] == m[1][1]
    }
}

fn eigenvector(m: Matrix, lambda: u8) -> [u8; 2] {
    (1..9)
        .map(|i| [i % 3, i / 3])
        .find(|v| (0..2).all(|i| (m[i][0] * v[0] + m[i][1] * v[1]) % 3 == lambda * v[i] % 3))
        .expect("the positive case has the specified eigenvalue")
}

fn kernel(m: Matrix, q: u8) -> Result<Option<Vec<Vector>>> {
    validate_matrix(m, q)?;
    if !condition(m, q) {
        return Ok(None);
    }
    let basis = if q == 2 {
        let e = eigenvector(m, 1);
        let f = eigenvector(m, 2);
        vec![
            [e[0], e[1], e[0], e[1], e[0], e[1]],
            [f[0], f[1], f[0], f[1], 0, 0],
            [0, 0, f[0], f[1], f[0], f[1]],
        ]
    } else {
        let lambda = m[0][0];
        (0..3)
            .map(|j| {
                let mut v = [0; 6];
                for i in 0..3 {
                    let weight = if i == 1 { lambda } else { 1 };
                    v[2 * i] = weight;
                    v[2 * i + 1] = u8::from(i == j) * weight;
                }
                v
            })
            .collect()
    };
    ensure!(
        rank(basis.iter().map(|v| v.to_vec()).collect()) == 3,
        "kernel rank failed"
    );
    ensure!(isotropic(&basis, q), "kernel isotropy failed");
    ensure!(stable(&basis, m), "kernel Frobenius stability failed");
    ensure!(transverse(&basis), "kernel coordinate intersection failed");
    Ok(Some(basis))
}

fn trim(v: &mut Vec<u32>) {
    while v.last() == Some(&0) {
        v.pop();
    }
}

fn power(mut a: u32, mut exponent: u32, mul: impl Fn(u32, u32) -> u32) -> u32 {
    let mut value = 1;
    while exponent != 0 {
        if exponent & 1 != 0 {
            value = mul(value, a);
        }
        a = mul(a, a);
        exponent >>= 1;
    }
    value
}

fn remainder(
    mut p: Vec<u32>,
    h: &[u32],
    size: u32,
    mul: impl Fn(u32, u32) -> u32 + Copy,
) -> Vec<u32> {
    trim(&mut p);
    let inverse = power(*h.last().unwrap(), size - 2, mul);
    while p.len() >= h.len() {
        let factor = mul(*p.last().unwrap(), inverse);
        let offset = p.len() - h.len();
        for (i, &c) in h.iter().enumerate() {
            p[offset + i] ^= mul(factor, c);
        }
        trim(&mut p);
    }
    p
}

fn root_count(n: u32, b: u32, mul: impl Fn(u32, u32) -> u32 + Copy) -> usize {
    let h = vec![b, 0, 0, 1, 1];
    let mut v = vec![0, 1];
    for _ in 0..n {
        let mut square = vec![0; 2 * v.len() - 1];
        for (i, &c) in v.iter().enumerate() {
            square[2 * i] = mul(c, c);
        }
        v = remainder(square, &h, 1 << n, mul);
    }
    v.resize(v.len().max(2), 0);
    v[1] ^= 1;
    trim(&mut v);
    let mut a = h;
    while !v.is_empty() {
        let next = remainder(a, &v, 1 << n, mul);
        a = v;
        v = next;
    }
    a.len() - 1
}

fn curve(d: u32, a: u32, b: u32) -> Result<Value> {
    ensure!(
        (1..=6).contains(&d),
        "base degree must be 1..=6 (absolute degree at most 18)"
    );
    let n = 3 * d;
    let f = Field::new(n)?;
    ensure!(
        b != 0 && b < f.size && a < f.size,
        "invalid coefficients or singular b=0"
    );
    // Only mul/evaluate are used: no full raw trace/inverse tables are needed.
    let raw = RawField {
        degree: n,
        size: f.size,
        modulus: f.modulus,
        traces: Vec::new(),
        inverses: Vec::new(),
    };
    let roots = root_count(n, b, |x, y| f.mul(x, y));
    ensure!(
        roots == root_count(n, b, |x, y| raw.mul(x, y)),
        "raw root-gcd disagreement"
    );
    let mut x = b;
    let mut absolute_degree = 0;
    for i in 1..=n {
        x = raw.mul(x, x);
        if x == b {
            absolute_degree = i;
            break;
        }
    }
    ensure!(absolute_degree != 0, "coefficient orbit did not close");
    let q = if d.is_multiple_of(2) { 1 } else { 2 };
    let accepted = roots == if q == 2 { 2 } else { 4 };
    let geometric = accepted && d >= 2 && absolute_degree == n;
    Ok(json!({
        "kind": "binary-cubic-3-gluing-recognition/v1",
        "field": {"characteristic":2,"base_degree":d,"relative_degree":3,
                  "absolute_degree":n,"modulus":f.modulus,"encoding":"integer polynomial basis"},
        "curve": {"equation":"y^2+x*y=x^3+a*x^2+b","a":a,"b":b},
        "absolute_degree_b":absolute_degree,
        "absolute_trace_a":f.trace[a as usize],
        "division_polynomial":"X^4+X^3+b",
        "rational_division_roots":roots,
        "raw_arithmetic_root_check":true,
        "coordinate_transverse_rational_3_kernel_exists":accepted,
        "geometric_indecomposability_sufficient_hypotheses":geometric,
        "genus_three_transfer_for_one_source_twist_derived":geometric,
        "source_twist_selected":false,
        "target_equation_constructed":false,
        "explicit_isogeny_evaluated":false,
        "source_torsion_basis_constructed":false,
        "planted_log_verified":false,
        "publication_novelty_established":false,
        "curve_id":null,"candidate_id":null,"subgroup_order":null,
        "construction_cost":null,"transfer_cost":null,"solve_cost":null,"rho_cost":null,
        "interpretation":"Exact kernel-type criterion and conditional twist-pair existence; no catalogue promotion, selected twist, explicit transfer or cost claim. A negative kernel test does not exclude other descents."
    }))
}

fn main() -> Result<()> {
    let value = match Args::parse().command {
        Command::Curve { base_degree, a, b } => curve(base_degree, a, b)?,
        Command::Matrix { entries, q_mod_3 } => {
            let m = [[entries[0], entries[1]], [entries[2], entries[3]]];
            let certificate = kernel(m, q_mod_3)?;
            json!({"kind":"cubic-3-gluing-module/v1","matrix":m,"q_mod_3":q_mod_3,
                   "pairing_block_weights":[1,q_mod_3,1],"kernel_basis":certificate,
                   "source_torsion_basis_constructed":false,
                   "publication_novelty_established":false,
                   "interpretation":"Abstract transported module only; no source curve or explicit transfer is instantiated."})
        }
    };
    println!("{}", serde_json::to_string_pretty(&value)?);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    // Independent RREF enumeration, not the constructive kernel routine.
    fn all_lagrangians(q: u8) -> Vec<Vec<Vector>> {
        let mut found = Vec::new();
        for p0 in 0..4 {
            for p1 in p0 + 1..5 {
                for p2 in p1 + 1..6 {
                    let pivots = [p0, p1, p2];
                    let mut slots = Vec::new();
                    for (r, &pivot) in pivots.iter().enumerate() {
                        for c in pivot + 1..6 {
                            if !pivots.contains(&c) {
                                slots.push((r, c));
                            }
                        }
                    }
                    for mut code in 0..3_u32.pow(slots.len() as u32) {
                        let mut basis = vec![[0; 6]; 3];
                        for (r, &pivot) in pivots.iter().enumerate() {
                            basis[r][pivot] = 1;
                        }
                        for &(r, c) in &slots {
                            basis[r][c] = (code % 3) as u8;
                            code /= 3;
                        }
                        if isotropic(&basis, q) {
                            found.push(basis);
                        }
                    }
                }
            }
        }
        found
    }

    #[test]
    fn explicit_kernels_and_invalid_inputs() -> Result<()> {
        for (m, q) in [
            ([[1, 0], [0, 2]], 2),
            ([[1, 0], [0, 1]], 1),
            ([[2, 0], [0, 2]], 1),
        ] {
            assert!(kernel(m, q)?.is_some());
        }
        assert!(kernel([[0, 0], [0, 0]], 1).is_err());
        assert!(kernel([[1, 0], [0, 1]], 2).is_err());
        assert!(kernel([[3, 0], [0, 1]], 1).is_err());
        assert!(kernel([[1, 0], [0, 1]], 0).is_err());
        Ok(())
    }

    #[test]
    fn all_forty_eight_matrices_against_independent_subspaces() -> Result<()> {
        let spaces: Vec<_> = (1..=2).map(all_lagrangians).collect();
        for list in &spaces {
            assert_eq!(list.len(), 1120);
        }
        let mut checked = 0;
        for code in 0..81 {
            let m = [[code % 3, code / 3 % 3], [code / 9 % 3, code / 27 % 3]];
            let q = determinant(m);
            if q == 0 {
                continue;
            }
            let exists = spaces[(q - 1) as usize]
                .iter()
                .any(|l| transverse(l) && stable(l, m));
            assert_eq!(exists, condition(m, q), "M={m:?}, q={q}");
            assert_eq!(kernel(m, q)?.is_some(), exists);
            checked += 1;
        }
        assert_eq!(checked, 48);
        Ok(())
    }

    fn direct_roots(d: u32, b: u32) -> Result<usize> {
        let f = Field::new(3 * d)?;
        let raw = RawField {
            degree: f.degree,
            size: f.size,
            modulus: f.modulus,
            traces: Vec::new(),
            inverses: Vec::new(),
        };
        Ok((0..f.size)
            .filter(|&x| raw.evaluate(&[b, 0, 0, 1, 1], x) == 0)
            .count())
    }

    #[test]
    fn fixed_binary_coefficients_and_scope() -> Result<()> {
        for a in [0, 1] {
            let value = curve(3, a, 24)?;
            assert_eq!(value["rational_division_roots"], 2);
            assert_eq!(direct_roots(3, 24)?, 2);
            assert_eq!(value["absolute_degree_b"], 9);
            assert_eq!(
                value["genus_three_transfer_for_one_source_twist_derived"],
                true
            );
            assert_eq!(value["source_twist_selected"], false);
        }
        for (d, b) in [(2, 2), (1, 2), (3, 1)] {
            let value = curve(d, 0, b)?;
            assert_eq!(value["rational_division_roots"], direct_roots(d, b)?);
            if d == 1 || b == 1 {
                assert_eq!(
                    value["geometric_indecomposability_sufficient_hypotheses"],
                    false
                );
            }
        }
        assert!(curve(0, 0, 2).is_err());
        assert!(curve(7, 0, 2).is_err());
        assert!(curve(1, 0, 0).is_err());
        assert!(curve(1, 8, 2).is_err());
        assert!(curve(1, 0, 8).is_err());
        Ok(())
    }
}
