//! Necessary CM-degree and polarization conditions for a fixed cubic source.
//! The geometric Hom-lattice bridge is documented separately, not assumed proved by this code.
use anyhow::{ensure, Result};
use serde_json::{json, Value};
use std::collections::BTreeMap;

fn power(mut x: u64, mut n: u64, p: u64) -> u64 {
    let mut r = 1;
    while n != 0 {
        if n & 1 != 0 {
            r = r * x % p;
        }
        x = x * x % p;
        n >>= 1;
    }
    r
}
fn prime(n: u64) -> bool {
    n >= 2
        && (2..)
            .take_while(|d| d * d <= n)
            .all(|d| !n.is_multiple_of(d))
}
fn norm(x: i64, y: i64) -> i64 {
    8 * x * x + 3 * x * y + 26 * y * y
}
fn triangle(a: u64, b: u64, c: u64) -> bool {
    let (ab, bc, ca) = (a * b, b * c, c * a);
    ab * ab + bc * bc + ca * ca <= 2 * a * b * c * (a + b + c)
}
fn pairing(v: [u64; 6], w: [u64; 6], q: u64, p: u64) -> u64 {
    (0..3).fold(0, |s, i| {
        (s + power(q, i as u64, p)
            * ((v[2 * i] * w[2 * i + 1] + p * p - v[2 * i + 1] * w[2 * i]) % p))
            % p
    })
}
fn combination(b: [[u64; 6]; 3], a: [u64; 3], p: u64) -> [u64; 6] {
    std::array::from_fn(|i| (0..3).map(|j| b[j][i] * a[j]).sum::<u64>() % p)
}
fn kernel(trace: i64, p: u64) -> Result<Value> {
    let q = 8 % p;
    let t = trace.rem_euclid(p as i64) as u64;
    let determinant = 512 % p;
    let roots: Vec<_> = (1..p)
        .filter(|&x| (x * x + p * p - t * x + determinant) % p == 0)
        .collect();
    ensure!(roots.len() == 2, "split-distinct case required");
    let (alpha, beta) = (roots[0], roots[1]);
    let lambda = (1..p).find(|&x| power(x, 3, p) == alpha).unwrap();
    let ilambda = power(lambda, p - 2, p);
    let c1 = q * ilambda % p;
    let c2 = c1 * c1 % p;
    let b = [
        [1, 0, ilambda, 0, ilambda * ilambda % p, 0],
        [0, c1, 0, p - 1, 0, 0],
        [0, c2, 0, 0, 0, p - 1],
    ];
    for &v in &b {
        for &w in &b {
            ensure!(pairing(v, w, q, p) == 0, "weighted isotropy failed");
        }
    }
    let images = [[lambda, 0, 0], [0, p - c1, 1], [0, p - c2, 0]];
    for i in 0..3 {
        let v = b[i];
        let fv = [alpha * v[4] % p, beta * v[5] % p, v[0], v[1], v[2], v[3]];
        ensure!(
            fv == combination(b, images[i], p),
            "Frobenius action failed"
        );
    }
    let mut intersections = [0; 3];
    for u in 0..p {
        for s in 0..p {
            for t in 0..p {
                let v = combination(b, [u, s, t], p);
                for (i, total) in intersections.iter_mut().enumerate() {
                    if (0..6).filter(|c| c / 2 != i).all(|c| v[c] == 0) {
                        *total += 1;
                    }
                }
            }
        }
    }
    ensure!(intersections == [1, 1, 1], "coordinate intersection failed");
    // Coordinates 0,3,5 form the nonzero diagonal minor diag(1,-1,-1).
    ensure!(
        b[0][0] * b[1][3] % p * b[2][5] % p != 0,
        "basis rank minor failed"
    );
    Ok(
        json!({"source_trace":trace,"ell":p,"q_mod_ell":q,"frobenius_eigenvalues":roots,"basis":b,"frobenius_action_on_basis":images,"coordinate_intersection_sizes":intersections,"abstract_points_checked":p*p*p,"actual_elliptic_torsion_coordinates":false}),
    )
}
fn certificate() -> Result<Value> {
    ensure!(
        prime(823) && (-823i64).rem_euclid(4) == 1,
        "fundamental discriminant check"
    );
    let mut norms = BTreeMap::new();
    for x in -10..=10 {
        for y in -5..=5 {
            let n = norm(x, y);
            ensure!(
                32 * n == (16 * x + 3 * y).pow(2) + 823 * y * y,
                "norm completion identity"
            );
            if n > 0 && n <= 676 {
                norms.entry(n as u64).or_insert([x, y]);
            }
        }
    }
    let mut degree_partitions = Vec::new();
    let mut triangle_survivors = Vec::new();
    for a in 1..=17 {
        for b in a..=26 {
            if a + b >= 53 {
                continue;
            }
            let c = 53 - a - b;
            if c < b {
                continue;
            }
            if norms.contains_key(&(a * b))
                && norms.contains_key(&(a * c))
                && norms.contains_key(&(b * c))
            {
                let record = json!({"degrees":[a,b,c],"pair_products":[a*b,a*c,b*c],"norm_witnesses":[norms[&(a*b)],norms[&(a*c)],norms[&(b*c)]],"triangle_condition":triangle(a,b,c)});
                degree_partitions.push(record.clone());
                if triangle(a, b, c) {
                    triangle_survivors.push(record);
                }
            }
        }
    }
    let prime_screens:Vec<_>=(5..=53).filter(|&p|prime(p) && p%3==2).map(|p| {
        let d=(-823i64).rem_euclid(p as i64) as u64;
        json!({"ell":p,"discriminant_mod_ell":d,"split_distinct":d!=0 && (1..p).any(|a|a*a%p==d)})
    }).collect();
    let no_cube_trace = (-5i64..=5).all(|u| (u * u * u - 24 * u).abs() != 35);
    ensure!(no_cube_trace, "source Frobenius could be a cubic power");
    Ok(
        json!({"kind":"fixed-cubic-cm-polarization-screen/v1","source_Q":512,"source_traces":[-35,35],"frobenius_discriminant":-823,"norm_form":[8,3,26],"norm_bound":676,"enumeration_bounds":{"x":[-10,10],"y":[-5,5]},"represented_degrees":norms,"positive_three_component_partitions":degree_partitions,"triangle_survivors":triangle_survivors,"prime_screens":prime_screens,"abstract_kernels":[kernel(-35,53)?,kernel(35,53)?],"no_integral_cube_trace_in_hasse_range":no_cube_trace,"geometric_hom_lattice_bridge_checked":false,"quotient_reconstructed":false,"log_transfer_verified":false,"novelty_established":false}),
    )
}
fn main() -> Result<()> {
    println!("{}", serde_json::to_string_pretty(&certificate()?)?);
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn fixed_norm_and_triangle_controls() {
        assert_eq!(norm(-2, 1), 52);
        assert_eq!(norm(0, 1), 26);
        assert_eq!(norm(5, 4), 676);
        assert!(!triangle(1, 26, 26));
        assert!(triangle(17, 18, 18));
    }
    #[test]
    fn exact_two_source_modules() {
        assert!(kernel(-35, 53).is_ok());
        assert!(kernel(35, 53).is_ok());
        assert!(kernel(35, 5).is_err());
    }
}
