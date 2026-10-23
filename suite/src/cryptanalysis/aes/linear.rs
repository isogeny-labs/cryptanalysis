//! Linear cryptanalysis of reduced-round AES (Matsui, EUROCRYPT 1993).
//!
//! Linear cryptanalysis searches for **linear equations among plaintext,
//! ciphertext, and key bits** that hold with probability ≠ ½. Each such
//! equation has a *bias* `ε`, with `Pr[equation holds] = ½ + ε`. Given
//! `≈ 1/ε²` known plaintext/ciphertext pairs, an attacker can determine
//! which value of `½ + ε` or `½ − ε` the equation realises, and thus
//! recover one bit of information about the key.
//!
//! For AES the Linear Approximation Table (LAT) of the S-box has
//! maximum absolute entry **16** (out of an ideal lower bound of 0 and
//! a worst case of 128). The corresponding bias is `16/256 = 1/16`.
//! Per the *wide-trail* design strategy:
//!
//! - A 2-round linear trail crosses at least **5 active S-boxes**
//!   (branch number of MixColumns = 5).
//! - Piling-up lemma: bias of an `n`-S-box trail = `2^(n-1) · ∏ εᵢ`.
//! - With `εᵢ ≤ 1/16` and `n ≥ 5`: 2-round bias ≤ `2⁴ · (1/16)⁵ = 2⁻¹⁶`.
//! - 4-round bias ≤ `2⁻³²`; 8-round bias ≤ `2⁻⁶⁴`. Full AES is
//!   immune in any practical sense.
//!
//! This module provides:
//!
//! 1. [`aes_sbox_lat`] — the LAT, plus [`max_linear_bias`].
//! 2. [`linear_correlation`] — the signed correlation
//!    `C(a, b) = 2 · LAT[a][b] / 256` for masks `(a, b)`.
//! 3. [`recover_key_bit_one_round`] — Matsui-style attack on 1-round
//!    AES recovering one bit of `K_R0 ⊕ K_R1_shifted`.
//! 4. [`measure_key_parity_one_round`] — the empirical LAT parity count,
//!    including ties where the corpus does not select a parity.
//! 5. [`recover_key_byte_one_round`] — exact one-round byte consistency;
//!    this recovery method is separate from the statistical LAT estimate.
//!
//! # Why we stop at 1 round in this module
//!
//! The wide-trail bound makes a 2-round Matsui-style attack uninteresting
//! pedagogically: you would need `2³²` known plaintexts and the
//! cryptanalysis would mostly highlight that the design defeats you.
//! At 1 round we count samples satisfying an LAT approximation and infer
//! one key parity by majority vote. Exact one-round key-byte consistency
//! is available separately and must not be attributed to that vote.

use super::reduced::{ReducedAes128, SBOX};

/// Bit-mask dot product: `popcount(a ∧ b) mod 2`.
fn dot(a: u8, b: u8) -> u8 {
    (a & b).count_ones() as u8 & 1
}

/// AES S-box LAT.
///
/// `LAT[a][b] = #{x : a·x ⊕ b·S(x) = 0} − 128`. That is, the signed
/// imbalance from the random expectation of 128. A nonzero entry means
/// the linear approximation `a·x ⊕ b·S(x) = 0` deviates from 50/50;
/// the magnitude is the bias scaled by 256.
///
/// Verified properties:
///
/// - `LAT[0][0] = 128` (the trivial all-zero approximation holds for
///   every `x`; `128 = 256 − 128`).
/// - `LAT[0][b] = LAT[a][0] = 0` for nonzero masks (S-box is balanced).
/// - `max |LAT[a][b]| = 16` for nonzero `(a, b)` — AES's headline
///   linearity result.
pub fn aes_sbox_lat() -> Vec<Vec<i32>> {
    let mut lat = vec![vec![0i32; 256]; 256];
    for a in 0..256usize {
        for b in 0..256usize {
            let mut count = 0i32;
            for x in 0..256usize {
                if dot(a as u8, x as u8) ^ dot(b as u8, SBOX[x]) == 0 {
                    count += 1;
                }
            }
            lat[a][b] = count - 128;
        }
    }
    lat
}

