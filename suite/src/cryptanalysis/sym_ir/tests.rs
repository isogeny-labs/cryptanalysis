//! IR-fidelity regression gate (plan section 4.2): `eval` of every
//! description in [`super::primitives`] must agree bit-for-bit with the
//! existing implementation on its known-answer vectors and on 1,000 seeded
//! random (key, block) pairs. Nothing here is a claim about security.

use super::primitives::{aes128, chacha, present80, sha256_compress, simon, speck, toyspn};
use super::{eval, eval_rounds, expand_key, Primitive};
use crate::cryptanalysis::aes::reduced::ReducedAes128;
use crate::cryptanalysis::aes::small_scale::SmallAes;
use crate::cryptanalysis::boomerang::ToySpn;
use crate::cryptanalysis::sbox::Sbox;
use crate::hash::sha256 as sha;
use crate::symmetric::{aes, chacha20, present, simon as simon_ref, speck as speck_ref};
use rand::rngs::SmallRng;
use rand::{Rng, SeedableRng};

const RANDOM_PAIRS: usize = 1000;

fn rng(tag: u64) -> SmallRng {
    SmallRng::seed_from_u64(0x5917_1A00_0000_0000 ^ tag)
}

fn rand_bytes<const N: usize>(r: &mut SmallRng) -> [u8; N] {
    let mut b = [0u8; N];
    r.fill(&mut b[..]);
    b
}

fn h(s: &str) -> Vec<u8> {
    hex::decode(s).unwrap()
}

// ── structural sanity ───────────────────────────────────────────────────

fn present_sbox() -> Sbox {
    Sbox::new(
        4,
        4,
        vec![0xC, 5, 6, 0xB, 9, 0, 0xA, 0xD, 3, 0xE, 0xF, 8, 4, 7, 1, 2],
    )
    .unwrap()
}

fn serpent_s0() -> Sbox {
    Sbox::new(
        4,
        4,
        vec![3, 8, 15, 1, 10, 6, 5, 11, 14, 13, 4, 2, 7, 0, 9, 12],
    )
    .unwrap()
}

#[test]
fn every_description_validates() {
    let mut all: Vec<Primitive> = vec![
        aes128::aes128(),
        aes128::reduced(4, true),
        aes128::small_scale(4),
        present80::present80(),
        toyspn::toyspn(&serpent_s0(), 4),
        speck::speck64_128(),
        speck::speck128_128(),
        speck::speck128_256(),
        simon::simon64_128(),
        simon::simon128_128(),
        simon::simon128_256(),
        chacha::chacha20(),
        chacha::chacha(7),
        chacha::reduced_width(16, 8),
        chacha::reduced_width(8, 8),
        sha256_compress::sha256_compress(),
        sha256_compress::steps(20),
    ];
    for nr in 1..=10 {
        all.push(aes128::reduced(nr, false));
    }
    for p in &all {
        p.validate().unwrap_or_else(|e| panic!("{}: {e}", p.name));
    }
}

#[test]
fn key_schedule_round_key_counts() {
    assert_eq!(expand_key(&aes128::aes128(), &[0u8; 16]).len(), 11);
    assert_eq!(expand_key(&present80::present80(), &[0u8; 10]).len(), 32);
    assert_eq!(expand_key(&speck::speck64_128(), &[0u8; 16]).len(), 27);
    assert_eq!(expand_key(&simon::simon64_128(), &[0u8; 16]).len(), 44);
    assert_eq!(
        expand_key(&sha256_compress::steps(64), &[0u8; 64]).len(),
        64
    );
    assert_eq!(expand_key(&chacha::chacha20(), &[]).len(), 0);
}

// ── AES-128 ─────────────────────────────────────────────────────────────

#[test]
fn aes128_fips197_vectors() {
    let p = aes128::aes128();
    // Appendix B
    assert_eq!(
        eval(
            &p,
            &h("2b7e151628aed2a6abf7158809cf4f3c"),
            &h("3243f6a8885a308d313198a2e0370734")
        ),
        h("3925841d02dc09fbdc118597196a0b32")
    );
    // Appendix C.1
    assert_eq!(
        eval(
            &p,
            &h("000102030405060708090a0b0c0d0e0f"),
            &h("00112233445566778899aabbccddeeff")
        ),
        h("69c4e0d86a7b0430d8cdb78070b4c55a")
    );
}

