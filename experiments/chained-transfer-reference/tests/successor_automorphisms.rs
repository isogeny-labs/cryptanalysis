//! Complete geometric branch-automorphism certificate for the two fixed
//! Richelot targets. Existing FpR/polynomial engines only;no DLP/benchmark.
use isogeny_algos::field::{Field, Rng};
use isogeny_algos::fpr::{FpR, ER};
use isogeny_algos::poly;
use std::collections::HashSet;

fn cross_ratio(f: &FpR, roots: [ER; 3]) -> [ER; 4] {
    let [a, b, c] = roots;
    let u = f.sub(b, c);
    let v = f.sub(b, a);
    [u, f.neg(f.mul(a, u)), v, f.neg(f.mul(c, v))]
}

fn from_triples(f: &FpR, source: [ER; 3], target: [ER; 3]) -> [ER; 4] {
    let [a, b, c, d] = cross_ratio(f, source);
    let [u, v, w, z] = cross_ratio(f, target);
    let matrix = [
        f.sub(f.mul(z, a), f.mul(v, c)),
        f.sub(f.mul(z, b), f.mul(v, d)),
        f.sub(f.mul(u, c), f.mul(w, a)),
        f.sub(f.mul(u, d), f.mul(w, b)),
    ];
    assert_ne!(
        f.sub(f.mul(matrix[0], matrix[3]), f.mul(matrix[1], matrix[2])),
        f.zero()
    );
    let pivot = *matrix.iter().find(|x| **x != f.zero()).unwrap();
    matrix.map(|x| f.div(x, pivot))
}

fn image(f: &FpR, m: &[ER; 4], x: ER) -> Option<ER> {
    let denominator = f.add(f.mul(m[2], x), m[3]);
    if denominator == f.zero() {
        None
    } else {
        Some(f.div(f.add(f.mul(m[0], x), m[1]), denominator))
    }
}

fn audit(f: &FpR, coefficients: [u64; 7]) -> usize {
    let p = coefficients.map(|c| f.from_u64(c)).to_vec();
    let mut rng = Rng::new(0x0021_a017);
    let roots = poly::roots(f, &p, &mut rng);
    assert_eq!(roots.len(), 6);
    assert_eq!(roots.iter().copied().collect::<HashSet<_>>().len(), 6);
    let mut product = vec![f.one()];
    for r in &roots {
        assert_eq!(poly::eval(f, &p, *r), f.zero());
        product = poly::mul(f, &product, &vec![f.neg(*r), f.one()]);
    }
    assert_eq!(product, p);
    let source = [roots[0], roots[1], roots[2]];
    let mut matrices = HashSet::new();
    let mut automorphisms = vec![];
    for i in 0..6 {
        for j in 0..6 {
            for k in 0..6 {
                if i == j || i == k || j == k {
                    continue;
                }
                let target = [roots[i], roots[j], roots[k]];
                let m = from_triples(f, source, target);
                for (a, b) in source.into_iter().zip(target) {
                    assert_eq!(image(f, &m, a), Some(b));
                }
                assert!(matrices.insert(m));
                let permutation = roots
                    .iter()
                    .map(|x| image(f, &m, *x).and_then(|y| roots.iter().position(|r| *r == y)))
                    .collect::<Option<Vec<_>>>();
                if let Some(permutation) = permutation {
                    assert_eq!(permutation.iter().copied().collect::<HashSet<_>>().len(), 6);
                    automorphisms.push((m, permutation));
                }
            }
        }
    }
    assert_eq!(matrices.len(), 120);
    println!("fixed target{coefficients:?}:six actualFp6 roots,exactfactor product,all120 unique PGL2 triple-images;preserving branchset {}",automorphisms.len());
    for (matrix, permutation) in &automorphisms {
        println!("branch automorphism permutation{permutation:?},matrix{matrix:?}");
    }
    automorphisms.len()
}

#[test]
fn all_geometric_branch_automorphisms_on_actual_richelot_targets() {
    let f = FpR::from_modulus(101, &[33, 46, 2, 18, 56, 12, 1]);
    for coefficients in [[31, 75, 74, 54, 71, 55, 1], [95, 26, 19, 27, 94, 91, 1]] {
        assert_eq!(
            audit(&f, coefficients),
            1,
            "only identity may preserve the full branch set"
        );
    }
    println!("PASS both complete geometric PGL2 branch stabilizers trivial. Every geometric branch automorphism is determined by three roots,so coefficients lie in the declared splitting field. Hyperelliptic/Torelli bridge identifies polarized-Jacobian automorphisms with plus/minus identity;that bridge remains written,not Lean formalized.");
}

#[cfg(not(test))]
fn main() {
    println!("Development certificate:run cargo test --release --locked --example chained_richelot_automorphisms -- --nocapture");
}

// Versioned reuse: the complete accepted oracle above is an immutable prefix.
// The new fixture does not modify its field/polynomial/PGL2 implementation.
#[test]
fn successor_complete_geometric_branch_automorphisms() {
    let accepted = include_bytes!("richelot_automorphisms.rs");
    assert!(include_bytes!("successor_automorphisms.rs").starts_with(accepted));
    let f = FpR::from_modulus(101, &[33, 46, 2, 18, 56, 12, 1]);
    assert_eq!(audit(&f, [95, 93, 43, 39, 92, 17, 1]), 1);
    println!("PASS actual T2 all120 unique PGL2 triple-images,only identity preserves the six roots;accepted independent oracle is byte-identical prefix. Hyperelliptic/Torelli and prime-field descent remain the written bridge.");
}
