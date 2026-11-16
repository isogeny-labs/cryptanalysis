//! Same public S3 descent API as the framework; cold context and first build.
use cryptanalysis_suite::cryptanalysis::koblitz_index_calculus::find_irreducible_sparse;
use cryptanalysis_suite::cryptanalysis::pq_descent_symbolic::{
    descend, semaev_s3_word, semaev_s4_word,
};
use cryptanalysis_suite::cryptanalysis::semaev_decomp::Gf2;
use rand::{rngs::StdRng, Rng, SeedableRng};
use sha2::{Digest, Sha256};
use std::time::Instant;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let n: u32 = args[1].parse().unwrap();
    let np: usize = args[2].parse().unwrap();
    let fixture: u64 = args[3].parse().unwrap();
    let summands: u32 = args.get(4).map(|s| s.parse().unwrap()).unwrap_or(2);
    assert!(np <= n as usize && np * summands as usize <= 64);
    let irr = find_irreducible_sparse(n).unwrap();
    let mask = (1u64 << n) - 1;
    let mut rng =
        StdRng::seed_from_u64(0x5333_2026_1115 ^ fixture.wrapping_mul(0x9e37_79b9_7f4a_7c15));
    // The low np bits are the identity matrix, so the basis is independent.
    let low = (1u64 << np) - 1;
    let basis: Vec<u64> = (0..np)
        .map(|i| (1u64 << i) ^ (rng.gen::<u64>() & mask & !low))
        .collect();
    let b = (rng.gen::<u64>() & mask) | 1;
    let x_r = rng.gen::<u64>() & mask;
    let context_started = Instant::now();
    let gf = Gf2::new(&irr);
    let context_s = context_started.elapsed().as_secs_f64();
    let started = Instant::now();
    let system = descend(&gf, b, x_r, &basis, summands).unwrap();
    let build_s = started.elapsed().as_secs_f64();
    for _ in 0..32 {
        let assignment = rng.gen::<u64>();
        let xs = system.lift(assignment);
        let direct = match summands {
            2 => semaev_s3_word(&gf, b, xs[0], xs[1], x_r),
            3 => semaev_s4_word(&gf, b, xs[0], xs[1], xs[2], x_r),
            _ => unreachable!(),
        };
        for (bit, equation) in system.equations.iter().enumerate() {
            assert_eq!(u64::from(equation.eval(assignment)), (direct >> bit) & 1);
        }
    }
    let masks: Vec<Vec<u64>> = system
        .equations
        .iter()
        .map(|p| p.terms.iter().map(|m| m.mask).collect())
        .collect();
    let serialized = serde_json::to_vec(&(system.n_vars, system.field_monomials, &masks)).unwrap();
    let checksum = hex::encode(Sha256::digest(&serialized));
    println!(
        "{}",
        serde_json::json!({
            "n":n,"np":np,"summands":summands,"fixture":fixture,"basis":basis,"b":b,"x_r":x_r,
            "field_polynomial_terms":irr.low_terms,"context_s":context_s,"first_build_s":build_s,
            "cold_stage_s":context_s+build_s,"field_monomials":system.field_monomials,
            "coordinate_terms":masks.iter().map(Vec::len).sum::<usize>(),
            "checksum":checksum,"equation_checks":32,"feature":cfg!(feature="s3-direct-coefficients")
        })
    );
}