#[test]
fn aes128_matches_symmetric_aes_random() {
    let p = aes128::aes128();
    let mut r = rng(1);
    for _ in 0..RANDOM_PAIRS {
        let key: [u8; 16] = rand_bytes(&mut r);
        let pt: [u8; 16] = rand_bytes(&mut r);
        let want = aes::encrypt_block(&pt, &aes::AesKey::Aes128(key));
        assert_eq!(eval(&p, &key, &pt), want);
    }
}

#[test]
fn aes128_round_keys_match_reference_schedule() {
    let mut r = rng(2);
    let key: [u8; 16] = rand_bytes(&mut r);
    let reference = ReducedAes128::new(&key, 10, false);
    let rks = expand_key(&aes128::aes128(), &key);
    for (i, rk) in rks.iter().enumerate() {
        let want: Vec<u8> = reference.round_key(i).iter().flatten().copied().collect();
        let got = super::Codec::BYTES.decode(rk, 128);
        assert_eq!(got, want, "round key {i}");
    }
}

#[test]
fn reduced_aes_matches_reduced_aes128_all_nr_and_flags() {
    for nr in 1..=10usize {
        for mc in [false, true] {
            let p = aes128::reduced(nr, mc);
            let mut r = rng(0x100 + nr as u64 * 2 + mc as u64);
            for _ in 0..RANDOM_PAIRS {
                let key: [u8; 16] = rand_bytes(&mut r);
                let pt: [u8; 16] = rand_bytes(&mut r);
                let want = ReducedAes128::new(&key, nr, mc).encrypt(&pt);
                assert_eq!(eval(&p, &key, &pt), want, "nr={nr} mc={mc}");
            }
        }
    }
}

#[test]
fn eval_rounds_truncation_keeps_the_cut_round_whole() {
    // First n rounds of 10-round AES, cut round keeping MixColumns, equal
    // the n-round cipher with final MixColumns retained.
    let full = aes128::aes128();
    let mut r = rng(3);
    for n in 1..10usize {
        for _ in 0..50 {
            let key: [u8; 16] = rand_bytes(&mut r);
            let pt: [u8; 16] = rand_bytes(&mut r);
            let want = ReducedAes128::new(&key, n, true).encrypt(&pt);
            assert_eq!(eval_rounds(&full, &key, &pt, n), want, "n={n}");
        }
    }
    // n = 10 is the full cipher.
    let key = [7u8; 16];
    let pt = [9u8; 16];
    assert_eq!(eval_rounds(&full, &key, &pt, 10), eval(&full, &key, &pt));
}

#[test]
fn small_scale_aes_matches_small_aes() {
    fn cells(b: &[u8]) -> [u8; 4] {
        [b[0] & 15, b[0] >> 4, b[1] & 15, b[1] >> 4]
    }
    fn bytes(c: [u8; 4]) -> [u8; 2] {
        [c[0] | (c[1] << 4), c[2] | (c[3] << 4)]
    }
    for nr in 1..=10usize {
        let p = aes128::small_scale(nr);
        let mut r = rng(0x200 + nr as u64);
        for _ in 0..RANDOM_PAIRS {
            let key: [u8; 2] = rand_bytes(&mut r);
            let pt: [u8; 2] = rand_bytes(&mut r);
            let want = SmallAes::new(cells(&key), nr).encrypt(cells(&pt));
            assert_eq!(eval(&p, &key, &pt), bytes(want).to_vec(), "nr={nr}");
        }
    }
    // Exhaustive over all 2^16 plaintexts for one key, 4 rounds.
    let p = aes128::small_scale(4);
    let key = bytes([0xa, 0x5, 0x3, 0xc]);
    let cipher = SmallAes::new(cells(&key), 4);
    for x in 0..=u16::MAX {
        let pt = x.to_le_bytes();
        assert_eq!(
            eval(&p, &key, &pt),
            bytes(cipher.encrypt(cells(&pt))).to_vec()
        );
    }
}

// ── PRESENT-80 ──────────────────────────────────────────────────────────

