#[cfg(all(target_arch = "aarch64", target_feature = "neon"))]
fn dual_bench(t: u64, order: &str, expected_base: &Points) {
    let twist_curve = Curve::<31>::new(2, M::P - 14).unwrap();
    let mut expected_twist = Points::new();
    for x in inverse_tree::<false, false>(t, 0) {
        if let Some(q) = twist_curve.lift_x(x).unwrap() {
            expected_twist.push((x, q.y()));
        }
    }
    expected_twist.sort_unstable();
    let mut base = Points::with_capacity(128);
    let mut twist = Points::with_capacity(128);
    for method in order.chars() {
        let mut run = || {
            base.clear();
            twist.clear();
            let xs = half_fiber_root::<4, 7>(black_box(t));
            match method {
                'x' => neon_lift::dual_routes::<true>(&xs, 14, &mut base, &mut twist),
                'y' => neon_lift::dual_routes::<false>(&xs, 14, &mut base, &mut twist),
                'u' => neon_lift::dual_ordered::<true>(&xs, 14, &mut base, &mut twist),
                'v' => neon_lift::dual_ordered::<false>(&xs, 14, &mut base, &mut twist),
                'i' => {
                    neon_lift::packed_lift::<16, false>(&xs, 14, &mut base);
                    neon_lift::packed_lift::<16, false>(&xs, M::P - 14, &mut twist);
                }
                'j' => neon_lift::dual_packed::<16, false>(&xs, 14, &mut base, &mut twist),
                'k' => neon_lift::dual_packed::<16, true>(&xs, 14, &mut base, &mut twist),
                _ => unreachable!(),
            }
            black_box((base.as_slice(), twist.as_slice()));
        };
        run();
        let start = Instant::now();
        for _ in 0..256 {
            run();
        }
        let ns = start.elapsed().as_nanos() as f64 / 256.;
        assert_eq!(&base, expected_base);
        assert_eq!(twist, expected_twist);
        println!("{method},{},{},{ns:.3}", base.len(), twist.len());
    }
}

#[cfg(all(target_arch = "aarch64", target_feature = "neon"))]
fn stream_bench(terminals: &[u64], order: &str, fourth: bool) {
    assert_eq!(terminals.len(), 32);
    let expected: Vec<_> = terminals
        .iter()
        .map(|&t| {
            [14, M::P - 14].map(|b| {
                let curve = Curve::<31>::new(2, b).unwrap();
                let mut table = Points::new();
                for x in inverse_tree::<false, false>(t, 0) {
                    if let Some(q) = curve.lift_x(x).unwrap() {
                        table.push((x, q.y()));
                    }
                }
                table.sort_unstable();
                table
            })
        })
        .collect();
    let mut base = Points::with_capacity(128);
    let mut twist = Points::with_capacity(128);
    for method in order.chars() {
        let mut run = |idx: usize, check: bool| {
            base.clear();
            twist.clear();
            let xs = half_fiber_root::<4, 7>(black_box(terminals[idx]));
            match method {
                'u' => neon_lift::dual_ordered::<true>(&xs, 14, &mut base, &mut twist),
                'x' => neon_lift::dual_routes::<true>(&xs, 14, &mut base, &mut twist),
                'y' => neon_lift::dual_routes::<false>(&xs, 14, &mut base, &mut twist),
                _ => unreachable!(),
            }
            if check {
                assert_eq!(base, expected[idx][0]);
                assert_eq!(twist, expected[idx][1]);
            }
            black_box((base.as_slice(), twist.as_slice()));
        };
        for idx in 0..32 {
            run(idx, true);
        }
        let (stride, shift) = if fourth { (19, 11) } else { (13, 7) };
        let start = Instant::now();
        for pass in 0..8 {
            for i in 0..32 {
                run((stride * i + shift * pass) % 32, false);
            }
        }
        println!("{method},{:.3}", start.elapsed().as_nanos() as f64 / 256.);
    }
}
