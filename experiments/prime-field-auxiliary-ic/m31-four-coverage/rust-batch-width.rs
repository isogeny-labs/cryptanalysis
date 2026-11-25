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
    #[cfg(signed_pairs)]
    include!("signed-pairs.rs");
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

// Independent public keys isolate the cost of a full membership scan.
fn count_hits(points: &[Option<Point>], keys: &[u64]) -> usize {
    points
        .iter()
        .flatten()
        .filter(|p| keys.binary_search(&p.x()).is_ok())
        .count()
}

fn phases(curve: Curve<31>, state: &mut u64, order: &str) {
    const WIDTH: usize = 142;
    let reps: usize = std::env::args().nth(3).map_or(128, |s| s.parse().unwrap());
    assert!(reps > 0);
    let mut scratch = BatchScratch::default();
    let mut keys: Vec<_> = (0..WIDTH / 2)
        .map(|_| sample_point(curve, state).unwrap().x())
        .collect();
    keys.sort_unstable();
    let mut right = Vec::new();
    for _ in 0..WIDTH / 2 {
        let p = sample_point(curve, state).unwrap();
        right.extend([Some(p), Some(curve.negate(p).unwrap())]);
    }
    let mut cases = Vec::new();
    let mut result = vec![None; WIDTH];
    for _ in 0..32 {
        let p = sample_point(curve, state);
        let sums: Vec<_> = right.iter().map(|&q| curve.add(p, q).unwrap()).collect();
        result.fill(p);
        curve.batch_add_inner(&mut result, &right, &mut scratch);
        assert_eq!(result, sums);
        cases.push((p, sums));
    }
    let hits: usize = cases.iter().map(|(_, sums)| count_hits(sums, &keys)).sum();
    for phase in order.chars() {
        let start = Instant::now();
        let mut found = 0;
        for _ in 0..reps {
            for (p, sums) in &cases {
                match phase {
                    'a' | 'c' => {
                        result.fill(black_box(*p));
                        curve.batch_add_inner(&mut result, black_box(&right), &mut scratch);
                        let output = black_box(&result);
                        if phase == 'c' {
                            found += count_hits(output, black_box(&keys));
                        }
                    }
                    'l' => found += count_hits(black_box(sums), black_box(&keys)),
                    _ => panic!("unknown phase"),
                }
            }
        }
        let ns = start.elapsed().as_nanos() as f64 / (reps * cases.len()) as f64;
        assert_eq!(found, if phase == 'a' { 0 } else { reps * hits });
        println!("{phase},{hits},{ns:.3}");
    }
}

#[path = "membership-bench.rs"]
mod membership;

fn coordinate_lookup(curve: Curve<31>, path: &str, round: u64) {
    let keys: Vec<u32> = std::fs::read_to_string(path)
        .unwrap()
        .lines()
        .map(|s| s.parse().unwrap())
        .collect();
    assert_eq!(keys.len(), 71);
    assert!(keys.windows(2).all(|w| w[0] < w[1]));
    let repetitions: usize = std::env::args().nth(4).map_or(1024, |s| s.parse().unwrap());
    assert!(repetitions > 0);
    let table = membership::build(&keys);
    let mut right = Vec::new();
    for &key in &keys {
        let p = curve.lift_x(u64::from(key)).unwrap().unwrap();
        right.extend([Some(p), Some(curve.negate(p).unwrap())]);
    }
    let mut state = 0x2718281828459045 ^ round;
    let cases: Vec<_> = (0..64).map(|_| sample_point(curve, &mut state)).collect();
    let mut output = vec![None; right.len()];
    let mut scratch = BatchScratch::default();
    let mut hits = 0;
    for &p in cases.iter().chain([None].iter()) {
        output.fill(p);
        curve.batch_add_inner(&mut output, &right, &mut scratch);
        for (&sum, &q) in output.iter().zip(&right) {
            assert_eq!(sum, curve.add(p, q).unwrap());
            if let Some(point) = sum {
                let x = point.x() as u32;
                let present = keys.binary_search(&x).is_ok();
                assert_eq!(present, membership::lookup(&table, &keys, x));
                if p.is_some() {
                    hits += usize::from(present);
                } else {
                    assert!(present);
                }
            }
        }
    }
    #[cfg(signed_pairs)]
    if std::env::args().nth(1).as_deref() == Some("signed-pairs") {
        let reps: [Point; 71] = std::array::from_fn(|i| right[2 * i].unwrap());
        let mut paired = vec![None; right.len()];
        for &p in cases.iter().chain(&right).chain([None].iter()) {
            field::signed_batch(curve, p, &reps, &mut paired);
            for (&got, &q) in paired.iter().zip(&right) {
                assert_eq!(got, curve.add(p, q).unwrap());
            }
        }
        for shared in [round % 2 == 0, round % 2 != 0] {
            let start = Instant::now();
            let mut found = 0;
            for _ in 0..repetitions {
                for &p in &cases {
                    if shared {
                        field::signed_batch(curve, black_box(p), black_box(&reps), &mut output);
                    } else {
                        output.fill(black_box(p));
                        curve.batch_add_inner(&mut output, black_box(&right), &mut scratch);
                    }
                    found += black_box(&output)
                        .iter()
                        .flatten()
                        .filter(|p| membership::lookup(&table, &keys, p.x() as u32))
                        .count();
                }
            }
            let ns = start.elapsed().as_nanos() as f64 / (repetitions * cases.len()) as f64;
            assert_eq!(found, hits * repetitions);
            println!("{round},{shared},{hits},{ns:.3}");
        }
        return;
    }
    let keys = black_box(keys.as_slice());
    let table = black_box(&table);
    let mut run = |bucket: bool| {
        let start = Instant::now();
        let mut found = 0;
        for _ in 0..repetitions {
            for &p in &cases {
                output.fill(black_box(p));
                curve.batch_add_inner(&mut output, black_box(&right), &mut scratch);
                let sums = black_box(output.as_slice());
                found += if bucket {
                    sums.iter()
                        .flatten()
                        .filter(|p| membership::lookup(table, keys, p.x() as u32))
                        .count()
                } else {
                    sums.iter()
                        .flatten()
                        .filter(|p| keys.binary_search(&(p.x() as u32)).is_ok())
                        .count()
                };
            }
        }
        let ns = start.elapsed().as_nanos() as f64 / (repetitions * cases.len()) as f64;
        assert_eq!(found, hits * repetitions);
        println!("{round},{bucket},{hits},{ns:.3}");
    };
    run(round % 2 == 0);
    run(round % 2 != 0);
}