fn present_ref(key: &[u8; 10], block: [u8; 8]) -> [u8; 8] {
    let mut b = block;
    present::Present80::new(key).encrypt_block(&mut b);
    b
}

#[test]
fn present80_paper_vectors() {
    let p = present80::present80();
    assert_eq!(
        eval(&p, &[0u8; 10], &[0u8; 8]),
        h("5579c1387b228445"),
        "key 0 / pt 0"
    );
    assert_eq!(
        eval(&p, &[0xFFu8; 10], &[0xFFu8; 8]),
        h("3333dcd3213210d2"),
        "key 1 / pt 1"
    );
    // The paper's other two PRESENT-80 vectors (all-ones key / zero block,
    // zero key / all-ones block) have no vector in the existing tests, so
    // they are cross-checked against the existing implementation instead.
    for (k, b) in [([0xFFu8; 10], [0u8; 8]), ([0u8; 10], [0xFFu8; 8])] {
        assert_eq!(eval(&p, &k, &b), present_ref(&k, b).to_vec());
    }
}

#[test]
fn present80_matches_symmetric_present_random() {
    let p = present80::present80();
    let mut r = rng(4);
    for _ in 0..RANDOM_PAIRS {
        let key: [u8; 10] = rand_bytes(&mut r);
        let pt: [u8; 8] = rand_bytes(&mut r);
        assert_eq!(eval(&p, &key, &pt), present_ref(&key, pt).to_vec());
    }
}

// ── ToySpn ──────────────────────────────────────────────────────────────

#[test]
fn toyspn_matches_boomerang_toyspn() {
    for (si, sbox) in [serpent_s0(), present_sbox()].into_iter().enumerate() {
        for rounds in [1usize, 2, 3, 4, 5, 8] {
            let p = toyspn::toyspn(&sbox, rounds);
            let mut r = rng(0x300 + 16 * si as u64 + rounds as u64);
            for _ in 0..RANDOM_PAIRS {
                let mk: u64 = r.gen();
                let pt: u16 = r.gen();
                let want = ToySpn::new(sbox.clone(), rounds, mk).encrypt_u16(pt);
                assert_eq!(
                    eval(&p, &mk.to_le_bytes(), &pt.to_le_bytes()),
                    want.to_le_bytes().to_vec(),
                    "sbox {si} rounds {rounds}"
                );
            }
        }
    }
    // The vector pinned by the existing round-trip test's key.
    let sbox = serpent_s0();
    let p = toyspn::toyspn(&sbox, 4);
    for pt in 0..=u16::MAX {
        let want = ToySpn::new(sbox.clone(), 4, 0xDEAD_BEEF).encrypt_u16(pt);
        assert_eq!(
            eval(&p, &0xDEAD_BEEFu64.to_le_bytes(), &pt.to_le_bytes()),
            want.to_le_bytes().to_vec()
        );
    }
}

// ── Speck / Simon ───────────────────────────────────────────────────────

fn words_le<const N: usize>(ws: &[u64], bytes_per_word: usize) -> [u8; N] {
    let mut out = [0u8; N];
    for (i, w) in ws.iter().enumerate() {
        out[i * bytes_per_word..(i + 1) * bytes_per_word]
            .copy_from_slice(&w.to_le_bytes()[..bytes_per_word]);
    }
    out
}

#[test]
fn speck_paper_vectors() {
    // Appendix C vectors, written as in the existing tests: block = (y, x),
    // key = (k0, l0, ...), all little-endian words.
    let key64: [u8; 16] = words_le(&[0x03020100, 0x0b0a0908, 0x13121110, 0x1b1a1918], 4);
    let pt64: [u8; 8] = words_le(&[0x7475432d, 0x3b726574], 4);
    let ct64: [u8; 8] = words_le(&[0x454e028b, 0x8c6fa548], 4);
    assert_eq!(
        eval(&speck::speck64_128(), &key64, &pt64),
        ct64.to_vec(),
        "Speck64/128"
    );

    let key128: [u8; 16] = words_le(&[0x0706050403020100, 0x0f0e0d0c0b0a0908], 8);
    let pt128: [u8; 16] = words_le(&[0x7469206564616d20, 0x6c61766975716520], 8);
    let ct128: [u8; 16] = words_le(&[0x7860fedf5c570d18, 0xa65d985179783265], 8);
    assert_eq!(
        eval(&speck::speck128_128(), &key128, &pt128),
        ct128.to_vec(),
        "Speck128/128"
    );

    let mut key256 = [0u8; 32];
    for (i, b) in key256.iter_mut().enumerate() {
        *b = i as u8;
    }
    let pt256: [u8; 16] = words_le(&[0x202e72656e6f6f70, 0x65736f6874206e49], 8);
    let ct256: [u8; 16] = words_le(&[0x4eeeb48d9c188f43, 0x4109010405c0f53e], 8);
    assert_eq!(
        eval(&speck::speck128_256(), &key256, &pt256),
        ct256.to_vec(),
        "Speck128/256"
    );
}

