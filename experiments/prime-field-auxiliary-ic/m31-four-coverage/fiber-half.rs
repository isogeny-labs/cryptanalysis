const FIXED_STEP: u64 = 1_330_526_061;

// For slots i >= 1, x[i] = weights[i]*x[1] - weights[i-1]*x[0].
const FIXED_WEIGHTS: [u32; 64] = {
    let mut u = [0; 64];
    u[1] = 1;
    let mut i = 2;
    while i < 64 {
        u[i] = ((FIXED_STEP * u[i - 1] as u64 + M::P - u[i - 2] as u64) % M::P) as u32;
        i += 1;
    }
    u
};

const CENTERED_WEIGHTS: [i32; 64] = {
    let mut weights = [0; 64];
    let mut i = 0;
    while i < 64 {
        let x = FIXED_WEIGHTS[i] as i32;
        weights[i] = if x > (M::P / 2) as i32 {
            x - M::P as i32
        } else {
            x
        };
        i += 1;
    }
    weights
};

#[inline(always)]
fn terminal_root<const MODE: u8>(x: u64) -> u64 {
    match MODE {
        0 => M::pow(x, 1 << 29),
        1 => {
            let mut v = x;
            for _ in 0..29 {
                v = M::sq(v);
            }
            v
        }
        2..=7 => {
            let p = M::P as i64;
            let mut v = x as i64;
            for _ in 0..29 {
                let product = v * v;
                v = (product >> 31) + ((product & p) - p);
            }
            (v + ((v >> 63) & p)) as u64
        }
        _ => unreachable!(),
    }
}

fn half_fiber<const W: usize>(terminal: u64) -> [u64; 128] {
    half_fiber_root::<W, 0>(terminal)
}

fn half_fiber_root<const W: usize, const ROOT: u8>(terminal: u64) -> [u64; 128] {
    const {
        assert!(W.is_power_of_two() && W <= 32);
    }
    let mut leaf = terminal;
    for _ in 0..7 {
        leaf = terminal_root::<ROOT>(M::add(leaf, 2));
    }
    // Trace of an order-128 element, shared by all fibers in this panel.
    let step = if ROOT >= 3 {
        FIXED_STEP
    } else {
        iterate(leaf, 24)
    };
    let delta = M::mul(M::sub(M::sq(leaf), 4), M::sub(M::sq(step), 4));
    let mut xs = [0; 128];
    xs[0] = leaf;
    xs[1] = M::mul(
        M::add(M::mul(leaf, step), terminal_root::<ROOT>(delta)),
        1 << 30,
    );
    if ROOT >= 4 {
        let a = xs[0];
        let b = xs[1];
        let centered = |x: u64| {
            if x > M::P / 2 {
                x as i64 - M::P as i64
            } else {
                x as i64
            }
        };
        let ca = centered(a);
        let cb = centered(b);
        for i in 2..64 {
            let u = u64::from(FIXED_WEIGHTS[i]);
            let v = u64::from(FIXED_WEIGHTS[i - 1]);
            xs[i] = if ROOT == 5 {
                let z = (u * b) as i64 - (v * a) as i64;
                let p = M::P as i64;
                let f = (z >> 31) + (z & p);
                let r = (f >> 31) + (f & p);
                if r < 0 {
                    (r + p) as u64
                } else if r >= p {
                    (r - p) as u64
                } else {
                    r as u64
                }
            } else if ROOT == 6 || ROOT == 7 {
                let (cu, cv) = if ROOT == 7 {
                    (
                        i64::from(CENTERED_WEIGHTS[i]),
                        i64::from(CENTERED_WEIGHTS[i - 1]),
                    )
                } else {
                    (centered(u), centered(v))
                };
                let z = cu * cb - cv * ca + ((M::P as i64) << 30);
                let f = ((z as u64) >> 31) + ((z as u64) & M::P);
                if f >= M::P {
                    f - M::P
                } else {
                    f
                }
            } else {
                M::sub(M::mul(u, b), M::mul(v, a))
            };
        }
    } else {
        for i in 2..2 * W {
            xs[i] = M::sub(M::mul(step, xs[i - 1]), xs[i - 2]);
        }
        let stride = iterate(step, W.trailing_zeros() as usize);
        for block in (2 * W..64).step_by(W) {
            for i in block..block + W {
                xs[i] = M::sub(M::mul(stride, xs[i - W]), xs[i - 2 * W]);
            }
        }
    }
    for i in 0..64 {
        xs[i + 64] = M::sub(0, xs[i]);
    }
    xs
}

