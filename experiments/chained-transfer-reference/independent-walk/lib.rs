//! Unchanged pre-existing verifier modules under separate source custody.
//! A dependency crate preserves their original super-module relationships;
//! upstream unit modules remain under Cargo's normal dependency cfg.
#[path = "../../../../crypto/src/cryptanalysis/isogeny_walk/curve.rs"]
pub mod curve;
#[path = "../../../../crypto/src/cryptanalysis/isogeny_walk/field.rs"]
pub mod field;
#[path = "../../../../crypto/src/cryptanalysis/isogeny_walk/kernel.rs"]
pub mod kernel;
#[path = "../../../../crypto/src/cryptanalysis/isogeny_walk/modpoly.rs"]
pub mod modpoly;
#[path = "../../../../crypto/src/cryptanalysis/isogeny_walk/poly.rs"]
pub mod poly;
