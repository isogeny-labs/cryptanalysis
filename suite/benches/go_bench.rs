//! Go-style benchmarks for representative `cryptanalysis-suite` code.
//!
//! Output is the Go benchmark format (`Benchmark<name>-<procs>`,
//! `ns/op`, `B/op`), so it can be fed to `benchstat` next to the C
//! `ca_bench` numbers or any Go/C/Rust baseline:
//!
//! ```sh
//! cargo bench --bench go_bench -- -benchtime 100ms -count 5 | tee new.txt
//! benchstat old.txt new.txt
//! ```
//!
//! The harness lives in `src/benchfmt.rs`; it auto-scales `b.N` like
//! `testing.B` and accepts `-bench`, `-benchtime` (duration or `Nx`) and
//! `-count`.

use cryptanalysis_suite::benchfmt::Harness;
use cryptanalysis_suite::binary_ecc::{F2mElement, IrreduciblePoly};
use cryptanalysis_suite::cryptanalysis::koblitz_index_calculus::find_irreducible_sparse;
use cryptanalysis_suite::cryptanalysis::semaev_decomp::Gf2;
use cryptanalysis_suite::hash::sha256::sha256;
use cryptanalysis_suite::symmetric::aes::{encrypt_block, AesKey};
use std::hint::black_box;

fn bits_positions(count: u32) -> Vec<u32> {
    (0..count).step_by(3).collect()
}

fn main() {
    let mut h = Harness::from_env()
        .expect("bad benchmark flags")
        .with_package("cryptanalysis_suite");

    // ── Hashes (the symmetric/hash attack targets) ──────────────────────
    for len in [64usize, 256, 1024, 16 * 1024] {
        let msg = vec![0xa5u8; len];
        h.bench_bytes(&format!("SHA256/{len}B"), len as u64, || {
            black_box(sha256(black_box(&msg)));
        })
        .unwrap();
    }

    // ── Symmetric primitive ─────────────────────────────────────────────
    let aes_key = AesKey::new(&[0x42u8; 16]).unwrap();
    let block = [0x11u8; 16];
    h.bench_bytes("AES128/encrypt_block", 16, || {
        black_box(encrypt_block(black_box(&block), &aes_key));
    })
    .unwrap();

    // ── Binary-field arithmetic (GHS / summation-polynomial path) ───────
    for (label, irr) in [
        ("F2m113", IrreduciblePoly::deg_113()),
        ("F2m131", IrreduciblePoly::deg_131()),
    ] {
        let m = irr.degree;
        let a = F2mElement::from_bit_positions(&bits_positions(m), m);
        let b = F2mElement::from_bit_positions(
            &bits_positions(m).into_iter().rev().collect::<Vec<_>>(),
            m,
        );
        h.bench(&format!("{label}/mul"), || {
            black_box(a.mul(black_box(&b), &irr));
        })
        .unwrap();
        h.bench(&format!("{label}/square"), || {
            black_box(a.square(&irr));
        })
        .unwrap();
        h.bench(&format!("{label}/flt_inverse"), || {
            black_box(a.flt_inverse(&irr));
        })
        .unwrap();
    }

    // ── Koblitz one-word field (the index-calculus inner loop) ──────────
    let irr = find_irreducible_sparse(53).expect("irreducible polynomial for n=53");
    let gf = Gf2::new(&irr);
    let mask = if gf.n >= 64 {
        u64::MAX
    } else {
        (1u64 << gf.n) - 1
    };
    let x = 0x1234_5678_9abcu64 & mask | 1;
    let y = 0x5a5a_1234_5678u64 & mask | 1;
    h.bench("Gf2/n53/mul", || {
        black_box(gf.mul(black_box(x), black_box(y)));
    })
    .unwrap();
    h.bench("Gf2/n53/sqr", || {
        black_box(gf.sqr(black_box(x)));
    })
    .unwrap();
    h.bench("Gf2/n53/inv", || {
        black_box(gf.inv(black_box(x)));
    })
    .unwrap();

    h.flush().unwrap();
}