#[test]
fn speck_matches_symmetric_speck_random() {
    let (p64, p128, p256) = (
        speck::speck64_128(),
        speck::speck128_128(),
        speck::speck128_256(),
    );
    let mut r = rng(5);
    for _ in 0..RANDOM_PAIRS {
        let k16: [u8; 16] = rand_bytes(&mut r);
        let k32: [u8; 32] = rand_bytes(&mut r);
        let b8: [u8; 8] = rand_bytes(&mut r);
        let b16: [u8; 16] = rand_bytes(&mut r);

        let mut want = b8;
        speck_ref::Speck64_128::new(&k16).encrypt_block(&mut want);
        assert_eq!(eval(&p64, &k16, &b8), want.to_vec());

        let mut want = b16;
        speck_ref::Speck128_128::new(&k16).encrypt_block(&mut want);
        assert_eq!(eval(&p128, &k16, &b16), want.to_vec());

        let mut want = b16;
        speck_ref::Speck128_256::new(&k32).encrypt_block(&mut want);
        assert_eq!(eval(&p256, &k32, &b16), want.to_vec());
    }
}

#[test]
fn simon_paper_vectors() {
    let key64: [u8; 16] = words_le(&[0x03020100, 0x0b0a0908, 0x13121110, 0x1b1a1918], 4);
    let pt64: [u8; 8] = words_le(&[0x20646e75, 0x656b696c], 4);
    let ct64: [u8; 8] = words_le(&[0xb9dfa07a, 0x44c8fc20], 4);
    assert_eq!(
        eval(&simon::simon64_128(), &key64, &pt64),
        ct64.to_vec(),
        "Simon64/128"
    );

    let key128: [u8; 16] = words_le(&[0x0706050403020100, 0x0f0e0d0c0b0a0908], 8);
    let pt128: [u8; 16] = words_le(&[0x6c6c657661727420, 0x6373656420737265], 8);
    let ct128: [u8; 16] = words_le(&[0x65aa832af84e0bbc, 0x49681b1e1e54fe3f], 8);
    assert_eq!(
        eval(&simon::simon128_128(), &key128, &pt128),
        ct128.to_vec(),
        "Simon128/128"
    );

    let mut key256 = [0u8; 32];
    for (i, b) in key256.iter_mut().enumerate() {
        *b = i as u8;
    }
    let pt256: [u8; 16] = words_le(&[0x6d69732061207369, 0x74206e69206d6f6f], 8);
    let ct256: [u8; 16] = words_le(&[0x3bf72a87efe7b868, 0x8d2b5579afc8a3a0], 8);
    assert_eq!(
        eval(&simon::simon128_256(), &key256, &pt256),
        ct256.to_vec(),
        "Simon128/256"
    );
}

#[test]
fn simon_matches_symmetric_simon_random() {
    let (p64, p128, p256) = (
        simon::simon64_128(),
        simon::simon128_128(),
        simon::simon128_256(),
    );
    let mut r = rng(6);
    for _ in 0..RANDOM_PAIRS {
        let k16: [u8; 16] = rand_bytes(&mut r);
        let k32: [u8; 32] = rand_bytes(&mut r);
        let b8: [u8; 8] = rand_bytes(&mut r);
        let b16: [u8; 16] = rand_bytes(&mut r);

        let mut want = b8;
        simon_ref::Simon64_128::new(&k16).encrypt_block(&mut want);
        assert_eq!(eval(&p64, &k16, &b8), want.to_vec());

        let mut want = b16;
        simon_ref::Simon128_128::new(&k16).encrypt_block(&mut want);
        assert_eq!(eval(&p128, &k16, &b16), want.to_vec());

        let mut want = b16;
        simon_ref::Simon128_256::new(&k32).encrypt_block(&mut want);
        assert_eq!(eval(&p256, &k32, &b16), want.to_vec());
    }
}

