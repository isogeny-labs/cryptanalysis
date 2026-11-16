use ic_f2m_three_limb_validation::f2m::{F2mElement, IrreduciblePoly};
use std::hint::black_box;
use std::time::Instant;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let degree: u32 = args[1].parse().unwrap();
    let fixture: u64 = args[2].parse().unwrap();
    let iterations: u64 = args[3].parse().unwrap();
    let poly = match degree {
        113 => IrreduciblePoly::deg_113(),
        131 => IrreduciblePoly::deg_131(),
        155 => IrreduciblePoly::deg_155_oakley_group3(),
        163 => IrreduciblePoly::deg_163(),
        233 => IrreduciblePoly::deg_233(),
        _ => panic!("unsupported degree"),
    };
    let mut seed = 0x6a09_e667_f3bc_c909_u64 ^ fixture.wrapping_mul(0x9e37_79b9_7f4a_7c15);
    let mut element = || {
        let mut bits = Vec::new();
        for bit in 0..degree {
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            if seed & 1 != 0 {
                bits.push(bit);
            }
        }
        F2mElement::from_bit_positions(&bits, degree)
    };
    let mut value = element();
    let rhs = element();
    assert_eq!(value.mul(&rhs, &poly), value.schoolbook_mul(&rhs, &poly));
    let initial = value.to_biguint().to_str_radix(16);
    let multiplier = rhs.to_biguint().to_str_radix(16);
    let started = Instant::now();
    for _ in 0..iterations {
        value = black_box(value.mul(black_box(&rhs), black_box(&poly)));
    }
    let seconds = started.elapsed().as_secs_f64();
    let checksum = value.to_biguint().to_str_radix(16);
    println!("{{\"degree\":{degree},\"fixture\":{fixture},\"iterations\":{iterations},\"wall_s\":{seconds:.12},\"specialized\":{},\"initial\":\"{initial}\",\"multiplier\":\"{multiplier}\",\"checksum\":\"{checksum}\"}}", cfg!(feature = "f2m-karatsuba3"));
}