/// Differential-linear connectivity table for the AES S-box.
///
/// `DLCT[a][b] = (1/2) sum_x (-1)^(b · (S(x) xor S(x xor a)))`.
/// The half-scale convention gives `DLCT[0][b] = DLCT[a][0] = 128`.
pub fn aes_sbox_dlct() -> Vec<Vec<i32>> {
    let mut table = vec![vec![0i32; 256]; 256];
    for (a, row) in table.iter_mut().enumerate() {
        for x in 0..256usize {
            let difference = SBOX[x] ^ SBOX[x ^ a];
            for (mask, value) in row.iter_mut().enumerate() {
                *value += if dot(mask as u8, difference) == 0 {
                    1
                } else {
                    -1
                };
            }
        }
        for value in row {
            *value /= 2;
        }
    }
    table
}

/// Returns `(a, b, |bias|)` for the maximum-magnitude entry over
/// nonzero `(a, b)`. The headline `16` corresponds to bias `16/256 = 1/16`.
pub fn max_linear_bias(lat: &[Vec<i32>]) -> (u8, u8, u32) {
    let mut best = (0u8, 0u8, 0u32);
    for (a, row) in lat.iter().enumerate() {
        for (b, &v) in row.iter().enumerate() {
            if a == 0 && b == 0 {
                continue;
            }
            let mag = v.unsigned_abs();
            if mag > best.2 {
                best = (a as u8, b as u8, mag);
            }
        }
    }
    best
}

/// Signed correlation `C(a, b) = 2 · LAT[a][b] / 256 = LAT[a][b] / 128`.
/// `|C| ≤ 1`; the linear approximation has bias `C/2`.
pub fn linear_correlation(lat: &[Vec<i32>], a: u8, b: u8) -> f64 {
    lat[a as usize][b as usize] as f64 / 128.0
}

/// Matsui-style one-round known-plaintext attack: recover one parity
/// bit of the effective key at byte position `(c, r)`.
///
/// The 1-round AES output byte at `(c, r)` is:
///
/// `C[c][r] = K_R1[c][r] ⊕ SBOX[P[(c+r) mod 4][r] ⊕ K_R0[(c+r) mod 4][r]]`.
///
/// Using a linear approximation `a · x ⊕ b · S(x) = 0` (bias `ε`):
///
/// `Pr[ a·P[i,r] ⊕ b·C[c,r] = a·K_R0[i,r] ⊕ b·K_R1[c,r] ] = ½ + ε`.
///
/// The RHS is a constant `K* ∈ {0, 1}` determined by the key. Count
/// the LHS over many known pairs; whichever value (`0` or `1`) is more
/// common is `K*` if the LAT entry is positive, and the opposite if
/// negative.
///
/// Returns the recovered bit `K*`, plus a confidence margin (how far
/// the empirical count was from the random expectation `n/2`).
pub fn recover_key_bit_one_round(
    pairs: &[([u8; 16], [u8; 16])],
    byte_pos: (usize, usize),
    input_mask: u8,
    output_mask: u8,
    lat: &[Vec<i32>],
) -> (u8, i32) {
    let (c, r) = byte_pos;
    let i = (c + r) % 4;
    let plaintext_byte_pos = 4 * i + r;
    let ciphertext_byte_pos = 4 * c + r;
    let mut zeros = 0i32;
    for (p, ct) in pairs {
        let lhs =
            dot(input_mask, p[plaintext_byte_pos]) ^ dot(output_mask, ct[ciphertext_byte_pos]);
        if lhs == 0 {
            zeros += 1;
        }
    }
    let margin = zeros - pairs.len() as i32 / 2;
    // If LAT entry is positive: zeros > n/2 ⇒ K* = 0, else K* = 1.
    // If LAT entry is negative: the relationship inverts.
    let lat_sign = lat[input_mask as usize][output_mask as usize].signum();
    let bit = if lat_sign >= 0 {
        if margin > 0 {
            0
        } else {
            1
        }
    } else if margin > 0 {
        1
    } else {
        0
    };
    (bit, margin)
}

/// One measured LAT approximation at a selected AES byte position. The
/// inferred parity is absent on an exact tie; sample noise may still make a
/// non-tied estimate wrong.
#[derive(Clone, Debug)]
pub struct LinearParityMeasurement {
    pub input_mask: u8,
    pub output_mask: u8,
    pub lat_entry: i32,
    pub pair_count: usize,
    pub zero_count: usize,
    pub one_count: usize,
    pub inferred_key_parity: Option<u8>,
}