// ── ChaCha ──────────────────────────────────────────────────────────────

fn chacha_state_bytes(key: &[u8; 32], nonce: &[u8; 12], counter: u32) -> Vec<u8> {
    let mut s = Vec::with_capacity(64);
    for c in chacha20::SIGMA {
        s.extend_from_slice(&c.to_le_bytes());
    }
    s.extend_from_slice(key);
    s.extend_from_slice(&counter.to_le_bytes());
    s.extend_from_slice(nonce);
    s
}

#[test]
fn chacha20_rfc8439_block_vector() {
    let key: [u8; 32] = h("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")
        .try_into()
        .unwrap();
    let nonce: [u8; 12] = h("000000090000004a00000000").try_into().unwrap();
    let expected = h("10f1e7e4d13b5915500fdd1fa32071c4c7d1f4c733c068030422aa9ac3d46c4ed2826446079faa0914c2d705d98b02a2b5129cd1de164eb9cbd083e8a2503c4e");
    assert_eq!(
        eval(
            &chacha::chacha20(),
            &[],
            &chacha_state_bytes(&key, &nonce, 1)
        ),
        expected
    );
}

#[test]
fn chacha_matches_symmetric_chacha20_random() {
    type Block = fn(&[u8; 32], &[u8; 12], u32) -> [u8; 64];
    let cases: [(Primitive, Block); 3] = [
        (chacha::chacha20(), chacha20::chacha20_block),
        (chacha::chacha12(), chacha20::chacha12_block),
        (chacha::chacha8(), chacha20::chacha8_block),
    ];
    for (i, (p, reference)) in cases.iter().enumerate() {
        let mut r = rng(0x700 + i as u64);
        for _ in 0..RANDOM_PAIRS {
            let key: [u8; 32] = rand_bytes(&mut r);
            let nonce: [u8; 12] = rand_bytes(&mut r);
            let counter: u32 = r.gen();
            let want = reference(&key, &nonce, counter);
            assert_eq!(
                eval(p, &[], &chacha_state_bytes(&key, &nonce, counter)),
                want.to_vec(),
                "{}",
                p.name
            );
        }
    }
}

/// Independent reference for the documented reduced-width convention.
fn chacha_reference(w: usize, rounds: usize, state: &[u64; 16]) -> [u64; 16] {
    let mask = (1u64 << w) - 1;
    let rotl = |x: u64, k: usize| ((x << k) | (x >> (w - k))) & mask;
    let rot = [16, 12, 8, 7].map(|r| r * w / 32);
    let mut s = *state;
    let qr = |s: &mut [u64; 16], a: usize, b: usize, c: usize, d: usize| {
        s[a] = (s[a] + s[b]) & mask;
        s[d] = rotl(s[d] ^ s[a], rot[0]);
        s[c] = (s[c] + s[d]) & mask;
        s[b] = rotl(s[b] ^ s[c], rot[1]);
        s[a] = (s[a] + s[b]) & mask;
        s[d] = rotl(s[d] ^ s[a], rot[2]);
        s[c] = (s[c] + s[d]) & mask;
        s[b] = rotl(s[b] ^ s[c], rot[3]);
    };
    for i in 0..rounds {
        if i.is_multiple_of(2) {
            qr(&mut s, 0, 4, 8, 12);
            qr(&mut s, 1, 5, 9, 13);
            qr(&mut s, 2, 6, 10, 14);
            qr(&mut s, 3, 7, 11, 15);
        } else {
            qr(&mut s, 0, 5, 10, 15);
            qr(&mut s, 1, 6, 11, 12);
            qr(&mut s, 2, 7, 8, 13);
            qr(&mut s, 3, 4, 9, 14);
        }
    }
    let mut out = [0u64; 16];
    for i in 0..16 {
        out[i] = (s[i] + state[i]) & mask;
    }
    out
}

