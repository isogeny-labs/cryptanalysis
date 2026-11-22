//! Micro-timings of the ideal engine's primitives at a given rank (diagnostic).
use cryptanalysis_suite::highgenus::fp::Fp;
use cryptanalysis_suite::highgenus::instances::prime_one_mod;
use cryptanalysis_suite::highgenus::kummer::SuperellipticCurve;
use cryptanalysis_suite::highgenus::poly::Poly;
use rand::rngs::StdRng;
use rand::SeedableRng;
use std::time::Instant;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let m: u32 = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(11);
    let p = prime_one_mod(m as u64, 3).unwrap();
    let k = Fp::new(p).unwrap();
    let x = Poly::from_coeffs(vec![0, 1], &k);
    let xm1 = Poly::from_coeffs(vec![p - 1, 1], &k);
    let c = SuperellipticCurve::new(k, m, vec![(x, 1), (xm1, 2)]).unwrap();
    let mut rng = StdRng::seed_from_u64(1);
    let t = Instant::now();
    let a = c.random_element(1, &mut rng);
    let b = c.random_element(1, &mut rng);
    eprintln!(
        "m={m} p={p} g={} two random elements in {:?} (deg {} {})",
        c.genus,
        t.elapsed(),
        a.degree(),
        b.degree()
    );
    let t = Instant::now();
    let prod = c.mul_ideals(&a, &b);
    eprintln!("mul_ideals {:?} (deg {})", t.elapsed(), prod.degree());
    let t = Instant::now();
    let _ = c.two_generators(&prod);
    eprintln!("two_generators {:?}", t.elapsed());
    let t = Instant::now();
    let phi = c.minimal_element(&prod);
    eprintln!("minimal_element {:?} wdeg {:?}", t.elapsed(), c.wdeg(&phi));
    let t = Instant::now();
    let q = c.quotient(&prod, &phi);
    eprintln!("quotient {:?} (deg {})", t.elapsed(), q.degree());
    let t = Instant::now();
    let _ = c.reduce_once(&q);
    eprintln!("second reduce_once {:?}", t.elapsed());
    let _ = cryptanalysis_suite::highgenus::kummer::profile_snapshot();
    let t = Instant::now();
    let _ = c.add_classes(&a, &b);
    eprintln!("add_classes {:?}", t.elapsed());
    let prof = cryptanalysis_suite::highgenus::kummer::profile_snapshot();
    eprintln!("profile [hnf, mul_elt, two_gen, adj, minimal] = {prof:?}");
}