pub fn measure_key_parity_one_round(
    pairs: &[([u8; 16], [u8; 16])],
    byte_pos: (usize, usize),
    input_mask: u8,
    output_mask: u8,
    lat: &[Vec<i32>],
) -> Option<LinearParityMeasurement> {
    if pairs.is_empty() || input_mask == 0 || output_mask == 0 {
        return None;
    }
    let entry = *lat.get(input_mask as usize)?.get(output_mask as usize)?;
    if entry == 0 {
        return None;
    }
    let (c, r) = byte_pos;
    if c >= 4 || r >= 4 {
        return None;
    }
    let plaintext_position = 4 * ((c + r) % 4) + r;
    let ciphertext_position = 4 * c + r;
    let zeros = pairs
        .iter()
        .filter(|(p, ct)| {
            dot(input_mask, p[plaintext_position]) ^ dot(output_mask, ct[ciphertext_position]) == 0
        })
        .count();
    let signed_margin = 2 * zeros as i64 - pairs.len() as i64;
    let inferred_key_parity = if signed_margin == 0 {
        None
    } else {
        Some(if (signed_margin > 0) == (entry > 0) {
            0
        } else {
            1
        })
    };
    Some(LinearParityMeasurement {
        input_mask,
        output_mask,
        lat_entry: entry,
        pair_count: pairs.len(),
        zero_count: zeros,
        one_count: pairs.len() - zeros,
        inferred_key_parity,
    })
}

/// Recover the input whitening key byte at `(c,r)` by testing each of 256
/// candidates against the exact one-round relation
/// `C[c,r] = S(P[(c+r) mod 4,r] xor K0) xor K1`. A surviving candidate
/// must imply the same output whitening byte `K1` for every pair. This is
/// exact consistency, not statistical linear key recovery. The `lat` argument
/// is retained for callers of the existing API and is not used here.
pub fn recover_key_byte_one_round(
    pairs: &[([u8; 16], [u8; 16])],
    byte_pos: (usize, usize),
    _lat: &[Vec<i32>],
) -> Option<u8> {
    let (c, r) = byte_pos;
    let i = (c + r) % 4;
    let plaintext_byte_pos = 4 * i + r;
    let ciphertext_byte_pos = 4 * c + r;

    let mut k_eff: Option<u8> = None;
    for k in 0u16..256 {
        let k = k as u8;
        let mut consistent = true;
        let mut k_out: Option<u8> = None;
        for (p, ct) in pairs {
            let candidate_out =
                SBOX[(p[plaintext_byte_pos] ^ k) as usize] ^ ct[ciphertext_byte_pos];
            match k_out {
                None => k_out = Some(candidate_out),
                Some(prev) if prev != candidate_out => {
                    consistent = false;
                    break;
                }
                _ => {}
            }
        }
        if consistent {
            if k_eff.is_some() {
                // Ambiguous — return None.
                return None;
            }
            k_eff = Some(k);
        }
    }
    k_eff
}

