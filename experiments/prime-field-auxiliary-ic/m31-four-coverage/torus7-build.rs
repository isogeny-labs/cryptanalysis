//! M31 public-coordinate generation, sorted output and fiber checks.
#![allow(dead_code)]
use std::{hint::black_box, time::Instant};
#[derive(Debug)]
pub enum Error {
    Invalid(&'static str),
}
pub type Result<T> = std::result::Result<T, Error>;
mod field {
    include!(env!("M31_FIELD_RS"));
}
use field::{Curve, F};
include!("torus7-coordinates.rs");

fn twist_tables(xs: &[u64; 128], b: u64, joint: bool) -> (Points, Points) {
    if !joint {
        let mut neg = xs.map(|x| M::sub(0, x));
        neg.sort_unstable();
        return (on_curve::<8>(xs, b), on_curve::<8>(&neg, M::sub(0, b)));
    }
    let mut base = Vec::with_capacity(128);
    let mut twist = Vec::with_capacity(128);
    for chunk in xs.chunks_exact(8) {
        let (rhs, y) = candidates::<8>(chunk, b);
        for i in 0..8 {
            let ordinate = y[i].min(M::sub(0, y[i]));
            let square = M::sq(y[i]);
            if square == rhs[i] {
                base.push((chunk[i], ordinate));
            }
            if square == M::sub(0, rhs[i]) {
                twist.push((M::sub(0, chunk[i]), ordinate));
            }
        }
    }
    twist.sort_unstable();
    (base, twist)
}

fn twist_panel(order: &str) {
    let xs = roots();
    // b=0 and x=0 exercise a root shared by both curves.
    let controls = std::array::from_fn(|i| i as u64);
    for (inputs, b) in [(&xs, 14), (&controls, 0)] {
        let pair = twist_tables(inputs, b, true);
        assert_eq!(pair, twist_tables(inputs, b, false));
        for (coords, coeff, neg) in [(&pair.0, b, false), (&pair.1, M::sub(0, b), true)] {
            let curve = Curve::<31>::new(2, coeff).unwrap();
            let mut reference: Points = inputs
                .iter()
                .filter_map(|&x| {
                    let x = if neg { M::sub(0, x) } else { x };
                    curve.lift_x(x).unwrap().map(|p| (x, p.y()))
                })
                .collect();
            reference.sort_unstable();
            assert_eq!(coords, &reference);
        }
        if b == 0 {
            assert!(pair.0.contains(&(0, 0)) && pair.1.contains(&(0, 0)));
        } else {
            assert_eq!((pair.0.len(), pair.1.len()), (71, 57));
        }
    }
    for mode in order.chars() {
        let joint = match mode {
            'j' => true,
            's' => false,
            _ => panic!("unknown mode"),
        };
        let start = Instant::now();
        for _ in 0..2048 {
            let roots = roots();
            black_box(twist_tables(&roots, black_box(14), joint));
        }
        println!("{mode},{:.3}", start.elapsed().as_nanos() as f64 / 2048.);
    }
}

#[path = "membership-bench.rs"]
mod membership;

fn branch_key(mut x: u64) -> u32 {
    let mut bits = 0;
    for j in 0..7 {
        bits |= u32::from(x > M::P / 2) << j;
        x = M::sub(M::sq(x), 2);
    }
    bits
}

fn branch_cost(seed: u64, order: &str) {
    let mut xs = roots();
    let curve = Curve::<31>::new(2, 14).unwrap();
    let positive: Vec<_> = xs
        .iter()
        .filter(|&&x| curve.lift_x(x).unwrap().is_some())
        .map(|&x| x as u32)
        .collect();
    let buckets = membership::build(&positive);
    let mask = 0x5ec55aed5ec7a5051ebd2a65e6d923ee_u128;
    let mut state = seed;
    for i in (1..128).rev() {
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        xs.swap(i, state as usize % (i + 1));
    }
    let keys = xs.map(branch_key);
    for (&x, &key) in xs.iter().zip(&keys) {
        assert_eq!(
            membership::lookup(&buckets, &positive, x as u32),
            (mask >> key) & 1 == 1
        );
    }
    for method in order.chars() {
        let start = Instant::now();
        let mut hits = 0;
        for _ in 0..16384 {
            hits += match method {
                'x' => black_box(&xs)
                    .iter()
                    .filter(|&&x| membership::lookup(&buckets, &positive, x as u32))
                    .count(),
                'g' => black_box(&xs)
                    .iter()
                    .filter(|&&x| (mask >> branch_key(x)) & 1 == 1)
                    .count(),
                'k' => black_box(&keys)
                    .iter()
                    .filter(|&&key| (mask >> key) & 1 == 1)
                    .count(),
                _ => panic!("bad method"),
            };
        }
        let ns = start.elapsed().as_nanos() as f64 / 16384.;
        assert_eq!(hits, 71 * 16384);
        println!("{method},{ns:.3}");
    }
}

include!("fiber-filter.rs");

include!("fiber-address.rs");

include!("fiber-cache.rs");

include!("fiber-half.rs");

fn main() {
    #[cfg(all(target_arch = "aarch64", target_feature = "neon"))]
    if std::env::args().nth(1).as_deref() == Some("validate-signed") {
        neon_lift::check_signed();
        return;
    }
    #[cfg(all(target_arch = "aarch64", target_feature = "neon"))]
    if std::env::args().nth(1).as_deref() == Some("fiber-half") {
        let args: Vec<_> = std::env::args().collect();
        half_bench(
            args[2].parse().unwrap(),
            &args[3],
            args.iter().skip(4).any(|s| s == "holdout"),
            args.iter().skip(4).any(|s| s == "single"),
        );
        return;
    }
    if std::env::args().nth(1).as_deref() == Some("fiber-cache") {
        let args: Vec<_> = std::env::args().collect();
        cache_bench(args[2].parse().unwrap(), args[3].parse().unwrap(), &args[4]);
        return;
    }
    if std::env::args().nth(1).as_deref() == Some("fiber-address") {
        address_bench(
            std::env::args().nth(2).unwrap().parse().unwrap(),
            &std::env::args().nth(3).unwrap(),
        );
        return;
    }
    if std::env::args().nth(1).as_deref() == Some("fiber-filter") {
        filter_bench(
            std::env::args().nth(2).unwrap().parse().unwrap(),
            &std::env::args().nth(3).unwrap(),
        );
        return;
    }
    #[cfg(all(target_arch = "aarch64", target_feature = "neon"))]
    if std::env::args().nth(1).as_deref() == Some("validate-neon") {
        neon_lift::validate();
        return;
    }
    if std::env::args().nth(1).as_deref() == Some("branch-cost") {
        branch_cost(
            std::env::args().nth(2).unwrap().parse().unwrap(),
            &std::env::args().nth(3).unwrap(),
        );
        return;
    }
    if std::env::args().nth(1).as_deref() == Some("twist") {
        twist_panel(&std::env::args().nth(2).unwrap());
        return;
    }
    let curve = Curve::<31>::new(2, 14).unwrap();
    let expected = build(0, curve);
    assert_eq!(expected.len(), 71);
    for arg in std::env::args().skip(1) {
        if arg == "points" {
            for (x, y) in &expected {
                println!("{x},{y}");
            }
            continue;
        }
        let width = arg.parse().unwrap();
        assert_eq!(build(width, curve), expected);
        let start = Instant::now();
        for _ in 0..1024 {
            black_box(build(black_box(width), black_box(curve)));
        }
        println!("{width},{:.3}", start.elapsed().as_nanos() as f64 / 1024.);
    }
}
