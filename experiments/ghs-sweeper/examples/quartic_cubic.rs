//! Exact replay of the published ordinary O3 plane-quartic family over F8.
//! A matching Weil polynomial supplies no evaluated elliptic-subgroup map.
use anyhow::{ensure, Result};
use clap::{Parser, Subcommand};
use ghs_sweeper::{field::Field, verify::RawField};
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

type Coefficients = [u32; 6];
type Exponent = [u8; 3];
const QUADRATIC: [Exponent; 6] = [
    [2, 0, 0],
    [0, 2, 0],
    [0, 0, 2],
    [1, 1, 0],
    [0, 1, 1],
    [1, 0, 1],
];

#[derive(Parser)]
#[command(
    about = "Published ordinary O3 quartics over F8: exact zeta screen, no DLP map or novelty claim"
)]
struct Args {
    #[command(subcommand)]
    command: Command,
}
#[derive(Subcommand)]
enum Command {
    Census {
        #[arg(long, default_value_t = 2)]
        threads: usize,
    },
    Verify {
        #[arg(long, num_args = 6)]
        coefficients: Vec<u32>,
    },
}
#[derive(Clone, Debug, Serialize, Deserialize)]
struct Parameters {
    s: u32,
    t: u32,
    cubic_root: u32,
    conjugates: [u32; 3],
    base_embedding: Vec<u32>,
}

