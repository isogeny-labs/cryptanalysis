pub fn add(a: u8, b: u8) -> u8 {
    (a + b) % 7
}
pub fn mul(a: u8, b: u8) -> u8 {
    (a * b) % 7
}
pub fn sub(a: u8, b: u8) -> u8 {
    add(a, mul(6, b))
}
pub fn inv(a: u8) -> u8 {
    assert!(a > 0 && a < 7);
    (0..5).fold(1, |b, _| mul(b, a))
}
