//! **Named-primitive registry** for the auto-attack CLI.
//!
//! Maps short identifiers (`toyspn-2r`, `aes-2r`, `present80-4r`,
//! `speck64-128-6r`, `chacha-w16-8r`, `sha256-16steps`, ...) to a
//! [`Primitive`] of the [`sym_ir`](crate::cryptanalysis::sym_ir) cipher IR, bound to a fixed key as a
//! [`KeyedPrimitive`]. The structural metadata in [`CipherEntry`] (block and
//! key size, kind, S-box, ARX presence) is read off the IR; which techniques
//! apply is decided by
//! [`applicable_techniques`](crate::cryptanalysis::sym_techniques::applicable_techniques),
//! not by a per-name flag.
//!
//! ## Names
//!
//! A base name with an optional `-Nr` (rounds) or `-Nsteps` suffix:
//!
//! | name | primitive |
//! |---|---|
//! | `aes-Nr` (`N` in 1..=10) | AES-128 cut to `N` rounds, last round keeps MixColumns, all-zero key (the historical `ReducedAes128` behaviour) |
//! | `aes128` | FIPS 197 AES-128, 10 rounds, no final MixColumns |
//! | `aes-small-Nr` (1..=15) | small-scale AES `SR(N,2,2,4)` |
//! | `present80`, `present80-Nr` (1..=31) | PRESENT-80; a cut version adds the post-whitening key after round `N` |
//! | `toyspn-Nr`, `toyspn-present-Nr` | 16-bit ToySpn with the Serpent-S0 / PRESENT S-box, master key `0xC0FFEE` |
//! | `speck64-128`, `speck128-128`, `speck128-256` (`-Nr`) | Speck |
//! | `simon64-128`, `simon128-128`, `simon128-256` (`-Nr`) | Simon |
//! | `chacha8`, `chacha12`, `chacha20` | ChaCha block function |
//! | `chacha-w8-Nr`, `chacha-w16-Nr`, `chacha-w32-Nr` | reduced-width ChaCha with `N` single rounds |
//! | `sha256`, `sha256-Nsteps` (1..=64) | SHA-256 compression, first `N` steps; the "key" is the 512-bit message block |
//!
//! A name followed by `-Nr` cuts the primitive's round list to its first `N`
//! rounds when it has more than `N`; for the fixed-round names above the
//! suffix is the only way to ask for a reduced version.
//!
//! Keys are [`default_key`] except where noted (AES: zero key; ToySpn:
//! `0xC0FFEE`), so repeated runs see the same instance.

use crate::cryptanalysis::boomerang::BlockCipher;
use crate::cryptanalysis::sbox::Sbox;
use crate::cryptanalysis::sym_bridge::{default_key, KeyedPrimitive};
use crate::cryptanalysis::sym_ir::primitives::{
    aes128, chacha, present80, sha256_compress, simon, speck, toyspn,
};
use crate::cryptanalysis::sym_ir::{Kind, Layer, Primitive, SboxId};
use crate::cryptanalysis::sym_techniques::ir_facts;

/// Structural metadata of a registered primitive, derived from its IR.
#[derive(Clone, Debug)]
pub struct CipherEntry {
    /// The registered name, normalised (e.g. `"toyspn-2r"`).
    pub name: String,
    /// One-line description generated from the IR.
    pub description: String,
    /// Block size in bytes.
    pub block_bytes: usize,
    /// Block size in bits.
    pub block_bits: usize,
    /// Key size in bits (0 for unkeyed permutations).
    pub key_bits: usize,
    /// Number of rounds in the IR description.
    pub rounds: usize,
    /// Structural family.
    pub kind: Kind,
    /// Whether some round contains an ARX layer.
    pub has_arx: bool,
    /// Common width of the S-box layers, if they all share one.
    pub sbox_width: Option<usize>,
    /// The first S-box of the description, if any.
    pub sbox: Option<Sbox>,
    /// A canonical `(alpha, delta)` pair for differential demos: bit 0 of
    /// byte 0 set.
    pub canonical_alpha: Vec<u8>,
    /// Canonical output difference (same value as `canonical_alpha`).
    pub canonical_delta: Vec<u8>,
}

