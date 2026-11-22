//! Benchmark complete affine addition on fixed 64-point M31 batches.
//! By default, columns are exceptional slots, reference ns/batch, and one, four,
//! and eight product lanes. With "tangents", columns compare reference, four
//! lanes, shared tangent inversions, and shared inversions with cached numerators.
//! With "isolated", the first column selects the exceptional case for all 64
//! slots (0 left identity, 1 right identity, 2 doubling, 3 inverse pair).
//! Each timing row covers 2,048 batches.
//! Generated points and scalar-reference checks are outside the timer.
//! rustc --edition=2021 -C opt-level=3 -C target-cpu=native batch_add_64_bench.rs -o /tmp/batch-add-64
#![allow(dead_code)]
use std::{hint::black_box, time::Instant};
#[derive(Debug)]
pub enum Error {
    Invalid(&'static str),
}
pub type Result<T> = std::result::Result<T, Error>;
mod field {
    include!("../../crates/prime-field-auxiliary-ic/src/field.rs");
    pub type Batch = [Option<Point>; 64];
    #[inline(never)]
    pub fn striped<const W: usize, const TANGENTS: bool, const CACHE: bool>(
        curve: Curve<31>,
        points: &mut Batch,
        steps: &Batch,
        _scratch: &mut BatchScratch,
    ) {
        assert!(W > 0 && 64 % W == 0);
        let mut products = [1; W];
        let mut prefix = [0; 64];
        let mut denominators = [0; 64];
        let mut numerators = [0; 64];
        for t in 0..64 / W {
            for j in 0..W {
                let i = t * W + j;
                let den = match (points[i], steps[i]) {
                    (Some(a), Some(b)) => {
                        if TANGENTS && a == b {
                            if CACHE {
                                numerators[i] =
                                    F::<31>::add(F::<31>::mul(3, F::<31>::sq(a.x)), curve.a);
                            }
                            F::<31>::add(a.y, a.y)
                        } else {
                            if CACHE {
                                numerators[i] = F::<31>::sub(b.y, a.y);
                            }
                            F::<31>::sub(b.x, a.x)
                        }
                    }
                    _ => 0,
                };
                prefix[i] = products[j];
                denominators[i] = den;
                products[j] = F::<31>::mul(products[j], den.max(1));
            }
        }
        let mut lane_prefix = [1; W];
        let mut total = 1;
        for j in 0..W {
            lane_prefix[j] = total;
            total = F::<31>::mul(total, products[j]);
        }
        let mut inverse = F::<31>::inv(total);
        for j in (0..W).rev() {
            let p = products[j];
            products[j] = F::<31>::mul(inverse, lane_prefix[j]);
            inverse = F::<31>::mul(inverse, p);
        }
        for t in (0..64 / W).rev() {
            for j in 0..W {
                let i = t * W + j;
                let den = denominators[i];
                let inv = F::<31>::mul(products[j], prefix[i]);
                products[j] = F::<31>::mul(products[j], den.max(1));
                points[i] = if den == 0 {
                    curve.add_inner(points[i], steps[i])
                } else {
                    let a = points[i].unwrap();
                    let b = steps[i].unwrap();
                    let numerator = if CACHE {
                        numerators[i]
                    } else if TANGENTS && a.x == b.x {
                        F::<31>::add(F::<31>::mul(3, F::<31>::sq(a.x)), curve.a)
                    } else {
                        F::<31>::sub(b.y, a.y)
                    };
                    Some(curve.finish_add(a, b, F::<31>::mul(numerator, inv)))
                };
            }
        }
    }
    #[inline(never)]
    pub fn reference(
        curve: Curve<31>,
        points: &mut Batch,
        steps: &Batch,
        scratch: &mut BatchScratch,
    ) {
        curve.batch_add_inner(points, steps, scratch);
    }
}
use field::{Batch, BatchScratch, Curve};
fn main() {
    let c = Curve::<31>::new(2, 14).unwrap();
    let mut rng = 20261121u64;
    let mut sample = || loop {
        rng ^= rng << 13;
        rng ^= rng >> 7;
        rng ^= rng << 17;
        if let Some(p) = c.lift_x(rng % c.modulus()).unwrap() {
            break Some(p);
        }
    };
    let mode = std::env::args().nth(1).unwrap_or_else(|| "lanes".into());
    assert!(
        matches!(mode.as_str(), "lanes" | "tangents" | "isolated"),
        "expected lanes, tangents, or isolated"
    );
    let paths: [fn(Curve<31>, &mut Batch, &Batch, &mut BatchScratch); 4] = if mode == "lanes" {
        [
            field::reference,
            field::striped::<1, false, false>,
            field::striped::<4, false, false>,
            field::striped::<8, false, false>,
        ]
    } else {
        [
            field::reference,
            field::striped::<4, false, false>,
            field::striped::<4, true, false>,
            field::striped::<4, true, true>,
        ]
    };
    let auxiliary = Curve::<31>::new(1, 0).unwrap();
    let torsion = Some(auxiliary.point(0, 0).unwrap());
    for f in paths {
        let mut batch = [torsion; 64];
        f(
            auxiliary,
            &mut batch,
            &[torsion; 64],
            &mut BatchScratch::default(),
        );
        assert_eq!(batch, [None; 64]);
    }
    let cases: &[usize] = if mode == "isolated" {
        &[0, 1, 2, 3]
    } else {
        &[0, 1, 8, 32, 64]
    };
    for &case in cases {
        let exceptions = if mode == "isolated" { 64 } else { case };
        let mut pairs = Vec::new();
        for k in 0..128 {
            let mut a: Batch = std::array::from_fn(|_| sample());
            let mut b: Batch = std::array::from_fn(|_| sample());
            for j in 0..exceptions {
                let i = (j * 17 + k) % 64;
                match if mode == "isolated" {
                    case
                } else {
                    (j + k) % 4
                } {
                    0 => a[i] = None,
                    1 => b[i] = None,
                    2 => b[i] = a[i],
                    _ => b[i] = Some(c.negate(a[i].unwrap()).unwrap()),
                }
            }
            let expected: Batch = std::array::from_fn(|i| c.add(a[i], b[i]).unwrap());
            for f in paths {
                let mut v = a;
                f(c, &mut v, &b, &mut BatchScratch::default());
                assert_eq!(v, expected);
            }
            pairs.push((a, b));
        }
        for r in 0..17 {
            let mut nanoseconds = [0.0; 4];
            for j in 0..4 {
                let i = (r / 2 + if r % 2 == 0 { j } else { 3 - j }) % 4;
                let mut scratch = BatchScratch::default();
                let mut warm = pairs[0].0;
                paths[i](c, &mut warm, &pairs[0].1, &mut scratch);
                let start = Instant::now();
                for _ in 0..16 {
                    for (a, b) in &pairs {
                        let mut v = *black_box(a);
                        paths[i](c, &mut v, black_box(b), &mut scratch);
                        black_box(&v);
                    }
                }
                nanoseconds[i] = start.elapsed().as_nanos() as f64 / 2048.;
            }
            if r > 0 {
                println!(
                    "{} {} {} {} {}",
                    case, nanoseconds[0], nanoseconds[1], nanoseconds[2], nanoseconds[3]
                );
            }
        }
    }
}
