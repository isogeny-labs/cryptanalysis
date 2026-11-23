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
type M = F<31>;

fn iterate(mut x: u64, n: usize) -> u64 {
    for _ in 0..n {
        x = M::sub(M::sq(x), 2);
    }
    x
}

fn roots() -> [u64; 128] {
    let t = (0..black_box(4096))
        .find(|&v| iterate(v, 30) == M::P - 2)
        .unwrap();
    let step = iterate(t, 24);
    let delta = M::mul(M::sub(M::sq(t), 4), M::sub(M::sq(step), 4));
    let sqrt = M::pow(delta, 1 << 29);
    assert_eq!(M::sq(sqrt), delta);
    let mut xs = [0; 128];
    xs[0] = t;
    xs[1] = M::mul(M::add(M::mul(t, step), sqrt), 1 << 30);
    for i in 2..128 {
        xs[i] = M::sub(M::mul(step, xs[i - 1]), xs[i - 2]);
    }
    xs.sort_unstable();
    let value = iterate(t, 7);
    assert!(xs.windows(2).all(|w| w[0] < w[1]));
    assert!(xs.iter().all(|&x| iterate(x, 7) == value));
    xs
}

type Points = Vec<(u64, u64)>;

fn candidates<const W: usize>(chunk: &[u64], b: u64) -> ([u64; W], [u64; W]) {
    let rhs: [u64; W] = std::array::from_fn(|i| {
        let x = chunk[i];
        M::add(M::add(M::mul(M::sq(x), x), M::add(x, x)), b)
    });
    let mut y = rhs;
    for _ in 0..29 {
        for v in &mut y {
            *v = M::sq(*v);
        }
    }
    (rhs, y)
}

fn on_curve<const W: usize>(xs: &[u64; 128], b: u64) -> Points {
    let mut out = Vec::with_capacity(128);
    for chunk in xs.chunks_exact(W) {
        let (rhs, y) = candidates::<W>(chunk, b);
        for i in 0..W {
            if M::sq(y[i]) == rhs[i] {
                out.push((chunk[i], y[i].min(M::sub(0, y[i]))));
            }
        }
    }
    out
}
fn interleaved<const W: usize>(xs: &[u64; 128]) -> Points {
    on_curve::<W>(xs, 14)
}

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

fn build(width: usize, curve: Curve<31>) -> Vec<(u64, u64)> {
    let xs = roots();
    match width {
        0 => {
            let mut out = Vec::with_capacity(128);
            for x in xs {
                if let Some(q) = curve.lift_x(x).unwrap() {
                    out.push((x, q.y()));
                }
            }
            out
        }
        1 => interleaved::<1>(&xs),
        4 => interleaved::<4>(&xs),
        8 => interleaved::<8>(&xs),
        16 => interleaved::<16>(&xs),
        32 => interleaved::<32>(&xs),
        _ => panic!("unsupported lane count"),
    }
}

fn main() {
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
