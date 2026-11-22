//! Small, reusable analysis surface from the crypto repository.
//!
//! Pinned source snapshot from crypto commit e4f200cc2da058492a9a27f348fb88dc23f8a745.
//! `UPSTREAM.sha256` binds the two implementation files.

#[path = "avalanche.rs"]
pub mod avalanche;

#[path = "statistical.rs"]
pub mod statistical;

#[cfg(test)]
mod hash {
    use sha2::{Digest, Sha256};

    pub fn sha256(data: &[u8]) -> [u8; 32] {
        Sha256::digest(data).into()
    }
}