include!("setup-batches.rs");

fn main() {
    let curve = Curve::<31>::new(2, 14).unwrap();
    #[cfg(all(
        target_arch = "aarch64",
        target_feature = "neon",
        neon_coordinates,
        signed_pairs
    ))]
    if std::env::args().nth(1).as_deref() == Some("coordinate-only") {
        coordinate_panel(
            curve,
            &std::env::args().nth(2).unwrap(),
            std::env::args().nth(3).as_deref() == Some("first"),
        );
        return;
    }
    if std::env::args().nth(1).as_deref() == Some("trace-batches") {
        setup_panel::<true>(
            curve,
            &std::env::args().nth(2).unwrap(),
            std::env::args().nth(3).unwrap().parse().unwrap(),
        );
        return;
    }
    if std::env::args().nth(1).as_deref() == Some("setup-batches") {
        setup_panel::<false>(
            curve,
            &std::env::args().nth(2).unwrap(),
            std::env::args().nth(3).unwrap().parse().unwrap(),
        );
        return;
    }
    if std::env::args().nth(1).as_deref() == Some("coordinate-lookup")
        || (cfg!(signed_pairs) && std::env::args().nth(1).as_deref() == Some("signed-pairs"))
    {
        coordinate_lookup(
            curve,
            &std::env::args().nth(2).unwrap(),
            std::env::args().nth(3).unwrap().parse().unwrap(),
        );
        return;
    }
    let mut state = 0x2718281828459045;
    if std::env::args().nth(1).as_deref() == Some("phases") {
        phases(
            curve,
            &mut state,
            &std::env::args().nth(2).expect("phase order"),
        );
        return;
    }
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

#[cfg(all(
    target_arch = "aarch64",
    target_feature = "neon",
    neon_coordinates,
    signed_pairs
))]
fn coordinate_panel(curve: Curve<31>, order: &str, first: bool) {
    for method in order.chars() {
        let build = || match method {
            'o' => coordinate_source::generate(curve),
            'z' => coordinate_source::weighted(),
            _ => panic!("expected o or z"),
        };
        let start = Instant::now();
        let points = black_box(build());
        let initial = start.elapsed().as_nanos();
        let reference: Vec<_> = include_str!("base71-points.csv")
            .lines()
            .map(|row| {
                let (x, y) = row.split_once(',').unwrap();
                (x.parse::<u64>().unwrap(), y.parse::<u64>().unwrap())
            })
            .collect();
        assert_eq!(points.as_slice(), reference);
        let ns = if first {
            initial as f64
        } else {
            let start = Instant::now();
            for _ in 0..256 {
                black_box(build());
            }
            start.elapsed().as_nanos() as f64 / 256.
        };
        println!("{method},{ns:.3}");
    }
}
