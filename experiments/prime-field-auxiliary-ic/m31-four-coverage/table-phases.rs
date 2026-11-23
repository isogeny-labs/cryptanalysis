#[cfg(all(target_arch = "aarch64", target_feature = "neon"))]
fn table_phases<const PROFILE: bool, const ROOT: u8>(
    terminal: u64,
    expected: &Points,
    out: &mut Points,
) {
    let mut phase_ns = [0u128; 3];
    let start = Instant::now();
    for _ in 0..256 {
        out.clear();
        let a = PROFILE.then(Instant::now);
        let xs = half_fiber_root::<4, ROOT>(black_box(terminal));
        let b = PROFILE.then(Instant::now);
        neon_lift::paired_points::<true, false, 1>(&xs, 14, out);
        let c = PROFILE.then(Instant::now);
        neon_lift::sort_words(out);
        black_box(out.as_slice());
        if let (Some(a), Some(b), Some(c)) = (a, b, c) {
            let d = Instant::now();
            phase_ns[0] += (b - a).as_nanos();
            phase_ns[1] += (c - b).as_nanos();
            phase_ns[2] += (d - c).as_nanos();
        }
    }
    let total = start.elapsed().as_nanos() as f64 / 256.;
    assert_eq!(out, expected);
    let [roots, lift, sort] = phase_ns.map(|n| n as f64 / 256.);
    println!(
        "{},{},{total:.3},{roots:.3},{lift:.3},{sort:.3}",
        match (PROFILE, ROOT) {
            (true, 0) => "P",
            (false, 0) => "U",
            (true, _) => "D",
            (false, _) => "E",
        },
        out.len()
    );
}