impl CipherEntry {
    /// Derive the metadata from `p`, labelled `name`.
    pub fn from_primitive(name: &str, p: &Primitive) -> CipherEntry {
        let facts = ir_facts(p);
        let sbox_width = match facts.sbox_widths.as_slice() {
            [w] => Some(*w),
            _ => None,
        };
        let mut unit = vec![0u8; p.block_bytes()];
        unit[0] = 1;
        CipherEntry {
            name: name.to_string(),
            description: format!(
                "{} ({:?}, {}-bit block, {}-bit key, {} rounds{}{})",
                p.name,
                p.kind,
                p.block_bits,
                p.key_bits,
                p.rounds.len(),
                match sbox_width {
                    Some(w) => format!(", {w}-bit S-boxes"),
                    None => String::new(),
                },
                if facts.has_arx { ", ARX" } else { "" },
            ),
            block_bytes: p.block_bytes(),
            block_bits: p.block_bits,
            key_bits: p.key_bits,
            rounds: p.rounds.len(),
            kind: p.kind,
            has_arx: facts.has_arx,
            sbox_width,
            sbox: p.sboxes.first().cloned(),
            canonical_alpha: unit.clone(),
            canonical_delta: unit,
        }
    }
}

fn serpent_s0() -> Sbox {
    Sbox::new(
        4,
        4,
        vec![3, 8, 15, 1, 10, 6, 5, 11, 14, 13, 4, 2, 7, 0, 9, 12],
    )
    .unwrap()
}

fn present_sbox() -> Sbox {
    Sbox::new(
        4,
        4,
        vec![0xC, 5, 6, 0xB, 9, 0, 0xA, 0xD, 3, 0xE, 0xF, 8, 4, 7, 1, 2],
    )
    .unwrap()
}

/// Keep the first `n` rounds of `p`, renaming it `"{name}-{n}r"`. For
/// PRESENT-style descriptions the cut round receives the next round key as
/// post-whitening, so the output is not the raw S-box/pLayer state. Returns
/// `None` if `n` is 0 or exceeds the number of rounds.
fn cut_rounds(mut p: Primitive, n: usize, post_whiten: bool) -> Option<Primitive> {
    if n == 0 || n > p.rounds.len() {
        return None;
    }
    let had = p.rounds.len();
    p.rounds.truncate(n);
    if post_whiten && n < had {
        p.rounds[n - 1].layers.push(Layer::AddRoundKey {
            round_key: n,
            bit_offset: 0,
        });
    }
    p.name = format!("{}-{n}r", p.name);
    Some(p)
}

/// Split `"base-12r"` into `("base", 12, "r")` and `"base-12steps"` into
/// `("base", 12, "steps")`.
fn split_suffix(name: &str) -> Option<(&str, usize, &'static str)> {
    let (base, tail) = name.rsplit_once('-')?;
    for unit in ["steps", "r"] {
        if let Some(num) = tail.strip_suffix(unit) {
            if !num.is_empty() && num.bytes().all(|b| b.is_ascii_digit()) {
                return Some((
                    base,
                    num.parse().ok()?,
                    if unit == "r" { "r" } else { "steps" },
                ));
            }
        }
    }
    None
}

