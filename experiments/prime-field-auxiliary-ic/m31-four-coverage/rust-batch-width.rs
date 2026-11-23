//! Compile against the field.rs under test, setting M31_FIELD_RS to its absolute path.
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
use field::{BatchScratch, Curve, Point};

fn sample_point(curve: Curve<31>, state: &mut u64) -> Option<Point> {
    loop {
        *state ^= *state << 13;
        *state ^= *state >> 7;
        *state ^= *state << 17;
        if let Some(p) = curve.lift_x(*state % curve.modulus()).unwrap() {
            return Some(p);
        }
    }
}

type Batch = (Vec<Option<Point>>, Vec<Option<Point>>);

fn measure(curve: Curve<31>, cases: &[Batch], scratch: &mut BatchScratch) -> f64 {
    let size = cases[0].0.len();
    let reps = (131072 / (size.max(1) * cases.len())).clamp(4, 256);
    let mut result = cases[0].0.clone();
    let start = Instant::now();
    for _ in 0..reps {
        for (a, b) in cases {
            result.copy_from_slice(black_box(a));
            curve.batch_add_inner(&mut result, black_box(b), scratch);
            black_box(&result);
        }
    }
    start.elapsed().as_nanos() as f64 / (reps * cases.len()) as f64
}

fn operand_shapes(curve: Curve<31>, state: &mut u64) {
    println!("size,shape,ns_per_batch");
    let mut scratch = BatchScratch::default();
    for size in [64, 112, 116, 142] {
        let mut cases = Vec::new();
        let mut index_state = 2718281828u64;
        let table: Vec<_> = (0..32).map(|_| sample_point(curve, state)).collect();
        let mut signed = Vec::new();
        for _ in 0..size / 2 {
            let point = sample_point(curve, state);
            signed.extend([point, Some(curve.negate(point.unwrap()).unwrap())]);
        }
        let shape = if size == 64 {
            "reused_rhs_table"
        } else {
            "broadcast_lhs_signed_rhs"
        };
        for _ in 0..32 {
            let (a, b): Batch = if size == 64 {
                let a = (0..size).map(|_| sample_point(curve, state)).collect();
                let b = (0..size)
                    .map(|_| {
                        index_state ^= index_state << 13;
                        index_state ^= index_state >> 7;
                        index_state ^= index_state << 17;
                        table[(index_state % 32) as usize]
                    })
                    .collect();
                (a, b)
            } else {
                (vec![sample_point(curve, state); size], signed.clone())
            };
            let expected: Vec<_> = a
                .iter()
                .zip(&b)
                .map(|(&x, &y)| curve.add(x, y).unwrap())
                .collect();
            let mut actual = a.clone();
            curve.batch_add(&mut actual, &b, &mut scratch).unwrap();
            assert_eq!(actual, expected);
            cases.push((a, b));
        }
        println!("{size},{shape},{:.3}", measure(curve, &cases, &mut scratch));
    }
}

fn main() {
    let curve = Curve::<31>::new(2, 14).unwrap();
    let mut state = 0x2718281828459045;
    if std::env::args().nth(1).as_deref() == Some("shapes") {
        operand_shapes(curve, &mut state);
        return;
    }
    let mut scratch = BatchScratch::default();
    println!("size,exception_spacing,ns_per_batch");
    for size in [0, 1, 4, 8, 16, 31, 32, 63, 64, 65, 128, 256] {
        for spacing in [0, 8, 1] {
            let mut cases = Vec::new();
            for k in 0..16 {
                let mut a: Vec<_> = (0..size).map(|_| sample_point(curve, &mut state)).collect();
                let mut b: Vec<_> = (0..size).map(|_| sample_point(curve, &mut state)).collect();
                for j in 0..size {
                    if spacing != 0 && (j + k) % spacing == 0 {
                        match (j / spacing + k) % 4 {
                            0 => a[j] = None,
                            1 => b[j] = None,
                            2 => b[j] = a[j],
                            _ => b[j] = Some(curve.negate(a[j].unwrap()).unwrap()),
                        }
                    }
                }
                let expected: Vec<_> = a
                    .iter()
                    .zip(&b)
                    .map(|(&x, &y)| curve.add(x, y).unwrap())
                    .collect();
                let mut result = a.clone();
                curve.batch_add(&mut result, &b, &mut scratch).unwrap();
                assert_eq!(result, expected);
                cases.push((a, b));
            }
            println!(
                "{size},{spacing},{:.3}",
                measure(curve, &cases, &mut scratch)
            );
        }
    }
}
