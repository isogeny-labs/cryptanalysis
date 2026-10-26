//! Cubic prime-to-characteristic gluing module checks. No quotient or log map.
use anyhow::{ensure, Result};
use clap::{Parser, Subcommand};
use ghs_sweeper::{field::Field, verify::RawField};
use serde_json::{json, Value};
use std::collections::BTreeMap;

type V = [u16; 6];
type M = [[u16; 2]; 2];
type B = [V; 3];

#[derive(Parser)]
#[command(about = "Cubic gluing module criteria; no quotient, transfer, or novelty certificate")]
struct Args {
    #[command(subcommand)]
    command: Command,
}
#[derive(Subcommand)]
enum Command {
    Matrix {
        #[arg(long, default_value_t = 5)]
        ell: u16,
        #[arg(long)]
        q: u16,
        #[arg(long, num_args = 4)]
        entries: Vec<u16>,
    },
    /// Enumerate every GL2(F5) matrix and every weighted Lagrangian.
    Exhaustive,
    /// Exact, complete ordinary binary source-model census for d=3.
    BinaryCensus,
}

fn sub(a: u16, b: u16, p: u16) -> u16 {
    (a + p - b % p) % p
}
fn pow(mut a: u16, mut n: u16, p: u16) -> u16 {
    let mut r = 1;
    while n != 0 {
        if n & 1 != 0 {
            r = r * a % p;
        }
        a = a * a % p;
        n >>= 1;
    }
    r
}
fn det(m: M, p: u16) -> u16 {
    sub(m[0][0] * m[1][1] % p, m[0][1] * m[1][0] % p, p)
}
fn scalar(m: M) -> bool {
    m[0][1] == 0 && m[1][0] == 0 && m[0][0] == m[1][1]
}
fn eigenvalues(m: M, p: u16) -> Vec<u16> {
    (0..p)
        .filter(|&z| {
            sub(
                sub(z * z % p, (m[0][0] + m[1][1]) * z % p, p),
                p - det(m, p),
                p,
            ) == 0
        })
        .collect()
}
fn criterion(m: M, p: u16) -> bool {
    scalar(m) || eigenvalues(m, p).len() == 2
}
fn frob(v: V, m: M, p: u16) -> V {
    [
        (m[0][0] * v[4] + m[0][1] * v[5]) % p,
        (m[1][0] * v[4] + m[1][1] * v[5]) % p,
        v[0],
        v[1],
        v[2],
        v[3],
    ]
}
fn pairing(v: V, w: V, q: u16, p: u16) -> u16 {
    let mut sum = 0;
    let mut weight = 1;
    for i in 0..3 {
        sum = (sum + weight * sub(v[2 * i] * w[2 * i + 1] % p, v[2 * i + 1] * w[2 * i] % p, p)) % p;
        weight = weight * q % p;
    }
    sum
}
fn rank(mut rows: Vec<Vec<u16>>, p: u16) -> usize {
    let mut k = 0;
    for c in 0..rows[0].len() {
        let Some(j) = (k..rows.len()).find(|&j| rows[j][c] != 0) else {
            continue;
        };
        rows.swap(k, j);
        let inv = pow(rows[k][c], p - 2, p);
        for x in &mut rows[k] {
            *x = *x * inv % p;
        }
        for j in 0..rows.len() {
            if j == k {
                continue;
            }
            let a = rows[j][c];
            for t in c..rows[j].len() {
                rows[j][t] = sub(rows[j][t], a * rows[k][t] % p, p);
            }
        }
        k += 1;
        if k == rows.len() {
            break;
        }
    }
    k
}
fn transverse(b: B, p: u16) -> bool {
    (0..3).all(|i| {
        rank(
            b.iter()
                .map(|v| (0..6).filter(|&c| c / 2 != i).map(|c| v[c]).collect())
                .collect(),
            p,
        ) == 3
    })
}
fn check(b: B, m: M, q: u16, p: u16) -> Result<()> {
    ensure!(
        rank(b.iter().map(|r| r.to_vec()).collect(), p) == 3,
        "kernel rank"
    );
    ensure!(
        b.iter()
            .all(|&v| b.iter().all(|&w| pairing(v, w, q, p) == 0)),
        "isotropy"
    );
    for &v in &b {
        let mut rows: Vec<_> = b.iter().map(|r| r.to_vec()).collect();
        rows.push(frob(v, m, p).to_vec());
        ensure!(rank(rows, p) == 3, "Frobenius stability");
    }
    ensure!(transverse(b, p), "coordinate transversality");
    Ok(())
}
fn eigenvector(m: M, z: u16, p: u16) -> [u16; 2] {
    (1..p * p)
        .map(|x| [x % p, x / p])
        .find(|v| (0..2).all(|i| (m[i][0] * v[0] + m[i][1] * v[1]) % p == z * v[i] % p))
        .unwrap()
}
fn kernel(m: M, q: u16, p: u16) -> Result<Option<B>> {
    ensure!([5, 11].contains(&p), "implemented primes are 5 and 11");
    ensure!(
        q > 0 && q < p && m.iter().flatten().all(|&x| x < p),
        "noncanonical input"
    );
    ensure!(
        det(m, p) == pow(q, 3, p),
        "determinant must equal q^3, not q"
    );
    if !criterion(m, p) {
        return Ok(None);
    }
    let mut b = [[0; 6]; 3];
    if scalar(m) {
        let lambda = (1..p).find(|&x| pow(x, 3, p) == m[0][0]).unwrap();
        for (j, row) in b.iter_mut().enumerate() {
            for i in 0..3 {
                let scale = pow(pow(lambda, i as u16, p), p - 2, p);
                row[2 * i] = u16::from(i != j) * scale;
                row[2 * i + 1] = u16::from(i == j) * scale;
            }
        }
    } else {
        let roots = eigenvalues(m, p);
        let (e, f) = (eigenvector(m, roots[0], p), eigenvector(m, roots[1], p));
        let lambda = (1..p).find(|&x| pow(x, 3, p) == roots[0]).unwrap();
        let mut c = [0; 3];
        for i in 0..3 {
            let scale = pow(pow(lambda, i as u16, p), p - 2, p);
            for j in 0..2 {
                b[0][2 * i + j] = scale * e[j] % p;
            }
            c[i] = pow(q, i as u16, p) * scale % p;
        }
        for i in 0..2 {
            for j in 0..2 {
                b[i + 1][j] = c[i + 1] * f[j] % p;
                b[i + 1][2 * (i + 1) + j] = (p - c[0]) * f[j] % p;
            }
        }
    }
    check(b, m, q, p)?;
    Ok(Some(b))
}