/// Build the [`Primitive`] and key registered under `name`, or `None`.
/// See the [module docs](self) for the grammar.
pub fn primitive_by_name(name: &str) -> Option<(Primitive, Vec<u8>)> {
    let with_default = |p: Primitive| {
        let k = default_key(&p);
        Some((p, k))
    };
    // Fixed names first.
    match name {
        "aes128" => return Some((aes128::aes128(), vec![0u8; 16])),
        "present80" => return with_default(present80::present80()),
        "speck64-128" => return with_default(speck::speck64_128()),
        "speck128-128" => return with_default(speck::speck128_128()),
        "speck128-256" => return with_default(speck::speck128_256()),
        "simon64-128" => return with_default(simon::simon64_128()),
        "simon128-128" => return with_default(simon::simon128_128()),
        "simon128-256" => return with_default(simon::simon128_256()),
        "chacha8" => return with_default(chacha::chacha8()),
        "chacha12" => return with_default(chacha::chacha12()),
        "chacha20" => return with_default(chacha::chacha20()),
        "sha256" => return with_default(sha256_compress::sha256_compress()),
        _ => {}
    }
    let (base, n, unit) = split_suffix(name)?;
    if n == 0 {
        return None;
    }
    if unit == "steps" {
        return (base == "sha256" && n <= 64)
            .then(|| sha256_compress::steps(n))
            .and_then(with_default);
    }
    let toy_key = || 0xC0FFEEu64.to_le_bytes().to_vec();
    match base {
        "aes" if n <= 10 => Some((aes128::reduced(n, true), vec![0u8; 16])),
        "aes-small" if n <= 15 => with_default(aes128::small_scale(n)),
        "toyspn" => Some((toyspn::toyspn(&serpent_s0(), n), toy_key())),
        "toyspn-present" => Some((toyspn::toyspn(&present_sbox(), n), toy_key())),
        "present80" => cut_rounds(present80::present80(), n, true).and_then(with_default),
        "speck64-128" => cut_rounds(speck::speck64_128(), n, false).and_then(with_default),
        "speck128-128" => cut_rounds(speck::speck128_128(), n, false).and_then(with_default),
        "speck128-256" => cut_rounds(speck::speck128_256(), n, false).and_then(with_default),
        "simon64-128" => cut_rounds(simon::simon64_128(), n, false).and_then(with_default),
        "simon128-128" => cut_rounds(simon::simon128_128(), n, false).and_then(with_default),
        "simon128-256" => cut_rounds(simon::simon128_256(), n, false).and_then(with_default),
        "chacha8" | "chacha12" | "chacha20" => {
            let full = match base {
                "chacha8" => chacha::chacha8(),
                "chacha12" => chacha::chacha12(),
                _ => chacha::chacha20(),
            };
            cut_rounds(full, n, false).and_then(with_default)
        }
        "chacha-w8" | "chacha-w16" | "chacha-w32" if n >= 1 => {
            let w: usize = base["chacha-w".len()..].parse().ok()?;
            with_default(chacha::reduced_width(w, n))
        }
        _ => None,
    }
}

/// A registered primitive bound to its key, with derived metadata.
pub struct RegisteredCipher {
    name: String,
    keyed: KeyedPrimitive,
}

impl RegisteredCipher {
    /// Look a primitive up by name; `None` if the name is not recognised.
    pub fn from_name(name: &str) -> Option<Self> {
        let (p, key) = primitive_by_name(name)?;
        Some(RegisteredCipher {
            name: name.to_string(),
            keyed: KeyedPrimitive::new(p, key),
        })
    }

    /// The registered name.
    pub fn name(&self) -> &str {
        &self.name
    }

    /// The IR description.
    pub fn primitive(&self) -> &Primitive {
        self.keyed.primitive()
    }

    /// The keyed oracle.
    pub fn keyed(&self) -> &KeyedPrimitive {
        &self.keyed
    }

    /// Structural metadata derived from the IR.
    pub fn entry(&self) -> CipherEntry {
        CipherEntry::from_primitive(&self.name, self.keyed.primitive())
    }

    /// Encrypt one block.
    pub fn encrypt(&self, block: &[u8]) -> Vec<u8> {
        self.keyed.eval(block)
    }

    /// Decrypt one block. Panics if [`RegisteredCipher::can_decrypt`] is
    /// false.
    pub fn decrypt(&self, block: &[u8]) -> Vec<u8> {
        BlockCipher::decrypt(&self.keyed, block)
    }

    /// Whether a decryption oracle exists for this primitive.
    pub fn can_decrypt(&self) -> bool {
        self.keyed.is_invertible()
    }

    /// The first S-box of the description, if it has one.
    pub fn sbox(&self) -> Option<Sbox> {
        first_sbox(self.keyed.primitive())
    }
}

/// The S-box used by the first S-box layer of `p`'s rounds, if any.
pub fn first_sbox(p: &Primitive) -> Option<Sbox> {
    p.rounds
        .iter()
        .flat_map(|r| &r.layers)
        .find_map(|l| match l {
            Layer::SboxParallel {
                sbox: SboxId(i), ..
            } => Some(p.sboxes[*i].clone()),
            _ => None,
        })
}

/// Lets every generic consumer (`boomerang_distinguisher`,
/// `rectangle_attack`, ...) run on a registered primitive. `decrypt` panics
/// for primitives without a decryption oracle.
impl BlockCipher for RegisteredCipher {
    fn block_bytes(&self) -> usize {
        self.keyed.primitive().block_bytes()
    }
    fn encrypt(&self, block: &[u8]) -> Vec<u8> {
        self.keyed.eval(block)
    }
    fn decrypt(&self, block: &[u8]) -> Vec<u8> {
        BlockCipher::decrypt(&self.keyed, block)
    }
}

