fn half_fiber<const W: usize>(terminal: u64) -> [u64; 128] {
    const {
        assert!(W.is_power_of_two() && W <= 32);
    }
    let mut leaf = terminal;
    for _ in 0..7 {
        leaf = M::pow(M::add(leaf, 2), 1 << 29);
    }
    let step = iterate(leaf, 24);
    let delta = M::mul(M::sub(M::sq(leaf), 4), M::sub(M::sq(step), 4));
    let mut xs = [0; 128];
    xs[0] = leaf;
    xs[1] = M::mul(M::add(M::mul(leaf, step), M::pow(delta, 1 << 29)), 1 << 30);
    for i in 2..2 * W {
        xs[i] = M::sub(M::mul(step, xs[i - 1]), xs[i - 2]);
    }
    let stride = iterate(step, W.trailing_zeros() as usize);
    for block in (2 * W..64).step_by(W) {
        for i in block..block + W {
            xs[i] = M::sub(M::mul(stride, xs[i - W]), xs[i - 2 * W]);
        }
    }
    for i in 0..64 {
        xs[i + 64] = M::sub(0, xs[i]);
    }
    xs
}

#[cfg(all(target_arch = "aarch64", target_feature = "neon"))]
fn half_bench(rotation: usize, order: &str, holdout: bool) {
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
    let mut expected = Points::new();
    let curve = Curve::<31>::new(2, 14).unwrap();
    for &t in &terminals {
        let full = recurrence_fiber(t);
        for candidate in [half_fiber::<1>(t), half_fiber::<4>(t), half_fiber::<8>(t)] {
            assert_eq!(candidate, full);
        }
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
        let mut run = || {
            out.clear();
            for &t in black_box(&terminals) {
                let xs = match method {
                    'f' => recurrence_fiber(t),
                    'h' => half_fiber::<1>(t),
                    'q' | 'd' | 'p' | 'c' | 'w' | 's' => half_fiber::<4>(t),
                    'o' => half_fiber::<8>(t),
                    _ => panic!("unknown method"),
                };
                let start = out.len();
                match method {
                    'd' => neon_lift::paired_points::<false, false>(&xs, 14, &mut out),
                    'p' | 'w' => neon_lift::paired_points::<true, false>(&xs, 14, &mut out),
                    'c' => neon_lift::paired_points::<true, true>(&xs, 14, &mut out),
                    _ => out.extend(neon_lift::points::<8>(&xs, 14)),
                }
                if matches!(method, 'w' | 's') {
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
