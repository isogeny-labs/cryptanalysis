// Generate into key order by placing the low representative first at every fork.
fn inverse_tree<const KEY_ORDER: bool, const PRUNE: bool>(terminal: u64, mask: u128) -> [u64; 128] {
    let mut xs = [0; 128];
    xs[0] = terminal;
    for depth in 0..7 {
        for i in (0..1 << depth).rev() {
            if PRUNE && depth == 6 && (mask >> (2 * i)) & 3 == 0 {
                continue;
            }
            let y = M::pow(M::add(xs[i], 2), 1 << 29);
            let z = M::sub(0, y);
            let pair = if KEY_ORDER {
                [y.min(z), y.max(z)]
            } else {
                [y, z]
            };
            xs[2 * i..2 * i + 2].copy_from_slice(&pair);
        }
    }
    xs
}

fn address_bench(seed: usize, order: &str) {
    let mut rows: Vec<_> = include_str!("fiber-masks.csv")
        .lines()
        .skip(1)
        .map(|row| {
            let mut fields = row.split(',').skip(1);
            (
                fields.next().unwrap().parse::<u64>().unwrap(),
                fields.next().unwrap().parse::<u128>().unwrap(),
            )
        })
        .collect();
    rows.rotate_left(seed % 32);
    let curve = Curve::<31>::new(2, 14).unwrap();
    let mut expected = Points::new();
    for &(terminal, mask) in &rows {
        let start = expected.len();
        for (i, x) in inverse_tree::<true, false>(terminal, mask)
            .into_iter()
            .enumerate()
        {
            assert_eq!(iterate(x, 7), terminal);
            assert_eq!(branch_key(x) as usize, i);
            let pt = curve.lift_x(x).unwrap();
            assert_eq!(pt.is_some(), mask >> i & 1 == 1);
            if let Some(q) = pt {
                expected.push((x, q.y()));
            }
        }
        expected[start..].sort_unstable();
    }
    let mut out = Vec::with_capacity(4096);
    for method in order.chars() {
        let mut run = || {
            out.clear();
            for &(terminal, mut mask) in black_box(&rows) {
                let start = out.len();
                match method {
                    'd' => lift_list(&inverse_tree::<false, false>(terminal, mask), &mut out),
                    'a' => lift_list(&inverse_tree::<true, false>(terminal, mask), &mut out),
                    'e' | 's' => {
                        let xs = if method == 's' {
                            inverse_tree::<true, true>(terminal, mask)
                        } else {
                            inverse_tree::<true, false>(terminal, mask)
                        };
                        let mut kept = [0; 128];
                        let mut n = 0;
                        while mask != 0 {
                            kept[n] = xs[mask.trailing_zeros() as usize];
                            mask &= mask - 1;
                            n += 1;
                        }
                        lift_list(&kept[..n], &mut out);
                    }
                    _ => panic!("unknown method"),
                }
                out[start..].sort_unstable();
            }
            black_box(out.as_slice());
        };
        run();
        let start = Instant::now();
        for _ in 0..32 {
            run();
        }
        let ns = start.elapsed().as_nanos() as f64 / 32.;
        assert_eq!(out, expected);
        println!("{method},{ns:.3}");
    }
}