/// Build `n_pairs` known-plaintext samples for a 1-round cipher with
/// `final_mix_columns = false`. Deterministic for reproducibility.
pub fn known_plaintext_corpus(
    cipher: &ReducedAes128,
    n_pairs: usize,
    seed: u64,
) -> Vec<([u8; 16], [u8; 16])> {
    let mut state = seed;
    let mut byte = || {
        state = state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        (state >> 33) as u8
    };
    (0..n_pairs)
        .map(|_| {
            let mut p = [0u8; 16];
            for b in p.iter_mut() {
                *b = byte();
            }
            let c = cipher.encrypt(&p);
            (p, c)
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lat_origin() {
        let lat = aes_sbox_lat();
        assert_eq!(lat[0][0], 128);
        for b in 1..256 {
            assert_eq!(lat[0][b], 0, "LAT[0][{b}] should be 0 (balanced)");
            assert_eq!(lat[b][0], 0, "LAT[{b}][0] should be 0 (balanced)");
        }
    }

    /// All LAT entries are even: if `x` is a counted input then so is
    /// `x ⊕ all-ones-input` for the same dot products (by complement).
    /// Wait — this isn't quite the right argument; the actual reason
    /// is that the linear/affine over GF(2) S-box always pairs inputs
    /// in some way. Empirically true for AES.
    #[test]
    fn lat_entries_even() {
        let lat = aes_sbox_lat();
        for row in &lat {
            for &v in row {
                assert_eq!(v % 2, 0);
            }
        }
    }

    #[test]
    fn aes_max_linear_bias_is_sixteen() {
        let lat = aes_sbox_lat();
        let (a, b, mag) = max_linear_bias(&lat);
        assert_eq!(mag, 16, "AES S-box max linear bias should be 16/256 = 1/16");
        assert_eq!((a, b, lat[a as usize][b as usize]), (1, 72, -16));
    }

    /// The correlation of the max bias is ±16/128 = ±1/8.
    #[test]
    fn aes_max_correlation() {
        let lat = aes_sbox_lat();
        let (a, b, _) = max_linear_bias(&lat);
        let c = linear_correlation(&lat, a, b);
        assert!((c.abs() - 1.0 / 8.0).abs() < 1e-12);
    }

    /// One-round key recovery by brute force over a single byte position.
    #[test]
    fn one_round_byte_recovery() {
        let key: [u8; 16] = [
            0xa5, 0x77, 0x83, 0x14, 0x21, 0x6e, 0xc9, 0xb2, 0x4d, 0x05, 0x88, 0xfb, 0x37, 0x52,
            0xee, 0x9f,
        ];
        let cipher = ReducedAes128::new(&key, 1, false);
        let corpus = known_plaintext_corpus(&cipher, 8, 0xfa11_face);
        let lat = aes_sbox_lat();
        // Recover the effective input-side key byte at every position.
        for c in 0..4 {
            for r in 0..4 {
                let recovered = recover_key_byte_one_round(&corpus, (c, r), &lat)
                    .expect("should recover unambiguously");
                let i = (c + r) % 4;
                let expected_input_key = cipher.round_key(0)[i][r];
                assert_eq!(
                    recovered, expected_input_key,
                    "wrong K_R0 byte at (c={c}, r={r}): got {recovered:#x}, want {expected_input_key:#x}"
                );
            }
        }
    }

    /// The single-bit majority-vote attack: with enough samples, the
    /// recovered bit matches the true key-bit-parity.
    #[test]
    fn single_bit_majority_vote_converges() {
        let key = [0x42u8; 16];
        let cipher = ReducedAes128::new(&key, 1, false);
        let corpus = known_plaintext_corpus(&cipher, 4096, 0xbeef);
        let lat = aes_sbox_lat();
        // Use the strongest approximation at byte position (0, 0).
        let (a, b, _) = max_linear_bias(&lat);
        let (bit, margin) = recover_key_bit_one_round(&corpus, (0, 0), a, b, &lat);
        // Verify against the true value of a · K_R0[0,0] ⊕ b · K_R1_shift[0,0].
        let k_in = cipher.round_key(0)[0][0];
        let k_out = cipher.round_key(1)[0][0];
        let expected_bit = dot(a, k_in) ^ dot(b, k_out);
        assert_eq!(
            bit, expected_bit,
            "majority-vote bit {bit} != expected {expected_bit}; margin = {margin}"
        );
        // A bias of 1/16 over 4096 samples gives expected margin ≈ 256.
        assert!(margin.abs() >= 100, "margin too small: {margin}");
        let measured = measure_key_parity_one_round(&corpus, (0, 0), a, b, &lat).unwrap();
        assert_eq!(measured.pair_count, corpus.len());
        assert_eq!(measured.zero_count + measured.one_count, corpus.len());
        assert_eq!(measured.inferred_key_parity, Some(expected_bit));
    }

    #[test]
    fn measured_linear_parity_keeps_a_tie_unresolved() {
        let lat = aes_sbox_lat();
        let (a, b, _) = max_linear_bias(&lat);
        let output_bit = 1u8 << b.trailing_zeros();
        let zero = ([0u8; 16], [0u8; 16]);
        let mut one_ciphertext = [0u8; 16];
        one_ciphertext[0] = output_bit;
        let tied =
            measure_key_parity_one_round(&[zero, ([0u8; 16], one_ciphertext)], (0, 0), a, b, &lat)
                .unwrap();
        assert_eq!(tied.zero_count, 1);
        assert_eq!(tied.one_count, 1);
        assert_eq!(tied.inferred_key_parity, None);
    }
}
