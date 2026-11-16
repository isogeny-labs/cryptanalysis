//! Static code-generation audit, not a performance measurement.
#[path = "../../suite/src/cryptanalysis/ic_framework/u32_reciprocal.rs"]
mod reducer;

#[no_mangle]
pub fn ic_reciprocal_mul(reducer: reducer::U32Reciprocal, a: u32, b: u32) -> u64 {
    reducer.mul(a, b)
}

#[no_mangle]
pub fn ic_generic_mul(a: u64, b: u64, modulus: u64) -> u64 {
    ((a as u128 * b as u128) % modulus as u128) as u64
}