/// Construct the AES S-box as an `Sbox` (the standard FIPS-197 table).
pub fn aes_sbox() -> Sbox {
    #[rustfmt::skip]
    let t: Vec<u32> = vec![
        0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
        0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
        0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
        0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
        0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
        0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
        0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
        0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
        0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
        0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
        0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
        0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
        0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
        0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
        0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
        0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
    ];
    Sbox::new(8, 8, t).unwrap()
}

/// Example names, one or more per family, for CLI discovery. Any name
/// accepted by [`primitive_by_name`] (the grammar in the module docs) also
/// works; this list is not exhaustive.
pub fn list_ciphers() -> Vec<&'static str> {
    vec![
        "toyspn-1r",
        "toyspn-2r",
        "toyspn-3r",
        "toyspn-4r",
        "toyspn-present-2r",
        "aes-1r",
        "aes-2r",
        "aes-3r",
        "aes-4r",
        "aes-small-4r",
        "present80-4r",
        "speck64-128-6r",
        "simon64-128-8r",
        "chacha-w16-4r",
        "chacha8",
        "sha256-8steps",
    ]
}

// ── Tests ────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::aes::reduced::ReducedAes128;
    use crate::cryptanalysis::boomerang::ToySpn;
    use crate::cryptanalysis::sym_ir::eval;
    use crate::symmetric::{present, simon as simon_ref, speck as speck_ref};

    /// Every name in the grammar resolves, validates and evaluates.
    #[test]
    fn registry_resolves_every_family() {
        let mut names: Vec<String> = Vec::new();
        for n in 1..=10 {
            names.push(format!("aes-{n}r"));
        }
        for n in 1..=15 {
            names.push(format!("aes-small-{n}r"));
        }
        for n in [1, 5, 31] {
            names.push(format!("present80-{n}r"));
        }
        for b in [
            "speck64-128",
            "speck128-128",
            "speck128-256",
            "simon64-128",
            "simon128-128",
            "simon128-256",
        ] {
            names.push(b.to_string());
            names.push(format!("{b}-3r"));
        }
        for b in ["chacha8", "chacha12", "chacha20"] {
            names.push(b.to_string());
            names.push(format!("{b}-4r"));
        }
        for w in [8, 16, 32] {
            names.push(format!("chacha-w{w}-6r"));
        }
        for n in [1, 16, 64] {
            names.push(format!("sha256-{n}steps"));
        }
        names.extend(
            [
                "aes128",
                "present80",
                "sha256",
                "toyspn-5r",
                "toyspn-present-1r",
            ]
            .map(String::from),
        );
        names.extend(list_ciphers().into_iter().map(String::from));
        for name in names {
            let (p, key) = primitive_by_name(&name).unwrap_or_else(|| panic!("{name} unresolved"));
            p.validate().unwrap_or_else(|e| panic!("{name}: {e}"));
            let block = vec![0x42u8; p.block_bytes()];
            let out = eval(&p, &key, &block);
            assert_eq!(out.len(), p.block_bytes(), "{name}");
            let e = CipherEntry::from_primitive(&name, &p);
            assert_eq!(e.block_bits, p.block_bits);
        }
    }

    #[test]
    fn unknown_or_out_of_range_names_return_none() {
        for n in [
            "not-a-cipher",
            "aes-0r",
            "aes-11r",
            "aes-small-16r",
            "present80-32r",
            "toyspn-0r",
            "speck64-128-28r",
            "sha256-65steps",
            "chacha-w64-4r",
            "aes-r",
            "aes-2x",
        ] {
            assert!(RegisteredCipher::from_name(n).is_none(), "{n}");
        }
    }

    /// `eval` through the registry equals the independent implementation.
    #[test]
    fn registry_eval_matches_symmetric_implementations() {
        // Old-registry behaviour: ReducedAes128 with a zero key, MixColumns kept.
        for n in 1..=4 {
            let c = RegisteredCipher::from_name(&format!("aes-{n}r")).unwrap();
            let reference = ReducedAes128::new(&[0u8; 16], n, true);
            let pt: Vec<u8> = (0..16).map(|i| (i * 17) as u8).collect();
            assert_eq!(
                c.encrypt(&pt),
                BlockCipher::encrypt(&reference, &pt),
                "aes-{n}r"
            );
        }
        // ToySpn: same instance as the historical registry.
        for n in 1..=4 {
            let c = RegisteredCipher::from_name(&format!("toyspn-{n}r")).unwrap();
            let reference = ToySpn::new(serpent_s0(), n, 0xC0FFEE);
            for x in [0x0000u16, 0x1234, 0xBEEF, 0xFFFF] {
                let b = x.to_le_bytes();
                assert_eq!(c.encrypt(&b), BlockCipher::encrypt(&reference, &b));
            }
        }
        // Full-round PRESENT-80, Speck64/128, Simon64/128 against symmetric/.
        let key80 = default_key(&present80::present80());
        let mut b = [0x01u8, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF];
        let c = RegisteredCipher::from_name("present80").unwrap();
        let got = c.encrypt(&b);
        present::Present80::new(key80.as_slice().try_into().unwrap()).encrypt_block(&mut b);
        assert_eq!(got, b.to_vec());
        // The registry's default key goes through the same path for the
        // ARX ciphers.
        let k = default_key(&speck::speck64_128());
        let mut b8 = [9u8, 8, 7, 6, 5, 4, 3, 2];
        let got = RegisteredCipher::from_name("speck64-128")
            .unwrap()
            .encrypt(&b8);
        speck_ref::Speck64_128::new(k.as_slice().try_into().unwrap()).encrypt_block(&mut b8);
        assert_eq!(got, b8.to_vec());
        let k = default_key(&simon::simon64_128());
        let mut b8 = [9u8, 8, 7, 6, 5, 4, 3, 2];
        let got = RegisteredCipher::from_name("simon64-128")
            .unwrap()
            .encrypt(&b8);
        simon_ref::Simon64_128::new(k.as_slice().try_into().unwrap()).encrypt_block(&mut b8);
        assert_eq!(got, b8.to_vec());
    }

    /// Decrypt inverts encrypt wherever a decryption oracle exists.
    #[test]
    fn registered_ciphers_round_trip_when_invertible() {
        for name in list_ciphers() {
            let c = RegisteredCipher::from_name(name).unwrap();
            let p: Vec<u8> = (0..c.entry().block_bytes).map(|i| i as u8).collect();
            let e = c.encrypt(&p);
            assert_eq!(e.len(), p.len());
            if c.can_decrypt() {
                assert_eq!(c.decrypt(&e), p, "round-trip failed for {name}");
            }
        }
        for n in [
            "toyspn-2r",
            "aes-2r",
            "present80-4r",
            "speck64-128-6r",
            "simon64-128-8r",
        ] {
            assert!(RegisteredCipher::from_name(n).unwrap().can_decrypt(), "{n}");
        }
        for n in ["chacha8", "sha256-8steps"] {
            assert!(
                !RegisteredCipher::from_name(n).unwrap().can_decrypt(),
                "{n}"
            );
        }
    }

    /// The metadata is read off the IR.
    #[test]
    fn entry_metadata_comes_from_the_ir() {
        let e = RegisteredCipher::from_name("toyspn-2r").unwrap().entry();
        assert_eq!((e.block_bits, e.key_bits, e.sbox_width), (16, 64, Some(4)));
        assert_eq!(e.kind, Kind::Spn);
        assert!(!e.has_arx && e.sbox.is_some());
        let e = RegisteredCipher::from_name("aes-2r").unwrap().entry();
        assert_eq!((e.block_bits, e.sbox_width), (128, Some(8)));
        let e = RegisteredCipher::from_name("speck64-128-6r")
            .unwrap()
            .entry();
        assert!(e.has_arx && e.sbox.is_none() && e.rounds == 6);
    }

    /// The AES S-box helper returns the canonical FIPS-197 table.
    #[test]
    fn aes_sbox_helper_matches_fips197() {
        let s = aes_sbox();
        assert_eq!(s.lookup(0), 0x63);
        assert_eq!(s.lookup(0x53), 0xed);
        assert!(s.is_bijective());
        assert_eq!(
            RegisteredCipher::from_name("aes-2r")
                .unwrap()
                .sbox()
                .unwrap()
                .lookup(0x53),
            0xed
        );
    }
}
