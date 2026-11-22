//! Native Rust binary cover-candidate sweeper. No command certifies novelty.

pub mod field;
pub mod journal;
pub mod prior;
pub mod runner;
pub mod search;
pub mod source;
pub mod verify;

use anyhow::Result;
use serde::Serialize;
use sha2::{Digest, Sha256};

pub fn canonical<T: Serialize>(value: &T) -> Result<String> {
    // serde_json's default Map is a BTreeMap: recursively sorted keys, UTF-8,
    // compact separators. Identity records contain only integers and strings.
    Ok(serde_json::to_string(&serde_json::to_value(value)?)?)
}

pub fn digest(bytes: impl AsRef<[u8]>) -> String {
    format!("{:x}", Sha256::digest(bytes.as_ref()))
}

pub fn identifier<T: Serialize>(value: &T) -> Result<String> {
    Ok(digest(canonical(value)?))
}

pub fn engine_fingerprint() -> String {
    digest(concat!(
        include_str!("../Cargo.toml"),
        include_str!("../Cargo.lock"),
        include_str!("lib.rs"),
        include_str!("main.rs"),
        include_str!("field.rs"),
        include_str!("search.rs"),
        include_str!("verify.rs"),
        include_str!("source.rs"),
        include_str!("prior.rs"),
        include_str!("journal.rs"),
        include_str!("runner.rs")
    ))
}