#[test]
fn chacha_reduced_width_matches_independent_reference() {
    for w in [8usize, 16, 32] {
        for rounds in [1usize, 4, 7, 12, 20] {
            let p = chacha::reduced_width(w, rounds);
            let mut r = rng(0x800 + (w * 100 + rounds) as u64);
            for _ in 0..200 {
                let mask = (1u64 << w) - 1;
                let key: [u64; 8] = std::array::from_fn(|_| r.gen::<u64>() & mask);
                let cn: [u64; 4] = std::array::from_fn(|_| r.gen::<u64>() & mask);
                let block = chacha::input_block(w, &key, &cn);
                let mut st = [0u64; 16];
                st[..4].copy_from_slice(&chacha::constants(w));
                st[4..12].copy_from_slice(&key);
                st[12..].copy_from_slice(&cn);
                let want = chacha_reference(w, rounds, &st);
                let nb = w / 8;
                let want_bytes: Vec<u8> = want
                    .iter()
                    .flat_map(|v| v.to_le_bytes()[..nb].to_vec())
                    .collect();
                assert_eq!(eval(&p, &[], &block), want_bytes, "w={w} rounds={rounds}");
            }
        }
    }
    // 32-bit reduced_width is the standard ChaCha description.
    assert_eq!(
        chacha::reduced_width(32, 20).rounds,
        chacha::chacha20().rounds
    );
    assert_eq!(chacha::reduced_rotations(16), [8, 6, 4, 3]);
    assert_eq!(chacha::reduced_rotations(8), [4, 3, 2, 1]);
    assert_eq!(
        chacha::constants(32),
        [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574]
    );
}

// ── SHA-256 compression ─────────────────────────────────────────────────

fn state_bytes(s: &[u32; 8]) -> Vec<u8> {
    s.iter().flat_map(|w| w.to_be_bytes()).collect()
}

fn sha256_pad(msg: &[u8]) -> Vec<u8> {
    let mut out = msg.to_vec();
    out.push(0x80);
    while out.len() % 64 != 56 {
        out.push(0);
    }
    out.extend_from_slice(&((msg.len() as u64) * 8).to_be_bytes());
    out
}

fn sha256_via_ir(msg: &[u8]) -> Vec<u8> {
    let p = sha256_compress::sha256_compress();
    let mut st = state_bytes(&sha::H0);
    for blk in sha256_pad(msg).chunks_exact(64) {
        st = eval(&p, blk, &st);
    }
    st
}

#[test]
fn sha256_compress_fips_known_answers() {
    let long = b"abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu";
    let cases: [(&[u8], &str); 5] = [
        (
            b"",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ),
        (
            b"abc",
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        ),
        (
            b"hello world",
            "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
        ),
        (
            b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
            "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1",
        ),
        (
            long,
            "cf5b16a778af8380036ce59e7b0492370b249b11e8f07a51afac45037afee9d1",
        ),
    ];
    for (msg, digest) in cases {
        assert_eq!(
            sha256_via_ir(msg),
            h(digest),
            "{:?}",
            String::from_utf8_lossy(msg)
        );
    }
}

#[test]
fn sha256_via_ir_matches_sha256_on_assorted_lengths() {
    let mut r = rng(9);
    for len in [0usize, 1, 55, 56, 63, 64, 65, 119, 200] {
        let mut msg = vec![0u8; len];
        r.fill(&mut msg[..]);
        assert_eq!(sha256_via_ir(&msg), sha::sha256(&msg).to_vec(), "len {len}");
    }
}

#[test]
fn sha256_compress_matches_compress_random() {
    let p = sha256_compress::sha256_compress();
    let mut r = rng(10);
    for _ in 0..RANDOM_PAIRS {
        let mut st: [u32; 8] = std::array::from_fn(|_| r.gen());
        let blk: [u8; 64] = rand_bytes(&mut r);
        let got = eval(&p, &blk, &state_bytes(&st));
        sha::compress(&mut st, &blk);
        assert_eq!(got, state_bytes(&st));
    }
}