#[cfg(all(target_arch = "aarch64", target_feature = "neon"))]
fn half_bench(rotation: usize, order: &str, holdout: bool, single: bool) {
    let mut terminals: Vec<u64> = include_str!("fiber-masks.csv")
        .lines()
        .skip(1)
        .map(|s| s.split(',').nth(1).unwrap().parse().unwrap())
        .collect();
    if holdout {
        let archived = terminals;
        let first = archived[0];
        let (mut prev, mut curr) = (2, first);
        terminals = Vec::with_capacity(32);
        for power in 1..=127 {
            if power >= 65 && power % 2 == 1 {
                assert!(!archived.contains(&curr) && !terminals.contains(&curr));
                terminals.push(curr);
            }
            (prev, curr) = (curr, M::sub(M::mul(first, curr), prev));
        }
    }
    terminals.rotate_left(rotation % 32);
    if single {
        terminals.truncate(1);
    }
    let mut expected = Points::new();
    let curve = Curve::<31>::new(2, 14).unwrap();
    for &t in &terminals {
        let full = recurrence_fiber(t);
        assert_eq!(half_fiber_root::<4, 1>(t), full);
        assert_eq!(half_fiber_root::<4, 2>(t), full);
        for candidate in [half_fiber::<1>(t), half_fiber::<4>(t), half_fiber::<8>(t)] {
            assert_eq!(candidate, full);
        }
        let mut fixed = half_fiber_root::<4, 3>(t);
        let mut baseline = full;
        let mut weighted = half_fiber_root::<4, 4>(t);
        assert_eq!(half_fiber_root::<4, 5>(t), weighted);
        assert_eq!(half_fiber_root::<4, 6>(t), weighted);
        assert_eq!(half_fiber_root::<4, 7>(t), weighted);
        weighted.sort_unstable();
        fixed.sort_unstable();
        baseline.sort_unstable();
        assert_eq!(fixed, baseline);
        assert_eq!(weighted, baseline);
        let start = expected.len();
        for x in inverse_tree::<false, false>(t, 0) {
            if let Some(q) = curve.lift_x(x).unwrap() {
                expected.push((x, q.y()));
            }
        }
        expected[start..].sort_unstable();
    }
    let mut out = Points::with_capacity(4096);
    for method in order.chars() {
        if matches!(
            method,
            'P' | 'U' | 'D' | 'E' | 'G' | 'H' | '1' | '2' | '3' | '4'
        ) {
            assert!(single, "phase profile requires one terminal");
            match method {
                '1' => table_phases::<true, 4>(terminals[0], &expected, &mut out),
                '2' => table_phases::<false, 4>(terminals[0], &expected, &mut out),
                '3' => table_phases::<true, 7>(terminals[0], &expected, &mut out),
                '4' => table_phases::<false, 7>(terminals[0], &expected, &mut out),
                'P' => table_phases::<true, 0>(terminals[0], &expected, &mut out),
                'U' => table_phases::<false, 0>(terminals[0], &expected, &mut out),
                'D' => table_phases::<true, 2>(terminals[0], &expected, &mut out),
                'G' => table_phases::<true, 3>(terminals[0], &expected, &mut out),
                'H' => table_phases::<false, 3>(terminals[0], &expected, &mut out),
                'E' => table_phases::<false, 2>(terminals[0], &expected, &mut out),
                _ => unreachable!(),
            }
            continue;
        }
        let mut run = || {
            out.clear();
            for &t in black_box(&terminals) {
                let xs = match method {
                    'A' => half_fiber_root::<4, 1>(t),
                    'K' => half_fiber_root::<4, 5>(t),
                    'L' => half_fiber_root::<4, 6>(t),
                    'J' => half_fiber_root::<4, 4>(t),
                    'F' => half_fiber_root::<4, 3>(t),
                    'B' => half_fiber_root::<4, 2>(t),
                    't' => inverse_tree::<false, false>(t, 0),
                    'f' => recurrence_fiber(t),
                    'h' => half_fiber::<1>(t),
                    'q' | 'd' | 'p' | 'c' | 'w' | 's' | 'z' | 'n' => half_fiber::<4>(t),
                    'o' => half_fiber::<8>(t),
                    _ => panic!("unknown method"),
                };
                let start = out.len();
                match method {
                    't' => lift_list(&xs, &mut out),
                    'd' => neon_lift::paired_points::<false, false, 0>(&xs, 14, &mut out),
                    'p' | 'w' => neon_lift::paired_points::<true, false, 0>(&xs, 14, &mut out),
                    'n' => neon_lift::paired_points::<true, false, 2>(&xs, 14, &mut out),
                    'z' | 'A' | 'B' | 'F' | 'J' | 'K' | 'L' => {
                        neon_lift::paired_points::<true, false, 1>(&xs, 14, &mut out)
                    }
                    'c' => neon_lift::paired_points::<true, true, 0>(&xs, 14, &mut out),
                    _ => out.extend(neon_lift::points::<8>(&xs, 14)),
                }
                if matches!(
                    method,
                    'w' | 's' | 'z' | 'n' | 'A' | 'B' | 'F' | 'J' | 'K' | 'L'
                ) {
                    neon_lift::sort_words(&mut out[start..]);
                } else {
                    out[start..].sort_unstable();
                }
            }
            black_box(out.as_slice());
        };
        run();
        let start = Instant::now();
        for _ in 0..64 {
            run();
        }
        let ns = start.elapsed().as_nanos() as f64 / 64.;
        assert_eq!(out, expected);
        println!("{method},{ns:.3}");
    }
}
