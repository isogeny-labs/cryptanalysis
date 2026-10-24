//! Streebog (GOST R 34.11-2012) with conventional byte-oriented API order.
//!
//! The previous local compression implementation disagreed with independent
//! byte-oriented test vectors. RFC 6986 displays bit strings most-significant
//! first; its M1 bytes and result are reversed to compare with the API here.
//! Use RustCrypto's implementation and keep this module's public API.

use streebog::{Digest, Streebog256, Streebog512};

#[derive(Clone, Debug)]
enum Variant {
    Bits256(Streebog256),
    Bits512(Streebog512),
}

#[derive(Clone, Debug)]
pub struct Streebog {
    variant: Variant,
}

impl Streebog {
    pub fn new_256() -> Self {
        Self {
            variant: Variant::Bits256(Streebog256::new()),
        }
    }

    pub fn new_512() -> Self {
        Self {
            variant: Variant::Bits512(Streebog512::new()),
        }
    }

    pub fn update(&mut self, data: &[u8]) {
        match &mut self.variant {
            Variant::Bits256(h) => h.update(data),
            Variant::Bits512(h) => h.update(data),
        }
    }

    pub fn finalize(self) -> Vec<u8> {
        match self.variant {
            Variant::Bits256(h) => h.finalize().to_vec(),
            Variant::Bits512(h) => h.finalize().to_vec(),
        }
    }
}

pub fn streebog_256(data: &[u8]) -> [u8; 32] {
    let mut h = Streebog::new_256();
    h.update(data);
    h.finalize().try_into().expect("fixed 256-bit digest")
}

pub fn streebog_512(data: &[u8]) -> [u8; 64] {
    let mut h = Streebog::new_512();
    h.update(data);
    h.finalize().try_into().expect("fixed 512-bit digest")
}

#[cfg(test)]
mod tests {
    use super::*;

    // RFC 6986, Sections 10.1.1 and 10.1.2, message M1. Its display order
    // is reversed for the conventional byte-oriented digest interface.
    const M1: &str = concat!(
        "32313039383736353433323130393837",
        "36353433323130393837363534333231",
        "30393837363534333231303938373635",
        "343332313039383736353433323130",
    );

    #[test]
    fn rfc6986_m1_vectors() {
        let msg: Vec<u8> = hex::decode(M1).unwrap().into_iter().rev().collect();
        let expected_512: Vec<u8> = hex::decode(concat!(
            "486f64c1917879417fef082b3381a4e211c324f074654c38823a7b76f830ad00",
            "fa1fbae42b1285c0352f227524bc9ab16254288dd6863dccd5b9f54a1ad0541b"
        ))
        .unwrap()
        .into_iter()
        .rev()
        .collect();
        let expected_256: Vec<u8> =
            hex::decode("00557be5e584fd52a449b16b0251d05d27f94ab76cbaa6da890b59d8ef1e159d")
                .unwrap()
                .into_iter()
                .rev()
                .collect();
        assert_eq!(streebog_512(&msg).as_slice(), expected_512);
        assert_eq!(streebog_256(&msg).as_slice(), expected_256);
    }

    #[test]
    fn streaming_matches_one_shot_at_block_boundaries() {
        for size in [0, 1, 63, 64, 65, 127, 128, 129, 4097] {
            let bytes: Vec<u8> = (0..size).map(|i| (i * 37) as u8).collect();
            for chunk_size in [1, 3, 63, 64, 65, 257] {
                let mut h256 = Streebog::new_256();
                let mut h512 = Streebog::new_512();
                for chunk in bytes.chunks(chunk_size) {
                    h256.update(chunk);
                    h512.update(chunk);
                }
                assert_eq!(
                    h256.finalize(),
                    streebog_256(&bytes),
                    "256/{size}/{chunk_size}"
                );
                assert_eq!(
                    h512.finalize(),
                    streebog_512(&bytes),
                    "512/{size}/{chunk_size}"
                );
            }
        }
    }
}