/// Independent reference for the first `n` steps with feed-forward.
fn sha256_steps_reference(n: usize, st: &[u32; 8], blk: &[u8]) -> [u32; 8] {
    let mut w = [0u32; 64];
    for i in 0..16 {
        w[i] = u32::from_be_bytes(blk[4 * i..4 * i + 4].try_into().unwrap());
    }
    for i in 16..64 {
        let g0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
        let g1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
        w[i] = g1
            .wrapping_add(w[i - 7])
            .wrapping_add(g0)
            .wrapping_add(w[i - 16]);
    }
    let [mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut hh] = *st;
    for i in 0..n {
        let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
        let ch = (e & f) ^ (!e & g);
        let t1 = hh
            .wrapping_add(s1)
            .wrapping_add(ch)
            .wrapping_add(sha::K[i])
            .wrapping_add(w[i]);
        let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
        let maj = (a & b) ^ (a & c) ^ (b & c);
        let t2 = s0.wrapping_add(maj);
        hh = g;
        g = f;
        f = e;
        e = d.wrapping_add(t1);
        d = c;
        c = b;
        b = a;
        a = t1.wrapping_add(t2);
    }
    let v = [a, b, c, d, e, f, g, hh];
    std::array::from_fn(|i| st[i].wrapping_add(v[i]))
}

#[test]
fn sha256_reduced_steps_match_independent_reference() {
    let mut r = rng(11);
    for n in 1..=64usize {
        let p = sha256_compress::steps(n);
        for _ in 0..20 {
            let st: [u32; 8] = std::array::from_fn(|_| r.gen());
            let blk: [u8; 64] = rand_bytes(&mut r);
            assert_eq!(
                eval(&p, &blk, &state_bytes(&st)),
                state_bytes(&sha256_steps_reference(n, &st, &blk)),
                "steps({n})"
            );
        }
    }
    // eval_rounds on the full description agrees with steps(n).
    let full = sha256_compress::sha256_compress();
    let st = state_bytes(&sha::H0);
    let blk = [0x5au8; 64];
    for n in [1usize, 9, 20, 27, 63] {
        assert_eq!(
            eval_rounds(&full, &blk, &st, n),
            eval(&sha256_compress::steps(n), &blk, &st)
        );
    }
}

// ── Linear-key-schedule variants, for the types the primitives do not use ─

#[test]
fn independent_and_linear_schedules_expand_as_documented() {
    use super::{Codec, FeedForward, Gf2Matrix, KeySchedule, Kind, Layer, Round};
    // 8-bit block, XOR of round key 0 then round key 1; the key is the two
    // 8-bit round keys (Independent) or k and a rotation of k (Linear).
    let layers = vec![
        Layer::AddRoundKey {
            round_key: 0,
            bit_offset: 0,
        },
        Layer::AddRoundKey {
            round_key: 1,
            bit_offset: 0,
        },
    ];
    let mut p = Primitive {
        name: "xor2".into(),
        block_bits: 8,
        key_bits: 16,
        scratch_bits: 0,
        block_codec: Codec::BYTES,
        key_codec: Codec::BYTES,
        sboxes: vec![],
        rounds: vec![Round { layers }],
        key_schedule: KeySchedule::Independent {
            round_keys: 2,
            round_key_bits: 8,
        },
        feed_forward: FeedForward::None,
        kind: Kind::Spn,
    };
    p.validate().unwrap();
    assert_eq!(eval(&p, &[0x0f, 0xf3], &[0x55]), vec![0x55 ^ 0x0f ^ 0xf3]);

    let rot: Vec<usize> = (0..8).map(|i| (i + 1) % 8).collect();
    let mut m = Gf2Matrix::zero(16, 8);
    let pm = Gf2Matrix::from_permutation(&rot);
    for i in 0..8 {
        m.set(i, i, true);
        for j in 0..8 {
            m.set(8 + i, j, pm.get(i, j));
        }
    }
    p.key_bits = 8;
    p.key_schedule = KeySchedule::Linear {
        matrix: m,
        round_key_bits: 8,
    };
    p.validate().unwrap();
    let k = 0b1001_0110u8;
    let want = 0x55 ^ k ^ k.rotate_right(1);
    assert_eq!(eval(&p, &[k], &[0x55]), vec![want]);
}
