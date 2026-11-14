//! CT16: independent finite-field Frobenius and geometric J[2] controls.
//!
//! For a separable sextic y^2=f(x) in odd characteristic, the fifteen
//! nonidentity geometric 2-torsion classes correspond to unordered pairs of
//! its six Weierstrass points. Frobenius acts by permuting the roots.
//! This test imports no Richelot or Cantor code and makes no DLP cost claim.

fn residue(a: i64, p: i64) -> i64 {
    a.rem_euclid(p)
}

fn trim(mut a: Vec<i64>) -> Vec<i64> {
    while a.last() == Some(&0) {
        a.pop();
    }
    a
}

fn inverse(a: i64, p: i64) -> i64 {
    (1..p)
        .find(|b| residue(a * b, p) == 1)
        .expect("nonzero leading coefficient")
}

fn times(a: &[i64], b: &[i64], p: i64) -> Vec<i64> {
    if a.is_empty() || b.is_empty() {
        return Vec::new();
    }
    let mut product = vec![0; a.len() + b.len() - 1];
    for (i, &ai) in a.iter().enumerate() {
        for (j, &bj) in b.iter().enumerate() {
            product[i + j] = residue(product[i + j] + ai * bj, p);
        }
    }
    trim(product)
}

fn minus(a: &[i64], b: &[i64], p: i64) -> Vec<i64> {
    trim(
        (0..a.len().max(b.len()))
            .map(|i| {
                residue(
                    a.get(i).copied().unwrap_or(0) - b.get(i).copied().unwrap_or(0),
                    p,
                )
            })
            .collect(),
    )
}

fn modulo(a: &[i64], modulus: &[i64], p: i64) -> Vec<i64> {
    let mut a = trim(a.to_vec());
    let modulus = trim(modulus.to_vec());
    assert!(!modulus.is_empty());
    let inv_lead = inverse(*modulus.last().unwrap(), p);
    while a.len() >= modulus.len() && !a.is_empty() {
        let shift = a.len() - modulus.len();
        let lead = residue(*a.last().unwrap() * inv_lead, p);
        for (i, &coefficient) in modulus.iter().enumerate() {
            a[shift + i] = residue(a[shift + i] - lead * coefficient, p);
        }
        a = trim(a);
    }
    a
}

fn power_mod(a: &[i64], mut exponent: u64, modulus: &[i64], p: i64) -> Vec<i64> {
    let mut base = modulo(a, modulus, p);
    let mut result = vec![1];
    while exponent != 0 {
        if exponent % 2 == 1 {
            result = modulo(&times(&result, &base, p), modulus, p);
        }
        base = modulo(&times(&base, &base, p), modulus, p);
        exponent /= 2;
    }
    result
}

fn gcd(mut a: Vec<i64>, mut b: Vec<i64>, p: i64) -> Vec<i64> {
    while !b.is_empty() {
        let r = modulo(&a, &b, p);
        a = b;
        b = r;
    }
    if a.is_empty() {
        return a;
    }
    let inv = inverse(*a.last().unwrap(), p);
    trim(a.iter().map(|&c| residue(c * inv, p)).collect())
}

fn monic(a: &[i64], p: i64) -> Vec<i64> {
    let leading = inverse(*a.last().unwrap(), p);
    a.iter().map(|&c| residue(c * leading, p)).collect()
}

fn orbit_length(modulus: &[i64], p: i64) -> usize {
    let x = vec![0, 1];
    let mut orbit = vec![x.clone()];
    let mut value = x.clone();
    for step in 1..=modulus.len() - 1 {
        value = power_mod(&value, p as u64, modulus, p);
        if value == x {
            return step;
        }
        assert!(!orbit.contains(&value), "unexpected shorter orbit");
        orbit.push(value.clone());
    }
    panic!("Frobenius did not return to the root");
}

fn permutation(cycles: &[&[usize]], power: usize) -> [usize; 6] {
    let mut perm = [0; 6];
    for &cycle in cycles {
        for (index, &point) in cycle.iter().enumerate() {
            perm[point] = cycle[(index + power) % cycle.len()];
        }
    }
    perm
}

