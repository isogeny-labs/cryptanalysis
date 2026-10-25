//! Exact low-degree geometric exclusions; no quotient reconstruction.
use anyhow::{ensure, Result};
use ghs_sweeper::{field::Field, verify::RawField};
use serde_json::json;

const PHI3: &[(u32, u32)] = &[(4, 0), (0, 4), (3, 3)];
const PHI5: &[(u32, u32)] = &[(6, 0), (0, 6), (5, 5), (4, 2), (2, 4)];
fn power(mut x: u32, mut n: u32, mul: impl Fn(u32, u32) -> u32 + Copy) -> u32 {
    let mut r = 1;
    while n != 0 {
        if n & 1 != 0 {
            r = mul(r, x);
        }
        x = mul(x, x);
        n >>= 1;
    }
    r
}
fn evaluate(terms: &[(u32, u32)], x: u32, y: u32, mul: impl Fn(u32, u32) -> u32 + Copy) -> u32 {
    terms
        .iter()
        .fold(0, |s, &(i, j)| s ^ mul(power(x, i, mul), power(y, j, mul)))
}
fn exclusions(x: u32, y: u32, mul: impl Fn(u32, u32) -> u32 + Copy) -> ([u32; 4], bool) {
    let (xx, yy) = (mul(x, x), mul(y, y));
    let values = [
        evaluate(PHI3, x, y, mul),
        evaluate(PHI5, x, y, mul),
        evaluate(PHI3, xx, y, mul),
        evaluate(PHI3, x, yy, mul),
    ];
    let no_power_two = x != y && xx != y && yy != x && mul(xx, xx) != y && mul(yy, yy) != x;
    (values, no_power_two && values.iter().all(|&v| v != 0))
}
fn order(f: &Field, raw: Option<&RawField>, b: u32) -> u32 {
    let mut count = 2;
    for x in 1..f.size {
        let rhs = if let Some(r) = raw {
            x ^ r.mul(b, r.mul(r.inverses[x as usize], r.inverses[x as usize]))
        } else {
            x ^ f.mul(b, f.mul(f.inv(x), f.inv(x)))
        };
        let trace = raw.map_or(f.trace[rhs as usize], |r| r.traces[rhs as usize]);
        if trace == 0 {
            count += 2;
        }
    }
    count
}
fn main() -> Result<()> {
    let f = Field::new(9)?;
    let raw = RawField::new(9, f.modulus)?;
    let mut rows = Vec::new();
    let mut survivors = 0;
    for b in 1..f.size {
        if power(b, 8, |x, y| f.mul(x, y)) == b {
            continue;
        }
        let size = order(&f, None, b);
        ensure!(size == order(&f, Some(&raw), b), "point-count disagreement");
        let t = 513 - i64::from(size);
        if t.rem_euclid(3) == 0 || ![2, 3].contains(&t.rem_euclid(5)) {
            continue;
        }
        let j = f.inv(b);
        let jq = power(j, 8, |x, y| f.mul(x, y));
        let (values, good) = exclusions(j, jq, |x, y| f.mul(x, y));
        ensure!(
            (values, good)
                == exclusions(
                    raw.inverses[b as usize],
                    power(j, 8, |x, y| raw.mul(x, y)),
                    |x, y| raw.mul(x, y)
                ),
            "modular evaluation disagreement"
        );
        survivors += usize::from(good);
        rows.push(json!({"b":b,"a0_trace":t,"a0_order":size,"a1_order":1026-size,"j":j,"j_q":jq,"modular_values_phi3_phi5_phi3_x2_phi3_y2":values,"no_geometric_isogeny_degree_1_to_6":good}));
    }
    ensure!(rows.len() == 126, "five-only source scope changed");
    println!(
        "{}",
        serde_json::to_string_pretty(
            &json!({"kind":"binary-cubic-five-gluing-geometric-screen/v1","modulus":f.modulus,"base_degree":3,"absolute_degree":9,"input_twist_pairs":rows.len(),"surviving_twist_pairs":survivors,"surviving_models":2*survivors,"arithmetic_backends_agree":true,"rows":rows,"quotient_constructed":false,"selected_source_twist":null,"log_transfer_verified":false,"publication_novelty_established":false})
        )?
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    fn reduced(text: &str) -> Vec<(u32, u32)> {
        let mut out = Vec::new();
        for line in text.lines().filter(|x| !x.trim().is_empty()) {
            let (indices, coefficient) = line.trim().split_once(']').unwrap();
            let (i, j) = indices.trim_start_matches('[').split_once(',').unwrap();
            let (i, j) = (i.parse::<u32>().unwrap(), j.parse::<u32>().unwrap());
            let coefficient = coefficient.trim();
            assert!(coefficient
                .trim_start_matches('-')
                .bytes()
                .all(|c| c.is_ascii_digit()));
            if (coefficient.as_bytes().last().unwrap() - b'0') % 2 != 0 {
                out.push((i, j));
                if i != j {
                    out.push((j, i));
                }
            }
        }
        out.sort_unstable();
        out
    }
    #[test]
    fn reductions_match_retained_primary_coefficients() {
        let mut p3 = PHI3.to_vec();
        p3.sort_unstable();
        let mut p5 = PHI5.to_vec();
        p5.sort_unstable();
        assert_eq!(
            p3,
            reduced(include_str!("../cubic-gluing-reference/phi_j_3.txt"))
        );
        assert_eq!(
            p5,
            reduced(include_str!("../cubic-gluing-reference/phi_j_5.txt"))
        );
    }
    #[test]
    fn actual_modular_neighbors_and_inseparable_controls() {
        let f = Field::new(9).unwrap();
        let raw = RawField::new(9, f.modulus).unwrap();
        for (b, terms) in [(24, PHI3), (48, PHI5)] {
            let x = f.inv(b);
            let roots: Vec<_> = (1..f.size)
                .filter(|&y| evaluate(terms, x, y, |a, b| f.mul(a, b)) == 0)
                .collect();
            assert!(!roots.is_empty());
            for y in roots {
                assert_eq!(evaluate(terms, y, x, |a, b| raw.mul(a, b)), 0);
                assert!(!exclusions(x, y, |a, b| f.mul(a, b)).1);
            }
            assert!(!exclusions(x, x, |a, b| f.mul(a, b)).1);
            assert!(!exclusions(x, f.mul(x, x), |a, b| f.mul(a, b)).1);
            assert!(!exclusions(x, power(x, 4, |a, b| f.mul(a, b)), |a, b| f.mul(a, b)).1);
        }
    }
}
