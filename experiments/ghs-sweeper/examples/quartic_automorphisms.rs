//! Complete geometric automorphisms of supplied ordinary O3 quartics via their Fano bitangents.
use anyhow::{ensure, Result};
use clap::Parser;
use ghs_sweeper::field::Field;
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::PathBuf,
};
type Exponent = [u8; 3];
type Poly = BTreeMap<Exponent, u32>;
type Matrix = [[u32; 3]; 3];
#[derive(Parser)]
struct Args {
    #[arg(long)]
    census: PathBuf,
}
fn add(p: &mut Poly, e: Exponent, c: u32) {
    *p.entry(e).or_default() ^= c;
}
fn multiply(p: &Poly, q: &Poly, f: &Field) -> Poly {
    let mut out = Poly::new();
    for (a, &x) in p {
        for (b, &y) in q {
            add(&mut out, std::array::from_fn(|i| a[i] + b[i]), f.mul(x, y));
        }
    }
    out.retain(|_, v| *v != 0);
    out
}
fn substitute(p: &Poly, m: Matrix, f: &Field) -> Poly {
    let mut out = Poly::new();
    for (e, &c) in p {
        let mut term = Poly::from([([0, 0, 0], c)]);
        for i in 0..3 {
            let linear: Poly = (0..3)
                .filter(|&j| m[i][j] != 0)
                .map(|j| {
                    let mut a = [0; 3];
                    a[j] = 1;
                    (a, m[i][j])
                })
                .collect();
            for _ in 0..e[i] {
                term = multiply(&term, &linear, f);
            }
        }
        for (a, c) in term {
            add(&mut out, a, c);
        }
    }
    out.retain(|_, c| *c != 0);
    out
}
fn matmul(a: Matrix, b: Matrix, f: &Field) -> Matrix {
    std::array::from_fn(|i| {
        std::array::from_fn(|j| (0..3).fold(0, |s, k| s ^ f.mul(a[i][k], b[k][j])))
    })
}
fn identity() -> Matrix {
    [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
}
fn gamma(code: u16) -> Matrix {
    std::array::from_fn(|i| std::array::from_fn(|j| u32::from((code >> (3 * i + j)) & 1)))
}
fn gamma_code(m: Matrix) -> Result<u16> {
    ensure!(m.iter().flatten().all(|&a| a <= 1), "matrix left F2");
    Ok((0..3).fold(0, |s, i| {
        s ^ (0..3).fold(0, |v, j| v | ((m[i][j] as u16) << (3 * i + j)))
    }))
}
fn rank(code: u16) -> usize {
    let mut rows = [
        (code & 7) as u8,
        ((code >> 3) & 7) as u8,
        ((code >> 6) & 7) as u8,
    ];
    let mut r = 0;
    for col in 0..3 {
        if let Some(i) = (r..3).find(|&i| rows[i] & (1 << col) != 0) {
            rows.swap(r, i);
            for j in 0..3 {
                if j != r && rows[j] & (1 << col) != 0 {
                    rows[j] ^= rows[r];
                }
            }
            r += 1;
        }
    }
    r
}
fn product(a: u16, b: u16) -> u16 {
    let br = [b & 7, (b >> 3) & 7, (b >> 6) & 7];
    (0..3).fold(0, |s, i| {
        s | ((0..3)
            .filter(|&j| a & (1 << (3 * i + j)) != 0)
            .fold(0, |v, j| v ^ br[j])
            << (3 * i))
    })
}
fn order(g: u16) -> usize {
    let id = 273;
    let mut v = id;
    for n in 1..=168 {
        v = product(v, g);
        if v == id {
            return n;
        }
    }
    0
}
fn split_polynomial(q: &Poly, m: Matrix, f: &Field) -> Poly {
    let split = substitute(q, m, f);
    let mut p = Poly::from([([2, 1, 1], 1), ([1, 2, 1], 1), ([1, 1, 2], 1)]);
    for (e, c) in split {
        add(&mut p, e.map(|v| 2 * v), f.mul(c, c));
    }
    p.retain(|_, c| *c != 0);
    p
}
fn proportional(p: &Poly, q: &Poly, f: &Field) -> bool {
    if p.len() != q.len() || p.keys().ne(q.keys()) {
        return false;
    }
    let (&e, &a) = p.first_key_value().unwrap();
    let c = f.mul(a, f.inv(q[&e]));
    p.iter().all(|(e, &a)| a == f.mul(c, q[e]))
}
fn automorphisms(coeff: [u32; 6], p: &Value, f: &Field) -> Result<Value> {
    ensure!(coeff.iter().all(|&a| a < 8), "noncanonical F8 coefficient");
    let base = Field::new(3)?;
    let emb = f.embedding(&base)?;
    let v = p["cubic_root"].as_u64().unwrap() as u32;
    let vp = f.power(v, 8);
    let vpp = f.power(v, 64);
    ensure!(
        f.mul(f.mul(v, v), v) ^ f.mul(v, v) == emb[p["s"].as_u64().unwrap() as usize],
        "cubic source binding"
    );
    let m = [[v, vp, vpp], [vp, vpp, v], [vpp, v, vp]];
    ensure!(
        matmul(m, m, f) == identity(),
        "normal basis transform inverse"
    );
    let exponents = [
        [2, 0, 0],
        [0, 2, 0],
        [0, 0, 2],
        [1, 1, 0],
        [0, 1, 1],
        [1, 0, 1],
    ];
    let q: Poly = (0..6)
        .filter(|&i| coeff[i] != 0)
        .map(|i| (exponents[i], emb[coeff[i] as usize]))
        .collect();
    let splitq = substitute(&q, m, f);
    let val = |e| splitq.get(&e).copied().unwrap_or(0);
    let [a, b, c, d, e, ff] = exponents.map(val);
    ensure!(
        a != 0
            && b != 0
            && c != 0
            && a ^ b ^ d != 0
            && b ^ c ^ e != 0
            && a ^ c ^ ff != 0
            && a ^ b ^ c ^ d ^ e ^ ff != 1,
        "singular split model"
    );
    let split = split_polynomial(&q, m, f);
    let original = substitute(&split, m, f);
    let gl: Vec<_> = (0..512u16).filter(|&g| rank(g) == 3).collect();
    ensure!(gl.len() == 168, "GL3(F2) cardinality");
    let mut autos = BTreeMap::new();
    let mut sigma = BTreeMap::new();
    let mut rational = Vec::new();
    for g in gl {
        if !proportional(&substitute(&split, gamma(g), f), &split, f) {
            continue;
        }
        let actual = matmul(matmul(m, gamma(g), f), m, f);
        ensure!(
            proportional(&substitute(&original, actual, f), &original, f),
            "original-coordinate automorphism replay"
        );
        let conjugate = actual.map(|r| r.map(|x| f.power(x, 8)));
        let sg = gamma_code(matmul(matmul(m, conjugate, f), m, f))?;
        if conjugate == actual {
            rational.push(g);
        }
        sigma.insert(g, sg);
        autos.insert(g, actual);
    }
    ensure!(autos.contains_key(&273), "identity missing");
    for &a in autos.keys() {
        ensure!(autos.contains_key(&sigma[&a]), "Galois closure");
        for &b in autos.keys() {
            ensure!(autos.contains_key(&product(a, b)), "automorphism closure");
        }
    }
    let expected_rational = if coeff[0] == coeff[1]
        && coeff[1] == coeff[2]
        && coeff[3] == coeff[4]
        && coeff[4] == coeff[5]
    {
        3
    } else {
        1
    };
    ensure!(
        rational.len() == expected_rational,
        "published rational automorphism count"
    );
    let involutions: Vec<_> = autos.keys().copied().filter(|&g| order(g) == 2).collect();
    let mut v4 = BTreeSet::new();
    let mut cyclic_v4 = BTreeSet::new();
    for &a in &involutions {
        for &b in &involutions {
            if a == b || product(a, b) != product(b, a) {
                continue;
            }
            let mut group = [273, a, b, product(a, b)];
            group.sort_unstable();
            v4.insert(group);
            let mut conjugated = group.map(|g| sigma[&g]);
            conjugated.sort_unstable();
            if conjugated == group && sigma[&a] != a {
                cyclic_v4.insert(group);
            }
        }
    }
    let records:Vec<_>=autos.iter().map(|(&code,&matrix)|json!({"split_code":code,"original_matrix":matrix,"order":order(code),"sigma_code":sigma[&code]})).collect();
    Ok(
        json!({"coefficients":coeff,"geometric_automorphism_order":autos.len(),"rational_automorphism_order":rational.len(),"involutions":involutions,"V4_subgroups":v4,"frobenius_stable_V4_with_three_cycle":cyclic_v4,"automorphisms":records,"explicit_quotient_maps_constructed":false}),
    )
}
fn main() -> Result<()> {
    let input = fs::read_to_string(Args::parse().census)?;
    let data: Value = serde_json::from_str(&input)?;
    ensure!(
        data["kind"] == "ordinary-o3-f8-complete-census/v1",
        "wrong census kind"
    );
    let f = Field::new(9)?;
    ensure!(data["extension_modulus"] == f.modulus, "field mismatch");
    let mut rows = Vec::new();
    for target in data["target_representatives"].as_array().unwrap() {
        let coeff: [u32; 6] = serde_json::from_value(target["coefficients"].clone())?;
        ensure!(target["raw_verified"] == true, "unverified target");
        let mut row = automorphisms(coeff, &data["parameters"], &f)?;
        row["source_trace"] = target["source_trace"].clone();
        row["code"] = target["code"].clone();
        rows.push(row);
    }
    println!(
        "{}",
        serde_json::to_string_pretty(
            &json!({"kind":"ordinary-o3-target-automorphism-census/v1","models":rows.len(),"rows":rows,"classification_source":"Nart-Ritzenthaler arXiv:math/0312366v2, ordinary Fano-bitangent classification; arXiv:0905.0546, V4 covers","explicit_map_verified":false,"novelty_established":false})
        )?
    );
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn finite_group_control() {
        let gl: Vec<_> = (0..512u16).filter(|&a| rank(a) == 3).collect();
        assert_eq!(gl.len(), 168);
        for &a in &gl {
            assert_eq!(product(a, 273), a);
            assert_eq!(product(273, a), a);
            assert!(order(a) > 0);
            assert_eq!(gamma_code(gamma(a)).unwrap(), a);
        }
    }
    #[test]
    fn polynomial_substitution_control() {
        let f = Field::new(9).unwrap();
        let p = Poly::from([([2, 1, 1], 1), ([4, 0, 0], 23)]);
        assert_eq!(substitute(&p, identity(), &f), p);
        let a = [[0, 1, 0], [1, 0, 0], [0, 0, 1]];
        assert_eq!(substitute(&substitute(&p, a, &f), a, &f), p);
    }
}