fn fixed_geometric_two_torsion(cycles: &[&[usize]], power: usize) -> usize {
    let sigma = permutation(cycles, power);
    let mut count = 1; // identity
    for i in 0..6 {
        for j in i + 1..6 {
            if (sigma[i] == i && sigma[j] == j)
                || (sigma[i] == j && sigma[j] == i)
            {
                count += 1;
            }
        }
    }
    count
}

fn matchings(points: &[usize]) -> Vec<Vec<(usize, usize)>> {
    if points.is_empty() {
        return vec![Vec::new()];
    }
    let first = points[0];
    let mut all = Vec::new();
    for &partner in points.iter().skip(1) {
        let remaining: Vec<_> = points[1..]
            .iter()
            .copied()
            .filter(|&point| point != partner)
            .collect();
        for mut rest in matchings(&remaining) {
            rest.insert(0, (first, partner));
            all.push(rest);
        }
    }
    all
}

fn stable_pairings(cycles: &[&[usize]]) -> Vec<Vec<(usize, usize)>> {
    let sigma = permutation(cycles, 1);
    let all = matchings(&[0, 1, 2, 3, 4, 5]);
    assert_eq!(all.len(), 15);
    all.into_iter()
        .filter(|matching| {
            matching.iter().all(|&(i, j)| {
                matching.iter().any(|&(k, l)| {
                    (sigma[i] == k && sigma[j] == l)
                        || (sigma[i] == l && sigma[j] == k)
                })
            })
        })
        .collect()
}

fn audit(p: i64, source: &[i64], cubics: [&[i64]; 2], targets: [&[i64]; 2]) {
    let x = [0, 1];
    assert_eq!(times(cubics[0], cubics[1], p), source);
    for cubic in cubics {
        assert_eq!(cubic.len(), 4);
        assert_eq!(orbit_length(cubic, p), 3);
        assert_eq!(
            gcd(
                cubic.to_vec(),
                minus(&power_mod(&x, p as u64, cubic, p), &x, p),
                p,
            ),
            vec![1],
        );
    }
    for target_raw in targets {
        let target = monic(target_raw, p);
        assert_eq!(target.len(), 7);
        assert_eq!(orbit_length(&target, p), 6);
        assert_eq!(power_mod(&x, (p as u64).pow(6), &target, p), x);
        // Rabin irreducibility: proper prime divisors of degree 6 are 2 and 3.
        for d in [2, 3] {
            assert_eq!(
                gcd(
                    target.clone(),
                    minus(&power_mod(&x, (p as u64).pow(d), &target, p), &x, p),
                    p,
                ),
                vec![1],
            );
        }
    }
    let source_cycles: [&[usize]; 2] = [&[0, 1, 2], &[3, 4, 5]];
    let target_cycles: [&[usize]; 1] = [&[0, 1, 2, 3, 4, 5]];
    assert_eq!(stable_pairings(&source_cycles).len(), 3);
    let target_matchings = stable_pairings(&target_cycles);
    assert_eq!(target_matchings.len(), 1);
    assert_eq!(target_matchings[0], vec![(0, 3), (1, 4), (2, 5)]);
    for (power, expected_source, expected_target) in
        [(1, 1, 1), (2, 1, 1), (3, 16, 4), (6, 16, 16)]
    {
        assert_eq!(
            fixed_geometric_two_torsion(&source_cycles, power),
            expected_source
        );
        assert_eq!(
            fixed_geometric_two_torsion(&target_cycles, power),
            expected_target
        );
    }
}

#[test]
fn ct16_frobenius_and_unpolarized_jacobian_obstruction() {
    audit(
        17,
        &[2, 0, 2, 0, 0, 0, 1],
        [&[7, 1, 6, 1], &[10, 1, 11, 1]],
        [&[10, 6, 14, 2, 12, 10, 9], &[10, 11, 14, 15, 12, 7, 9]],
    );
    audit(
        101,
        &[56, 0, 13, 0, 6, 0, 1],
        [&[67, 63, 25, 1], &[34, 63, 76, 1]],
        [
            &[56, 41, 62, 78, 24, 57, 80],
            &[56, 60, 62, 23, 24, 44, 80],
        ],
    );
}