// Each invocation starts with the same canonical x keys and prepared left operands.
fn charge_setup(curve: Curve<31>, keys: &[u32; 71], cases: &[Option<Point>]) -> usize {
    let reps: [Point; 71] =
        std::array::from_fn(|i| curve.lift_x(u64::from(keys[i])).unwrap().unwrap());
    let mut output = vec![None; 142];
    let mut hits = 0;
    #[cfg(signed_pairs)]
    {
        let table = black_box(membership::build(keys));
        let reps = black_box(reps);
        for &p in cases {
            field::signed_batch(curve, p, &reps, &mut output);
            hits += black_box(&output)
                .iter()
                .flatten()
                .filter(|q| membership::lookup(&table, keys, q.x() as u32))
                .count();
        }
    }
    #[cfg(not(signed_pairs))]
    {
        let right: [Option<Point>; 142] = black_box(std::array::from_fn(|i| {
            let q = reps[i / 2];
            if i % 2 == 0 {
                Some(q)
            } else {
                Some(curve.neg_inner(q))
            }
        }));
        let mut scratch = BatchScratch::default();
        for &p in cases {
            output.fill(p);
            curve.batch_add_inner(&mut output, &right, &mut scratch);
            hits += black_box(&output)
                .iter()
                .flatten()
                .filter(|q| keys.binary_search(&(q.x() as u32)).is_ok())
                .count();
        }
    }
    black_box(output);
    hits
}

fn setup_panel(curve: Curve<31>, path: &str, seed: u64) {
    let keys: [u32; 71] = std::fs::read_to_string(path)
        .unwrap()
        .lines()
        .map(|s| s.parse().unwrap())
        .collect::<Vec<_>>()
        .try_into()
        .unwrap();
    let reps = keys.map(|x| curve.lift_x(u64::from(x)).unwrap().unwrap());
    let mut state = 0x2718281828459045 ^ seed;
    for positive in [false, true] {
        let cases: Vec<_> = (0..256)
            .map(|i| {
                if positive && i % 8 == 0 {
                    curve
                        .add(
                            Some(reps[(i + seed as usize) % 71]),
                            Some(reps[(i + seed as usize + 11) % 71]),
                        )
                        .unwrap()
                } else {
                    sample_point(curve, &mut state)
                }
            })
            .collect();
        let oracle: Vec<usize> = cases
            .iter()
            .map(|&p| {
                reps.iter()
                    .flat_map(|&q| [q, curve.negate(q).unwrap()])
                    .filter_map(|q| curve.add(p, Some(q)).unwrap())
                    .filter(|q| keys.binary_search(&(q.x() as u32)).is_ok())
                    .count()
            })
            .collect();
        let mut widths = [0, 1, 4, 16, 64, 256];
        widths.rotate_left(seed as usize % 6);
        for n in widths {
            let expected: usize = oracle[..n].iter().sum();
            if positive && n > 0 {
                assert!(expected >= 2 * n.div_ceil(8));
            }
            let repetitions = 4096 / (n + 16);
            let start = Instant::now();
            let mut hits = 0;
            for _ in 0..repetitions {
                hits += black_box(charge_setup(
                    curve,
                    black_box(&keys),
                    black_box(&cases[..n]),
                ));
            }
            let ns = start.elapsed().as_nanos() as f64 / repetitions as f64;
            assert_eq!(hits, repetitions * expected);
            println!("{seed},{positive},{n},{expected},{ns:.3}");
        }
    }
}
