//! Small native check target compiling the actual library modules in place.
//! This also works in a sparse checkout without unrelated research fixtures.
#[path = "../../../src/binary_ecc/curve.rs"]
pub mod curve;
#[path = "../../../src/binary_ecc/efd/mod.rs"]
pub mod efd;
#[path = "../../../src/binary_ecc/f2m.rs"]
pub mod f2m;

#[cfg(test)]
pub mod hash {
    pub mod sha256 {
        use sha2::{Digest, Sha256};
        pub fn sha256(data: &[u8]) -> [u8; 32] {
            Sha256::digest(data).into()
        }
    }
}
