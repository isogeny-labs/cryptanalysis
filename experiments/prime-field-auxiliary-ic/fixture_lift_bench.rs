//! Standalone M31 point-lift benchmark. From this directory run
//! rustc --edition=2021 -C opt-level=3 -C target-cpu=native fixture_lift_bench.rs -o /tmp/lift-bench
//! and then /tmp/lift-bench. Rows give ns per 32-coordinate fiber in
//! reference, width 1, width 4, width 8, and width 32 order.
//! Inputs and smaller ordinates come from field31_s5_base0/public.json
//! (SHA256 a5fd508b6deacd2e2036a790946d7700929a822caf92e1fed699e6a7657fb9ca).
//! P marks a coordinate with no lift. Root generation and sorting are excluded.
#![allow(dead_code)]
use std::{hint::black_box, time::Instant};
#[derive(Debug)]
pub enum Error {
    Invalid(&'static str),
}
pub type Result<T> = std::result::Result<T, Error>;
#[path = "../../crates/prime-field-auxiliary-ic/src/field.rs"]
mod field;
use field::Curve;
const P: u32 = 2147483647;
#[inline(always)]
fn reduce(t: u64) -> u32 {
    let v = ((t as u32) & P) + (t >> 31) as u32;
    if v >= P {
        v - P
    } else {
        v
    }
}
#[inline(always)]
fn square(t: u32) -> u32 {
    reduce(t as u64 * t as u64)
}
#[inline(never)]
fn run<const W: usize>(xs: &[u32; 32], out: &mut [u32; 32], curve: Curve<31>) {
    if W == 0 {
        for (a, x) in out.iter_mut().zip(xs) {
            *a = curve.lift_x(*x as u64).unwrap().map_or(P, |q| q.y() as u32);
        }
        return;
    }
    for (coordinates, outputs) in xs.chunks_exact(W).zip(out.chunks_exact_mut(W)) {
        let mut rhs = [0; W];
        for i in 0..W {
            let x = coordinates[i] as u64;
            rhs[i] = reduce(square(coordinates[i]) as u64 * x + 2 * x + 14);
        }
        let mut y = rhs;
        for _ in 0..29 {
            for a in &mut y {
                *a = square(*a);
            }
        }
        for i in 0..W {
            outputs[i] = if square(y[i]) == rhs[i] {
                y[i].min(P - y[i])
            } else {
                P
            };
        }
    }
}
const ROOTS: [u32; 32] = [
    3, 308768278, 1213058799, 1950178058, 1620095117, 1685732321, 845665662, 1760557235,
    1393679185, 536276641, 1896314920, 1171458932, 1533993268, 1528659296, 1851652048, 987367763,
    1431655765, 1908835095, 1857409341, 975624154, 80168778, 1101836261, 985108144, 2084456163,
    753804470, 1900319349, 1900239952, 141165527, 98625645, 1491270739, 2008905047, 1560638367,
];
const EXPECT: [u32; 32] = [
    417540811, 313437383, 461061450, 2147483647, 2147483647, 174410159, 2147483647, 842831714,
    618134602, 19398713, 655567214, 205324396, 2147483647, 2147483647, 2147483647, 2147483647,
    2147483647, 99767383, 2147483647, 502209836, 2147483647, 2147483647, 203353269, 1048614557,
    790950997, 261501473, 1022538104, 2147483647, 439352624, 2147483647, 2147483647, 2147483647,
];
fn main() {
    let c = Curve::new(2, 14).unwrap();
    let paths: [fn(&[u32; 32], &mut [u32; 32], Curve<31>); 5] =
        [run::<0>, run::<1>, run::<4>, run::<8>, run::<32>];
    let mut s = 1u32;
    for k in 0..1001 {
        let mut a = ROOTS;
        if k > 0 {
            for x in &mut a {
                s = s.wrapping_mul(1664525).wrapping_add(1013904223);
                *x = s % P;
            }
            a[0] = 0;
            a[1] = P - 1;
        }
        let mut expected_y = [0; 32];
        paths[0](&a, &mut expected_y, c);
        if k == 0 {
            assert_eq!(expected_y, EXPECT);
        }
        for f in paths {
            let mut out = [0; 32];
            f(&a, &mut out, c);
            assert_eq!(out, expected_y);
        }
    }
    for k in 0..25 {
        let mut times = [0.; 5];
        for t in 0..5 {
            let m = (if k % 2 == 0 { t } else { 4 - t } + k / 2) % 5;
            let mut out = [0; 32];
            let st = Instant::now();
            for _ in 0..2000 {
                paths[m](black_box(&ROOTS), &mut out, c);
                black_box(&out);
            }
            times[m] = st.elapsed().as_secs_f64() * 5e5;
        }
        if k > 0 {
            println!(
                "{} {} {} {} {}",
                times[0], times[1], times[2], times[3], times[4]
            );
        }
    }
}