#[derive(Clone, Copy)]
struct Rref {
    basis: B,
    pivots: [usize; 3],
    transverse: bool,
}
impl Rref {
    fn stable(self, m: M, p: u16) -> bool {
        self.basis.iter().all(|&v| {
            let mut w = frob(v, m, p);
            for r in 0..3 {
                let a = w[self.pivots[r]];
                for (c, x) in w.iter_mut().enumerate() {
                    *x = sub(*x, a * self.basis[r][c] % p, p);
                }
            }
            w == [0; 6]
        })
    }
}
fn enumerate(q: u16) -> Vec<Rref> {
    let mut out = Vec::new();
    for a in 0..4 {
        for b in a + 1..5 {
            for c in b + 1..6 {
                let pivots = [a, b, c];
                let mut basis = [[0; 6]; 3];
                for i in 0..3 {
                    basis[i][pivots[i]] = 1;
                }
                let free: Vec<_> = (0..3)
                    .flat_map(|r| {
                        (pivots[r] + 1..6)
                            .filter(move |t| !pivots.contains(t))
                            .map(move |t| (r, t))
                    })
                    .collect();
                for code in 0..5usize.pow(free.len() as u32) {
                    let mut n = code;
                    for &(r, t) in &free {
                        basis[r][t] = (n % 5) as u16;
                        n /= 5;
                    }
                    if pairing(basis[0], basis[1], q, 5) == 0
                        && pairing(basis[0], basis[2], q, 5) == 0
                        && pairing(basis[1], basis[2], q, 5) == 0
                    {
                        out.push(Rref {
                            basis,
                            pivots,
                            transverse: transverse(basis, 5),
                        });
                    }
                }
            }
        }
    }
    out
}
fn exhaustive() -> Result<Value> {
    let mut rows = Vec::new();
    let (mut total, mut positives) = (0, 0);
    let mut per_form = Vec::new();
    for q in 1..5 {
        let spaces = enumerate(q);
        ensure!(spaces.len() == 19656, "wrong Lagrangian enumeration size");
        per_form.push(json!({"q": q, "lagrangians": spaces.len(), "transverse_lagrangians": spaces.iter().filter(|s| s.transverse).count()}));
        for code in 0..625u16 {
            let m = [[code % 5, code / 5 % 5], [code / 25 % 5, code / 125]];
            if det(m, 5) != pow(q, 3, 5) {
                continue;
            }
            total += 1;
            let (mut stable, mut good) = (0, 0);
            for &s in &spaces {
                if s.stable(m, 5) {
                    stable += 1;
                    good += usize::from(s.transverse);
                }
            }
            let predicted = criterion(m, 5);
            ensure!(
                predicted == (good != 0),
                "criterion disagreement q={q} M={m:?}"
            );
            ensure!(
                kernel(m, q, 5)?.is_some() == predicted,
                "construction disagreement"
            );
            positives += usize::from(predicted);
            rows.push(json!({"q": q, "matrix": m, "stable": stable, "stable_transverse": good, "predicted": predicted}));
        }
    }
    ensure!(
        total == 480 && positives == 184,
        "wrong matrix class counts"
    );
    Ok(
        json!({"kind": "cubic-gluing-f5-exact-module-census/v1", "ell": 5, "matrices": total, "positive_matrices": positives, "disagreements": 0, "forms": per_form, "rows": rows, "quotient_constructed": false, "novel_affected_family_established": false}),
    )
}

