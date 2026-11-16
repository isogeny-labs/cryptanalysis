fn vs(s: u64) -> Vec<u8> {
    (0..64).filter(|&i| s & (1u64 << i) != 0).collect()
}
fn bits(v: &[u8]) -> u64 {
    v.iter().fold(0, |s, &v| s | (1u64 << v))
}
fn pairing(a: u8, b: u8) -> u32 {
    ((((a & 0x15) << 1) | ((a & 0x2a) >> 1)) & b).count_ones() & 1
}
fn frob(x: u8) -> u8 {
    ((x << 2) & 63) | (x >> 4)
}
fn span(g: [u8; 3]) -> u64 {
    bits(
        &(0..8)
            .map(|v| {
                g.iter().enumerate().fold(0, |out, (i, &b)| {
                    out ^ if v & (1 << i) != 0 { b } else { 0 }
                })
            })
            .collect::<Vec<_>>(),
    )
}
fn rank(v: &[u8]) -> u32 {
    let mut basis = [0u8; 6];
    let mut r = 0;
    for &x in v {
        let mut x = x;
        for bit in (0..6).rev() {
            if x & (1 << bit) != 0 {
                if basis[bit] != 0 {
                    x ^= basis[bit];
                } else {
                    basis[bit] = x;
                    r += 1;
                    break;
                }
            }
        }
    }
    r
}
fn dimension(s: u64) -> u32 {
    let v = vs(s);
    assert!(v.contains(&0));
    assert!(v.len().is_power_of_two());
    for &a in &v {
        for &b in &v {
            assert!(v.contains(&(a ^ b)));
            assert_eq!(pairing(a, b), 0);
        }
    }
    let d = (v.len() as u32).trailing_zeros();
    assert_eq!(d, rank(&v));
    d
}
