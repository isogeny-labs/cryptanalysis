// Scalar remainder arithmetic is independent of the Mersenne reductions under test.
#[cfg(all(target_arch = "aarch64", target_feature = "neon"))]
fn check_packed_lift() {
    let p = M::P;
    let mut seed = 0x63a5_1ef9_a87b_u64;
    let mut accepted = 0;
    let mut zero_roots = 0;
    for panel in 0..256 {
        let mut xs = [0; 128];
        for i in 0..64 {
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            xs[i] = if panel < 4 {
                0
            } else if i % 8 == 0 {
                1
            } else {
                seed % p
            };
            xs[64 + i] = (p - xs[i]) % p;
        }
        let b = match panel {
            0 => 0,
            1 => 1,
            2 => p - 1,
            3 => (p / 2) * (p / 2) % p,
            _ => seed % p,
        };
        let mut expected = vec![(p, p)]; // Existing caller output must survive each append.
        for &x in &xs {
            let rhs = ((x * x % p) * x + 2 * x + b) % p;
            let mut y = rhs;
            for _ in 0..29 {
                y = y * y % p;
            }
            if y * y % p == rhs {
                expected.push((x, y.min((p - y) % p)));
                zero_roots += usize::from(y == 0);
            }
        }
        expected[1..].sort_unstable();
        accepted += expected.len() - 1;
        if panel < 4 {
            match panel {
                2 => assert_eq!(expected.len(), 1),
                _ => assert_eq!(expected.len(), 129),
            }
        }
        fn compare<const V: usize, const ALWAYS: bool>(xs: &[u64; 128], b: u64, expected: &Points) {
            let mut got = vec![(M::P, M::P)];
            neon_lift::packed_lift::<V, ALWAYS>(xs, b, &mut got);
            assert_eq!(&got, expected);
        }
        compare::<4, false>(&xs, b, &expected);
        compare::<8, false>(&xs, b, &expected);
        compare::<16, false>(&xs, b, &expected);
        compare::<32, false>(&xs, b, &expected);
        compare::<8, true>(&xs, b, &expected);
    }
    println!("256 panels, 32768 slots, {accepted} accepted, {zero_roots} zero ordinates, 5 implementations");
}
