// The terminal is the only input. Recover one leaf, then traverse its
// fiber using the same trace recurrence as the single-fiber roots() builder.
fn recurrence_fiber(terminal: u64) -> [u64; 128] {
    let mut leaf = terminal;
    for _ in 0..7 {
        leaf = M::pow(M::add(leaf, 2), 1 << 29);
    }
    let step = iterate(leaf, 24);
    let delta = M::mul(M::sub(M::sq(leaf), 4), M::sub(M::sq(step), 4));
    let mut xs = [0; 128];
    xs[0] = leaf;
    xs[1] = M::mul(M::add(M::mul(leaf, step), M::pow(delta, 1 << 29)), 1 << 30);
    for i in 2..128 {
        xs[i] = M::sub(M::mul(step, xs[i - 1]), xs[i - 2]);
    }
    xs
}

// A request returns an owned, sorted point sequence in caller-provided storage.
// A cache can retain state between requests within one timed campaign.
fn cache_campaign(
    terminals: &[u64],
    method: char,
    requests: usize,
    out: &mut Points,
    inspect: &mut impl FnMut(&Points),
) {
    let mut masks = [0u128; 32];
    let mut saved = Vec::new();
    for request in 0..requests {
        out.clear();
        if matches!(method, 'c' | 'C') && request > 0 {
            out.extend_from_slice(black_box(saved.as_slice()));
        } else {
            for (row, &terminal) in black_box(terminals).iter().enumerate() {
                let start = out.len();
                if matches!(method, 'v' | 'C') {
                    #[cfg(all(target_arch = "aarch64", target_feature = "neon"))]
                    out.extend(neon_lift::points::<8>(&recurrence_fiber(terminal), 14));
                    #[cfg(not(all(target_arch = "aarch64", target_feature = "neon")))]
                    panic!("native recurrence mode requires NEON");
                } else if method == 'r' {
                    lift_list(&recurrence_fiber(terminal), out);
                } else if method != 'm' {
                    lift_list(&inverse_tree::<false, false>(terminal, 0), out);
                } else if request == 0 {
                    let xs = inverse_tree::<true, false>(terminal, 0);
                    for (j, block) in xs.chunks_exact(8).enumerate() {
                        let (rhs, y) = candidates::<8>(block, 14);
                        for i in 0..8 {
                            if M::sq(y[i]) == rhs[i] {
                                masks[row] |= 1u128 << (8 * j + i);
                                out.push((block[i], y[i].min(M::sub(0, y[i]))));
                            }
                        }
                    }
                } else {
                    let mut mask = masks[row];
                    let xs = inverse_tree::<true, true>(terminal, mask);
                    let mut kept = [0; 128];
                    let mut n = 0;
                    while mask != 0 {
                        kept[n] = xs[mask.trailing_zeros() as usize];
                        mask &= mask - 1;
                        n += 1;
                    }
                    lift_list(&kept[..n], out);
                }
                out[start..].sort_unstable();
            }
            if matches!(method, 'c' | 'C') {
                saved.extend_from_slice(out);
                black_box(&saved);
            }
        }
        inspect(out);
    }
}

fn cache_bench(rotation: usize, requests: usize, order: &str) {
    let mut terminals: Vec<u64> = include_str!("fiber-masks.csv")
        .lines()
        .skip(1)
        .map(|s| s.split(',').nth(1).unwrap().parse().unwrap())
        .collect();
    terminals.rotate_left(rotation % 32);
    let curve = Curve::<31>::new(2, 14).unwrap();
    let mut expected = Points::new();
    for &t in &terminals {
        let start = expected.len();
        let mut original = inverse_tree::<false, false>(t, 0);
        let mut recurrence = recurrence_fiber(t);
        original.sort_unstable();
        recurrence.sort_unstable();
        assert_eq!(original, recurrence);
        for x in original {
            if let Some(pt) = curve.lift_x(x).unwrap() {
                expected.push((x, pt.y()));
            }
        }
        expected[start..].sort_unstable();
    }
    assert_eq!(expected.len(), 2063);
    let mut out = Points::with_capacity(4096);
    for method in order.chars() {
        assert!(matches!(method, 'c' | 'd' | 'm' | 'r' | 'v' | 'C'));
        cache_campaign(&terminals, method, requests, &mut out, &mut |v| {
            assert_eq!(v, &expected)
        });
        let start = Instant::now();
        for _ in 0..8 {
            cache_campaign(&terminals, method, requests, &mut out, &mut |v| {
                black_box(v.as_slice());
            });
        }
        println!("{method},{:.3}", start.elapsed().as_nanos() as f64 / 8.);
    }
}