fn parameters(base: &Field, extension: &Field) -> Result<Parameters> {
    let emb = extension.embedding(base)?;
    let s = (1..8)
        .find(|&s| (0..8).all(|x| base.mul(base.mul(x, x), x) ^ base.mul(x, x) ^ s != 0))
        .unwrap();
    let v = (0..extension.size)
        .find(|&x| extension.mul(extension.mul(x, x), x) ^ extension.mul(x, x) == emb[s as usize])
        .unwrap();
    let vp = extension.power(v, 8);
    let vpp = extension.power(v, 64);
    ensure!(v ^ vp ^ vpp == 1, "cubic trace binding");
    let tv = extension.mul(
        extension.mul(extension.mul(v, v), extension.inv(vp)) ^ 1,
        extension.inv(v),
    );
    let t = emb
        .iter()
        .position(|&x| x == tv)
        .ok_or_else(|| anyhow::anyhow!("cubic orientation left base field"))? as u32;
    ensure!(base.mul(t, t) ^ t ^ 1 == base.inv(s), "resolvent binding");
    Ok(Parameters {
        s,
        t,
        cubic_root: v,
        conjugates: [v, vp, vpp],
        base_embedding: emb,
    })
}
fn decode(mut code: u32) -> Coefficients {
    std::array::from_fn(|_| {
        let a = code & 7;
        code >>= 3;
        a
    })
}
fn encode(c: Coefficients) -> u32 {
    c.iter().enumerate().fold(0, |s, (i, a)| s | a << (3 * i))
}
fn rotate(c: Coefficients) -> Coefficients {
    [c[1], c[2], c[0], c[4], c[5], c[3]]
}
fn canonical(c: Coefficients) -> bool {
    let code = encode(c);
    code <= encode(rotate(c)) && code <= encode(rotate(rotate(c)))
}
fn qvalue(c: Coefficients, p: [u32; 3], emb: &[u32], mul: impl Fn(u32, u32) -> u32 + Copy) -> u32 {
    let [x, y, z] = p;
    let monomials = [
        mul(x, x),
        mul(y, y),
        mul(z, z),
        mul(x, y),
        mul(y, z),
        mul(z, x),
    ];
    (0..6).fold(0, |s, i| s ^ mul(emb[c[i] as usize], monomials[i]))
}
fn smooth(c: Coefficients, p: &Parameters, f: &Field) -> bool {
    qvalue(c, p.conjugates, &p.base_embedding, |a, b| f.mul(a, b)) != 0
        && qvalue(c, p.conjugates.map(|a| a ^ 1), &p.base_embedding, |a, b| {
            f.mul(a, b)
        }) != 0
        && c.iter().fold(0, |s, &a| s ^ a) != 1
}
fn add_term(poly: &mut BTreeMap<Exponent, u32>, e: Exponent, c: u32) {
    *poly.entry(e).or_default() ^= c;
}
fn rhs(base: &Field, p: &Parameters) -> BTreeMap<Exponent, u32> {
    let st = base.mul(p.s, p.t);
    let su = base.mul(p.s, p.t ^ 1);
    let cubic = [
        ([3, 0, 0], p.s),
        ([0, 3, 0], p.s),
        ([0, 0, 3], p.s),
        ([1, 1, 1], 1),
        ([1, 2, 0], st),
        ([2, 0, 1], st),
        ([0, 1, 2], st),
        ([1, 0, 2], su),
        ([2, 1, 0], su),
        ([0, 2, 1], su),
    ];
    let mut poly = BTreeMap::new();
    for (e, c) in cubic {
        for i in 0..3 {
            let mut e = e;
            e[i] += 1;
            add_term(&mut poly, e, c);
        }
    }
    poly.retain(|_, c| *c != 0);
    poly
}
fn equation(c: Coefficients, base: &Field, p: &Parameters) -> BTreeMap<Exponent, u32> {
    let mut poly = rhs(base, p);
    for i in 0..6 {
        add_term(&mut poly, QUADRATIC[i].map(|a| 2 * a), base.mul(c[i], c[i]));
    }
    poly.retain(|_, v| *v != 0);
    poly
}
fn polynomial_value(
    poly: &BTreeMap<Exponent, u32>,
    point: [u32; 3],
    emb: &[u32],
    mul: impl Fn(u32, u32) -> u32 + Copy,
) -> u32 {
    let powers = point.map(|a| {
        let mut v = [1; 5];
        for i in 1..5 {
            v[i] = mul(v[i - 1], a);
        }
        v
    });
    poly.iter().fold(0, |s, (e, &c)| {
        s ^ mul(
            emb[c as usize],
            mul(
                powers[0][e[0] as usize],
                mul(powers[1][e[1] as usize], powers[2][e[2] as usize]),
            ),
        )
    })
}
#[derive(Clone)]
struct PointRow {
    terms: [[u16; 8]; 6],
    root: u16,
}
fn point_rows(degree: u32, base: &Field, p: &Parameters) -> Result<Vec<PointRow>> {
    let f = Field::new(degree)?;
    let emb = f.embedding(base)?;
    let r = rhs(base, p);
    let mut rows = Vec::new();
    let mut push = |point: [u32; 3]| {
        let [x, y, z] = point;
        let m = [
            f.mul(x, x),
            f.mul(y, y),
            f.mul(z, z),
            f.mul(x, y),
            f.mul(y, z),
            f.mul(z, x),
        ];
        rows.push(PointRow {
            terms: std::array::from_fn(|i| std::array::from_fn(|a| f.mul(m[i], emb[a]) as u16)),
            root: f.power(
                polynomial_value(&r, point, &emb, |a, b| f.mul(a, b)),
                1 << (degree - 1),
            ) as u16,
        });
    };
    for x in 0..f.size {
        for y in 0..f.size {
            push([x, y, 1]);
        }
    }
    for x in 0..f.size {
        push([x, 1, 0]);
    }
    push([1, 0, 0]);
    ensure!(
        rows.len() == (f.size * f.size + f.size + 1) as usize,
        "projective point coverage"
    );
    Ok(rows)
}
fn count(c: Coefficients, rows: &[PointRow]) -> u32 {
    rows.iter()
        .filter(|r| (0..6).fold(0, |s, i| s ^ r.terms[i][c[i] as usize]) == r.root)
        .count() as u32
}
fn raw_count(c: Coefficients, degree: u32, base: &Field, p: &Parameters) -> Result<u32> {
    let f = Field::new(degree)?;
    let raw = RawField::new(degree, f.modulus)?;
    let emb = f.embedding(base)?;
    for a in 0..8 {
        for b in 0..8 {
            ensure!(
                raw.mul(emb[a], emb[b]) == emb[base.mul(a as u32, b as u32) as usize],
                "embedding replay"
            );
        }
    }
    let poly = equation(c, base, p);
    let mut total = 0;
    // First-nonzero-coordinate normalization, unlike the last-coordinate fast path.
    for y in 0..f.size {
        for z in 0..f.size {
            total += u32::from(polynomial_value(&poly, [1, y, z], &emb, |a, b| raw.mul(a, b)) == 0);
        }
    }
    for z in 0..f.size {
        total += u32::from(polynomial_value(&poly, [0, 1, z], &emb, |a, b| raw.mul(a, b)) == 0);
    }
    total += u32::from(polynomial_value(&poly, [0, 0, 1], &emb, |a, b| raw.mul(a, b)) == 0);
    Ok(total)
}
#[derive(Clone, Debug, Serialize)]
struct Witness {
    code: u32,
    coefficients: Coefficients,
    point_counts: [u32; 3],
    source_trace: i64,
    jacobian_order: i64,
    raw_verified: bool,
}
fn verify(c: Coefficients) -> Result<Value> {
    ensure!(
        c.iter().all(|&a| a < 8),
        "coefficients must be canonical F8 masks"
    );
    let base = Field::new(3)?;
    let f9 = Field::new(9)?;
    let p = parameters(&base, &f9)?;
    ensure!(smooth(c, &p, &f9), "singular quartic rejected");
    let mut counts = [0; 3];
    for (i, value) in counts.iter_mut().enumerate() {
        let d = 3 * (i as u32 + 1);
        *value = count(c, &point_rows(d, &base, &p)?);
        ensure!(
            *value == raw_count(c, d, &base, &p)?,
            "raw count disagreement"
        );
    }
    let compatible = counts[0] == 9 && counts[1] == 65;
    let source_trace = if compatible {
        ensure!((513 - i64::from(counts[2])) % 3 == 0, "Newton divisibility");
        Some((513 - i64::from(counts[2])) / 3)
    } else {
        None
    };
    let poly: Vec<_> = equation(c, &base, &p)
        .into_iter()
        .map(|(exponents, coefficient)| json!({"exponents":exponents,"coefficient":coefficient}))
        .collect();
    Ok(
        json!({"kind":"ordinary-o3-quartic-replay/v1","base_modulus":base.modulus,"extension_modulus":f9.modulus,"parameters":p,"coefficients":c,"quartic_polynomial":poly,"point_counts":counts,"source_trace":source_trace,"genus":3,"smooth":true,"ordinary":true,"nonhyperelliptic":true,"raw_verified":true,"explicit_map_verified":false,"novelty_established":false}),
    )
}
fn census(threads: usize) -> Result<Value> {
    ensure!((1..=8).contains(&threads), "threads must be 1..=8");
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(threads)
        .build()?;
    let base = Field::new(3)?;
    let f9 = Field::new(9)?;
    let p = parameters(&base, &f9)?;
    let mut coverage = Sha256::new();
    let mut smooth_total = 0;
    let mut models = Vec::new();
    for code in 0..262144 {
        let c = decode(code);
        let good = smooth(c, &p, &f9);
        let representative = canonical(c);
        coverage.update(code.to_le_bytes());
        coverage.update([u8::from(good), u8::from(representative)]);
        smooth_total += usize::from(good);
        if good && representative {
            models.push((code, c));
        }
    }
    ensure!(
        smooth_total == 228481 && models.len() == 76189,
        "published O3 cardinality disagreement"
    );
    let rows1 = point_rows(3, &base, &p)?;
    let stage1: Vec<_> = pool.install(|| {
        models
            .par_iter()
            .map(|&(code, c)| (code, c, count(c, &rows1)))
            .collect()
    });
    for &(code, _, n) in &stage1 {
        coverage.update(code.to_le_bytes());
        coverage.update(n.to_le_bytes());
    }
    let first: Vec<_> = stage1.into_iter().filter(|r| r.2 == 9).collect();
    eprintln!(
        "O3 smooth models={smooth_total}, orbit representatives={}, N1=9 representatives={}",
        models.len(),
        first.len()
    );
    let rows2 = point_rows(6, &base, &p)?;
    let stage2: Vec<_> = pool.install(|| {
        first
            .par_iter()
            .map(|&(code, c, _)| (code, c, count(c, &rows2)))
            .collect()
    });
    for &(code, _, n) in &stage2 {
        coverage.update(code.to_le_bytes());
        coverage.update(n.to_le_bytes());
    }
    let second: Vec<_> = stage2.into_iter().filter(|r| r.2 == 65).collect();
    eprintln!("N1=9, N2=65 representatives={}", second.len());
    let rows3 = point_rows(9, &base, &p)?;
    let stage3: Vec<_> = pool.install(|| {
        second
            .par_iter()
            .map(|&(code, c, _)| (code, c, count(c, &rows3)))
            .collect()
    });
    let mut by_trace: BTreeMap<i64, (usize, Witness)> = BTreeMap::new();
    let mut targets = Vec::new();
    for (code, c, n) in stage3 {
        coverage.update(code.to_le_bytes());
        coverage.update(n.to_le_bytes());
        let power_sum = 513 - i64::from(n);
        ensure!(power_sum % 3 == 0, "Newton coefficient not integral");
        let trace = power_sum / 3;
        ensure!(
            trace.abs() <= 45 && trace % 2 != 0,
            "source trace incompatible with ordinary cubic restriction"
        );
        let w = Witness {
            code,
            coefficients: c,
            point_counts: [9, 65, n],
            source_trace: trace,
            jacobian_order: 513 - trace,
            raw_verified: false,
        };
        by_trace
            .entry(trace)
            .and_modify(|r| r.0 += 1)
            .or_insert((1, w.clone()));
        if trace.abs() == 35 {
            targets.push(w);
        }
    }
    let control_traces: Vec<_> = by_trace.keys().copied().take(3).collect();
    for trace in control_traces {
        let w = &mut by_trace.get_mut(&trace).unwrap().1;
        for i in 0..3 {
            ensure!(
                raw_count(w.coefficients, 3 * (i as u32 + 1), &base, &p)? == w.point_counts[i],
                "raw control count disagreement"
            );
        }
        w.raw_verified = true;
    }
    for w in &mut targets {
        for i in 0..3 {
            ensure!(
                raw_count(w.coefficients, 3 * (i as u32 + 1), &base, &p)? == w.point_counts[i],
                "raw target count disagreement"
            );
        }
        w.raw_verified = true;
    }
    let histogram:Vec<_>=by_trace.into_iter().map(|(trace,(orbits,witness))|json!({"trace":trace,"orbit_representatives":orbits,"first_witness":witness})).collect();
    Ok(
        json!({"kind":"ordinary-o3-f8-complete-census/v1","classification_source":"Nart-Ritzenthaler, arXiv:math/0312366v2, section 1.4 O3","base_modulus":base.modulus,"extension_modulus":f9.modulus,"parameters":p,"parameter_vectors":262144,"smooth_vectors":smooth_total,"smooth_c3_orbit_representatives":models.len(),"N1_9_representatives":first.len(),"N1_9_N2_65_representatives":second.len(),"point_row_counts":[rows1.len(),rows2.len(),rows3.len()],"stage_coverage_sha256":format!("{:x}",coverage.finalize()),"histogram":histogram,"target_traces":[-35,35],"target_representatives":targets,"threads":threads,"explicit_elliptic_map_verified":false,"novel_affected_family_established":false,"performance_claim":false}),
    )
}
fn main() -> Result<()> {
    let value = match Args::parse().command {
        Command::Census { threads } => census(threads)?,
        Command::Verify { coefficients } => verify(coefficients.try_into().unwrap())?,
    };
    println!("{}", serde_json::to_string_pretty(&value)?);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn cubic_norm_matches_the_published_normal_form() {
        let b = Field::new(3).unwrap();
        let f = Field::new(9).unwrap();
        let p = parameters(&b, &f).unwrap();
        let r = rhs(&b, &p);
        let [v, vp, vpp] = p.conjugates;
        for a in 0..8 {
            for bb in 0..8 {
                for c in 0..8 {
                    let [x, y, z] = [
                        p.base_embedding[a],
                        p.base_embedding[bb],
                        p.base_embedding[c],
                    ];
                    let l = f.mul(v, x) ^ f.mul(vp, y) ^ f.mul(vpp, z);
                    let lp = f.mul(vp, x) ^ f.mul(vpp, y) ^ f.mul(v, z);
                    let lpp = f.mul(vpp, x) ^ f.mul(v, y) ^ f.mul(vp, z);
                    assert_eq!(
                        f.mul(f.mul(l, lp), f.mul(lpp, x ^ y ^ z)),
                        polynomial_value(&r, [x, y, z], &p.base_embedding, |a, b| f.mul(a, b))
                    );
                }
            }
        }
    }
    #[test]
    fn smoothness_matches_all_seven_critical_fano_points() {
        let b = Field::new(3).unwrap();
        let f = Field::new(9).unwrap();
        let p = parameters(&b, &f).unwrap();
        let [v, vp, vpp] = p.conjugates;
        let axes = [[v, vp, vpp], [vp, vpp, v], [vpp, v, vp]];
        let mut points = axes.to_vec();
        for i in 0..3 {
            points.push(std::array::from_fn(|j| axes[i][j] ^ axes[(i + 1) % 3][j]));
        }
        points.push([1, 1, 1]);
        for code in 0..64u32 {
            let c = std::array::from_fn(|i| (code >> i) & 1);
            let eq = equation(c, &b, &p);
            let direct = points
                .iter()
                .all(|&a| polynomial_value(&eq, a, &p.base_embedding, |a, b| f.mul(a, b)) != 0);
            assert_eq!(smooth(c, &p, &f), direct);
        }
        assert!(!smooth([0; 6], &p, &f));
        assert!(!smooth([1, 1, 1, 0, 0, 0], &p, &f));
        assert!(smooth([2, 0, 0, 0, 0, 0], &p, &f));
    }
    #[test]
    fn projective_lookup_counts_equal_direct_raw_counts() {
        let b = Field::new(3).unwrap();
        let f = Field::new(9).unwrap();
        let p = parameters(&b, &f).unwrap();
        let rows = point_rows(3, &b, &p).unwrap();
        for c in [
            [2, 0, 0, 0, 0, 0],
            [0, 0, 0, 2, 0, 0],
            [2, 3, 4, 1, 5, 6],
            [0; 6],
        ] {
            assert_eq!(count(c, &rows), raw_count(c, 3, &b, &p).unwrap());
        }
    }
    #[test]
    fn three_cycle_orbits_and_invalid_inputs() {
        for code in 0..262144 {
            let c = decode(code);
            assert_eq!(encode(c), code);
            assert_eq!(rotate(rotate(rotate(c))), c);
        }
        assert!(verify([8, 0, 0, 0, 0, 0]).is_err());
        assert!(verify([0; 6]).is_err());
        assert!(census(0).is_err());
    }
}