fn source_order(n: u32, a: u32, b: u32, mul: impl Fn(u32, u32) -> u32 + Copy) -> u32 {
    let size = 1 << n;
    let mut count = 2; // O and the unique point above x=0.
    for x in 1..size {
        let mut z = 1;
        let mut u = x;
        let mut exponent = size - 2;
        while exponent != 0 {
            if exponent & 1 != 0 {
                z = mul(z, u);
            }
            u = mul(u, u);
            exponent >>= 1;
        }
        let rhs = x ^ a ^ mul(b, mul(z, z));
        let (mut trace, mut t) = (0, rhs);
        for _ in 0..n {
            trace ^= t;
            t = mul(t, t);
        }
        if trace == 0 {
            count += 2;
        }
    }
    count
}
fn binary_census() -> Result<Value> {
    let f = Field::new(9)?;
    let raw = RawField::new(9, f.modulus)?;
    let mut buckets: BTreeMap<(i64, bool, &'static str), (usize, u32, u32)> = BTreeMap::new();
    let mut models = 0;
    let mut added = 0;
    for b in 1..f.size {
        // Degree 9 has only the proper subfields F2 and F8.
        if pow_binary(b, 8, |x, y| f.mul(x, y)) == b {
            continue;
        }
        for a in [0, 1] {
            let order = source_order(9, a, b, |x, y| f.mul(x, y));
            ensure!(
                order == source_order(9, a, b, |x, y| raw.mul(x, y)),
                "raw point-count disagreement"
            );
            let t = 513 - i64::from(order);
            let three = t.rem_euclid(3) == 0;
            let delta = (t * t - 4 * 512).rem_euclid(5);
            let five = match delta {
                1 | 4 => "split_distinct",
                0 => "scalar_or_jordan_unresolved",
                _ => "irreducible",
            };
            let entry = buckets.entry((t, three, five)).or_insert((0, a, b));
            entry.0 += 1;
            models += 1;
            added += usize::from(!three && five == "split_distinct");
        }
    }
    ensure!(models == 1008, "full-absolute-degree model scope changed");
    let rows: Vec<_> = buckets.into_iter().map(|((trace, three, five), (count,a,b))| json!({"trace": trace, "models": count, "three_kernel": three, "five_module_status": five, "representative": {"a": a,"b":b}, "source_order": 513-trace})).collect();
    Ok(
        json!({"kind":"binary-cubic-gluing-trace-census/v1", "base_degree":3,"absolute_degree":9,"modulus":f.modulus,"full_absolute_degree_models":models,"five_positive_three_negative_models":added,"arithmetic_backends_agree":true,"rows":rows,"excluded_koblitz_b":1,"curve_id":null,"subgroup_generator":null,"quotient_constructed":false,"log_transfer_verified":false,"novel_affected_family_established":false}),
    )
}
fn pow_binary(mut a: u32, mut n: u32, mul: impl Fn(u32, u32) -> u32) -> u32 {
    let mut r = 1;
    while n != 0 {
        if n & 1 != 0 {
            r = mul(r, a);
        }
        a = mul(a, a);
        n >>= 1;
    }
    r
}
fn main() -> Result<()> {
    let value = match Args::parse().command {
        Command::Matrix { ell, q, entries } => {
            let m = [[entries[0], entries[1]], [entries[2], entries[3]]];
            let basis = kernel(m, q, ell)?;
            json!({"ell":ell,"q":q,"matrix":m,"stable_transverse_kernel":basis.is_some(),"basis":basis,"quotient_constructed":false,"log_transfer_verified":false})
        }
        Command::Exhaustive => exhaustive()?,
        Command::BinaryCensus => binary_census()?,
    };
    println!("{}", serde_json::to_string_pretty(&value)?);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn split_scalar_jordan_and_irreducible() {
        assert!(kernel([[3, 0], [0, 4]], 3, 5).unwrap().is_some());
        assert!(kernel([[1, 0], [0, 1]], 1, 5).unwrap().is_some());
        assert!(kernel([[1, 1], [0, 1]], 1, 5).unwrap().is_none());
        assert!(kernel([[0, 3], [1, 0]], 3, 5).unwrap().is_none());
    }
    #[test]
    fn input_validation_and_q_cubed() {
        assert!(kernel([[3, 0], [0, 4]], 2, 5).is_err());
        assert!(kernel([[5, 0], [0, 1]], 1, 5).is_err());
        assert!(kernel([[0, 0], [0, 0]], 0, 5).is_err());
        assert!(kernel([[1, 0], [0, 1]], 1, 7).is_err());
    }
    #[test]
    fn all_positive_f11_constructions() {
        let mut count = 0;
        for q in 1..11 {
            for code in 0..14641u32 {
                let m = [
                    [(code % 11) as u16, (code / 11 % 11) as u16],
                    [(code / 121 % 11) as u16, (code / 1331) as u16],
                ];
                if det(m, 11) == pow(q, 3, 11) {
                    count += usize::from(kernel(m, q, 11).unwrap().is_some());
                }
            }
        }
        assert_eq!(count, 5950); // 10 scalars + C(10,2)*11*12 split-distinct.
    }
}
